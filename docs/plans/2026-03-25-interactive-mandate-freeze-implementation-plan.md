# Interactive Mandate Freeze Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert mandate generation into a grouped interactive freeze flow so mandate artifacts are only written from confirmed freeze content.

**Architecture:** Add a durable `mandate_freeze_draft.yaml` artifact to `00_idea_intake/`, make mandate generation depend on fully confirmed freeze groups plus final approval, and update the session skill/docs to drive grouped interaction rather than silent artifact generation.

**Tech Stack:** Python, pytest, Markdown docs, YAML artifacts

---

### Task 1: Add failing tests for the freeze draft scaffold and mandate build requirements

**Files:**
- Modify: `tests/test_idea_runtime_scripts.py`

**Step 1: Write the failing test**

Add tests that expect:

- `scaffold_idea_intake.py` creates `mandate_freeze_draft.yaml`
- `build_mandate_from_intake.py` fails when the freeze draft is missing or has unconfirmed groups
- successful mandate build reads data from the confirmed freeze draft

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_idea_runtime_scripts.py -v`
Expected: failing scaffold/build assertions for the new draft requirement

**Step 3: Write minimal implementation**

Add the draft scaffold and mandate build validation.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_idea_runtime_scripts.py -v`
Expected: PASS

### Task 2: Add failing runtime tests for grouped mandate confirmation progress

**Files:**
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Write the failing test**

Add tests that expect:

- `mandate_confirmation_pending` reports the next freeze group when the draft is incomplete
- explicit approval alone is not enough to enter `mandate_author` while groups remain unconfirmed
- a fully confirmed draft plus approval permits mandate generation

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -v`
Expected: failures around pending-stage next actions or premature mandate generation

**Step 3: Write minimal implementation**

Add helpers that inspect the freeze draft and derive the next required group.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -v`
Expected: PASS

### Task 3: Update mandate outputs to freeze grouped content

**Files:**
- Modify: `tools/idea_runtime.py`

**Step 1: Write the failing test**

Extend existing build tests to expect:

- `mandate.md` includes research-intent content
- `research_scope.md` includes scope and data contract content
- `run_config.toml` and `field_dictionary.md` reflect frozen execution/data inputs

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_idea_runtime_scripts.py -v`
Expected: content assertion failures

**Step 3: Write minimal implementation**

Generate mandate outputs from the confirmed draft rather than loosely from scope defaults.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_idea_runtime_scripts.py -v`
Expected: PASS

### Task 4: Update skill/docs contract for grouped interactive mandate freezing

**Files:**
- Modify: `.agents/skills/qros-research-session/SKILL.md`
- Modify: `.agents/skills/qros-mandate-author/SKILL.md`
- Modify: `docs/experience/qros-research-session-usage.md`
- Modify: `docs/experience/idea-intake-to-mandate-flow.md`
- Modify: `docs/experience/quickstart-codex.md`
- Modify: `tests/test_research_session_assets.py`

**Step 1: Write the failing test**

Adjust the asset tests to expect:

- grouped mandate freeze semantics
- the four group names
- explicit group-level echo/confirm behavior before final mandate approval

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_research_session_assets.py -v`
Expected: failures because docs still describe a thinner confirmation flow

**Step 3: Write minimal implementation**

Update the docs and skill contract so they describe grouped interactive freezing.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_research_session_assets.py -v`
Expected: PASS

### Task 5: Run final focused verification

**Files:**
- Verify: `tests/test_run_research_session_script.py`
- Verify: `tests/test_idea_runtime_scripts.py`
- Verify: `tests/test_research_session_runtime.py`
- Verify: `tests/test_research_session_assets.py`

**Step 1: Run focused verification**

Run: `python -m pytest tests/test_run_research_session_script.py tests/test_idea_runtime_scripts.py tests/test_research_session_runtime.py tests/test_research_session_assets.py -v`
Expected: all targeted tests pass

**Step 2: Re-check behavior against the approved design**

Confirm:

- mandate content is grouped and durable on disk before generation
- approval alone does not bypass grouped freeze completion
- docs and skill text match the new interaction contract

Execution will continue in this session immediately after the plan is written.
