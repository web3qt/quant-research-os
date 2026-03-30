---
name: qros-csf-signal-ready-author
description: Use when reviewed csf_data_ready outputs must be frozen into formal csf_signal_ready artifacts through grouped interactive confirmation.
---

# CSF Signal Ready Author

## Purpose

只在 `csf_data_ready review` closure 完成之后，把 `02_csf_data_ready` 冻结成正式 `03_csf_signal_ready` 产物。

这里的 `csf_signal_ready` 不是静默扫参数，而是交互式冻结 cross-sectional factor 路线的正式因子合同。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `03_csf_signal_ready` 需要交付的 factor panel、factor manifest 和 coverage 证据，而不是把空目录、placeholder 文件或只有合同语义的说明文档当作 csf_signal_ready 完成。

## Required Inputs

- `02_csf_data_ready/panel_manifest.json`
- `02_csf_data_ready/asset_universe_membership.parquet`
- `02_csf_data_ready/eligibility_base_mask.parquet`
- `02_csf_data_ready/csf_data_contract.md`
- `02_csf_data_ready/stage_completion_certificate.yaml`

## Required Outputs

- `factor_panel.parquet`
- `factor_manifest.yaml`
- `factor_coverage.parquet`
- `factor_contract.md`
- `factor_field_dictionary.md`
- `signal_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `factor_identity`
- `factor_role_contract`
- `factor_structure_contract`
- `neutralization_policy`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 csf_data_ready 产物
- 只能冻结 `research_route = cross_sectional_factor` 的因子定义
- 必须显式冻结 `factor_role`、`factor_structure`、`portfolio_expression` 与 `neutralization_policy`
- 不得产出任何时序主线措辞、预测 horizon 口径或单资产触发语义
- 空目录、placeholder `parquet/csv/md`、只有口头或文档语义说明的产物都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_signal_ready？`
- 不得静默修改 data_ready 已冻结的面板主键、准入语义或时间边界

## Gate Discipline

### 因子角色必须显式
`factor_role` 必须在 `standalone_alpha | regime_filter | combo_filter` 中三选一。

### 因子结构必须显式
`factor_structure` 必须在 `single_factor | multi_factor_score` 中二选一。

### 投组合表达必须显式
`portfolio_expression` 必须冻结为 `long_short_market_neutral` 或 `long_only_rank`，不得留空。

### 中性化策略必须显式
`neutralization_policy` 必须冻结为 `none | market_beta_neutral | group_neutral`，并且 group taxonomy 若启用必须版本化。

### 多因子必须是确定性的
`multi_factor_score` 第一版只能采用确定性组合公式，不得在本阶段引入训练后学权重。

## Working Rules

1. 确认 `02_csf_data_ready/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `factor_identity`
3. 再收敛并确认 `factor_role_contract`；明确 `standalone_alpha | regime_filter | combo_filter`
4. 再收敛并确认 `factor_structure_contract`；明确 `single_factor | multi_factor_score`
5. 再收敛并确认 `neutralization_policy`；明确 `portfolio_expression`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 `factor_panel.parquet`、factor manifest 和 coverage 证据
8. 输出一份 grouped csf_signal_ready summary
9. 只有用户最终批准后，才生成正式 `03_csf_signal_ready` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_signal_ready 完成
