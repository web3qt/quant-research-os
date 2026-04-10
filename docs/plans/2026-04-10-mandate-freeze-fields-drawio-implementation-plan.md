# Mandate Freeze Fields Draw.io Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 新建一张独立的 `draw.io` 字段字典图，用矩阵版式解释 `mandate` 冻结字段。

**Architecture:** 保留现有 `02-mandate.excalidraw` 作为流程图，单独新增一个 `.drawio` 文件承载字段解释。图采用单页 2x2 分类矩阵，每类按 `字段名: 解释` 展示，底部统一补正式产物落点和禁止事项。最后用 XML 校验和最小文档检查收尾。

**Tech Stack:** `draw.io` XML (`mxfile` / `mxGraphModel`), Markdown, `xmllint`, `pytest`

---

### Task 1: Save The Approved Design

**Files:**
- Create: `docs/plans/2026-04-10-mandate-freeze-fields-drawio-design.md`
- Create: `docs/plans/2026-04-10-mandate-freeze-fields-drawio-implementation-plan.md`

**Step 1: Record the approved diagram structure**

- 记录单页矩阵版式、4 个分类块、底部落点区和颜色语义。

**Step 2: Record validation rules**

- 固化 XML 校验、页面数量校验和最小文档检查命令。

### Task 2: Build The Standalone Draw.io Diagram

**Files:**
- Create: `docs/show/csf/image/02-mandate-freeze-fields.drawio`

**Step 1: Create title and framing blocks**

- 写入标题、说明和禁止事项。

**Step 2: Create the four field-category panels**

- `研究路线定义`
- `数据与标签`
- `可调参数边界`
- `执行与治理`

每个面板内使用 `字段名: 解释`，避免流程式箭头。

**Step 3: Add artifact landing summary**

- 在底部统一说明这些字段会落到哪些正式产物。

### Task 3: Validate And Hand Off

**Files:**
- Validate: `docs/show/csf/image/02-mandate-freeze-fields.drawio`

**Step 1: Run XML validation**

Run: `xmllint --noout docs/show/csf/image/02-mandate-freeze-fields.drawio`

Expected: no output, exit code `0`

**Step 2: Confirm page count**

Run: `rg -n "<diagram" docs/show/csf/image/02-mandate-freeze-fields.drawio`

Expected: exactly `1` match

**Step 3: Run minimal docs checks**

Run: `python -m pytest tests/test_project_bootstrap.py tests/test_install_docs.py`

Expected: `4 passed`

