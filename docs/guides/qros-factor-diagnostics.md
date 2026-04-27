# QROS Factor Diagnostics

`qros-factor-diagnostics` 是可选 diagnostics 入口，用来查看横截面因子研究阶段的数据质量、因子质量、回测结果和 holdout 稳定性。

它不是 review，不是 gate，也不写 review closure。正式放行仍然由 `qros-review`、review preflight 和 runtime gate 决定。

## 怎么用

普通用户在 Codex 里直接问：

```text
$qros-factor-diagnostics 看下当前 lineage 的因子诊断
$qros-factor-diagnostics 看下 csf_test_evidence 阶段的 Rank IC、分层和稳定性
$qros-factor-diagnostics 看下 csf_backtest_ready 阶段的成本后收益、回撤、换手和容量
$qros-factor-diagnostics 看下 csf_holdout_validation 阶段有没有退化或 regime shift
$qros-factor-diagnostics mean IC 为负说明什么，跟当前策略方向有没有冲突
$qros-factor-diagnostics 不要只给数字，用中文解释这些指标说明什么
```

Codex 会读取当前 active research repo 的 `outputs/`，默认选择最近修改的 lineage。你也可以在问题里自然说明目标，例如：

```text
$qros-factor-diagnostics 看下 lineage btc_alt_k 的 csf_test_evidence 阶段
$qros-factor-diagnostics 只看当前 lineage 的 backtest 质量和成本侵蚀
$qros-factor-diagnostics 帮我解释 missing diagnostics 里哪些最应该补
```

普通用户不需要手动执行 `./.qros/bin/qros-factor-diagnostics`。

## 维护者 / 调试入口

如果需要 deterministic runtime debugging，才在 active research repo 根目录运行：

```bash
./.qros/bin/qros-factor-diagnostics
./.qros/bin/qros-factor-diagnostics --lineage-id <lineage_id>
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
./.qros/bin/qros-factor-diagnostics --lineage-id <lineage_id> --stage csf_backtest_ready --json
```

## 输出说明

输出会包含：

- `Health`：`GOOD`、`WATCH`、`WEAK`、`INSUFFICIENT_DATA` 或 `NOT_APPLICABLE`
- `Confidence`：`HIGH`、`MEDIUM` 或 `LOW`
- `interpretation`：用中文解释指标含义，例如 mean Rank IC 为负代表因子排序与未来收益排序反向
- `strategy_link`：说明该指标和当前策略假设的关系，例如是否可能和做多高因子组方向冲突
- observed diagnostics：已经从 formal artifacts 读到的指标
- missing diagnostics：当前缺少或 V1 尚未计算的指标
- evidence gaps：证据缺口
- next diagnostics：建议补充的诊断项

`Health` 只是研究质量诊断，不是正式 `PASS / FAIL`。

默认报告不应该只是指标数字。它应该先用中文说明这些数代表什么，再说明和当前策略假设的关系，例如：

- mean IC / Rank IC 为负：可能表示因子方向与未来收益反向，需要检查 `factor_direction` 是否写反。
- 成本后收益弱于成本前收益：可能表示信号有原始收益，但被换手、手续费、滑点或容量约束吃掉。
- holdout 退化：可能表示样本外市场状态不同、训练期过拟合，或成本/风险暴露没有延续。

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
