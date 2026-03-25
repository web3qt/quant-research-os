# Data Ready Orchestration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend `qros-research-session` so the first-wave flow continues from mandate review into interactive `data_ready` freezing, formal `02_data_ready` artifact generation, and `data_ready review`.

**Architecture:** Reuse the existing mandate pattern. Add a dedicated `tools/data_ready_runtime.py` for stage scaffolding and formal outputs, then extend `tools/research_session.py` to detect and drive new `data_ready` states. Keep review closure on the existing stage review engine and add a new author skill plus doc updates.

**Tech Stack:** Python, YAML, markdown docs, pytest

---

### Task 1: Document The Design On Disk

**Files:**
- Create: `docs/plans/2026-03-25-data-ready-orchestration-design.md`
- Create: `docs/plans/2026-03-25-data-ready-orchestration-implementation-plan.md`

**Step 1: Write the design doc**

Save the approved `data_ready` product semantics, freeze groups, runtime states, outputs, and guardrails.

**Step 2: Write the implementation plan**

Save this task-by-task plan so execution stays aligned with the approved design.

### Task 2: Add Failing Runtime Tests

**Files:**
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Write failing tests**

Add tests for:

- `mandate_review_complete -> data_ready_confirmation_pending`
- next `data_ready` freeze group reporting
- explicit `--confirm-data-ready` approval before build
- `data_ready_review` and `data_ready_review_complete` stage detection

**Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -v
```

Expected: failures because `data_ready` stages and CLI flag do not exist yet.

### Task 3: Add Failing Asset And Doc Tests

**Files:**
- Modify: `tests/test_research_session_assets.py`
- Modify: `tests/test_idea_runtime_scripts.py`

**Step 1: Write failing tests**

Add assertions that:

- `qros-data-ready-author` exists
- `qros-research-session` mentions `data_ready_confirmation_pending`
- usage docs describe `data_ready`
- a new build script can scaffold formal `02_data_ready` outputs from confirmed draft inputs

**Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_research_session_assets.py tests/test_idea_runtime_scripts.py -v
```

Expected: failures because the skill and runtime script do not exist yet.

### Task 4: Implement Data Ready Runtime

**Files:**
- Create: `tools/data_ready_runtime.py`
- Create: `scripts/build_data_ready_from_mandate.py`

**Step 1: Write minimal implementation**

Implement:

- `DATA_READY_FREEZE_DRAFT_FILE`
- `DATA_READY_FREEZE_GROUP_ORDER`
- blank freeze draft scaffold
- `scaffold_data_ready()`
- `build_data_ready_from_mandate()`
- required output generation for `02_data_ready/*`

The build should consume only confirmed freeze groups and already frozen mandate outputs.

**Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_idea_runtime_scripts.py -v
```

Expected: new data_ready runtime tests pass.

### Task 5: Extend Research Session State Machine

**Files:**
- Modify: `tools/research_session.py`
- Modify: `scripts/run_research_session.py`

**Step 1: Write minimal implementation**

Add:

- `data_ready_confirmation_pending`
- `data_ready_author`
- `data_ready_review`
- `data_ready_review_complete`
- data_ready approval artifact handling
- `--confirm-data-ready`
- next-group reporting for `data_ready`
- automatic `02_data_ready` build only after explicit approval

**Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -v
```

Expected: data_ready state machine tests pass.

### Task 6: Update Skills And Experience Docs

**Files:**
- Create: `.agents/skills/qros-data-ready-author/SKILL.md`
- Create: `.agents/skills/qros-data-ready-author/agents/openai.yaml`
- Modify: `.agents/skills/qros-research-session/SKILL.md`
- Modify: `README.md`
- Modify: `README_EN.md`
- Modify: `docs/experience/qros-research-session-usage.md`
- Modify: `docs/experience/quickstart-codex.md`

**Step 1: Write minimal doc and skill updates**

Make the first-wave story consistent with the new `data_ready` boundary and grouped freeze flow.

**Step 2: Run asset tests**

Run:

```bash
python -m pytest tests/test_research_session_assets.py -v
```

Expected: asset and doc coverage tests pass.

### Task 7: Run Full Focused Verification

**Files:**
- Test: `tests/test_idea_runtime_scripts.py`
- Test: `tests/test_research_session_runtime.py`
- Test: `tests/test_run_research_session_script.py`
- Test: `tests/test_research_session_assets.py`

**Step 1: Run verification**

Run:

```bash
python -m pytest tests/test_idea_runtime_scripts.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py tests/test_research_session_assets.py -v
```

Expected: all targeted tests pass.

### Task 8: Review Diff And Report Outcome

**Files:**
- Modify: only files changed above

**Step 1: Inspect git diff**

Run:

```bash
git status --short
git diff -- tools scripts tests .agents/skills README.md README_EN.md docs/experience docs/plans
```

**Step 2: Summarize outcome**

Report:

- what changed
- what was verified
- any remaining gaps, especially that first-wave `data_ready` still builds formal skeleton artifacts rather than real heavy data compute
