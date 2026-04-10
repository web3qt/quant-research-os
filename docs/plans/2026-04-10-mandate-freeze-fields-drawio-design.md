# Mandate Freeze Fields Draw.io Design

**Goal:** 新建一张独立的 `draw.io` 图，用“先分类，再逐字段解释”的方式展示 `mandate` 冻结字段，避免和现有 `02-mandate.excalidraw` 流程图混在一起。

**Scope**

- 新建单独图文件：
  - `docs/show/csf/image/02-mandate-freeze-fields.drawio`
- 不替换、不删除现有：
  - `docs/show/csf/image/02-mandate.excalidraw`
- 图内容只回答一件事：
  - `mandate` 阶段到底冻结哪些字段，每个字段是什么意思，为什么要在这一阶段锁住，以及主要落到哪类正式产物

**Design**

- 采用单页 `2x2` 矩阵版式，而不是流程图。
- 顶部为标题和一句话说明：
  - 这张图是字段字典，不是流程推进图
- 中间 4 个分类面板：
  - `研究路线定义`
  - `数据与标签`
  - `可调参数边界`
  - `执行与治理`
- 每个面板中的字段统一用下列格式：
  - `field_name: 一句话解释`
- 底部补一个统一落点说明块：
  - 这些字段最终分散落到 `research_route.yaml`、`time_split.json`、`parameter_grid.yaml`、`run_config.toml`、`mandate.md`、`research_scope.md`、`artifact_catalog.md`、`field_dictionary.md`

**Visual Conventions**

- 沿用仓库现有 `draw.io` 视觉语义：
  - 标题：绿色
  - 路线定义：蓝色
  - 数据与标签：青绿色
  - 参数边界：橙色
  - 执行与治理：紫色
  - 落点说明：绿色
  - 禁止事项：浅红
- 所有字段解释左对齐，避免做复杂箭头，优先强调可读性
- 输出标准 `mxfile` / `mxGraphModel` XML，不压缩，便于后续手工调整

**Validation**

- XML 合法：`xmllint --noout docs/show/csf/image/02-mandate-freeze-fields.drawio`
- 图文件只包含 1 个 `<diagram>`
- 图中必须出现四类分类标题和底部落点说明

