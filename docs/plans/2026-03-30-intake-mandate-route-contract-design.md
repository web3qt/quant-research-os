# Intake Mandate Route Contract Design

**Date:** 2026-03-30  
**Status:** Approved for first-wave implementation  
**Scope:** `Codex-only`, `intake -> mandate` governance layer, first wave supports `time_series_signal` and `cross_sectional_factor`

## Goal

让研究员在 `idea_intake -> mandate` 之间，显式讨论并冻结“这条研究线到底属于哪类研究路线”，避免把截面问题、时序问题、触发问题混成一套默认语义后再靠下游阶段补救。

第一版只解决一件事：

- 在 `idea_intake` 输出 route recommendation
- 在 `mandate` 正式冻结 route truth
- 让后续 workflow 能读取 route 并按 route 分流 stage contract

## Core Principle

本次设计把研究流程拆成两层：

1. `治理层`
   统一管理 intake、mandate、data contract、lineage、rollback、review 和 artifact audit。
2. `研究路线层`
   在统一治理骨架之内，按 research route 切换 `signal_ready / train / test / backtest` 的语义和 formal gate。

统一的是治理，不统一的是研究语义。

## First-Wave Route Taxonomy

第一版只正式支持两条 route：

- `time_series_signal`
- `cross_sectional_factor`

以下 route 只保留概念占位，不进入第一版 formal contract：

- `event_trigger`
- `relative_value`

这样可以先把 route governance 做稳，而不是一开始铺开全部研究类型。

## Recommended Responsibility Split

推荐采用中间方案：

- `idea_intake` 给出 `candidate_routes + recommended_route`
- `mandate` 冻结 `research_route`

不采用的两个极端：

- `idea_intake` 直接冻结最终 route：太早，输入仍粗，容易误判。
- `mandate` 才第一次讨论 route：太晚，前置资格评估无法帮助研究员澄清问题类型。

## Intake Route Assessment Contract

`idea_intake` 不冻结最终 route，但必须正式产出 route assessment。

### Required Outputs

人类可读：

- `research_question_set.md` 新增 `Route Assessment` 段落

机器可读：

- `idea_gate_decision.yaml.route_assessment`

### Required Fields

`route_assessment` 至少包含：

- `candidate_routes`
- `recommended_route`
- `why_recommended`
- `why_not_other_routes`
- `route_risks`
- `route_decision_pending`

建议形态：

```yaml
route_assessment:
  candidate_routes:
    - cross_sectional_factor
    - time_series_signal
  recommended_route: cross_sectional_factor
  why_recommended:
    - edge is expressed as same-time cross-asset ranking
    - output is better suited for cross-sectional sorting than absolute direction
  why_not_other_routes:
    time_series_signal:
      - thesis is not primarily about one asset's own path
  route_risks:
    - universe breadth may be insufficient for stable ranking
  route_decision_pending: true
```

### Mandatory Intake Questions

第一版 intake 必须多问四个 route 判定问题：

1. edge 主要发生在“同一时点资产之间”，还是“单个资产跨时间”？
2. 输出更像“连续打分/排序”，还是“事件触发后条件反应”？
3. 交易表达更像“横截面选强弱”，还是“单资产做方向”？
4. 这个对象是 `standalone alpha`，还是更像 `filter`？

只有这些问题问完，系统才允许给出 route recommendation。

## Mandate Route Freeze Contract

`mandate` 在现有 `research_intent` 冻结组中增加 route freeze，而不是再开一整套独立确认流程。

### Required Outputs

人类可读：

- `mandate.md` 新增 `研究路线与排除路线` 段落

机器可读：

- 新增 `01_mandate/research_route.yaml`

建议形态：

```yaml
research_route: cross_sectional_factor
excluded_routes:
  - time_series_signal
route_rationale:
  - thesis is expressed as cross-asset ranking rather than single-asset absolute direction
  - downstream evidence should prioritize rank-based cross-sectional tests
route_change_policy:
  before_downstream_freeze: rollback_to_mandate
  after_downstream_freeze: child_lineage
route_contract_version: v1
```

### Formal Gate Additions

Mandate formal gate 第一版新增三个 blocking 条件：

1. `research_route` 已冻结，不能留空
2. `excluded_routes` 已明确，不能只写推荐路线不写排除项
3. `route_rationale` 已写明，必须解释“为什么不是另一类问题”

### Change Discipline

- 在 `mandate` 阶段内部、且尚无下游正式产物时，route 变更允许 `rollback_to_mandate`
- 一旦已经有 `signal_ready / train / test / backtest` 任一正式产物，再改 route，默认 `child_lineage`

## Route-Specific Stage Contract Boundary

统一 stage 名称保留：

- `signal_ready`
- `train`
- `test`
- `backtest`

从 `signal_ready` 开始，按 `research_route` 分流 contract。

### `time_series_signal`

- `signal_ready`：逐资产时序信号、状态字段、未来收益对齐
- `train`：阈值、regime cuts、质量过滤、参数台账
- `test`：方向命中率、IC、分层收益、regime 一致性
- `backtest`：冻结信号映射成方向规则后验证成本后经济可行性

### `cross_sectional_factor`

- `signal_ready`：`date x asset` 因子面板、排序字段、截面覆盖
- `train`：winsorize、standardize、neutralize、bucket/quantile schema、再平衡频率
- `test`：`Rank IC`、`ICIR`、分组收益、单调性、breadth、稳定性
- `backtest`：因子分数映射成组合权重，再看换手、成本、容量、组合 OOS

第一版只要求 route 能被识别和冻结，不要求一次实现完 `cross_sectional_factor` 的全部专属 artifact。

## First-Wave Implementation Scope

第一版只改四类对象：

1. 文档合同
   - `docs/main-flow-sop/00_idea_intake_sop_cn.md`
   - `docs/main-flow-sop/00_mandate_sop_cn.md`
   - `docs/main-flow-sop/research_workflow_sop.md`
2. 机器可读 schema / examples
   - `docs/intake-sop/idea_gate_decision_schema.yaml`
   - `docs/intake-sop/examples/idea_gate_decision.example.yaml`
   - 新增 `docs/main-flow-sop/research_route_schema.yaml`
   - 新增 `docs/main-flow-sop/research_route.example.yaml`
3. author / orchestrator skills
   - `skills/qros-idea-intake-author/SKILL.md`
   - `skills/qros-mandate-author/SKILL.md`
   - `skills/qros-research-session/SKILL.md`
4. runtime routing
   - `tools/research_session.py`
   - `scripts/build_mandate_from_intake.py`
   - `scripts/run_research_session.py`

## Non-Goals

第一版明确不做：

- `cross_sectional_factor` 全量 `test/backtest` artifact 落地
- `Rank IC / ICIR / factor return / neutralization` 的完整 formal gate
- `event_trigger` 与 `relative_value` 的正式 route contract
- live execution / production admission 改造

## Acceptance Criteria

第一版完成后，至少满足以下 6 条：

1. `idea_intake` 若 verdict 为 `GO_TO_MANDATE`，则必须存在 `route_assessment`
2. `route_assessment` 必须包含 `candidate_routes / recommended_route / why_recommended / why_not_other_routes`
3. `mandate` 冻结时必须生成 `research_route.yaml`
4. 缺少 `research_route` 或 `excluded_routes` 的 mandate 不得 formal pass
5. 已冻结 mandate 若试图改 route，系统必须提示 `rollback_to_mandate` 或 `child_lineage`
6. `qros-research-session` 状态输出中能够报告当前 route

## Expected Outcome

更新后，研究员在正式进入 `mandate` 之前，就能把“这条线到底按截面还是按时序走”讨论清楚；一旦进入 `mandate`，route 就成为正式冻结对象；后续如果扩 `cross_sectional_factor` 专属 stage contract，也有稳定 machine-readable 锚点可接。
