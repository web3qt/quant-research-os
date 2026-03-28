# Test Evidence Robust Statistics Guidance Design

## Goal

把 `Test Evidence` 阶段对异方差性、自相关与稳健统计推断的要求写清楚，让 agent 在审阅与门禁判断时知道什么时候必须交代推断口径、哪些方法可接受、哪些结论只能停留在 audit-only。

## Scope

本次变更只更新文档与 skill：

- `qros-test-evidence-review` 本地 skill 两份副本
- `docs/gates/workflow_stage_gates.yaml`
- `docs/main-flow-sop/04_test_evidence_sop_cn.md`
- `docs/main-flow-sop/research_workflow_sop.md`

不修改 runtime、测试、依赖或统计实现代码。

## Design Principles

1. 方法导向，不绑定实现库。
2. 只有当 formal gate 直接引用 `t` 值、`p` 值、回归显著性或残差型证据时，才强制要求记录稳健推断口径。
3. 未说明稳健性的原始 `OLS` 显著性，可以作为 exploratory / audit evidence，但不能直接充当 formal pass 依据。
4. skill 中给方法名和判断原则，不把 `statsmodels`、`arch` 之类库名写成硬要求。

## Accepted Statistical Guidance

文档统一接受并点名以下方法作为示例：

- `HAC / Newey-West`：时间序列或可能存在序列相关时的稳健 `t` 值/标准误
- `White` / `Breusch-Pagan`：异方差诊断
- `WLS` / `GLS`：当方差结构已知或可近似建模时的修正方案
- `ARCH / GARCH`：当波动聚集本身就是主要问题时的建模方案

这些方法是“可接受口径示例”，不是强制实现清单。

## Gate Semantics

统一语义如下：

- formal gate 若依赖回归或显著性统计，必须写明稳健推断口径，或说明为何无需该修正。
- audit-only 保留对 `HAC t` 值、条件分层、拥挤度等解释性证据的检查。
- 若直接把未经说明的原始 `OLS` 显著性升级为 formal pass 依据，应视为 blocking finding。

## Non-Goals

- 不新增 machine-readable artifact
- 不新增统计库依赖
- 不把 skill 改写成实现说明书
- 不要求所有 Test Evidence 场景都必须跑完整回归诊断

## Expected Outcome

更新后，agent 在 `Test Evidence` 阶段会更一致地做出以下判断：

- 什么时候需要提 `HAC / Newey-West`
- 什么时候应怀疑异方差影响了显著性
- 什么时候应把 `White / Breusch-Pagan / WLS / GLS / ARCH / GARCH` 写进保留风险或修正建议
- 什么时候不能让未经稳健说明的显著性直接通过 formal gate
