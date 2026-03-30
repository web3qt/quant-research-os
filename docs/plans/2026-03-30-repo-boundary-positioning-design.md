# Repo Boundary Positioning Design

**Date:** 2026-03-30  
**Status:** Approved for design handoff  
**Scope:** 为 `README.md` 与 `docs/main-flow-sop/research_workflow_sop.md` 增加 repo 级职责边界声明，明确 `quant-research-os` 是指导 agent 辅助策略员开展正式研究的治理框架，而不是具体策略业务代码仓

## Goal

把仓库定位说清楚，避免后续再次把 `quant-research-os` 误解为：

- 研究员手写因子、回测、验证代码的主仓
- 具体研究线真实业务代码的沉淀仓
- 需要内置所有 IC、回测或因子计算实现的系统

本次设计要明确：

- 这个 repo 的职责是什么
- 这个 repo 明确不负责什么
- 真实研究代码应该在哪里生成
- 这个边界应该在什么文档层级被反复强调

## Decision

采用 `README + workflow` 双点声明方案，不新增单独的“仓库定位说明”文档。

原因：

- `README.md` 是新读者第一次进入仓库时最先看到的地方，适合承载 repo 级身份声明
- `research_workflow_sop.md` 是内部流程解释层，适合承载制度化边界说明
- 新增独立文档会增加维护成本，并且定位信息反而更容易漂移

## Boundary Statement

本次设计要表达的核心边界有四点：

1. `quant-research-os` 是指导 agent 辅助策略员开展正式量化研究的治理框架。
2. 本仓库负责提供 `workflow / gates / skills / runtime / lineage / review discipline`。
3. 本仓库不负责沉淀某条具体策略线的真实业务研究代码，也不要求研究员在这里手写因子、回测或验证实现。
4. 具体研究代码应由 agent 在当前研究仓或当前研究上下文中生成，并按 QROS 合同产出正式 artifact，供策略员审查、确认和推进。

## Placement Strategy

### `README.md`

放在简介段落之后，作为 repo 级职责边界声明。

写法要求：

- 足够短，第一次进入仓库即可读懂
- 明确回答“这个 repo 是什么”和“这个 repo 不是什么”
- 说明真实研究代码应由 agent 在具体研究上下文中生成

### `docs/main-flow-sop/research_workflow_sop.md`

放在 `0. 文档定位与优先级` 后面，新增简短的 repo boundary 段落。

写法要求：

- 不重复 README 的全部文字
- 更制度化地说明：QROS 约束的是正式研究流程与 artifact 治理
- 明确：具体因子、检验、回测与验证实现由 agent 在研究上下文中生成
- 保留现有纪律：空目录、占位文件和只有语义说明的文档不能被当作阶段完成

## Proposed Wording

### `README.md`

建议文案：

> QROS 是一个指导 agent 辅助策略员开展正式量化研究的治理框架。  
> 本仓库提供研究流程、阶段门禁、skills、runtime、lineage 与 review discipline，用来约束研究如何被定义、冻结、审查和推进。  
> 本仓库不负责沉淀某条具体策略线的真实业务研究代码，也不要求研究员在这里手写因子、回测或验证实现。  
> 具体研究代码应由 agent 在当前研究仓或当前研究上下文中生成，并按 QROS 合同产出正式 artifact，供策略员审查、确认和推进。

### `docs/main-flow-sop/research_workflow_sop.md`

建议文案：

> QROS 约束的是正式研究流程与 artifact 治理，而不是把本仓库当作具体策略研究代码的承载体。  
> 对于某条实际研究线，agent 应在当前研究仓或当前研究上下文中生成因子、检验、回测与验证实现；本规范只要求这些实现形成可审查、可复现、可追溯的正式产物，并通过对应 gate。  
> 因为空目录、占位文件或只有语义说明的文档，都不能被当作阶段完成。

## Non-Goals

本次设计不做以下事情：

- 不修改 runtime、gate truth 或 skill 行为
- 不新增 repo 级“研究代码执行引擎”职责
- 不把 repo 定义成研究员手写策略代码的工作区
- 不新增第三份定位文档

## Acceptance Criteria

设计落地后，应满足以下标准：

- 新读者在 `README.md` 第一屏附近即可理解 repo 职责边界
- 已进入流程的使用者在 `research_workflow_sop.md` 中再次看到同一边界的制度化表达
- 两处文案不互相矛盾，且不与现有 `route / stage / artifact` 语义冲突
- 文案不会把 QROS 误写成业务研究代码仓

## Validation

本次修改只需要最小验证：

- 运行 `git diff --check`
- 人工确认 `README.md` 的声明足够前置
- 人工确认 `research_workflow_sop.md` 的边界说明不与现有流程语义冲突

不需要新增测试，因为本次只调整文档定位，不修改 runtime、gates 或研究流程逻辑。
