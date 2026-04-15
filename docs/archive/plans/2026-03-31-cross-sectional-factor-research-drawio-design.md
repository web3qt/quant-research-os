# Cross-Sectional Factor Research Draw.io Design

**Goal:** 生成一个可直接在 `draw.io` / `diagrams.net` 打开的多页 `.drawio` 文件，用于表达横截面因子研究的知识框架与执行流程。

**Scope**

- 输出一个多页文件：
  - 第 1 页：思维导图
  - 第 2 页：流程图
- 文件路径：`docs/main-flow-sop/drawio/cross_sectional_factor_research_framework.drawio`
- 图内容基于用户给出的横截面因子研究 10 步流程、artifact 产物链和常见错误。

**Design**

- 第 1 页采用中心节点 + 左右分支的思维导图版式。
- 中心节点为“横截面因子研究框架”。
- 左侧分支承载：
  - 研究对象
  - 研究 mandate
  - universe 与样本时点
  - label 设计
  - 候选因子族
  - 因子预处理
  - 单因子检验
- 右侧分支承载：
  - 因子诊断与归因
  - 去重与家族管理
  - 多因子组合
  - 组合构建与约束
  - 成本 / 容量 / OOS
  - 核心 artifact
  - 常见错误
- 第 2 页采用线性主流程 + 决策节点 + artifact 支撑链。
- 主流程固定为：
  - mandate
  - universe
  - label
  - factor
  - preprocess / neutralize
  - single-factor test
  - diagnostics
  - dedup
  - multi-factor
  - portfolio construction
  - backtest / OOS
  - candidate strategy
- 决策节点固定为：
  - 排序能力是否稳定
  - 是否属于假暴露 / 重复暴露
  - 成本后是否仍可做

**Visual Conventions**

- 沿用仓库现有 `draw.io` 视觉语义：
  - 中心标题：绿色
  - 主流程 / 主分支：紫色，贴合 cross-sectional factor 路线
  - 决策节点：橙色菱形
  - 成功输出 / artifact：绿色
  - 风险 / 常见错误：橙色或红色
  - 说明节点：浅灰
- 输出为标准 `mxfile` / `mxGraphModel` XML，不做压缩，便于后续手工调整。

**Validation**

- XML 合法：可通过 `xmllint --noout` 校验。
- 文件中存在 2 个 `<diagram>` 页面。
- 页面名称分别为：
  - `Mind Map`
  - `Flow`
- Spot check：
  - 第 1 页包含用户要求的研究主线、artifact 与常见错误
  - 第 2 页包含顺序流程、决策节点与 artifact 输出链
