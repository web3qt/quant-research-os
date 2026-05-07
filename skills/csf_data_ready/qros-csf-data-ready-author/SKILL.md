---
name: qros-csf-data-ready-author
description: Use when a reviewed mandate must be frozen into formal csf_data_ready artifacts through grouped interactive confirmation.
---

# CSF Data Ready Author

## Purpose

只在 `mandate review` closure 完成之后，把 `01_mandate` 冻结成正式 `02_csf_data_ready` 产物。

这里的 `csf_data_ready` 不是静默拼一份共享数据说明，而是交互式冻结 cross-sectional factor 路线必须复用的面板底座、准入语义和共享派生层。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `02_csf_data_ready` 需要交付的面板与覆盖证据，而不是把空目录、placeholder 文件或只有合同语义的说明文档当作 csf_data_ready 完成。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage csf_data_ready --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Artifact Contract Truth

`contracts/artifacts/csf_data_ready_artifacts.yaml` 是本阶段 formal artifact shape 的机器真值层。不得把 `SKILL.md` 当作字段真值；本 skill 只负责引导执行顺序、freeze confirmation、真实物化和校验动作。

执行要求：

- 必须先确认 freeze groups，再运行 lineage-local stage program 真实生成 formal artifacts
- 不得手写或自行扩展未在 `contracts/artifacts/csf_data_ready_artifacts.yaml` 声明的 formal artifact shape
- 完成 build 后必须运行 `qros-validate-stage --stage csf_data_ready`
- 进入 review 前必须运行 deterministic preflight，确认 artifact contract validation、semantic validation 和 upstream binding validation 都通过
- validator/preflight 不通过，不得进入 `csf_data_ready` review

## Required Inputs

- `01_mandate/mandate.md`
- `01_mandate/research_scope.md`
- `01_mandate/research_route.yaml`
- `01_mandate/time_split.json`
- `01_mandate/stage_completion_certificate.yaml`

## Required Outputs

- `panel_manifest.json`
- `asset_universe_membership.parquet`
- `eligibility_base_mask.parquet`
- `cross_section_coverage.parquet`
- `split_sample_adequacy_report.yaml`
- `shared_feature_base/`
- `asset_taxonomy_snapshot.parquet`（若 mandate 允许 `group_neutral`）
- `csf_data_contract.md`
- `csf_data_ready_gate_decision.md`
- `run_manifest.json`
- `rebuild_csf_data_ready.py` or equivalent program snapshot
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `panel_contract`
- `taxonomy_contract`
- `eligibility_contract`
- `shared_feature_base`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 mandate 产物
- 只能冻结 `research_route = cross_sectional_factor` 的面板底座
- 必须在当前 research repo 里真实生成 `date x asset` 面板、覆盖证据和共享派生层
- 必须先显式生成或刷新本 stage 的 lineage-local stage program，再执行 author build；QROS runtime 只负责校验和调用，不再后台静默生成默认 wrapper
- 该 stage program 必须是当前 lineage 在本 stage 里真实产生产物的程序，必须明确 formal artifacts 的生成路径、输入绑定和 replay 入口
- thin wrapper、framework builder shim、只转发共享 helper 的 skeleton 都不合法；`run_stage.py` 与关键 helper 不能只是把框架 builder 包一层
- 必须把本阶段真实使用的面板构建程序保存到 stage 目录，并登记到 `run_manifest.json`
- 不得产出任何时序主线措辞、预测 horizon 口径或单资产触发语义
- 必须在 `csf_data_ready` 根据已生成的 `cross_section_coverage.parquet` 和 mandate 的 `time_split.json` 生成 `split_sample_adequacy_report.yaml`；这是 data-ready 阶段的样本充足性门禁，不得回写或扩展 mandate 语义
- `split_sample_adequacy_report.yaml` 的 `sample_unit` 必须是 `cross_section_snapshot`；train/test/backtest/holdout 任一 split 低于 `minimum_required` 时，必须直接 FAIL，不得进入 review 或下游阶段
- 空目录、placeholder `parquet/csv/md`、只有口头或文档语义说明的产物都不能算正式完成
- 必须先回显 freeze draft；可以逐组确认，也可以一次展示全部 groups 后接受 `确认全部` 批量确认 groups
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_data_ready？`
- 不得静默修改 mandate 冻结的 universe 口径、时间边界或路由

- 若本阶段需要新增或修改代码，必须为真实产生产物的程序中的关键步骤、关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 语言规则统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外口径。

## Gate Discipline

### 面板主键必须显式
`panel_manifest.json` 必须按 `contracts/artifacts/csf_data_ready_artifacts.yaml` 明确写出 `panel_primary_key`、`cross_section_time_key`、`asset_key`、`shared_feature_outputs` 和 `coverage_floor_min_ratio`，不得把面板当作隐式时序表。

### 准入语义必须保留
`eligibility_base_mask.parquet` 只负责记录基础可研究掩码，不得混入具体因子定义。

### Split 样本充足性必须直接门禁
`split_sample_adequacy_report.yaml` 必须逐一写出 `split_sample_counts`、`minimum_required`、`adequacy` 和 `final_verdict`。每个 downstream split 的最低要求是 1 个 `cross_section_snapshot`；任一 split 不满足时，`final_verdict` 必须为 `FAIL`，author lane 必须停在 `csf_data_ready` 修复数据覆盖，不能推进 review。

### 分组中性化底座必须版本化
若后续允许 `neutralization_policy = group_neutral`，`asset_taxonomy_snapshot.parquet` 中的 `group_taxonomy_reference` 必须与 mandate 冻结值一致，且可追溯。

## Working Rules

1. 确认 `01_mandate/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `panel_contract`
3. 再收敛并确认 `taxonomy_contract`
4. 再收敛并确认 `eligibility_contract`
5. 再收敛并确认 `shared_feature_base`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 `panel_manifest.json`、覆盖证据和共享派生层
8. 输出一份 grouped csf_data_ready summary
9. 只有用户最终批准后，才生成正式 `02_csf_data_ready` artifacts
10. 生成 `run_manifest.json`，写清 runtime 版本、program_artifacts、replay_command 和输入根目录
11. 保存 `rebuild_csf_data_ready.py` 或等价 stage-local 程序快照
12. 生成 `split_sample_adequacy_report.yaml`，并确认 `final_verdict = PASS`
13. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
14. 运行 `qros-validate-stage --stage csf_data_ready`
15. 运行 deterministic preflight，确认 artifact contract validation、semantic validation 和 upstream binding validation 通过
16. 若当前只能产出 skeleton、placeholder 或 split 样本不足，必须明确判定为未完成，不得冒充 csf_data_ready 完成
