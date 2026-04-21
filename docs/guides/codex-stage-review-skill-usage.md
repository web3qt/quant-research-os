# Codex Stage Review Skill Usage

## Scope

当前 first-wave 已覆盖 mainline 与 CSF 的整套 `qros-*-review` skills。  
固定 stage -> skill 映射、三层约束来源，以及“哪些已经是 runtime 强约束”请优先看：

- [QROS Review Constraint Map](qros-review-constraint-map.md)

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
- `review/result/reviewer_findings.raw.yaml` 或 `review/result/adversarial_review_result.yaml`
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

对 `csf_signal_ready`，当前阶段关于 mandate route 继承的唯一正式证据应当是：

- `author/formal/route_inheritance_contract.yaml`

review checklist 和 deterministic engine 应只认这个 artifact，而不是再要求 reviewer 在当前阶段目录里临时拼 `mandate.md` / `research_route.yaml` 的替代解释。

新的治理方向下，review 仍要求人显式发起，但显式动作现在是进入对应的 `qros-*-review` skill，而不是手动再开一个 Codex review session。该 stage-specific review skill 会在**当前会话**里用 `spawn_agent` 拉起 reviewer 子代理，再调用 `./.qros/bin/qros-start-spawned-review` 注册 active cycle。当前 runtime 仍沿用 `spawned_reviewer_receipt.yaml` 这个历史文件名来保存 receipt。

## Running The Review Engine

在当前 `outputs/<lineage>/<stage>/` 目录下，正常用户路径应当是：

1. 在当前会话里直接进入对应 `qros-*-review`
2. 该 skill 内部用 `spawn_agent` 拉起 reviewer 子代理
3. 该 skill 内部运行 `./.qros/bin/qros-start-spawned-review` 注册 active cycle
4. reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
5. 当前会话随后运行 `./.qros/bin/qros-review` 完成 deterministic closer

如果你要手工调试或做恢复，也可以显式分解成下面两步：

```bash
./.qros/bin/qros-start-spawned-review --reviewer-id <id> --reviewer-session-id <session> --spawned-agent-id <child_agent_id>
./.qros/bin/qros-review
```

如果不在 stage 目录中，也可以显式传参：

```bash
./.qros/bin/qros-start-spawned-review --stage-dir outputs/topic_a/mandate --lineage-root outputs/topic_a --reviewer-id <id> --reviewer-session-id <session> --spawned-agent-id <child_agent_id>
./.qros/bin/qros-review --stage-dir outputs/topic_a/mandate --lineage-root outputs/topic_a
```

当前 `qros-review` 会在内部完成：

- raw findings -> canonical result
- reviewer write-scope audit
- closure artifacts 写盘

单独的 `qros-audit-reviewer` 仍然保留给调试、排查和手工恢复，不再是正常主路径的必经命令。

发起 review 之前，author lane 最好先完成一次 `review-ready` 自查：

- 当前 request scope 指向的是**最新** author outputs，而不是修复前的 stale 路径
- 必需 outputs、`artifact_catalog.md`、`field_dictionary.md`、`run_manifest.json` 与 program provenance 已到位
- handoff 已明确说明这轮声称已完成什么、希望 reviewer 重点验证什么、还存在哪些已知限制

当前 runtime 还会把这层自查冻结到 request / handoff：

- `launcher_review_ready_status`
- `launcher_checked_artifact_paths`
- `launcher_checked_provenance_paths`
- `launcher_handoff_context_paths`

另外，review runtime 还会把关键节点追加到：

- `review/review_cycle_trace.jsonl`

如果 reviewer 返回 `FIX_REQUIRED`，应显式回 author lane 读取 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，修复并刷新 outputs 后，再显式重新进入对应 `qros-*-review`；不要直接复用旧 receipt / result / audit。

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
