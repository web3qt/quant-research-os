# Spurious Regression Guidance Design

## Goal

把 `Test Evidence` 阶段对虚假回归、单位根、非平稳 level series 与协整边界的治理要求写清楚，让 agent 在审阅与门禁判断时知道：什么时候必须披露 `ADF`、`Phillips-Perron`、`KPSS`、`Engle-Granger`、`Johansen` 或同类防虚假回归 protocol 或免做理由，什么时候 level-series 回归结论只能停留在 audit-only。

## Scope

本次变更只更新治理层文档与 review skill：

- `docs/review-sop/review_checklist_master.yaml`
- `docs/gates/workflow_stage_gates.yaml`
- `docs/main-flow-sop/research_workflow_sop.md`
- `docs/main-flow-sop/04_test_evidence_sop_cn.md`
- `qros-test-evidence-review` 本地 skill 两份副本

不修改 runtime、测试、依赖、统计实现代码或外部库绑定。

## Design Principles

1. 只在 formal gate 依赖可能非平稳 level series 的回归、长期均衡关系、价差均值回复或残差型 spread 结构时，才强制要求披露防虚假回归 protocol 或免做理由。
2. `regime_stationarity_audit`、结构突变检验与单位根/协整是三类不同问题，不能混用术语或互相替代。
3. `ADF`、`Phillips-Perron`、`KPSS` 用于 unit-root / stationarity 风险判断；`Engle-Granger`、`Johansen` 用于 cointegration / 长期关系诊断；returns / differencing / log-differencing 可作为常见处理路径。
4. 如果 series 非平稳且没有 cointegration 证据，level-series 的高 `R^2`、显著 `t` 值或看似稳定的残差关系，最多只能停留在 audit-only。
5. 如果主证据本来就在收益率、差分或其他弱化趋势影响的空间里，不应机械强制要求单位根/协整检验；关键是解释为什么“不适用”。

## Accepted Diagnostic Guidance

文档统一接受并点名以下方法作为示例：

- `ADF`：常见的 unit-root 风险检查
- `Phillips-Perron`：对自相关/异方差更稳健的 unit-root 检查补充
- `KPSS`：以 stationarity 为原假设的补充检验
- `Engle-Granger`：两变量或残差型长期关系的常见 cointegration protocol
- `Johansen`：多变量长期均衡关系的常见 cointegration protocol
- returns / differencing / log-differencing / stationarity-checked spread：常见处理路径

这些方法是“可接受 protocol 示例”，不是强制实现清单。

## Gate Semantics

统一语义如下：

- 若 formal gate 直接依赖可能非平稳的价格 level、累计量、链上规模指标或 level spread 回归，必须记录防虚假回归 protocol 或免做理由。
- 若 formal gate 进一步声称长期均衡关系、pair spread 均值回复或非平稳 series 间残差关系可交易，必须说明 cointegration protocol 或为何不需要。
- 如果检出非平稳且没有 cointegration 证据，level-series 回归不应继续支撑 formal `PASS`；应降回 audit-only，或改用 returns / differencing 后重新定义证据。
- 如果主证据本来就在 returns、差分或其他已弱化趋势影响的空间里，可以把该 protocol 明确标记为不适用，但不能默许省略说明。

## Non-Goals

- 不新增 machine-readable artifact
- 不新增统计库依赖
- 不要求所有 Test Evidence 场景都必须跑单位根/协整检验
- 不扩展到 `Holdout Validation`
- 不把 skill 改写成计量经济学教材

## Expected Outcome

更新后，agent 在 `Test Evidence` 阶段会更一致地做出以下判断：

- 什么时候需要怀疑虚假回归，而不是被 level-series 的高 `R^2` 或显著 `t` 值误导
- 什么时候 `ADF` / `Phillips-Perron` / `KPSS` 已足够，什么时候还要进一步交代 `Engle-Granger` / `Johansen`
- 什么时候 returns / differencing 已经是合理处理路径，因而单位根/协整 protocol 可以明确写“不适用”
- 什么时候不能把非平稳 series 之间的 level 回归直接升级为 formal `PASS`
