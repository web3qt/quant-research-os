# Stage Artifact Map Draw.io Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a repo-local draw.io artifact map under `docs/show/` that explains, for each first-wave stage, what to read first, which files are generated, and what those files are for.

**Architecture:** Create a single `draw.io` file with two pages: one for common + mainline stages and one for the CSF branch. Reuse current repo terminology and current on-disk artifact contract, then add a short README entry pointing users to the new file.

**Tech Stack:** draw.io XML, Markdown docs

---

### Task 1: Add The Design Artifact

**Files:**
- Create: `docs/plans/2026-04-11-stage-artifact-map-drawio-design.md`
- Create: `docs/plans/2026-04-11-stage-artifact-map-drawio-implementation-plan.md`

**Step 1: Save the design**

Write the approved scope, page split, stage card structure, and README integration.

**Step 2: Save the implementation plan**

Write this plan so later edits stay aligned with the approved scope.

### Task 2: Create The Draw.io File

**Files:**
- Create: `docs/show/qros-stage-artifact-map.drawio`

**Step 1: Add page `Mainline`**

Include:

- common directory layout box
- reading order box
- cards for `idea_intake`, `mandate`, `data_ready`, `signal_ready`, `train_freeze`, `test_evidence`, `backtest_ready`, `holdout_validation`

**Step 2: Add page `CSF`**

Include:

- shared-prefix note: `idea_intake` and `mandate` are common
- cards for `csf_data_ready`, `csf_signal_ready`, `csf_train_freeze`, `csf_test_evidence`, `csf_backtest_ready`, `csf_holdout_validation`

**Step 3: Keep file names and purposes aligned with runtime**

Use only current-stage formal outputs and the current `author/formal` / `review/closure` contract.

### Task 3: Add README Entry

**Files:**
- Modify: `docs/show/README.md`

**Step 1: Add `Stage Artifact Map` section**

Document:

- file path: `docs/show/qros-stage-artifact-map.drawio`
- page meanings
- suggested reading order

### Task 4: Verify Docs Baseline

**Files:**
- Test: `tests/test_project_bootstrap.py`
- Test: `tests/test_install_docs.py`

**Step 1: Run minimal checks**

Run:

```bash
python -m pytest tests/test_project_bootstrap.py tests/test_install_docs.py -q
```

Expected: pass.

### Task 5: Review Diff And Report

**Files:**
- Modify: only the files above

**Step 1: Inspect diff**

Run:

```bash
git status --short
git diff -- docs/show docs/plans
```

**Step 2: Summarize**

Report:

- draw.io file added
- pages added
- README entry added
- verification run
