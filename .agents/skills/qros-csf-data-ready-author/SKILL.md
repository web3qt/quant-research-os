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
- `coverage_report.parquet`
- `shared_feature_base/`
- `csf_data_contract.md`
- `data_ready_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `panel_contract`
- `quality_semantics`
- `universe_admission`
- `shared_derived_layer`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 mandate 产物
- 只能冻结 `research_route = cross_sectional_factor` 的面板底座
- 必须在当前 research repo 里真实生成 `date x asset` 面板、覆盖证据和共享派生层
- 不得产出任何时序主线措辞、预测 horizon 口径或单资产触发语义
- 空目录、placeholder `parquet/csv/md`、只有口头或文档语义说明的产物都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_data_ready？`
- 不得静默修改 mandate 冻结的 universe 口径、时间边界或路由

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

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
3. 再收敛并确认 `quality_semantics`；明确缺失、坏值、stale 和 outlier 的处理语义
4. 再收敛并确认 `universe_admission`；确认排除项已显式记录
5. 再收敛并确认 `shared_derived_layer`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 `panel_manifest.json`、覆盖证据和共享派生层
8. 输出一份 grouped csf_data_ready summary
9. 只有用户最终批准后，才生成正式 `02_csf_data_ready` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_data_ready 完成
