# QROS Stage Failure Handler Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a unified QROS failure-handling skill and wire `qros-research-session` plus the session runtime so failure verdicts automatically stop normal progression and route the agent into stage-specific institutional failure handling for `data_ready -> shadow`.

**Architecture:** Introduce a new `qros-stage-failure-handler` skill that embeds the shared failure harness and stage-specific routing rules from the existing fail-SOP corpus. Extend `tools/research_session.py` to expose explicit failure-routing signals alongside its existing stage-detection behavior, then update `qros-research-session` and usage docs so the conversation contract requires automatic mode switching on `PASS FOR RETRY`, `RETRY`, `NO-GO`, and `CHILD LINEAGE`.

**Tech Stack:** Python 3.11, `pytest`, existing QROS review certificates, existing QROS skills and fail-SOP documentation

---

### Task 1: Lock Failure-Handling Asset Expectations

**Files:**
- Create: `tests/test_stage_failure_handler_assets.py`
- Modify: `tests/test_project_bootstrap.py`

**Step 1: Write the failing asset tests**

Create `tests/test_stage_failure_handler_assets.py` with assertions that:

- `skills/qros-stage-failure-handler/SKILL.md` exists
- the skill text explicitly covers `data_ready`, `signal_ready`, `train_freeze`, `test_evidence`, `backtest_ready`, `holdout_validation`, and `shadow`
- the skill text requires stopping normal stage progression on `PASS FOR RETRY`, `RETRY`, `NO-GO`, and `CHILD LINEAGE`
- the skill text requires formal outputs including `failure_disposition.yaml`

Extend `tests/test_project_bootstrap.py` so the repo bootstrap contract expects:

- `skills/qros-stage-failure-handler/SKILL.md`
- the updated `qros-research-session` skill text mentioning automatic failure routing

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_stage_failure_handler_assets.py tests/test_project_bootstrap.py -v`

Expected: FAIL because the new skill and tightened session contract do not exist yet.

**Step 3: Commit**

```bash
git add tests/test_stage_failure_handler_assets.py tests/test_project_bootstrap.py
git commit -m "test: add failure handler skill expectations"
```

### Task 2: Add Runtime Failure-Routing Status Signals

**Files:**
- Modify: `tools/research_session.py`
- Modify: `tests/test_research_session_runtime.py`

**Step 1: Write the failing runtime tests**

Extend `tests/test_research_session_runtime.py` so each already-orchestrated review stage verifies:

- structured certificate verdict `PASS FOR RETRY` sets `requires_failure_handling` to `True`
- structured certificate verdict `RETRY` sets `requires_failure_handling` to `True`
- structured certificate verdict `NO-GO` sets `requires_failure_handling` to `True`
- structured certificate verdict `CHILD LINEAGE` sets `requires_failure_handling` to `True`
- structured certificate verdict `PASS` keeps `requires_failure_handling` as `False`
- `next_action` points to failure handling instead of the next confirmation stage when failure routing is required

Keep the existing progression assertions intact so the runtime still proves it does not advance on non-advancing verdicts.

**Step 2: Run focused tests to verify failure**

Run: `python -m pytest tests/test_research_session_runtime.py -k failure_handling -v`

Expected: FAIL because the runtime status model does not yet expose explicit failure-routing fields.

**Step 3: Implement the minimal runtime change**

Modify `tools/research_session.py` to:

- add explicit status fields for `review_verdict`, `requires_failure_handling`, `failure_stage`, and `failure_reason_summary`
- populate those fields deterministically from `stage_completion_certificate.yaml`
- keep backward compatibility for unstructured legacy certificates
- ensure `next_action` becomes failure-oriented whenever `requires_failure_handling` is `True`

Do not encode full stage-specific classification logic into the runtime. The runtime only reports routing status.

**Step 4: Run focused tests**

Run: `python -m pytest tests/test_research_session_runtime.py -k failure_handling -v`

Expected: PASS

**Step 5: Commit**

```bash
git add tools/research_session.py tests/test_research_session_runtime.py
git commit -m "feat: add session failure routing status"
```

### Task 3: Add The Unified Failure Handler Skill

**Files:**
- Create: `skills/qros-stage-failure-handler/SKILL.md`
- Modify: `tests/test_stage_failure_handler_assets.py`

**Step 1: Write the skill content**

Create `skills/qros-stage-failure-handler/SKILL.md` with sections covering:

- purpose and scope
- automatic entry conditions from `qros-research-session`
- shared failure harness
- stage-specific routing for `data_ready -> shadow`
- required formal outputs
- rules for allowed versus forbidden actions
- explicit prohibition on resuming normal stage progression before failure disposition is formed

The skill should embed the shared harness directly because `stage-failure-harness` is referenced in docs but is not a standalone checked-in file.

**Step 2: Run focused asset tests**

Run: `python -m pytest tests/test_stage_failure_handler_assets.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add skills/qros-stage-failure-handler/SKILL.md tests/test_stage_failure_handler_assets.py
git commit -m "feat: add unified stage failure handler skill"
```

### Task 4: Tighten Research Session Skill And Usage Docs

**Files:**
- Modify: `skills/qros-research-session/SKILL.md`
- Modify: `docs/experience/qros-research-session-usage.md`
- Modify: `docs/experience/quickstart-codex.md`
- Modify: `tests/test_stage_failure_handler_assets.py`

**Step 1: Write failing doc-level assertions**

Extend `tests/test_stage_failure_handler_assets.py` so it asserts:

- `qros-research-session` explicitly says it must switch to `qros-stage-failure-handler` when failure verdicts appear
- the usage docs explain that review failure is not ordinary debugging and causes a failure-handling mode switch

**Step 2: Update the assets**

Modify `skills/qros-research-session/SKILL.md` to require:

- automatic switch to `qros-stage-failure-handler`
- immediate stop of normal orchestration on non-advancing failure verdicts
- use of runtime failure-routing status instead of ad hoc agent judgment

Update the usage docs so users understand:

- which verdicts trigger failure mode
- why stage-specific failure handling exists
- that the active research repo must preserve the failed state before modification

**Step 3: Run focused asset tests**

Run: `python -m pytest tests/test_stage_failure_handler_assets.py tests/test_project_bootstrap.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add skills/qros-research-session/SKILL.md docs/experience/qros-research-session-usage.md docs/experience/quickstart-codex.md tests/test_stage_failure_handler_assets.py tests/test_project_bootstrap.py
git commit -m "feat: route research session failures into handler skill"
```

### Task 5: Add Script-Level Failure Routing Coverage

**Files:**
- Modify: `tests/test_run_research_session_script.py`
- Modify: `scripts/run_research_session.py`

**Step 1: Write the failing script test**

Extend `tests/test_run_research_session_script.py` with a scenario that:

- prepares a lineage at `test_evidence review`
- writes a structured `stage_completion_certificate.yaml` with `stage_status: RETRY`
- runs `scripts/run_research_session.py`
- asserts the printed status reports failure routing instead of `backtest_ready_confirmation_pending`

The assertions should check for:

- current stage remains the failed review stage
- `requires_failure_handling: true`
- `review_verdict: RETRY`
- `next_action` references failure handling

**Step 2: Run the focused test to verify failure**

Run: `python -m pytest tests/test_run_research_session_script.py -k failure_routing -v`

Expected: FAIL because the script output does not yet surface the new routing fields clearly enough.

**Step 3: Implement the minimal script update**

Modify `scripts/run_research_session.py` so the printed status summary includes the new failure-routing fields when present.

**Step 4: Run focused tests**

Run: `python -m pytest tests/test_run_research_session_script.py -k failure_routing -v`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/run_research_session.py tests/test_run_research_session_script.py
git commit -m "feat: expose failure routing in session script output"
```

### Task 6: Run Full Verification And Smoke A Failure Scenario

**Files:**
- Verify only: repository-wide

**Step 1: Run the relevant automated tests**

Run: `python -m pytest tests/test_project_bootstrap.py tests/test_stage_failure_handler_assets.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py -v`

Expected: PASS with the new skill, docs, runtime status fields, and script output included.

**Step 2: Smoke a failed review scenario**

Run a repo-local smoke flow that prepares a temporary lineage with a failed `test_evidence review` certificate, then execute:

```bash
python scripts/run_research_session.py --outputs-root /tmp/qros-failure-smoke/outputs --lineage-id <lineage-id>
```

Expected:

- the reported stage stays at `test_evidence_review`
- the status summary includes `requires_failure_handling: true`
- the summary references the failure handler rather than the next normal stage

**Step 3: Review git status**

Run: `git status --short`

Expected: clean, or only intended tracked files changed. Do not commit smoke outputs under `/tmp`.

**Step 4: Commit final implementation**

```bash
git add tools/research_session.py scripts/run_research_session.py skills/qros-stage-failure-handler/SKILL.md skills/qros-research-session/SKILL.md docs/experience/qros-research-session-usage.md docs/experience/quickstart-codex.md tests/test_stage_failure_handler_assets.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py tests/test_project_bootstrap.py
git commit -m "feat: add unified stage failure handling"
```
