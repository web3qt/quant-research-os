---
name: qros-signal-diagnostics
description: Use when the user asks to inspect TSS signal diagnostics, signal evidence quality, event forward returns, hit rate, backtest metrics, holdout stability, or explicitly invokes qros-signal-diagnostics.
---

# QROS Signal Diagnostics

## Purpose

这是只读的 TSS 信号阶段 diagnostics skill。

它帮助研究员查看当前或指定 lineage 的 `time_series_signal` 阶段质量：

- 时间索引、样本切分和质量标记
- signal panel、signal event 和 route inheritance
- train threshold / variant ledger 诊断
- test 阶段 hit rate、forward return、base rate uplift、事件数量和 `mean_rank_ic`
- backtest 阶段成本后收益、回撤、换手、容量诊断
- holdout 阶段方向一致性、forward return 退化和组合退化

## User Invocation

用户通常只会在 Codex 里直接问，不会手动执行 shell command。优先识别这些问法：

```text
$qros-signal-diagnostics 看下当前 TSS lineage 的信号诊断
$qros-signal-diagnostics 帮我解释这条 TSS 研究线的 test evidence，重点看 hit rate、forward return 和事件数量
$qros-signal-diagnostics 看下 tss_backtest_ready 阶段的成本后收益、回撤和换手
$qros-signal-diagnostics 看下 tss_holdout_validation 阶段有没有样本外退化
$qros-signal-diagnostics mean_rank_ic 小于 0 说明什么，按高信号做多会不会站错方向
$qros-signal-diagnostics 不要只给数字，用中文解释这些指标说明什么
```

也要支持自然语言限定：

```text
$qros-signal-diagnostics 看下 lineage btc_tss_k 的 tss_test_evidence 阶段
$qros-signal-diagnostics 只看当前 lineage 的 forward return、命中率和事件数量
$qros-signal-diagnostics 帮我解释 missing diagnostics 里哪些最应该补
```

不要要求用户手动执行 shell wrapper。

## Explanation Requirements

不要只输出指标数字。必须用中文解释核心指标含义，并把指标和当前策略的关系讲清楚。

解释时至少覆盖：

- `mean_rank_ic < 0`：说明信号方向可能反了 / 当前窗口预测关系为负；如果策略按高信号做多，则可能系统性站错方向，需要检查信号方向、标签方向和持有窗口。
- `hit_rate`：命中率高于 50% 只表示方向判断略优于随机基准，还要结合 base rate、事件数量和成本后表现。
- `mean_forward_return`：forward return 表示信号触发后的平均后续收益；为负时高信号做多可能与实际收益方向冲突。
- `event_count` / 事件数量：事件太少时，命中率和平均收益容易被少数事件主导。
- `signal_frequency`：过低会导致交易机会和统计样本不足，过高可能接近长期持仓。
- 成本后收益弱于成本前收益：说明交易成本、滑点、换手或容量可能吃掉信号收益。
- holdout 退化：说明样本外表现弱于 test / backtest，需要检查过拟合、市场状态变化或成本假设。

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
./.qros/bin/qros-signal-diagnostics
./.qros/bin/qros-signal-diagnostics --lineage-id "<lineage_id>"
./.qros/bin/qros-signal-diagnostics --stage tss_test_evidence
./.qros/bin/qros-signal-diagnostics --lineage-id "<lineage_id>" --stage tss_backtest_ready --json
```

把用户自然语言里的 lineage 或 stage 约束映射到 wrapper 参数；如果用户没有指定，使用默认“最近修改 lineage + 自动推断 stage”。

## Supported Stages

当前只覆盖 `time_series_signal` 路线：

- `tss_data_ready`
- `tss_signal_ready`
- `tss_train_freeze`
- `tss_test_evidence`
- `tss_backtest_ready`
- `tss_holdout_validation`

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

`qros-signal-diagnostics` 只回答“做得怎么样、缺什么、哪些证据偏弱、指标和策略假设是什么关系”。

它不回答“是否正式通过阶段”。正式放行仍然由 `qros-review`、review preflight 和 runtime gate 决定。

如果 diagnostics 显示 `INSUFFICIENT_DATA` 或大量 missing metrics，应建议用户补齐诊断证据；不要直接说 stage 失败。

如果 diagnostics 显示 `GOOD`，也只能说 diagnostics evidence 看起来较完整；不要说可以跳过 review 或直接进入下一阶段。
