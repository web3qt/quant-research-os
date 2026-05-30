# qros-paper-to-spec / paper-data-spec 讨论记录

日期：2026-05-30

## 背景

围绕 `qros-paper-to-spec` 的能力边界、PDF 读取可信度、以及面向数字货币合约论文研究的 `paper-data-spec` 设计进行讨论。

## 已确认的问题

### 1. Codex 读取 PDF 的可审计性不足

当前 `qros-paper-to-spec` 合同要求 Codex 先读取 PDF / URL / 摘要，但现有 runtime wrapper 不负责抓取或解析 PDF，也不会记录读取覆盖率。

因此，除非 Codex 在执行时主动报告，否则研究员无法可靠知道：

- PDF 总页数是多少
- 成功读取了哪些页
- 哪些章节被覆盖
- 哪些表格、公式或附录没有被解析
- `paper_stated` 中每个关键结论对应哪些原文证据

结论：需要在后续设计中加入 reading coverage / evidence map，避免 Codex 只读摘要却表现成理解了全文。

### 2. 研究目标是论文思想到 crypto perps 回测

目标不是机械复现论文结论，而是：

> 抽取论文核心策略假设，改写成适用于数字货币合约市场的可检验回测 spec。

不建议直接从论文生成完整回测代码。原因是直接写代码会把大量关键假设埋进实现中，包括：

- universe
- bar 粒度
- price type
- funding
- fee / slippage
- label horizon
- train/test 切分
- 参数冻结
- 防未来函数

结论：应该走 spec-first，而不是 paper-to-code。

### 3. 阶段化研究流程是合理的

讨论得到的理想链路：

```text
PDF
 -> reading coverage
 -> paper_data_spec
 -> paper_signal_spec
 -> paper_train_freeze_spec
 -> paper_test_evidence_spec
 -> paper_backtest_spec
 -> implementation
 -> backtest evidence
```

每个阶段理论上可以由单独 skill 负责，但顶层入口仍保留 `qros-paper-to-spec`。

### 4. `qros-paper-to-spec` 的定位

不废弃现有 `qros-paper-to-spec`。

新的定位是：

- `qros-paper-to-spec` 作为顶层 orchestration skill
- 内部逐步调用细分阶段
- 第一阶段优先细化 `paper-data-spec`

第一期不进入 QROS 主研究流程，不绑定 `qros-research-session` 的 `data_ready`。

## paper-data-spec 设计方向

### 1. 定位

`paper-data-spec` 先作为 paper-to-spec fast-lane 的独立产物。

它不直接生成 `tss_data_ready` / `csf_data_ready`，也不进入 heavy governance flow。

职责是回答：

1. 这篇论文的核心策略思想需要哪些数据才能表达？
2. 迁移到 crypto perpetuals 后必须补哪些数据口径？
3. 哪些数据问题如果不问清楚，会改变策略定义、收益归因或回测有效性？

### 2. 目标市场

采用：

```text
generic crypto perpetuals + exchange_profile override
```

也就是核心字段保持通用，但允许使用 profile 覆盖默认值，例如：

- `generic_crypto_perp`
- `binance_usdt_perp`
- `okx_perp`
- `bybit_perp`

### 3. 阻断策略

采用严格阻断。

核心数据口径不清楚时必须停下来问研究员，不允许 agent 用默认值硬推。

核心阻断字段包括：

- universe
- price_bars
- price_type
- funding
- fees_and_slippage
- label_or_return_target
- timestamp_alignment
- data_availability

### 4. 字段库形态

采用分层字段库：

- core fields 必填
- optional blocks 按 PDF 内容触发
- 不为每篇论文展开所有 crypto perps 数据字段，避免 spec 臃肿

可选 block 包括：

- derivatives_positioning：open interest、long/short ratio、liquidations、basis/premium
- liquidity_microstructure：spread、depth、order book、capacity
- cross_exchange：跨交易所价差、lead-lag、套利信号
- external_or_onchain：链上、宏观、现货指数、外部市场数据
- sentiment_or_news：文本、社媒、公告、新闻

## 文件数量约束

用户明确要求不要有过多治理文件，保持最小必要文件。

因此第一期设计收敛为：

```text
contracts/paper_to_spec/paper_data_spec_contract.yaml
skills/core/qros-paper-to-spec/SKILL.md
docs/guides/qros-paper-to-spec-usage.md
```

第一期最多新增一个 contract 文件：

```text
contracts/paper_to_spec/paper_data_spec_contract.yaml
```

它同时承担：

- `paper_data_spec.yaml` 的 schema 要求
- crypto perps data field library
- blocking rules
- exchange profile 默认值

暂不拆分：

- `crypto_perp_data_field_library.yaml`
- `exchange_profiles/binance_usdt_perp.yaml`
- `paper_data_blocking_policy.yaml`

## 第一版 paper_data_spec.yaml 草案

```yaml
spec_version: v1

source:
  title:
  locator:
  source_kind:
  paper_slug:

reading_coverage:
  coverage_level: full | partial | low
  total_pages:
  extracted_pages:
  covered_sections:
  low_confidence_regions:
  unread_or_unextracted_pages:
  data_relevant_evidence:

target_market:
  market_type: crypto_perpetual
  exchange_profile: generic_crypto_perp | binance_usdt_perp | okx_perp | bybit_perp
  quote_currency:
  contract_settlement:
  timezone:

core_data_requirements:
  universe:
  price_bars:
  price_type:
  funding:
  fees_and_slippage:
  label_or_return_target:
  timestamp_alignment:
  data_availability:

triggered_optional_blocks:
  derivatives_positioning:
  liquidity_microstructure:
  cross_exchange:
  external_or_onchain:
  sentiment_or_news:

ambiguities:
  blocking:
  non_blocking:

implementation_handoff:
  raw_inputs:
  derived_inputs:
  expected_dataset_outputs:
  validation_checks:
```

每个 data requirement 使用统一结构：

```yaml
price_bars:
  status: required | optional | not_needed | unknown
  source: paper_stated | agent_inferred | researcher_required
  value:
    timeframe: 1h
    fields: [open, high, low, close, volume]
  evidence:
    - page: 6
      section: Data
      summary: Paper evaluates hourly returns.
  blocking_if_unknown: true
  question_if_unknown: What bar interval should be used for crypto perps adaptation?
```

## 当前设计决策

- 继续保留 `qros-paper-to-spec` 作为用户入口。
- 第一阶段优先细化 `paper-data-spec`。
- `paper-data-spec` 是 fast-lane 独立产物，不直接进入 QROS 主流程。
- 采用 generic crypto perpetuals + exchange profile override。
- 对核心数据字段采用严格阻断。
- 使用分层字段库。
- 第一版保持文件数量最小化，最多新增一个 contract 文件。

