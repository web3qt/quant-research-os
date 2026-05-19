# 阶段 Review Skill 使用说明

## 作用域

当前已覆盖 mainline（mandate / data_ready / signal_ready / train_freeze / test_evidence / backtest_ready / holdout_validation）、CSF 和 TSS 的全套 `qros-*-review` skills。
固定 stage -> skill 映射、三层约束来源，以及”哪些已经是 runtime 强约束”请优先看：

- [QROS Review Constraint Map](qros-review-constraint-map.md)

它们通过宿主特定的 skills 目录暴露给对应 host（Codex: `~/.codex/skills/qros-*`；Claude Code: `.claude-plugin/skills/qros-*`）；而真正执行 review engine 时，当前 research repo 还需要先有自己的 `./.qros/` 本地 runtime。安装和刷新优先使用 `Fetch and follow instructions .../.codex/INSTALL.md` 或 `qros-update`。

## 这些 Skill 做什么

所有 `qros-*-review` skills 的目标一致：

- 读取 stage contract
- 读取 stage checklist
- 检查当前 stage 的 evidence artifacts
- 按统一 verdict vocabulary 输出 review 结论
- 指导生成统一 closure artifacts

## 规则输入

这些 skills 的规则来源固定为：

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`

如果 formal gate、checklist 或 verdict 规则变化，应更新这两份 contract 真值后重新生成 skills。

## 证据输入

运行 review 时，skills 预期当前 stage 至少具备下列证据输入中的相关部分：

- `author/formal/artifact_catalog.md`
- `author/formal/field_dictionary.md` 或 `author/formal/*_fields.md`
- `author/formal/run_manifest.json`
- stage-specific machine artifacts

例如：

- `Mandate` 重点看 `time_split.json`、`parameter_grid.yaml`、`run_config.toml`
- `Data Ready` 重点看 `dataset_manifest.json`、`qc_report.parquet`、`aligned_bars/`
- `Signal Ready` 重点看 `param_manifest.csv`、`timeseries/`、`signal_fields_contract.md`

## Reviewer Findings / 审查发现

当前 review 执行闭环要求在当前 `stage_dir` 下至少提供：

- `review/request/reviewer_receipt.yaml`
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

新的治理方向下，review 仍要求人显式确认，但普通路径中的显式动作是 `qros-research-session` 记录 `CONFIRM_REVIEW`，而不是要求用户进入对应的 `qros-*-review` skill。确认后，`qros-research-session` 会在**当前会话**里复用 stage-specific review 协议：用 `spawn_agent` 拉起 reviewer 子代理，再调用 `./.qros/bin/qros-review-cycle prepare` 注册 active cycle、生成 handoff prompt 和 closer command。stage-specific review skill 仍保留为高级/debug/manual recovery 入口。当前 runtime 使用 `reviewer_receipt.yaml` 保存 receipt。

## 运行 Review Engine

在当前 `outputs/<lineage>/<stage>/` 目录下，正常用户路径应当是：

1. 继续 `qros-research-session`，由它识别当前 stage 是否处于 `*_review_confirmation_pending`
2. 用户显式确认 `CONFIRM_REVIEW`
3. `qros-research-session` 内部用 `spawn_agent` 拉起 reviewer 子代理
4. `qros-research-session` 内部优先运行 `./.qros/bin/qros-review-cycle prepare` 注册 active cycle，并复用它输出的 reviewer handoff prompt / closer command
5. reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
6. 当前会话随后运行 `./.qros/bin/qros-review` 完成 deterministic closer

如果你要手工调试或做恢复，也可以显式分解成下面两步：

```bash
./.qros/bin/qros-review-cycle prepare --reviewer-id <id> --reviewer-session-id <session> --reviewer-agent-id <child_agent_id>
./.qros/bin/qros-review
```

如果不在 stage 目录中，也可以显式传参：

```bash
./.qros/bin/qros-review-cycle prepare --stage-dir outputs/topic_a/mandate --lineage-root outputs/topic_a --reviewer-id <id> --reviewer-session-id <session> --reviewer-agent-id <child_agent_id>
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

如果 reviewer 返回 `FIX_REQUIRED`，应显式回 author lane 读取 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，修复并刷新 outputs 后，再通过 `qros-research-session` 重新进入 review confirmation / review lane；不要直接复用旧 receipt / result / audit。

## Thin Generated Review Skills

generated review skills are workflow entrypoints, not stage truth. 当前生成出来的 `qros-*-review` skill 主要负责：

- stage-entry guard
- shared review discipline
- reviewer isolation / write boundary
- 强制先跑 `qros-review-cycle prepare`

stage-specific gates、outputs、checklist、rollback 和 downstream permissions 不再应该长期内联在 skill 正文里。它们通过 `qros-review-cycle prepare` 生成到：

- `review/request/stage_contract_context.yaml`
- `review/request/stage_contract_context.md`

reviewer handoff 应显式引用这两份文件。它们是 review-cycle-local rendering of current contracts and current author outputs。

## Closure Artifacts / 关闭产物

review 结束后，skills 统一面向以下 closure artifacts：

- `review/closure/latest_review_pack.yaml`
- `review/closure/stage_gate_review.yaml`
- `review/closure/stage_completion_certificate.yaml`

## 重新生成 Skills

重新生成全部 host-specific review skills：

```bash
# 生成 Codex skills（写入 skills/ 目录）
python runtime/scripts/gen_stage_review_skills.py --host codex

# 生成 Claude Code skills（写入 .claude-plugin/skills/ 目录）
python runtime/scripts/gen_stage_review_skills.py --host claude-code
```

这个命令会重写 repo source bundles：

- `skills/mandate/qros-mandate-review/`
- `skills/data_ready/qros-data-ready-review/`
- `skills/signal_ready/qros-signal-ready-review/`
- `skills/train_freeze/qros-train-freeze-review/`
- `skills/test_evidence/qros-test-evidence-review/`
- `skills/backtest_ready/qros-backtest-ready-review/`
- `skills/holdout_validation/qros-holdout-validation-review/`
- `skills/csf_data_ready/qros-csf-data-ready-review/`
- `skills/csf_signal_ready/qros-csf-signal-ready-review/`
- `skills/csf_train_freeze/qros-csf-train-freeze-review/`
- `skills/csf_test_evidence/qros-csf-test-evidence-review/`
- `skills/csf_backtest_ready/qros-csf-backtest-ready-review/`
- `skills/csf_holdout_validation/qros-csf-holdout-validation-review/`
- `skills/tss_data_ready/qros-tss-data-ready-review/`
- `skills/tss_signal_ready/qros-tss-signal-ready-review/`
- `skills/tss_train_freeze/qros-tss-train-freeze-review/`
- `skills/tss_test_evidence/qros-tss-test-evidence-review/`
- `skills/tss_backtest_ready/qros-tss-backtest-ready-review/`
- `skills/tss_holdout_validation/qros-tss-holdout-validation-review/`

如果你要把更新后的 source bundles 同步到 Codex 已安装环境和当前 research repo 的 `./.qros/`，在该 research repo 根运行 `qros-update`，然后 Restart Codex。对于 Claude Code，对应的 skills 会写入 `.claude-plugin/skills/`，plugin update 时自动刷新。

## 新鲜度验证

验证已生成 skills 是否与当前模板和 YAML 保持一致：

```bash
python runtime/scripts/gen_stage_review_skills.py --host codex --dry-run
```

预期输出：

```text
FRESH: qros-mandate-review
FRESH: qros-data-ready-review
FRESH: qros-signal-ready-review
FRESH: qros-train-freeze-review
FRESH: qros-test-evidence-review
FRESH: qros-backtest-ready-review
FRESH: qros-holdout-validation-review
FRESH: qros-csf-data-ready-review
FRESH: qros-csf-signal-ready-review
FRESH: qros-csf-train-freeze-review
FRESH: qros-csf-test-evidence-review
FRESH: qros-csf-backtest-ready-review
FRESH: qros-csf-holdout-validation-review
FRESH: qros-tss-data-ready-review
FRESH: qros-tss-signal-ready-review
FRESH: qros-tss-train-freeze-review
FRESH: qros-tss-test-evidence-review
FRESH: qros-tss-backtest-ready-review
FRESH: qros-tss-holdout-validation-review
```

如果输出 `STALE:`，表示：

- 模板改了但未重新生成
- YAML contract/checklist 改了但未重新生成
- 已生成 skill 被手工改动过

## 测试命令

运行当前实现的测试：

```bash
python -m pytest tests -v
```

最常用的验证命令：

```bash
# 生成 Codex skills
python runtime/scripts/gen_stage_review_skills.py --host codex

# 新鲜度检查
python runtime/scripts/gen_stage_review_skills.py --host codex --dry-run

# 生成 Claude Code skills
python runtime/scripts/gen_stage_review_skills.py --host claude-code

# Claude Code 新鲜度检查
python runtime/scripts/gen_stage_review_skills.py --host claude-code --dry-run
```
