# Cross-Sectional Factor Research Draw.io Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 生成一个多页 `draw.io` 文件，分别展示横截面因子研究的思维导图和执行流程图。

**Architecture:** 直接手写标准 `mxfile` XML，并沿用仓库既有 `draw.io` 样式。第 1 页使用思维导图布局，第 2 页使用流程图布局，并在流程图中补入决策节点与 artifact 输出链。最后用 XML 校验确认文件结构合法。

**Tech Stack:** `draw.io` XML (`mxfile` / `mxGraphModel`), Markdown, `xmllint`

---

### Task 1: Write Design And Plan Artifacts

**Files:**
- Create: `docs/plans/2026-03-31-cross-sectional-factor-research-drawio-design.md`
- Create: `docs/plans/2026-03-31-cross-sectional-factor-research-drawio-implementation-plan.md`

**Step 1: Capture the approved design**

- 记录页面结构、节点分组、颜色语义和验证标准。

**Step 2: Save implementation steps**

- 将图文件生成、校验和交付路径固化成实现计划。

### Task 2: Build The Multi-Page Draw.io File

**Files:**
- Create: `docs/main-flow-sop/drawio/cross_sectional_factor_research_framework.drawio`

**Step 1: Build page 1**

- 生成 “Mind Map” 页面。
- 根节点使用绿色。
- 主分支使用紫色。
- `artifact` 与 `常见错误` 使用独立色块突出。

**Step 2: Build page 2**

- 生成 “Flow” 页面。
- 用正交流程线串联 10 步主线。
- 插入 3 个关键决策节点。
- 添加支持说明块与 artifact 输出链。

### Task 3: Validate And Hand Off

**Files:**
- Validate: `docs/main-flow-sop/drawio/cross_sectional_factor_research_framework.drawio`

**Step 1: Run XML validation**

Run: `xmllint --noout docs/main-flow-sop/drawio/cross_sectional_factor_research_framework.drawio`

Expected: no output, exit code `0`

**Step 2: Confirm page count**

Run: `rg -n "<diagram" docs/main-flow-sop/drawio/cross_sectional_factor_research_framework.drawio`

Expected: exactly `2` matches

**Step 3: Inspect git diff**

Run: `git diff -- docs/plans/2026-03-31-cross-sectional-factor-research-drawio-design.md docs/plans/2026-03-31-cross-sectional-factor-research-drawio-implementation-plan.md docs/main-flow-sop/drawio/cross_sectional_factor_research_framework.drawio`

Expected: only the intended new files appear
