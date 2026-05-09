# QROS TSS Route Prefix Design

## Goal

将原先 `time_series_signal` 路线的 post-mandate 主线正式改造成带 `tss_` 前缀的路线级流程，并在流程完整度上对齐现有 `csf_*` 横截面因子框架。

这次改造的目标不是新增第三条研究路线，而是把原先默认的时序信号主线重命名并收紧为：

```text
time_series_signal
  -> 02_tss_data_ready
  -> 03_tss_signal_ready
  -> 04_tss_train_freeze
  -> 05_tss_test_evidence
  -> 06_tss_backtest_ready
  -> 07_tss_holdout_validation
```

其中 `TSS = Time Series Signal`，语义是：单个资产基于自身历史状态预测自身未来路径。

## Confirmed Product Decisions

1. `research_route = time_series_signal` 的 canonical post-mandate stages 全部改为 `tss_*`。
2. 原先无前缀的 `data_ready`、`signal_ready`、`train_freeze`、`test_evidence`、`backtest_ready`、`holdout_validation` 不再作为 canonical time-series 主线。
3. 新 TSS 主线的流程形态要与 CSF 主线对称，但业务语义不能照搬横截面因子。
4. TSS 关注 `asset x timestamp x horizon x param_id`，而不是 CSF 的 `date x asset` 排序面板。
5. TSS 需要自己的 artifact contracts、semantic validators、author/review skills、runtime builders、stage diagnostics。
6. TSS diagnostics 应独立于 `$qros-factor-diagnostics`，优先新增 `$qros-signal-diagnostics`。
7. 本设计文档是目标设计，不表示当前 runtime 已经完成这些行为。

## Route Shape

最终路线分叉应变为：

```text
00_idea_intake
01_mandate
├─ time_series_signal
│  ├─ 02_tss_data_ready
│  ├─ 03_tss_signal_ready
│  ├─ 04_tss_train_freeze
│  ├─ 05_tss_test_evidence
│  ├─ 06_tss_backtest_ready
│  └─ 07_tss_holdout_validation
└─ cross_sectional_factor
   ├─ 02_csf_data_ready
   ├─ 03_csf_signal_ready
   ├─ 04_csf_train_freeze
   ├─ 05_csf_test_evidence
   ├─ 06_csf_backtest_ready
   └─ 07_csf_holdout_validation
```

Stage ids、session stages、skill names、artifact contracts 都应显式使用 `tss_` 前缀。

Program directory 可以继续按 route 分层，保持与 CSF 现有模式一致：

```text
outputs/<lineage_id>/program/time_series_signal/data_ready/
outputs/<lineage_id>/program/time_series_signal/signal_ready/
outputs/<lineage_id>/program/time_series_signal/train_freeze/
outputs/<lineage_id>/program/time_series_signal/test_evidence/
outputs/<lineage_id>/program/time_series_signal/backtest_ready/
outputs/<lineage_id>/program/time_series_signal/holdout_validation/
```

Formal stage directory 必须带 `tss_` 前缀：

```text
outputs/<lineage_id>/02_tss_data_ready/
outputs/<lineage_id>/03_tss_signal_ready/
outputs/<lineage_id>/04_tss_train_freeze/
outputs/<lineage_id>/05_tss_test_evidence/
outputs/<lineage_id>/06_tss_backtest_ready/
outputs/<lineage_id>/07_tss_holdout_validation/
```

## CSF / TSS Semantic Split

CSF 的核心问题：

```text
同一时间点，哪些资产更强？
date x asset -> factor score -> rank / bucket / portfolio
```

TSS 的核心问题：

```text
某个资产在某个状态下，未来路径是否有优势？
asset x timestamp -> signal / trigger -> future return / path -> trade
```

因此 TSS 不应复用 CSF 的 Rank IC、Top-Bottom Spread、bucket monotonicity 作为主证据。TSS 的主证据应围绕：

- forward return
- hit rate
- base-rate uplift
- event study
- signal frequency
- threshold stability
- path risk, such as MFE / MAE
- cost and funding drag
- holdout direction consistency

## Stage Design

### `tss_data_ready`

Purpose: 产出单资产时序预测路线的数据底座、统一时间索引、质量标记和 forward label base。

Core question: 是否已经形成可复现、无前视、可供信号层消费的 `asset x timestamp` 时序样本底座。

Required outputs:

```text
time_index_manifest.json
asset_time_index.parquet
aligned_asset_bars/
feature_base/
forward_label_base/
quality_flags.parquet
split_sample_adequacy_report.yaml
tss_data_contract.md
tss_data_ready_gate_decision.md
run_manifest.json
rebuild_tss_data_ready.py
artifact_catalog.md
field_dictionary.md
```

Key machine semantics:

- `asset_time_index.parquet` 主键为 `asset, timestamp`。
- `aligned_asset_bars/` 只保存 as-of 可用行情与状态字段。
- `forward_label_base/` 保存未来收益或未来路径标签，但必须明确声明不能被 `tss_signal_ready` 当作输入字段。
- `quality_flags.parquet` 显式记录 missing、stale、bad price、outlier、low liquidity。
- `split_sample_adequacy_report.yaml` 的 `sample_unit` 应为 `asset_time_observation`。

Blocking checks:

- `asset, timestamp` 主键唯一。
- open time / close time 语义不得混用。
- forward labels 的 label timestamp 必须严格晚于 signal timestamp。
- train/test/backtest/holdout split 均有足够样本。
- 不得静默 forward-fill 或静默删除异常样本。

### `tss_signal_ready`

Purpose: 将 mandate 已冻结的时序信号表达实例化为可复现的 signal / trigger / forecast panel。

Core question: 下游 train/test 到底消费哪个 `param_id`、哪个 signal field、哪个 horizon、哪个触发语义。

Required outputs:

```text
signal_manifest.yaml
param_manifest.csv
signal_panel.parquet
signal_event_panel.parquet
signal_coverage_report.parquet
route_inheritance_contract.yaml
tss_signal_contract.md
signal_field_dictionary.md
tss_signal_ready_gate_decision.md
run_manifest.json
artifact_catalog.md
field_dictionary.md
```

Key machine semantics:

- `signal_panel.parquet` 主键为 `asset, timestamp, param_id, horizon`。
- `signal_event_panel.parquet` 记录触发事件，至少包含 `triggered`, `signal_side`, `event_id`。
- `signal_manifest.yaml` 冻结 signal expression、input fields、as-of semantics、horizon set。
- `param_manifest.csv` 冻结所有下游允许消费的 `param_id`。
- `route_inheritance_contract.yaml` 必须声明 `research_route: time_series_signal` 和 `inheritance_mode: exact_copy`。

Blocking checks:

- 所有 input fields 必须来自 `tss_data_ready` 的 formal artifacts。
- `forward_label_base` 字段不得出现在 signal input map。
- 下游使用的 `param_id` 必须已在本阶段物化。
- `signal_side` 和 horizon 语义必须明确，不能到 test/backtest 再解释。

### `tss_train_freeze`

Purpose: 在训练窗内冻结阈值、事件去重、horizon、过滤条件和 admissible variants。

Core question: 后续 test 复用哪把已经冻结的尺子，而不是边验证边调 threshold。

Required outputs:

```text
tss_train_freeze.yaml
train_threshold_ledger.csv
train_variant_ledger.csv
train_variant_rejects.csv
train_signal_quality.parquet
train_event_diagnostics.parquet
train_calibration_report.parquet
tss_train_contract.md
tss_train_freeze_gate_decision.md
run_manifest.json
artifact_catalog.md
field_dictionary.md
```

Key machine semantics:

- `tss_train_freeze.yaml` 冻结 threshold rule、horizon rule、event dedupe rule、purge/embargo policy、cooldown policy。
- `train_variant_ledger.csv` 记录所有 candidate variants。
- `train_variant_rejects.csv` 记录 reject reason，不允许只保留通过者。
- `train_event_diagnostics.parquet` 记录事件频率、overlap rate、base rate、class imbalance。

Blocking checks:

- 不得用 test/backtest/holdout 结果回写 threshold。
- overlap label、purge、embargo 语义必须显式。
- per-symbol calibration 与 pooled calibration 必须明确二选一或说明组合规则。
- kept variants 必须来自 signal-ready 已冻结 param set。

### `tss_test_evidence`

Purpose: 在独立测试窗验证冻结信号是否具有时序预测优势，并冻结可进入 backtest 的 signal variants。

Core question: 信号触发后，未来路径是否比 base rate 更好，且证据不是由少数事件或窗口支撑。

Required outputs:

```text
event_forward_return.parquet
signal_performance_summary.json
event_study_curve.parquet
path_risk_report.parquet
frequency_stability_report.parquet
subperiod_stability_report.json
tss_test_gate_table.csv
tss_selected_variants_test.csv
tss_test_contract.md
tss_test_gate_decision.md
run_manifest.json
artifact_catalog.md
field_dictionary.md
```

Key metrics:

- mean forward return
- median forward return
- hit rate
- base-rate uplift
- precision / recall when signal is event-like
- event count
- signal frequency
- HAC or bootstrap t-stat
- MFE / MAE
- horizon decay
- subperiod stability

Blocking checks:

- 只能复用 `tss_train_freeze` 的 frozen thresholds 和 kept variants。
- 不得在 test 内新增 param_id、horizon 或 threshold。
- `tss_selected_variants_test.csv` 必须来自全量 test ledger。
- 搜索量较大时必须记录 multiple testing 处理或免做理由。
- 事件数不足时不得用均值表现冒充稳定结论。

### `tss_backtest_ready`

Purpose: 将测试通过的时序信号映射成正式交易生命周期，并验证成本后可交易性。

Core question: 冻结信号进入真实交易规则后，是否仍具备成本后收益和可控风险。

Required outputs:

```text
strategy_contract.yaml
engine_compare.csv
position_timeseries.parquet
order_ledger.csv
trade_ledger.csv
pnl_timeseries.parquet
cost_funding_report.parquet
risk_report.parquet
drawdown_report.json
tss_backtest_gate_table.csv
tss_backtest_contract.md
tss_backtest_ready_gate_decision.md
run_manifest.json
artifact_catalog.md
field_dictionary.md
```

Key machine semantics:

- `strategy_contract.yaml` 冻结 entry、exit、holding period、cooldown、stop loss、take profit、position sizing、leverage、margin、funding、fees、slippage。
- `position_timeseries.parquet` 记录每个 timestamp 的持仓状态。
- `order_ledger.csv` 和 `trade_ledger.csv` 区分意图订单与实际成交。
- `engine_compare.csv` 保留双引擎或等价语义对照纪律。

Blocking checks:

- 只能消费 `tss_selected_variants_test.csv` 中冻结的 variants。
- backtest 内不得重新挑选 signal、symbol、horizon 或 threshold。
- 必须报 net after cost，不得只报 gross。
- 资金费率、手续费、滑点、持仓风险口径必须可解释。
- 若双引擎语义不一致，不能进入 holdout。

### `tss_holdout_validation`

Purpose: 在最终未参与设计的窗口验证冻结信号和交易规则是否仍然稳定。

Core question: 最终冻结方案在 holdout 中是否出现方向翻转、触发频率塌陷、路径风险恶化或成本后失效。

Required outputs:

```text
tss_holdout_run_manifest.json
holdout_signal_diagnostics.parquet
holdout_event_compare.parquet
holdout_backtest_compare.parquet
threshold_drift_audit.json
regime_shift_audit.json
tss_holdout_gate_decision.md
artifact_catalog.md
field_dictionary.md
```

Blocking checks:

- holdout 只复用冻结方案，不调参。
- signal direction 不能明显翻向。
- signal frequency 不能塌陷到无法解释。
- net after cost 不能由成本或 funding 完全吞噬。
- threshold drift 或 regime shift 明显时必须显式审计。

## Runtime And Contract Changes

### Artifact Contracts

新增：

```text
contracts/artifacts/tss_data_ready_artifacts.yaml
contracts/artifacts/tss_signal_ready_artifacts.yaml
contracts/artifacts/tss_train_freeze_artifacts.yaml
contracts/artifacts/tss_test_evidence_artifacts.yaml
contracts/artifacts/tss_backtest_ready_artifacts.yaml
contracts/artifacts/tss_holdout_validation_artifacts.yaml
```

每个 contract 必须设置：

```yaml
stage: tss_<stage_name>
unknown_machine_top_level_fields: forbid
```

所有 machine-readable artifacts 必须有字段级描述，避免只写 stage-level 文档。

### Stage Gates

`contracts/stages/workflow_stage_gates.yaml` 需要新增或替换为：

```text
tss_data_ready
tss_signal_ready
tss_train_freeze
tss_test_evidence
tss_backtest_ready
tss_holdout_validation
```

`data_ready`、`signal_ready` 等无前缀 post-mandate stage 不再作为 `time_series_signal` canonical stage。

### Runtime Tools

新增：

```text
runtime/tools/tss_data_ready_runtime.py
runtime/tools/tss_signal_ready_runtime.py
runtime/tools/tss_train_runtime.py
runtime/tools/tss_test_evidence_runtime.py
runtime/tools/tss_backtest_runtime.py
runtime/tools/tss_holdout_runtime.py
```

新增 semantic validators：

```text
runtime/tools/tss_data_ready_contract_runtime.py
runtime/tools/tss_signal_ready_contract_runtime.py
runtime/tools/tss_train_freeze_contract_runtime.py
runtime/tools/tss_test_evidence_contract_runtime.py
runtime/tools/tss_backtest_ready_contract_runtime.py
runtime/tools/tss_holdout_validation_contract_runtime.py
```

`runtime/tools/artifact_contract_runtime.py` 必须注册 `tss_*` artifact contracts。

### Skills

新增：

```text
skills/tss_data_ready/qros-tss-data-ready-author
skills/tss_data_ready/qros-tss-data-ready-review
skills/tss_signal_ready/qros-tss-signal-ready-author
skills/tss_signal_ready/qros-tss-signal-ready-review
skills/tss_train_freeze/qros-tss-train-freeze-author
skills/tss_train_freeze/qros-tss-train-freeze-review
skills/tss_test_evidence/qros-tss-test-evidence-author
skills/tss_test_evidence/qros-tss-test-evidence-review
skills/tss_backtest_ready/qros-tss-backtest-ready-author
skills/tss_backtest_ready/qros-tss-backtest-ready-review
skills/tss_holdout_validation/qros-tss-holdout-validation-author
skills/tss_holdout_validation/qros-tss-holdout-validation-review
```

旧无前缀 time-series post-mandate skills 不再是 canonical route entry。

### Session Routing

`qros-research-session` 需要将 `research_route = time_series_signal` 路由到：

```text
tss_data_ready_confirmation_pending
tss_data_ready
tss_data_ready review
tss_signal_ready_confirmation_pending
tss_signal_ready
tss_signal_ready review
tss_train_freeze_confirmation_pending
tss_train_freeze
tss_train_freeze review
tss_test_evidence_confirmation_pending
tss_test_evidence
tss_test_evidence review
tss_backtest_ready_confirmation_pending
tss_backtest_ready
tss_backtest_ready review
tss_holdout_validation_confirmation_pending
tss_holdout_validation
tss_holdout_validation review
```

确认问题也必须带 TSS stage 名称，例如：

```text
是否按以上内容冻结 tss_data_ready？
是否按以上内容冻结 tss_signal_ready？
```

### Diagnostics

新增：

```text
contracts/diagnostics/tss_metric_library.yaml
contracts/diagnostics/tss_stage_diagnostic_profiles.yaml
skills/core/qros-signal-diagnostics/SKILL.md
runtime/bin/qros-signal-diagnostics
runtime/scripts/run_signal_diagnostics.py
runtime/tools/signal_diagnostics.py
```

`$qros-factor-diagnostics` 继续服务 CSF。`$qros-signal-diagnostics` 服务 TSS。

后续可以再新增 `$qros-diagnostics`，根据 `research_route` 自动分发。

## Review And Preflight

TSS review 需要与 CSF 对齐：

- author build 后必须运行 `qros-validate-stage --stage tss_<stage>`。
- review preflight 必须包含 artifact contract validation、semantic validation、upstream binding validation。
- reviewer 只审当前 stage-local 内容，不负责修补上游绑定。
- `review/closure/stage_completion_certificate.yaml` 仍是进入下一阶段的唯一 completion truth。

Key semantic validators:

- `tss_data_ready`: no-lookahead label alignment、time key uniqueness、split sample adequacy。
- `tss_signal_ready`: signal input 不得包含 forward labels，param_id 必须物化，route inheritance exact copy。
- `tss_train_freeze`: train threshold 只能来自 train window，kept/rejected variants 全量记账。
- `tss_test_evidence`: test 只能复用 frozen train rules，selected variants 来自完整 ledger。
- `tss_backtest_ready`: backtest 不得重选 variants，成本后结果和 engine compare 必须可解释。
- `tss_holdout_validation`: holdout 不得调参，方向、频率和成本后表现必须独立验证。

## Testing Strategy

Focused tests should cover:

1. `artifact_contract_runtime.py` can load every `tss_*` contract.
2. `qros-validate-stage --stage tss_data_ready` validates required artifacts.
3. `research_route = time_series_signal` routes to `tss_data_ready_confirmation_pending`.
4. `tss_signal_ready` rejects signal inputs that bind to `forward_label_base`.
5. `tss_train_freeze` rejects unknown kept variants.
6. `tss_test_evidence` rejects selected variants not present in train kept ledger.
7. `tss_backtest_ready` rejects missing `strategy_contract.yaml` or missing net-after-cost metrics.
8. `tss_holdout_validation` rejects holdout artifacts that imply threshold tuning.
9. Old unprefixed post-mandate stages are not advertised as canonical time-series route stages.
10. Docs and skills consistently use `tss_*` names.

Smoke should run after any session routing or stage-display changes.

Full-smoke is required if the implementation touches:

- `qros-research-session` stage flow
- review / display / next-stage orchestration
- route split
- canonical session stage naming
- anti-drift snapshots

## Migration Boundary

This is a route-level canonical rename, not a user-facing alias feature.

Implementation should avoid long-term dual naming. During the implementation window, legacy files may remain in the repository only as migration scaffolding or tests, but user-facing docs, active skills, runtime routing and new contracts must converge on `tss_*`.

After migration, new time-series lineages should not create:

```text
02_data_ready
03_signal_ready
04_train_freeze
05_test_evidence
06_backtest
07_holdout
```

They should create only:

```text
02_tss_data_ready
03_tss_signal_ready
04_tss_train_freeze
05_tss_test_evidence
06_tss_backtest_ready
07_tss_holdout_validation
```

