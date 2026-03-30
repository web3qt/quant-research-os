# Open Risks Stage-Aware Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `open_risks` in research session status summaries depend on the current stage so post-mandate stages no longer display stale intake rollback metadata.

**Architecture:** Keep intake-stage behavior unchanged, but pass `current_stage` into the session summary helper and suppress intake-derived `open_risks` for mandate and downstream stages when no stage-specific risk source exists. Cover both runtime objects and CLI output with focused regression tests.

**Tech Stack:** Python runtime orchestration, pytest regression tests

---

### Task 1: Save The Approved Design And Implementation Plan

**Files:**
- Create: `docs/plans/2026-03-30-open-risks-stage-aware-design.md`
- Create: `docs/plans/2026-03-30-open-risks-stage-aware-implementation-plan.md`

**Step 1: Write the design doc**

Capture the approved stage-aware `open_risks` rule, rejected alternatives, implementation shape, non-goals, and acceptance criteria.

**Step 2: Write the implementation plan**

Capture the exact runtime and test file edits plus the focused verification commands.

**Step 3: Commit the planning docs**

Run:

```bash
git add docs/plans/2026-03-30-open-risks-stage-aware-design.md docs/plans/2026-03-30-open-risks-stage-aware-implementation-plan.md
git commit -m "docs: add open risks stage-aware plan"
```

Expected: only the two planning docs are committed.

### Task 2: Make Session Transition Summary Stage-Aware

**Files:**
- Modify: `tools/research_session.py`

**Step 1: Update the helper signature**

Change `session_transition_summary(lineage_root)` to accept `current_stage`.

**Step 2: Preserve intake semantics**

For:

- `idea_intake`
- `idea_intake_confirmation_pending`

continue returning intake-derived `required_reframe_actions` and `rollback_target`.

**Step 3: Suppress stale intake risks after mandate**

For all later stages, if no stage-local risk source exists, return `[]` for `open_risks`.

**Step 4: Update the runtime call site**

Pass `current_stage` from `run_research_session()` into `session_transition_summary()`.

### Task 3: Add Focused Regression Tests

**Files:**
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Add runtime regression coverage**

Create or update a test that builds a lineage in `csf_data_ready_confirmation_pending` and asserts:

```python
assert status.open_risks == []
```

**Step 2: Add CLI regression coverage**

Create or update a script test for the same scenario and assert stdout does not contain:

```text
Open risks:
rollback_target remains 00_idea_intake
```

**Step 3: Keep intake behavior covered**

Ensure an intake-stage test still demonstrates that intake `required_reframe_actions` or fallback rollback messaging can appear there.

### Task 4: Run Focused Verification

**Files:**
- Modify: `tools/research_session.py`
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Run the targeted tests**

Run:

```bash
python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -q
```

Expected: all targeted tests pass.

**Step 2: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected: no formatting or whitespace errors.

### Task 5: Commit The Fix

**Files:**
- Modify: `tools/research_session.py`
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Commit only the runtime and test fix**

Run:

```bash
git add tools/research_session.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py
git commit -m "fix: make open risks stage aware"
```

Expected: the commit contains only the status-summary fix and its regression tests.
