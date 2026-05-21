# QROS Codex 快速开始

---

<br>

## 1. 安装

先在 active research repo 根目录打开 Codex。

如果你想走最短的 Codex-native 路径，告诉 Codex：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

Codex 会安装全局 QROS skills，初始化当前 research repo 的 `./.qros/`，然后要求你重启 Codex。重启后，在同一个 active research repo 中运行 `qros-research-session`。

---

<br>

## 2. 从统一 Skill 开始

在 Codex 里按目的选择命令：

| 目的 | 在 Codex 里输入 |
| --- | --- |
| 开始或继续一条研究线 | `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT` |
| 查看 QROS 使用帮助 | `qros-research-session help` |
| 查看当前研究进度 | `qros-progress` |
| 更新 QROS 到最新稳定版本，并刷新当前 host + 当前 repo 的 `./.qros/` | `qros-update` |

正常用户从这里开始，不需要先跑 `./.qros/bin/qros-session`。

新 QROS lineage 的第一站是 `mandate_admission`。QROS 不再为新研究线创建 `00_idea_intake/`；原 intake 资格评估、scope、route assessment 和 kill criteria 现在集中在 `01_mandate/author/draft/mandate_admission.yaml`。当 admission 被接受后，流程进入 `mandate_freeze_confirmation_pending`，用户只需要确认 mandate freeze。

`qros-update` 同时适用于 Codex 和 Claude Code。你只需要在 active research repo 根目录输入 `qros-update`；它会自动识别当前 host，刷新全局 QROS 安装，并重建当前 repo 的 `./.qros/` runtime，默认跟踪最新稳定版本。

如果你是框架开发者并且需要显式跟踪未发布主干，使用 `qros-update main`。

> 如果你第一次看到 `research_intent`、`window_contract`、`delivery_contract` 这类 group 名，先看：
>
> - `docs/guides/stage-freeze-group-field-guide.md`

---

<br>

## 3. 让 Agent 推进当前流程

当前 QROS 的第一阶段主流程是：

- `idea_intake`
- `mandate`
- `mandate review`
- `time_series_signal` route：
  - `tss_data_ready`
  - `tss_signal_ready`
  - `tss_train_freeze`
  - `tss_test_evidence`
  - `tss_backtest_ready`
  - `tss_holdout_validation`
- `cross_sectional_factor` route：
  - `csf_data_ready`
  - `csf_signal_ready`
  - `csf_train_freeze`
  - `csf_test_evidence`
  - `csf_backtest_ready`
  - `csf_holdout_validation`

Agent 应该做这些事：

- 创建或恢复当前 lineage
- 缺少 `mandate_admission` draft 时进行 scaffold
- 对全新的 raw idea 先停在 `mandate_admission`，补齐 observation、hypothesis、scope、data source、`bar_size`、route assessment 和 kill criteria
- admission 通过后进入 `mandate_freeze_confirmation_pending`，逐组确认 `research_intent`、`scope_contract`、`data_contract`、`execution_contract`
- `mandate` review closure 后先进入 `mandate_next_stage_confirmation_pending`，等显式 `CONFIRM_NEXT_STAGE` 后按 `research_route` 进入 `tss_*` 或 `csf_*` 阶段
- 每个 route-specific stage 都要先冻结 grouped contracts，再由当前 active research repo 真实生成 formal artifacts，然后由 `qros-research-session` 显式确认并编排 review
- 不得把空目录、placeholder 文件、contract-only markdown 或本仓库里的说明文档当成阶段完成
- review verdict 不是正常放行时，停止普通阶段推进，转入 `qros-stage-failure-handler`

如果要看每个阶段具体冻结哪些 group，看：

- `docs/guides/stage-freeze-group-field-guide.md`
- `docs/guides/qros-research-session-usage.md`

---

<br>

## 4. 你应该看到什么

Agent 应该报告：

- `lineage`
- `current_stage`
- `artifacts_written`
- `gate_status`
- `next_action`
- `why_now`
- `open_risks`

底层 runtime 会把 artifacts 写到 active research repo 的 `outputs/<lineage_id>/` 下。

> 对 route-specific `tss_*` / `csf_*` 阶段，这些 artifacts 必须是真实阶段交付。目录骨架、placeholder 文件和只有文档解释的替代物，不足以声称阶段完成。

> **Review failure 不是普通 debug，也不是普通调试。** 如果某个 stage review 以 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE` 结束，session 应停止普通阶段推进，暴露 `requires_failure_handling`，并切换到 `qros-stage-failure-handler`。

> 如果 controlled retry 写出的 `failure_packages/*/post_retry_decision.yaml` 中 `normal_progression_allowed: false`，runtime 应暴露 `FAILURE_DISPOSITION_REQUIRED`。在 failure package 写出带 `NO_GO` 或 `CHILD_LINEAGE` 的 `failure_disposition.yaml` 之前，原 lineage 不得重新进入 review 或 next-stage progression；即使 disposition 已写出，原 lineage 的普通推进仍保持阻塞。

---

<br>

## 5. 内部 Runtime 说明

QROS 内部仍使用脚本做 deterministic state transitions，但这些是 runtime 内部机制，不是普通用户的主入口。

---

<br>

## 6. 结束状态

route-specific holdout review closure 后，runtime 会进入对应的 `<route>_holdout_validation_next_stage_confirmation_pending`。显式 `CONFIRM_NEXT_STAGE` 后，它会进入 `<route>_holdout_validation_review_complete`，不会继续进入更后面的治理阶段。

> Codex 直接通过 `~/.codex/skills/` 发现 QROS；`./setup` 会把扁平化的 `qros-*` skills 写到那里。
