# QROS 文档导航

这个目录只应该被理解成**解释层**。  
也就是：给人读的说明、SOP、图示、治理说明和历史计划。

如果不先区分“谁是解释层，谁是真值层，谁只是历史记录”，读起来会很乱。

## 先看哪里

普通使用者先看：

- [安装说明](guides/installation.md)
- [Codex 快速开始](guides/quickstart-codex.md)
- [QROS 统一研究会话说明](guides/qros-research-session-usage.md)
- [阶段冻结字段说明](guides/stage-freeze-group-field-guide.md)

需要理解仓库结构时再看：

- [根 README](../README.md)
- [QROS for Codex](README.codex.md)
- [根 AGENTS](../AGENTS.md)

## 真值与解释层

机器真值文件在 `contracts/`，不是在 `docs/`：

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `contracts/governance/review_governance_policy.yaml`

文档层负责解释这些真值，不应与真值冲突：

- `docs/sop/main-flow/`：主流程和各阶段操作说明
- `docs/sop/failures/`：失败处置与 lineage change control
- `docs/sop/review/`：review / closure 标准与模板
- `docs/governance/`：治理决策流程说明

## 当前整个仓库的层次

如果你是第一次维护这个项目，可以先把根目录理解成下面几层：

- `contracts/`：代码直接读取的真值层
- `skills/`：agent 行为层
- `runtime/bin/ + runtime/scripts/ + runtime/tools/ + runtime/hooks/`：运行时实现层
- `templates/`：生成模板层
- `docs/`：解释层
- `tests/`：验证层
- `harness/`：分层 `AGENTS.md` 组织方式的示例子树，不是主仓真实治理面

也就是说，`docs/` 不是整个项目的总入口树，只是其中的人类解释层。

## 目录分工

- `docs/guides/`
  面向用户和操作者的入口文档。
- `docs/sop/main-flow/`
  面向阶段执行者的正式 SOP。
- `docs/sop/failures/`
  面向失败分流和 rollback / child-lineage 决策。
- `docs/sop/review/`
  面向 reviewer / referee 的关闭标准、清单和模板。
- `docs/governance/`
  面向 review governance 和制度演进。
- `docs/visuals/`
  图示、演示图和 drawio/excalidraw 资产。
- `docs/archive/plans/`
  历史设计稿、实施计划和工作记录。

## `harness/` 不是 docs 的一部分

`harness/` 虽然也有 `docs/`、`skills/`、`runtime/tools/`、`tests/` 子目录，但它不属于主产品文档树。

它服务的是根 `AGENTS.md` 的 instruction 组织与验证，主要用途是：

- 演示分层 `AGENTS.md` 地图
- 验证不同启动目录下的 instruction 读取边界
- 给 Codex 的 instruction / orchestration 机制提供支撑性样例

主仓真实目录级规则入口在：

- `../contracts/AGENTS.md`
- `../skills/AGENTS.md`
- `../runtime/AGENTS.md`
- `AGENTS.md`
- `../tests/AGENTS.md`

所以：

- 普通使用者先不用进 `harness/`
- 只有当你在研究“Codex 如何读 AGENTS.md、如何做目录级 instruction 分层”时，才需要看它

## 读文档时的规则

1. 如果是 gate、checklist、policy 真值，优先看 `contracts/`。
2. 如果是“这个阶段该怎么做”，优先看 `docs/sop/main-flow/`。
3. 如果是“失败后怎么办”，优先看 `docs/sop/failures/` 和对应 failure skill。
4. 如果是“这个文档为什么这样设计”，再看 `docs/archive/plans/`。

## 关于 `docs/archive/plans/`

`docs/archive/plans/` 是历史设计与实施记录，不是当前运行时真值。  
其中可能保留当时的旧路径、旧目录名或旧实施假设；引用它时，必须再回到当前的 `contracts/`、`skills/`、`runtime/tools/` 和 live docs 核对。
