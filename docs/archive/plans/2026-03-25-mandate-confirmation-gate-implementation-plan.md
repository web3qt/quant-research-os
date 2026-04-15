# Mandate Confirmation Gate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a hard confirmation gate between intake admission and mandate generation so `GO_TO_MANDATE` no longer auto-builds `01_mandate/`.

**Architecture:** Extend the session runtime with a new `mandate_confirmation_pending` stage plus a durable approval artifact in `00_idea_intake/`. Keep the change narrow: tests first, then runtime detection, explicit CLI approval, and finally documentation and skill contract updates.

**Tech Stack:** Python, pytest, Markdown docs, YAML artifacts

---

### Task 1: Add failing runtime tests for the pending-confirmation stage

**Files:**
- Modify: `tests/test_research_session_runtime.py`

**Step 1: Write the failing test**

Add tests that expect:

- `detect_session_stage()` returns `mandate_confirmation_pending` when `idea_gate_decision.yaml.verdict == GO_TO_MANDATE` and no approval artifact exists
- `detect_session_stage()` returns `mandate_author` only when approval artifact records `CONFIRM_MANDATE`

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_research_session_runtime.py -v`
Expected: failing stage assertions for the new confirmation state

**Step 3: Write minimal implementation**

Update the runtime stage logic to recognize the approval artifact and return the new state.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_research_session_runtime.py -v`
Expected: PASS

### Task 2: Add failing session-script tests for non-automatic mandate generation

**Files:**
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Write the failing test**

Add tests that expect:

- an admitted lineage without approval remains at `mandate_confirmation_pending`
- `01_mandate/mandate.md` is not created in that case
- an explicit approval command allows a later session run to enter `mandate_review`

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_run_research_session_script.py -v`
Expected: failures because the current script still auto-builds mandate artifacts

**Step 3: Write minimal implementation**

Add an explicit CLI approval path and prevent mandate generation until approval exists.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_run_research_session_script.py -v`
Expected: PASS

### Task 3: Implement approval artifact helpers and session summary changes

**Files:**
- Modify: `tools/research_session.py`

**Step 1: Write the failing test**

Extend tests to expect:

- stable approval artifact path handling
- `gate_status` and `next_action` reflect pending confirmation
- approval summary fields are surfaced

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_research_session_runtime.py -v`
Expected: missing helper or summary assertions

**Step 3: Write minimal implementation**

Add helpers for:

- reading gate verdict
- reading approval decision
- writing `mandate_transition_approval.yaml`
- deriving pending-confirmation `gate_status` and `next_action`

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_research_session_runtime.py -v`
Expected: PASS

### Task 4: Update docs and skill assets to describe the new gate

**Files:**
- Modify: `docs/experience/qros-research-session-usage.md`
- Modify: `docs/experience/idea-intake-to-mandate-flow.md`
- Modify: `.agents/skills/qros-research-session/SKILL.md`
- Modify: `tests/test_research_session_assets.py`

**Step 1: Write the failing test**

Adjust asset tests to expect explicit confirmation wording and the new pending stage.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_research_session_assets.py -v`
Expected: failures because docs and skill text still say mandate auto-builds

**Step 3: Write minimal implementation**

Update the docs and skill contract so they explain:

- the new `mandate_confirmation_pending` stage
- the explicit command requirement
- that `GO_TO_MANDATE` no longer auto-builds mandate

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_research_session_assets.py -v`
Expected: PASS

### Task 5: Run final verification

**Files:**
- Verify: `tests/test_research_session_runtime.py`
- Verify: `tests/test_run_research_session_script.py`
- Verify: `tests/test_research_session_assets.py`

**Step 1: Run focused verification**

Run: `python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py tests/test_research_session_assets.py -v`
Expected: all selected tests pass

**Step 2: Review behavior against requirements**

Confirm:

- admitted intake stops at `mandate_confirmation_pending`
- mandate build requires explicit approval
- docs and skill text match runtime behavior

User requested in-session implementation immediately after planning, so execution should continue directly in this session.
