# Main Flow SOP Draw.io Design

**Goal:** 为 `docs/main-flow-sop/01` 到 `09` 的主流程 SOP 文档补齐与 `00_mandate_sop_cn.drawio` 同风格的思维导图文件。

**Scope**

- 目标文件为 `01_data_ready_sop_cn.md` 到 `09_canary_production_sop_cn.md`
- 每个 `.md` 生成一个同名 `.drawio`
- 风格统一参考 `docs/main-flow-sop/00_mandate_sop_cn.drawio`

**Design**

- 采用统一版式：中心节点 + 左侧章节树 + 右侧章节树。
- 左侧固定承载“文档目的 / 阶段定位 / 适用范围 / 执行步骤 / Artifact / Formal Gate”。
- 右侧固定承载“Audit-Only / 常见陷阱 / 失败与回退 / 阶段专属要求 / Checklist / 关联文档”。
- 每个一级章节下展开最关键的二级节点；执行步骤完整展开，其他章节只保留可辨识的关键子项。
- 颜色语义沿用参考图：
  - 中心节点：绿色
  - 一级章节：蓝色
  - 执行步骤子节点：黄色
  - Formal Gate 通过项：绿色
  - Formal Gate 失败项：红色
  - 常见陷阱：橙色
  - 其余子节点：浅灰

**Implementation Notes**

- 从 `.md` 自动提取标题、一级章节和对应二级章节。
- 根据文档正文使用的 heading level 自动归一化，兼容 `# / ## / ###` 两套层级风格。
- 输出为标准 `mxfile` / `mxGraphModel` XML，保证 draw.io 可直接打开。

**Validation**

- 文件存在性：`01` 到 `09` 每个 `.md` 都有同名 `.drawio`
- XML 校验：逐个解析生成的 `.drawio`，确认结构合法
- Spot check：抽查至少 2 个文件，确认章节与子节点映射正确
