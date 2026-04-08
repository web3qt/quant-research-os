# QROS Stage Display Skill Usage

## Purpose

`qros-stage-display` 现在是一个**runtime-owned direct render** 合同：

- runtime 先生成 deterministic structured summary
- 然后 runtime 直接从这份 summary 渲染 HTML
- 不再需要 request / prompt / completion artifact，也不再需要另一个 Codex 会话继续完成 display

## Supported Stages

- `mandate`
- `data_ready`
- `signal_ready`
- `train_freeze`
- `test_evidence`
- `backtest_ready`
- `holdout_validation`
- `csf_data_ready`
- `csf_signal_ready`
- `csf_train_freeze`
- `csf_test_evidence`
- `csf_backtest_ready`
- `csf_holdout_validation`

The runtime remains registry-thin:

- one generic skill surface
- `mandate` and `csf_data_ready` keep stage-specific summary builders
- the remaining reviewable mainline / CSF stages use the shared generic review-closure builder
- unsupported stages fail fast

## Output Location

Runtime writes:

- `<lineage_root>/reports/stage_display/<stage>.summary.json`
- `<lineage_root>/reports/stage_display/<stage>.summary.html`

其中：

- `summary.json` 是 source of truth
- `summary.html` 是 runtime 直接从 summary 渲染出的页面
- render 失败时，`summary.json` 会保留 `render_status` / `render_error`
- render 失败时不应保留伪成功的 `summary.html`

`qros-research-session` 读取这些 runtime-owned artifacts，再决定 display 是 complete / retrying / exhausted。

## Command

直接生成 deterministic summary + HTML：

```bash
python scripts/run_stage_display.py \
  --stage-id mandate \
  --lineage-root <lineage-root> \
  --json
```

或：

```bash
python scripts/run_stage_display.py \
  --stage-id csf_data_ready \
  --outputs-root <outputs-root> \
  --lineage-id <lineage-id> \
  --json
```

## Structured Summary Contract

summary JSON 至少包含：

- `stage_id`
- `lineage_id`
- `lineage_root`
- `stage_directory`
- `section_order`
- `sections[]`
- item markers：`available`, `missing`, `question`
- `render_status`
- optional `render_error`

`mandate` 只反映冻结后的 mandate artifacts 与 review closure evidence，例如：

- research question / route / factor identity
- scope and data contract facts
- execution and review closure evidence

`csf_data_ready` 只反映冻结后的 artifact / contract facts，例如：

- panel manifest evidence
- universe / eligibility / coverage evidence
- run manifest / rebuild / delivery evidence

其他支持的 stage 使用 generic deterministic summary shape：

- stage metadata and core review evidence
- frozen artifact inventory
- review closure artifacts

No supported stage display path parses parquet internals or makes performance claims.

## Failure Semantics

- display 失败时，runtime 不再等待外部 worker
- session rerun 时会自动重试
- 最多 3 次
- 第 3 次失败后，display gate 阻塞并保留错误信息

## Testing / Controlled Expectations

`run_stage_display.py` 现在只保留 direct-render contract。旧的 worker handoff、completion 回写和兼容 render override surface 已全部删除。

## Notes

- This skill is generic by entrypoint，不是 worker handoff surface。
- runtime 负责 facts、summary 和 HTML render。
- 后续若要新增 stage，必须注册新的 builder，并补对应的 stage-specific tests。
