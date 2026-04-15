# Codex Stage Review Skill Usage

## Scope

当前第一版只覆盖 3 个 stage review skills：

- `qros-mandate-review`
- `qros-data-ready-review`
- `qros-signal-ready-review`

它们都是通过 `./setup --host codex --mode user-global` 直接写入 `~/.codex/skills/` 暴露给 Codex 的 skills；而真正执行 review engine 时，当前 research repo 还需要先有自己的 `./.qros/` 本地 runtime。

## What These Skills Do

这 3 个 skills 的目标一致：

- 读取 stage contract
- 读取 stage checklist
- 检查当前 stage 的 evidence artifacts
- 按统一 verdict vocabulary 输出 review 结论
- 指导生成统一 closure artifacts

## Rule Inputs

这些 skills 的规则来源固定为：

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`

如果 formal gate、checklist 或 verdict 规则变化，应更新这两份 contract 真值后重新生成 skills。

## Evidence Inputs

运行 review 时，skills 预期当前 stage 至少具备下列证据输入中的相关部分：

- `author/formal/artifact_catalog.md`
- `author/formal/field_dictionary.md` 或 `author/formal/*_fields.md`
- `author/formal/run_manifest.json`
- stage-specific machine artifacts

例如：

- `Mandate` 重点看 `time_split.json`、`parameter_grid.yaml`、`run_config.toml`
- `Data Ready` 重点看 `dataset_manifest.json`、`qc_report.parquet`、`aligned_bars/`
- `Signal Ready` 重点看 `param_manifest.csv`、`timeseries/`、`signal_fields_contract.md`

## Reviewer Findings

第一版 review 执行闭环要求在当前 `stage_dir` 下提供：

- `review/result/review_findings.yaml`

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
./.qros/bin/qros-review
```

如果不在 stage 目录中，也可以显式传参：

```bash
./.qros/bin/qros-review --stage-dir outputs/topic_a/mandate --lineage-root outputs/topic_a
```

## Closure Artifacts

review 结束后，skills 统一面向以下 closure artifacts：

- `review/closure/latest_review_pack.yaml`
- `review/closure/stage_gate_review.yaml`
- `review/closure/stage_completion_certificate.yaml`

## Regenerating Skills

重新生成首批 Codex skills：

```bash
python runtime/scripts/gen_codex_stage_review_skills.py
```

这个命令会重写 repo source bundles：

- `skills/mandate/qros-mandate-review/`
- `skills/data_ready/qros-data-ready-review/`
- `skills/signal_ready/qros-signal-ready-review/`

如果你要把更新后的 source bundles 同步到 Codex 已安装环境，再运行：

```bash
./setup --host codex --mode user-global
```

如果要让当前 research repo 的本地 runtime 也同步到最新版本，再在该项目根执行：

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

## Freshness Validation

验证已生成 skills 是否与当前模板和 YAML 保持一致：

```bash
python runtime/scripts/gen_codex_stage_review_skills.py --dry-run
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
python runtime/scripts/gen_codex_stage_review_skills.py
python runtime/scripts/gen_codex_stage_review_skills.py --dry-run
```
