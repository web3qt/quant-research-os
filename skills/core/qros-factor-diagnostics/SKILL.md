---
name: qros-factor-diagnostics
description: Use when the user asks to inspect CSF factor diagnostics, stage health, factor quality, backtest metrics, holdout stability, or explicitly invokes qros-factor-diagnostics.
---

# QROS Factor Diagnostics

## Purpose

这是只读的 CSF 因子阶段 diagnostics skill。

它帮助研究员查看当前或指定 lineage 的横截面因子阶段质量：

- 数据覆盖和样本充足性
- 因子面板与字段绑定质量
- train variant / bucket / neutralization 诊断
- test 阶段 Rank IC、ICIR、分层与稳定性诊断
- backtest 阶段成本后收益、回撤、换手、容量诊断
- holdout 阶段方向一致性、退化幅度和 regime shift 诊断

## User Invocation

用户通常只会在 Codex 里直接问，不会手动执行 shell command。优先识别这些问法：

```text
$qros-factor-diagnostics 看下当前 lineage 的因子诊断
$qros-factor-diagnostics 看下 csf_test_evidence 阶段的 Rank IC、分层和稳定性
$qros-factor-diagnostics 看下 csf_backtest_ready 阶段的成本后收益、回撤、换手和容量
$qros-factor-diagnostics 看下 csf_holdout_validation 阶段有没有退化或 regime shift
$qros-factor-diagnostics mean IC 为负说明什么，跟当前策略方向有没有冲突
$qros-factor-diagnostics 不要只给数字，用中文解释这些指标说明什么
```

也要支持自然语言限定：

```text
$qros-factor-diagnostics 看下 lineage btc_alt_k 的 csf_test_evidence 阶段
$qros-factor-diagnostics 只看当前 lineage 的 backtest 质量和成本侵蚀
$qros-factor-diagnostics 帮我解释 missing diagnostics 里哪些最应该补
```

不要要求用户手动执行 shell wrapper。

## Explanation Requirements

不要只输出指标数字。必须用中文解释核心指标含义，并把指标和当前策略的关系讲清楚。

解释时至少覆盖：

- mean IC / Rank IC 为负：说明因子排序和未来收益排序反向，可能和做多高因子组的方向冲突，需要检查 `factor_direction`。
- Rank IC 胜率或 ICIR 偏弱：说明预测方向不稳定，可能只在少数日期有效。
- Top-Bottom Spread 或分层单调性偏弱：说明因子排序不一定能转化成稳定分组收益。
- 成本后收益弱于成本前收益：说明交易成本、滑点、换手或容量可能吃掉信号收益。
- 最大回撤较深：说明即使均值收益可用，也需要关注仓位、风控和策略承受能力。
- holdout 退化：说明样本外表现弱于 backtest，需要检查过拟合、市场状态变化或成本假设。

推荐报告结构：

```text
先说结论
怎么理解这些数
跟当前策略的关系
缺什么证据
下一步优先检查什么
```

## Runtime Execution

当 skill 触发后，由 agent 在 active research repo 内部优先使用 repo-local wrapper：

```bash
./.qros/bin/qros-factor-diagnostics
./.qros/bin/qros-factor-diagnostics --lineage-id "<lineage_id>"
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
./.qros/bin/qros-factor-diagnostics --lineage-id "<lineage_id>" --stage csf_backtest_ready --json
```

把用户自然语言里的 lineage 或 stage 约束映射到 wrapper 参数；如果用户没有指定，使用默认“最近修改 lineage + 自动推断 stage”。

## Supported Stages

当前只覆盖 `cross_sectional_factor` 路线：

- `csf_data_ready`
- `csf_signal_ready`
- `csf_train_freeze`
- `csf_test_evidence`
- `csf_backtest_ready`
- `csf_holdout_validation`

## Hard Boundaries

- 只读。
- 不写 artifact。
- 不创建 lineage。
- 不 scaffold stage program。
- 不运行 author skill。
- 不运行 review skill。
- 不替代 `qros-review`。
- 不写 `review/closure`。
- 不写 `stage_completion_certificate.yaml`。
- 不修改任何 `*_gate_decision.md`。
- 不推进 stage。
- 不把 `Health` 解释成正式 `PASS / FAIL`。

## Reporting Rules

汇报时至少覆盖：

- `lineage_id`
- `stage`
- `health`
- `confidence`
- `formal_verdict_boundary`
- observed diagnostics
- missing diagnostics
- evidence gaps
- next diagnostics

必须明确说明：

```text
这是 diagnostics，不是 review verdict，也不是 gate verdict。
```

## Interpretation Discipline

`qros-factor-diagnostics` 只回答“做得怎么样、缺什么、哪些证据偏弱”。

它不回答“是否正式通过阶段”。正式放行仍然由 `qros-review`、review preflight 和 runtime gate 决定。

如果 diagnostics 显示 `INSUFFICIENT_DATA` 或大量 missing metrics，应建议用户补齐诊断证据；不要直接说 stage 失败。

如果 diagnostics 显示 `GOOD`，也只能说 diagnostics evidence 看起来较完整；不要说可以跳过 review 或直接进入下一阶段。
