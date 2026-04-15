---
name: qros-csf-data-ready-author
description: Use when a reviewed mandate must be frozen into formal csf_data_ready artifacts through grouped interactive confirmation.
---

# CSF Data Ready Author

## Purpose

只在 `mandate review` closure 完成之后，把 `01_mandate` 冻结成正式 `02_csf_data_ready` 产物。

这里的 `csf_data_ready` 不是静默拼一份共享数据说明，而是交互式冻结 cross-sectional factor 路线必须复用的面板底座、准入语义和共享派生层。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `02_csf_data_ready` 需要交付的面板与覆盖证据，而不是把空目录、placeholder 文件或只有合同语义的说明文档当作 csf_data_ready 完成。

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
- 必须把本阶段真实使用的面板构建程序保存到 stage 目录，并登记到 `run_manifest.json`
- 不得产出任何时序主线措辞、预测 horizon 口径或单资产触发语义
- 空目录、placeholder `parquet/csv/md`、只有口头或文档语义说明的产物都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_data_ready？`
- 不得静默修改 mandate 冻结的 universe 口径、时间边界或路由

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 语言规则统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外口径。

## Gate Discipline

### 面板主键必须显式
`panel_manifest.json` 必须明确写出 `date_key`、`asset_key`、`panel_frequency` 和 `coverage_rule`，不得把面板当作隐式时序表。

### 准入语义必须保留
`eligibility_base_mask.parquet` 只负责记录基础可研究掩码，不得混入具体因子定义。

### 分组中性化底座必须版本化
若后续允许 `neutralization_policy = group_neutral`，`shared_feature_base/` 中的 group taxonomy 必须版本化并可追溯。

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
12. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
13. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_data_ready 完成
