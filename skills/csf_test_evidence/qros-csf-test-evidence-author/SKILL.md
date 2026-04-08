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

- `04_csf_train_freeze/csf_train_freeze.yaml`
- `04_csf_train_freeze/train_variant_ledger.csv`
- `03_csf_signal_ready/factor_manifest.yaml`
- `02_csf_data_ready/asset_universe_membership.parquet`
- `04_csf_train_freeze/stage_completion_certificate.yaml`

## Required Outputs

- `rank_ic_timeseries.parquet`
- `bucket_returns.parquet`
- `admissibility_report.parquet`
- `factor_selection.csv`
- `factor_selection.parquet`
- `selected_factor_spec.json`
- `test_gate_table.csv`
- `test_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `formal_gate_contract`
- `admissibility_contract`
- `audit_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 csf_train_freeze 产物
- `standalone_alpha` 与 `regime_filter` / `combo_filter` 的证据语义必须分开冻结
- 必须在当前 research repo 里真实生成独立样本上的统计证据、admissibility 结果和冻结对象
- 不得产出任何时序主线措辞、best_h、预测 horizon 或单资产命中率语义
- 空目录、placeholder `parquet/csv/json/md`、只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_test_evidence？`
- 不得在 test 窗重估 train 尺子或回写下游组合规则

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

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

### selected_factor_spec 必须完整
`selected_factor_spec.json` 必须写清：
- `selected_factor_id`
- `factor_role`
- `factor_structure`
- `portfolio_expression`
- `neutralization_policy`

### 不得把 test 当 backtest
`factor_selection` 只允许冻结进入 backtest 的候选，不允许在本阶段宣布交易层胜利。

## Working Rules

1. 确认 `04_csf_train_freeze/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `formal_gate_contract`
4. 再收敛并确认 `admissibility_contract`
5. 再收敛并确认 `audit_contract`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 test 统计证据、admissibility 结果、factor selection 和 frozen spec
8. 输出一份 grouped csf_test_evidence summary
9. 只有用户最终批准后，才生成正式 `05_csf_test_evidence` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_test_evidence 完成
