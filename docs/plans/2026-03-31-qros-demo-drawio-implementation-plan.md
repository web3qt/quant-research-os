# QROS Demo Draw.io Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a two-page draw.io asset for presenting QROS, covering both the high-level positioning and the main stage workflow.

**Architecture:** Build a single uncompressed `.drawio` XML file at `docs/show/qros-demo.drawio` so the user can open and edit it directly in diagrams.net. Keep the first page focused on governance and system positioning, and the second page focused on stage progression and route branching, matching the terminology already used in the repo docs.

**Tech Stack:** draw.io XML, Markdown

---

### Task 1: Add Draw.io Asset

**Files:**
- Create: `docs/show/qros-demo.drawio`
- Modify: `docs/show/README.md`

**Step 1: Create the Overview page**

- Add title and core nodes:
  - raw idea
  - idea intake
  - mandate freeze
  - governance layer
  - runtime / skills / session
  - formal research line

**Step 2: Create the Flow page**

- Add:
  - `idea_intake -> mandate_confirmation_pending -> mandate -> research_route`
  - one left-side intake case panel with key questions and the reason for each question
  - one grouped freeze summary near `mandate_confirmation_pending`
  - four small grouped-freeze cards describing what each contract section freezes
  - one vertical fishbone under `research_intent` showing the actual frozen fields in sequence
  - time-series branch
  - CSF branch
  - promotion / shadow / canary
  - governance annotations

**Step 3: Link the new asset from the show README**

- Add one short line near the top pointing to `qros-demo.drawio`.

**Step 4: Validate XML**

Run: `xmllint --noout docs/show/qros-demo.drawio`
Expected: Exit code `0`

### Task 2: Verify Placement

**Files:**
- Verify: `docs/show/qros-demo.drawio`
- Verify: `docs/plans/2026-03-31-qros-demo-drawio-design.md`
- Verify: `docs/plans/2026-03-31-qros-demo-drawio-implementation-plan.md`

**Step 1: Check file existence**

Run: `find docs/show docs/plans -maxdepth 1 | sort | rg 'qros-demo.drawio|qros-demo-drawio'`
Expected: All three drawio-related files are present.

**Step 2: Check page names**

Run: `rg -n '<diagram id=.*name=\"(Overview|Flow)\"' docs/show/qros-demo.drawio`
Expected: The file contains both `Overview` and `Flow`.
