# QROS Signal Diagnostics

`qros-signal-diagnostics` 是可选 diagnostics 入口，用来查看 TSS (`time_series_signal`) 研究阶段的时间序列信号质量、事件证据、回测结果和 holdout 稳定性。

它不是 review，不是 gate，也不写 review closure。正式放行仍然由 `qros-review`、review preflight 和 runtime gate 决定。

## 怎么用

普通用户在 Codex 里直接问：

```text
$qros-signal-diagnostics 看下当前 TSS lineage 的信号诊断
$qros-signal-diagnostics 帮我解释这条 TSS 研究线的 test evidence，重点看 hit rate、forward return 和事件数量
$qros-signal-diagnostics 看下 tss_backtest_ready 阶段的成本后收益、回撤和换手
$qros-signal-diagnostics 看下 tss_holdout_validation 阶段有没有样本外退化
$qros-signal-diagnostics mean_rank_ic 小于 0 说明什么，按高信号做多会不会站错方向
$qros-signal-diagnostics 不要只给数字，用中文解释这些指标说明什么
```

Codex 会读取当前 active research repo 的 `outputs/`，默认选择最近修改的 lineage。你也可以在问题里自然说明目标，例如：

```text
$qros-signal-diagnostics 看下 lineage btc_tss_k 的 tss_test_evidence 阶段
$qros-signal-diagnostics 只看当前 lineage 的 forward return、命中率和事件数量
$qros-signal-diagnostics 帮我解释 missing diagnostics 里哪些最应该补
```

普通用户不需要手动执行 `./.qros/bin/qros-signal-diagnostics`。

## 维护者 / 调试入口

如果需要 deterministic runtime debugging，才在 active research repo 根目录运行：

```bash
./.qros/bin/qros-signal-diagnostics
./.qros/bin/qros-signal-diagnostics --lineage-id <lineage_id>
./.qros/bin/qros-signal-diagnostics --stage tss_test_evidence
./.qros/bin/qros-signal-diagnostics --lineage-id <lineage_id> --stage tss_backtest_ready --json
```

## 输出说明

输出会包含：

- `Health`：`GOOD`、`WATCH`、`WEAK`、`INSUFFICIENT_DATA` 或 `NOT_APPLICABLE`
- `Confidence`：`HIGH`、`MEDIUM` 或 `LOW`
- `interpretation` / `explanation`：用中文解释指标含义，例如 `mean_rank_ic < 0` 代表信号方向可能反了 / 当前窗口预测关系为负
- `strategy_link`：说明该指标和当前策略假设的关系，例如按高信号做多时是否可能系统性站错方向
- observed diagnostics：已经从 formal artifacts 读到的指标
- missing diagnostics：当前缺少或 V1 尚未计算的指标
- evidence gaps：证据缺口
- next diagnostics：建议补充的诊断项

`Health` 只是研究质量诊断，不是正式 `PASS / FAIL`。

默认报告不应该只是指标数字。它应该先用中文说明这些数代表什么，再说明和当前策略假设的关系，例如：

- `mean_rank_ic < 0`：可能表示信号方向可能反了；如果策略按高信号做多，则可能系统性站错方向。
- `hit_rate` 高于 50%：只能说明方向判断略优于随机基准，还要结合 base rate uplift、事件数量和成本后表现。
- `mean_forward_return` 为负：说明信号触发后的平均后续收益为负，高信号做多可能与收益方向冲突。
- 事件数量太少：命中率、平均收益和 Rank IC 容易被少数事件主导。
- 成本后收益弱于成本前收益：可能表示信号有原始收益，但被换手、手续费、滑点或容量约束吃掉。
- holdout 退化：可能表示样本外市场状态不同、测试期过拟合，或成本/风险暴露没有延续。

## 支持阶段

当前覆盖 `time_series_signal` 路线：

| Stage | 主要 diagnostics |
| --- | --- |
| `tss_data_ready` | time index coverage、asset_count、split sample adequacy、quality flag rate |
| `tss_signal_ready` | signal 非空率、signal event count、parameter count、route inheritance |
| `tss_train_freeze` | threshold ledger、variant ledger、reject reason、train quality score |
| `tss_test_evidence` | mean forward return、hit rate、base rate uplift、event count、signal frequency、mean_rank_ic、MFE/MAE |
| `tss_backtest_ready` | gross/net return、gross/net erosion、max drawdown、turnover、capacity utilization |
| `tss_holdout_validation` | direction_match、holdout forward return、holdout hit rate、net return delta、drawdown delta |

## 边界

这个命令只读：

- 不创建 lineage
- 不写 formal artifact
- 不写 `review/closure`
- 不写 `stage_completion_certificate.yaml`
- 不修改任何 `*_gate_decision.md`
- 不推进 stage
- 不替代 `qros-review`

建议使用方式：

```text
author 完成阶段
  -> qros-signal-diagnostics 做 TSS 信号质量体检
  -> 补齐缺失 diagnostics
  -> qros-review 做正式审查
```
