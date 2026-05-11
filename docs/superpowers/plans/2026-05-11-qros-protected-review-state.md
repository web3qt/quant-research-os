# QROS Protected Review State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Block manual adjustment of QROS protected governance state by validating runtime-owned review state, receipt-bound reviewer findings, and digest cache trust before review/session/progress advancement.

**Architecture:** Add a focused `protected_state_guard` module under `runtime/tools/review_skillgen/` and keep the existing lineage immutable ledger as the upstream-artifact authority. Integrate the guard into review preflight, review cycle preparation, review closure, stage entry, progress/session status, and expose explicit validate/reset commands so recovery archives stale cycles instead of editing YAML.

**Tech Stack:** Python 3.13, PyYAML, pytest, existing QROS runtime scripts and shell wrappers.

---

## File Structure

- Create `runtime/tools/review_skillgen/protected_state_guard.py`
  - Owns `ProtectedStateError`, protected-state reason codes, projection validation, fresh digest validation, and reset helpers.
- Modify `runtime/tools/review_skillgen/review_runtime_state.py`
  - Add fresh digest recomputation that bypasses `materialization_digest_ledger.yaml`.
- Modify `runtime/tools/review_skillgen/review_result_writer.py`
  - Require raw reviewer findings to include current-cycle binding fields before canonicalization.
- Modify `runtime/tools/review_skillgen/protocol_validator.py`
  - Pass current author digest into result canonicalization and keep write-scope audit after canonical result materialization.
- Modify `runtime/tools/review_skillgen/review_preflight.py`
  - Run protected-state guard after lineage lock validation and before normal deterministic checks.
- Modify `runtime/tools/review_session_runtime.py`
  - Run protected-state guard in `prepare`; add explicit reset API.
- Modify `runtime/tools/review_skillgen/review_engine.py`
  - Run protected-state guard before closure and use fresh digest when checking receipt-bound author outputs.
- Modify `runtime/tools/stage_entry_guard.py`, `runtime/tools/progress_runtime.py`, and `runtime/tools/research_session.py`
  - Surface protected-state failures as integrity blocks.
- Modify `runtime/scripts/review_cycle.py`
  - Add `validate` and `reset --archive-stale-cycle` subcommands.
- Add tests in `tests/review/test_protected_state_guard.py`, extend `tests/review/test_review_result_writer.py`, `tests/review/test_review_cycle_prepare.py`, and `tests/review/test_adversarial_review_runtime.py`.
- Update review skill prompt generation and active review skill text to require the new raw findings binding fields.

---

### Task 1: Add Fresh Author Digest API

**Files:**
- Modify: `runtime/tools/review_skillgen/review_runtime_state.py`
- Test: `tests/review/test_review_runtime_state.py`

- [ ] **Step 1: Write failing test for cache bypass**

Append this test to `tests/review/test_review_runtime_state.py`:

```python
def test_compute_author_materialization_digest_fresh_bypasses_corrupt_cache(tmp_path: Path) -> None:
    stage_dir = tmp_path / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "research_route.yaml").write_text("route: first\n", encoding="utf-8")
    (formal_dir / "program_execution_manifest.json").write_text("{}\n", encoding="utf-8")

    cached = review_runtime_state.compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    ledger_path = stage_dir / "review" / "state" / "materialization_digest_ledger.yaml"
    ledger_text = ledger_path.read_text(encoding="utf-8")
    ledger_path.write_text(ledger_text.replace(cached, "0" * 64), encoding="utf-8")

    fresh = review_runtime_state.compute_author_materialization_digest_fresh(
        artifact_root=formal_dir,
        required_outputs=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert fresh == cached
    assert "0" * 64 in ledger_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run failing test**

Run: `python -m pytest tests/review/test_review_runtime_state.py::test_compute_author_materialization_digest_fresh_bypasses_corrupt_cache -q`

Expected: FAIL with `AttributeError: module 'runtime.tools.review_skillgen.review_runtime_state' has no attribute 'compute_author_materialization_digest_fresh'`.

- [ ] **Step 3: Implement fresh digest function**

Add this function below `compute_author_materialization_digest` in `runtime/tools/review_skillgen/review_runtime_state.py`:

```python
def compute_author_materialization_digest_fresh(
    *,
    artifact_root: Path,
    required_outputs: Sequence[str],
    required_provenance_paths: Sequence[str] = ("program_execution_manifest.json",),
) -> str:
    artifact_root = artifact_root.resolve()
    parts: list[bytes] = []
    for name in list(required_outputs) + list(required_provenance_paths):
        target = artifact_root / name
        parts.extend(
            [
                name.encode("utf-8"),
                b"\0",
                _path_digest(target, root=artifact_root, ledger=None).encode("utf-8"),
                b"\0",
            ]
        )
    return _digest_bytes(parts)
```

- [ ] **Step 4: Run focused test**

Run: `python -m pytest tests/review/test_review_runtime_state.py::test_compute_author_materialization_digest_fresh_bypasses_corrupt_cache -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add runtime/tools/review_skillgen/review_runtime_state.py tests/review/test_review_runtime_state.py
git commit -m "feat: add fresh author digest calculation"
```

---

### Task 2: Add Protected State Guard Module

**Files:**
- Create: `runtime/tools/review_skillgen/protected_state_guard.py`
- Test: `tests/review/test_protected_state_guard.py`

- [ ] **Step 1: Write failing guard tests**

Create `tests/review/test_protected_state_guard.py`:

```python
from pathlib import Path

import pytest
import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import ensure_adversarial_review_request
from runtime.tools.review_skillgen.protected_state_guard import (
    PROTECTED_STATE_DRIFT,
    REVIEW_STATE_PROJECTION_DRIFT,
    REVIEWER_FINDINGS_UNBOUND,
    ProtectedStateError,
    assert_protected_review_state_intact,
)
from runtime.tools.review_skillgen.review_runtime_state import compute_author_materialization_digest, write_review_runtime_state


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _stage(tmp_path: Path) -> tuple[Path, Path, dict[str, object], str]:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    _write(formal_dir / "research_route.yaml", "route: csf\n")
    _write(formal_dir / "program_execution_manifest.json", "{}\n")
    request = ensure_adversarial_review_request(
        stage_dir,
        lineage_id="btc_alt",
        stage="mandate",
        author_identity="author-1",
        author_session_id="session-1",
        required_program_dir="programs/mandate",
        required_program_entrypoint="run.py",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        program_hash="abc123",
        stage_invoked_at="2026-05-11T00:00:00Z",
    )
    digest = compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    return lineage_root, stage_dir, request, digest


def test_guard_rejects_closed_state_without_closure(tmp_path: Path) -> None:
    lineage_root, stage_dir, request, digest = _stage(tmp_path)
    write_review_runtime_state(
        stage_dir,
        review_state="review_closed_pass",
        active_review_cycle_id=str(request["review_cycle_id"]),
        review_requested_at="2026-05-11T00:00:00Z",
        review_bound_author_digest=digest,
        reviewer_identity="reviewer-1",
        reviewer_session_id="review-session-1",
        last_review_verdict="PASS",
        closure_written_at="2026-05-11T00:01:00Z",
    )

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=["research_route.yaml"],
            required_provenance_paths=["program_execution_manifest.json"],
            allow_missing_state=True,
        )

    assert exc_info.value.reason_code == REVIEW_STATE_PROJECTION_DRIFT
    assert "review_closed_pass" in str(exc_info.value)


def test_guard_rejects_state_bound_to_stale_author_digest(tmp_path: Path) -> None:
    lineage_root, stage_dir, request, digest = _stage(tmp_path)
    write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id=str(request["review_cycle_id"]),
        review_requested_at="2026-05-11T00:00:00Z",
        review_bound_author_digest=digest,
        reviewer_identity="reviewer-1",
        reviewer_session_id="review-session-1",
    )
    _write(stage_dir / "author" / "formal" / "research_route.yaml", "route: changed\n")

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=["research_route.yaml"],
            required_provenance_paths=["program_execution_manifest.json"],
            allow_missing_state=True,
        )

    assert exc_info.value.reason_code == REVIEW_STATE_PROJECTION_DRIFT
    assert "review_bound_author_digest" in str(exc_info.value)


def test_guard_rejects_raw_findings_without_receipt(tmp_path: Path) -> None:
    lineage_root, stage_dir, _request, _digest = _stage(tmp_path)
    _write(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        yaml.safe_dump(
            {
                "review_cycle_id": "bad",
                "reviewer_agent_id": "reviewer-1",
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
            required_outputs=["research_route.yaml"],
            required_provenance_paths=["program_execution_manifest.json"],
            allow_missing_state=True,
        )

    assert exc_info.value.reason_code == REVIEWER_FINDINGS_UNBOUND
```

- [ ] **Step 2: Run tests and verify module import failure**

Run: `python -m pytest tests/review/test_protected_state_guard.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'runtime.tools.review_skillgen.protected_state_guard'`.

- [ ] **Step 3: Implement protected state guard**

Create `runtime/tools/review_skillgen/protected_state_guard.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    REVIEWER_RECEIPT_FILENAME,
    load_adversarial_review_request,
    load_reviewer_receipt,
)
from runtime.tools.review_skillgen.review_result_writer import RAW_REVIEWER_FINDINGS_FILENAME
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest_fresh,
    load_review_runtime_state,
    review_runtime_state_path,
)


PROTECTED_STATE_DRIFT = "PROTECTED_STATE_DRIFT"
REVIEW_STATE_PROJECTION_DRIFT = "REVIEW_STATE_PROJECTION_DRIFT"
REVIEWER_FINDINGS_UNBOUND = "REVIEWER_FINDINGS_UNBOUND"
MATERIALIZATION_CACHE_UNTRUSTED = "MATERIALIZATION_CACHE_UNTRUSTED"
_CLOSURE_FILES = (
    "latest_review_pack.yaml",
    "stage_completion_certificate.yaml",
    "stage_gate_review.yaml",
)


@dataclass(frozen=True)
class ProtectedStateError(RuntimeError):
    reason_code: str
    protected_path: str
    message: str
    next_action: str

    def __str__(self) -> str:
        return f"{self.reason_code}: {self.message} Next action: {self.next_action}"

    def to_payload(self) -> dict[str, str]:
        return {
            "reason_code": self.reason_code,
            "protected_path": self.protected_path,
            "message": self.message,
            "next_action": self.next_action,
        }


def _raise(reason_code: str, path: Path, message: str) -> None:
    raise ProtectedStateError(
        reason_code=reason_code,
        protected_path=path.as_posix(),
        message=message,
        next_action="Run qros-review-cycle reset --archive-stale-cycle, then request a fresh reviewer run.",
    )


def _load_raw_findings(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        _raise(REVIEWER_FINDINGS_UNBOUND, path, "raw reviewer findings must load to a mapping")
    return payload


def _validate_runtime_state(
    *,
    stage_dir: Path,
    required_outputs: Sequence[str],
    required_provenance_paths: Sequence[str],
    allow_missing_state: bool,
) -> None:
    state_path = review_runtime_state_path(stage_dir)
    request_path = stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    receipt_path = stage_dir / "review" / "request" / REVIEWER_RECEIPT_FILENAME
    if not state_path.exists():
        if allow_missing_state:
            return
        _raise(REVIEW_STATE_PROJECTION_DRIFT, state_path, "review runtime state is missing")

    state = load_review_runtime_state(state_path)
    request = load_adversarial_review_request(request_path) if request_path.exists() else {}
    active_cycle = state.get("active_review_cycle_id")
    request_cycle = request.get("review_cycle_id")
    if active_cycle and request_cycle and active_cycle != request_cycle:
        _raise(
            REVIEW_STATE_PROJECTION_DRIFT,
            state_path,
            f"active_review_cycle_id {active_cycle} does not match request {request_cycle}",
        )
    if state["review_state"] == "review_in_progress" and (not request_path.exists() or not receipt_path.exists()):
        _raise(
            REVIEW_STATE_PROJECTION_DRIFT,
            state_path,
            "review_in_progress requires active adversarial_review_request.yaml and reviewer_receipt.yaml",
        )
    current_digest = compute_author_materialization_digest_fresh(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=required_outputs,
        required_provenance_paths=required_provenance_paths,
    )
    bound_digest = state.get("review_bound_author_digest")
    if bound_digest and bound_digest != current_digest:
        _raise(
            REVIEW_STATE_PROJECTION_DRIFT,
            state_path,
            "review_bound_author_digest does not match current author/formal digest",
        )
    if state["review_state"].startswith("review_closed"):
        missing = [name for name in _CLOSURE_FILES if not (stage_dir / "review" / "closure" / name).exists()]
        if missing:
            _raise(
                REVIEW_STATE_PROJECTION_DRIFT,
                state_path,
                f"{state['review_state']} requires closure artifacts; missing: {', '.join(missing)}",
            )


def _validate_raw_findings(stage_dir: Path) -> None:
    raw_path = stage_dir / "review" / "result" / RAW_REVIEWER_FINDINGS_FILENAME
    if not raw_path.exists():
        return
    receipt_path = stage_dir / "review" / "request" / REVIEWER_RECEIPT_FILENAME
    request_path = stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    if not receipt_path.exists() or not request_path.exists():
        _raise(REVIEWER_FINDINGS_UNBOUND, raw_path, "raw findings exist without active request and receipt")
    raw = _load_raw_findings(raw_path)
    receipt = load_reviewer_receipt(receipt_path)
    request = load_adversarial_review_request(request_path)
    if raw.get("review_cycle_id") != request.get("review_cycle_id"):
        _raise(REVIEWER_FINDINGS_UNBOUND, raw_path, "raw findings review_cycle_id does not match active request")
    if raw.get("reviewer_agent_id") != receipt.get("reviewer_agent_id"):
        _raise(REVIEWER_FINDINGS_UNBOUND, raw_path, "raw findings reviewer_agent_id does not match receipt")


def assert_protected_review_state_intact(
    *,
    stage_dir: Path,
    lineage_root: Path,
    required_outputs: Sequence[str],
    required_provenance_paths: Sequence[str],
    allow_missing_state: bool = True,
) -> None:
    del lineage_root
    stage_dir = stage_dir.resolve()
    _validate_runtime_state(
        stage_dir=stage_dir,
        required_outputs=required_outputs,
        required_provenance_paths=required_provenance_paths,
        allow_missing_state=allow_missing_state,
    )
    _validate_raw_findings(stage_dir)
```

- [ ] **Step 4: Run guard tests**

Run: `python -m pytest tests/review/test_protected_state_guard.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add runtime/tools/review_skillgen/protected_state_guard.py tests/review/test_protected_state_guard.py
git commit -m "feat: add protected review state guard"
```

---

### Task 3: Bind Raw Reviewer Findings to Receipt

**Files:**
- Modify: `runtime/tools/review_skillgen/review_result_writer.py`
- Modify: `runtime/tools/review_session_runtime.py`
- Test: `tests/review/test_review_result_writer.py`

- [ ] **Step 1: Update tests for required raw binding fields**

In `tests/review/test_review_result_writer.py`, update raw findings payloads that should pass to include:

```python
"review_cycle_id": receipt_payload["review_cycle_id"],
"reviewer_agent_id": receipt_payload["reviewer_agent_id"],
```

Add a new rejection test:

```python
def test_ensure_runtime_review_result_rejects_raw_findings_with_mismatched_cycle(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc" / "01_mandate"
    request_payload = _write_review_request(stage_dir)
    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    raw_path = stage_dir / "review" / "result" / "reviewer_findings.raw.yaml"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        yaml.safe_dump(
            {
                "review_cycle_id": "wrong-cycle",
                "reviewer_agent_id": receipt_payload["reviewer_agent_id"],
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="review_cycle_id"):
        ensure_runtime_review_result(
            review_result_dir=stage_dir / "review" / "result",
            request_payload=request_payload,
            receipt_payload=receipt_payload,
            runtime_identity=ReviewerRuntimeIdentity(
                reviewer_identity="reviewer",
                reviewer_role="reviewer",
                reviewer_session_id="reviewer-session",
                reviewer_mode="adversarial",
            ),
        )
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/review/test_review_result_writer.py -q`

Expected: FAIL because `_load_raw_reviewer_findings` does not require `review_cycle_id` or `reviewer_agent_id`.

- [ ] **Step 3: Implement raw binding validation**

In `runtime/tools/review_skillgen/review_result_writer.py`, add:

```python
def _require_raw_string(payload: dict[str, Any], key: str, *, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: {key} must be a non-empty string")
    return value.strip()
```

Then update `_load_raw_reviewer_findings` to include:

```python
return {
    "review_cycle_id": _require_raw_string(payload, "review_cycle_id", path=path),
    "reviewer_agent_id": _require_raw_string(payload, "reviewer_agent_id", path=path),
    "review_loop_outcome": outcome,
    ...
}
```

In `ensure_runtime_review_result`, after loading `raw_payload`, add:

```python
if raw_payload["review_cycle_id"] != request_payload["review_cycle_id"]:
    raise ValueError(f"{raw_path}: review_cycle_id does not match adversarial_review_request.yaml")
if raw_payload["reviewer_agent_id"] != receipt_payload["reviewer_agent_id"]:
    raise ValueError(f"{raw_path}: reviewer_agent_id does not match reviewer_receipt.yaml")
```

- [ ] **Step 4: Update reviewer handoff prompt**

In `_reviewer_handoff_prompt` in `runtime/tools/review_session_runtime.py`, change the raw fields section to include the binding fields first:

```python
"Write reviewer_findings.raw.yaml with top-level fields:",
f"review_cycle_id: {payload['review_cycle_id']}",
f"reviewer_agent_id: {payload['receipt_payload']['reviewer_agent_id']}",
"review_loop_outcome",
"blocking_findings",
"reservation_findings",
"info_findings",
"residual_risks",
```

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/review/test_review_result_writer.py tests/review/test_review_cycle_prepare.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add runtime/tools/review_skillgen/review_result_writer.py runtime/tools/review_session_runtime.py tests/review/test_review_result_writer.py tests/review/test_review_cycle_prepare.py
git commit -m "feat: bind raw reviewer findings to receipt"
```

---

### Task 4: Integrate Guard into Review Preflight and Closure

**Files:**
- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Modify: `runtime/tools/review_skillgen/review_engine.py`
- Modify: `runtime/tools/review_skillgen/protocol_validator.py`
- Test: `tests/review/test_adversarial_review_runtime.py`
- Test: `tests/review/test_review_preflight.py`

- [ ] **Step 1: Add failing preflight test for stale state**

Add to `tests/review/test_review_preflight.py`:

```python
def test_review_preflight_rejects_stale_review_runtime_state(tmp_path: Path) -> None:
    stage_dir, lineage_root = _build_reviewable_stage(tmp_path, stage="mandate")
    payload = run_review_preflight(explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})
    assert payload["status"] == "PASS"

    state_path = stage_dir / "review" / "state" / "review_runtime_state.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        yaml.safe_dump(
            {
                "review_state": "review_closed_pass",
                "active_review_cycle_id": "manual-cycle",
                "review_bound_author_digest": "0" * 64,
                "last_review_verdict": "PASS",
                "closure_written_at": "2026-05-11T00:00:00Z",
                "updated_at": "2026-05-11T00:00:00Z",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ProtectedStateError, match="REVIEW_STATE_PROJECTION_DRIFT"):
        run_review_preflight(explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})
```

- [ ] **Step 2: Run failing test**

Run: `python -m pytest tests/review/test_review_preflight.py::test_review_preflight_rejects_stale_review_runtime_state -q`

Expected: FAIL because `run_review_preflight` does not call `assert_protected_review_state_intact`.

- [ ] **Step 3: Integrate guard in preflight**

In `runtime/tools/review_skillgen/review_preflight.py`, import:

```python
from runtime.tools.review_skillgen.protected_state_guard import assert_protected_review_state_intact
```

After `stage_contract = gates["stages"][stage]`, call:

```python
assert_protected_review_state_intact(
    stage_dir=stage_dir,
    lineage_root=lineage_root,
    required_outputs=stage_contract.get("required_outputs", []),
    required_provenance_paths=["program_execution_manifest.json"],
    allow_missing_state=True,
)
```

- [ ] **Step 4: Guard closure path**

In `runtime/tools/review_skillgen/review_engine.py`, import the guard and call it after loading `stage_contract` and before `load_and_validate_protocol`:

```python
assert_protected_review_state_intact(
    stage_dir=stage_dir,
    lineage_root=lineage_root,
    required_outputs=stage_contract.get("required_outputs", []),
    required_provenance_paths=["program_execution_manifest.json"],
    allow_missing_state=False,
)
```

Then compute `author_digest` with `compute_author_materialization_digest_fresh` for the protected-state comparison path. Keep the existing cached `compute_author_materialization_digest` only where runtime intentionally refreshes cache after validation.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/review/test_review_preflight.py tests/review/test_adversarial_review_runtime.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add runtime/tools/review_skillgen/review_preflight.py runtime/tools/review_skillgen/review_engine.py runtime/tools/review_skillgen/protocol_validator.py tests/review/test_review_preflight.py tests/review/test_adversarial_review_runtime.py
git commit -m "feat: guard protected review state before review"
```

---

### Task 5: Add Review Cycle Validate and Reset Commands

**Files:**
- Modify: `runtime/tools/review_session_runtime.py`
- Modify: `runtime/scripts/review_cycle.py`
- Test: `tests/review/test_review_cycle_prepare.py`

- [ ] **Step 1: Write failing CLI tests**

Append to `tests/review/test_review_cycle_prepare.py`:

```python
def test_review_cycle_reset_archives_stale_cycle(tmp_path: Path) -> None:
    stage_dir, lineage_root = _build_review_ready_stage(tmp_path)
    payload = start_review_cycle(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="reviewer",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-agent",
    )
    assert (stage_dir / "review" / "request" / "reviewer_receipt.yaml").exists()

    reset_payload = reset_review_cycle(
        stage_dir=stage_dir,
        review_cycle_id=payload["review_cycle_id"],
        reason="stale",
    )

    assert reset_payload["archived_paths"]
    assert not (stage_dir / "review" / "request" / "reviewer_receipt.yaml").exists()
    assert reset_payload["next_action"] == "run qros-review-cycle prepare and request a fresh reviewer run"
```

- [ ] **Step 2: Run failing test**

Run: `python -m pytest tests/review/test_review_cycle_prepare.py::test_review_cycle_reset_archives_stale_cycle -q`

Expected: FAIL with `NameError` or import failure for `reset_review_cycle`.

- [ ] **Step 3: Implement reset helper**

In `runtime/tools/review_session_runtime.py`, add:

```python
def reset_review_cycle(
    *,
    stage_dir: Path,
    review_cycle_id: str | None = None,
    reason: str = "stale",
) -> dict[str, Any]:
    stage_dir = stage_dir.resolve()
    if review_cycle_id is None:
        request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
        if not request_path.exists():
            return {
                "stage_dir": str(stage_dir),
                "archived_paths": [],
                "next_action": "run qros-review-cycle prepare and request a fresh reviewer run",
            }
        request_payload = load_adversarial_review_request(request_path)
        review_cycle_id = request_payload["review_cycle_id"]
    archived_paths = archive_active_review_cycle(
        stage_dir,
        review_cycle_id=review_cycle_id,
        reason=reason,
    )
    return {
        "stage_dir": str(stage_dir),
        "review_cycle_id": review_cycle_id,
        "archived_paths": archived_paths,
        "next_action": "run qros-review-cycle prepare and request a fresh reviewer run",
    }
```

- [ ] **Step 4: Add validate/reset CLI subcommands**

In `runtime/scripts/review_cycle.py`, add imports:

```python
from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff, reset_review_cycle
from runtime.tools.review_skillgen.protected_state_guard import assert_protected_review_state_intact
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
```

Add subparsers:

```python
validate = subparsers.add_parser("validate", help="Validate protected review state without writing changes.")
validate.add_argument("--stage-dir", type=Path, required=True)
validate.add_argument("--lineage-root", type=Path, required=True)
validate.add_argument("--json", action="store_true")

reset = subparsers.add_parser("reset", help="Archive stale active review cycle.")
reset.add_argument("--stage-dir", type=Path, required=True)
reset.add_argument("--lineage-root", type=Path, required=True)
reset.add_argument("--archive-stale-cycle", action="store_true", required=True)
reset.add_argument("--json", action="store_true")
```

For `validate`, reuse `run_review_preflight` with explicit context. For `reset`, call `reset_review_cycle(stage_dir=args.stage_dir, reason="stale")`.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/review/test_review_cycle_prepare.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add runtime/tools/review_session_runtime.py runtime/scripts/review_cycle.py tests/review/test_review_cycle_prepare.py
git commit -m "feat: add protected review state reset command"
```

---

### Task 6: Surface Protected-State Blocks in Session and Progress

**Files:**
- Modify: `runtime/tools/stage_entry_guard.py`
- Modify: `runtime/tools/progress_runtime.py`
- Modify: `runtime/tools/research_session.py`
- Test: `tests/session/test_lineage_lock_session_status.py`
- Test: `tests/session/test_research_session_runtime.py`

- [ ] **Step 1: Add failing progress/session tests**

In `tests/session/test_lineage_lock_session_status.py`, add:

```python
def test_progress_surfaces_protected_review_state_drift(tmp_path: Path) -> None:
    outputs_root, lineage_root, stage_dir = _build_review_pending_lineage(tmp_path)
    (stage_dir / "review" / "state").mkdir(parents=True)
    (stage_dir / "review" / "state" / "review_runtime_state.yaml").write_text(
        yaml.safe_dump(
            {
                "review_state": "review_closed_pass",
                "active_review_cycle_id": "manual-cycle",
                "review_bound_author_digest": "0" * 64,
                "last_review_verdict": "PASS",
                "closure_written_at": "2026-05-11T00:00:00Z",
                "updated_at": "2026-05-11T00:00:00Z",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert payload["gate_status"] == "PROTECTED_STATE_DRIFT"
    assert payload["blocking_reason_code"] == "REVIEW_STATE_PROJECTION_DRIFT"
    assert "qros-review-cycle reset --archive-stale-cycle" in payload["next_action"]
```

- [ ] **Step 2: Run failing test**

Run: `python -m pytest tests/session/test_lineage_lock_session_status.py::test_progress_surfaces_protected_review_state_drift -q`

Expected: FAIL because progress only surfaces `FROZEN_ARTIFACT_MUTATED`.

- [ ] **Step 3: Add status helper in research session**

In `runtime/tools/research_session.py`, add a helper next to `_lineage_lock_blocked_status`:

```python
def _protected_state_blocked_status(
    *,
    lineage_root: Path,
    lineage_mode: str,
    lineage_selection_reason: str,
    violation,
):
    return summarize_session_status(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        lineage_mode=lineage_mode,
        lineage_selection_reason=lineage_selection_reason,
        current_stage=detect_session_stage(lineage_root),
        current_route=current_research_route(lineage_root),
        artifacts_written=[],
        gate_status="PROTECTED_STATE_DRIFT",
        next_action=violation.next_action,
        why_now="Protected review state drift must be repaired before normal QROS workflow can continue.",
        open_risks=[str(violation)],
        factor_role=current_route_contract(lineage_root)["factor_role"],
        factor_structure=current_route_contract(lineage_root)["factor_structure"],
        portfolio_expression=current_route_contract(lineage_root)["portfolio_expression"],
        neutralization_policy=current_route_contract(lineage_root)["neutralization_policy"],
        blocking_reason=str(violation),
        runtime_blocking_reason_code_override=violation.reason_code,
        runtime_next_action_override=violation.next_action,
    )
```

- [ ] **Step 4: Catch protected-state errors in progress and stage entry**

In `runtime/tools/progress_runtime.py`, import `ProtectedStateError` and `_protected_state_blocked_status`, then catch it after lineage lock checks when review state snapshot or status derivation raises it.

In `runtime/tools/stage_entry_guard.py`, import `ProtectedStateError` and catch it like `FrozenArtifactMutationError`, with `current_active_skill="qros-research-session"` and `message=str(exc)`.

- [ ] **Step 5: Run focused session tests**

Run: `python -m pytest tests/session/test_lineage_lock_session_status.py tests/session/test_research_session_runtime.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add runtime/tools/research_session.py runtime/tools/progress_runtime.py runtime/tools/stage_entry_guard.py tests/session/test_lineage_lock_session_status.py tests/session/test_research_session_runtime.py
git commit -m "feat: surface protected state drift in session status"
```

---

### Task 7: Update Review Skill Text and Docs

**Files:**
- Modify: `skills/*/qros-*-review/SKILL.md` where generated review instructions mention raw findings fields
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `docs/superpowers/specs/2026-05-11-qros-protected-review-state-design.md` only if implementation naming changes
- Test: `tests/review/test_adversarial_review_skill_generation.py`
- Test: `tests/skills/test_tss_author_review_skills.py`

- [ ] **Step 1: Update generated prompt expectations**

In review skill generation tests, require the raw findings instruction to include:

```text
review_cycle_id
reviewer_agent_id
review_loop_outcome
```

- [ ] **Step 2: Run failing documentation/skill tests**

Run: `python -m pytest tests/review/test_adversarial_review_skill_generation.py tests/skills/test_tss_author_review_skills.py -q`

Expected: FAIL where generated/active skill text lacks the new binding fields.

- [ ] **Step 3: Update skill generation source and regenerated active skills**

Find the source template with:

```bash
rg -n "reviewer_findings.raw.yaml|review_loop_outcome" runtime/tools skills
```

Update the template and active skill text so reviewer handoff requires:

```text
review_cycle_id: copy the literal review cycle value printed in the reviewer handoff
reviewer_agent_id: copy the literal reviewer agent id printed in the reviewer handoff
review_loop_outcome: one of FIX_REQUIRED, CLOSURE_READY_PASS, CLOSURE_READY_CONDITIONAL_PASS, CLOSURE_READY_PASS_FOR_RETRY, CLOSURE_READY_RETRY, CLOSURE_READY_NO_GO, CLOSURE_READY_CHILD_LINEAGE
blocking_findings: []
reservation_findings: []
info_findings: []
residual_risks: []
```

- [ ] **Step 4: Update shared protocol doc**

In `docs/guides/qros-review-shared-protocol.md`, add a short section:

```markdown
### Raw Reviewer Findings Binding

`review/result/reviewer_findings.raw.yaml` is reviewer-owned evidence for the
active review cycle. It must include `review_cycle_id` and `reviewer_agent_id`
from `review/request/reviewer_receipt.yaml`. QROS rejects raw findings that do
not bind to the active receipt or that target stale author outputs.
```

- [ ] **Step 5: Run docs/skill tests**

Run: `python -m pytest tests/review/test_adversarial_review_skill_generation.py tests/skills/test_tss_author_review_skills.py tests/docs/test_install_docs.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add runtime/tools skills docs/guides/qros-review-shared-protocol.md tests/review/test_adversarial_review_skill_generation.py tests/skills/test_tss_author_review_skills.py tests/docs/test_install_docs.py
git commit -m "docs: document protected reviewer findings binding"
```

---

### Task 8: Final Verification

**Files:**
- No code changes unless verification reveals a defect.

- [ ] **Step 1: Run focused review/runtime tests**

Run:

```bash
python -m pytest tests/review/test_review_runtime_state.py tests/review/test_protected_state_guard.py tests/review/test_review_result_writer.py tests/review/test_review_cycle_prepare.py tests/review/test_adversarial_review_runtime.py tests/runtime/test_lineage_lock_ledger.py -q
```

Expected: PASS.

- [ ] **Step 2: Run docs/bootstrap checks**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [ ] **Step 3: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 4: Run full-smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS.

- [ ] **Step 5: Check worktree**

Run: `git status --short`

Expected: no uncommitted changes.

---

## Self-Review

- Spec coverage: Phase 1 protected files, guard entrypoints, cache downgrade, receipt-bound raw findings, explicit reset/validate recovery, failure codes, docs, and verification are covered. Phase 2 event log is intentionally excluded from implementation tasks.
- Placeholder scan: no placeholder tokens or undefined implementation phases are required to complete this plan.
- Type consistency: the plan uses `Path`, `Sequence[str]`, `ProtectedStateError`, `assert_protected_review_state_intact`, `compute_author_materialization_digest_fresh`, and existing request/receipt loaders consistently across tasks.
