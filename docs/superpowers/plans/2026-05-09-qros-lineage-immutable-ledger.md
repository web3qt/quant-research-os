# QROS Lineage Immutable Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lineage-level immutable ledger that blocks mutation of already reviewed formal/closure artifacts while preserving current reviewer write-scope audit behavior.

**Architecture:** Create a focused `runtime/tools/lineage_lock_ledger.py` module for ledger write, validation, and error formatting. Integrate it at closure write time and at workflow entrypoints (`qros-session`, `qros-progress`, stage entry, review preflight, review cycle prepare, and `qros-review`) so frozen upstream mutations hard-block before downstream digests can normalize them.

**Tech Stack:** Python 3.13, PyYAML, pytest, existing QROS runtime modules.

---

### Task 1: Add Ledger Runtime Module

**Files:**
- Create: `runtime/tools/lineage_lock_ledger.py`
- Test: `tests/runtime/test_lineage_lock_ledger.py`

- [ ] **Step 1: Write failing unit tests**

Create tests covering first lock write, idempotent re-lock, mutation rejection, and validation failure payload:

```python
from pathlib import Path

import pytest
import yaml

from runtime.tools.lineage_lock_ledger import (
    FROZEN_ARTIFACT_MUTATED,
    FrozenArtifactMutationError,
    assert_lineage_locks_intact,
    lock_reviewed_stage,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_lock_reviewed_stage_writes_author_and_closure_files(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    _write(stage_dir / "author" / "formal" / "research_route.yaml", "research_route: cross_sectional_factor\n")
    _write(stage_dir / "author" / "formal" / "program_execution_manifest.json", "{}\n")
    _write(stage_dir / "review" / "closure" / "stage_gate_review.yaml", "final_verdict: PASS\n")
    _write(stage_dir / "review" / "closure" / "stage_completion_certificate.yaml", "final_verdict: PASS\n")
    _write(stage_dir / "review" / "closure" / "latest_review_pack.yaml", "final_verdict: PASS\n")

    payload = lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T00:00:00+00:00",
    )

    assert payload["ledger_version"] == 1
    files = payload["locked_stages"]["mandate"]["files"]
    assert [item["path"] for item in files] == [
        "01_mandate/author/formal/program_execution_manifest.json",
        "01_mandate/author/formal/research_route.yaml",
        "01_mandate/review/closure/latest_review_pack.yaml",
        "01_mandate/review/closure/stage_completion_certificate.yaml",
        "01_mandate/review/closure/stage_gate_review.yaml",
    ]


def test_lock_reviewed_stage_is_idempotent_when_digests_match(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    for rel in [
        "author/formal/research_route.yaml",
        "author/formal/program_execution_manifest.json",
        "review/closure/stage_gate_review.yaml",
        "review/closure/stage_completion_certificate.yaml",
        "review/closure/latest_review_pack.yaml",
    ]:
        _write(stage_dir / rel, f"{rel}\n")

    first = lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T00:00:00+00:00",
    )
    second = lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T01:00:00+00:00",
    )

    assert second == first


def test_lock_reviewed_stage_rejects_changed_locked_file(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    for rel in [
        "author/formal/research_route.yaml",
        "author/formal/program_execution_manifest.json",
        "review/closure/stage_gate_review.yaml",
        "review/closure/stage_completion_certificate.yaml",
        "review/closure/latest_review_pack.yaml",
    ]:
        _write(stage_dir / rel, f"{rel}\n")

    lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    _write(stage_dir / "author" / "formal" / "research_route.yaml", "changed\n")

    with pytest.raises(FrozenArtifactMutationError) as exc_info:
        assert_lineage_locks_intact(lineage_root)

    assert exc_info.value.reason_code == FROZEN_ARTIFACT_MUTATED
    assert exc_info.value.path == "01_mandate/author/formal/research_route.yaml"
    assert "Restore 01_mandate/author/formal/research_route.yaml" in exc_info.value.next_action
```

- [ ] **Step 2: Run tests and verify import failure**

Run: `python -m pytest tests/runtime/test_lineage_lock_ledger.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'runtime.tools.lineage_lock_ledger'`.

- [ ] **Step 3: Implement module**

Add `runtime/tools/lineage_lock_ledger.py` with:

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import yaml


LINEAGE_LOCK_LEDGER_FILENAME = "lineage_lock_ledger.yaml"
FROZEN_ARTIFACT_MUTATED = "FROZEN_ARTIFACT_MUTATED"
PASS_LIKE_FINAL_VERDICTS = {"PASS", "CONDITIONAL PASS", "GO", "PASS FOR RETRY", "RETRY"}
CLOSURE_FILENAMES = (
    "latest_review_pack.yaml",
    "stage_completion_certificate.yaml",
    "stage_gate_review.yaml",
)


@dataclass(frozen=True)
class FrozenArtifactMutationError(RuntimeError):
    lineage_id: str
    locked_stage: str
    path: str
    expected_sha256: str | None
    observed_sha256: str | None
    lock_reason: str

    @property
    def reason_code(self) -> str:
        return FROZEN_ARTIFACT_MUTATED

    @property
    def next_action(self) -> str:
        return (
            f"Frozen upstream artifact changed. Restore {self.path} to the locked version, "
            "or open a child lineage if this frozen fact change is intentional."
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "reason_code": self.reason_code,
            "lineage_id": self.lineage_id,
            "locked_stage": self.locked_stage,
            "path": self.path,
            "expected_sha256": self.expected_sha256,
            "observed_sha256": self.observed_sha256,
            "lock_reason": self.lock_reason,
            "next_action": self.next_action,
        }

    def __str__(self) -> str:
        return (
            f"{self.reason_code}: {self.path} changed for locked stage {self.locked_stage}; "
            f"expected={self.expected_sha256} observed={self.observed_sha256}. {self.next_action}"
        )
```

The module must also implement `ledger_path`, `load_lineage_lock_ledger`, `assert_lineage_locks_intact`, and `lock_reviewed_stage`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/runtime/test_lineage_lock_ledger.py -q`

Expected: PASS.

### Task 2: Lock Stage Closure Outputs

**Files:**
- Modify: `runtime/tools/review_skillgen/closure_writer.py`
- Modify: `tests/review/test_run_stage_review_script.py`

- [ ] **Step 1: Add failing closure test**

Extend `test_run_stage_review_script_creates_closure_artifacts` to assert the ledger exists and includes mandate formal/closure files:

```python
    ledger = yaml.safe_load((stage_dir.parent / "lineage_lock_ledger.yaml").read_text(encoding="utf-8"))
    locked = ledger["locked_stages"]["mandate"]["files"]
    locked_paths = {item["path"] for item in locked}
    assert "mandate/author/formal/research_route.yaml" in locked_paths
    assert "mandate/review/closure/stage_gate_review.yaml" in locked_paths
```

- [ ] **Step 2: Run failing test**

Run: `python -m pytest tests/review/test_run_stage_review_script.py::test_run_stage_review_script_creates_closure_artifacts -q`

Expected: FAIL because `lineage_lock_ledger.yaml` is missing.

- [ ] **Step 3: Integrate closure locking**

In `runtime/tools/review_skillgen/closure_writer.py`, import `lock_reviewed_stage` and call it after closure files and evaluator artifacts are written:

```python
from runtime.tools.lineage_lock_ledger import lock_reviewed_stage
```

```python
    review_scope = payload.get("review_scope", {})
    lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage=payload["stage"],
        review_cycle_id=str(payload.get("adversarial_review_result", {}).get("review_cycle_id", "")),
        final_verdict=str(payload["final_verdict"]),
        required_artifact_paths=review_scope.get("required_artifact_paths", []),
        required_provenance_paths=review_scope.get("required_provenance_paths", []),
    )
```

- [ ] **Step 4: Run closure test**

Run: `python -m pytest tests/review/test_run_stage_review_script.py::test_run_stage_review_script_creates_closure_artifacts -q`

Expected: PASS.

### Task 3: Block Review Entrypoints On Frozen Mutation

**Files:**
- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Modify: `runtime/tools/review_session_runtime.py`
- Modify: `runtime/tools/review_skillgen/review_engine.py`
- Test: `tests/review/test_lineage_lock_entrypoints.py`

- [ ] **Step 1: Write failing tests for preflight, prepare, and qros-review**

Create `tests/review/test_lineage_lock_entrypoints.py` using `_prepare_mandate_stage` from `tests/review/test_run_stage_review_script.py`, lock mandate once, mutate `author/formal/research_route.yaml`, then assert each entrypoint raises or exits with `FROZEN_ARTIFACT_MUTATED`.

- [ ] **Step 2: Run failing tests**

Run: `python -m pytest tests/review/test_lineage_lock_entrypoints.py -q`

Expected: FAIL because entrypoints do not validate the lineage ledger yet.

- [ ] **Step 3: Add validation calls**

Add this import in all three runtime files:

```python
from runtime.tools.lineage_lock_ledger import assert_lineage_locks_intact
```

Call `assert_lineage_locks_intact(lineage_root)` after context inference and before review/preflight/prepare work proceeds.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/review/test_lineage_lock_entrypoints.py -q`

Expected: PASS.

### Task 4: Surface Hard Block In Session And Progress

**Files:**
- Modify: `runtime/tools/progress_runtime.py`
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/tools/stage_entry_guard.py`
- Test: `tests/session/test_lineage_lock_session_status.py`

- [ ] **Step 1: Write failing tests**

Add tests that create a locked mandate, mutate `research_route.yaml`, and verify:

- `progress_status_payload` returns `blocking_reason_code == "FROZEN_ARTIFACT_MUTATED"`
- `run_research_session` returns `blocking_reason_code == "FROZEN_ARTIFACT_MUTATED"`
- `check_stage_entry_for_lineage` raises `StageEntryGuardError` with the same message

- [ ] **Step 2: Run failing tests**

Run: `python -m pytest tests/session/test_lineage_lock_session_status.py -q`

Expected: FAIL because session/progress/stage entry do not consult the ledger yet.

- [ ] **Step 3: Implement status helper**

In `runtime/tools/research_session.py`, import:

```python
from runtime.tools.lineage_lock_ledger import FrozenArtifactMutationError, assert_lineage_locks_intact
```

Add a small helper that builds a `SessionContext` hard block from `FrozenArtifactMutationError`, with:

```python
runtime_stage_status_override="blocked"
runtime_blocking_reason_code_override="FROZEN_ARTIFACT_MUTATED"
gate_status="FROZEN_ARTIFACT_MUTATED"
next_action=exc.next_action
```

Call it before writing any transition decisions or scaffolds.

- [ ] **Step 4: Integrate progress and stage entry**

In `progress_runtime.py`, catch the same violation and return a read-only blocked `SessionContext`.

In `stage_entry_guard.py`, call `assert_lineage_locks_intact(lineage_root)` before evaluating current stage; convert violations to `StageEntryGuardError`.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/session/test_lineage_lock_session_status.py -q`

Expected: PASS.

### Task 5: Documentation And Verification

**Files:**
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Test: focused tests from Tasks 1-4

- [ ] **Step 1: Update review protocol docs**

Add a short section explaining that `lineage_lock_ledger.yaml` protects already reviewed upstream artifacts and is separate from `reviewer_write_scope_audit.yaml`.

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/runtime/test_lineage_lock_ledger.py tests/review/test_lineage_lock_entrypoints.py tests/session/test_lineage_lock_session_status.py tests/review/test_run_stage_review_script.py::test_run_stage_review_script_creates_closure_artifacts -q
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
