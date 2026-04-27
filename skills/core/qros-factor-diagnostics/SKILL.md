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

## Required Runtime

优先使用 repo-local wrapper：

```bash
./.qros/bin/qros-factor-diagnostics
./.qros/bin/qros-factor-diagnostics --lineage-id "<lineage_id>"
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
./.qros/bin/qros-factor-diagnostics --lineage-id "<lineage_id>" --stage csf_backtest_ready --json
```

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
