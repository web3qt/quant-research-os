# Serial Correlation Diagnostics Guidance Design

## Goal

把 `Test Evidence` 阶段对残差自相关、serial correlation 与相关诊断 protocol 的治理要求写清楚，让 agent 在审阅与门禁判断时知道：什么时候需要交代 `Durbin-Watson`、`Breusch-Godfrey LM`、`Ljung-Box` 这类检验或免做理由，什么时候这些证据只能停留在 audit-only。

## Scope

本次变更只更新治理层文档与 review skill：

- `docs/review-sop/review_checklist_master.yaml`
- `docs/gates/workflow_stage_gates.yaml`
- `docs/main-flow-sop/research_workflow_sop.md`
- `docs/main-flow-sop/04_test_evidence_sop_cn.md`
- `qros-test-evidence-review` 本地 skill 两份副本

不修改 runtime、测试、依赖、统计实现代码或外部库绑定。

## Design Principles

1. 方法导向，不绑定具体 Python 统计库。
2. 只有当 formal gate 直接依赖残差近似独立、原始 `OLS` 误差设定，或把未校正回归显著性作为证据时，才强制要求披露 serial-correlation diagnostic protocol 或免做理由。
3. `HAC / Newey-West` 解决的是稳健推断口径；`DW / BG-LM / Ljung-Box` 解决的是“自相关有没有被诊断与解释”。两者相关，但不完全等价。
4. `Durbin-Watson` 适合作为快速一阶残差自相关检查；`Breusch-Godfrey LM` 更适合高阶相关和带滞后项的回归；`Ljung-Box` 可作为审计级补充。
5. 没有 serial-correlation diagnostic 的原始 `OLS` 结论，最多只能停留在 exploratory / audit evidence，不应直接支撑 formal `PASS`。

## Accepted Diagnostic Guidance

文档统一接受并点名以下方法作为示例：

- `Durbin-Watson`：快速检查一阶残差自相关
- `Breusch-Godfrey LM`：更通用的高阶残差自相关检验，且适用于带滞后项的回归
- `Ljung-Box`：用于残差或时间序列整体 serial correlation 的补充审计
- `HAC / Newey-West`：不是自相关“检验”，但可作为存在序列相关风险时的稳健推断口径

这些方法是“可接受 protocol 示例”，不是强制实现清单。

## Gate Semantics

统一语义如下：

- 若 formal gate 直接依赖 `t` 值、`p` 值、回归显著性或残差型证据，仍然必须说明稳健推断口径。
- 若 formal gate 进一步依赖残差近似独立、原始 `OLS` 误差设定，或 reviewer 明确使用“未见明显 serial correlation”来支撑结论，则必须记录自相关诊断 protocol 或免做理由。
- `Breusch-Godfrey LM` 一般比 `Durbin-Watson` 更适合作为正式回归审计依据；`Durbin-Watson` 可保留为快速检查或补充说明。
- `Ljung-Box` 可以作为 residual diagnostics 的审计补充，但不要求它单独承担 formal gate 的全部责任。

## Non-Goals

- 不新增 machine-readable artifact
- 不新增统计库依赖
- 不要求所有 Test Evidence 场景都必须跑完整 residual diagnostics
- 不把 skill 改写成计量经济学实现手册
- 不扩展到 `Holdout Validation` 或 runtime 默认草稿项

## Expected Outcome

更新后，agent 在 `Test Evidence` 阶段会更一致地做出以下判断：

- 什么时候 `HAC / Newey-West` 已足够，什么时候还要交代自相关诊断 protocol
- 什么时候应该优先提 `Breusch-Godfrey LM` 而不是只提 `Durbin-Watson`
- 什么时候 `Ljung-Box` 只是补充 audit evidence
- 什么时候不能让“未经 serial-correlation 诊断的原始 OLS 结论”直接通过 formal gate
