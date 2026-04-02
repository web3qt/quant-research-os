# QROS Research Session Usage

## What It Is

`qros-research-session` 是当前这段 QROS 工作流的统一单入口 orchestrator。

用户不需要记多个命令，只要从这一个 skill 开始，让 QROS 判断当前 lineage 处在哪个阶段。

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

之后 agent 会接管并推进整个 session。

Codex 会通过 `~/.agents/skills/qros` 找到这个 skill；这个路径应当指向 `~/.qros/skills`。

对于一个全新的 raw idea，正常行为不应该是直接替用户完成 `qualification_scorecard.yaml` 和 `idea_gate_decision.yaml`。第一轮应该先停在 `idea_intake_confirmation_pending`，先问清 observation、hypothesis、scope、data source、`bar_size` 和 kill criteria，并在得到显式确认后再进入正式 qualification。

QROS 仓库是工作流框架，不是研究产物仓。安装后，agent 应该在用户当前打开的 research repo 中推进 lineage，并把正式阶段产物写到那个 repo 的 `outputs/<lineage_id>/` 下；空目录、placeholder 文件和只有合同语义的说明文档不能被当作 `data_ready` 或其他阶段已经真实完成。

阶段 review 失败不是普通调试。当当前 stage review verdict 是 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE` 时，QROS 不应继续普通阶段推进，而应根据 runtime 的 `requires_failure_handling` 信号切换到 `qros-stage-failure-handler`。

## Internal Runtime

deterministic backend 的入口在克隆下来的仓库里：

```bash
~/.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
```

如果你想先看当前状态而不是直接从对话里猜，可以直接运行 `qros-session`。默认会打印一块面向人的状态面板：

```text
Lineage: btc_leads_alts
🧭 Current orchestrator: qros-research-session
📍 Current stage: data_ready_confirmation_pending
🔨 Current active skill: qros-data-ready-author
💡 Why this skill: Current stage data_ready_confirmation_pending is in the authoring/freeze flow, so qros-data-ready-author is the active author skill.
⛔ Blocking reason: data_ready freeze confirmation is still incomplete.
▶ Next action: Complete data_ready freeze group: extraction_contract
🔁 Resume hint: Continue in the same research repo and rerun qros-session --lineage-id btc_leads_alts after completing the next required step.
🧠 Why now:
- qualified
⚠ Open risks:
- rollback_target remains 00_idea_intake
```

这里要区分三层语义：

- `Current orchestrator`：统一总控入口，始终是 `qros-research-session`
- `Current stage`：当前 lineage 真实所处的阶段
- `Current active skill`：按当前 stage / verdict 推导出来、制度上现在真正应该干活的 skill；如果 review verdict 进入失败类分支，这里会切到 `qros-stage-failure-handler`

如果你要让脚本输出机读状态而不是文本面板，可以加 `--json`：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --json
```

这适合：

- shell 脚本轮询当前 session 状态
- 后续 HUD 或自动化集成
- 想稳定读取 `current_stage / current_skill / next_action / resume_hint` 这些字段的场景

如果要做调试或手动恢复，也可以通过下面的命令显式触发 intake interview approval：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --confirm-intake
```

如果要做调试或手动恢复，也可以通过下面的命令显式触发 mandate approval：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --confirm-mandate
```

如果要做调试或手动恢复，也可以通过下面的命令显式触发 data_ready approval：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --confirm-data-ready
```

如果要做调试或手动恢复，也可以通过下面的命令显式触发 signal_ready approval：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --confirm-signal-ready
```

如果要做调试或手动恢复，也可以通过下面的命令显式触发 train_freeze approval：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --confirm-train-freeze
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready 和 train_freeze。

对于 `data_ready`，这里的“build `02_data_ready/`”指的是在当前研究仓真实物化共享数据层和证据，而不是只在 QROS 框架仓里演示目录结构，或只写一份 skeleton 文档。

如果要做调试或手动恢复，也可以通过下面的命令显式触发 test_evidence approval：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --confirm-test-evidence
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze 和 test_evidence。

对于 `signal_ready`、`train_freeze`、`test_evidence`、`backtest_ready` 和 `holdout_validation`，这里的“build stage dir”同样指在当前研究仓真实生成该阶段要求的正式产物和证据，而不是只落目录、placeholder 文件或合同说明文档。

如果要做调试或手动恢复，也可以通过下面的命令显式触发 backtest_ready approval：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --confirm-backtest-ready
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze、test_evidence 和 backtest_ready。

如果要做调试或手动恢复，也可以通过下面的命令显式触发 holdout_validation approval：

```bash
~/.qros/bin/qros-session --lineage-id <lineage_id> --confirm-holdout-validation
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze、test_evidence、backtest_ready 和 holdout_validation。

## How Stage Detection Works

session runtime 会按下面这个顺序检查磁盘状态：

1. no intake scaffold yet -> `idea_intake`
2. intake scaffold exists but intake interview is not explicitly approved -> `idea_intake_confirmation_pending`
3. intake interview approved but intake gate is not yet admitted -> `idea_intake`
4. intake admitted but not explicitly approved for mandate -> `mandate_confirmation_pending`
5. intake admitted and explicitly approved, but mandate not built -> `mandate`
6. mandate artifacts exist but review closure is missing -> `mandate review`
7. mandate review closure exists -> `data_ready_confirmation_pending`
8. data_ready artifacts exist but review closure is missing -> `data_ready review`
9. data_ready review closure exists -> `signal_ready_confirmation_pending`
10. signal_ready artifacts exist but review closure is missing -> `signal_ready review`
11. signal_ready review closure exists -> `train_freeze_confirmation_pending`
12. train_freeze artifacts exist but review closure is missing -> `train_freeze review`
13. train_freeze review closure exists -> `test_evidence_confirmation_pending`
14. test_evidence artifacts exist but review closure is missing -> `test_evidence review`
15. test_evidence review closure exists -> `backtest_ready_confirmation_pending`
16. backtest_ready artifacts exist but review closure is missing -> `backtest_ready review`
17. backtest_ready review closure exists -> `holdout_validation_confirmation_pending`
18. holdout_validation artifacts exist but review closure is missing -> `holdout_validation review`
19. holdout_validation review closure exists -> session stops and reports completion

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
- 按 group 交互式冻结 mandate
- 确认 `research_intent`
- 确认 `scope_contract`
- 确认 `data_contract`
  这里会明确问数据来源哪里来，以及后续研究周期基于什么 `bar_size`，例如 `1m`、`5m`、`15m`
- 确认 `execution_contract`
- 在生成 mandate 前先问 `是否确认进入 mandate？`
- mandate review closure 完成后，按 group 交互式冻结 data_ready
- 确认 `extraction_contract`
- 确认 `quality_semantics`
- 确认 `universe_admission`
- 确认 `shared_derived_layer`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的共享输出，以及 QC 或 coverage 证据
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `data_ready`
- 在生成 data_ready 前先问 `是否按以上内容冻结 data_ready？`
- data_ready review closure 完成后，按 group 交互式冻结 signal_ready
- 确认 `signal_expression`
- 确认 `param_identity`
- 确认 `time_semantics`
- 确认 `signal_schema`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 baseline signal timeseries、param manifests 和 coverage 证据
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `signal_ready`
- 在生成 signal_ready 前先问 `是否按以上内容冻结 signal_ready？`
- signal_ready review closure 完成后，按 group 交互式冻结 train_freeze
- 确认 `window_contract`
- 确认 `threshold_contract`
- 确认 `quality_filters`
- 确认 `param_governance`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 train thresholds、质量输出和 ledgers
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `train_freeze`
- 在生成 train_freeze 前先问 `是否按以上内容冻结 train_freeze？`
- train_freeze review closure 完成后，按 group 交互式冻结 test_evidence
- 确认 `window_contract`
- 确认 `formal_gate_contract`
- 确认 `admissibility_contract`
- 确认 `audit_contract`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 independent-sample statistics、admissibility outputs 和 frozen selections
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `test_evidence`
- 在生成 test_evidence 前先问 `是否按以上内容冻结 test_evidence？`
- test_evidence review closure 完成后，按 group 交互式冻结 backtest_ready
- 确认 `execution_policy`
- 确认 `portfolio_policy`
- 确认 `risk_overlay`
- 确认 `engine_contract`
- 确认 `delivery_contract`
- 让当前 research repo 真实物化这些 group 承诺的 dual-engine backtest outputs、combo ledgers 和 capacity evidence
- 不把空目录、placeholder 文件或只有合同语义的 markdown 视为已完成的 `backtest_ready`
- 在生成 backtest_ready 前先问 `是否按以上内容冻结 backtest_ready？`
- backtest_ready review closure 完成后，按 group 交互式冻结 holdout_validation
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
6. QROS 进入 grouped freeze 模式，而不是静默写出 mandate
7. QROS 确认 `research_intent`
8. QROS 确认 `scope_contract`
9. QROS 确认 `data_contract`
   这里会明确问数据来源和 `bar_size`
10. QROS 确认 `execution_contract`
11. QROS 展示最终的 grouped mandate summary，并询问 `是否确认进入 mandate？`
12. 用户用自然语言回答
13. agent 在内部记录批准决定，然后构建 `01_mandate/`
14. mandate review closure 完成后，QROS 进入 `data_ready_confirmation_pending`
15. QROS 确认 `extraction_contract`
16. QROS 确认 `quality_semantics`
17. QROS 确认 `universe_admission`
18. QROS 确认 `shared_derived_layer`
19. QROS 确认 `delivery_contract`
20. QROS 展示最终的 grouped data_ready summary，并询问 `是否按以上内容冻结 data_ready？`
21. agent 在内部记录批准决定，然后在当前 active research repo 中构建 `02_data_ready/`
22. 这个 build 应该真实物化共享数据产物和证据，而不是只 scaffold 目录或写 placeholder 文件
23. data_ready review closure 完成后，QROS 进入 `signal_ready_confirmation_pending`
24. QROS 确认 `signal_expression`
25. QROS 确认 `param_identity`
26. QROS 确认 `time_semantics`
27. QROS 确认 `signal_schema`
28. QROS 确认 `delivery_contract`
29. QROS 展示最终的 grouped signal_ready summary，并询问 `是否按以上内容冻结 signal_ready？`
30. agent 在内部记录批准决定，然后在当前 active research repo 中构建 `03_signal_ready/`
31. 这个 build 应该真实物化 signal timeseries、param manifests 和 coverage 证据，而不是只 scaffold 目录或写 placeholder 文件
32. signal_ready review closure 完成后，QROS 进入 `train_freeze_confirmation_pending`
33. QROS 确认 `window_contract`
34. QROS 确认 `threshold_contract`
35. QROS 确认 `quality_filters`
36. QROS 确认 `param_governance`
37. QROS 确认 `delivery_contract`
38. QROS 展示最终的 grouped train_freeze summary，并询问 `是否按以上内容冻结 train_freeze？`
39. agent 在内部记录批准决定，然后在当前 active research repo 中构建 `04_train_freeze/`
40. 这个 build 应该真实物化 train thresholds、质量输出和 ledgers，而不是只 scaffold 目录或写 placeholder 文件
41. train_freeze review closure 完成后，QROS 进入 `test_evidence_confirmation_pending`
42. QROS 确认 `window_contract`
43. QROS 确认 `formal_gate_contract`
44. QROS 确认 `admissibility_contract`
45. QROS 确认 `audit_contract`
46. QROS 确认 `delivery_contract`
47. QROS 展示最终的 grouped test_evidence summary，并询问 `是否按以上内容冻结 test_evidence？`
48. agent 在内部记录批准决定，然后在当前 active research repo 中构建 `05_test_evidence/`
49. 这个 build 应该真实物化 test statistics、admissibility outputs 和 frozen selection artifacts，而不是只 scaffold 目录或写 placeholder 文件
50. test_evidence review closure 完成后，QROS 进入 `backtest_ready_confirmation_pending`
51. QROS 确认 `execution_policy`
52. QROS 确认 `portfolio_policy`
53. QROS 确认 `risk_overlay`
54. QROS 确认 `engine_contract`
55. QROS 确认 `delivery_contract`
56. QROS 展示最终的 grouped backtest_ready summary，并询问 `是否按以上内容冻结 backtest_ready？`
57. agent 在内部记录批准决定，然后在当前 active research repo 中构建 `06_backtest/`
58. 这个 build 应该真实物化 dual-engine backtest outputs、combo ledgers 和 capacity evidence，而不是只 scaffold 目录或写 placeholder 文件
59. backtest_ready review closure 完成后，QROS 进入 `holdout_validation_confirmation_pending`
60. QROS 确认 `window_contract`
61. QROS 确认 `reuse_contract`
62. QROS 确认 `drift_audit`
63. QROS 确认 `failure_governance`
64. QROS 确认 `delivery_contract`
65. QROS 展示最终的 grouped holdout_validation summary，并询问 `是否按以上内容冻结 holdout_validation？`
66. agent 在内部记录批准决定，然后在当前 active research repo 中构建 `07_holdout/`
67. 这个 build 应该真实物化 single-window、merged-window 和 comparison outputs，而不是只 scaffold 目录或写 placeholder 文件
68. holdout_validation review closure 完成后，session 会停止，而不是继续进入更后面的阶段

## Why This Exists

这个设计的目标，是把内部脚本隐藏在一个一致的 skill 流程后面。

这些脚本仍然重要，因为它们是 deterministic runtime；但从用户视角，主要应该通过 `qros-research-session` 交互。
