# Signal Ready Orchestration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend `qros-research-session` so the first-wave flow continues from data_ready review into interactive baseline-only `signal_ready` freezing, formal `03_signal_ready` artifact generation, and `signal_ready review`.

**Architecture:** Reuse the mandate/data_ready pattern. Add a dedicated `tools/signal_ready_runtime.py` for stage scaffolding and formal outputs, then extend `tools/research_session.py` to detect and drive new `signal_ready` states. Keep review closure on the existing stage review engine and add a new author skill plus doc updates.

**Tech Stack:** Python, YAML, markdown docs, pytest

---

### Task 1: Document The Design On Disk

**Files:**
- Create: `docs/plans/2026-03-25-signal-ready-orchestration-design.md`
- Create: `docs/plans/2026-03-25-signal-ready-orchestration-implementation-plan.md`

**Step 1: Write the design doc**

Save the approved baseline-only `signal_ready` product semantics, freeze groups, runtime states, outputs, and guardrails.

**Step 2: Write the implementation plan**

Save this task-by-task plan so execution stays aligned with the approved design.

### Task 2: Add Failing Runtime Tests

**Files:**
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Write failing tests**

Add tests for:

- `data_ready_review_complete -> signal_ready_confirmation_pending`
- next `signal_ready` freeze group reporting
- explicit `--confirm-signal-ready` approval before build
- `signal_ready_review` and `signal_ready_review_complete` stage detection

**Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -v
```

Expected: failures because `signal_ready` stages and CLI flag do not exist yet.

### Task 3: Add Failing Asset And Runtime Tests

**Files:**
- Modify: `tests/test_research_session_assets.py`
- Modify: `tests/test_idea_runtime_scripts.py`

**Step 1: Write failing tests**

Add assertions that:

- `qros-signal-ready-author` exists
- `qros-research-session` mentions `signal_ready_confirmation_pending`
- usage docs describe `signal_ready`
- a new build script can scaffold formal `03_signal_ready` outputs from confirmed draft inputs

**Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_research_session_assets.py tests/test_idea_runtime_scripts.py -v
```

Expected: failures because the skill and runtime script do not exist yet.

### Task 4: Implement Signal Ready Runtime

**Files:**
- Create: `tools/signal_ready_runtime.py`
- Create: `scripts/build_signal_ready_from_data_ready.py`

**Step 1: Write minimal implementation**

Implement:

- `SIGNAL_READY_FREEZE_DRAFT_FILE`
- `SIGNAL_READY_FREEZE_GROUP_ORDER`
- blank freeze draft scaffold
- `scaffold_signal_ready()`
- `build_signal_ready_from_data_ready()`
- required output generation for `03_signal_ready/*`

The build should consume only confirmed freeze groups and already frozen upstream outputs.

**Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_idea_runtime_scripts.py -v
```

Expected: new signal_ready runtime tests pass.

### Task 5: Extend Research Session State Machine

**Files:**
- Modify: `tools/research_session.py`
- Modify: `scripts/run_research_session.py`

**Step 1: Write minimal implementation**

Add:

- `signal_ready_confirmation_pending`
- `signal_ready_author`
- `signal_ready_review`
- `signal_ready_review_complete`
- signal_ready approval artifact handling
- `--confirm-signal-ready`
- next-group reporting for `signal_ready`
- automatic `03_signal_ready` build only after explicit approval

**Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -v
```

Expected: signal_ready state machine tests pass.

### Task 6: Update Skills And Experience Docs

**Files:**
- Create: `.agents/skills/qros-signal-ready-author/SKILL.md`
- Create: `.agents/skills/qros-signal-ready-author/agents/openai.yaml`
- Modify: `.agents/skills/qros-research-session/SKILL.md`
- Modify: `README.md`
- Modify: `README_EN.md`
- Modify: `docs/experience/qros-research-session-usage.md`
- Modify: `docs/experience/quickstart-codex.md`

**Step 1: Write minimal doc and skill updates**

Make the first-wave story consistent with the new `signal_ready` boundary and grouped baseline freeze flow.

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
- any remaining gaps, especially that first-wave `signal_ready` still builds formal skeleton artifacts rather than real heavy signal compute
