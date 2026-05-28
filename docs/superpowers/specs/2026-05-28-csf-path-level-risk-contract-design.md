# CSF 路径级风险诊断 Hard Contract 设计

## 背景

当前 `csf_backtest_ready` 与 `csf_holdout_validation` 已经覆盖组合可行性的最低闭环：成本前后收益、最大回撤、换手、容量、name-level concentration、holdout 方向匹配与退化对比。

但这套合同还没有把路径级交易诊断作为 formal hard contract。`portfolio_return_series.parquet`、equity curve、Sharpe、Calmar、profit factor、trade/day PnL ledger 等信息目前更接近 recommended diagnostics 或 gap-detect 语义。结果是 review 能看到平均收益和回撤，但难以机器级复核：

- 收益是否集中在少数日期。
- 回撤路径是否由日度净值序列支持。
- Sharpe、Calmar、profit factor 是否能从正式 return / PnL 序列复算。
- holdout 回撤退化来自日期集中、资产集中、成本侵蚀还是 regime shift。
- sparse-bucket days 下单名权重过高是否直接贡献了组合 PnL 风险。

这对 Binance USDT 永续、横截面 bucket 策略尤其重要。该类策略可能在平均净收益为正的同时存在高换手、稀疏持仓、单名集中和 holdout 回撤变深的问题。只看 summary metrics 不足以支撑严肃 review。

## 目标

把 CSF `06_csf_backtest_ready` 和 `07_csf_holdout_validation` 升级为路径级交易诊断合同。

两个阶段都必须产出同构的机器可读路径诊断产物：

- `portfolio_return_series.parquet`
- `equity_curve.parquet`
- `portfolio_pnl_ledger.parquet`
- `asset_pnl_ledger.parquet`
- `risk_adjusted_metrics.parquet`

这些产物成为 formal required artifacts。缺失、空文件、字段缺失、主键重复、variant 不一致、date 不可解析、关键数值不可解析，或汇总指标无法从原始序列复算时，`qros-validate-stage --stage csf_backtest_ready` 或 `qros-validate-stage --stage csf_holdout_validation` 必须失败。

本设计不新增风险指标表现阈值。Sharpe、Calmar、profit factor 可以很差，但必须真实、可复算、口径一致。现有 hard metric gates 继续保留：

- `csf_backtest_ready`: `mean_net_return > 0`
- `csf_holdout_validation`: `direction_match = true` 且 `holdout_mean_net_return > 0`

## 非目标

- 不在 QROS 框架仓内实现某条策略的真实回测程序。
- 不引入交易所级撮合引擎。
- 不把 Sharpe、Calmar 或 profit factor 变成新的机器表现阈值。
- 不改变 `mandate`、`factor_role`、`portfolio_expression`、`neutralization_policy` 或 route 语义。
- 不允许在 holdout 因新增诊断而重新调参、重新选 variant 或回写冻结字段。

## Artifact Contract 设计

`csf_backtest_ready` 与 `csf_holdout_validation` 新增同构 formal artifacts。Backtest 文件描述 backtest 窗口；holdout 文件描述 holdout 窗口。字段语义保持一致，方便 review 做同口径比较。

### portfolio_return_series.parquet

粒度：每个 `date × variant_id` 一行。

必需字段：

- `date`
- `variant_id`
- `gross_return`
- `net_return`
- `turnover`
- `cost`
- `asset_count`
- `max_name_weight`

用途：

- 记录正式组合日度或再平衡级收益序列。
- 作为 equity curve、volatility、Sharpe、Sortino、Calmar 的复算来源。
- 暴露稀疏日期、成本侵蚀和单名权重风险。

### equity_curve.parquet

粒度：每个 `date × variant_id` 一行。

必需字段：

- `date`
- `variant_id`
- `gross_equity`
- `net_equity`
- `drawdown`

用途：

- 固化正式净值路径。
- 支撑最大回撤与 Calmar 复算。
- 支撑 backtest 与 holdout 的路径级退化比较。

### portfolio_pnl_ledger.parquet

粒度：每个 `date × variant_id` 一行。

必需字段：

- `date`
- `variant_id`
- `gross_pnl`
- `cost`
- `net_pnl`
- `capital_base`
- `profit_loss_sign`

`profit_loss_sign` 允许值：

- `profit`
- `loss`
- `flat`

用途：

- 记录 portfolio-level PnL 台账。
- 支撑 profit factor 复算。
- 明确 `net_return` 与资金基数之间的关系。

### asset_pnl_ledger.parquet

粒度：每个 `date × variant_id × asset` 一行。

必需字段：

- `date`
- `variant_id`
- `asset`
- `weight`
- `side`
- `asset_return`
- `gross_pnl_contribution`
- `cost_contribution`
- `net_pnl_contribution`

用途：

- 支撑资产级归因。
- 检查 sparse-bucket days 与单名集中度。
- 复核资产贡献能否聚合到 portfolio PnL。

### risk_adjusted_metrics.parquet

粒度：每个 `variant_id` 一行。

必需字段：

- `variant_id`
- `annualized_return_365d`
- `annualized_return_252d`
- `volatility_365d`
- `volatility_252d`
- `sharpe_365d`
- `sharpe_252d`
- `sortino_365d`
- `sortino_252d`
- `calmar_365d`
- `calmar_252d`
- `profit_factor`
- `max_drawdown`
- `observation_count`

计算口径：

- 365 天是 crypto 永续主口径。
- 252 天是传统交易日参考口径。
- 风险指标默认基于 `net_return`。
- `max_drawdown` 基于 `net_equity` 或 `net_return` 复算。
- `profit_factor` 基于 `portfolio_pnl_ledger.net_pnl` 的正负加总复算。
- `capital_base` 可以是固定 `1.0` 或真实资金基数，但必须在 field dictionary 或 provenance 中说明。

## Runtime Validator 设计

CSF backtest / holdout semantic validator 增加 deterministic consistency checks。

### 基础结构检查

所有新增 parquet 必须满足：

- 文件存在。
- 可读取。
- 非空。
- 必需字段齐全。
- `date` 可解析并可排序。
- `variant_id` 属于本阶段 selected variants。
- 表内主键不重复。
- 数值字段可解析为有限数值，除非字段语义明确允许空值。

### Return 与 Equity 一致性

对每个 `variant_id`：

- `equity_curve.net_equity` 必须能由 `portfolio_return_series.net_return` 从初始净值 `1.0` 累乘复算。
- `equity_curve.gross_equity` 必须能由 `portfolio_return_series.gross_return` 从初始净值 `1.0` 累乘复算。
- `equity_curve.drawdown` 必须能从 `net_equity` 的历史高点复算。
- `risk_adjusted_metrics.max_drawdown` 必须与复算最大回撤一致。

### Portfolio Ledger 一致性

对每个 `date × variant_id`：

- `portfolio_pnl_ledger.net_pnl` 必须与 `portfolio_return_series.net_return × capital_base` 在容差内一致。
- `portfolio_pnl_ledger.gross_pnl` 必须与 `portfolio_return_series.gross_return × capital_base` 在容差内一致。
- `portfolio_pnl_ledger.cost` 必须与 `portfolio_return_series.cost` 在口径上保持一致。
- `profit_loss_sign` 必须由 `net_pnl` 决定：正为 `profit`，负为 `loss`，零为 `flat`。

### Asset Ledger 聚合一致性

对每个 `date × variant_id`：

- `asset_pnl_ledger.gross_pnl_contribution` 加总后必须等于 `portfolio_pnl_ledger.gross_pnl`。
- `asset_pnl_ledger.cost_contribution` 加总后必须等于 `portfolio_pnl_ledger.cost`。
- `asset_pnl_ledger.net_pnl_contribution` 加总后必须等于 `portfolio_pnl_ledger.net_pnl`。
- `weight` 聚合规则按 `portfolio_contract.yaml` 的 `portfolio_expression` 和 exposure rules 判断。

第一版至少应严格支持常见表达：

- `long_only_rank`: 权重和应接近 `1.0`，不得出现 short side。
- `short_only_rank`: 空头绝对权重和应接近 `1.0`，不得出现 long side。
- `long_short_market_neutral`: long 权重和与 short 绝对权重和应分别接近冻结规则。

无法由现有 contract 明确判断的表达，validator 应检查 PnL 聚合一致性，并要求 review 在 gate decision 中解释 weight/exposure 口径。

### Risk Metrics 复算一致性

对每个 `variant_id`：

- 从 `portfolio_return_series.net_return` 复算 `annualized_return_365d` 与 `annualized_return_252d`。
- 从 `portfolio_return_series.net_return` 复算 `volatility_365d` 与 `volatility_252d`。
- 从 `portfolio_return_series.net_return` 复算 `sharpe_365d` 与 `sharpe_252d`。
- 从负收益序列复算 `sortino_365d` 与 `sortino_252d`。
- 从 annualized return 与 max drawdown 复算 `calmar_365d` 与 `calmar_252d`。
- 从 `portfolio_pnl_ledger.net_pnl` 的正负加总复算 `profit_factor`。
- `observation_count` 必须等于 return series 有效观测数量。

validator 使用小容差比较 summary metrics 与复算结果。容差应集中定义，避免不同 runtime helper 各自写死。

### 表现阈值

新增风险指标不产生新的 hard performance threshold。

以下情况不因表现差而失败：

- `sharpe_365d <= 0`
- `calmar_365d <= 0`
- `profit_factor <= 1`
- `volatility` 很高
- `sortino` 很差

以下情况必须失败：

- 指标缺失。
- 指标不可复算。
- 原始序列与汇总表不一致。
- backtest 与 holdout 使用不同字段或不同计算口径却未声明。
- holdout 重新调参、重新选 variant 或改变 frozen portfolio contract。

## Diagnostics Runtime 设计

`runtime/tools/factor_diagnostics.py` 不再把 CSF backtest 的 Sharpe、Sortino、Calmar、profit factor 作为纯 gap-detect 指标。

变更后：

- `sharpe` 从 `risk_adjusted_metrics.parquet.sharpe_365d` 读取，252 口径作为附加 detail。
- `sortino` 从 `risk_adjusted_metrics.parquet.sortino_365d` 读取。
- `calmar` 从 `risk_adjusted_metrics.parquet.calmar_365d` 读取。
- `profit_factor` 从 `risk_adjusted_metrics.parquet.profit_factor` 读取。
- `alpha`、`beta` 仍可保持 recommended/gap-detect，除非后续另设 benchmark contract。

`contracts/diagnostics/csf_stage_diagnostic_profiles.yaml` 中，CSF backtest 的 risk-adjusted metrics 应从 recommended 升为 required。CSF holdout 应新增同构路径级诊断维度，用于读取 holdout risk metrics 和路径退化。

## Docs 与 Skills 设计

需要同步更新 active docs 与 skills，避免用户继续以为这些只是推荐诊断。

最小更新范围：

- `docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md`
- `docs/sop/main-flow/07_csf_holdout_validation_sop_cn.md`
- `docs/guides/qros-research-session-usage.md`
- `docs/guides/qros-factor-diagnostics.md`
- `skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md`
- `skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md`
- `skills/csf_holdout_validation/qros-csf-holdout-validation-author/SKILL.md`
- `skills/csf_holdout_validation/qros-csf-holdout-validation-review/SKILL.md`
- 如主入口 skill 直接列出 CSF formal outputs，也同步更新 `skills/core/qros-research-session/SKILL.md`

文档必须明确：

- 这些路径级 artifacts 是 hard contract。
- 365 天是 crypto 永续主口径，252 天是参考口径。
- 风险指标必须可由 formal return / PnL 序列复算。
- Sharpe、Calmar、profit factor 不新增 PASS 阈值。
- Holdout 与 backtest 必须同构输出，不能只做 compare summary。

## 测试设计

需要覆盖以下测试层。

### Contract Tests

更新：

- `tests/contracts/test_csf_backtest_ready_artifact_contract.py`
- `tests/contracts/test_csf_holdout_validation_artifact_contract.py`

验证新增 artifact 名称、required columns、json/yaml 字段路径和 unknown field policy。

### Runtime Artifact Validation Tests

更新 `tests/runtime/test_artifact_contract_runtime.py` 或相邻测试，确保 generic artifact contract runtime 能识别新增 parquet shapes。

### Semantic Validator Tests

更新或新增：

- `tests/runtime/test_csf_backtest_ready_semantic_validation.py`
- `tests/runtime/test_csf_holdout_validation_semantic_validation.py`

覆盖：

- 缺少新增 artifact 时失败。
- return/equity 不一致时失败。
- drawdown 复算不一致时失败。
- portfolio ledger 与 return series 不一致时失败。
- asset ledger 聚合不一致时失败。
- risk metrics 与复算结果不一致时失败。
- Sharpe/Calmar/profit factor 表现差但可复算时不因新增指标失败。

### Diagnostics Tests

更新：

- `tests/runtime/test_factor_diagnostics.py`

确保 Sharpe、Sortino、Calmar、profit factor 从 `risk_adjusted_metrics.parquet` 读取，而不是继续显示 missing gap。

### Docs Regression Tests

更新已有 docs tests，或新增针对 CSF backtest/holdout contract-first docs 的断言，确保 active SOP 和 usage guide 提到新增 hard artifacts 与 365/252 口径。

### Verification Commands

因为该变更触及 stage gate semantics、artifact contract、review/display 诊断口径，完成实现时必须运行：

- focused tests
- `python runtime/scripts/run_verification_tier.py --tier smoke`
- `python runtime/scripts/run_verification_tier.py --tier full-smoke`

## 实施顺序建议

1. 先更新 artifact contracts 与 contract tests。
2. 再更新 runtime semantic validators 和 focused failure/pass tests。
3. 再更新 diagnostics metric readers 和 diagnostics tests。
4. 最后更新 docs、skills 和 docs regression tests。
5. 运行 focused tests、smoke、full-smoke。

这个顺序能先锁定机器合同，再扩展 runtime 行为，最后同步解释层。

## Implementation Defaults

本设计已经固定以下决策：

- 使用 hard contract，而不是推荐输出。
- 同时强制原始序列和汇总指标表。
- 同时强制 portfolio-level ledger 和 asset-level ledger。
- Holdout 与 backtest 完全同构。
- 同时输出 365 和 252，365 是 crypto 主口径。
- 不新增 Sharpe、Calmar、profit factor 表现阈值。
- Runtime validator 必须做 deterministic consistency check。

为避免实现时出现多套口径，第一版采用以下默认值：

- 数值容差集中定义为 runtime 常量，默认绝对容差 `1e-9`、相对容差 `1e-6`。
- 年化收益采用简单年化：`mean(net_return) × annualization_days`。
- 波动率采用样本标准差，`ddof = 1`；有效观测数小于 2 时 volatility、Sharpe、Sortino、Calmar 必须显式写为 null 或 runtime 约定的不可计算哨兵值，并由 validator 接受该不可计算状态。
- Sharpe 使用零无风险利率：`annualized_return / annualized_volatility`。
- Sortino 使用零目标收益率，downside volatility 同样按 annualization days 年化。
- Calmar 使用 `annualized_return / abs(max_drawdown)`；最大回撤为 0 时必须显式写为 null 或不可计算哨兵值。
- Profit factor 使用 `sum(net_pnl > 0) / abs(sum(net_pnl < 0))`；无亏损且有盈利时必须显式写为 `inf` 或 runtime 约定的上限哨兵值，无盈利无亏损时写为 null 或不可计算哨兵值。
- `capital_base`、`gross_pnl`、`net_pnl`、`cost` 必须同单位。若 `capital_base = 1.0`，则 PnL ledger 是 normalized PnL；若使用真实资金基数，field dictionary 必须声明币种和单位。
- 第一版 exposure 校验严格覆盖 `long_only_rank`、`short_only_rank`、`long_short_market_neutral`；其他组合表达先执行 PnL 聚合一致性和 selected variant 检查，并要求 gate decision 显式解释 exposure 口径。
