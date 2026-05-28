# Replication PoC Quick Lane 设计

## 背景

QROS 当前主流程适合严肃研究治理：从 idea intake / mandate 开始，经过 data、signal、train、test、backtest、holdout 和 review gate，逐步冻结正式 lineage。

论文或研报复现的工作形态不同。用户常常先想知道一篇材料里的策略是否能被 Agent 读懂、转成明确实验、用本地数据快速跑出证据，再决定是否值得进入正式 QROS lineage。如果直接塞进正式主流程，会过早引入 mandate 冻结、stage review 和 holdout gate，降低探索速度；如果只让 Agent 临时代码实现，又会失去 provenance、assumption audit 和可复查结果。

因此新增一条独立 quick lane：读取 PDF / markdown / 网页研报，生成 Replication Spec，向用户确认数据源后，在 research repo 中直接生成并运行最小可运行 PoC 回测，输出快速证据和是否升格为正式 lineage 的建议。

## 目标

- 支持 PDF、markdown、网页链接作为研报 / 论文输入。
- Agent 读取全文并抽取可复现策略定义。
- 采用研究员模式：允许补齐缺失字段，但每个补齐项必须写入 assumption audit。
- 每次复现都先生成 data requirement report，并向用户确认数据源后才能运行 PoC。
- 独立写入 `replications/<paper_id>/`，不写正式 `outputs/<lineage>/`。
- 支持 TSS / CSF route classification，并生成对应最小 PoC 模板。
- 直接生成并运行最小可运行 test/backtest，输出接近正式 backtest evidence 的快速证据。
- 输出双结论：
  - replication verdict：是否忠实复现论文 / 研报定义。
  - promotion verdict：是否值得升格为正式 QROS lineage。

## 非目标

- 不把 quick lane 接入正式 QROS stage gate / review。
- 不自动下载或替换数据源。
- 不在第一版覆盖所有论文格式、公式图像 OCR 或复杂表格识别。
- 不自动创建正式 lineage 或写入 `stage_completion_certificate.yaml`。
- 不把 PoC 结果包装成正式 QROS review closure。

## 总体架构

新增 skill + CLI 双入口：

```text
$qros-replication-poc
        |
        v
qros-replicate
        |
        v
replications/<paper_id>/
```

skill 负责用户交互、解释和确认：

- 接收 PDF / URL / markdown 路径。
- 展示解析与策略抽取结果。
- 向用户确认数据源。
- 解释 PoC 证据、assumption 风险和双 verdict。

CLI 负责确定性落盘、执行和校验：

- 文档摄取。
- spec 抽取。
- data requirement report 生成。
- 数据绑定确认写入。
- PoC 程序生成和运行。
- verdict 生成。

quick lane 不写正式 lineage，不触发 review，不推进 `qros-research-session` 主流程。

## 目录结构

第一版保持扁平结构，避免做成完整 mini stage system：

```text
replications/<paper_id>/
  source/
    source_manifest.yaml
    extracted_text.md
    extraction_notes.md

  spec/
    replication_spec.yaml
    strategy_definition.md
    assumption_audit.yaml
    data_requirement_report.yaml
    data_binding.yaml
    route_classification.yaml

  program/
    run_replication.py
    helpers/
      data_loader.py
      signal_builder.py
      backtest.py
      metrics.py

  results/
    train_test_holdout_split.yaml
    signal_panel.parquet
    test_evidence.parquet
    backtest_summary.parquet
    portfolio_return_series.parquet
    equity_curve.parquet
    drawdown_report.json
    turnover_capacity_report.parquet
    sensitivity_report.parquet
    replication_verdict.yaml
    promotion_verdict.yaml

  README.md
  artifact_catalog.md
```

`source_manifest.yaml` records source URI / file path, source type, file hash when local, ingest timestamp, parser, and extraction warnings.

`replication_spec.yaml` is the machine-readable core contract. It must be complete enough to generate a runnable PoC, with assumptions explicitly separated from source-backed fields.

`data_requirement_report.yaml` must be produced before PoC execution. `run-poc` must fail closed unless `spec/data_binding.yaml` exists.

`program/` must contain runnable code for the current replication. A pure skeleton with only placeholders is invalid.

`results/` stores quick evidence and verdict artifacts. These are not formal QROS stage artifacts.

## CLI 流程

Proposed CLI:

```bash
qros-replicate ingest --source <pdf-or-url> --paper-id <id>
qros-replicate extract-spec --paper-id <id>
qros-replicate data-report --paper-id <id>
qros-replicate confirm-data --paper-id <id> --data-source <path-or-name>
qros-replicate run-poc --paper-id <id>
qros-replicate verdict --paper-id <id>
```

Flow:

1. User provides a paper, report, URL, or markdown path through `$qros-replication-poc`.
2. `ingest` writes `source/source_manifest.yaml`, `source/extracted_text.md`, and `source/extraction_notes.md`.
3. `extract-spec` writes `spec/replication_spec.yaml`, `spec/strategy_definition.md`, `spec/assumption_audit.yaml`, and `spec/route_classification.yaml`.
4. `data-report` writes `spec/data_requirement_report.yaml`.
5. The skill stops and asks the user to confirm the data source.
6. `confirm-data` writes `spec/data_binding.yaml`.
7. `run-poc` generates or refreshes `program/*`, runs the PoC, and writes `results/*`.
8. `verdict` writes `results/replication_verdict.yaml` and `results/promotion_verdict.yaml`.
9. The skill explains the results in Chinese and recommends whether to promote the idea into a formal QROS lineage.

`run-poc` must not auto-download data, silently switch data sources, or infer a local data path without explicit confirmation.

## Replication Spec

`spec/replication_spec.yaml` should use this first-version shape:

```yaml
paper:
  paper_id:
  title:
  authors:
  source_type: pdf | url | markdown
  source_uri:
  publication_date:

extraction:
  extraction_timestamp:
  parser:
  source_confidence: high | medium | low
  missing_sections: []
  ambiguous_sections: []

strategy:
  strategy_name:
  route: time_series_signal | cross_sectional_factor
  hypothesis:
  mechanism:
  signal_definition:
    raw_formula:
    normalized_formula:
    lookback_window:
    holding_horizon:
    rebalance_frequency:
    lag_policy:
  portfolio_construction:
    expression:
    long_leg:
    short_leg:
    weighting:
    leverage:
    constraints:
  cost_model:
    fee_bps:
    slippage_bps:
    turnover_cost_bps:
  evaluation:
    primary_metric:
    secondary_metrics:
    benchmark:
    train_window:
    test_window:
    holdout_window:

data_requirements:
  market:
  instrument_type:
  universe:
  frequency:
  required_fields:
  sample_window:
  survivorship_policy:
  tradability_filter:
  local_data_binding_required: true

assumptions:
  - field:
    assumed_value:
    reason:
    source_gap:
    impact: low | medium | high

implementation:
  poc_template: csf | tss
  expected_outputs:
  failure_conditions:
```

Rules:

- Source-backed fields go into their natural locations.
- Missing but necessary implementation fields go into `assumptions`.
- `local_data_binding_required: true` is mandatory in the first version.
- `route` controls whether CSF or TSS templates are generated.
- `failure_conditions` define when PoC execution must stop.

## Data Confirmation

Every replication must produce `data_requirement_report.yaml` and wait for user confirmation before execution.

The report should include:

- market / universe
- bar size / sampling frequency
- required fields such as OHLCV, volume, funding, open interest, benchmark, or classification data
- sample window
- survivorship and tradability policy
- fee / slippage requirements
- expected local path or named data connection
- known limitations

Confirmed data is written to `spec/data_binding.yaml`:

```yaml
confirmed_by:
confirmed_at:
data_source_path:
data_connection_name:
allowed_fields: []
sample_window:
known_limitations: []
```

`run-poc` only reads confirmed data bindings. Missing or invalid binding is a hard failure.

## PoC Templates

### CSF Template

Input shape:

- `date/time × asset` panel.

Expected work:

- Build factor / signal panel.
- Evaluate Rank IC, bucket returns, top-bottom spread, breadth, and monotonicity where applicable.
- Build portfolio according to spec: long-only, short-only, or long-short.
- Compute cost-after-return, equity curve, drawdown, turnover, capacity proxy, and name/date concentration.

### TSS Template

Input shape:

- `asset × time` series.

Expected work:

- Build signal time series.
- Evaluate forward return by signal bucket, hit rate, conditional return, and event/path response where applicable.
- Build position series.
- Compute cost-after-return, equity curve, drawdown, turnover, Sharpe, Calmar, profit factor, and subperiod stability.

## Result Artifacts

Required quick lane result artifacts:

- `results/train_test_holdout_split.yaml`
- `results/signal_panel.parquet`
- `results/test_evidence.parquet`
- `results/backtest_summary.parquet`
- `results/portfolio_return_series.parquet`
- `results/equity_curve.parquet`
- `results/drawdown_report.json`
- `results/turnover_capacity_report.parquet`
- `results/sensitivity_report.parquet`
- `results/replication_verdict.yaml`
- `results/promotion_verdict.yaml`

These are quick lane artifacts. They may reuse QROS metric helpers where appropriate, but they do not satisfy formal QROS stage contracts by themselves.

## Error Handling

`qros-replicate` must fail closed and write `results/replication_failure.yaml` for:

- source text cannot be extracted
- route cannot be classified as TSS or CSF
- signal formula cannot be converted into executable logic
- confirmed data source is missing
- confirmed data does not satisfy `data_requirement_report.yaml`
- sample length is insufficient for train/test/holdout
- required result artifacts are missing after execution
- high-impact assumptions exceed the configured threshold

Failure output must include:

- failed step
- missing or invalid fields
- user action needed
- whether rerun is possible after fixing input or data

## Verdicts

### Replication Verdict

`results/replication_verdict.yaml` answers whether the paper/report was faithfully reproduced.

Suggested fields:

```yaml
replication_decision: FAITHFUL_REPLICATION | PARTIAL_REPLICATION | INCONCLUSIVE | FAILED_REPLICATION
source_fidelity:
  source_backed_fields: []
  assumption_fields: []
  high_impact_assumptions: []
result_match:
  matches_reported_direction:
  matches_reported_magnitude:
  mismatch_reasons: []
```

Mismatch reasons should distinguish data mismatch, formula ambiguity, sample-window mismatch, market/regime difference, implementation assumption impact, and unsupported paper details.

### Promotion Verdict

`results/promotion_verdict.yaml` answers whether the idea should enter formal QROS lineage.

Suggested fields:

```yaml
promotion_decision: PROMOTE_TO_LINEAGE | NEEDS_MORE_WORK | DO_NOT_PROMOTE
recommended_route: time_series_signal | cross_sectional_factor
recommended_next_step:
  - create_mandate_draft
blocking_risks: []
required_formal_lineage_checks: []
```

Promotion is independent from replication fidelity. A paper can be only partially reproduced but still worth formal QROS research if the quick evidence and mechanism are strong enough.

## Skill Behavior

`$qros-replication-poc` should:

- explain that quick lane is independent from formal QROS lineage
- accept source path or URL
- run ingest and extract-spec through deterministic CLI
- summarize extracted strategy definition and assumptions
- stop for data source confirmation every time
- run PoC only after confirmation
- summarize evidence and verdicts
- recommend whether to create a formal mandate draft, request more data, refine formula, or stop

It must not:

- auto-download data
- silently choose a data source
- claim formal QROS review completion
- write `outputs/<lineage>/`
- generate stage completion certificates

## Testing Strategy

Focused tests should cover:

- contract validation for quick lane artifact presence and field shape
- source manifest generation for local markdown/PDF stubs and URL metadata stubs
- spec extraction from deterministic fixture text
- assumption audit captures missing required fields
- data-report blocks `run-poc` until `data_binding.yaml` exists
- CSF template writes required quick result artifacts from a tiny fixture panel
- TSS template writes required quick result artifacts from a tiny fixture series
- verdict generation separates replication and promotion decisions
- skill docs state that the lane is independent and requires data confirmation

Because this changes user workflow and adds a CLI, implementation should eventually run focused tests plus smoke. Full-smoke is required if implementation touches `qros-research-session` stage flow, canonical stage naming, review orchestration, or existing stage gates. The intended first implementation should avoid those areas.

## Open Design Decisions Fixed For First Version

- Input support starts with PDF / markdown / URL, but first implementation may use deterministic parser stubs for tests.
- Assumptions are allowed, but must be explicit and impact-rated.
- Data source must be confirmed by the user every time.
- The lane is independent under `replications/<paper_id>/`.
- TSS and CSF are both supported through route classification and minimal templates.
- The quick lane produces rich evidence, including train/test/holdout, cost-after-return, equity curve, drawdown, turnover/capacity proxy, stability, sensitivity, and dual verdicts.
