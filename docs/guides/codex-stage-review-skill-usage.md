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

当前 review 执行闭环要求在当前 `stage_dir` 下至少提供：

- `review/request/spawned_reviewer_receipt.yaml`
- `review/request/reviewer_write_scope_baseline.yaml`
- `review/result/adversarial_review_result.yaml`
- `review/result/reviewer_write_scope_audit.yaml`
- `review/result/review_findings.yaml`

其中 `adversarial_review_result.yaml` 现在还必须显式声明：

- `reviewer_agent_id`
- `reviewer_execution_mode: spawned_agent`
- `reviewer_context_source: explicit_handoff_only`
- `reviewer_history_inheritance: none`
- `handoff_manifest_digest`

`review_findings.yaml` 仍建议至少包含：

- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`
- `recommended_verdict`
- `rollback_stage`
- `allowed_modifications`

自动可判定的硬项由 engine 处理，语义类判断由 reviewer 通过这个文件补充。

制度上，`spawned_agent` 指独立 reviewer 子代理，而不是启动 review 的当前主线程继续自写 `review/result/*`。在当前 `Codex-only` 版本里，这个 reviewer child 应通过 native `spawn_agent` 启动；`./.qros/bin/qros-spawn-reviewer` 只负责写 launcher-side receipt，不等于 reviewer 已经完成审查。

## Running The Review Engine

在当前 `outputs/<lineage>/<stage>/` 目录下，主线程应先通过 native `spawn_agent` 启动独立 reviewer 子代理；wrapper 层先由 runtime launcher 写 receipt 和 baseline，reviewer 子代理写完 `review/result/*` 后，主线程先做 deterministic write-scope audit，再执行 deterministic closure：

```bash
./.qros/bin/qros-spawn-reviewer --reviewer-id <id> --reviewer-session-id <session> --launcher-thread-id <leader-thread-id> --spawned-agent-id <child-agent-id>
./.qros/bin/qros-audit-reviewer
./.qros/bin/qros-review
```

如果不在 stage 目录中，也可以显式传参：

```bash
./.qros/bin/qros-spawn-reviewer --stage-dir outputs/topic_a/mandate --lineage-root outputs/topic_a --reviewer-id <id> --reviewer-session-id <session> --launcher-thread-id <leader-thread-id> --spawned-agent-id <child-agent-id>
./.qros/bin/qros-audit-reviewer --stage-dir outputs/topic_a/mandate --lineage-root outputs/topic_a
./.qros/bin/qros-review --stage-dir outputs/topic_a/mandate --lineage-root outputs/topic_a
```

发起 review 之前，主线程最好先完成一次 `review-ready` 自查：

- 当前 request scope 指向的是**最新** author outputs，而不是修复前的 stale 路径
- 必需 outputs、`artifact_catalog.md`、`field_dictionary.md`、`run_manifest.json` 与 program provenance 已到位
- handoff 已明确说明这轮声称已完成什么、希望 reviewer 重点验证什么、还存在哪些已知限制

当前 runtime 还会把这层自查冻结到 request / handoff：

- `launcher_review_ready_status`
- `launcher_checked_artifact_paths`
- `launcher_checked_provenance_paths`
- `launcher_handoff_context_paths`

如果 reviewer 返回 `FIX_REQUIRED`，主线程应先读 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，回 author lane 修复并刷新 outputs，再起一个新的 reviewer cycle；不要直接复用旧 receipt / result / audit。

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
