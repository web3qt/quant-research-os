---
name: qros-paper-to-spec
description: Read a paper source and produce staged crypto perpetual paper_data_spec.yaml and paper_signal_spec.yaml artifacts with strict blocking questions.
---

# qros-paper-to-spec

## Purpose

`qros-paper-to-spec` 现在是 paper data-spec-first 入口。它先把论文、PDF、URL 或粘贴摘要整理成 crypto perpetual research fast-lane 的 `paper_data_spec.yaml`，再在 data spec valid 之后设计 `paper_signal_spec.yaml`。

这个入口独立于 `qros-research-session`，不进入 mandate / freeze / review / failure handling 的 heavy governance flow。

## Current outputs

第一阶段产出 data spec：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

第二阶段产出 signal spec：

```text
outputs/paper_to_spec/<paper_slug>/paper_signal_spec.yaml
```

当前不直接生成完整 strategy spec，不直接生成回测代码，也不进入 train-freeze / test-evidence / backtest spec。

旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

## Data Contract

生成 `paper_data_spec.yaml` 时必须遵守：

```text
contracts/paper_to_spec/paper_data_spec_contract.yaml
```

该 contract 是第一版 machine-readable 真值层，包含：

- required top-level fields
- core required data fields
- strict blocking fields
- requirement status / source enums
- crypto perpetual optional field blocks
- exchange profile defaults
- blocking question groups

## Signal Contract

生成 `paper_signal_spec.yaml` 时必须遵守：

```text
contracts/paper_to_spec/paper_signal_spec_contract.yaml
```

该 contract 是第二阶段 machine-readable 真值层，依赖已校验的 `paper_data_spec.yaml`，包含：

- data spec reference
- signal family
- prediction target
- feature inputs
- signal definition
- signal timing
- lookahead controls
- train/test policy
- portfolio mapping
- diagnostics
- signal-stage blocking question groups

## Execution protocol

下面分为 data execution protocol 和 signal execution protocol。

## Data Execution Protocol

收到 `$qros-paper-to-spec <pdf|url|summary>` 后，按以下顺序执行：

1. `source`：识别 `source_kind`、原始 locator、title、paper_slug。
2. `read source itself`：Codex 必须自己读取 PDF / URL / pasted summary，不能把读取责任推给 runtime wrapper。
3. `reading_coverage`：记录 PDF 总页数、成功提取页、覆盖章节、未提取页、低置信表格/公式和 data-relevant evidence。
4. `target_market`：默认面向 `crypto_perpetual`，使用 `generic_crypto_perp` 或研究员明确指定的 exchange profile。
5. `core_data_requirements`：逐项填写 `universe`、`price_bars`、`price_type`、`funding`、`fees_and_slippage`、`label_or_return_target`、`timestamp_alignment`、`data_availability`。
6. `triggered_optional_blocks`：只在论文或 data reasoning 触发时展开 derivatives positioning、liquidity microstructure、cross-exchange、external/onchain、sentiment/news。
7. `strict blocking`：任何 strict blocking field 为 `unknown`，或关键 evidence 不足，必须停止并问研究员。
8. `materialize`：在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml` 写入当前阶段产物。
9. `validate`：使用 deterministic validator 校验 `paper_data_spec.yaml`，若失败则修正 artifact 或把阻断问题返回研究员。

Validator 入口：

```text
python runtime/scripts/validate_paper_data_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、reading coverage 和 strict blocking unknown，不判断策略是否有效。

## Signal Execution Protocol

只有 `paper_data_spec.yaml` 通过 validator 后，才允许继续 signal spec：

1. `data_spec_reference`：记录 paper_slug、data spec path、validation_status、继承的 data fields。
2. `signal_research_intent`：用一句话说明论文核心策略思想要检验什么，不写成完整 strategy spec。
3. `core_signal_requirements`：逐项填写 `signal_family`、`prediction_target`、`feature_inputs`、`signal_definition`、`signal_timing`、`lookahead_controls`、`train_test_policy`、`portfolio_mapping`、`diagnostics`。
4. `triggered_optional_blocks`：只在论文或 signal reasoning 触发时展开 cross-sectional ranking、time-series thresholds、parameter search、machine learning model、regime filter、risk filter。
5. `train_test_policy`：必须明确是 `not_required_rule_based`、`required_parameter_fit`、`required_ml_model` 还是 `unknown`。
6. `strict blocking`：任何 signal strict blocking field 为 `unknown`，或无法区分论文原文与 agent 推断，必须停止并问研究员。
7. `materialize`：在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_signal_spec.yaml` 写入当前阶段产物。

## Requirement entry shape

每个 data requirement 使用同一结构：

```yaml
status: required | optional | not_needed | unknown
source: paper_stated | agent_inferred | researcher_required | exchange_profile_default
value: {}
evidence: []
blocking_if_unknown: true
question_if_unknown: ""
```

`paper_stated` 只能用于论文明确写出的 data 事实。crypto perpetual 迁移假设必须标为 `agent_inferred`，研究员确认项必须标为 `researcher_required`，profile 制度默认值必须标为 `exchange_profile_default`。

Signal spec 使用同一 entry shape，但 source enum 是：

```yaml
source: paper_stated | data_spec_inherited | agent_inferred | researcher_required
```

`data_spec_inherited` 只能用于从 valid `paper_data_spec.yaml` 继承的字段。train/test 相关结论如果论文没有明确说明，必须标为 `agent_inferred` 或 `researcher_required`，不能标为 `paper_stated`。

## Strict blocking fields

以下字段不清楚时必须停止，不得继续 signal / train / test / backtest：

- `universe`
- `price_bars`
- `price_type`
- `funding`
- `fees_and_slippage`
- `label_or_return_target`
- `timestamp_alignment`
- `data_availability`

Signal strict blocking fields：

- `signal_family`
- `prediction_target`
- `feature_inputs`
- `signal_definition`
- `signal_timing`
- `lookahead_controls`
- `train_test_policy`
- `portfolio_mapping`
- `diagnostics`

阻断问题最多聚合成 3 个问题，并按 contract 中的 `blocking_question_groups` 归类：

- `market_scope`
- `bar_and_price`
- `return_accounting`
- `source_coverage`

Signal 阻断问题按 contract 中的 `blocking_question_groups` 归类：

- `signal_identity`
- `prediction_and_inputs`
- `leakage_and_training`
- `portfolio_and_diagnostics`

## Boundaries

- 不直接生成完整 strategy spec。
- 不直接生成回测代码。
- 不把 validator failure 包装成 review verdict；这不是 `qros-research-session` review。
- 不把 crypto perpetual 迁移假设伪装成论文原文。
- 不把 train/test 是否需要留到 backtest 阶段才判断；必须在 `paper_signal_spec.yaml` 的 `train_test_policy` 里先分类。
- 不为所有 optional blocks 机械展开字段；只展开被 PDF 或 data reasoning 触发的块。
- 不保留与 `paper_data_spec_contract.yaml` 或 `paper_signal_spec_contract.yaml` 冲突的字段名或枚举。
