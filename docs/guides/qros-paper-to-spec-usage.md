# QROS paper-to-spec 使用说明

## 当前状态

`qros-paper-to-spec` 是 paper data-spec-first 入口。旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

当前不要再把它当作“PDF 直接生成完整 strategy spec”或“PDF 直接生成回测代码”的入口。旧版 `paper -> strategy_spec -> baseline` fast-lane 已经下线。

第一阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

第二阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_signal_spec.yaml
```

第三阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_train_freeze_spec.yaml
```

这个入口不是 `qros-research-session` 的阶段入口，不进入 mandate / freeze / review / failure handling 的 heavy governance flow。

## Data Contract

`paper_data_spec.yaml` 必须遵守：

```text
contracts/paper_to_spec/paper_data_spec_contract.yaml
```

第一版 contract 锁定以下内容：

- required top-level fields
- core data requirements
- strict blocking fields
- requirement status / source enums
- crypto perpetual optional blocks
- exchange profile defaults
- blocking question groups

## Signal Contract

`paper_signal_spec.yaml` 必须遵守：

```text
contracts/paper_to_spec/paper_signal_spec_contract.yaml
```

第二阶段 contract 依赖已校验的 `paper_data_spec.yaml`，锁定 signal family、prediction target、feature inputs、signal definition、signal timing、lookahead controls、train/test policy、portfolio mapping 和 diagnostics。

## Train-Freeze Contract

`paper_train_freeze_spec.yaml` 必须遵守：

```text
contracts/paper_to_spec/paper_train_freeze_spec_contract.yaml
```

第三阶段 contract 依赖已校验的 `paper_signal_spec.yaml`，锁定 train/test mode、frozen signal definition、parameter freeze、train window、test window、split policy、selection policy、model training、refit policy、leakage controls 和 artifact identity。

## Data 执行流程

收到 `$qros-paper-to-spec <pdf|url|summary>` 后，Codex 应按这个顺序处理：

1. 识别 `source`：title、locator、source_kind、paper_slug。
2. 自己读取 PDF / URL / pasted summary，并记录 `reading_coverage`。
3. 确认 `target_market`，默认面向 `crypto_perpetual`，使用 `generic_crypto_perp` 或研究员指定的 exchange profile。
4. 填写 `core_data_requirements`：`universe`、`price_bars`、`price_type`、`funding`、`fees_and_slippage`、`label_or_return_target`、`timestamp_alignment`、`data_availability`。
5. 只在论文或 data reasoning 触发时填写 `triggered_optional_blocks`，包括 derivatives positioning、liquidity microstructure、cross-exchange、external/onchain、sentiment/news。
6. 如任何 strict blocking field 为 `unknown`，或 PDF 读取覆盖不足以支撑 data 结论，必须停止并问研究员。
7. 没有阻断项时，写入 `outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml`。
8. 使用 deterministic validator 校验 `paper_data_spec.yaml`。

Validator 入口：

```text
python runtime/scripts/validate_paper_data_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、reading coverage 和 strict blocking unknown，不判断策略是否有效。

## Signal 执行流程

只有 `paper_data_spec.yaml` 通过 validator 后，才允许继续 `paper_signal_spec.yaml`：

1. 写入 `data_spec_reference`：paper_slug、data spec path、validation_status、inherited_data_fields。
2. 写入 `signal_research_intent`：用一句话说明论文核心策略思想要检验什么。
3. 填写 `core_signal_requirements`：`signal_family`、`prediction_target`、`feature_inputs`、`signal_definition`、`signal_timing`、`lookahead_controls`、`train_test_policy`、`portfolio_mapping`、`diagnostics`。
4. 只在论文或 signal reasoning 触发时填写 `triggered_optional_blocks`，包括 cross-sectional ranking、time-series thresholds、parameter search、machine learning model、regime filter、risk filter。
5. `train_test_policy` 必须明确是 `not_required_rule_based`、`required_parameter_fit`、`required_ml_model` 还是 `unknown`。
6. 任一 signal strict blocking field 为 `unknown`，必须停止并问研究员。
7. 没有阻断项时，写入 `outputs/paper_to_spec/<paper_slug>/paper_signal_spec.yaml`。
8. 使用 deterministic validator 校验 `paper_signal_spec.yaml`。

Signal validator 入口：

```text
python runtime/scripts/validate_paper_signal_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_signal_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、data spec reference、strict blocking unknown、train/test policy 和 handoff shape，不判断策略是否能赚钱。

## Train-Freeze 执行流程

只有 `paper_signal_spec.yaml` 通过 validator 后，才允许继续 `paper_train_freeze_spec.yaml`：

1. 写入 `signal_spec_reference`：paper_slug、signal spec path、validation_status、inherited_signal_fields、inherited_train_test_policy。
2. 写入 `train_freeze_intent`：用一句话说明本阶段要冻结哪些信号、参数、窗口或模型状态。
3. 填写 `core_train_freeze_requirements`：`train_test_mode`、`frozen_signal_definition`、`parameter_freeze`、`train_window`、`test_window`、`split_policy`、`selection_policy`、`model_training`、`refit_policy`、`leakage_controls`、`artifact_identity`。
4. 只在 signal spec 或 train/freeze reasoning 触发时填写 `triggered_optional_blocks`，包括 rule-based freeze、parameter search freeze、ML training freeze、walk-forward freeze、regime-specific freeze。
5. `train_test_mode` 必须继承 signal spec 的 `train_test_policy`，并明确是 `not_required_rule_based`、`required_parameter_fit`、`required_ml_model` 还是 `unknown`。
6. 任一 train-freeze strict blocking field 为 `unknown`，或无法说明 train/test split 与 leakage controls，必须停止并问研究员。
7. 没有阻断项时，写入 `outputs/paper_to_spec/<paper_slug>/paper_train_freeze_spec.yaml`。
8. 使用 deterministic validator 校验 `paper_train_freeze_spec.yaml`。

Train-freeze validator 入口：

```text
python runtime/scripts/validate_paper_train_freeze_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_train_freeze_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、signal spec reference、inherited train/test policy consistency、strict blocking unknown、train/test mode 和 handoff shape，不判断策略是否能赚钱。

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

Train-freeze spec 使用同一 entry shape，但 source enum 是：

```yaml
source: signal_spec_inherited | paper_stated | agent_inferred | researcher_required
```

`signal_spec_inherited` 只能用于从 valid `paper_signal_spec.yaml` 继承的字段。参数冻结、训练窗口、选择指标、refit 规则和 artifact identity 如果论文没有明确说明，必须标为 `agent_inferred` 或 `researcher_required`。

## Strict blocking

以下字段不清楚时必须停止，不得继续 signal / train / test / backtest：

- `universe`
- `price_bars`
- `price_type`
- `funding`
- `fees_and_slippage`
- `label_or_return_target`
- `timestamp_alignment`
- `data_availability`

Signal 阶段以下字段不清楚时必须停止，不得继续 train / test / backtest：

- `signal_family`
- `prediction_target`
- `feature_inputs`
- `signal_definition`
- `signal_timing`
- `lookahead_controls`
- `train_test_policy`
- `portfolio_mapping`
- `diagnostics`

Train-freeze 阶段以下字段不清楚时必须停止，不得继续 test / backtest：

- `train_test_mode`
- `frozen_signal_definition`
- `parameter_freeze`
- `train_window`
- `test_window`
- `split_policy`
- `selection_policy`
- `model_training`
- `refit_policy`
- `leakage_controls`
- `artifact_identity`

阻断问题最多聚合成 3 个问题，并按 `blocking_question_groups` 归类：

- `market_scope`
- `bar_and_price`
- `return_accounting`
- `source_coverage`

Signal 阶段阻断问题按 `paper_signal_spec_contract.yaml` 中的 `blocking_question_groups` 归类：

- `signal_identity`
- `prediction_and_inputs`
- `leakage_and_training`
- `portfolio_and_diagnostics`

Train-freeze 阶段阻断问题按 `paper_train_freeze_spec_contract.yaml` 中的 `blocking_question_groups` 归类：

- `freeze_identity`
- `split_and_selection`
- `fit_and_refit`
- `leakage`

## 边界

- 不直接生成完整 strategy spec。
- 不直接生成回测代码。
- 不把 validator failure 包装成 review verdict；这不是 `qros-research-session` review。
- 不把 crypto perpetual 迁移假设伪装成论文原文。
- 不把 train/test 是否需要留到 backtest 阶段才判断；必须在 `paper_signal_spec.yaml` 的 `train_test_policy` 里先分类。
- 不把参数选择、模型训练、split policy 或 artifact identity 留到 backtest 阶段才定义；必须在 `paper_train_freeze_spec.yaml` 里冻结。
- 不为所有 optional blocks 机械展开字段；只展开被论文或 data reasoning 触发的块。
- 不保留与 `paper_data_spec_contract.yaml`、`paper_signal_spec_contract.yaml` 或 `paper_train_freeze_spec_contract.yaml` 冲突的字段名或枚举。

## 后续

`paper_train_freeze_spec.yaml` 稳定后，再继续设计 paper test-evidence spec 和 backtest spec。
