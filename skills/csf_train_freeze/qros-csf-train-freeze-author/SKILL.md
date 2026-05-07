---
name: qros-csf-train-freeze-author
description: Use when reviewed csf_signal_ready outputs must be frozen into formal csf_train_freeze artifacts through grouped interactive confirmation.
---

# CSF Train Freeze Author

## Purpose

只在 `csf_signal_ready review` closure 完成之后，把 `03_csf_signal_ready` 冻结成正式 `04_csf_train_freeze` 产物。

这里的 `csf_train_freeze` 不是给因子重新发明规则，而是把 cross-sectional factor 路线后续必须复用的预处理尺子、中性化尺子和分组尺子正式落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `04_csf_train_freeze` 需要交付的阈值、质量证据和参数台账，而不是把 placeholder 文件或只有合同语义的说明文档当作 csf_train_freeze 完成。

formal artifact shape 的真值层是 `contracts/artifacts/csf_train_freeze_artifacts.yaml`。本 skill 只负责执行顺序、确认边界和用户交互，不得手写或自行扩展 formal artifact shape。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage csf_train_freeze --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Required Inputs

- `03_csf_signal_ready/author/formal/factor_manifest.yaml`
- `03_csf_signal_ready/author/formal/component_factor_manifest.yaml`
- `03_csf_signal_ready/author/formal/factor_panel.parquet`
- `03_csf_signal_ready/author/formal/factor_coverage_report.parquet`
- `03_csf_signal_ready/author/formal/factor_group_context.parquet`
- `03_csf_signal_ready/author/formal/route_inheritance_contract.yaml`
- `03_csf_signal_ready/author/formal/factor_contract.md`
- `03_csf_signal_ready` review closure artifacts

## Required Outputs

- `csf_train_freeze.yaml`
- `train_factor_quality.parquet`
- `train_variant_ledger.csv`
- `train_variant_rejects.csv`
- `train_bucket_diagnostics.parquet`
- `train_neutralization_diagnostics.parquet`
- `csf_train_contract.md`
- `csf_train_freeze_gate_decision.md`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 6 组推进：

- `preprocess_contract`
- `neutralization_contract`
- `ranking_bucket_contract`
- `rebalance_contract`
- `search_governance_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 csf_signal_ready 产物
- 当前阶段只冻结 train 尺子，不替因子宣布赢家
- 必须在当前 research repo 里真实生成训练窗估计得到的预处理、中性化和分组尺子
- `csf_signal_ready` 已冻结的 factor expression / transform 轴不得在本阶段重新作为候选搜索轴；若变更这些轴，必须回到 `csf_signal_ready`
- 不得产出任何时序主线措辞、best_h、预测 horizon 或单资产命中率语义
- 必须先显式生成或刷新本 stage 的 lineage-local stage program，再执行 author build；QROS runtime 只负责校验和调用，不再后台静默生成默认 wrapper
- 该 stage program 必须是当前 lineage 在本 stage 里真实产生产物的程序，必须明确 formal artifacts 的生成路径、输入绑定和 replay 入口
- thin wrapper、framework builder shim、只转发共享 helper 的 skeleton 都不合法；`run_stage.py` 与关键 helper 不能只是把框架 builder 包一层
- 空目录、placeholder `parquet/csv/json/md`、只有说明文档都不能算正式完成
- 必须先回显 freeze draft；可以逐组确认，也可以一次展示全部 groups 后接受 `确认全部` 批量确认 groups
- 六组全部确认后，才允许最终 `是否按以上内容冻结 csf_train_freeze？`
- 不得借用 test/backtest 结果回写 train 尺子
- 必须先运行 `qros-validate-stage --stage csf_train_freeze --lineage-id <lineage_id>`
- 必须通过 csf_train_freeze semantic validator 与 deterministic review preflight
- validator / preflight 不通过，不得进入 `qros-csf-train-freeze-review` 或 `qros-review-cycle prepare`

- 若本阶段需要新增或修改代码，必须为真实产生产物的程序中的关键步骤、关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 语言规则统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外口径。

## Gate Discipline

### 严禁用下游结果回写 train 尺子
以下任何行为都必须触发 **CHILD LINEAGE**：
- 用 test/backtest 结果反推阈值
- 用下游表现选择分组切点
- 基于后续表现调整中性化条件

### 参数台账必须完整
`train_variant_ledger.csv` 中的所有候选组合都必须有可追溯身份，拒绝项也必须保留原因。

### Signal 轴治理必须显式
`csf_train_freeze.yaml` 的字段由 `contracts/artifacts/csf_train_freeze_artifacts.yaml` 定义。其中 search governance 必须显式写清：
- `frozen_signal_contract_reference`
- `train_governable_axes`
- `non_governable_axes_after_signal`
- `non_governable_axis_reject_rule`

如果某个 inherited variant 想改变 `fragility_score_transform`、`raw_factor_fields`、`derived_factor_fields` 或 `score_combination_formula`，不得继续伪装成 train 变体，必须进 reject ledger，并说明这需要重开 `csf_signal_ready`。

### 阈值语义分离
`csf_train_freeze.yaml` 必须使用 runtime-facing 合同分组：
- `preprocess_contract`
- `neutralization_contract`
- `ranking_bucket_contract`
- `rebalance_contract`
- `search_governance_contract`
- `delivery_contract`

## Working Rules

1. 确认 `03_csf_signal_ready` review closure 已完成
2. 先收敛并确认 `preprocess_contract`
3. 再收敛并确认 `neutralization_contract`
4. 再收敛并确认 `ranking_bucket_contract`
5. 再收敛并确认 `rebalance_contract`
6. 再确认 `search_governance_contract`
7. 最后确认 `delivery_contract`
8. 明确当前 research repo 中由谁负责真实生成 train 尺子、quality 证据、param ledger 和 reject ledger
9. 输出一份 grouped csf_train_freeze summary
10. 只有用户最终批准后，才生成正式 `04_csf_train_freeze` artifacts
11. 运行 `qros-validate-stage --stage csf_train_freeze`，再运行 csf_train_freeze semantic validator / review preflight
12. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
13. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_train_freeze 完成
