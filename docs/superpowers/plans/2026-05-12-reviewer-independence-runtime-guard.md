# Reviewer Independence Runtime Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent launcher/main-thread review impersonation and stale reviewer evidence reuse by enforcing reviewer independence at runtime.

**Architecture:** Extend the existing protected review state guard so review request/receipt/state/result/closure files form one sealed transaction. `qros-review` remains the only canonicalizer/closer, while `qros-review-cycle reset --archive-stale-cycle` is the only normal recovery from stale active review evidence.

**Tech Stack:** Python 3.13, PyYAML, pytest, existing QROS runtime modules under `runtime/tools/review_skillgen`.

---

## File Structure

- Modify `runtime/tools/review_skillgen/protected_state_guard.py`
  - Add reason codes for stale review evidence, closure projection drift, and protected result drift.
  - Validate request/receipt/handoff/state/raw findings/canonical result/closure consistency.
  - Recompute current author digest using fresh file reads.
- Modify `runtime/tools/review_skillgen/review_result_writer.py`
  - Reject stale canonical result files when raw findings are absent but an active review cycle still exists.
  - Keep raw findings canonicalization as the only path that writes canonical result files for an active cycle.
- Modify `runtime/tools/review_skillgen/reviewer_write_scope_audit.py`
  - Treat `reviewer_findings.raw.yaml` as an allowed pre-closer result file.
  - Reject unexpected result files with a stable write-scope violation message.
- Modify `runtime/tools/review_session_runtime.py`
  - Stop auto-archiving stale/closed cycles during `prepare`; require explicit reset first.
- Add/modify tests:
  - `tests/review/test_review_result_writer.py`
  - `tests/review/test_review_runtime_state.py`
  - `tests/review/test_adversarial_review_runtime.py`
  - `tests/session/test_lineage_lock_session_status.py`

## Task 1: Guard raw findings and stale author digest

**Files:**
- Modify: `runtime/tools/review_skillgen/protected_state_guard.py`
- Test: `tests/review/test_review_runtime_state.py`

- [ ] **Step 1: Write failing tests for stale raw findings**

Add these imports and tests to `tests/review/test_review_runtime_state.py`:

```python
import pytest
import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ensure_adversarial_review_request,
    issue_reviewer_receipt,
)
from runtime.tools.review_skillgen.protected_state_guard import (
    REVIEWER_FINDINGS_UNBOUND,
    STALE_REVIEW_EVIDENCE,
    ProtectedStateError,
    assert_protected_review_state_intact,
)
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest,
    write_review_runtime_state,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import write_reviewer_write_scope_baseline
```

```python
def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_raw_findings_case(tmp_path: Path) -> tuple[Path, Path, list[str], list[str]]:
    lineage_root = tmp_path / "outputs" / "raw_binding_case"
    stage_dir = lineage_root / "01_mandate"
    required_outputs = ["mandate.md", "run_manifest.json"]
    required_provenance = ["program_execution_manifest.json"]
    for name in required_outputs:
        _write_text(stage_dir / "author" / "formal" / name, f"{name}: ok\n")
    _write_text(stage_dir / "author" / "formal" / "program_execution_manifest.json", "{}\n")
    request = ensure_adversarial_review_request(
        stage_dir,
        lineage_id=lineage_root.name,
        stage="mandate",
        author_identity="author-agent",
        author_session_id="author-session",
        required_program_dir="program/mandate",
        required_program_entrypoint="run_stage.py",
        required_artifact_paths=required_outputs,
        required_provenance_paths=required_provenance,
        program_hash="hash-1",
        stage_invoked_at="2026-05-12T00:00:00+00:00",
    )
    receipt = issue_reviewer_receipt(
        stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child",
    )
    digest = compute_author_materialization_digest(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=required_outputs,
        required_provenance_paths=required_provenance,
    )
    write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id=request["review_cycle_id"],
        review_requested_at=receipt["receipt_written_at"],
        review_bound_author_digest=digest,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
    )
    write_reviewer_write_scope_baseline(
        stage_dir,
        review_cycle_id=receipt["review_cycle_id"],
        launcher_thread_id=receipt["launcher_thread_id"],
        reviewer_agent_id=receipt["reviewer_agent_id"],
    )
    return lineage_root, stage_dir, required_outputs, required_provenance


def test_protected_guard_rejects_raw_findings_with_wrong_reviewer_agent(tmp_path: Path) -> None:
    lineage_root, stage_dir, required_outputs, required_provenance = _prepare_raw_findings_case(tmp_path)
    request = yaml.safe_load((stage_dir / "review/request/adversarial_review_request.yaml").read_text())
    _write_text(
        stage_dir / "review/result/reviewer_findings.raw.yaml",
        yaml.safe_dump(
            {
                "review_cycle_id": request["review_cycle_id"],
                "reviewer_agent_id": "launcher-main-thread",
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
            },
            sort_keys=False,
        ),
    )

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=required_outputs,
            required_provenance_paths=required_provenance,
            allow_missing_state=False,
        )

    assert exc_info.value.reason_code == REVIEWER_FINDINGS_UNBOUND


def test_protected_guard_rejects_raw_findings_after_author_outputs_change(tmp_path: Path) -> None:
    lineage_root, stage_dir, required_outputs, required_provenance = _prepare_raw_findings_case(tmp_path)
    request = yaml.safe_load((stage_dir / "review/request/adversarial_review_request.yaml").read_text())
    receipt = yaml.safe_load((stage_dir / "review/request/reviewer_receipt.yaml").read_text())
    _write_text(
        stage_dir / "review/result/reviewer_findings.raw.yaml",
        yaml.safe_dump(
            {
                "review_cycle_id": request["review_cycle_id"],
                "reviewer_agent_id": receipt["reviewer_agent_id"],
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
            },
            sort_keys=False,
        ),
    )
    _write_text(stage_dir / "author" / "formal" / "mandate.md", "changed after reviewer receipt\n")

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=required_outputs,
            required_provenance_paths=required_provenance,
            allow_missing_state=False,
        )

    assert exc_info.value.reason_code == STALE_REVIEW_EVIDENCE
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/review/test_review_runtime_state.py::test_protected_guard_rejects_raw_findings_with_wrong_reviewer_agent tests/review/test_review_runtime_state.py::test_protected_guard_rejects_raw_findings_after_author_outputs_change -v
```

Expected: FAIL because `STALE_REVIEW_EVIDENCE` does not exist and the current guard reports only the generic digest drift path.

- [ ] **Step 3: Implement reason codes and digest-aware raw findings validation**

In `runtime/tools/review_skillgen/protected_state_guard.py`, add reason codes near the existing constants:

```python
STALE_REVIEW_EVIDENCE = "STALE_REVIEW_EVIDENCE"
CLOSURE_PROJECTION_DRIFT = "CLOSURE_PROJECTION_DRIFT"
REVIEWER_WRITE_SCOPE_VIOLATION = "REVIEWER_WRITE_SCOPE_VIOLATION"
```

Change `_validate_review_runtime_state()` so digest drift while a request/receipt or raw findings exists reports stale review evidence:

```python
    if bound_digest and bound_digest != current_digest:
        raw_path = stage_dir / "review" / "result" / RAW_REVIEWER_FINDINGS_FILENAME
        if request_path.exists() or receipt_path.exists() or raw_path.exists():
            _raise(
                STALE_REVIEW_EVIDENCE,
                state_path,
                "current author/formal digest no longer matches the active review-bound author digest",
            )
        _raise(
            REVIEW_STATE_PROJECTION_DRIFT,
            state_path,
            "review_bound_author_digest does not match current author/formal digest",
        )
```

Extend `_validate_raw_findings()`:

```python
    state_path = review_runtime_state_path(stage_dir)
    state = load_review_runtime_state(state_path) if state_path.exists() else {}
    if state.get("review_state", "").startswith("review_closed"):
        _raise(REVIEWER_FINDINGS_UNBOUND, raw_path, "raw findings cannot exist after review closure")
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/review/test_review_runtime_state.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_skillgen/protected_state_guard.py tests/review/test_review_runtime_state.py
git commit -m "feat: bind raw reviewer findings to current author digest"
```

## Task 2: Reject stale canonical result projections

**Files:**
- Modify: `runtime/tools/review_skillgen/review_result_writer.py`
- Test: `tests/review/test_review_result_writer.py`

- [ ] **Step 1: Write failing test for canonical result without raw findings**

Add this test to `tests/review/test_review_result_writer.py`:

```python
def test_ensure_runtime_review_result_rejects_stale_canonical_result_without_raw_findings(
    tmp_path: Path,
) -> None:
    stage_dir = _prepare_mandate_review_case(tmp_path)
    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    _write_yaml(
        stage_dir / "review" / "result" / "adversarial_review_result.yaml",
        {
            "review_cycle_id": request_payload["review_cycle_id"],
            "reviewer_identity": "reviewer-agent",
            "reviewer_role": "reviewer",
            "reviewer_session_id": "review-session",
            "reviewer_mode": "adversarial",
            "reviewer_agent_id": receipt_payload["reviewer_agent_id"],
            "reviewer_execution_mode": "spawned_agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
            "review_loop_outcome": "CLOSURE_READY_PASS",
            "reviewed_program_dir": "program/mandate",
            "reviewed_program_entrypoint": "run_stage.py",
            "reviewed_artifact_paths": sorted(request_payload["stage_content_artifact_paths"]),
            "reviewed_provenance_paths": ["program_execution_manifest.json"],
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": ["canonical result was hand-written"],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )

    with pytest.raises(ValueError) as exc_info:
        ensure_runtime_review_result(
            review_result_dir=stage_dir / "review" / "result",
            request_payload=request_payload,
            receipt_payload=receipt_payload,
            runtime_identity=ReviewerRuntimeIdentity(
                reviewer_identity="reviewer-agent",
                reviewer_role="reviewer",
                reviewer_session_id="review-session",
                reviewer_mode="adversarial",
            ),
        )

    assert "PROTECTED_STATE_DRIFT" in str(exc_info.value)
    assert "reviewer_findings.raw.yaml is required" in str(exc_info.value)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/review/test_review_result_writer.py::test_ensure_runtime_review_result_rejects_stale_canonical_result_without_raw_findings -v
```

Expected: FAIL because current code accepts existing canonical result files.

- [ ] **Step 3: Require raw findings for active-cycle canonicalization**

In `runtime/tools/review_skillgen/review_result_writer.py`, add:

```python
PROTECTED_STATE_DRIFT = "PROTECTED_STATE_DRIFT"
```

Replace the `if result_path.exists():` branch in `ensure_runtime_review_result()` with:

```python
    if result_path.exists():
        raise ValueError(
            f"{PROTECTED_STATE_DRIFT}: {result_path}: reviewer_findings.raw.yaml is required "
            "for active-cycle canonicalization; reset stale review state and request a fresh reviewer run"
        )
```

This makes raw findings the only active-cycle input accepted by `qros-review`.

- [ ] **Step 4: Update tests that relied on hand-written canonical results**

In `tests/review/test_adversarial_review_runtime.py`, helpers currently write
`adversarial_review_result.yaml` directly. Replace those uses in tests that call
`run_stage_review()` with raw findings where possible:

```python
def _write_raw_reviewer_findings(
    stage_dir: Path,
    *,
    review_loop_outcome: str,
    reviewer_agent_id: str = "reviewer-child-agent",
    blocking_findings: list[str] | None = None,
) -> None:
    request_payload = _review_request_payload(stage_dir)
    _write_yaml(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        {
            "review_cycle_id": request_payload["review_cycle_id"],
            "reviewer_agent_id": reviewer_agent_id,
            "review_loop_outcome": review_loop_outcome,
            "blocking_findings": blocking_findings or [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )
```

Keep a separate test for stale hand-written canonical files.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m pytest tests/review/test_review_result_writer.py tests/review/test_adversarial_review_runtime.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_skillgen/review_result_writer.py tests/review/test_review_result_writer.py tests/review/test_adversarial_review_runtime.py
git commit -m "feat: require raw reviewer findings for active review closure"
```

## Task 3: Tighten result write scope and closed-cycle checks

**Files:**
- Modify: `runtime/tools/review_skillgen/reviewer_write_scope_audit.py`
- Modify: `runtime/tools/review_skillgen/protected_state_guard.py`
- Test: `tests/review/test_adversarial_review_runtime.py`
- Test: `tests/session/test_lineage_lock_session_status.py`

- [ ] **Step 1: Write failing tests for unexpected result files and closed-cycle raw findings**

Add to `tests/review/test_adversarial_review_runtime.py`:

```python
def test_run_stage_review_rejects_unexpected_result_file(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(stage_dir, review_loop_outcome="CLOSURE_READY_PASS")
    _write_yaml(stage_dir / "review" / "result" / "launcher_notes.yaml", {"note": "not reviewer owned"})

    with pytest.raises(ValueError) as exc_info:
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )

    assert "REVIEWER_WRITE_SCOPE_VIOLATION" in str(exc_info.value)
```

Add to `tests/session/test_lineage_lock_session_status.py`:

```python
def test_progress_blocks_raw_findings_after_closed_review_state(tmp_path: Path) -> None:
    outputs_root, lineage_root, stage_dir = _build_review_pending_lineage(tmp_path)
    _write(
        stage_dir / "review" / "state" / "review_runtime_state.yaml",
        yaml.safe_dump(
            {
                "review_state": "review_closed_pass",
                "active_review_cycle_id": "manual-cycle",
                "review_bound_author_digest": None,
                "last_review_verdict": "PASS",
                "closure_written_at": "2026-05-12T00:00:00Z",
                "updated_at": "2026-05-12T00:00:00Z",
            },
            sort_keys=False,
        ),
    )
    _write(stage_dir / "review" / "closure" / "latest_review_pack.yaml", "review_cycle_id: manual-cycle\n")
    _write(stage_dir / "review" / "closure" / "stage_gate_review.yaml", "review_cycle_id: manual-cycle\n")
    _write(stage_dir / "review" / "closure" / "stage_completion_certificate.yaml", "review_cycle_id: manual-cycle\n")
    _write(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        "review_cycle_id: manual-cycle\nreviewer_agent_id: reviewer-child\nreview_loop_outcome: CLOSURE_READY_PASS\n",
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert payload["stage_status"] == "blocked"
    assert payload["blocking_reason_code"] == "REVIEWER_FINDINGS_UNBOUND"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py::test_run_stage_review_rejects_unexpected_result_file tests/session/test_lineage_lock_session_status.py::test_progress_blocks_raw_findings_after_closed_review_state -v
```

Expected: FAIL because raw findings are not yet allowed as a pre-closer result file and closed-cycle raw findings may not be checked in progress.

- [ ] **Step 3: Allow raw findings but reject unexpected result files with stable code**

In `runtime/tools/review_skillgen/reviewer_write_scope_audit.py`, update `ALLOWED_RESULT_FILENAMES`:

```python
ALLOWED_RESULT_FILENAMES = {
    RAW_REVIEWER_FINDINGS_FILENAME,
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    "review_findings.yaml",
    REVIEWER_WRITE_SCOPE_AUDIT_FILENAME,
}
```

Import `RAW_REVIEWER_FINDINGS_FILENAME` from `review_result_writer.py`.

In `validate_reviewer_write_scope_audit()`, change the audit failure message:

```python
    if audit_payload["audit_status"] != "PASS":
        raise ValueError("REVIEWER_WRITE_SCOPE_VIOLATION: reviewer_write_scope_audit.yaml audit_status must be PASS before closure")
```

- [ ] **Step 4: Ensure progress/session guard reports closed-cycle raw findings**

In `runtime/tools/review_skillgen/protected_state_guard.py`, keep the closed-cycle raw check from Task 1 and ensure caller surfaces `REVIEWER_FINDINGS_UNBOUND`. If progress/session currently collapses all protected state errors to `REVIEW_STATE_PROJECTION_DRIFT`, adjust the mapping in the caller to preserve `exc.reason_code`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py tests/session/test_lineage_lock_session_status.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_skillgen/reviewer_write_scope_audit.py runtime/tools/review_skillgen/protected_state_guard.py tests/review/test_adversarial_review_runtime.py tests/session/test_lineage_lock_session_status.py
git commit -m "feat: reject protected review result drift"
```

## Task 4: Require explicit reset before new review prepare

**Files:**
- Modify: `runtime/tools/review_session_runtime.py`
- Test: `tests/review/test_adversarial_review_runtime.py`

- [ ] **Step 1: Write failing prepare behavior test**

Add this test to `tests/review/test_adversarial_review_runtime.py`:

```python
from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff, reset_review_cycle
```

```python
def test_prepare_review_cycle_requires_explicit_reset_for_stale_active_cycle(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_reviewer_receipt(stage_dir)
    _write_text(stage_dir / "author" / "formal" / "mandate.md", "changed after prepare\n")

    with pytest.raises(ValueError) as exc_info:
        prepare_review_cycle_for_handoff(
            cwd=tmp_path,
            explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
            reviewer_identity="reviewer-agent",
            reviewer_session_id="review-session-2",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-2",
            host="codex",
        )

    assert "STALE_REVIEW_EVIDENCE" in str(exc_info.value)
    assert "qros-review-cycle reset --archive-stale-cycle" in str(exc_info.value)

    reset_payload = reset_review_cycle(stage_dir=stage_dir, reason="stale")
    assert reset_payload["archived_paths"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py::test_prepare_review_cycle_requires_explicit_reset_for_stale_active_cycle -v
```

Expected: FAIL because `_archive_if_stale_or_closed()` currently auto-archives stale cycles.

- [ ] **Step 3: Replace auto-archive with hard failure**

In `runtime/tools/review_session_runtime.py`, change `_archive_if_stale_or_closed()` to `_assert_no_active_stale_or_closed_cycle()`:

```python
def _assert_no_active_stale_or_closed_cycle(stage_dir: Path, *, current_digest: str) -> None:
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    if not request_path.exists():
        return

    request_payload = load_adversarial_review_request(request_path)
    state_path = review_runtime_state_path(stage_dir)
    state_payload = load_review_runtime_state(state_path) if state_path.exists() else None
    bound_digest = state_payload.get("review_bound_author_digest") if state_payload else None
    if bound_digest is None:
        bound_digest = current_digest

    closure_exists = (_review_closure_path(stage_dir, "stage_completion_certificate.yaml")).exists()
    proof_chain_error = _review_proof_chain_error(stage_dir)
    if bound_digest == current_digest and not closure_exists and proof_chain_error is None:
        raise ValueError(
            f"active review cycle {request_payload['review_cycle_id']} is still in progress; "
            "start a new review only after it closes or run qros-review-cycle reset --archive-stale-cycle"
        )

    raise ValueError(
        f"STALE_REVIEW_EVIDENCE: active review cycle {request_payload['review_cycle_id']} is stale or closed; "
        "run qros-review-cycle reset --archive-stale-cycle before preparing a fresh reviewer run"
    )
```

Update `_prepare_review_cycle()`:

```python
    _assert_no_active_stale_or_closed_cycle(stage_dir, current_digest=current_digest)
    archived_paths: list[str] = []
```

- [ ] **Step 4: Keep reset command as the only archiver**

Ensure `reset_review_cycle()` still calls `archive_active_review_cycle()` and returns:

```python
"next_action": "run qros-review-cycle prepare and request a fresh reviewer run"
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py runtime/scripts/review_cycle.py -q
```

Expected: pytest ignores the script path if not a test file; if collection errors, rerun:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_session_runtime.py tests/review/test_adversarial_review_runtime.py
git commit -m "feat: require explicit reset for stale review cycles"
```

## Task 5: Full verification and docs alignment

**Files:**
- Modify if needed: `docs/guides/qros-review-shared-protocol.md`
- Verify: `docs/superpowers/specs/2026-05-12-reviewer-independence-runtime-guard-design.md`

- [ ] **Step 1: Check shared protocol mentions the new hard-fail behavior**

Run:

```bash
rg -n "STALE_REVIEW_EVIDENCE|CLOSURE_PROJECTION_DRIFT|REVIEWER_WRITE_SCOPE_VIOLATION|reset --archive-stale-cycle" docs/guides/qros-review-shared-protocol.md docs/superpowers/specs/2026-05-12-reviewer-independence-runtime-guard-design.md
```

Expected: the spec contains all codes; shared protocol may not. If shared protocol lacks them, update it with this concise paragraph under "执行门禁":

```markdown
如果 `author/formal/*` 在 active review cycle 之后发生变化，已有 raw findings、
canonical result、audit 和 closure 都必须视为 stale。runtime 应以
`STALE_REVIEW_EVIDENCE` 阻断普通推进，并要求先运行
`qros-review-cycle reset --archive-stale-cycle`，再重新 prepare 和启动独立
reviewer。launcher 主线程不得手工改 `reviewer_findings.raw.yaml`、不得把
`PASS` 改成 `CLOSURE_READY_PASS`、不得复用旧 reviewer 结论证明新 author outputs。
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/review/test_review_result_writer.py tests/review/test_review_runtime_state.py tests/review/test_adversarial_review_runtime.py tests/session/test_lineage_lock_session_status.py
```

Expected: PASS.

- [ ] **Step 3: Run smoke and full-smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: both PASS. These are required because the change touches review/session/progress semantics.

- [ ] **Step 4: Commit verification/doc changes**

```bash
git add docs/guides/qros-review-shared-protocol.md
git commit -m "docs: document stale review evidence guard"
```

If the shared protocol already contains the new behavior and no docs changed, skip this commit.

## Self-Review Checklist

- Spec coverage:
  - Active cycle binding: Tasks 1 and 2.
  - Current author digest binding: Task 1.
  - Closer-owned canonical files: Task 2.
  - Closed cycle integrity: Task 3.
  - Result write scope: Task 3.
  - Explicit reset recovery: Task 4.
  - Verification and docs: Task 5.
- Placeholder scan: no task uses placeholder markers or unspecified error handling.
- Type consistency:
  - Reason codes are string constants in `protected_state_guard.py`.
  - Raw findings schema uses `review_cycle_id`, `reviewer_agent_id`, and legal `review_loop_outcome`.
  - Recovery command consistently uses `qros-review-cycle reset --archive-stale-cycle`.
