# QROS Factor Diagnostics Skill Design

## Goal

新增一个只读的因子阶段诊断入口，让研究员在不触发 review、不改变 stage、不写 closure 的前提下，查看当前横截面因子研究阶段的数据质量、因子质量、组合质量和稳健性证据。

这个能力回答：

- 当前阶段有哪些关键 diagnostics 已经存在？
- 这些指标看起来健康、偏弱，还是证据不足？
- 哪些应该看的指标缺失？
- 下一步应该补哪些诊断，才能让研究员更有把握进入正式 review？

它不回答：

- 这个 stage 是否正式通过？
- 是否允许进入下一阶段？
- review closure 是否可以写入？

这些仍然由 `qros-review`、review preflight 和 runtime gate 负责。

## Confirmed Product Decisions

1. 新能力定位为 diagnostics skill，不是 review skill。
2. diagnostics 输出健康判断，但不输出 stage `PASS` / `FAIL` verdict。
3. diagnostics 不写 `review/closure`，不写 `stage_completion_certificate.yaml`，不修改任何 `*_gate_decision.md`。
4. diagnostics 默认只读 formal artifacts；V1 不从原始行情数据完整重算所有指标。
5. diagnostics 可以指出“缺少某项指标”或“某项证据偏弱”，但不得把这些解释成正式 gate 结论。
6. diagnostics 应覆盖 `cross_sectional_factor` 路线的 6 个 post-mandate stages：
   - `csf_data_ready`
   - `csf_signal_ready`
   - `csf_train_freeze`
   - `csf_test_evidence`
   - `csf_backtest_ready`
   - `csf_holdout_validation`
7. V1 优先做 structured report 和 evidence gap detection；V2 再扩展完整指标计算库。

## Naming

推荐用户入口：

```text
$qros-factor-diagnostics
```

推荐 runtime wrapper：

```bash
./.qros/bin/qros-factor-diagnostics
```

命名不用 `gate`、`review` 或 `pass`，避免用户误解为正式放行工具。

## Scope

### In Scope

- 根据当前 research repo 的 `outputs/<lineage_id>/` 读取 CSF formal artifacts。
- 无 `--lineage-id` 时选择最近修改的 lineage。
- 支持显式传入 `--lineage-id`。
- 支持显式传入 `--stage`，否则从当前 lineage 状态或已存在 formal stage 推断。
- 输出人类可读诊断摘要。
- 支持 `--json` 输出 machine-readable diagnostics report。
- 对每个 stage 给出 expected diagnostics、observed diagnostics、missing diagnostics、risk notes 和 next diagnostics。

### Out Of Scope

- 不推进 `qros-research-session`。
- 不创建 lineage。
- 不 scaffold stage program。
- 不运行 author skill。
- 不运行 review skill。
- 不写 review closure。
- 不替代 `qros-progress`。
- 不生成 HTML dashboard。
- 不把 diagnostics health 映射成 QROS formal verdict。

## Architecture

新增能力采用三层结构：

```text
skill
  -> repo-local wrapper
  -> runtime diagnostics engine
```

### Skill Layer

新增：

```text
skills/core/qros-factor-diagnostics/SKILL.md
skills/core/qros-factor-diagnostics/agents/openai.yaml
```

skill 负责：

- 触发时优先运行 `./.qros/bin/qros-factor-diagnostics`。
- 根据用户提供的 lineage id 或 stage 传参。
- 解释输出时保持 diagnostics 口吻。
- 明确提醒：这不是 review verdict。

skill 不负责：

- 自己手写复杂指标计算。
- 自己决定正式 gate。
- 自己写 formal artifact。

### CLI Layer

新增：

```text
runtime/bin/qros-factor-diagnostics
runtime/scripts/run_factor_diagnostics.py
```

CLI 参数：

```bash
./.qros/bin/qros-factor-diagnostics
./.qros/bin/qros-factor-diagnostics --lineage-id "<lineage_id>"
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
./.qros/bin/qros-factor-diagnostics --lineage-id "<lineage_id>" --stage csf_backtest_ready --json
```

CLI 行为：

- 默认 `outputs_root = ./outputs`。
- 无 lineage id 时选择最近修改的 lineage。
- 无 stage 时优先读取当前 session/progress 状态；若无法读取，再选择最近存在 formal artifact 的 CSF stage。
- 只读取文件，不写任何输出。
- `--json` 输出稳定 schema。

### Runtime Layer

新增：

```text
runtime/tools/factor_diagnostics.py
```

runtime 负责：

- 发现 lineage。
- 发现或校验 stage。
- 加载 diagnostics profiles。
- 读取 formal artifacts。
- 汇总 observed metrics。
- 标记 missing metrics。
- 生成 diagnostics report。

V1 不依赖重型指标库，不从原始交易数据重建完整回测。它只消费已经 materialized 的 stage formal artifacts。

## Contracts

新增：

```text
contracts/diagnostics/factor_metric_library.yaml
contracts/diagnostics/csf_stage_diagnostic_profiles.yaml
```

### `factor_metric_library.yaml`

定义标准指标名称、类别、解释和最小字段要求。

示例结构：

```yaml
schema_id: factor-metric-library-v1
schema_version: v1
metrics:
  rank_ic:
    display_name: Rank IC
    category: predictive_power
    meaning: 衡量因子排序与未来收益排序的一致性。
    expected_direction: higher_is_better
    required_inputs:
      - rank_ic_timeseries.parquet.rank_ic
    v1_observation_mode: read_existing
  top_bottom_spread:
    display_name: Top-Bottom Spread
    category: bucket_sorting
    meaning: 衡量最高组和最低组未来收益差。
    expected_direction: higher_is_better
    required_inputs:
      - bucket_returns.parquet
    v1_observation_mode: gap_detect_only
```

`v1_observation_mode` 允许三种值：

- `read_existing`：V1 可以直接读取已有字段。
- `derive_from_existing`：V1 可以从已有 stage artifact 轻量计算。
- `gap_detect_only`：V1 只判断是否存在足够输入，不做完整计算。

### `csf_stage_diagnostic_profiles.yaml`

定义每个 CSF stage 应该看哪些 diagnostics。

示例结构：

```yaml
schema_id: csf-stage-diagnostic-profiles-v1
schema_version: v1
profiles:
  csf_test_evidence:
    health_dimensions:
      predictive_power:
        required_metrics:
          - rank_ic
          - rank_ic_win_rate
          - icir
        recommended_metrics:
          - ic_skew
          - ic_autocorrelation
      bucket_sorting:
        required_metrics:
          - top_bottom_spread
          - monotonicity
          - bucket_win_rate
      evidence_stability:
        required_metrics:
          - breadth
          - subperiod_stability
```

Profiles 不定义 formal gate。它只定义 diagnostics 期望。

## Report Schema

JSON 输出建议：

```json
{
  "schema_id": "qros-factor-diagnostics-report-v1",
  "lineage_id": "btc_alt_transmission_v1",
  "stage": "csf_test_evidence",
  "route": "cross_sectional_factor",
  "health": "WATCH",
  "confidence": "MEDIUM",
  "formal_verdict_boundary": "diagnostics_only_not_review",
  "dimensions": [
    {
      "name": "predictive_power",
      "health": "WATCH",
      "observed_metrics": [
        {
          "metric_id": "rank_ic",
          "value": 0.034,
          "status": "observed",
          "source": "rank_ic_summary.json.mean_rank_ic"
        }
      ],
      "missing_metrics": [
        {
          "metric_id": "icir",
          "reason": "rank_ic_timeseries.parquet exists but ICIR derivation is not implemented in V1"
        }
      ],
      "risk_notes": [
        "Rank IC is positive, but stability diagnostics are incomplete."
      ]
    }
  ],
  "evidence_gaps": [
    "Top-Bottom Spread is not standardized as an explicit metric column."
  ],
  "next_diagnostics": [
    "Add ICIR and Rank IC win rate from rank_ic_timeseries.parquet.",
    "Add standardized top_bottom_spread from bucket_returns.parquet."
  ]
}
```

Allowed health values:

- `GOOD`
- `WATCH`
- `WEAK`
- `INSUFFICIENT_DATA`
- `NOT_APPLICABLE`

Allowed confidence values:

- `HIGH`
- `MEDIUM`
- `LOW`

Health is not a QROS formal verdict. It is an interpretation layer for research quality.

## Stage Profiles

### `csf_data_ready`

Main question:

> 横截面研究的数据底座是否足够完整、稳定、可交易？

Diagnostics:

- coverage ratio
- asset count
- split sample adequacy
- universe membership non-empty
- eligibility mask uniqueness
- liquidity panel availability
- beta input availability

V1 sources:

- `panel_manifest.json`
- `cross_section_coverage.parquet`
- `split_sample_adequacy_report.yaml`
- `asset_universe_membership.parquet`
- `eligibility_base_mask.parquet`
- `shared_feature_base/liquidity_panel.parquet`
- `shared_feature_base/beta_inputs.parquet`

### `csf_signal_ready`

Main question:

> 因子是否被干净、可复现、无未来信息地 materialize 成 date x asset panel？

Diagnostics:

- factor coverage
- factor score non-null ratio
- final score numeric validity
- input field binding completeness
- route inheritance consistency
- factor direction presence
- optional factor autocorrelation readiness

V1 sources:

- `factor_panel.parquet`
- `factor_manifest.yaml`
- `factor_coverage_report.parquet`
- `route_inheritance_contract.yaml`
- `factor_field_dictionary.md`

### `csf_train_freeze`

Main question:

> 训练阶段是否只冻结合法研究轴，并留下可审计的 variant selection / rejection 证据？

Diagnostics:

- candidate / kept / rejected variant coverage
- reject reason completeness
- quality score availability
- bucket min names
- neutralization diagnostics availability
- train-governable axes clarity

V1 sources:

- `csf_train_freeze.yaml`
- `train_factor_quality.parquet`
- `train_variant_ledger.csv`
- `train_variant_rejects.csv`
- `train_bucket_diagnostics.parquet`
- `train_neutralization_diagnostics.parquet`

### `csf_test_evidence`

Main question:

> 因子在独立 test 样本中是否仍有预测能力、排序能力和稳定性证据？

Diagnostics:

- IC
- Rank IC
- ICIR
- Rank IC win rate
- Top-Bottom Spread
- monotonicity
- bucket win rate
- breadth
- subperiod stability

V1 sources:

- `rank_ic_timeseries.parquet`
- `rank_ic_summary.json`
- `bucket_returns.parquet`
- `monotonicity_report.json`
- `breadth_coverage_report.parquet`
- `subperiod_stability_report.json`
- `csf_test_gate_table.csv`

V1 notes:

- `mean_rank_ic` can be read directly.
- Rank IC win rate and ICIR can be derived from `rank_ic_timeseries.parquet`.
- Top-Bottom Spread may require standardizing bucket labels; if labels are insufficient, mark as evidence gap instead of guessing.

### `csf_backtest_ready`

Main question:

> 因子能否转成可交易、成本后仍有意义的组合表现？

Diagnostics:

- mean gross return
- mean net return
- gross/net erosion
- max drawdown
- turnover
- capacity utilization
- name-level concentration
- Alpha
- Beta
- Sharpe
- Sortino
- Calmar
- Profit Factor

V1 sources:

- `portfolio_summary.parquet`
- `turnover_capacity_report.parquet`
- `drawdown_report.json`
- `name_level_metrics.parquet`
- `csf_backtest_gate_table.csv`
- `cost_assumption_report.md`

V1 notes:

- Directly read `mean_gross_return`, `mean_net_return`, `max_drawdown`, `turnover`, `capacity_utilization`.
- Sharpe, Sortino, Calmar, Profit Factor require return series or trade/PnL series. If absent, mark missing rather than infer from summary.

### `csf_holdout_validation`

Main question:

> 最终冻结方案在 holdout 中是否方向一致、没有塌陷，并且退化可解释？

Diagnostics:

- direction match
- holdout mean net return
- holdout vs backtest net return delta
- holdout vs backtest drawdown delta
- coverage
- breadth
- bucket stability score
- rolling stability status
- regime shift audit status

V1 sources:

- `holdout_factor_diagnostics.parquet`
- `holdout_test_compare.parquet`
- `holdout_portfolio_compare.parquet`
- `rolling_holdout_stability.json`
- `regime_shift_audit.json`

## Human Output Format

默认文本输出：

```text
QROS Factor Diagnostics

Lineage: <lineage_id>
Stage: <stage>
Route: cross_sectional_factor
Health: WATCH
Confidence: MEDIUM
Boundary: diagnostics only, not review verdict

Observed
- mean_rank_ic: 0.034
- coverage_ratio_min: 0.92

Missing / Not Computed
- ICIR: rank_ic_timeseries exists, V1 derivation not enabled
- Sharpe: portfolio return series not present

Risk Notes
- Bucket returns exist, but Top-Bottom Spread is not standardized as a column.
- Evidence may be positive but stability diagnostics are incomplete.

Next Diagnostics
- Add standardized top_bottom_spread.
- Derive rank_ic_win_rate and ICIR from rank_ic_timeseries.parquet.
```

## Error Handling

Expected user-facing failures:

- no `outputs/` directory
- no lineage found
- requested lineage does not exist
- requested stage is not a CSF diagnostics-supported stage
- formal directory missing
- formal artifacts exist but required files are unreadable

Error messages must be actionable:

```text
No CSF formal artifacts found for lineage <lineage_id>.
Run qros-progress to confirm current stage, or pass --stage explicitly.
```

The command must not create missing directories as part of error recovery.

## Relationship To Existing QROS Commands

| Command / Skill | Role | Relationship |
| --- | --- | --- |
| `$qros-progress` | Current state lookup | diagnostics may use similar lineage selection, but adds metric interpretation |
| `$qros-stage-display` | Presentation guidance | diagnostics is evidence quality, not display layout |
| `$qros-review` | Formal review / closure | diagnostics can be read before review, but cannot decide review verdict |
| `$qros-research-session` | Authoring / orchestration | diagnostics does not advance session |
| `qros-validate-stage` | Artifact contract validation | diagnostics may report validation gaps, but does not replace validator |

## Testing Strategy

### Contract Tests

Add tests for:

- `contracts/diagnostics/factor_metric_library.yaml` exists.
- every metric has `display_name`, `category`, `meaning`, `expected_direction`, `v1_observation_mode`.
- `contracts/diagnostics/csf_stage_diagnostic_profiles.yaml` exists.
- every supported CSF stage has at least one health dimension.
- every metric referenced by a stage profile exists in the metric library.

### Runtime Tests

Add tests for:

- no outputs root produces a clear error and creates nothing.
- newest lineage selection matches `qros-progress` expectations.
- `--lineage-id` selects an explicit lineage.
- `--stage` rejects unsupported stages.
- `csf_test_evidence` report reads `mean_rank_ic`.
- `csf_backtest_ready` report reads `mean_net_return`, `mean_gross_return`, `max_drawdown`, `turnover`, `capacity_utilization`.
- `csf_holdout_validation` report reads `direction_match`, `holdout_mean_net_return`, `net_return_delta`.
- missing metrics are reported as diagnostics gaps, not process failures.
- `--json` output conforms to report schema.

### Skill Tests

Add tests for:

- skill tree includes `qros-factor-diagnostics`.
- skill body says it is read-only.
- skill body explicitly says it does not replace `qros-review`.
- skill body forbids writing closure artifacts or gate decisions.
- install/bootstrap includes `qros-factor-diagnostics` wrapper.

### Documentation Tests

Add tests for:

- README or Codex docs mention `$qros-factor-diagnostics` as optional diagnostics.
- docs do not describe it as a review or gate command.
- factor diagnostics guide lists supported CSF stages.

## Rollout Plan

### V1

- Add diagnostics contracts.
- Add runtime report generation from existing formal artifacts.
- Add repo-local wrapper.
- Add skill.
- Add docs and focused tests.

### V2

- Derive ICIR and Rank IC win rate from `rank_ic_timeseries.parquet`.
- Standardize Top-Bottom Spread calculation from `bucket_returns.parquet`.
- Add portfolio return-series support for Sharpe, Sortino, Calmar, Volatility and Profit Factor.
- Add optional `--write-report` only if report persistence is needed.

If `--write-report` is added later, it must write outside formal and review closure directories:

```text
outputs/<lineage_id>/diagnostics/<stage>/factor_diagnostics_report.json
```

It must remain non-authoritative.

## Verification Scope

This feature touches skill discovery, runtime wrappers, contracts, docs and tests.

Minimum verification for implementation:

```bash
python -m pytest tests/contracts/test_factor_diagnostic_contracts.py tests/runtime/test_factor_diagnostics.py tests/bootstrap/test_native_skill_runtime_paths.py tests/docs/test_factor_diagnostics_docs.py -q
python runtime/scripts/run_verification_tier.py --tier smoke
```

Because this feature must not change session stage flow, review semantics, route selection, or gate behavior, full-smoke is only required if implementation accidentally touches those areas.
