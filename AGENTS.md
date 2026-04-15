# Quant Research OS 指南

## 目的

这个仓库是 QROS 的流程与治理仓。

它不是某条具体策略研究线的实现仓，也不负责长期保存某条 lineage 的真实研究程序。真实研究程序、阶段执行代码和正式产物应当存在于消费 QROS 的 active research repo 中。

## Codex 应默认遵守的理解

- 把这个仓库视为流程、工具和治理规则仓，而不是策略实现仓。
- 优先修改 `skills/`、runtime helper、SOP 文档、schema 和测试。
- 不要因为目录存在、文件占位或只有合同说明文档，就宣称某个 stage 已完成。
- 必须明确区分以下几类对象：
  - 治理合同
  - 机器可读产物
  - review closure
  - failure handling

## 主流程

正常研究工作的统一入口应当是：

- `qros-research-session`

当前第一阶段主流程覆盖：

- `idea_intake`
- `mandate`
- `data_ready`
- `signal_ready`
- `train_freeze`
- `test_evidence`
- `backtest_ready`
- `holdout_validation`

每个阶段都必须先冻结要求的 grouped contracts，再真实物化 formal artifacts，之后通过 review 才能进入下一阶段。

如果 review verdict 不是正常放行，不要继续普通阶段推进，应当转入 failure handling。

## 仓库边界

- 本仓库负责：workflow 规则、skills、文档、runtime wrapper、测试、artifact expectation。
- 本仓库不负责：用户某条 live lineage 的真实策略实现。
- 对 stage-local executable programs，应当做引用、校验和 provenance 约束；但真实 research repo 仍然是 lineage execution outputs 的事实来源。

## 重要目录

- `skills/`：QROS skill 入口与分阶段行为
- `tools/`：runtime helper、scaffold/build 逻辑
- `scripts/`：命令行 wrapper 与确定性 task runner
- `docs/`：SOP、使用说明、review 文档、操作文档
- `tests/`：workflow 行为和文档回归测试
- `bin/`：稳定的用户入口，例如 `qros-session` 与 `qros-review`
- `harness/`：用于演示和测试分层 `AGENTS.md` 组织方式的示例子树

## Harness 说明

`harness/` 是一个“分层 AGENTS 组织方式”的演示与测试子树，用来说明：

- 根 `AGENTS.md` 应该如何做地图
- 子目录 `AGENTS.md` 应该如何承接更细规则
- 什么时候适合把规则下沉到离内容更近的目录

当前 `harness/` 子树包含：

- `harness/AGENTS.md`：harness 子树自己的根地图
- `harness/docs/AGENTS.md`：文档型子目录规则示例
- `harness/skills/AGENTS.md`：skill / workflow 子目录规则示例
- `harness/tools/AGENTS.md`：runtime / helper 子目录规则示例
- `harness/tests/AGENTS.md`：测试子目录规则示例

当前真实生效的目录级规则入口是：

- `skills/AGENTS.md`：真实 skill / workflow 规则
- `runtime/AGENTS.md`：真实 runtime / helper / scaffold 规则
- `docs/AGENTS.md`：真实文档目录规则
- `tests/AGENTS.md`：真实测试目录规则

### 重要工作方式说明

如果你是在仓库根目录启动 Codex，例如：

```bash
codex --cd /Users/mac08/workspace/web3qt/quant-research-os
```

那么 Codex 默认只会把“项目根到当前工作目录”路径上的 `AGENTS.md` 纳入指令链。  
这意味着：

- 根目录启动时，默认会读到本文件
- 根目录启动时，不会自动把 `harness/AGENTS.md` 和 `harness/*/AGENTS.md` 当作已加载指令

因此，在“总是从仓库根启动”的使用方式下，`harness/` 子树只应被理解为 instruction 分层示例，而不是主仓真实治理面。真实编辑规则应放在目标文件路径祖先链上的 `AGENTS.md` 中，例如根目录、`skills/`、`runtime/`、`docs/`、`tests/`。

### 什么时候进入 harness 子树

当任务本身是下面这些类型时，再进入 `harness/` 或它的更深子目录启动 Codex：

- 设计或评估分层 `AGENTS.md` 地图结构
- 试验文档型子目录如何承接规则
- 试验 skill / tools / tests 目录的专属指令写法
- 验证“从某个子目录启动时，Codex 会实际读取哪些 instruction files”

如果任务和 QROS 主仓的真实 skills、runtime、docs、tests 无关，而是专门讨论 instruction map / harness 设计，优先把它视为 `harness/` 子树任务。

## 命令

默认本地验证命令：

- 全量测试：`python -m pytest`
- 文档 / bootstrap 最小检查：
  `python -m pytest tests/test_project_bootstrap.py tests/test_install_docs.py`
- smoke：
  `python runtime/scripts/run_verification_tier.py --tier smoke`
- full-smoke：
  `python runtime/scripts/run_verification_tier.py --tier full-smoke`

如果修改的是某个具体 stage runtime，先跑最小相关测试，再按需要扩大验证范围。

## 测试分层要求

- 每个新需求默认都必须先定义并实际执行验证，不允许只写“已测试”而不给命令。
- 最低要求是：**focused tests + smoke**。
- 只要改动触及下列任一项，**full-smoke 也必须跑**：
- `qros-research-session` stage flow / gate semantics
- review / display / next-stage orchestration
- route split / CSF routing
- anti-drift snapshots 或 canonical session stage naming
- stage-display supported stage contract
- lineage-local stage-program auto-author seams
- `smoke` / `full-smoke` 的当前定义与命令以
  `docs/guides/qros-verification-tiers.md` 和
  `runtime/scripts/run_verification_tier.py` 为准。
- 如果任务是纯文档 / 纯图示且明确不改变 runtime / workflow contract，至少运行文档 / bootstrap 最小检查，并在最终报告里明确说明为什么没有跑 smoke / full-smoke。

## 文档规则

- 用户文档必须与当前 runtime 行为和测试夹具保持一致。
- 解释 freeze groups 时，优先以用户在磁盘上真实会看到的 runtime-facing field shape 为准。
- 如果文档在解释字段，优先做字段一一对应，而不是只写 stage-level 叙述。
- 如果新增或重命名了文档里出现的 artifact 或字段，必须同步更新最近的文档和锁定其存在/表述的测试。
- 如果正式 schema、枚举集合、字段语义或 stage gate 含义发生变化，必须同步清理 active skills、SOP、review checklist、`docs/show/` 图示和当前仍被引用的说明文档中的旧口径；不要保留与当前合同冲突的示例或“历史上只支持旧值”的表述。

## 编辑规则

- 保持 diff 小、可审查、可回退。
- 复用仓库现有术语，不要为同一个 stage、artifact 或 contract 再发明第二套命名。
- 没有明确理由不要新增依赖。
- 默认使用中文注释；尤其是 `tools/`、`scripts/`、`skills/` 里涉及各研究阶段实现、runtime gate、review/failure routing 的代码，新增注释应优先写成清晰、简短、面向维护者的中文说明。
- 当修改影响用户工作流、artifact contract 或 stage 语义时，优先同时更新测试和文档。

## 完成标准

在宣称任务完成之前，至少确认：

- 相关验证命令已经实际运行。
- 文档表述与当前 runtime 行为一致。
- 最终报告里明确写出这次运行过的 focused tests / smoke / full-smoke。
- 如果仍有缺口，要明确写出，尤其是某条 route 或某个 stage 只做了部分覆盖时。

## 子目录覆盖

如果后续某个子目录需要更具体的规则，可以在该子目录再放一个 `AGENTS.md`。

更深层的 `AGENTS.md` 应只对该子树做收窄或专门化，不要无必要地重写整仓规则。
