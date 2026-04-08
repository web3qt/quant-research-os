---
name: qros-stage-display
description: Use when a frozen stage needs a runtime-owned stage-display summary that renders structured summary JSON and HTML directly.
---

# QROS Stage Display

## Purpose

把已冻结阶段的关键交付物整理成正式的 display surface，而不是一次性脚本、临时导出物或手工 bundle。

这个 skill 采用 **generic by shape, registry-thin by implementation** 的方式：

- 只有一个统一 skill 入口
- 具体阶段语义仍由 repo-owned stage builder 决定
- runtime 自己直接写 summary JSON 与 HTML，不依赖外部 handoff
- `mandate` 与 `csf_data_ready` 仍保留更强的 stage-specific summary 语义

## v1 Supported Stage List

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

v1 formally supports the current reviewable mainline and CSF stages.

未注册阶段必须显式失败：

- `Unsupported stage for qros-stage-display: <stage_id>`
- 不得写出 partial HTML
- 不得假装 fallback 到其他 stage

## Required Inputs For `mandate`

- `01_mandate/mandate.md`
- `01_mandate/research_scope.md`
- `01_mandate/research_route.yaml`
- `01_mandate/time_split.json`
- `01_mandate/parameter_grid.yaml`
- `01_mandate/run_config.toml`
- `01_mandate/artifact_catalog.md`
- `01_mandate/field_dictionary.md`
- `01_mandate/program_execution_manifest.json`
- `01_mandate/stage_completion_certificate.yaml`

## Required Inputs For `csf_data_ready`

当 stage 为 `csf_data_ready` 时，至少需要以下冻结产物：

- `02_csf_data_ready/panel_manifest.json`
- `02_csf_data_ready/asset_universe_membership.parquet`
- `02_csf_data_ready/eligibility_base_mask.parquet`
- `02_csf_data_ready/cross_section_coverage.parquet`
- `02_csf_data_ready/shared_feature_base/`
- `02_csf_data_ready/csf_data_contract.md`
- `02_csf_data_ready/run_manifest.json`
- `02_csf_data_ready/artifact_catalog.md`
- `02_csf_data_ready/field_dictionary.md`
- `02_csf_data_ready/rebuild_csf_data_ready.py`

## Required Outputs

runtime 直接写出：

- `reports/stage_display/<stage>.summary.json`
- `reports/stage_display/<stage>.summary.html`

其中：

- `*.summary.json` 是 deterministic source of truth
- `*.summary.html` 是 runtime 直接从 summary 渲染出的用户可见页面
- render 失败时，`summary.json` 必须保留 `render_status` / `render_error`，且不得保留伪成功 HTML

## Fact Boundary

Display 内容必须严格受 frozen stage artifacts 和 contracts 约束。

Forbidden behaviors:

- infer factor performance
- infer alpha quality
- invent coverage explanations not present in the frozen artifacts
- blur `available` / `missing` / `question` markers for presentation polish

## Invocation

可从 repo root 或 installed runtime 调用，直接生成 deterministic summary + HTML：

```bash
python scripts/run_stage_display.py \
  --stage-id csf_data_ready \
  --lineage-root <path-to-lineage-root> \
  --json
```

也可以使用另一种 path resolution：

```bash
python scripts/run_stage_display.py \
  --stage-id csf_data_ready \
  --outputs-root <outputs-root> \
  --lineage-id <lineage-id> \
  --json
```

## Notes

- This skill is generic by entrypoint，不是 free-form worker discovery。
- runtime 负责 facts、summary 和 HTML render。
- 其他 reviewable stage 可以走 generic deterministic summary builder；`mandate` 与 `csf_data_ready` 允许保留更强的 stage-owned section 语义。
- 后续若要新增 stage，必须注册新的 builder，并补对应的 stage-specific tests。
