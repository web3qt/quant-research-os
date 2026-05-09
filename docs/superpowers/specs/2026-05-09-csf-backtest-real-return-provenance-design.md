# CSF Backtest 真实收益来源与 Proxy PnL 阻断设计

## 背景

在一条 Claude Code 驱动的 QROS 研究线中，`csf_backtest_ready` 的 stage-local program 使用 `mom_ret` 作为 return proxy 计算组合 PnL：

```python
daily_portfolio_return = sum(weight * mom_ret)
```

这类结果不能视为真实可交易回测。`mom_ret` 来自 signal/factor panel，可能是因子构造输入、动量特征或诊断字段，而不是由独立价格路径、调仓账本和交易成本模型计算出的可交易收益。

当前 QROS 的 artifact contract、runtime validator 和 skill 文案没有形成机器级阻断：只要程序产出 `portfolio_summary`、`mean_net_return`、`max_drawdown` 等字段，就可能让 proxy PnL 伪装成 formal backtest metrics。

## 目标

`csf_backtest_ready` 的 formal gate 必须只接受来自真实可交易收益源的 metrics。任何来自 signal/factor panel 的 proxy return、`mom_ret` 或 signal-derived PnL，只能作为 diagnostic 信息存在，不能进入 formal summary、gate table、review pass 或下一阶段 handoff。

本设计解决治理与 runtime 约束问题，不直接修复某条 live lineage 的 stage-local program。

## 非目标

- 不在 QROS 仓库内实现完整交易所级撮合引擎。
- 不把所有 diagnostic proxy 计算从研究过程中彻底删除。
- 不因为 stage-local backtest 代码错误就默认开 child lineage。
- 不改变 mandate、factor role、neutralization policy 或 research hypothesis 的含义。

## 核心语义

`csf_backtest_ready` 新增硬规则：

- formal backtest metrics 必须来自真实可交易 return source。
- proxy PnL 可以存在于 diagnostic artifact，但不得进入 formal gate metrics。
- 如果 formal backtest 使用 proxy PnL，stage review 必须 blocking，不能进入 `holdout_validation`。

允许的 formal return 来源包括：

- 独立 market price path，例如 close、open、mark price、index price、OHLCV 或 mid/mark return。
- 可复现 execution accounting，例如 rebalance ledger、position weights、execution price、fee、slippage、funding。
- 带 provenance 的 tradable return column，且能追溯到 data-ready market data 或 execution ledger。

禁止作为 formal PnL 来源的包括：

- `mom_ret`。
- factor score、rank score、neutralized factor。
- signal panel 或 factor panel 中派生出的收益替代列。
- 没有独立 market data provenance 的任意 `return` 字段。
- 只适合诊断、但缺少成交时点、持仓、价格路径和成本约束的收益估算。

## Lineage 与 Failure 语义

发现 proxy PnL 后，优先判定为 stage artifact invalidation：

- 如果下游还没有冻结，修复同一个 `csf_backtest_ready` stage 并重跑。
- 如果错误结果已经被下游 freeze 并依赖，进入 failure handling 或 lineage change control。
- 只有需要改变 mandate 路线、factor role、neutralization policy 或 research hypothesis 时，才开 child lineage。

这避免把普通 stage-local backtest 实现错误扩大成不必要的 lineage 分叉。

## Artifact Contract 设计

在 `csf_backtest_ready` formal artifacts 中新增机器可读 provenance artifact：

```yaml
return_accounting_provenance.yaml
```

建议字段：

```yaml
return_source:
  source_type: market_price | execution_ledger | mark_price | ohlcv | funding_adjusted_price
  input_paths:
    - outputs/.../shared_feature_base/market_panel.parquet
  price_field: close
  return_field: forward_return_1d
  source_stage: data_ready
  is_signal_derived: false

accounting:
  rebalance_timing: next_bar | close_to_close | open_to_close
  holding_period: 1d
  fee_model: explicit | zero | fixed_bps | custom
  slippage_model: explicit | zero | fixed_bps | custom
  funding_model: explicit | zero | not_applicable
  missing_price_policy: drop_or_zero_weight | fail_closed
  gross_return_formula: sum(weight * tradable_forward_return)
  net_return_formula: gross_return - fees - slippage - funding

formal_outputs:
  portfolio_summary: portfolio_summary.parquet
  gate_table: csf_backtest_gate_table.csv
```

`portfolio_summary.parquet` 与 `csf_backtest_gate_table.csv` 必须能追溯到该 provenance。没有 provenance 时，formal backtest 不应通过。

## Runtime Validator 设计

`csf_backtest_ready` validator 增加四类检查。

### 1. Provenance 必须存在

`portfolio_summary` 和 `csf_backtest_gate_table` 不能孤立存在。validator 必须要求 formal 目录中存在 `return_accounting_provenance.yaml`，并验证字段完整。

### 2. 禁止来源类型

如果 provenance 中声明的 `source_type` 是以下任一值，直接 blocking：

- `signal_panel`
- `factor_panel`
- `diagnostic_proxy`
- `proxy_return`

`is_signal_derived` 必须为 `false`。

### 3. 禁止 formal return 字段

如果 formal return field、formula 或 accounting input columns 使用以下字段族，直接 blocking：

- `mom_ret`
- `factor_score`
- `rank_score`
- `neutralized`
- `signal`

检查应优先聚焦 `return_field`、formula 和 input column metadata，不应只因为路径里含有某个词就误杀合法文件。

### 4. 独立 market/execution 来源要求

`input_paths` 不能只来自 `signal_ready` 或 `train_freeze` 的 factor panel。formal backtest 至少需要引用以下来源之一：

- data-ready market/price panel。
- execution ledger。
- 明确声明为 tradable return source 的 independent return panel。

否则 metrics 只能归类为 diagnostic，不能过 formal gate。

## 代码扫描补充

validator 可以增加轻量 stage-local code scan，作为明显错误的补充阻断：

- 扫描 `program/.../backtest_ready/run_stage.py`。
- 如果出现 `weight * mom_ret`、`.select(["date", "asset", "mom_ret"])` 或等价的明显 proxy PnL 模式，给 blocking finding。

该扫描不是唯一真相，也不尝试做完整静态分析。它的目的只是捕捉当前已经出现的高风险模式。

## Author Skill 行为

`qros-csf-backtest-ready-author` 应改成“先确认真实 return source，再写 backtest program”：

- 生成 stage-local program 时不得从 signal/factor panel 取 `mom_ret` 作为 PnL。
- 必须从 `data_ready` 或明确 execution input 中选择 price/return source。
- 必须产出 `return_accounting_provenance.yaml`。
- 如果找不到真实可交易 return source，author 不得伪造 backtest，应产出 blocking handoff，说明缺少 tradable return source。
- proxy PnL 只能写入 diagnostic 文件，且命名必须明确带 `diagnostic` 或 `proxy`。

## Review Skill 行为

`qros-csf-backtest-ready-review` 应显式检查：

- `portfolio_summary` 与 gate table 是否引用 `return_accounting_provenance.yaml`。
- formal return field 是否来自 market/execution source。
- 是否存在 `mom_ret` 或 factor panel PnL。
- net return、drawdown、funding、fee/slippage 是否由 accounting 输出，而不是信号面板统计。

如果发现 proxy PnL，review verdict 必须 blocking，并引导到 stage failure/fix，而不是继续普通推进。

## 最小 Accounting Helper

新增一个轻量 runtime helper，目标是减少 stage-local program 临时手写 proxy PnL 的空间。helper 只提供基础 accounting，不承担完整回测引擎职责。

建议能力：

- 读取 weights/rebalance ledger。
- 读取 tradable return 或 market price panel。
- 按 contract 计算 gross return、fee、slippage、funding、net return、drawdown。
- 输出 `portfolio_summary.parquet`、daily return artifact 和 `return_accounting_provenance.yaml`。

stage-local program 可以调用 helper，也可以自行实现等价逻辑；但 validator 是最终 gate。

## 测试设计

新增或更新 focused tests，覆盖以下场景：

- 缺少 `return_accounting_provenance.yaml` 时，`csf_backtest_ready` validation 失败。
- `source_type: signal_panel`、`factor_panel`、`diagnostic_proxy` 或 `proxy_return` 时失败。
- `return_field: mom_ret` 时失败。
- `input_paths` 只引用 `signal_ready/factor_panel.parquet` 时失败。
- stage-local code 中出现 `weight * mom_ret` 时失败。
- 引用 data-ready market price 或合法 tradable return source 的 positive fixture 通过。

按仓库验证规则，实施阶段至少运行：

```bash
python -m pytest <focused csf_backtest_ready tests>
python runtime/scripts/run_verification_tier.py --tier smoke
```

因为该改动触及 stage gate semantics，实施阶段还应运行：

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

## 文档更新

实施时需要同步更新：

- CSF backtest ready artifact contract 文档。
- author/review skill 文案。
- 相关 SOP 或 guide 中关于 formal backtest metrics 的说明。
- 任何展示 `mean_net_return`、`max_drawdown` 作为 gate metric 的文档，补充 provenance 前提。

文档应明确区分：

- diagnostic proxy PnL。
- formal tradable backtest result。
- review closure。
- failure handling。

## 成功标准

实现完成后，Claude Code 再写出 `sum(weight * mom_ret)` 这类 backtest 时，应出现以下结果：

- formal contract 因缺少合法 provenance 失败。
- 如果 provenance 声明 proxy source，validator 失败。
- 如果代码中存在明显 proxy PnL 模式，code scan 给 blocking finding。
- review skill 明确要求 stage fix 或 failure handling。
- 系统不会默认开 child lineage，除非错误结果已经被下游冻结并依赖，或需要改变研究路线。
