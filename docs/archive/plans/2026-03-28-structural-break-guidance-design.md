# Structural Break Guidance Design

## Goal

把 `Test Evidence` 与 `Holdout Validation` 阶段对结构突变、参数稳定性和关系连续性的治理要求写清楚，让 agent 在审阅与门禁判断时知道：什么时候必须披露 `Chow / Bai-Perron / CUSUM / rolling coefficient stability` 这类 protocol，什么时候只能把相关发现停留在 audit-only。

## Scope

本次变更只更新治理层文档与 review skill：

- `docs/review-sop/review_checklist_master.yaml`
- `docs/gates/workflow_stage_gates.yaml`
- `docs/main-flow-sop/research_workflow_sop.md`
- `docs/main-flow-sop/04_test_evidence_sop_cn.md`
- `docs/main-flow-sop/06_holdout_validation_sop_cn.md`
- `qros-test-evidence-review` 本地 skill 两份副本
- `qros-holdout-validation-review` 本地 skill 两份副本

不修改 runtime、测试、依赖、统计实现代码或外部库绑定。

## Design Principles

1. 治理导向，不绑定具体 Python 库或单一实现。
2. 只有当 formal gate 直接依赖“关系跨窗口稳定延续”这类主张时，才强制要求披露结构突变检验 protocol 或免做理由。
3. `regime mismatch` 与“机制本身断裂”必须分开讨论；结构突变检验是辅助判断工具，不是自动判死刑按钮。
4. 显著结构突变本身不自动等于 `NO-GO`，但如果 formal pass 依赖连续性主张却没有相应 protocol，就不能给 `PASS`。
5. Audit-only 允许使用较轻量的稳定性证据；formal gate 若要吃这类证据，必须把边界和解释写清楚。

## Accepted Structural-Break Guidance

文档统一接受并点名以下方法作为示例：

- `Chow`：断点已事先指定，想检验断点前后回归关系是否一致
- `Bai-Perron`：断点未知，且可能存在一个或多个 breakpoints
- `CUSUM / CUSUMSQ`：用于参数稳定性或累计漂移的连续监控
- `rolling / expanding coefficient stability`：作为审计级辅助证据，观察系数、beta、lead-lag 关系是否随时间持续漂移

这些方法是“可接受 protocol 示例”，不是强制实现清单。

## Gate Semantics

统一语义如下：

- `Test Evidence`：若 formal gate 进一步声称某个回归系数、lead-lag 关系、beta、threshold 机制或残差关系在 train/test 间稳定延续，必须记录结构突变检验 protocol 或免做理由。
- `Holdout Validation`：若 verdict 依赖“结构仍连续”或“结果退化只是 regime 不匹配而非机制断裂”的判断，必须记录结构突变检验 protocol 或免做理由。
- 若检出了显著 break，agent 必须区分它更像是 regime 组成变化、样本过短、实现问题，还是机制本身失效。
- 未披露 structural-break protocol 的连续性主张，最多只能停留在 audit-only，不得直接升级为 formal pass 依据。

## Non-Goals

- 不新增 machine-readable artifact
- 不新增统计库依赖
- 不要求所有 Test/Holdout 场景都必须跑完整 structural-break test
- 不把 skill 改写成计量经济学实现说明书
- 不顺手扩大为 generator/runtime 修复任务

## Expected Outcome

更新后，agent 在 `Test Evidence` 与 `Holdout Validation` 阶段会更一致地做出以下判断：

- 什么时候只做 regime/drift 解释还不够，必须补结构突变 protocol
- 什么时候 `Chow / Bai-Perron / CUSUM / rolling coefficient stability` 只是 audit evidence
- 什么时候显著 break 需要触发 reservations、`RETRY`、`NO-GO` 或 `CHILD LINEAGE`
- 什么时候不能把“关系仍连续”这种说法直接拿来支持 formal `PASS`
