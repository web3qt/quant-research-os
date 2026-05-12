# QROS Clear-Resume Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a disk-truth-driven clear/resume protocol so pass-like review handoffs explicitly tell Codex or Claude Code to `/clear` before continuing, and provide a validated `qros-resume` recovery entrypoint.

**Architecture:** Build one shared resume-capsule helper that reads the existing lineage and review state snapshots, then reuse it from `qros-review`, `qros-session`, `qros-progress`, and `qros-resume`. The capsule stays read-only and refuses stale or drifting state instead of trusting conversation history.

**Tech Stack:** Python 3.13, existing QROS runtime scripts and tools, pytest, bash wrappers under `runtime/bin/`.

---

### Task 1: Add the shared resume capsule helper

**Files:**
- Create: `runtime/tools/review_resume_protocol.py`
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/tools/progress_runtime.py`
- Test: `tests/session/test_lineage_lock_session_status.py`
- Test: `tests/review/test_review_preflight.py`

- [ ] **Step 1: Write the failing test**

```python
def test_progress_payload_exposes_clear_required_for_review_complete(tmp_path: Path) -> None:
    ...
    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_id)
    assert payload["clear_required"] is True
    assert payload["clear_instruction"].startswith("Clear the conversation")
    assert "qros-resume --lineage-id" in payload["recommended_command"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/session/test_lineage_lock_session_status.py::test_progress_payload_exposes_clear_required_for_review_complete -v`

Expected: FAIL because `clear_required` and related fields do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def build_clear_resume_capsule(status: SessionContext, *, outputs_root: Path | None = None) -> dict[str, object]:
    ...
```

The helper should derive the reminder from the existing `SessionContext` / review state snapshots without adding a new persisted state file.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/session/test_lineage_lock_session_status.py::test_progress_payload_exposes_clear_required_for_review_complete -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_resume_protocol.py runtime/tools/research_session.py runtime/tools/progress_runtime.py tests/session/test_lineage_lock_session_status.py tests/review/test_review_preflight.py
git commit -m "feat: add shared clear resume capsule"
```

### Task 2: Add `qros-resume`

**Files:**
- Create: `runtime/scripts/run_resume.py`
- Create: `runtime/bin/qros-resume`
- Modify: `runtime/tools/install_runtime.py`
- Test: `tests/bootstrap/test_install_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
def test_install_runtime_writes_qros_resume_bin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ...
    assert (install_root / ".qros" / "bin" / "qros-resume").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/bootstrap/test_install_runtime.py::test_install_runtime_writes_qros_resume_bin -v`

Expected: FAIL because the new wrapper is not installed yet.

- [ ] **Step 3: Write minimal implementation**

`run_resume.py` should:

```python
def main() -> int:
    payload = resume_status_payload(...)
    print(json.dumps(payload, ensure_ascii=False, indent=2)) if args.json else print(_render_text(payload))
```

The wrapper should validate state first, print the same clear/resume capsule, and only support `--continue` after validation succeeds.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/bootstrap/test_install_runtime.py::test_install_runtime_writes_qros_resume_bin -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/scripts/run_resume.py runtime/bin/qros-resume runtime/tools/install_runtime.py tests/bootstrap/test_install_runtime.py
git commit -m "feat: add qros-resume recovery entrypoint"
```

### Task 3: Surface the `/clear` reminder in status and review outputs

**Files:**
- Modify: `runtime/scripts/run_research_session.py`
- Modify: `runtime/scripts/run_progress.py`
- Modify: `runtime/scripts/run_stage_review.py`
- Modify: `runtime/tools/review_engine.py`
- Test: `tests/review/test_start_review_session.py`
- Test: `tests/review/test_review_cycle_prepare.py`
- Test: `tests/review/test_run_stage_review_script.py`
- Test: `tests/session/test_run_research_session_script.py`

- [ ] **Step 1: Write the failing test**

```python
def test_run_stage_review_script_prints_clear_reminder_on_pass(tmp_path: Path) -> None:
    ...
    assert "Clear the conversation" in result.stdout
    assert "qros-resume --lineage-id" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/review/test_run_stage_review_script.py::test_run_stage_review_script_prints_clear_reminder_on_pass -v`

Expected: FAIL because the closer output does not yet include the reminder.

- [ ] **Step 3: Write minimal implementation**

Render the reminder only when the current status is a normal-advance review boundary. Keep the wording identical across closer, session, and progress.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/review/test_run_stage_review_script.py::test_run_stage_review_script_prints_clear_reminder_on_pass -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/scripts/run_research_session.py runtime/scripts/run_progress.py runtime/scripts/run_stage_review.py runtime/tools/review_engine.py tests/review/test_start_review_session.py tests/review/test_review_cycle_prepare.py tests/review/test_run_stage_review_script.py tests/session/test_run_research_session_script.py
git commit -m "feat: remind users to clear before resuming"
```

### Task 4: Add end-to-end regression coverage

**Files:**
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Test: `tests/session/test_lineage_lock_session_status.py`
- Test: `tests/review/test_review_preflight.py`
- Test: `tests/review/test_adversarial_review_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
def test_qros_session_and_progress_repeat_clear_hint_after_review_complete(tmp_path: Path) -> None:
    ...
    assert "Clear the conversation" in session_output
    assert "Clear the conversation" in progress_output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/session/test_lineage_lock_session_status.py tests/review/test_review_preflight.py tests/review/test_adversarial_review_runtime.py -v`

Expected: FAIL until all call sites read the shared capsule.

- [ ] **Step 3: Write minimal implementation**

Update the user docs to explain that review pass boundaries must be followed by `/clear`, and that `qros-resume` is the post-clear re-entry point.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/session/test_lineage_lock_session_status.py tests/review/test_review_preflight.py tests/review/test_adversarial_review_runtime.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md tests/session/test_lineage_lock_session_status.py tests/review/test_review_preflight.py tests/review/test_adversarial_review_runtime.py
git commit -m "test: cover clear resume handoff flow"
```

### Validation

- [ ] Run focused tests:

```bash
python -m pytest tests/bootstrap/test_install_runtime.py tests/review/test_review_cycle_prepare.py tests/review/test_start_review_session.py tests/review/test_run_stage_review_script.py tests/review/test_review_preflight.py tests/session/test_lineage_lock_session_status.py tests/session/test_run_research_session_script.py -v
```

- [ ] Run smoke:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

- [ ] Run full-smoke:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```
