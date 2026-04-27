# QROS Factor Diagnostics

`qros-factor-diagnostics` 是可选 diagnostics 入口，用来查看横截面因子研究阶段的数据质量、因子质量、回测结果和 holdout 稳定性。

它不是 review，不是 gate，也不写 review closure。正式放行仍然由 `qros-review`、review preflight 和 runtime gate 决定。

## 怎么用

在 active research repo 根目录运行：

```bash
./.qros/bin/qros-factor-diagnostics
./.qros/bin/qros-factor-diagnostics --lineage-id <lineage_id>
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
./.qros/bin/qros-factor-diagnostics --lineage-id <lineage_id> --stage csf_backtest_ready --json
```

在 Codex 里可以使用：

```text
$qros-factor-diagnostics
```

## 输出说明

输出会包含：

- `Health`：`GOOD`、`WATCH`、`WEAK`、`INSUFFICIENT_DATA` 或 `NOT_APPLICABLE`
- `Confidence`：`HIGH`、`MEDIUM` 或 `LOW`
- observed diagnostics：已经从 formal artifacts 读到的指标
- missing diagnostics：当前缺少或 V1 尚未计算的指标
- evidence gaps：证据缺口
- next diagnostics：建议补充的诊断项

`Health` 只是研究质量诊断，不是正式 `PASS / FAIL`。

## 支持阶段

当前覆盖 `cross_sectional_factor` 路线：

| Stage | 主要 diagnostics |
| --- | --- |
| `csf_data_ready` | coverage、asset_count、split sample adequacy、membership、eligibility、liquidity、beta inputs |
| `csf_signal_ready` | factor coverage、score 非空率、factor_direction、input field binding、route inheritance |
| `csf_train_freeze` | variant ledger、reject reason、train quality score、bucket min names、neutralization diagnostics |
| `csf_test_evidence` | Rank IC、Rank IC win rate、ICIR、Top-Bottom Spread、monotonicity、breadth、subperiod stability |
| `csf_backtest_ready` | gross/net return、gross/net erosion、max drawdown、turnover、capacity utilization、Sharpe / Profit Factor 缺口 |
| `csf_holdout_validation` | direction_match、holdout mean net return、net return delta、drawdown delta、rolling stability、regime shift audit |

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
  -> qros-factor-diagnostics 做质量体检
  -> 补齐缺失 diagnostics
  -> qros-review 做正式审查
```
