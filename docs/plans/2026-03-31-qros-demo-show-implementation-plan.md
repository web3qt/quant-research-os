# QROS Demo Show Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a repo-local demo document that explains QROS to mixed audiences with one overview diagram, one workflow diagram, and concise speaker notes.

**Architecture:** Put a single entry document at `docs/show/README.md` so the user can present directly from one file. Use Mermaid diagrams for the visual layer and short Chinese narrative sections for the speaking layer, while preserving the repo's existing terminology for stages, routes, artifacts, and review gates.

**Tech Stack:** Markdown, Mermaid

---

### Task 1: Add The Main Show Document

**Files:**
- Create: `docs/show/README.md`

**Step 1: Draft the presentation structure**

- Add a title, one-sentence positioning, and a recommended speaking order.
- Keep the content in Chinese and optimized for mixed audiences.

**Step 2: Add the overview diagram**

- Build one Mermaid diagram that shows:
  - raw idea input
  - mandate freeze
  - stage gates
  - runtime and skills
  - formal artifacts
  - reproducible research output

**Step 3: Add the main workflow diagram**

- Build one Mermaid diagram that shows:
  - `idea_intake -> mandate`
  - route split into time-series and cross-sectional factor
  - promotion, shadow, and canary
  - review closure as a repeated governance action

**Step 4: Add speaker notes**

- Include:
  - a 30-second version
  - a 3 to 5 minute version
  - audience-specific value summary

**Step 5: Verify readability**

Run: `sed -n '1,260p' docs/show/README.md`
Expected: The document includes the overview diagram, workflow diagram, and speaker notes in one file.

### Task 2: Verify Repo Placement

**Files:**
- Verify: `docs/show/README.md`
- Verify: `docs/plans/2026-03-31-qros-demo-show-design.md`
- Verify: `docs/plans/2026-03-31-qros-demo-show-implementation-plan.md`

**Step 1: Check file existence**

Run: `find docs/show docs/plans -maxdepth 1 | sort`
Expected: The show document and both plan documents exist in the expected locations.

**Step 2: Spot check the content**

Run: `rg -n "Mermaid|3 到 5 分钟|idea_intake|cross_sectional_factor" docs/show/README.md`
Expected: The main presentation keywords appear in the show document.

