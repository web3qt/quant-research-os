# Codex Stage Review Skill Usage

## Scope

当前第一版只覆盖 3 个 stage review skills：

- `qros-mandate-review`
- `qros-data-ready-review`
- `qros-signal-ready-review`

它们都是由生成器写入 `.agents/skills/` 的 Codex skills。

## What These Skills Do

这 3 个 skills 的目标一致：

- 读取 stage contract
- 读取 stage checklist
- 检查当前 stage 的 evidence artifacts
- 按统一 verdict vocabulary 输出 review 结论
- 指导生成统一 closure artifacts

## Rule Inputs

这些 skills 的规则来源固定为：

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`

如果 formal gate、checklist 或 verdict 规则变化，应更新这两份文件后重新生成 skills。

## Evidence Inputs

运行 review 时，skills 预期当前 stage 至少具备下列证据输入中的相关部分：

- `artifact_catalog.md`
- `field_dictionary.md` 或 `*_fields.md`
- `run_manifest.json`
- stage-specific machine artifacts

例如：

- `Mandate` 重点看 `time_split.json`、`parameter_grid.yaml`、`run_config.toml`
- `Data Ready` 重点看 `dataset_manifest.json`、`qc_report.parquet`、`aligned_bars/`
- `Signal Ready` 重点看 `param_manifest.csv`、`timeseries/`、`signal_fields_contract.md`

## Reviewer Findings

第一版 review 执行闭环要求在当前 `stage_dir` 下提供：

- `review_findings.yaml`

建议至少包含：

- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`
- `recommended_verdict`
- `rollback_stage`
- `allowed_modifications`

自动可判定的硬项由 engine 处理，语义类判断由 reviewer 通过这个文件补充。

## Running The Review Engine

在当前 `outputs/<lineage>/<stage>/` 目录下执行：

```bash
python scripts/run_stage_review.py
```

如果不在 stage 目录中，也可以显式传参：

```bash
python scripts/run_stage_review.py --stage-dir outputs/topic_a/mandate --lineage-root outputs/topic_a
```

## Closure Artifacts

review 结束后，skills 统一面向以下 closure artifacts：

- `latest_review_pack.yaml`
- `stage_gate_review.yaml`
- `stage_completion_certificate.yaml`

## Regenerating Skills

重新生成首批 Codex skills：

```bash
python scripts/gen_codex_stage_review_skills.py
```

这个命令会重写：

- `.agents/skills/qros-mandate-review/`
- `.agents/skills/qros-data-ready-review/`
- `.agents/skills/qros-signal-ready-review/`

## Freshness Validation

验证已生成 skills 是否与当前模板和 YAML 保持一致：

```bash
python scripts/gen_codex_stage_review_skills.py --dry-run
```

预期输出：

```text
FRESH: qros-mandate-review
FRESH: qros-data-ready-review
FRESH: qros-signal-ready-review
```

如果输出 `STALE:`，表示：

- 模板改了但未重新生成
- YAML contract/checklist 改了但未重新生成
- 已生成 skill 被手工改动过

## Test Commands

运行当前实现的测试：

```bash
python -m pytest tests -v
```

最常用的两个验证命令：

```bash
python scripts/gen_codex_stage_review_skills.py
python scripts/gen_codex_stage_review_skills.py --dry-run
```
