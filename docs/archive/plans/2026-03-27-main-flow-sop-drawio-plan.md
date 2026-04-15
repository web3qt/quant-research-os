# Main Flow SOP Draw.io Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `docs/main-flow-sop/01` 到 `06` 的 SOP 文档生成统一风格的 `.drawio` 思维导图。

**Architecture:** 使用一个一次性生成脚本读取 Markdown heading 结构，按统一布局规则输出 draw.io XML。生成后通过 XML 解析和文件存在性检查做最小验证，避免逐文件手工维护大段 XML。

**Tech Stack:** Python 3, Markdown heading parsing, draw.io `mxfile` XML

---

### Task 1: Freeze source and output mapping

**Files:**
- Read: `docs/main-flow-sop/01_data_ready_sop_cn.md`
- Read: `docs/main-flow-sop/02_signal_ready_sop_cn.md`
- Read: `docs/main-flow-sop/03_train_calibration_sop_cn.md`
- Read: `docs/main-flow-sop/04_test_evidence_sop_cn.md`
- Read: `docs/main-flow-sop/05_backtest_ready_sop_cn.md`
- Read: `docs/main-flow-sop/06_holdout_validation_sop_cn.md`
- Read: `docs/main-flow-sop/00_mandate_sop_cn.drawio`

**Step 1:** Confirm target markdown files and existing reference draw.io.

**Step 2:** Confirm naming rule: each markdown file maps to same-path `.drawio`.

### Task 2: Generate draw.io files

**Files:**
- Create: `docs/main-flow-sop/01_data_ready_sop_cn.drawio`
- Create: `docs/main-flow-sop/02_signal_ready_sop_cn.drawio`
- Create: `docs/main-flow-sop/03_train_calibration_sop_cn.drawio`
- Create: `docs/main-flow-sop/04_test_evidence_sop_cn.drawio`
- Create: `docs/main-flow-sop/05_backtest_ready_sop_cn.drawio`
- Create: `docs/main-flow-sop/06_holdout_validation_sop_cn.drawio`

**Step 1:** Parse title and normalized section tree from each markdown file.

**Step 2:** Assign fixed left/right top-level buckets and child node colors.

**Step 3:** Emit valid `mxfile` XML for each target file.

### Task 3: Verify generated artifacts

**Files:**
- Test: `docs/main-flow-sop/*.drawio`

**Step 1:** Parse each generated XML file to verify structural validity.

**Step 2:** Check each target markdown file has a corresponding draw.io file.

**Step 3:** Spot-check generated node labels against source headings.

### Task 4: Summarize and hand off

**Files:**
- Report: `docs/plans/2026-03-27-main-flow-sop-drawio-design.md`
- Report: `docs/plans/2026-03-27-main-flow-sop-drawio-plan.md`

**Step 1:** Summarize what was created and what was validated.

**Step 2:** Call out any residual maintenance risks, mainly heading drift when markdown changes later.
