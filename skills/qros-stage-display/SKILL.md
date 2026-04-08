---
name: qros-stage-display
description: Use when a frozen stage needs a stage-display summary skill that produces a structured summary plus subagent-rendered HTML.
---

# QROS Stage Display

## Purpose

把已冻结阶段的关键交付物整理成正式的 display surface，而不是一次性脚本、临时导出物或手工 bundle。

这个 skill 采用 **generic by shape, registry-thin by implementation** 的方式：

- 只有一个统一 skill 入口
- 具体阶段语义仍由 repo-owned stage builder 决定
- v1 先正式支持所有 reviewable mainline / CSF stages；其中 `mandate` 与 `csf_data_ready` 仍保留更强的 stage-specific summary 语义

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

Any non-reviewable or unregistered stage is unsupported in v1.

任何未注册阶段都必须显式失败：

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
- `01_mandate/latest_review_pack.yaml`
- `01_mandate/stage_gate_review.yaml`
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

runtime 必须先写出 deterministic summary 与 handoff artifacts：

- `reports/stage_display/mandate.summary.json`
- `reports/stage_display/mandate.display_request.json`
- `reports/stage_display/mandate.display_prompt.txt`
- `reports/stage_display/csf_data_ready.summary.json`
- `reports/stage_display/csf_data_ready.display_request.json`
- `reports/stage_display/csf_data_ready.display_prompt.txt`

其他已支持 stage 也遵循同样命名：

- `reports/stage_display/<stage>.summary.json`
- `reports/stage_display/<stage>.display_request.json`
- `reports/stage_display/<stage>.display_prompt.txt`

当任意 Codex 会话完成原生 subagent render 之后，再回写：

- `reports/stage_display/<stage>.summary.html`
- `reports/stage_display/<stage>.display_result.json`

- `*.summary.json` 是 deterministic source of truth
- `*.display_request.json` / `*.display_prompt.txt` 是 native subagent handoff contract
- `*.display_result.json` 是 render completion contract
- `*.summary.html` 只有在 completion artifact 标记成功后才算有效成功产物

## Subagent Contract (Required)

Codex subagent 是这个 workflow 里的 **required core worker**，但它不再由 runtime 在后台 hidden subprocess 方式直接拥有。

也就是说：

- skill 必须先构建 deterministic structured summary
- runtime 必须产出 handoff artifact，让任意 Codex 会话都能原生、可见地 spawn subagent
- success 必须同时包含 structured summary、completion artifact 和 rendered HTML
- 如果 subagent rendering 失败，则 completion artifact 必须把失败状态回写到 lineage
- render 失败时，structured summary 可以保留，但不能伪装成成功 HTML

## Fact Boundary

Display 内容必须严格受 frozen stage artifacts 和 contracts 约束。

Forbidden behaviors:

- infer factor performance
- infer alpha quality
- invent coverage explanations not present in the frozen artifacts
- blur `available` / `missing` / `question` markers for presentation polish

## Invocation

可从 repo root 或 installed runtime 调用，生成 deterministic summary + handoff artifact：

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

- This skill is generic by entrypoint，不是 free-form subagent discovery。
- runtime 负责 facts + handoff；Codex 会话负责原生 visible subagent render。
- 其他 reviewable stage 可以走 generic deterministic summary builder；`mandate` 与 `csf_data_ready` 允许保留更强的 stage-owned section 语义。
- 后续若要新增 stage，必须注册新的 builder，并补对应的 stage-specific tests。
- 不得只靠修改 subagent prompt 就扩大支持范围。
