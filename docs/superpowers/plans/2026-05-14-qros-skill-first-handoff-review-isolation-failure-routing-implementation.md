# QROS Skill-First Handoff, Review Isolation, And Failure Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove normal-path shell recovery guidance, make review cycles fail closed when isolated reviewer context is mislabeled, and route CSF/TSS failures through the formal failure chain with coherent disposition state.

**Architecture:** Keep the runtime-owned handoff projection as the single source of truth for ordinary users, but make it skill-first instead of command-first. Bind review cycles to explicit reviewer identity/context metadata, reject stale or reused reviewer state if it claims freshness, and route every failure stage through `qros-stage-failure-handler` before `qros-lineage-change-control` can finalize disposition.

**Tech Stack:** Python 3.12/3.13, PyYAML, pytest, existing QROS runtime scripts, skills, and doc/test fixtures.

---

## File Structure

- Modify `runtime/tools/review_resume_protocol.py`
  - Make the shared direct-handoff capsule skill-first for normal stages and keep backend mechanics out of ordinary text output.
- Modify `runtime/tools/research_session.py`
  - Replace shell-oriented `resume_hint` text with skill-first guidance for pending confirmation, review, and failure states.
  - Keep `current_skill`, `next_action`, and `resume_hint` coherent across ordinary progression and failure routing.
- Modify `runtime/scripts/run_research_session.py`
  - Render the skill-first handoff fields without surfacing command-style resume instructions in the human-readable panel.
- Modify `runtime/scripts/run_resume.py`
  - Render the same skill-first capsule for disk-state inspection and stop echoing shell recovery phrasing in the normal path.
- Modify `runtime/tools/progress_runtime.py`
  - Mirror the skill-first direct handoff projection in read-only status payloads.
- Modify `runtime/tools/review_session_runtime.py`
  - Put reviewer context source and history inheritance into the handoff prompt and review-cycle payload so the reviewer lane cannot masquerade as a fresh isolated run.
- Modify `runtime/tools/review_skillgen/adversarial_review_contract.py`
  - Bind request/receipt/result contracts to canonical review context and keep reviewer identity and path validation fail-closed.
- Modify `runtime/tools/review_skillgen/review_result_writer.py`
  - Require raw reviewer findings to carry the current-cycle binding fields before canonicalization.
- Modify `runtime/tools/review_skillgen/review_engine.py`
  - Enforce reviewer isolation and refuse to canonicalize stale or mislabeled review state.
- Modify `runtime/tools/review_skillgen/protected_state_guard.py`
  - Extend protected-state checks so stale review state, raw findings, and canonical projections cannot drift apart.
- Modify `skills/core/qros-research-session/SKILL.md`
  - Rewrite the ordinary-path guidance to say “continue `qros-research-session`” instead of showing shell recovery as the next user-facing step.
- Modify `skills/core/qros-progress/SKILL.md`
  - Keep progress output skill-first and align the failure-disposition wording with the runtime state machine.
- Modify `skills/failure_handling/qros-stage-failure-handler/SKILL.md`
  - Add CSF/TSS backtest and holdout routing plus the failure-disposition handoff language.
- Modify `skills/failure_handling/qros-lineage-change-control/SKILL.md`
  - Clarify that ordinary progression stays blocked once disposition is recorded.
- Modify `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
  - Remove any user-facing command prompts from the skill path and keep it aligned with the new skill-first handoff contract.
- Modify `docs/guides/qros-research-session-usage.md`
  - Rewrite the “resume hint” examples and direct-handoff prose to be skill-first.
- Modify `docs/guides/qros-review-shared-protocol.md`
  - Distinguish skill-first user-facing guidance from backend/debug mechanics.
- Modify `docs/guides/installation.md`
  - Keep `qros-resume` as compatibility/debug material only and avoid presenting it as the ordinary path.
- Modify `tests/session/test_run_research_session_script.py`
- Modify `tests/session/test_run_resume_script.py`
- Modify `tests/session/test_qros_progress_runtime.py`
- Modify `tests/session/test_stage_failure_handler_assets.py`
- Modify `tests/session/test_research_session_runtime.py`
- Modify `tests/session/test_lineage_lock_session_status.py`
- Modify `tests/review/test_adversarial_review_runtime.py`
- Modify `tests/review/test_review_result_writer.py`
- Modify `tests/review/test_review_engine.py`
- Modify `tests/review/test_review_engine_csf_contract_gates.py`
- Modify `tests/review/test_run_stage_review_script.py`
- Modify `tests/anti_drift/test_anti_drift_replay.py`
- Modify `tests/docs/test_install_docs.py`

---

### Task 1: Make Ordinary Handoffs Skill-First

**Files:**
- Modify: `runtime/tools/review_resume_protocol.py`
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/scripts/run_research_session.py`
- Modify: `runtime/scripts/run_resume.py`
- Modify: `runtime/tools/progress_runtime.py`
- Test: `tests/session/test_run_research_session_script.py`
- Test: `tests/session/test_run_resume_script.py`
- Test: `tests/session/test_qros_progress_runtime.py`
- Test: `tests/session/test_lineage_lock_session_status.py`
- Test: `tests/review/test_run_stage_review_script.py`

1. **Write the failing test**

Update the existing positional-continue assertion in `tests/session/test_run_research_session_script.py` so it no longer expects a shell command in the resume hint:

```python
def test_run_research_session_accepts_positional_lineage_continue_mode(tmp_path: Path) -> None:
    ...
    assert payload["lineage_id"] == "btc_alt"
    assert payload["current_skill"] == "qros-research-session"
    assert "qros-research-session" in payload["resume_hint"]
    assert "qros-session" not in payload["resume_hint"]
    assert "qros-resume" not in payload["resume_hint"]
```

Also tighten the resume wrapper expectation in `tests/session/test_run_resume_script.py`:

```python
def test_run_resume_script_reports_direct_handoff_from_disk_state(tmp_path: Path) -> None:
    ...
    assert payload["current_stage"] == "mandate_next_stage_confirmation_pending"
    assert payload["recommended_skill"] == "qros-research-session"
    assert payload["handoff_hint"] == "Continue with qros-research-session."
    assert payload["next_action"] == "Continue with qros-research-session."
    assert "qros-session" not in payload["handoff_hint"]
    assert "qros-resume" not in payload["handoff_hint"]
```

2. **Run the test to verify it fails**

Run:

```bash
python -m pytest \
  tests/session/test_run_research_session_script.py::test_run_research_session_accepts_positional_lineage_continue_mode \
  tests/session/test_run_resume_script.py::test_run_resume_script_reports_direct_handoff_from_disk_state \
  -q
```

Expected: fail because `runtime/tools/research_session.py` still emits `qros-session ... --continue` / `qros-session --lineage-id ...` wording in `resume_hint`.

3. **Write the minimal implementation**

In `runtime/tools/research_session.py`, rewrite `_resume_hint(...)` and `_orchestrated_resume_hint(...)` so the ordinary path says what skill to continue, not what shell command to rerun. The important shape is:

```python
def _resume_hint(...):
    if requires_failure_handling:
        return f"Continue with {current_skill} for lineage {lineage_id}; the next step is failure handling."
    if current_stage.endswith("_review_confirmation_pending"):
        return f"Continue with {current_skill} for lineage {lineage_id}; confirm the review gate next."
    if current_stage.endswith("_next_stage_confirmation_pending"):
        return f"Continue with {current_skill} for lineage {lineage_id}; confirm the next-stage handoff."
    return f"Continue with {current_skill} for lineage {lineage_id}."
```

Keep `next_action` and `resume_hint` aligned with the same skill-first wording. In `runtime/tools/review_resume_protocol.py`, keep `recommended_skill`, `recommended_skill_reason`, `handoff_hint`, `next_action`, and `resume_hint` as the shared direct-handoff capsule, but do not reintroduce command text there. In the two CLI renderers, print the skill-first values and do not synthesize shell instructions in the text panel.

4. **Run the test to verify it passes**

Run:

```bash
python -m pytest \
  tests/session/test_run_research_session_script.py::test_run_research_session_accepts_positional_lineage_continue_mode \
  tests/session/test_run_resume_script.py::test_run_resume_script_reports_direct_handoff_from_disk_state \
  tests/session/test_qros_progress_runtime.py::test_progress_status_payload_surfaces_failure_disposition_gate \
  tests/session/test_lineage_lock_session_status.py::test_progress_payload_exposes_direct_handoff_for_review_complete \
  tests/review/test_run_stage_review_script.py::test_run_stage_review_script_creates_closure_artifacts \
  -q
```

Expected: pass, and the human-readable output should not contain `qros-session ... --continue`, `qros-session --lineage-id ...`, or `/clear` wording.

5. **Commit**

```bash
git add runtime/tools/review_resume_protocol.py runtime/tools/research_session.py runtime/scripts/run_research_session.py runtime/scripts/run_resume.py runtime/tools/progress_runtime.py tests/session/test_run_research_session_script.py tests/session/test_run_resume_script.py tests/session/test_qros_progress_runtime.py tests/session/test_lineage_lock_session_status.py tests/review/test_run_stage_review_script.py
git commit -m "feat: make direct handoffs skill-first"
```

---

### Task 2: Bind Review Cycles To Actual Reviewer Isolation

**Files:**
- Modify: `runtime/tools/review_session_runtime.py`
- Modify: `runtime/tools/review_skillgen/adversarial_review_contract.py`
- Modify: `runtime/tools/review_skillgen/review_result_writer.py`
- Modify: `runtime/tools/review_skillgen/review_engine.py`
- Modify: `runtime/tools/review_skillgen/protected_state_guard.py`
- Test: `tests/review/test_adversarial_review_runtime.py`
- Test: `tests/review/test_review_result_writer.py`
- Test: `tests/review/test_review_engine.py`
- Test: `tests/review/test_review_engine_csf_contract_gates.py`

1. **Write the failing test**

Add a focused assertion block to `tests/review/test_adversarial_review_runtime.py` so the reviewer handoff prompt and receipt/result trail carry the actual isolation contract:

```python
def test_prepare_review_cycle_records_explicit_handoff_only_context(tmp_path: Path) -> None:
    ...
    payload = prepare_review_cycle_for_handoff(...)
    receipt = yaml.safe_load((stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8"))
    result = yaml.safe_load((stage_dir / "review" / "result" / "adversarial_review_result.yaml").read_text(encoding="utf-8"))
    assert receipt["reviewer_context_source"] == "explicit_handoff_only"
    assert receipt["reviewer_history_inheritance"] == "none"
    assert result["reviewer_context_source"] == "explicit_handoff_only"
    assert result["reviewer_history_inheritance"] == "none"
    assert "reviewer_context_source: explicit_handoff_only" in payload["reviewer_handoff_prompt"]
    assert "reviewer_history_inheritance: none" in payload["reviewer_handoff_prompt"]
```

Also add one negative case in `tests/review/test_review_result_writer.py` that reuses the launcher identity in raw findings and expects a fail-closed collision:

```python
def test_ensure_runtime_review_result_rejects_reused_launcher_identity(tmp_path: Path) -> None:
    ...
    raw["reviewer_session_id"] = receipt_payload["launcher_session_id"]
    with pytest.raises(ValueError, match="REVIEWER_IDENTITY_COLLISION"):
        ensure_runtime_review_result(...)
```

2. **Run the test to verify it fails**

Run:

```bash
python -m pytest \
  tests/review/test_adversarial_review_runtime.py::test_prepare_review_cycle_records_explicit_handoff_only_context \
  tests/review/test_review_result_writer.py::test_ensure_runtime_review_result_rejects_reused_launcher_identity \
  -q
```

Expected: fail until `review_session_runtime.py`, `adversarial_review_contract.py`, and `review_result_writer.py` propagate the actual reviewer isolation metadata end to end.

3. **Write the minimal implementation**

In `runtime/tools/review_session_runtime.py`, make `_reviewer_handoff_prompt(...)` print the canonical reviewer isolation summary before the hard constraints block, and include the current review-cycle identity fields in the returned payload. In `runtime/tools/review_skillgen/adversarial_review_contract.py`, keep `reviewer_context_source` and `reviewer_history_inheritance` in the canonical receipt/result contract, verify they match the runtime’s declared isolation mode, and reject a cycle that claims `explicit_handoff_only` while actually reusing context. In `runtime/tools/review_skillgen/review_result_writer.py` and `runtime/tools/review_skillgen/review_engine.py`, keep the canonical result projection aligned with the active request/receipt and fail closed on any stale or mislabeled reviewer state.

4. **Run the test to verify it passes**

Run:

```bash
python -m pytest \
  tests/review/test_adversarial_review_runtime.py::test_prepare_review_cycle_records_explicit_handoff_only_context \
  tests/review/test_review_result_writer.py::test_ensure_runtime_review_result_rejects_reused_launcher_identity \
  tests/review/test_review_engine.py \
  tests/review/test_review_engine_csf_contract_gates.py \
  -q
```

Expected: pass, with `reviewer_context_source = explicit_handoff_only` and `reviewer_history_inheritance = none` preserved only when the runtime really used an isolated reviewer path.

5. **Commit**

```bash
git add runtime/tools/review_session_runtime.py runtime/tools/review_skillgen/adversarial_review_contract.py runtime/tools/review_skillgen/review_result_writer.py runtime/tools/review_skillgen/review_engine.py runtime/tools/review_skillgen/protected_state_guard.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_result_writer.py tests/review/test_review_engine.py tests/review/test_review_engine_csf_contract_gates.py
git commit -m "feat: harden reviewer isolation"
```

---

### Task 3: Route CSF/TSS Failures Through The Formal Failure Chain

**Files:**
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/tools/progress_runtime.py`
- Modify: `skills/failure_handling/qros-stage-failure-handler/SKILL.md`
- Modify: `skills/failure_handling/qros-lineage-change-control/SKILL.md`
- Modify: `tests/session/test_research_session_runtime.py`
- Modify: `tests/session/test_qros_progress_runtime.py`
- Modify: `tests/session/test_stage_failure_handler_assets.py`
- Modify: `tests/anti_drift/test_anti_drift_replay.py`

1. **Write the failing test**

Add a parameterized failure-routing regression to `tests/session/test_research_session_runtime.py` that covers the route-specific CSF and TSS stages the skill currently misses:

```python
@pytest.mark.parametrize(
    ("failed_stage", "stage_dir_name"),
    [
        ("csf_data_ready", "02_csf_data_ready"),
        ("csf_signal_ready", "03_csf_signal_ready"),
        ("csf_train_freeze", "04_csf_train_freeze"),
        ("csf_test_evidence", "05_csf_test_evidence"),
        ("csf_backtest_ready", "06_csf_backtest_ready"),
        ("csf_holdout_validation", "07_csf_holdout_validation"),
        ("tss_backtest_ready", "06_tss_backtest_ready"),
        ("tss_holdout_validation", "07_tss_holdout_validation"),
    ],
)
def test_run_research_session_routes_route_specific_failures_to_failure_handler(...):
    ...
    assert status.current_skill == "qros-stage-failure-handler"
    assert status.requires_failure_handling is True
    assert status.failure_stage == failed_stage
    assert "qros-stage-failure-handler" in status.next_action
```

Add a second assertion path that records a formal failure disposition and verifies the same lineage can only continue through change control:

```python
def test_run_research_session_routes_recorded_failure_to_change_control(...):
    ...
    assert status.blocking_reason_code == "FAILURE_DISPOSITION_RECORDED"
    assert status.current_skill == "qros-lineage-change-control"
    assert "qros-lineage-change-control" in status.next_action
```

Add one asset regression in `tests/session/test_stage_failure_handler_assets.py` so the failure-handler skill file must explicitly name the CSF/TSS route coverage:

```python
for stage_name in (
    "csf_data_ready",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
    "tss_backtest_ready",
    "tss_holdout_validation",
):
    assert stage_name in content
```

2. **Run the test to verify it fails**

Run:

```bash
python -m pytest \
  tests/session/test_research_session_runtime.py::test_run_research_session_routes_route_specific_failures_to_failure_handler \
  tests/session/test_research_session_runtime.py::test_run_research_session_routes_recorded_failure_to_change_control \
  tests/session/test_stage_failure_handler_assets.py \
  tests/anti_drift/test_anti_drift_replay.py::test_run_research_session_snapshot_matches_csf_backtest_ready_no_go_golden \
  -q
```

Expected: fail until the runtime routes every CSF/TSS failure stage through `qros-stage-failure-handler` and then `qros-lineage-change-control` once disposition is recorded.

3. **Write the minimal implementation**

In `runtime/tools/research_session.py`, expand the failure-routing branch so route-specific CSF/TSS stages do not fall through to generic stage handling, and so `FAILURE_DISPOSITION_REQUIRED` / `FAILURE_DISPOSITION_RECORDED` stay coherent with `current_skill`, `next_action`, `resume_hint`, and `blocking_reason_code`. In `runtime/tools/progress_runtime.py`, mirror that same state machine for read-only progress queries. In `skills/failure_handling/qros-stage-failure-handler/SKILL.md`, extend the scope and stage-routing table to include `csf_data_ready`, `csf_signal_ready`, `csf_train_freeze`, `csf_test_evidence`, `csf_backtest_ready`, `csf_holdout_validation`, `tss_backtest_ready`, and `tss_holdout_validation`. In `skills/failure_handling/qros-lineage-change-control/SKILL.md`, make the post-disposition rule explicit: ordinary review and next-stage progression stay blocked once disposition is recorded.

4. **Run the test to verify it passes**

Run:

```bash
python -m pytest \
  tests/session/test_research_session_runtime.py::test_run_research_session_routes_route_specific_failures_to_failure_handler \
  tests/session/test_research_session_runtime.py::test_run_research_session_routes_recorded_failure_to_change_control \
  tests/session/test_qros_progress_runtime.py::test_progress_status_payload_surfaces_failure_disposition_gate \
  tests/session/test_stage_failure_handler_assets.py \
  tests/anti_drift/test_anti_drift_replay.py::test_run_research_session_snapshot_matches_csf_backtest_ready_no_go_golden \
  -q
```

Expected: pass, and the CSF backtest replay should still resolve to the recorded no-go path instead of leaking back into ordinary review or next-stage flow.

5. **Commit**

```bash
git add runtime/tools/research_session.py runtime/tools/progress_runtime.py skills/failure_handling/qros-stage-failure-handler/SKILL.md skills/failure_handling/qros-lineage-change-control/SKILL.md tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py tests/session/test_stage_failure_handler_assets.py tests/anti_drift/test_anti_drift_replay.py
git commit -m "feat: route csf and tss failures formally"
```

---

### Task 4: Rewrite User-Facing Docs And Lock The Regression Tier

**Files:**
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `skills/core/qros-progress/SKILL.md`
- Modify: `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `docs/guides/installation.md`
- Modify: `tests/docs/test_install_docs.py`

1. **Write the failing test**

Update `tests/docs/test_install_docs.py` so it locks the new user-facing wording instead of the old clear/resume framing:

```python
def test_failure_mode_is_documented_in_usage_docs() -> None:
    usage_doc = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    quickstart_doc = Path("docs/guides/quickstart-codex.md").read_text(encoding="utf-8")

    for content in (usage_doc, quickstart_doc):
        assert "qros-stage-failure-handler" in content
        assert "review failure is not ordinary debugging" in content.lower() or "不是普通 debug" in content
        assert "PASS FOR RETRY" in content
        assert "RETRY" in content
        assert "NO-GO" in content
        assert "CHILD LINEAGE" in content
        assert "FAILURE_DISPOSITION_REQUIRED" in content
        assert "failure_disposition.yaml" in content
        assert "clear" not in content.lower()
```

Also tighten the install-doc expectations so the ordinary guidance emphasizes skill-first handoff and keeps `qros-resume` only in compatibility/debug context.

2. **Run the test to verify it fails**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py -q
```

Expected: fail until the docs and skills stop presenting shell recovery as the ordinary user-facing next step.

3. **Write the minimal implementation**

In `docs/guides/qros-research-session-usage.md`, rewrite the direct-handoff examples so they say “continue `qros-research-session`” and point to `qros-stage-failure-handler` / `qros-lineage-change-control` where appropriate. In `docs/guides/qros-review-shared-protocol.md`, keep the PASS-like handoff paragraphs but make the skill-first vs backend/debug split explicit. In `docs/guides/installation.md`, preserve wrapper compatibility text, but move `qros-resume` into the debug/compatibility section and keep it out of the ordinary workflow guidance. Mirror the same wording in `skills/core/qros-research-session/SKILL.md`, `skills/core/qros-progress/SKILL.md`, and `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md` so the skills no longer instruct the user to clear/resume a conversation before continuing.

4. **Run the test to verify it passes**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py -q
```

Expected: pass, with the docs now reading as skill-first workflow guidance instead of shell-first recovery instructions.

5. **Commit**

```bash
git add skills/core/qros-research-session/SKILL.md skills/core/qros-progress/SKILL.md skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md docs/guides/installation.md tests/docs/test_install_docs.py
git commit -m "docs: make qros handoffs skill-first"
```

---

## Self-Review

1. Spec coverage is complete: Task 1 removes command-oriented guidance from ordinary handoffs, Task 2 makes reviewer isolation explicit and fail-closed, Task 3 routes CSF/TSS failures through the formal failure chain, and Task 4 rewrites user-facing docs to match the runtime.
2. Placeholder scan is clean: no `TBD`, `TODO`, `implement later`, or vague “handle edge cases” steps are left in the plan.
3. Type and contract names are consistent across tasks: `recommended_skill`, `recommended_skill_reason`, `handoff_hint`, `current_skill`, `next_action`, `resume_hint`, `reviewer_context_source`, `reviewer_history_inheritance`, `FAILURE_DISPOSITION_REQUIRED`, and `FAILURE_DISPOSITION_RECORDED` all use the same meaning in runtime, tests, and docs.
4. Verification is explicit: each task has a focused pytest command, and the final execution gate includes `python runtime/scripts/run_verification_tier.py --tier smoke` followed by `python runtime/scripts/run_verification_tier.py --tier full-smoke` because this change touches stage flow, review orchestration, route split, and anti-drift behavior.
5. No gap remains against the spec’s success criteria: the ordinary path becomes skill-first, reviewer reuse cannot masquerade as isolation, failure disposition stays coherent, and the CSF backtest replay remains on the formal failure path.
