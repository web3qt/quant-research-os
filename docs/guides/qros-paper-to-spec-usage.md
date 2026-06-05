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

第四阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_test_evidence_spec.yaml
```

第五阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_backtest_spec.yaml
```

第六阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_backtest_implementation_spec.yaml
```

post-spec implementation handoff 是显式 opt-in。只有 requested PaperSpec chain 全部 valid 后，agent 才能询问研究员是否要从 specs 自动进入 active research repo 实现；研究员回答后可产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_auto_implementation_handoff.yaml
```

这个入口不是 `qros-research-session` 的阶段入口，不进入 mandate / freeze / review / failure handling 的 heavy governance flow。

## XML Field Guides

XML field guide 是 PaperSpec / `qros-paper-to-spec` 的 stage-specific semantic aids：它们用中文解释当前阶段字段含义、填写边界、常见错误和阻断提问方式，让 agent 更稳定地生成对应的 YAML spec。

生成某一阶段 spec 时，agent 必须 load only / 只读取当前阶段的 XML guide，不得为了当前阶段预先加载其他阶段 guide：

```text
contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_auto_implementation_handoff.fields.xml
```

XML guides 只是语义辅助，不是正式 artifact，不是 validator。YAML contract remains canonical。正式 artifact 仍然是 `paper_*_spec.yaml`。

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

第三阶段 contract 依赖已校验的 `paper_signal_spec.yaml`，锁定 train/test mode、frozen signal definition、parameter freeze、train window、test window、split policy、selection policy、calibration state、recalibration policy、leakage controls 和 artifact identity。这里的 Train 指传统量化里的样本内定尺、定参、选择规则冻结。

## Test-Evidence Contract

`paper_test_evidence_spec.yaml` 必须遵守：

```text
contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml
```

第四阶段 contract 依赖已校验的 `paper_train_freeze_spec.yaml`，锁定 test window、frozen artifact binding、signal diagnostics、performance diagnostics、rule-based evidence、parameter-calibration evidence、no-retune attestation、test result usage policy、provenance 和 evidence identity。

## Backtest Contract

`paper_backtest_spec.yaml` 必须遵守：

```text
contracts/paper_to_spec/paper_backtest_spec_contract.yaml
```

第五阶段 contract 依赖已校验的 `paper_test_evidence_spec.yaml`，锁定 backtest scope、frozen artifact binding、market assumptions、portfolio construction、position sizing、execution assumptions、fees/slippage/funding、risk controls、required metrics、pass/fail gate、reproducibility、provenance 和 implementation handoff plan。

## Backtest Implementation Contract

`paper_backtest_implementation_spec.yaml` 必须遵守：

```text
contracts/paper_to_spec/paper_backtest_implementation_spec_contract.yaml
```

第六阶段 contract 依赖已校验的 `paper_backtest_spec.yaml`，锁定 active research repo boundary、target stage program、backtest entrypoint、input artifacts、frozen config binding、data access plan、output artifacts、execution manifest、validation checks、no-retune controls 和 reproducibility controls。

## Auto Implementation Handoff Contract

`paper_auto_implementation_handoff.yaml` 必须遵守：

```text
contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml
```

该 handoff 依赖已校验的 `paper_backtest_implementation_spec.yaml`，锁定 paper spec chain validation state、implementation decision、data readiness brief、researcher data response、agent acquisition plan、acquisition provenance、active repo boundary 和 allowed next action。

当研究员显式同意实现且 required data 已由研究员提供并验证，或 agent acquisition 已获批并成功完成后，允许的实现下一步是生成 active repo 内的完整 PaperSpec 轻量实现链：

```text
program/data
program/signal
program/train_freeze
program/test_evidence
program/backtest
```

这一步对应 `allowed_next_action=generate_active_repo_paperspec_chain_scaffold`，不是只生成 backtest scaffold，也不是进入 `qros-research-session` 的 formal stage closure。

## Data 执行流程

收到 `$qros-paper-to-spec <pdf|url|summary>` 后，Codex 应按这个顺序处理：

1. 读取 XML field guide：只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml`，只作为字段语义辅助；validation 仍使用 `contracts/paper_to_spec/paper_data_spec_contract.yaml`。
2. 识别 `source`：title、locator、source_kind、paper_slug。
3. 自己读取 PDF / URL / pasted summary，并记录 `reading_coverage`。
4. 确认 `target_market`，默认面向 `crypto_perpetual`，使用 `generic_crypto_perp` 或研究员指定的 exchange profile。
5. 填写 `core_data_requirements`：`universe`、`price_bars`、`price_type`、`funding`、`fees_and_slippage`、`label_or_return_target`、`timestamp_alignment`、`data_availability`。
6. 只在论文或 data reasoning 触发时填写 `triggered_optional_blocks`，包括 derivatives positioning、liquidity microstructure、cross-exchange、external/onchain、sentiment/news。
7. 如任何 strict blocking field 为 `unknown`，或 PDF 读取覆盖不足以支撑 data 结论，必须停止并问研究员。
8. 没有阻断项时，在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml` 写入当前阶段产物，不写入 QROS framework repo。
9. 使用 deterministic validator 校验 `paper_data_spec.yaml`。

Validator 入口：

```text
python runtime/scripts/validate_paper_data_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、reading coverage 和 strict blocking unknown，不判断策略是否有效。

## Signal 执行流程

只有 `paper_data_spec.yaml` 通过 validator 后，才允许继续 `paper_signal_spec.yaml`：

1. 读取 XML field guide：只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml`，只作为字段语义辅助；validation 仍使用 `contracts/paper_to_spec/paper_signal_spec_contract.yaml`。
2. 写入 `data_spec_reference`：paper_slug、data spec path、validation_status、inherited_data_fields。
3. 写入 `signal_research_intent`：用一句话说明论文核心策略思想要检验什么。
4. 填写 `core_signal_requirements`：`signal_family`、`prediction_target`、`feature_inputs`、`signal_definition`、`signal_timing`、`lookahead_controls`、`train_test_policy`、`portfolio_mapping`、`diagnostics`。
5. 只在论文或 signal reasoning 触发时填写 `triggered_optional_blocks`，包括 cross-sectional ranking、time-series thresholds、parameter calibration、regime filter、risk filter。
6. `train_test_policy` 必须明确是 `not_required_rule_based`、`required_parameter_calibration` 还是 `unknown`。
7. 任一 signal strict blocking field 为 `unknown`，必须停止并问研究员。
8. 没有阻断项时，在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_signal_spec.yaml` 写入当前阶段产物，不写入 QROS framework repo。
9. 使用 deterministic validator 校验 `paper_signal_spec.yaml`。

Signal validator 入口：

```text
python runtime/scripts/validate_paper_signal_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_signal_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、data spec reference、strict blocking unknown、train/test policy 和 handoff shape，不判断策略是否能赚钱。

## Train-Freeze 执行流程

只有 `paper_signal_spec.yaml` 通过 validator 后，才允许继续 `paper_train_freeze_spec.yaml`：

1. 读取 XML field guide：只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml`，只作为字段语义辅助；validation 仍使用 `contracts/paper_to_spec/paper_train_freeze_spec_contract.yaml`。
2. 写入 `signal_spec_reference`：paper_slug、signal spec path、validation_status、inherited_signal_fields、inherited_train_test_policy。
3. 写入 `train_freeze_intent`：用一句话说明本阶段要冻结哪些信号、参数、定尺窗口、选择规则或定尺状态。
4. 填写 `core_train_freeze_requirements`：`train_test_mode`、`frozen_signal_definition`、`parameter_freeze`、`train_window`、`test_window`、`split_policy`、`selection_policy`、`calibration_state`、`recalibration_policy`、`leakage_controls`、`artifact_identity`。
5. 只在 signal spec 或 train/freeze reasoning 触发时填写 `triggered_optional_blocks`，包括 rule-based freeze、parameter calibration freeze、walk-forward freeze、regime-specific freeze。
6. `train_test_mode` 必须继承 signal spec 的 `train_test_policy`，并明确是 `not_required_rule_based`、`required_parameter_calibration` 还是 `unknown`。
7. 任一 train-freeze strict blocking field 为 `unknown`，或无法说明 train/test split 与 leakage controls，必须停止并问研究员。
8. 没有阻断项时，在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_train_freeze_spec.yaml` 写入当前阶段产物，不写入 QROS framework repo。
9. 使用 deterministic validator 校验 `paper_train_freeze_spec.yaml`。

Train-freeze validator 入口：

```text
python runtime/scripts/validate_paper_train_freeze_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_train_freeze_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、signal spec reference、inherited train/test policy consistency、strict blocking unknown、train/test mode 和 handoff shape，不判断策略是否能赚钱。

## Test-Evidence 执行流程

只有 `paper_train_freeze_spec.yaml` 通过 validator 后，才允许继续 `paper_test_evidence_spec.yaml`：

1. 读取 XML field guide：只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml`，只作为字段语义辅助；validation 仍使用 `contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml`。
2. 写入 `train_freeze_spec_reference`：paper_slug、train-freeze spec path、validation_status、inherited_freeze_fields、inherited_artifact_identity。
3. 写入 `test_evidence_intent`：用一句话说明本阶段要生成哪些冻结后测试证据，以及这些证据不能用于反向调参。
4. 填写 `core_test_evidence_requirements`：`test_window`、`frozen_artifact_binding`、`signal_diagnostics`、`performance_diagnostics`、`rule_based_evidence`、`parameter_calibration_evidence`、`no_retune_attestation`、`test_result_usage_policy`、`provenance`、`evidence_identity`。
5. 只在 train-freeze spec 或 evidence reasoning 触发时填写 `triggered_optional_blocks`，包括 rule-based test evidence、parameter-calibration test evidence、cost sensitivity evidence、robustness evidence、failure-case evidence。
6. `no_retune_attestation` 必须说明 test evidence 不得修改 frozen parameters、calibration state、signal formula 或 artifact identity。
7. `test_result_usage_policy` 必须说明 test 结果只能用于 diagnose / fail-or-continue，不允许变成 holdout 前再调参。
8. 任一 test-evidence strict blocking field 为 `unknown`，或无法绑定 frozen artifact，必须停止并问研究员。
9. 没有阻断项时，在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_test_evidence_spec.yaml` 写入当前阶段产物，不写入 QROS framework repo。
10. 使用 deterministic validator 校验 `paper_test_evidence_spec.yaml`。

Test-evidence validator 入口：

```text
python runtime/scripts/validate_paper_test_evidence_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_test_evidence_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、train-freeze spec reference、strict blocking unknown、no-retune attestation、test result usage policy 和 handoff shape，不判断策略是否能赚钱。

## Backtest 执行流程

只有 `paper_test_evidence_spec.yaml` 通过 validator 后，才允许继续 `paper_backtest_spec.yaml`：

1. 读取 XML field guide：只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml`，只作为字段语义辅助；validation 仍使用 `contracts/paper_to_spec/paper_backtest_spec_contract.yaml`。
2. 写入 `test_evidence_spec_reference`：paper_slug、test-evidence spec path、validation_status、inherited_evidence_fields、inherited_evidence_identity。
3. 写入 `backtest_intent`：用一句话说明本阶段要把冻结后的信号、证据和市场假设整理成可实现的回测需求，不写回测代码。
4. 填写 `core_backtest_requirements`：`backtest_scope`、`frozen_artifact_binding`、`market_assumptions`、`portfolio_construction`、`position_sizing`、`execution_assumptions`、`fees_slippage_funding`、`risk_controls`、`required_metrics`、`pass_fail_gate`、`reproducibility`、`provenance`、`implementation_handoff_plan`。
5. 只在 test-evidence spec 或 backtest reasoning 触发时填写 `triggered_optional_blocks`，包括 long-short portfolio、long-only/flat portfolio、leverage and margin、capacity and turnover、funding accounting、cost sensitivity。
6. `pass_fail_gate` 必须说明回测如何判定是否可继续实现，不能把 backtest 结果变成参数重调入口。
7. `implementation_handoff_plan` 必须说明 active research repo 后续要实现的文件、模块、输出和验证检查，但本 skill 不直接生成回测代码。
8. 任一 backtest strict blocking field 为 `unknown`，或无法绑定 frozen artifact / evidence identity，必须停止并问研究员。
9. 没有阻断项时，在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_backtest_spec.yaml` 写入当前阶段产物，不写入 QROS framework repo。
10. 使用 deterministic validator 校验 `paper_backtest_spec.yaml`。

Backtest validator 入口：

```text
python runtime/scripts/validate_paper_backtest_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_backtest_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、test-evidence spec reference、strict blocking unknown、pass/fail gate 是否禁止 retune，以及 handoff shape，不判断策略是否能赚钱。

## Backtest Implementation 执行流程

只有 `paper_backtest_spec.yaml` 通过 validator 后，才允许继续 `paper_backtest_implementation_spec.yaml`：

1. 读取 XML field guide：只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml`，只作为字段语义辅助；validation 仍使用 `contracts/paper_to_spec/paper_backtest_implementation_spec_contract.yaml`。
2. 写入 `backtest_spec_reference`：paper_slug、backtest spec path、validation_status、inherited_backtest_fields、inherited_backtest_identity。
3. 写入 `implementation_intent`：用一句话说明本阶段要把回测需求转成 active research repo 的实现计划，不生成真实回测代码。
4. 填写 `core_implementation_requirements`：`active_research_repo_boundary`、`target_stage_program`、`backtest_entrypoint`、`input_artifacts`、`frozen_config_binding`、`data_access_plan`、`output_artifacts`、`execution_manifest`、`validation_checks`、`no_retune_controls`、`reproducibility_controls`。
5. 只在 backtest spec 或实现 reasoning 触发时填写 `triggered_optional_blocks`，包括 vectorbt engine、backtrader engine、custom engine、data materialization、performance report。
6. `active_research_repo_boundary` 必须说明实现写入 active research repo，而不是 QROS framework repo。
7. `no_retune_controls` 必须说明实现不得修改 frozen signal、参数、定尺状态或 selection policy。
8. 任一 implementation strict blocking field 为 `unknown`，或无法说明 active repo 路径 / frozen binding / outputs / validation checks，必须停止并问研究员。
9. 没有阻断项时，在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_backtest_implementation_spec.yaml` 写入当前阶段产物，不写入 QROS framework repo。
10. 使用 deterministic validator 校验 `paper_backtest_implementation_spec.yaml`。

Backtest implementation validator 入口：

```text
python runtime/scripts/validate_paper_backtest_implementation_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_backtest_implementation_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、backtest spec reference、strict blocking unknown、active research repo boundary、no-retune controls 和 handoff shape，不生成 active repo scaffold。

## Post-Spec Implementation Handoff 执行流程

只有 requested PaperSpec chain 全部通过 deterministic validator 后，才允许进入 post-spec implementation handoff：

1. 明确询问研究员是否要 QROS 根据已验证 specs 在 active research repo 中自动实现。未回答或回答 declined 时，停止在 specs 之后，不生成代码、不下载数据、不写 live lineage artifact。
2. 读取 `contracts/paper_to_spec/field_guides/paper_auto_implementation_handoff.fields.xml`，只作为字段语义辅助；validation 仍使用 `contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml`。
3. 写入 `paper_spec_chain`：六个上游 specs 的 path、validation_status、digest；任一 validation_status 不是 `valid` 时不得继续实现。
4. 先产出 `data_readiness_brief`：required data、optional data、market scope、symbol universe、time range、cadence、fields、expected format、source constraints、provenance requirements 和 missing-data policy。
5. 询问 `researcher_data_response`：研究员能否提供 required datasets。能提供时，收集 paths、snapshots、credentials 或 access instructions，并先验证用户提供的数据。
6. 只有研究员明确 `cannot_provide` required datasets 时，才允许提出 `agent_acquisition_plan`。
7. agent acquisition plan 必须包含 source、symbols、time_range、fields、command、storage_target、expected_artifacts、limitations 和 approval；未获批准不得下载、物化或声称数据可用。
8. 数据就绪后，若继续实现，`allowed_next_action` 必须使用 `generate_active_repo_paperspec_chain_scaffold`，并生成 data、signal、train_freeze、test_evidence、backtest 五段轻量实现程序；不得用 backtest-only scaffold 代替完整 PaperSpec implementation chain。
9. `active_repo_boundary` 必须确认 handoff、数据、scaffold 或实现输出写入 active research repo；目标若是 QROS framework repo，必须阻塞并询问 active repo target。
10. 在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_auto_implementation_handoff.yaml` 写入 handoff artifact。
11. 使用 deterministic validator 校验 `paper_auto_implementation_handoff.yaml`。

Handoff validator 入口：

```text
python runtime/scripts/validate_paper_auto_implementation_handoff.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_auto_implementation_handoff.yaml
```

该 validator 只检查 handoff contract shape、上游 spec chain valid、implementation opt-in、data readiness blocking gaps、researcher data response、agent acquisition approval、active repo boundary 和 allowed next action，不判断策略是否有效，不宣称 QROS governance stage 完成。

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

`signal_spec_inherited` 只能用于从 valid `paper_signal_spec.yaml` 继承的字段。参数冻结、定尺窗口、选择指标、recalibration 规则和 artifact identity 如果论文没有明确说明，必须标为 `agent_inferred` 或 `researcher_required`。

Test-evidence spec 使用同一 entry shape，但 source enum 是：

```yaml
source: train_freeze_spec_inherited | paper_stated | agent_inferred | researcher_required
```

`train_freeze_spec_inherited` 只能用于从 valid `paper_train_freeze_spec.yaml` 继承的字段。test diagnostics、no-retune attestation、provenance 和 evidence identity 如果论文没有明确说明，必须标为 `agent_inferred` 或 `researcher_required`。

Backtest spec 使用同一 entry shape，但 source enum 是：

```yaml
source: test_evidence_spec_inherited | train_freeze_spec_inherited | paper_stated | agent_inferred | researcher_required
```

`test_evidence_spec_inherited` 只能用于从 valid `paper_test_evidence_spec.yaml` 继承的字段。portfolio construction、execution assumptions、fees/slippage/funding、risk controls、pass/fail gate 和 implementation handoff plan 如果论文没有明确说明，必须标为 `agent_inferred` 或 `researcher_required`。

Backtest implementation spec 使用同一 entry shape，但 source enum 是：

```yaml
source: backtest_spec_inherited | paper_stated | agent_inferred | researcher_required | repo_policy_required
```

`backtest_spec_inherited` 只能用于从 valid `paper_backtest_spec.yaml` 继承的字段。active repo boundary、stage program、entrypoint、execution manifest、validation checks、no-retune controls 和 reproducibility controls 必须来自 agent/researcher/repo policy 明确选择，不能伪装成论文原文。

Auto implementation handoff 不使用 requirement entry shape。它是 post-spec 决策和数据就绪 artifact，核心字段是 `implementation_decision`、`data_readiness_brief`、`researcher_data_response`、`agent_acquisition_plan`、`acquisition_provenance`、`active_repo_boundary` 和 `allowed_next_action`。

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
- `calibration_state`
- `recalibration_policy`
- `leakage_controls`
- `artifact_identity`

Test-evidence 阶段以下字段不清楚时必须停止，不得继续 backtest：

- `test_window`
- `frozen_artifact_binding`
- `signal_diagnostics`
- `performance_diagnostics`
- `no_retune_attestation`
- `test_result_usage_policy`
- `provenance`
- `evidence_identity`

Backtest 阶段以下字段不清楚时必须停止，不得继续实现回测：

- `backtest_scope`
- `frozen_artifact_binding`
- `market_assumptions`
- `portfolio_construction`
- `position_sizing`
- `execution_assumptions`
- `fees_slippage_funding`
- `risk_controls`
- `required_metrics`
- `pass_fail_gate`
- `reproducibility`
- `provenance`
- `implementation_handoff_plan`

Backtest implementation 阶段以下字段不清楚时必须停止，不得生成 active repo scaffold：

- `active_research_repo_boundary`
- `target_stage_program`
- `backtest_entrypoint`
- `input_artifacts`
- `frozen_config_binding`
- `data_access_plan`
- `output_artifacts`
- `execution_manifest`
- `validation_checks`
- `no_retune_controls`
- `reproducibility_controls`

阻断问题最多聚合成 3 个问题，并按 `blocking_question_groups` 归类：

- `market_scope`
- `bar_and_price`
- `return_accounting`
- `source_coverage`

Signal 阶段阻断问题按 `paper_signal_spec_contract.yaml` 中的 `blocking_question_groups` 归类：

- `signal_identity`
- `prediction_and_inputs`
- `leakage_and_calibration`
- `portfolio_and_diagnostics`

Train-freeze 阶段阻断问题按 `paper_train_freeze_spec_contract.yaml` 中的 `blocking_question_groups` 归类：

- `freeze_identity`
- `split_and_selection`
- `calibration_and_recalibration`
- `leakage`

Test-evidence 阶段阻断问题按 `paper_test_evidence_spec_contract.yaml` 中的 `blocking_question_groups` 归类：

- `evidence_scope`
- `diagnostics`
- `no_retune`
- `provenance_identity`

Backtest 阶段阻断问题按 `paper_backtest_spec_contract.yaml` 中的 `blocking_question_groups` 归类：

- `scope_and_binding`
- `portfolio_and_execution`
- `accounting_and_risk`
- `evidence_and_reproducibility`

Backtest implementation 阶段阻断问题按 `paper_backtest_implementation_spec_contract.yaml` 中的 `blocking_question_groups` 归类：

- `repo_boundary`
- `execution_inputs`
- `outputs_and_validation`
- `controls`

Auto implementation handoff 阻断问题按 `paper_auto_implementation_handoff_contract.yaml` 中的 `blocking_question_groups` 归类：

- `implementation_consent`
- `data_readiness`
- `agent_acquisition`
- `repo_boundary`
- `next_action`

## 边界

- 不直接生成完整 strategy spec。
- 不在缺少 post-spec implementation opt-in 时生成回测代码、下载数据或创建 active repo scaffold。
- 不把 PaperSpec 实现简化成 backtest-only scaffold；实现链必须覆盖 data、signal、train_freeze、test_evidence 和 backtest。
- 不把 backtest implementation plan 写成 QROS framework repo 内的 live lineage 程序；真实实现属于 active research repo。
- 不把 `paper_auto_implementation_handoff.yaml` 写成 review closure、stage advancement 或 live research artifact 完成证明。
- 不在列出 data readiness brief 和询问研究员能否供数之前执行 agent data acquisition。
- 不在 agent acquisition plan 未获批准时下载、物化或声称数据可用。
- 不把 validator failure 包装成 review verdict；这不是 `qros-research-session` review。
- 不把 crypto perpetual 迁移假设伪装成论文原文。
- 不把 train/test 是否需要留到 backtest 阶段才判断；必须在 `paper_signal_spec.yaml` 的 `train_test_policy` 里先分类。
- 不把参数选择、定尺状态、split policy 或 artifact identity 留到 backtest 阶段才定义；必须在 `paper_train_freeze_spec.yaml` 里冻结。
- 不把 test evidence 用作 holdout 前调参入口；test 结果只能用于诊断、失败处理或是否继续的判断。
- 不把 backtest 结果用作调参入口；`paper_backtest_spec.yaml` 只能定义实现需求和 pass/fail gate。
- 不为所有 optional blocks 机械展开字段；只展开被论文或 data reasoning 触发的块。
- 不保留与 `paper_data_spec_contract.yaml`、`paper_signal_spec_contract.yaml`、`paper_train_freeze_spec_contract.yaml`、`paper_test_evidence_spec_contract.yaml`、`paper_backtest_spec_contract.yaml` 或 `paper_backtest_implementation_spec_contract.yaml` 冲突的字段名或枚举。

## 后续

`paper_auto_implementation_handoff.yaml` 稳定后，再继续设计 active repo scaffold 生成入口与验证。
