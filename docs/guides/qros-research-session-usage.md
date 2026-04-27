# QROS Research Session Usage

## What It Is

`qros-research-session` 是当前这段 QROS 工作流的统一单入口 orchestrator。

用户不需要记多个命令，只要从这一个 skill 开始，让 QROS 判断当前 lineage 处在哪个阶段。

如果你不熟悉阶段里的 grouped freeze 字段，可以把
`docs/guides/stage-freeze-group-field-guide.md`
当作 companion 说明文档一起看。它专门解释 `research_intent`、`scope_contract`、`window_contract`、`delivery_contract` 这类通用字段在回答什么问题。

## First-Wave Boundary

当前版本覆盖：

- `idea_intake`
- `idea_intake_confirmation_pending`
- `mandate`
- `mandate review`
- `data_ready`
- `data_ready review`
- `signal_ready`
- `signal_ready review`
- `train_freeze`
- `train_freeze review`
- `test_evidence`
- `test_evidence review`
- `backtest_ready`
- `backtest_ready review`
- `holdout_validation`
- `holdout_validation review`

当前版本**不会**继续进入：

- 更后面的研究阶段

## User Entry

在 Codex 里，可以这样开始：

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`
- `qros-progress`
- `qros-factor-diagnostics`

之后 agent 会接管并推进整个 session。

`qros-progress` 是只读进度查询入口，不是推进入口。它默认读取当前 repo 的 `outputs/` 并选择最近修改的 lineage，返回 `current_stage`、`current_skill`、`gate_status`、`blocking_reason`、`next_action` 和 `open_risks`。它不写 artifact、不 scaffold、不确认 transition，也不会替代 `qros-research-session`、stage author skill、review skill 或 failure handling skill。

`qros-factor-diagnostics` 是可选 diagnostics 入口，不是 review，不是 gate。它读取 CSF formal artifacts，汇总数据质量、因子质量、回测结果和 holdout 稳定性；它不写 review closure、不修改 gate decision，也不替代 `qros-review`。

Codex 会通过 `~/.codex/skills/qros-*` 找到这个 skill。安装和更新都应优先走 `Fetch and follow instructions .../.codex/INSTALL.md` 或 `qros-update`；当前 research repo 的本地 runtime 位于 `./.qros/`。

对于一个全新的 raw idea，正常行为不应该是直接替用户完成 `qualification_scorecard.yaml` 和 `idea_gate_decision.yaml`。第一轮应该先停在 `idea_intake_confirmation_pending`，先问清 observation、hypothesis、scope、data source、`bar_size` 和 kill criteria，并在得到显式确认后再进入正式 qualification。

QROS 仓库是工作流框架，不是研究产物仓。安装后，agent 应该在用户当前打开的 research repo 中推进 lineage，并把正式阶段产物写到那个 repo 的 `outputs/<lineage_id>/` 下；空目录、placeholder 文件和只有合同语义的说明文档不能被当作 `data_ready` 或其他阶段已经真实完成。

另外，lineage 选择现在有一个明确 guard：

- 如果当前入口是 `raw_idea` 且没有显式 `lineage_id`，session 会把这次运行视为 **fresh start**
- 它不能因为磁盘上有一条更旧、但推进得更远的 lineage，就自动切过去恢复
- 如果 `raw_idea` 解析出的 slug 已经存在，runtime 会阻止隐式 resume，并要求你显式给出 `lineage_id` 才继续那条线


## Hard Gate: Lineage-local Stage Programs

从 `mandate` 开始，session runtime 只做治理，不再把 framework-side shared build helper 当作阶段完成来源。每个可执行阶段都要满足：

`freeze approval -> lineage-local program -> artifact build -> review closure`

Canonical program tree：

- `outputs/<lineage_id>/program/mandate/`
- `outputs/<lineage_id>/program/time_series/data_ready/`
- `outputs/<lineage_id>/program/time_series/signal_ready/`
- `outputs/<lineage_id>/program/time_series/train_freeze/`
- `outputs/<lineage_id>/program/time_series/test_evidence/`
- `outputs/<lineage_id>/program/time_series/backtest_ready/`
- `outputs/<lineage_id>/program/time_series/holdout_validation/`
- `outputs/<lineage_id>/program/cross_sectional_factor/data_ready/`
- `outputs/<lineage_id>/program/cross_sectional_factor/signal_ready/`
- `outputs/<lineage_id>/program/cross_sectional_factor/train_freeze/`
- `outputs/<lineage_id>/program/cross_sectional_factor/test_evidence/`
- `outputs/<lineage_id>/program/cross_sectional_factor/backtest_ready/`
- `outputs/<lineage_id>/program/cross_sectional_factor/holdout_validation/`

真实研究流里，`mandate` 之后的 stage program 由 Codex 在当前 author lane 显式生成或刷新；QROS runtime 只负责校验和调用，不再后台静默生成默认 wrapper。每个 stage program 目录至少包含 `stage_program.yaml`、`README.md` 和 manifest 指向的 entrypoint。runtime 成功调用后，必须在对应阶段产物目录写出 `program_execution_manifest.json`，把 `program_hash`、entrypoint、authoring session 和 output refs 记账，其中 `program_hash` 记录的是整个 `program_dir` 的 hash，而不是单个 `run_stage.py` 文件。共享 helper 可以放在 `outputs/<lineage_id>/program/common/`，但 completion 永远不能 fallback 到 framework-side shared builder；fixture/demo-only helper 也必须与真实研究流主路径隔离。

如果 freeze 已批准但程序缺失，`qros-session --json` 会把 `stage_status` 设为 `awaiting_stage_program`，并返回 `blocking_reason_code = STAGE_PROGRAM_MISSING`，同时给出 `required_program_dir`、`required_program_entrypoint`、`next_action` 与 `resume_hint`。这时正确动作不是等 runtime 补默认程序，而是让 Codex 在当前 research repo 中显式生成或刷新本 stage 的 lineage-local stage program。程序存在但 contract 不合法时，会改为 `awaiting_program_validation` / `STAGE_PROGRAM_INVALID`；程序执行完成后，session 通常会先进入 `*_review_confirmation_pending`。对大 stage，stage program 可以声明 `prebuild_schema_gate`，让 runtime 先跑 dry-run schema report，检查 required columns、primary key、coverage fields 和 manifest fields，通过后才触发全量 build。当前 runtime 只在 `mandate_review_confirmation_pending` 强制跑 deterministic review-entry preflight；这就是当前的 mandate-first / mandate-only rollout truth。只要 `mandate` 的 `author/formal/*` required outputs 已齐，runtime 就会先跑 `qros-review-preflight`。如果 author outputs 过不了这道 reviewer-lane gate，session 会直接停在 `awaiting_author_fix` / `OUTPUTS_INVALID`，要求先修 author/formal，再进入 review。对 `mandate` 来说，preflight 不是 optional hygiene check，而是 reviewer lane 之前的强制门禁，必须先拦下 thin wrapper stage program、placeholder 文件和 contract-only fake machine artifacts。其余 post-mandate `*_review_confirmation_pending` 目前仍要求主 Agent 完成 `review-ready` 自查与 handoff 准备，但 runtime 还没有统一自动执行这道 deterministic preflight；不要把它写成已经全量 rollout。新的治理方向下，review 不再要求你手动再开一个 Codex review session；显式动作改成进入对应的 `qros-*-review`。该 stage-specific review skill 会在**当前会话**里用 `spawn_agent` 拉起 reviewer 子代理，再调用 `./.qros/bin/qros-review-cycle prepare` 注册 active review cycle、写出 request/receipt 并生成 reviewer handoff prompt；reviewer 子代理完成后运行输出的 `./.qros/bin/qros-review` closer 命令做 raw findings 规范化、write-scope audit 和 closure。

这里有一个容易被忽略的主线程职责：在真正起 reviewer 之前，主 Agent 应先做一次 `review-ready` 自查。最少要重新核对当前 stage 的 required outputs、`artifact_catalog.md`、`field_dictionary.md`、`run_manifest.json`、当前 stage program provenance，以及 machine-readable artifacts 不是 placeholder。review 不应该把 reviewer 当成第一轮“帮 author 数缺件”的入口。

现在这层自查还会被压成 request / handoff contract：

- `launcher_review_ready_status`
- `launcher_checked_artifact_paths`
- `launcher_checked_provenance_paths`
- `launcher_handoff_context_paths`

此外，active request 现在会显式区分三类 scope：

- `required_artifact_paths` / `required_provenance_paths`
  这是当前 stage 完整 deterministic gate scope
- `stage_content_artifact_paths` / `stage_content_provenance_paths`
  这是 reviewer 子代理应聚焦的 stage-local 内容审查范围
- `upstream_binding_artifact_paths` / `upstream_binding_provenance_paths`
  这是 deterministic validator 负责的上游绑定范围

因此，`data_ready` / `signal_ready` / `train_freeze` 的 review 不应重新复审上游 stage 全目录；它们只应检查当前 stage formal package，以及当前 stage 内声明的上游绑定是否成立。

所以，只要主 Agent 修过 `author/formal/*` 却没刷新 request / handoff，runtime 就会把这轮 review 当成 stale handoff 拒掉。

另外，review lane 现在还应在 stage 目录里留下一个轻量 trace：

- `review/review_cycle_trace.jsonl`

它会把 request、receipt、audit、review verdict 这些关键节点记下来。以后你拿 `review_cycle_id`、`reviewer_session_id`、`spawned_agent_id` 或 `launcher_thread_id` 做回溯，会比只看聊天记录顺得多。

如果 reviewer 返回 `FIX_REQUIRED`，主 Agent 也不应该直接原地再叫一个 reviewer 来“复看一眼”。正确顺序是：

1. 先阅读 `review/result/adversarial_review_result.yaml`
2. 再阅读 `review/result/review_findings.yaml`
3. 回 author lane 修复允许范围内的问题
4. 刷新 `author/formal/*` 与 review request scope
5. 显式重新进入对应 `qros-*-review`，起一个新的 reviewer cycle

如果 reviewer 只写了：

- `review/result/reviewer_findings.raw.yaml`

而没有正式写出 `adversarial_review_result.yaml`，当前 runtime 会在 `qros-review` 内按 active request / receipt / runtime reviewer identity 做 deterministic 规范化写入。这样 reviewer 不必手写 `review_cycle_id`、`handoff_manifest_digest`、`reviewed_*_paths` 等 proof 字段；旧 canonical result 也会被当前 raw findings 正常覆盖。

author outputs 一旦变化，旧的 receipt / result / audit 就只能当历史记录，不能继续拿来证明新的 author outputs。

阶段 review 失败不是普通调试（不是普通 debug）。当当前 stage review verdict 是 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE` 时，QROS 不应继续普通阶段推进，而应根据 runtime 的 `requires_failure_handling` 信号切换到 `qros-stage-failure-handler`。

failure package 也会接管 runtime 状态。若最新 `failure_packages/*/post_retry_decision.yaml` 写明 `normal_progression_allowed: false`，`qros-session` / `qros-progress` 会进入 `FAILURE_DISPOSITION_REQUIRED`，并要求在该 failure package 下写出正式 `failure_disposition.yaml`。该 disposition 只能把原 lineage 关闭为 `NO_GO`，或声明必须开 `CHILD_LINEAGE`；在 disposition 写出前，不允许重新进入 review 或 next-stage。即使 disposition 已写出，原 lineage 也不得继续普通 review / holdout 推进。

对 `csf_test_evidence`、`csf_backtest_ready`、`csf_holdout_validation`，当前 runtime 还额外执行 hard metric gates，而不是只看 artifact 是否齐全：

- `standalone_alpha` 的 `mean_rank_ic <= 0` 时，不得从 `csf_test_evidence` 放行
- `mean_net_return <= 0` 时，不得把 `csf_backtest_ready` 判成通过
- `direction_match = false` 或 `holdout_mean_net_return <= 0` 时，不得把 `csf_holdout_validation` 判成通过

所以这些 CSF stage 的通过语义是“artifact + metric gate 都通过”，而不是单纯“流程跑通”。

对 `csf_data_ready`、`csf_signal_ready`、`csf_train_freeze`、`csf_test_evidence`，当前 runtime 则执行 contract / semantic gates：

- `csf_data_ready` 会检查 panel key、time key、asset key 和 shared feature base 合同是否显式冻结
- `csf_signal_ready` 现在要求 `author/formal/route_inheritance_contract.yaml` 作为当前阶段唯一正式 route 继承凭证；它必须把 mandate 的 `research_route.yaml` 与当前阶段绑定起来
- `csf_data_ready` 会检查 `cross_section_coverage.parquet` 的 `coverage_ratio` 是否达到冻结的 coverage floor
- `csf_data_ready` 会生成并检查 `split_sample_adequacy_report.yaml`；每个 train/test/backtest/holdout split 至少要有 1 个 `cross_section_snapshot`，任一 split 不足时直接 FAIL
- `csf_signal_ready` 会检查 `factor_direction` 是否属于允许词表，且 panel key / final score 字段 / score formula 不得留空
- `csf_train_freeze` 会检查 candidate variants、kept variants 和 train-governable axes 是否显式冻结
- `csf_train_freeze` 还会检查 `train_factor_quality.parquet` 非空、`train_variant_ledger.csv` / `train_variant_rejects.csv` 是否覆盖 candidate / kept / rejected variants，以及 train-governable axes 是否与 signal-ready 后不可调轴重叠
- `csf_test_evidence` 会检查 test-selected variants 是否来自 train kept variants、`rank_ic_summary.json` 与 `csf_selected_variants_test.csv` 是否一致、`run_manifest.json` 是否绑定上游 train freeze formal artifacts
- `csf_backtest_ready` 会检查 portfolio weights 和 gate rows 是否只引用 test-selected variants、`portfolio_expression` 是否与 mandate route 一致、`mean_net_return` 是否为正、`run_manifest.json` 是否绑定上游 test evidence formal artifacts

所以这些阶段的 `PASS` 含义是“研究对象的合同边界已经冻结并可复用”，不是“后段表现已经成立”。

另外，`csf_data_ready` 与 `csf_signal_ready` 现在还会对部分表执行最小结构 gate：

- `row_count_gt`：表必须非空
- `unique_key`：如 `date × asset` 这类主键不得重复

所以这些阶段的 `.parquet` 产物不能只是占位文本，必须至少是可读取的最小真实 parquet。
对于 `csf_signal_ready`，这些最小真实 parquet 还应尽量从上游 `csf_data_ready` 冻结产物派生，而不是静态硬编码资产列表。

`csf_data_ready` 现在采用 contract-first 口径：`contracts/artifacts/csf_data_ready_artifacts.yaml` 是 formal artifact shape 真值，skill 和文档只解释执行顺序、字段含义和 review 边界。`split_sample_adequacy_report.yaml` 属于 `csf_data_ready` formal artifact，它基于本阶段已生成的 `cross_section_coverage.parquet` 和上游 `time_split.json` 记录每个 downstream split 的 `cross_section_snapshot` 数量；这不是 mandate 字段扩展，也不是单资产事件语义。author build 后必须运行 `qros-validate-stage --stage csf_data_ready`，并在进入 review 前通过 deterministic preflight；validator/preflight 不通过，不得进入 `csf_data_ready` review。这里不改变上面的 session rollout truth：`qros-session` 自动强制 review-entry preflight 仍是 mandate-first / mandate-only，但 `qros-csf-data-ready-review` 的 reviewer lane 入口必须使用 standalone preflight。

`csf_signal_ready` 也采用 contract-first 口径：`contracts/artifacts/csf_signal_ready_artifacts.yaml` 是 factor formal artifact shape 真值，skill 不再维护字段清单副本。author build 后必须运行 `qros-validate-stage --stage csf_signal_ready`，并通过 semantic validator / deterministic preflight；validator/preflight 不通过，不得进入 `csf_signal_ready` review。该 preflight 会检查 `factor_panel.parquet`、`factor_manifest.yaml`、`component_factor_manifest.yaml`、`route_inheritance_contract.yaml`、`factor_coverage_report.parquet`、`factor_group_context.parquet` 与上游 `csf_data_ready` / mandate route 的绑定。

`csf_train_freeze` 同样采用 contract-first 口径：`contracts/artifacts/csf_train_freeze_artifacts.yaml` 是 train formal artifact shape 真值，skill 只解释确认顺序和 review 边界。author build 后必须运行 `qros-validate-stage --stage csf_train_freeze`，并通过 csf_train_freeze semantic validator / deterministic preflight；validator/preflight 不通过，不得进入 `csf_train_freeze` review。该 preflight 会检查 `csf_train_freeze.yaml`、`train_factor_quality.parquet`、`train_variant_ledger.csv`、`train_variant_rejects.csv`、`train_bucket_diagnostics.parquet`、`train_neutralization_diagnostics.parquet` 与上游 `csf_signal_ready` factor contract 的绑定。

`csf_test_evidence` 也采用 contract-first 口径：`contracts/artifacts/csf_test_evidence_artifacts.yaml` 是 test formal artifact shape 真值，skill 只解释确认顺序、证据语义和 review 边界。author build 后必须运行 `qros-validate-stage --stage csf_test_evidence`，并通过 csf_test_evidence semantic validator / deterministic preflight；validator/preflight 不通过，不得进入 `csf_test_evidence` review。该 preflight 会检查 `rank_ic_timeseries.parquet`、`rank_ic_summary.json`、`bucket_returns.parquet`、`breadth_coverage_report.parquet`、`csf_test_gate_table.csv`、`csf_selected_variants_test.csv` 与上游 `csf_train_freeze` kept variants 的绑定。

`csf_backtest_ready` 也采用 contract-first 口径：`contracts/artifacts/csf_backtest_ready_artifacts.yaml` 是 backtest formal artifact shape 真值，skill 只解释确认顺序、组合语义和 review 边界。author build 后必须运行 `qros-validate-stage --stage csf_backtest_ready`，并通过 csf_backtest_ready semantic validator / deterministic preflight；validator/preflight 不通过，不得进入 `csf_backtest_ready` review。该 preflight 会检查 `portfolio_contract.yaml`、`portfolio_weight_panel.parquet`、`turnover_capacity_report.parquet`、`portfolio_summary.parquet`、`csf_backtest_gate_table.csv`、`csf_backtest_gate_decision.md`、`target_strategy_compare.parquet` 与上游 `csf_test_evidence` selected variants 的绑定。

`csf_holdout_validation` 也采用 contract-first 口径：`contracts/artifacts/csf_holdout_validation_artifacts.yaml` 是 holdout formal artifact shape 真值，skill 只解释确认顺序、最终验证语义和 review 边界。author build 后必须运行 `qros-validate-stage --stage csf_holdout_validation`，并通过 csf_holdout_validation semantic validator / deterministic preflight；validator/preflight 不通过，不得进入 `csf_holdout_validation` review。该 preflight 会检查 `csf_holdout_run_manifest.json`、`holdout_factor_diagnostics.parquet`、`holdout_test_compare.parquet`、`holdout_portfolio_compare.parquet`、`rolling_holdout_stability.json`、`regime_shift_audit.json` 与上游 `csf_backtest_ready` frozen portfolio / selected variants 的绑定。

## Internal Runtime

deterministic backend 的入口在克隆下来的仓库里：

```bash
./.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
```

如果你想先看当前状态而不是直接从对话里猜，可以直接运行 `qros-session`。默认会打印一块面向人的状态面板：

```text
Lineage: btc_leads_alts
🧭 Current orchestrator: qros-research-session
📍 Current stage: mandate_next_stage_confirmation_pending
🔨 Current active skill: qros-research-session
💡 Why this skill: Current stage mandate_next_stage_confirmation_pending is waiting for explicit approval before entering the downstream stage.
⛔ Blocking reason: Explicit confirmation to enter data_ready is still incomplete.
▶ Next action: Run with --confirm-next-stage or reply CONFIRM_NEXT_STAGE <lineage_id> to enter data_ready.
🔁 Resume hint: Confirm the next-stage handoff for mandate, then rerun qros-session --lineage-id btc_leads_alts.
🧠 Why now:
- qualified
⚠ Open risks:
- rollback_target remains 00_idea_intake
```

这里要区分三层语义：

- `Current orchestrator`：统一总控入口，始终是 `qros-research-session`
- `Current stage`：当前 lineage 真实所处的阶段
- `Current active skill`：按当前 stage / verdict 推导出来、制度上现在真正应该干活的 skill；如果 review verdict 进入失败类分支，这里会切到 `qros-stage-failure-handler`

如果某个非终态阶段已经 review closure 完成，session 会进入 `*_next_stage_confirmation_pending`，等待用户是否进入下一阶段。对最终的 `holdout_validation`，最后一次 `CONFIRM_NEXT_STAGE` 会把 session 标成 `holdout_validation_review_complete`。展示/总结不是 formal workflow gate；如果用户想看阶段总结，应直接在对话里提出。

如果你要让脚本输出机读状态而不是文本面板，可以加 `--json`：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --json
```

这适合：

- shell 脚本轮询当前 session 状态
- 后续 HUD 或自动化集成
- 想稳定读取 `current_stage / current_skill / next_action / resume_hint` 这些字段的场景

`--snapshot` 仍然输出 canonical anti-drift decision snapshot，不会附带 reflection 面板内容。

如果只想看研究员当前最关心的最新进度，而不是进入 session 推进流程，优先用只读命令：

```bash
./.qros/bin/qros-progress
./.qros/bin/qros-progress --lineage-id <lineage_id>
./.qros/bin/qros-progress --json
```

无 `--lineage-id` 时，`qros-progress` 展示最近修改 lineage 的状态；输出中的 `Lineage` 会明确标出实际选择的是哪条线。

如果想在正式 review 前看一眼横截面因子阶段质量，可以使用只读 diagnostics：

```bash
./.qros/bin/qros-factor-diagnostics
./.qros/bin/qros-factor-diagnostics --lineage-id <lineage_id>
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
./.qros/bin/qros-factor-diagnostics --json
```

`qros-factor-diagnostics` 只输出 health、confidence、observed diagnostics、missing diagnostics 和 next diagnostics。它不是 review verdict，也不是 gate verdict。

如果你需要把流程级验证也跑成固定命令，而不是每次临时拼 pytest 文件列表，可以直接用：

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

更细的分层说明见：

- `docs/guides/qros-verification-tiers.md`

例如，当 `data_ready` 已经 freeze 但本地程序还没补齐时，机读状态应明确给出 program gate：

```json
{
  "current_stage": "data_ready_author",
  "current_route": "time_series_signal",
  "stage_status": "awaiting_stage_program",
  "blocking_reason_code": "STAGE_PROGRAM_MISSING",
  "required_program_dir": "program/time_series/data_ready",
  "required_program_entrypoint": "run_stage.py",
  "program_contract_status": "missing",
  "provenance_status": "missing",
  "next_action": "Author the lineage-local stage program under program/time_series/data_ready.",
  "resume_hint": "Continue in the same research repo after adding stage_program.yaml, README.md, and the entrypoint."
}
```

如果要做调试或手动恢复，也可以通过下面的命令显式触发 intake interview approval：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-intake
```

当当前状态是某个 `*_confirmation_pending` freeze gate 时，文本面板会展示全部 `Freeze groups` 及其 confirmed/pending 状态。agent 可以一次回显全部 group draft；如果用户看完后回复 `确认全部`，可以用下面的命令批量标记当前 draft 的所有 groups 已确认：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-all-freeze-groups
```

这个命令只写当前 freeze draft 的 group confirmations，不会替代最终 stage approval。批量确认后仍然必须再得到对应的最终确认，例如 `--confirm-mandate`、`--confirm-data-ready`、`--confirm-signal-ready`。

如果要做调试或手动恢复，也可以通过下面的命令显式触发 mandate approval：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-mandate
```

如果要做调试或手动恢复，也可以通过下面的命令显式触发 data_ready approval：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-data-ready
```

如果要做调试或手动恢复，也可以通过下面的命令显式触发 signal_ready approval：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-signal-ready
```

如果要做调试或手动恢复，也可以通过下面的命令显式触发 train_freeze approval：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-train-freeze
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready 和 train_freeze。

对于 `data_ready`，这里的“build `02_data_ready/`”指的是在当前研究仓真实物化共享数据层和证据，而不是只在 QROS 框架仓里演示目录结构，或只写一份 skeleton 文档。

如果要做调试或手动恢复，也可以通过下面的命令显式触发 test_evidence approval：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-test-evidence
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze 和 test_evidence。

对于 `signal_ready`、`train_freeze`、`test_evidence`、`backtest_ready` 和 `holdout_validation`，这里的“build stage dir”同样指在当前研究仓真实生成该阶段要求的正式产物和证据，而不是只落目录、placeholder 文件或合同说明文档。

如果要做调试或手动恢复，也可以通过下面的命令显式触发 backtest_ready approval：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-backtest-ready
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze、test_evidence 和 backtest_ready。

如果要做调试或手动恢复，也可以通过下面的命令显式触发 holdout_validation approval：

```bash
./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-holdout-validation
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze、test_evidence、backtest_ready 和 holdout_validation。

正常 review 主路径还应保持一个简单纪律：

- 一个 active review cycle 只认一个 reviewer child
- reviewer child 只读 `review/request/*` 和 `author/formal/*`
- reviewer child 只写 `review/result/*`
- 主 Agent 只在自己已经能清楚说出“这轮 reviewer 要验证哪些 formal gate、哪些 outputs 已经准备好”时才发起 review

## How Stage Detection Works

session runtime 会按下面这个顺序检查磁盘状态：

1. no intake scaffold yet -> `idea_intake`
2. intake scaffold exists but intake interview is not explicitly approved -> `idea_intake_confirmation_pending`
3. intake interview approved but intake gate is not yet admitted -> `idea_intake`
4. intake admitted but not explicitly approved for mandate -> `mandate_confirmation_pending`
5. freeze approval 缺失 -> 当前 `*_confirmation_pending` stage 保持 `awaiting_freeze_approval`
6. freeze approval 已记录后，runtime 先解析当前 stage 对应的 route-neutral 或 route-aware program dir
7. required program dir 不存在 -> 当前 stage 保持 author/build 态，但 `stage_status = awaiting_stage_program`
8. program dir 存在但 `stage_program.yaml`、entrypoint 或 authored_by 合同不合法 -> `stage_status = awaiting_program_validation`
9. program contract 合法但程序执行失败、provenance 缺失或 required outputs 不成立 -> `awaiting_program_execution` / 相应 blocking reason
10. stage artifacts 与 `program_execution_manifest.json` 都成立，但 review 还没开始 -> `<stage>_review_confirmation_pending`，并要求人显式进入对应 `qros-*-review`；当前只有 `mandate_review_confirmation_pending` 会先经过 mandatory review-entry preflight，其余 post-mandate review-confirm stages 仍停留在 mandate-first / mandate-only rollout truth
11. review 已开始但 closure 还缺失 -> `<stage>_review`，review substate 会落在 `awaiting_adversarial_review`、`awaiting_author_fix` 或 `awaiting_review_closure`
12. 任一非终态 stage 的 review closure exists 但 downstream handoff 未确认 -> `<stage>_next_stage_confirmation_pending`
13. 对非终态 stage，收到 `CONFIRM_NEXT_STAGE` 后 -> 下游 `<next_stage>_confirmation_pending`
14. `holdout_validation` review closure exists 但最终 handoff 未确认 -> `holdout_validation_next_stage_confirmation_pending`
15. 收到最终 `CONFIRM_NEXT_STAGE` 后 -> `holdout_validation_review_complete`

如果某个 reviewed stage 的 closure verdict 是 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE`，session 必须停止正常推进，转入 `qros-stage-failure-handler`，而不是继续打开下一个阶段。

## Expected User Experience

用户从一个 skill 开始：

- `qros-research-session`

然后系统会：

- 解析或创建 lineage
- 如果需要，先 scaffold intake
- 报告当前 stage
- 在可以确定性写盘时写入 deterministic artifacts
- 遇到缺失的研究判断或显式治理批准时停下来提问
- 对于一个全新的想法，先问 intake 问题，而不是静默完成 qualification
- 在把 intake interview 变成正式 qualification verdict 之前，先问一个显式确认问题
- 确认 `observation`
- 确认 `primary hypothesis`
- 确认 `counter-hypothesis`
- 确认 `market` / `universe` / `target_task`
- 确认 `data_source` / `bar_size`
- 确认 `kill criteria` 或 `reframe` 条件
- 一次展示全部 group draft 或按 group 交互式冻结 mandate
- 确认 `research_intent`
- 确认 `scope_contract`
- 确认 `data_contract`
  这里会明确问数据来源哪里来，以及后续研究周期基于什么 `bar_size`，例如 `1m`、`5m`、`15m`
- 确认 `execution_contract`
- 在生成 mandate 前先问 `是否确认进入 mandate？`
- mandate review closure 完成后，先进入 `mandate_next_stage_confirmation_pending`；确认 handoff 后，再按 group 交互式冻结 data_ready
- 确认 `extraction_contract`
- 确认 `quality_semantics`
- 确认 `universe_admission`
- 确认 `shared_derived_layer`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的共享输出，以及 QC 或 coverage 证据
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `data_ready`
- 在生成 data_ready 前先问 `是否按以上内容冻结 data_ready？`
- data_ready review closure 完成后，先进入 `data_ready_next_stage_confirmation_pending`；确认 handoff 后，再按 group 交互式冻结 signal_ready
- 确认 `signal_expression`
- 确认 `param_identity`
- 确认 `time_semantics`
- 确认 `signal_schema`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 baseline signal timeseries、param manifests 和 coverage 证据
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `signal_ready`
- 在生成 signal_ready 前先问 `是否按以上内容冻结 signal_ready？`
- signal_ready review closure 完成后，先进入 `signal_ready_next_stage_confirmation_pending`；确认 handoff 后，再按 group 交互式冻结 train_freeze
- 确认 `window_contract`
- 确认 `threshold_contract`
- 确认 `quality_filters`
- 确认 `param_governance`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 train thresholds、质量输出和 ledgers
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `train_freeze`
- 在生成 train_freeze 前先问 `是否按以上内容冻结 train_freeze？`
- train_freeze review closure 完成后，先进入 `train_freeze_next_stage_confirmation_pending`；确认 handoff 后，再按 group 交互式冻结 test_evidence
- 确认 `window_contract`
- 确认 `formal_gate_contract`
- 确认 `admissibility_contract`
- 确认 `audit_contract`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 independent-sample statistics、admissibility outputs 和 frozen selections
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `test_evidence`
- 在生成 test_evidence 前先问 `是否按以上内容冻结 test_evidence？`
- test_evidence review closure 完成后，先进入 `test_evidence_next_stage_confirmation_pending`；确认 handoff 后，再按 group 交互式冻结 backtest_ready
- 确认 `execution_policy`
- 确认 `portfolio_policy`
- 确认 `risk_overlay`
- 确认 `engine_contract`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 dual-engine backtest outputs、combo ledgers 和 capacity evidence
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `backtest_ready`
- 在生成 backtest_ready 前先问 `是否按以上内容冻结 backtest_ready？`
- backtest_ready review closure 完成后，先进入 `backtest_ready_next_stage_confirmation_pending`；确认 handoff 后，再按 group 交互式冻结 holdout_validation
- 确认 `window_contract`
- 确认 `reuse_contract`
- 确认 `drift_audit`
- 确认 `failure_governance`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 single-window、merged-window 和 comparison outputs
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `holdout_validation`
- 在生成 holdout_validation 前先问 `是否按以上内容冻结 holdout_validation？`

## Example Path

1. 从一个关于 BTC 带动 alt 反应的 raw idea 开始
2. QROS 创建 lineage，并 scaffold `00_idea_intake/`
3. QROS 会先问 intake 问题，而不是静默完成 qualification
4. 然后补齐 intake artifacts，并产出 `idea_gate_decision.yaml`
5. 如果 verdict 是 `GO_TO_MANDATE`，QROS 会停在 `mandate_confirmation_pending`
6. QROS 进入 grouped freeze 模式，一次展示全部 group draft 或按 group 展示，而不是静默写出 mandate
7. QROS 确认 `research_intent`
8. QROS 确认 `scope_contract`
9. QROS 确认 `data_contract`
   这里会明确问数据来源和 `bar_size`
10. QROS 确认 `execution_contract`
11. QROS 展示最终的 grouped mandate summary，并询问 `是否确认进入 mandate？`
12. 用户用自然语言回答
13. agent 在内部记录批准决定，然后先补齐 `outputs/<lineage_id>/program/mandate/` 下的 stage program，再由 runtime 校验并调用它构建 `01_mandate/`
14. mandate review closure 完成后，QROS 先进入 `mandate_next_stage_confirmation_pending`；收到 `CONFIRM_NEXT_STAGE` 后再进入 `data_ready_confirmation_pending`
15. QROS 确认 `extraction_contract`
16. QROS 确认 `quality_semantics`
17. QROS 确认 `universe_admission`
18. QROS 确认 `shared_derived_layer`
19. QROS 确认 `delivery_contract`
20. QROS 展示最终的 grouped data_ready summary，并询问 `是否按以上内容冻结 data_ready？`
21. agent 在内部记录批准决定，然后先补齐 `outputs/<lineage_id>/program/time_series/data_ready/`，再由 runtime 校验并调用它构建 `02_data_ready/`
22. 这个 build 应该真实物化共享数据产物和证据，而不是只 scaffold 目录或写 placeholder 文件
23. data_ready review closure 完成后，QROS 先进入 `data_ready_next_stage_confirmation_pending`；收到 `CONFIRM_NEXT_STAGE` 后再进入 `signal_ready_confirmation_pending`
24. QROS 确认 `signal_expression`
25. QROS 确认 `param_identity`
26. QROS 确认 `time_semantics`
27. QROS 确认 `signal_schema`
28. QROS 确认 `delivery_contract`
29. QROS 展示最终的 grouped signal_ready summary，并询问 `是否按以上内容冻结 signal_ready？`
30. agent 在内部记录批准决定，然后先补齐 `outputs/<lineage_id>/program/time_series/signal_ready/`，再由 runtime 校验并调用它构建 `03_signal_ready/`
31. 这个 build 应该真实物化 signal timeseries、param manifests 和 coverage 证据，而不是只 scaffold 目录或写 placeholder 文件
32. signal_ready review closure 完成后，QROS 先进入 `signal_ready_next_stage_confirmation_pending`；收到 `CONFIRM_NEXT_STAGE` 后再进入 `train_freeze_confirmation_pending`
33. QROS 确认 `window_contract`
34. QROS 确认 `threshold_contract`
35. QROS 确认 `quality_filters`
36. QROS 确认 `param_governance`
37. QROS 确认 `delivery_contract`
38. QROS 展示最终的 grouped train_freeze summary，并询问 `是否按以上内容冻结 train_freeze？`
39. agent 在内部记录批准决定，然后先补齐 `outputs/<lineage_id>/program/time_series/train_freeze/`，再由 runtime 校验并调用它构建 `04_train_freeze/`
40. 这个 build 应该真实物化 train thresholds、质量输出和 ledgers，而不是只 scaffold 目录或写 placeholder 文件
41. train_freeze review closure 完成后，QROS 先进入 `train_freeze_next_stage_confirmation_pending`；收到 `CONFIRM_NEXT_STAGE` 后再进入 `test_evidence_confirmation_pending`
42. QROS 确认 `window_contract`
43. QROS 确认 `formal_gate_contract`
44. QROS 确认 `admissibility_contract`
45. QROS 确认 `audit_contract`
46. QROS 确认 `delivery_contract`
47. QROS 展示最终的 grouped test_evidence summary，并询问 `是否按以上内容冻结 test_evidence？`
48. agent 在内部记录批准决定，然后先补齐 `outputs/<lineage_id>/program/time_series/test_evidence/`，再由 runtime 校验并调用它构建 `05_test_evidence/`
49. 这个 build 应该真实物化 test statistics、admissibility outputs 和 frozen selection artifacts，而不是只 scaffold 目录或写 placeholder 文件
50. test_evidence review closure 完成后，QROS 先进入 `test_evidence_next_stage_confirmation_pending`；收到 `CONFIRM_NEXT_STAGE` 后再进入 `backtest_ready_confirmation_pending`
51. QROS 确认 `execution_policy`
52. QROS 确认 `portfolio_policy`
53. QROS 确认 `risk_overlay`
54. QROS 确认 `engine_contract`
55. QROS 确认 `delivery_contract`
56. QROS 展示最终的 grouped backtest_ready summary，并询问 `是否按以上内容冻结 backtest_ready？`
57. agent 在内部记录批准决定，然后先补齐 `outputs/<lineage_id>/program/time_series/backtest_ready/`，再由 runtime 校验并调用它构建 `06_backtest/`
58. 这个 build 应该真实物化 dual-engine backtest outputs、combo ledgers 和 capacity evidence，而不是只 scaffold 目录或写 placeholder 文件
59. backtest_ready review closure 完成后，QROS 先进入 `backtest_ready_next_stage_confirmation_pending`；收到 `CONFIRM_NEXT_STAGE` 后再进入 `holdout_validation_confirmation_pending`
60. QROS 确认 `window_contract`
61. QROS 确认 `reuse_contract`
62. QROS 确认 `drift_audit`
63. QROS 确认 `failure_governance`
64. QROS 确认 `delivery_contract`
65. QROS 展示最终的 grouped holdout_validation summary，并询问 `是否按以上内容冻结 holdout_validation？`
66. agent 在内部记录批准决定，然后先补齐 `outputs/<lineage_id>/program/time_series/holdout_validation/`，再由 runtime 校验并调用它构建 `07_holdout/`
67. 这个 build 应该真实物化 single-window、merged-window 和 comparison outputs，而不是只 scaffold 目录或写 placeholder 文件
68. holdout_validation review closure 完成后，QROS 先进入 `holdout_validation_next_stage_confirmation_pending`；收到最终 `CONFIRM_NEXT_STAGE` 后进入 `holdout_validation_review_complete`，而不是继续进入更后面的治理阶段

## Why This Exists

这个设计的目标，是把内部脚本隐藏在一个一致的 skill 流程后面。

这些脚本仍然重要，因为它们是 deterministic runtime；但从用户视角，主要应该通过 `qros-research-session` 交互。

在 review 阶段，session 现在会显式区分几类状态：

- `awaiting_adversarial_review`：当前 stage 还没有 active review cycle，或 reviewer 子代理尚未写出 review 结果
- `awaiting_spawned_reviewer_completion`：active review cycle 已注册，当前只等待该 reviewer 子代理落 `review/result/*`
- `awaiting_reviewer_write_scope_audit`：closure-ready result 已存在，但 deterministic closer 还没完成 audit / closure
- `awaiting_author_fix`：reviewer 给出 `FIX_REQUIRED`，必须显式回 author lane 修复
- `awaiting_review_closure`：reviewer 已给出 `CLOSURE_READY_*`，等待 deterministic closer 写正式 closure artifacts

也就是说，单独运行 closure engine 已经不再构成有效 review；必须先有 adversarial reviewer 结果，并且 reviewer 不能与 author 是同一身份。author lane 与 reviewer 子代理之间的切换也必须是显式的，不再由 author 主会话静默自审。

在这层 review 闭环之上，QROS 还会为 **future-only** 的 institutional learning 写出治理候选信号；具体 contract 见上面的 `Governance-candidate lane` 小节。
