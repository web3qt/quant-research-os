---
name: qros-progress
description: Use when the user asks for latest QROS research progress, current lineage status, current stage, blocking gate, next action, or explicitly invokes qros-progress.
---

# QROS Progress

## Purpose

这是只读进度查询 skill。

它告诉研究员当前 research repo 中最新或指定 lineage：

- 推进到哪个 `current_stage`
- 当前制度上应使用哪个 `current_skill`
- 当前 `gate_status` / `stage_status` 是什么
- 是否存在 `blocking_reason`
- 下一步应该做什么

## Required Runtime

优先使用 repo-local wrapper：

```bash
./.qros/bin/qros-progress
./.qros/bin/qros-progress --lineage-id "<lineage_id>"
```

需要机读输出时使用：

```bash
./.qros/bin/qros-progress --json
./.qros/bin/qros-progress --lineage-id "<lineage_id>" --json
```

## Hard Boundaries

- 不写 artifact。
- 不创建 lineage。
- 不 scaffold `00_idea_intake/`。
- 不确认任何 transition。
- 不把目录存在、placeholder 文件或 contract-only 文档说成 stage 已完成。
- 不替代 `qros-research-session`、stage author skill、review skill 或 failure handling skill。

## Reporting Rules

汇报时至少覆盖：

- `lineage_id`
- `current_stage`
- `current_skill`
- `stage_status`
- `gate_status`
- `blocking_reason`
- `next_action`
- `open_risks`

如果无参数查询，必须说明这是最新修改 lineage 的状态，而不是全 repo 聚合状态。

## Interpretation Discipline

`qros-progress` 只是查看状态，不改变状态。

如果输出显示：

- `current_skill = qros-stage-failure-handler`，应进入 failure handling，而不是继续普通 stage 推进。
- `blocking_reason_code = FAILURE_DISPOSITION_REQUIRED`，应在 latest failure package 写出 `failure_disposition.yaml`，只能选择 `NO_GO` 或 `CHILD_LINEAGE`。
- `blocking_reason_code = FAILURE_DISPOSITION_RECORDED`，原 lineage 仍不得重新进入普通 review / next-stage，应走 `qros-lineage-change-control` 或 child lineage。
- `blocking_reason_code = STAGE_PROGRAM_MISSING`，应让 author lane 显式补 lineage-local stage program。
- `blocking_reason_code = REVIEW_CONFIRMATION_REQUIRED`，应进入对应 review skill 的显式 review 流程。
- `current_stage` 以 `_next_stage_confirmation_pending` 结尾，应先让用户确认是否进入下一阶段。

不要根据聊天记忆覆盖磁盘状态；磁盘和 runtime 输出是进度查询的事实来源。
