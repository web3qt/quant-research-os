---
name: qros-csf-test-evidence-author
description: Use when reviewed csf_train_freeze outputs must be frozen into formal csf_test_evidence artifacts through grouped interactive confirmation.
---

# CSF Test Evidence Author

## Purpose

只在 `csf_train_freeze review` closure 完成之后，把 `04_csf_train_freeze` 冻结成正式 `05_csf_test_evidence` 产物。

这里的 `csf_test_evidence` 不是静默挑一组好看的结果，而是交互式冻结 cross-sectional factor 路线的正式证据层。`standalone_alpha` 需要证明横截面排序能力，`regime_filter` / `combo_filter` 需要证明条件改善能力。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `05_csf_test_evidence` 需要交付的 test 统计结果、admissibility 结果和冻结对象，而不是把 placeholder 文件或只有合同语义的说明文档当作 csf_test_evidence 完成。

## Required Inputs

- 已通过 review closure 的 `04_csf_train_freeze/author/formal/*`
- `04_csf_train_freeze/author/formal/csf_train_freeze.yaml`
- `04_csf_train_freeze/author/formal/train_variant_ledger.csv`
- `01_mandate/author/formal/research_route.yaml`
- `contracts/artifacts/csf_test_evidence_artifacts.yaml`

## Required Outputs

- `rank_ic_timeseries.parquet`
- `rank_ic_summary.json`
- `bucket_returns.parquet`
- `monotonicity_report.json`
- `breadth_coverage_report.parquet`
- `subperiod_stability_report.json`
- `filter_condition_panel.parquet`
- `target_strategy_condition_compare.parquet`
- `gated_vs_ungated_summary.json`
- `csf_test_gate_table.csv`
- `csf_selected_variants_test.csv`
- `csf_test_contract.md`
- `csf_test_gate_decision.md`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `variant_contract`
- `evidence_contract`
- `audit_contract`
- `delivery_contract`

这些 group 的 runtime-facing 字段以 `runtime/tools/csf_test_evidence_runtime.py` 的 draft skeleton 和 `docs/guides/stage-freeze-group-field-guide.md` 为准。skill 只解释确认顺序，不再维护 formal artifact 字段真值。

## Mandatory Discipline

- 只能消费已经通过 review closure 的 csf_train_freeze 产物
- `standalone_alpha` 与 `regime_filter` / `combo_filter` 的证据语义必须分开冻结
- 必须在当前 research repo 里真实生成独立样本上的统计证据、admissibility 结果和冻结对象
- 不得手写或自行扩展 formal artifact shape；formal artifact shape 以 `contracts/artifacts/csf_test_evidence_artifacts.yaml` 为准
- 必须使用 runtime scaffold/build 物化 `05_csf_test_evidence/author/formal/*`
- build 后必须运行 `qros-validate-stage --stage csf_test_evidence`
- 进入 review 前必须通过 csf_test_evidence semantic validator / deterministic preflight
- 不得产出任何时序主线措辞、best_h、预测 horizon 或单资产命中率语义
- 必须先显式生成或刷新本 stage 的 lineage-local stage program，再执行 author build；QROS runtime 只负责校验和调用，不再后台静默生成默认 wrapper
- 该 stage program 必须是当前 lineage 在本 stage 里真实产生产物的程序，必须明确 formal artifacts 的生成路径、输入绑定和 replay 入口
- thin wrapper、framework builder shim、只转发共享 helper 的 skeleton 都不合法；`run_stage.py` 与关键 helper 不能只是把框架 builder 包一层
- 空目录、placeholder `parquet/csv/json/md`、只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_test_evidence？`
- 不得在 test 窗重估 train 尺子或回写下游组合规则

- 若本阶段需要新增或修改代码，必须为真实产生产物的程序中的关键步骤、关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 语言规则统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外口径。

## Gate Discipline

### standalone_alpha 与 filter/combo 必须分流
`standalone_alpha` 的正式 gate 关注：
- `Rank IC`
- `ICIR`
- bucket returns
- monotonicity
- breadth / coverage

`regime_filter` / `combo_filter` 的正式 gate 关注：
- gated vs ungated 对比
- 收益分布改善
- 回撤改善
- 尾部风险改善
- 覆盖率是否仍可接受

### Artifact shape 由 contract 决定
`rank_ic_summary.json`、`csf_test_gate_table.csv`、`csf_selected_variants_test.csv` 与所有 parquet columns 必须通过 `contracts/artifacts/csf_test_evidence_artifacts.yaml` 校验。agent 不得因为 skill 文本、聊天上下文或 reviewer 偏好新增 formal artifact 字段。

### 不得把 test 当 backtest
`csf_selected_variants_test.csv` 只允许冻结进入 backtest 的候选，不允许在本阶段宣布交易层胜利。

## Working Rules

1. 确认 `04_csf_train_freeze` 已有 review closure，且 formal artifacts 不是 placeholder
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `variant_contract`
4. 再收敛并确认 `evidence_contract`
5. 再收敛并确认 `audit_contract`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 test 统计证据、gate table 和 selected variants
8. 输出一份 grouped csf_test_evidence summary
9. 只有用户最终批准后，才生成正式 `05_csf_test_evidence` artifacts
10. 运行 `qros-validate-stage --stage csf_test_evidence`
11. 运行 csf_test_evidence semantic validator / deterministic preflight；validator/preflight 不通过，不得进入 `csf_test_evidence` review
12. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
13. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_test_evidence 完成
