# QROS Demo Show Design

**Goal:** 为混合受众演示准备一份仓库内可直接打开的展示文档，用一张总览图、一张主流程图和一套简明讲稿解释 QROS 的核心思路。

**Audience**

- 老板：关心为什么需要这个系统，以及它如何降低研究失控和口头决策风险。
- 开发：关心 runtime、skills、artifact 和 review gate 如何协作。
- 研究员：关心从想法到正式研究线的阶段推进逻辑。

**Approved Approach**

- 采用 `C. 总览图 + 主流程图`。
- 主展示文档落到 `docs/show/README.md`。
- 文档内包含：
  - 项目一句话定位
  - 总览图
  - 主流程图
  - 面向混合受众的讲解顺序
  - 3 到 5 分钟演示话术

**Design**

1. 第一部分讲“QROS 是什么”。
   - 突出它不是具体策略代码仓，而是研究治理和推进系统。
   - 结构上表现输入、治理机制、执行入口、正式产物和最终结果。

2. 第二部分讲“QROS 怎么运转”。
   - 从 `idea_intake` 到 `holdout_validation` 展示主干。
   - 明确 `mandate` 之后按 `research_route` 分成 time-series 和 cross-sectional factor 两条线。
   - 说明每个阶段都不是口头完成，而是要经过 artifact 和 review closure。

3. 第三部分讲“为什么它对三类人都重要”。
   - 对老板是治理和可审计。
   - 对研究员是研究纪律。
   - 对开发和 agent 是可确定推进和可恢复。

**Format Decision**

- 使用 Markdown + Mermaid。
- 原因：
  - 仓库内可读、可改、可版本管理。
  - 便于直接复制到支持 Mermaid 的文档或演示工具。
  - 比手工生成 draw.io 更快，也更适合这次“先讲清楚项目思路”的目标。

**Output Files**

- `docs/show/README.md`
- `docs/plans/2026-03-31-qros-demo-show-implementation-plan.md`

