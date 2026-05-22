---
name: qros-mandate-author
description: Use when mandate admission has passed and must be frozen into formal mandate artifacts.
---

# Mandate Author

## Purpose

只在 `mandate_admission.yaml` 明确 `ACCEPT_FOR_MANDATE` 且 mandate freeze 已确认后，把 `01_mandate/author/draft/` 产物冻结成正式 `01_mandate/author/formal/` 产物。

这里的 `mandate` 不是静默补文档，而是交互式冻结研究合同。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage mandate --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Required Inputs

- `01_mandate/author/draft/mandate_admission.yaml`
- `01_mandate/author/draft/mandate_freeze_draft.yaml`
- `01_mandate/author/draft/mandate_transition_approval.yaml`
- `route_assessment`

## Admission Rule

只有当 `mandate_admission.yaml` 明确写出 `ACCEPT_FOR_MANDATE`，且 freeze groups 与 `mandate_transition_approval.yaml` 都确认后，才允许继续。

如果 verdict 是：

- `NEEDS_REFRAME`
- `DROP`

则不得生成 mandate artifacts。

## Required Outputs

- `mandate.md`
- `research_scope.md`
- `time_split.json`
- `parameter_grid.yaml`
- `run_config.toml`
- `research_route.yaml`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 4 组推进：

- `research_intent`
- `scope_contract`
- `data_contract`
- `execution_contract`

## Mandatory Discipline

- 只能消费已经通过 qualification 的 intake artifacts
- 必须冻结研究主问题、scope、时间切分、参数边界和实现栈
- 必须先确认 `data_source` 与 `bar_size`，再冻结 mandate
- 必须先确认 `route_assessment`，再冻结 `research_route`
- 必须把 `data_viability_contract`、`time_coverage_contract`、`route_viability_contract` 作为 mandate freeze 前的 preflight 事实先锁定；reviewer 不是这些基础事实的第一发现点
- `research_route` 第一版只允许 `time_series_signal` 与 `cross_sectional_factor`
- 必须写清 `excluded_routes` 与 `route_rationale`
- 必须写清 success / failure / budget / excluded scope
- 必须先回显 freeze draft；可以逐组确认，也可以一次展示全部 groups 后接受 `确认全部` 批量确认 groups
- 四组全部确认后，才允许最终 `是否确认进入 mandate`
- 禁止 post-hoc restatement
- 禁止根据后验结果静默改题
- `contracts/artifacts/mandate_artifacts.yaml` 是 `01_mandate/author/formal` 的字段真值层
- 不得把 SKILL.md 作为字段真值；skill 只负责执行顺序、freeze 访谈和 runtime 调用
- 生成正式 mandate artifacts 后，必须运行 `qros-validate-stage --stage mandate`
- validator 不通过，不得进入 mandate review

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 语言规则统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外口径。

## Gate Discipline

### Universe 精确性要求
`scope_contract` 冻结时，universe 必须是以下之一：
- 显式 symbol 列表
- 显式的、可被代码执行的准入规则

"流动性好的 symbol"、"大概这些"等模糊描述**不得**通过。必须要求用户明确给出准入规则或列表。

### Companion Field Documentation 验证
每个机器可读产物生成后，必须验证对应的人类可读 companion 说明存在：

| 产物 | Companion 位置 |
|------|--------------|
| `time_split.json` | `mandate.md` 时间窗段落 |
| `parameter_grid.yaml` | `mandate.md` 参数边界段落（每个参数有 type/min/max/step/unit/rationale） |
| `run_config.toml` | `mandate.md` 实现栈段落 |

companion 说明不存在或只有裸字段名，**不得**宣布 mandate 完成。

### non_rust_exceptions 显式要求
`run_config.toml` 的 `non_rust_exceptions` 字段必须显式填写：
- 若全部 Rust 实现：写 `[]`
- 若有例外：每条例外必须有理由

不允许遗漏该字段。

### 容量与拥挤审计基准
`execution_contract` 必须包含：
- `crowding distinctiveness review` 的比较基准（benchmark）
- `capacity review` 的流动性代理变量、参与率边界

这两项是后续 backtest 阶段容量分析的锚点，缺失则 mandate 不完整。

### 后验结果回写检测
如果用户在已看过任何 signal/train/test/backtest 结果后申请冻结或修改 mandate，必须明确触发 **CHILD LINEAGE**，不允许静默修改。

## Working Rules

1. 读取 `01_mandate/author/draft/mandate_admission.yaml`
2. 确认 `admission_decision.verdict == ACCEPT_FOR_MANDATE`
3. 读取已确认的 `mandate_freeze_draft.yaml` 与 `mandate_transition_approval.yaml`
4. 先收敛并确认 `research_intent`
5. 在 `research_intent` 中确认 `route_assessment`、`research_route`、`excluded_routes`，先把 `route_viability_contract` 锁定，不得把“这题到底该走哪条 route”留给 reviewer
6. 再收敛并确认 `scope_contract`；核查 universe 是显式列表或可执行规则（见上）
7. 再收敛并确认 `data_contract`，先把 `data_viability_contract` 锁定，确保 `data_source` / `bar_size` / 真实可抽取性已经明确
8. 再收敛并确认 `execution_contract`；核查容量/拥挤审计基准已写清、non_rust_exceptions 已填写，并先把 `time_coverage_contract` 锁定，确保冻结时间边界不会等 reviewer 才第一次发现越界
9. 输出一份 grouped freeze summary
10. 只有用户最终批准后，才生成正式 mandate artifacts
11. 将 confirmed freeze groups 压成 `mandate.md`、`research_scope.md`
12. 生成 `time_split.json`、`parameter_grid.yaml`、`run_config.toml`、`research_route.yaml`
13. 验证每个机器可读产物都有 companion field documentation（见上）
14. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
15. 运行 `qros-validate-stage --stage mandate`
16. validator 不通过时，修复 formal artifacts；不得宣布 mandate 完成或进入 review
