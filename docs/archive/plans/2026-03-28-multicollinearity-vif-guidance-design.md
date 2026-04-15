# Multicollinearity And VIF Guidance Design

## Goal

把 `Test Evidence` 阶段对多重共线性、`VIF` 与多变量回归单个系数解释边界的治理要求写清楚，让 agent 在审阅与门禁判断时知道：什么时候必须披露 `VIF`、`condition number`、相关矩阵等 protocol 或免做理由，什么时候这些证据只能停留在 audit-only。

## Scope

本次变更只更新治理层文档与 review skill：

- `docs/review-sop/review_checklist_master.yaml`
- `docs/gates/workflow_stage_gates.yaml`
- `docs/main-flow-sop/research_workflow_sop.md`
- `docs/main-flow-sop/04_test_evidence_sop_cn.md`
- `qros-test-evidence-review` 本地 skill 两份副本

不修改 runtime、测试、依赖、统计实现代码或外部库绑定。

## Design Principles

1. 只在 formal gate 依赖“多变量回归里单个系数的符号、显著性或增量解释”时，才强制要求披露多重共线性诊断 protocol 或免做理由。
2. `VIF` 是最常见的共线性诊断，但不是唯一方法；`condition number`、pairwise correlation matrix、eigenvalue 类诊断都可以作为补充。
3. 高 `VIF` 不自动等于模型无效，但意味着单个系数解释、`t` 值和“控制后仍显著”这类话术需要收缩边界。
4. 如果 formal claim 只是预测能力、排序能力或单因子结构，不应强行套用 `VIF` 义务。
5. 不把固定阈值写成硬 fail 线；重点在于披露边界、解释风险，而不是机械判死刑。

## Accepted Diagnostic Guidance

文档统一接受并点名以下方法作为示例：

- `VIF`：衡量某个解释变量能被其他解释变量解释到什么程度，用于诊断单个系数解释脆弱性
- `condition number`：用于判断设计矩阵整体病态程度
- pairwise correlation matrix：作为快速筛查，但不能替代 `VIF` 或整体矩阵诊断
- eigenvalue / singular-value diagnostics：作为更细的矩阵病态补充证据

这些方法是“可接受 protocol 示例”，不是强制实现清单。

## Gate Semantics

统一语义如下：

- 若 formal gate 直接依赖多变量回归中单个系数的符号、显著性、稳健增量解释，或使用“控制常见因子后仍显著”来支撑结论，必须记录多重共线性诊断 protocol 或免做理由。
- `VIF` 一般是首选示例，但并不要求所有场景都必须跑 `VIF`；关键是解释“单个系数为何仍可解释”。
- 发现高共线性后，不应自动给 `NO-GO`；但若仍继续给出强单因子解释，就不能直接 formal `PASS`。
- 若研究主证据不是多变量回归单个系数解释，则共线性诊断可以留在 audit-only，或明确说明不适用。

## Non-Goals

- 不新增 machine-readable artifact
- 不新增统计库依赖
- 不要求所有 Test Evidence 场景都必须跑 `VIF`
- 不扩展到 `Holdout Validation`
- 不把 skill 改写成线性代数教材

## Expected Outcome

更新后，agent 在 `Test Evidence` 阶段会更一致地做出以下判断：

- 什么时候必须补 `VIF` 或同类共线性诊断
- 什么时候 pairwise correlation matrix 只是快速筛查，不足以支撑 formal claim
- 什么时候高 `VIF` 主要削弱的是“单个系数解释”，而不是整个研究立即失效
- 什么时候不能把“控制后仍显著”直接当成 formal `PASS` 依据
