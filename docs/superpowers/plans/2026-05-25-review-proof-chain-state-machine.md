# Review Proof Chain State Machine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a strict, receipt-bound, shared QROS review proof-chain state machine that removes mechanical review friction without allowing launcher self-review.

**Architecture:** Add shared review scope normalization and final review normalization modules, then route protocol validation, review projection, audit, and session status through those shared contracts. The raw reviewer-owned `review/final_review.yaml` remains immutable; runtime writes normalized shadow/result/audit/closure only after active receipt, scope, digest, and write-scope checks pass.

**Tech Stack:** Python 3.13, PyYAML, pytest, existing QROS runtime modules under `runtime/tools/review_skillgen/`.

---

## File Structure

- Create: `runtime/tools/review_skillgen/review_scope.py`
  - Owns normalized `ReviewScope`, path normalization, scope comparison, and digest input ordering.
- Create: `runtime/tools/review_skillgen/final_review_normalizer.py`
  - Owns strict receipt-bound final-review normalization and writes `review/result/final_review.normalized.yaml`.
- Modify: `runtime/tools/review_skillgen/review_runtime_state.py`
  - Uses normalized path order for cached and fresh author materialization digests.
- Modify: `runtime/tools/review_skillgen/protocol_validator.py`
  - Requires receipt for ordinary `review/final_review.yaml`, validates receipt-bound reviewer identity, normalizes final review, and projects result from request + receipt + normalized review.
- Modify: `runtime/tools/review_skillgen/review_engine.py`
  - Ensures `review/result` exists, writes canonical result, automatically runs and validates write-scope audit before closure.
- Modify: `runtime/tools/research_session.py`
  - Reports explicit proof-chain states such as `reviewer_unbound`, `review_format_invalid`, `review_scope_mismatch`, `author_outputs_stale`, and `reviewer_scope_violation`.
- Modify: `contracts/stages/workflow_stage_gates.yaml`
  - Align `csf_data_ready.required_outputs` with `runtime.tools.stage_evaluator.CSF_DATA_READY_REQUIRED_OUTPUTS`.
- Modify: `docs/guides/qros-research-session-usage.md`
  - Document strict receipt-bound review flow and user-facing states.
- Modify: `docs/guides/qros-review-shared-protocol.md`
  - Replace the old "reads final_review and advances" wording with receipt-bound projection wording.
- Modify: `docs/guides/codex-stage-review-skill-usage.md`
  - Document that `qros-research-session` validates receipt, scope, digest, normalization, and write-scope audit before advancing.
- Modify: every `skills/**/qros-*-review/SKILL.md`
  - Update shared review skill wording so stage-specific review skills do not imply bare `review/final_review.yaml` is enough for closure.
- Test: `tests/review/test_review_scope.py`
- Test: `tests/review/test_final_review_normalizer.py`
- Modify: `tests/review/test_review_runtime_state.py`
- Modify: `tests/review/test_protocol_validator.py`
- Modify: `tests/review/test_review_engine.py`
- Modify: `tests/session/test_research_session_runtime.py`

## Task 1: Canonical Review Scope

**Files:**
- Create: `runtime/tools/review_skillgen/review_scope.py`
- Test: `tests/review/test_review_scope.py`

- [ ] **Step 1: Write failing tests for path normalization and scope equality**

Create `tests/review/test_review_scope.py`:

```python
from __future__ import annotations

import pytest

from runtime.tools.review_skillgen.review_scope import (
    ReviewScope,
    normalize_review_path,
    normalize_review_paths,
)


def test_normalize_review_path_removes_trailing_slash() -> None:
    assert normalize_review_path("shared_feature_base/") == "shared_feature_base"


def test_normalize_review_paths_sorts_and_deduplicates() -> None:
    assert normalize_review_paths(["run_manifest.json", "panel_manifest.json", "run_manifest.json"]) == (
        "panel_manifest.json",
        "run_manifest.json",
    )


def test_normalize_review_path_rejects_parent_escape() -> None:
    with pytest.raises(ValueError, match="review path must not contain parent traversal"):
        normalize_review_path("../author/formal/run_manifest.json")


def test_review_scope_compares_paths_as_sets() -> None:
    left = ReviewScope(
        stage_id="csf_data_ready",
        required_artifact_paths=("shared_feature_base/", "panel_manifest.json"),
        required_provenance_paths=("program_execution_manifest.json",),
        stage_content_artifact_paths=("panel_manifest.json", "shared_feature_base"),
        stage_content_provenance_paths=("program_execution_manifest.json",),
        upstream_binding_artifact_paths=(),
        upstream_binding_provenance_paths=(),
        required_program_dir="program/cross_sectional_factor/data_ready",
        required_program_entrypoint="run_stage.py",
    )
    right = ReviewScope(
        stage_id="csf_data_ready",
        required_artifact_paths=("panel_manifest.json", "shared_feature_base"),
        required_provenance_paths=("program_execution_manifest.json",),
        stage_content_artifact_paths=("shared_feature_base/", "panel_manifest.json"),
        stage_content_provenance_paths=("program_execution_manifest.json",),
        upstream_binding_artifact_paths=(),
        upstream_binding_provenance_paths=(),
        required_program_dir="program/cross_sectional_factor/data_ready",
        required_program_entrypoint="run_stage.py",
    )

    assert left.normalized() == right.normalized()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/review/test_review_scope.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'runtime.tools.review_skillgen.review_scope'`.

- [ ] **Step 3: Implement `review_scope.py`**

Create `runtime/tools/review_skillgen/review_scope.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


def normalize_review_path(path: str) -> str:
    raw = str(path).strip().replace("\\", "/")
    if not raw:
        raise ValueError("review path must be non-empty")
    if raw.startswith("/"):
        raise ValueError("review path must be relative")
    normalized = PurePosixPath(raw).as_posix().rstrip("/")
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise ValueError("review path must not contain parent traversal")
    if normalized in {"", "."}:
        raise ValueError("review path must identify a file or directory")
    return normalized


def normalize_review_paths(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({normalize_review_path(path) for path in paths}))


@dataclass(frozen=True)
class ReviewScope:
    stage_id: str
    required_artifact_paths: tuple[str, ...]
    required_provenance_paths: tuple[str, ...]
    stage_content_artifact_paths: tuple[str, ...]
    stage_content_provenance_paths: tuple[str, ...]
    upstream_binding_artifact_paths: tuple[str, ...]
    upstream_binding_provenance_paths: tuple[str, ...]
    required_program_dir: str
    required_program_entrypoint: str

    def normalized(self) -> "ReviewScope":
        return ReviewScope(
            stage_id=self.stage_id,
            required_artifact_paths=normalize_review_paths(self.required_artifact_paths),
            required_provenance_paths=normalize_review_paths(self.required_provenance_paths),
            stage_content_artifact_paths=normalize_review_paths(self.stage_content_artifact_paths),
            stage_content_provenance_paths=normalize_review_paths(self.stage_content_provenance_paths),
            upstream_binding_artifact_paths=normalize_review_paths(self.upstream_binding_artifact_paths),
            upstream_binding_provenance_paths=normalize_review_paths(self.upstream_binding_provenance_paths),
            required_program_dir=normalize_review_path(self.required_program_dir),
            required_program_entrypoint=normalize_review_path(self.required_program_entrypoint),
        )

    def required_digest_paths(self) -> tuple[str, ...]:
        normalized = self.normalized()
        return normalized.required_artifact_paths + normalized.required_provenance_paths
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/review/test_review_scope.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_skillgen/review_scope.py tests/review/test_review_scope.py
git commit -m "feat: add review scope normalization"
```

## Task 2: Order-Insensitive Author Materialization Digest

**Files:**
- Modify: `runtime/tools/review_skillgen/review_runtime_state.py`
- Test: `tests/review/test_review_runtime_state.py`

- [ ] **Step 1: Write failing digest order test**

Append to `tests/review/test_review_runtime_state.py`:

```python
def test_author_materialization_digest_is_order_insensitive(tmp_path: Path) -> None:
    stage_dir = tmp_path / "02_csf_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in ("panel_manifest.json", "run_manifest.json", "program_execution_manifest.json"):
        (formal_dir / name).write_text(f"{name}: ok\n", encoding="utf-8")

    first = review_runtime_state.compute_author_materialization_digest_fresh(
        artifact_root=formal_dir,
        required_outputs=["panel_manifest.json", "run_manifest.json"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    second = review_runtime_state.compute_author_materialization_digest_fresh(
        artifact_root=formal_dir,
        required_outputs=["run_manifest.json", "panel_manifest.json"],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert second == first
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/review/test_review_runtime_state.py::test_author_materialization_digest_is_order_insensitive -q
```

Expected: FAIL because digest depends on input path order.

- [ ] **Step 3: Normalize digest input ordering**

Modify `runtime/tools/review_skillgen/review_runtime_state.py`:

```python
from runtime.tools.review_skillgen.review_scope import normalize_review_paths
```

Update both `compute_author_materialization_digest` and `compute_author_materialization_digest_fresh` loops:

```python
for name in normalize_review_paths(required_outputs) + normalize_review_paths(required_provenance_paths):
    target = artifact_root / name
    parts.extend(
        [
            name.encode("utf-8"),
            b"\0",
            _path_digest(target, root=artifact_root, ledger=ledger).encode("utf-8"),
            b"\0",
        ]
    )
```

For `compute_author_materialization_digest_fresh`, keep `ledger=None`:

```python
for name in normalize_review_paths(required_outputs) + normalize_review_paths(required_provenance_paths):
    target = artifact_root / name
    parts.extend(
        [
            name.encode("utf-8"),
            b"\0",
            _path_digest(target, root=artifact_root, ledger=None).encode("utf-8"),
            b"\0",
        ]
    )
```

- [ ] **Step 4: Run digest tests**

Run:

```bash
python -m pytest tests/review/test_review_runtime_state.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_skillgen/review_runtime_state.py tests/review/test_review_runtime_state.py
git commit -m "fix: make review materialization digest order-insensitive"
```

## Task 3: Final Review Normalizer

**Files:**
- Create: `runtime/tools/review_skillgen/final_review_normalizer.py`
- Test: `tests/review/test_final_review_normalizer.py`

- [ ] **Step 1: Write failing normalization tests**

Create `tests/review/test_final_review_normalizer.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from runtime.tools.review_skillgen.final_review_normalizer import (
    FORBIDDEN_FINAL_REVIEW_NORMALIZATION,
    normalize_final_review_payload,
    write_normalized_final_review,
)


def _request() -> dict:
    return {
        "review_cycle_id": "cycle-1",
        "lineage_id": "lineage-a",
        "stage": "mandate",
        "author_identity": "author-agent",
        "required_program_dir": "program/mandate",
        "required_program_entrypoint": "run_stage.py",
        "stage_content_artifact_paths": ["mandate.md", "field_dictionary.md"],
        "required_artifact_paths": ["mandate.md", "field_dictionary.md"],
        "required_provenance_paths": ["program_execution_manifest.json"],
    }


def _receipt() -> dict:
    return {
        "review_cycle_id": "cycle-1",
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "review-session",
        "reviewer_agent_id": "reviewer-child",
        "execution_mode": "spawned_agent",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
    }


def _final_review() -> dict:
    return {
        "lineage_id": "lineage-a",
        "stage_id": "mandate",
        "reviewer_identity": "reviewer-agent",
        "reviewer_agent_id": "reviewer-child",
        "reviewed_artifact_paths": ["field_dictionary.md", "mandate.md"],
        "reviewed_program_path": "program/mandate/run_stage.py",
        "reviewed_artifact_digest": "artifact-digest",
        "reviewed_program_digest": "program-digest",
        "verdict": "CONDITIONAL PASS",
        "review_summary": "reviewer summary",
        "blocking_findings": [],
        "reservation_findings": [{"id": "R1", "text": "clarify wording"}],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "rollback_stage": "",
        "downstream_permissions": ["data_ready"],
        "recommended_next_action": "advance",
    }


def test_normalize_final_review_sorts_scope_and_serializes_finding_objects() -> None:
    normalized = normalize_final_review_payload(
        final_review_payload=_final_review(),
        request_payload=_request(),
        receipt_payload=_receipt(),
    )

    assert normalized["reviewed_artifact_paths"] == ["field_dictionary.md", "mandate.md"]
    assert normalized["rollback_stage"] is None
    assert normalized["reservation_findings"] == ['{"id":"R1","text":"clarify wording"}']


def test_normalize_final_review_rejects_unbound_reviewer_agent() -> None:
    payload = _final_review()
    payload["reviewer_agent_id"] = "launcher-agent"

    with pytest.raises(ValueError, match="reviewer_agent_id does not match reviewer_receipt.yaml"):
        normalize_final_review_payload(
            final_review_payload=payload,
            request_payload=_request(),
            receipt_payload=_receipt(),
        )


def test_normalize_final_review_rejects_scope_mismatch() -> None:
    payload = _final_review()
    payload["reviewed_artifact_paths"] = ["mandate.md"]

    with pytest.raises(ValueError, match="reviewed_artifact_paths do not match active request scope"):
        normalize_final_review_payload(
            final_review_payload=payload,
            request_payload=_request(),
            receipt_payload=_receipt(),
        )


def test_normalize_final_review_rejects_missing_review_summary() -> None:
    payload = _final_review()
    payload.pop("review_summary")

    with pytest.raises(ValueError, match=FORBIDDEN_FINAL_REVIEW_NORMALIZATION):
        normalize_final_review_payload(
            final_review_payload=payload,
            request_payload=_request(),
            receipt_payload=_receipt(),
        )


def test_write_normalized_final_review_preserves_raw_file(tmp_path: Path) -> None:
    stage_dir = tmp_path / "01_mandate"
    raw_path = stage_dir / "review" / "final_review.yaml"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(yaml.safe_dump(_final_review(), sort_keys=False), encoding="utf-8")

    written = write_normalized_final_review(
        stage_dir=stage_dir,
        final_review_payload=_final_review(),
        request_payload=_request(),
        receipt_payload=_receipt(),
    )

    assert written == stage_dir / "review" / "result" / "final_review.normalized.yaml"
    assert raw_path.exists()
    assert yaml.safe_load(written.read_text(encoding="utf-8"))["review_summary"] == "reviewer summary"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/review/test_final_review_normalizer.py -q
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement final review normalizer**

Create `runtime/tools/review_skillgen/final_review_normalizer.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.review_scope import normalize_review_paths


NORMALIZED_FINAL_REVIEW_FILENAME = "final_review.normalized.yaml"
FORBIDDEN_FINAL_REVIEW_NORMALIZATION = "FORBIDDEN_FINAL_REVIEW_NORMALIZATION"


def _string_list(value: Any, *, key: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: {key} must be a list")
    normalized: list[str] = []
    for item in value:
        if isinstance(item, str):
            normalized.append(item)
        elif isinstance(item, dict):
            normalized.append(json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
        else:
            raise ValueError(f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: {key} items must be strings or mappings")
    return normalized


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: {key} must be provided by reviewer")
    return value.strip()


def _expected_stage_content_paths(request_payload: dict[str, Any]) -> list[str]:
    raw_paths = request_payload.get("stage_content_artifact_paths") or request_payload["required_artifact_paths"]
    return list(normalize_review_paths(raw_paths))


def normalize_final_review_payload(
    *,
    final_review_payload: dict[str, Any],
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
) -> dict[str, Any]:
    if final_review_payload.get("lineage_id") != request_payload["lineage_id"]:
        raise ValueError("review/final_review.yaml lineage_id does not match active request")
    if final_review_payload.get("stage_id") != request_payload["stage"]:
        raise ValueError("review/final_review.yaml stage_id does not match active request")
    if final_review_payload.get("reviewer_identity") != receipt_payload["requested_reviewer_identity"]:
        raise ValueError("review/final_review.yaml reviewer_identity does not match reviewer_receipt.yaml")
    if final_review_payload.get("reviewer_agent_id") != receipt_payload["reviewer_agent_id"]:
        raise ValueError("review/final_review.yaml reviewer_agent_id does not match reviewer_receipt.yaml")

    expected_program_path = f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}"
    if final_review_payload.get("reviewed_program_path") != expected_program_path:
        raise ValueError("review/final_review.yaml reviewed_program_path does not match active request")

    expected_paths = _expected_stage_content_paths(request_payload)
    reviewed_paths = list(normalize_review_paths(final_review_payload.get("reviewed_artifact_paths", [])))
    if reviewed_paths != expected_paths:
        raise ValueError("review/final_review.yaml reviewed_artifact_paths do not match active request scope")

    rollback_stage = final_review_payload.get("rollback_stage")
    if isinstance(rollback_stage, str) and not rollback_stage.strip():
        rollback_stage = None

    normalized = {
        "lineage_id": request_payload["lineage_id"],
        "stage_id": request_payload["stage"],
        "reviewer_identity": receipt_payload["requested_reviewer_identity"],
        "reviewer_agent_id": receipt_payload["reviewer_agent_id"],
        "reviewed_artifact_paths": reviewed_paths,
        "reviewed_program_path": expected_program_path,
        "reviewed_artifact_digest": _required_string(final_review_payload, "reviewed_artifact_digest"),
        "reviewed_program_digest": _required_string(final_review_payload, "reviewed_program_digest"),
        "verdict": _required_string(final_review_payload, "verdict"),
        "review_summary": _required_string(final_review_payload, "review_summary"),
        "blocking_findings": _string_list(final_review_payload.get("blocking_findings"), key="blocking_findings"),
        "reservation_findings": _string_list(final_review_payload.get("reservation_findings"), key="reservation_findings"),
        "info_findings": _string_list(final_review_payload.get("info_findings"), key="info_findings"),
        "residual_risks": _string_list(final_review_payload.get("residual_risks"), key="residual_risks"),
        "allowed_modifications": _string_list(final_review_payload.get("allowed_modifications"), key="allowed_modifications"),
        "rollback_stage": rollback_stage,
        "downstream_permissions": _string_list(final_review_payload.get("downstream_permissions"), key="downstream_permissions"),
        "recommended_next_action": _required_string(final_review_payload, "recommended_next_action"),
    }
    return normalized


def write_normalized_final_review(
    *,
    stage_dir: Path,
    final_review_payload: dict[str, Any],
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
) -> Path:
    normalized = normalize_final_review_payload(
        final_review_payload=final_review_payload,
        request_payload=request_payload,
        receipt_payload=receipt_payload,
    )
    path = stage_dir / "review" / "result" / NORMALIZED_FINAL_REVIEW_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path
```

- [ ] **Step 4: Run normalizer tests**

Run:

```bash
python -m pytest tests/review/test_final_review_normalizer.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_skillgen/final_review_normalizer.py tests/review/test_final_review_normalizer.py
git commit -m "feat: normalize receipt-bound final reviews"
```

## Task 4: Strict Receipt-Bound Protocol Validation

**Files:**
- Modify: `runtime/tools/review_skillgen/protocol_validator.py`
- Test: `tests/review/test_protocol_validator.py`

- [ ] **Step 1: Add tests for unbound final review and receipt-bound projection**

Append to `tests/review/test_protocol_validator.py`:

```python
def test_protocol_validator_rejects_final_review_without_receipt(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    prepare_review_cycle_for_handoff(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child-agent",
        host="codex",
    )

    request_dir = stage_dir / "review" / "request"
    result_dir = stage_dir / "review" / "result"
    request_payload = load_adversarial_review_request(request_dir / "adversarial_review_request.yaml")
    (request_dir / "reviewer_receipt.yaml").unlink()
    (stage_dir / "review" / "final_review.yaml").write_text(
        yaml.safe_dump(
            {
                "lineage_id": request_payload["lineage_id"],
                "stage_id": request_payload["stage"],
                "reviewer_identity": "reviewer-agent",
                "reviewer_agent_id": "reviewer-child-agent",
                "reviewed_artifact_paths": request_payload["stage_content_artifact_paths"],
                "reviewed_program_path": f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}",
                "reviewed_artifact_digest": "artifact-digest",
                "reviewed_program_digest": "program-digest",
                "verdict": "PASS",
                "review_summary": "looks good",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
                "allowed_modifications": [],
                "rollback_stage": None,
                "downstream_permissions": [],
                "recommended_next_action": "advance",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="REVIEWER_UNBOUND"):
        load_and_validate_protocol(
            review_request_dir=request_dir,
            review_result_dir=result_dir,
            request_loader=load_adversarial_review_request,
            receipt_loader=load_reviewer_receipt,
            runtime_identity=ReviewerRuntimeIdentity(
                reviewer_identity="reviewer-agent",
                reviewer_role="reviewer",
                reviewer_session_id="review-session",
                reviewer_mode="adversarial",
            ),
        )


def test_protocol_validator_projects_final_review_using_receipt_execution_mode(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    prepare_review_cycle_for_handoff(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child-agent",
        host="codex",
    )

    request_dir = stage_dir / "review" / "request"
    result_dir = stage_dir / "review" / "result"
    request_payload = load_adversarial_review_request(request_dir / "adversarial_review_request.yaml")
    (stage_dir / "review" / "final_review.yaml").write_text(
        yaml.safe_dump(
            {
                "lineage_id": request_payload["lineage_id"],
                "stage_id": request_payload["stage"],
                "reviewer_identity": "reviewer-agent",
                "reviewer_agent_id": "reviewer-child-agent",
                "reviewed_artifact_paths": list(reversed(request_payload["stage_content_artifact_paths"])),
                "reviewed_program_path": f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}",
                "reviewed_artifact_digest": "artifact-digest",
                "reviewed_program_digest": "program-digest",
                "verdict": "PASS",
                "review_summary": "looks good",
                "blocking_findings": [],
                "reservation_findings": [{"id": "I1", "text": "object finding"}],
                "info_findings": [],
                "residual_risks": [],
                "allowed_modifications": [],
                "rollback_stage": "",
                "downstream_permissions": [],
                "recommended_next_action": "advance",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    payload = load_and_validate_protocol(
        review_request_dir=request_dir,
        review_result_dir=result_dir,
        request_loader=load_adversarial_review_request,
        receipt_loader=load_reviewer_receipt,
        runtime_identity=ReviewerRuntimeIdentity(
            reviewer_identity="reviewer-agent",
            reviewer_role="reviewer",
            reviewer_session_id="review-session",
            reviewer_mode="adversarial",
        ),
    )

    assert payload["receipt_payload"]["execution_mode"] == "spawned_agent"
    assert payload["review_result"]["reviewer_execution_mode"] == "spawned_agent"
    assert payload["review_result"]["reservation_findings"] == ['{"id":"I1","text":"object finding"}']
    assert (stage_dir / "review" / "result" / "final_review.normalized.yaml").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/review/test_protocol_validator.py::test_protocol_validator_rejects_final_review_without_receipt tests/review/test_protocol_validator.py::test_protocol_validator_projects_final_review_using_receipt_execution_mode -q
```

Expected: FAIL because final review path currently does not require receipt and hard-codes `review_session`.

- [ ] **Step 3: Update protocol validator final-review path**

Modify imports in `runtime/tools/review_skillgen/protocol_validator.py`:

```python
from runtime.tools.review_skillgen.final_review_normalizer import (
    normalize_final_review_payload,
    write_normalized_final_review,
)
```

Change `_project_final_review_result` signature:

```python
def _project_final_review_result(
    *,
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
    runtime_identity: Any,
    normalized_final_review: dict[str, Any],
) -> dict[str, Any]:
```

Build `review_result` from receipt and normalized review:

```python
review_result = {
    "review_cycle_id": request_payload["review_cycle_id"],
    "reviewer_identity": normalized_final_review["reviewer_identity"],
    "reviewer_role": runtime_identity.reviewer_role,
    "reviewer_session_id": receipt_payload["requested_reviewer_session_id"],
    "reviewer_mode": runtime_identity.reviewer_mode,
    "reviewer_agent_id": receipt_payload["reviewer_agent_id"],
    "reviewer_execution_mode": receipt_payload["execution_mode"],
    "reviewer_context_source": receipt_payload["reviewer_context_source"],
    "reviewer_history_inheritance": receipt_payload["reviewer_history_inheritance"],
    "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
    "review_loop_outcome": _FINAL_REVIEW_OUTCOME_BY_VERDICT[normalized_final_review["verdict"]],
    "reviewed_program_dir": request_payload["required_program_dir"],
    "reviewed_program_entrypoint": request_payload["required_program_entrypoint"],
    "reviewed_artifact_paths": normalized_final_review["reviewed_artifact_paths"],
    "reviewed_provenance_paths": stage_content_provenance_paths_from_request(request_payload),
    "reviewed_project_root": request_payload["project_root"],
    "reviewed_lineage_root": request_payload["lineage_root"],
    "reviewed_stage_dir": request_payload["stage_dir"],
    "hard_gate_findings_acknowledged": True,
    "blocking_findings": list(normalized_final_review["blocking_findings"]),
    "reservation_findings": list(normalized_final_review["reservation_findings"]),
    "info_findings": list(normalized_final_review["info_findings"]),
    "residual_risks": list(normalized_final_review["residual_risks"]),
    "allowed_modifications": list(normalized_final_review["allowed_modifications"]),
    "downstream_permissions": list(normalized_final_review["downstream_permissions"]),
    "review_summary": normalized_final_review["review_summary"],
}
```

In `load_and_validate_protocol`, replace the `final_review_path.exists()` branch:

```python
if final_review_path.exists():
    if not receipt_path.exists():
        raise ValueError("REVIEWER_UNBOUND: review/final_review.yaml exists without active reviewer_receipt.yaml")
    receipt_payload = receipt_loader(receipt_path)
    validate_receipt_against_request(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=runtime_identity,
    )
    final_review_payload = load_final_review(final_review_path)
    normalized_final_review = normalize_final_review_payload(
        final_review_payload=final_review_payload,
        request_payload=request_payload,
        receipt_payload=receipt_payload,
    )
    write_normalized_final_review(
        stage_dir=stage_dir,
        final_review_payload=final_review_payload,
        request_payload=request_payload,
        receipt_payload=receipt_payload,
    )
    review_result = _project_final_review_result(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=runtime_identity,
        normalized_final_review=normalized_final_review,
    )
    return {
        "request_payload": request_payload,
        "receipt_payload": receipt_payload,
        "review_result": review_result,
        "audit_payload": {},
    }
```

- [ ] **Step 4: Run protocol validator tests**

Run:

```bash
python -m pytest tests/review/test_protocol_validator.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_skillgen/protocol_validator.py tests/review/test_protocol_validator.py
git commit -m "feat: require receipt-bound final review projection"
```

## Task 5: Automatic Result Projection And Write-Scope Audit

**Files:**
- Modify: `runtime/tools/review_skillgen/review_engine.py`
- Test: `tests/review/test_review_engine.py`

- [ ] **Step 1: Add review engine test for ordinary final-review closure**

Append helper and test to `tests/review/test_review_engine.py`:

```python
def _write_final_review(
    stage_dir: Path,
    *,
    verdict: str = "PASS",
    reviewer_identity: str = "reviewer-agent",
    reviewer_agent_id: str = "reviewer-child-agent",
) -> None:
    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    _write_yaml(
        stage_dir / "review" / "final_review.yaml",
        {
            "lineage_id": request_payload["lineage_id"],
            "stage_id": request_payload["stage"],
            "reviewer_identity": reviewer_identity,
            "reviewer_agent_id": reviewer_agent_id,
            "reviewed_artifact_paths": list(reversed(sorted(request_payload["required_artifact_paths"]))),
            "reviewed_program_path": f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}",
            "reviewed_artifact_digest": "artifact-digest",
            "reviewed_program_digest": "program-digest",
            "verdict": verdict,
            "review_summary": "looks good",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "rollback_stage": None,
            "downstream_permissions": [],
            "recommended_next_action": "advance",
        },
    )


def test_run_stage_review_projects_final_review_and_runs_audit(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    _write_final_review(stage_dir)

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    result_payload = yaml.safe_load(
        (stage_dir / "review" / "result" / "adversarial_review_result.yaml").read_text(encoding="utf-8")
    )
    audit_payload = yaml.safe_load(
        (stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml").read_text(encoding="utf-8")
    )

    assert payload["final_verdict"] == "PASS"
    assert result_payload["reviewer_execution_mode"] == "spawned_agent"
    assert audit_payload["audit_status"] == "PASS"
    assert payload["reviewer_write_scope_audit"]["audit_status"] == "PASS"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/review/test_review_engine.py::test_run_stage_review_projects_final_review_and_runs_audit -q
```

Expected: FAIL because final-review path does not automatically run audit after canonical result is written.

- [ ] **Step 3: Update review engine to run audit after projection**

Modify imports in `runtime/tools/review_skillgen/review_engine.py`:

```python
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    run_reviewer_write_scope_audit,
    validate_reviewer_write_scope_audit,
)
```

After `_write_canonical_review_result(...)`, add:

```python
if receipt_payload:
    audit_payload = run_reviewer_write_scope_audit(stage_dir)
    validate_reviewer_write_scope_audit(
        receipt_payload=receipt_payload,
        audit_payload=audit_payload,
        stage_dir=stage_dir,
    )
```

Ensure `review_result_dir` exists before writing canonical result by adding this at the start of `_write_canonical_review_result`:

```python
review_result_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Run review engine tests**

Run:

```bash
python -m pytest tests/review/test_review_engine.py tests/review/test_adversarial_review_runtime.py::test_run_stage_review_recreates_missing_reviewer_write_scope_audit -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_skillgen/review_engine.py tests/review/test_review_engine.py
git commit -m "feat: auto audit projected final reviews"
```

## Task 6: User-Facing Review State Projection

**Files:**
- Modify: `runtime/tools/research_session.py`
- Test: `tests/session/test_research_session_runtime.py`

- [ ] **Step 1: Add session tests for explicit proof-chain states**

Append tests to `tests/session/test_research_session_runtime.py` near existing review state tests:

```python
def test_run_research_session_reports_reviewer_unbound_for_bare_final_review(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    (stage_dir / "review" / "final_review.yaml").parent.mkdir(parents=True, exist_ok=True)
    (stage_dir / "review" / "final_review.yaml").write_text(
        "lineage_id: topic_a\nstage_id: mandate\nverdict: PASS\n",
        encoding="utf-8",
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.stage_status == "reviewer_unbound"
    assert status.blocking_reason_code == "REVIEWER_UNBOUND"


def test_run_research_session_reports_author_outputs_stale_after_prepare(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    (stage_dir / "author" / "formal" / "mandate.md").write_text("changed after prepare\n", encoding="utf-8")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.stage_status == "author_outputs_stale"
    assert status.blocking_reason_code == "AUTHOR_OUTPUTS_STALE"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_run_research_session_reports_reviewer_unbound_for_bare_final_review tests/session/test_research_session_runtime.py::test_run_research_session_reports_author_outputs_stale_after_prepare -q
```

Expected: FAIL because current session status uses broader review/audit pending states.

- [ ] **Step 3: Map protocol errors to explicit session states**

In `runtime/tools/research_session.py`, locate the review/proof-chain status helpers that load reviewer receipt, audit, runtime state, and protocol errors. Add deterministic mapping:

```python
REVIEW_PROTOCOL_STATUS_MAP = {
    "REVIEWER_UNBOUND": ("reviewer_unbound", "REVIEWER_UNBOUND"),
    "REVIEW_CONTRACT_CONTEXT_STALE": ("author_outputs_stale", "AUTHOR_OUTPUTS_STALE"),
    "reviewed_artifact_paths do not match active request scope": ("review_scope_mismatch", "REVIEW_SCOPE_MISMATCH"),
    "FORBIDDEN_FINAL_REVIEW_NORMALIZATION": ("review_format_invalid", "REVIEW_FORMAT_INVALID"),
    "REVIEWER_WRITE_SCOPE_VIOLATION": ("reviewer_scope_violation", "REVIEWER_SCOPE_VIOLATION"),
}
```

Use this mapping when constructing `stage_status`, `blocking_reason_code`, and `blocking_reason` for active review stages. Preserve existing `awaiting_author_fix`, `review_closed_pass`, and next-stage confirmation behavior.

- [ ] **Step 4: Run session review tests**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py tests/review/test_adversarial_review_runtime.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_session.py tests/session/test_research_session_runtime.py
git commit -m "feat: expose strict review proof states"
```

## Task 7: Align CSF Data Ready Required Output Scope

**Files:**
- Modify: `contracts/stages/workflow_stage_gates.yaml`
- Test: `tests/session/test_review_entry_preflight_scope.py`

- [ ] **Step 1: Add required-output alignment test**

Append to `tests/session/test_review_entry_preflight_scope.py`:

```python
def test_csf_data_ready_gate_required_outputs_match_stage_spec() -> None:
    from runtime.tools.stage_evaluator import STAGE_EVALUATOR_SPECS
    from runtime.tools.review_skillgen.loaders import load_gate_schema
    from runtime.tools.review_skillgen.review_engine import GATES_PATH
    from runtime.tools.review_skillgen.review_scope import normalize_review_paths

    gates = load_gate_schema(GATES_PATH)
    gate_outputs = gates["stages"]["csf_data_ready"]["required_outputs"]
    spec_outputs = STAGE_EVALUATOR_SPECS["csf_data_ready"].required_outputs

    assert normalize_review_paths(gate_outputs) == normalize_review_paths(spec_outputs)
```

- [ ] **Step 2: Run test to verify current scope drift**

Run:

```bash
python -m pytest tests/session/test_review_entry_preflight_scope.py::test_csf_data_ready_gate_required_outputs_match_stage_spec -q
```

Expected before contract alignment: FAIL because the current gate omits `asset_taxonomy_snapshot.parquet` and `csf_data_ready_gate_decision.md`, while the stage evaluator requires both.

- [ ] **Step 3: Align `csf_data_ready.required_outputs`**

Modify the `csf_data_ready.required_outputs` list in `contracts/stages/workflow_stage_gates.yaml` to match the stage evaluator spec after normalization:

```yaml
    required_outputs:
      - panel_manifest.json
      - asset_universe_membership.parquet
      - cross_section_coverage.parquet
      - split_sample_adequacy_report.yaml
      - eligibility_base_mask.parquet
      - shared_feature_base
      - asset_taxonomy_snapshot.parquet
      - csf_data_contract.md
      - csf_data_ready_gate_decision.md
      - run_manifest.json
      - rebuild_csf_data_ready.py
      - artifact_catalog.md
      - field_dictionary.md
```

- [ ] **Step 4: Run scope tests**

Run:

```bash
python -m pytest tests/session/test_review_entry_preflight_scope.py tests/review/test_review_scope.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add contracts/stages/workflow_stage_gates.yaml tests/session/test_review_entry_preflight_scope.py
git commit -m "fix: align csf data ready review scope"
```

## Task 8: Documentation And Verification

**Files:**
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `docs/guides/codex-stage-review-skill-usage.md`
- Modify: every file returned by `find skills -path '*/qros-*-review/SKILL.md' -type f`

- [ ] **Step 1: Document strict review proof-chain**

Add this paragraph near the existing review state section in `docs/guides/qros-research-session-usage.md`:

```markdown
Ordinary review closure is strict receipt-bound. A reviewer-owned `review/final_review.yaml` is not closure-ready by itself: QROS must have an active `review/request/reviewer_receipt.yaml`, the reviewer identity and agent id must match that receipt, the final review scope must equal the active normalized request scope, author outputs must still match the prepare-time digest, and the reviewer write-scope audit must pass. Runtime may write `review/result/final_review.normalized.yaml`, `adversarial_review_result.yaml`, and `reviewer_write_scope_audit.yaml`; ordinary reviewers should only write `review/final_review.yaml`.
```

Update the state list to include:

```markdown
- `reviewer_unbound`：`review/final_review.yaml` exists but has no valid active receipt binding
- `review_format_invalid`：reviewer output cannot be normalized without semantic changes
- `review_scope_mismatch`：reviewer did not review exactly the active normalized request scope
- `author_outputs_stale`：author outputs changed after review prepare
- `reviewer_scope_violation`：write-scope audit failed
```

In `docs/guides/qros-review-shared-protocol.md`, replace:

```markdown
- ordinary review path no longer uses receipt-bound raw findings or a closer command
- 主线程在 reviewer 完成后只读取 `review/final_review.yaml` 并推进状态
```

with:

```markdown
- ordinary review path no longer uses receipt-bound raw findings or a closer command, but final review closure is receipt-bound through `review/request/reviewer_receipt.yaml`
- 主线程在 reviewer 完成后读取 `review/final_review.yaml`，再由 runtime 校验 active receipt、normalized scope、author digest freshness、final-review normalization 和 reviewer write-scope audit；全部通过后才投影 result / closure 并推进状态
```

In `docs/guides/codex-stage-review-skill-usage.md`, replace the step that says the current session simply reads `review/final_review.yaml` and advances with:

```markdown
6. 当前会话读取 `review/final_review.yaml`，校验 active `reviewer_receipt.yaml`、normalized request scope、author materialization digest freshness、final-review normalization 和 reviewer write-scope audit，再按 runtime state 推进 author-fix、failure handling、next-stage confirmation 或 deterministic closure artifacts
```

For every `skills/**/qros-*-review/SKILL.md`, replace:

```markdown
- reviewer 子代理完成后，主线程读取 `review/final_review.yaml` 并按 verdict 推进 author-fix、next-stage confirmation 或 failure handling
```

with:

```markdown
- reviewer 子代理完成后，主线程读取 `review/final_review.yaml`，但必须先通过 active receipt、normalized request scope、author digest freshness、final-review normalization 和 reviewer write-scope audit，才能按 verdict 推进 author-fix、next-stage confirmation 或 failure handling
```

Also replace the numbered execution step:

```markdown
6. 主线程读取 `review/final_review.yaml`
```

with:

```markdown
6. 主线程读取 `review/final_review.yaml` 并完成 receipt / scope / digest / normalization / write-scope audit 校验
```

- [ ] **Step 2: Run docs/bootstrap checks**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [ ] **Step 3: Run focused review suite**

Run:

```bash
python -m pytest tests/review/test_review_scope.py tests/review/test_final_review_normalizer.py tests/review/test_review_runtime_state.py tests/review/test_protocol_validator.py tests/review/test_review_engine.py tests/session/test_review_entry_preflight_scope.py tests/session/test_research_session_runtime.py -q
```

Expected: PASS.

- [ ] **Step 4: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 5: Run full-smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS.

- [ ] **Step 6: Commit docs and any test fixture updates**

```bash
git add docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md docs/guides/codex-stage-review-skill-usage.md skills tests
git commit -m "docs: explain strict review proof chain"
```

## Task 9: Final Review And Integration Commit Check

**Files:**
- No planned code changes unless verification exposes regressions.

- [ ] **Step 1: Inspect final diff**

Run:

```bash
git status --short
git log --oneline -8
```

Expected: no unstaged changes except intentional verification fixture updates.

- [ ] **Step 2: Confirm design scope did not expand**

Run:

```bash
git diff --name-only HEAD~8..HEAD
```

Expected changed files are limited to review proof-chain runtime, review/session tests, docs, and any required stage gate scope alignment. No data artifact contract files such as `contracts/artifacts/csf_data_ready_artifacts.yaml` should be modified in this implementation.

- [ ] **Step 3: Prepare final implementation summary**

Include:

```text
Implemented strict receipt-bound review proof-chain state machine.
Focused tests: <exact command and pass count>
Docs/bootstrap: <exact command and pass count>
Smoke: <exact command and pass count>
Full-smoke: <exact command and pass count>
Commits: <list of commit hashes and subjects>
```

- [ ] **Step 4: Stop for user review**

Do not push unless the user asks. Report final status and wait.
