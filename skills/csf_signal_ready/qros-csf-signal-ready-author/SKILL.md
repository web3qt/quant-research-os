---
name: qros-csf-signal-ready-author
description: Use when reviewed csf_data_ready outputs must be frozen into formal csf_signal_ready artifacts through grouped interactive confirmation.
---

# CSF Signal Ready Author

## Purpose

只在 `csf_data_ready review` closure 完成之后，把 `02_csf_data_ready` 冻结成正式 `03_csf_signal_ready` 产物。

这里的 `csf_signal_ready` 不是静默扫参数，而是交互式冻结 cross-sectional factor 路线的正式因子合同。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `03_csf_signal_ready` 需要交付的 factor panel、factor manifest 和 coverage 证据，而不是把空目录、placeholder 文件或只有合同语义的说明文档当作 csf_signal_ready 完成。

## Contract-first Truth

- `contracts/artifacts/csf_signal_ready_artifacts.yaml` 是本阶段 formal artifact shape 的字段真值
- 不得把 `SKILL.md` 当作字段真值；本文件只定义执行顺序、确认纪律和 review 边界
- 不得手写或自行扩展 formal artifact shape
- 必须先使用 runtime scaffold 创建 `03_csf_signal_ready` author layout
- 必须读取 `contracts/artifacts/csf_signal_ready_artifacts.yaml`
- build 后必须运行 `qros-validate-stage --stage csf_signal_ready`
- build 后必须通过 `csf_signal_ready` semantic validator，确认 factor panel、final score、coverage、input field source、group context 与 route inheritance 都一致
- validator/preflight 不通过，不得进入 `csf_signal_ready` review

## Required Inputs

- `02_csf_data_ready/author/formal/panel_manifest.json`
- `02_csf_data_ready/author/formal/asset_universe_membership.parquet`
- `02_csf_data_ready/author/formal/eligibility_base_mask.parquet`
- `02_csf_data_ready/author/formal/shared_feature_base/*`
- `02_csf_data_ready/review/closure/stage_completion_certificate.yaml`
- `01_mandate/author/formal/research_route.yaml`

## Required Outputs

- `factor_panel.parquet`
- `factor_manifest.yaml`
- `component_factor_manifest.yaml`
- `factor_coverage_report.parquet`
- `factor_group_context.parquet`
- `route_inheritance_contract.yaml`
- `factor_contract.md`
- `factor_field_dictionary.md`
- `csf_signal_ready_gate_decision.md`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `factor_identity`
- `panel_contract`
- `factor_expression`
- `context_contract`
- `delivery_contract`

## Mandatory Discipline

- 生成 `factor_panel.parquet`、`factor_coverage_report.parquet`、`factor_group_context.parquet` 等机器产物时，必须使用 Polars (`pl.DataFrame.write_parquet`)，不得使用 pyarrow 或 pandas
- 只能消费已经通过 review closure 的 csf_data_ready 产物
- 只能冻结 `research_route = cross_sectional_factor` 的因子定义
- `factor_role`、`factor_structure`、`portfolio_expression` 与 neutralization route identity 必须从 mandate 的 `research_route.yaml` 继承，并写入 `route_inheritance_contract.yaml`
- 不得产出任何时序主线措辞、预测 horizon 口径或单资产触发语义
- 必须先显式生成或刷新本 stage 的 lineage-local stage program，再执行 author build；QROS runtime 只负责校验和调用，不再后台静默生成默认 wrapper
- 该 stage program 必须是当前 lineage 在本 stage 里真实产生产物的程序，必须明确 formal artifacts 的生成路径、输入绑定和 replay 入口
- thin wrapper、framework builder shim、只转发共享 helper 的 skeleton 都不合法；`run_stage.py` 与关键 helper 不能只是把框架 builder 包一层
- 空目录、placeholder `parquet/csv/md`、只有口头或文档语义说明的产物都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_signal_ready？`
- 不得静默修改 data_ready 已冻结的面板主键、准入语义或时间边界

- 若本阶段需要新增或修改代码，必须为真实产生产物的程序中的关键步骤、关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 语言规则统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外口径。

## Gate Discipline

### 因子角色必须显式
`factor_role` 必须在 `standalone_alpha | regime_filter | combo_filter` 中三选一。

### 因子结构必须显式
`factor_structure` 必须在 `single_factor | multi_factor_score` 中二选一。

### 投组合表达必须显式
`portfolio_expression` 必须显式冻结，且必须符合角色约束，不得留空：

- `standalone_alpha` 允许：
  - `long_short_market_neutral`
  - `long_only_rank`
  - `short_only_rank`
  - `benchmark_relative_long_only`
  - `group_relative_long_short`
- `regime_filter` 只允许：
  - `target_strategy_filter`
- `combo_filter` 只允许：
  - `target_strategy_filter`
  - `target_strategy_overlay`

### 中性化策略必须显式
`neutralization_policy` 必须冻结为 `none | market_beta_neutral | group_neutral`，并且 group taxonomy 若启用必须版本化。

### 多因子必须是确定性的
`multi_factor_score` 第一版只能采用确定性组合公式，不得在本阶段引入训练后学权重。

## Working Rules

1. 确认 `02_csf_data_ready/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `factor_identity`
3. 再收敛并确认 `panel_contract`
4. 再收敛并确认 `factor_expression`
5. 再收敛并确认 `context_contract`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 `factor_panel.parquet`、factor manifest 和 coverage 证据
8. 输出一份 grouped csf_signal_ready summary
9. 只有用户最终批准后，才生成正式 `03_csf_signal_ready` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 运行 `qros-validate-stage --stage csf_signal_ready`，并确认 semantic validator / deterministic preflight 通过
12. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_signal_ready 完成
