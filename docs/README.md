# QROS 文档导航

这个目录同时承载了用户说明、阶段 SOP、治理文档、评审文档、图示和历史计划。  
如果不先区分“谁是解释层，谁是真值层，谁只是历史记录”，读起来会很乱。

## 先看哪里

普通使用者先看：

- [安装说明](experience/installation.md)
- [Codex 快速开始](experience/quickstart-codex.md)
- [QROS 统一研究会话说明](experience/qros-research-session-usage.md)
- [阶段冻结字段说明](experience/stage-freeze-group-field-guide.md)

需要理解仓库结构时再看：

- [根 README](../README.md)
- [QROS for Codex](README.codex.md)

## 真值与解释层

机器真值文件在 `contracts/`，不是在 `docs/`：

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `contracts/governance/review_governance_policy.yaml`

文档层负责解释这些真值，不应与真值冲突：

- `docs/main-flow-sop/`：主流程和各阶段操作说明
- `docs/fail-sop/`：失败处置与 lineage change control
- `docs/review-sop/`：review / closure 标准与模板
- `docs/governance/`：治理决策流程说明

## 目录分工

- `docs/experience/`
  面向用户和操作者的入口文档。
- `docs/main-flow-sop/`
  面向阶段执行者的正式 SOP。
- `docs/fail-sop/`
  面向失败分流和 rollback / child-lineage 决策。
- `docs/review-sop/`
  面向 reviewer / referee 的关闭标准、清单和模板。
- `docs/governance/`
  面向 review governance 和制度演进。
- `docs/show/`
  图示、演示图和 drawio/excalidraw 资产。
- `docs/plans/`
  历史设计稿、实施计划和工作记录。

## 读文档时的规则

1. 如果是 gate、checklist、policy 真值，优先看 `contracts/`。
2. 如果是“这个阶段该怎么做”，优先看 `docs/main-flow-sop/`。
3. 如果是“失败后怎么办”，优先看 `docs/fail-sop/` 和对应 failure skill。
4. 如果是“这个文档为什么这样设计”，再看 `docs/plans/`。

## 关于 `docs/plans/`

`docs/plans/` 是历史设计与实施记录，不是当前运行时真值。  
其中可能保留当时的旧路径、旧目录名或旧实施假设；引用它时，必须再回到当前的 `contracts/`、`skills/`、`tools/` 和 live docs 核对。
