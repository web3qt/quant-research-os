from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

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
STALE_REVIEW_EVIDENCE = "STALE_REVIEW_EVIDENCE"
CLOSURE_PROJECTION_DRIFT = "CLOSURE_PROJECTION_DRIFT"
REVIEWER_WRITE_SCOPE_VIOLATION = "REVIEWER_WRITE_SCOPE_VIOLATION"

_CLOSURE_FILES = (
    "latest_review_pack.yaml",
    "stage_completion_certificate.yaml",
    "stage_gate_review.yaml",
)


@dataclass
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


def _default_next_action() -> str:
    return "Run qros-review-cycle reset --archive-stale-cycle, then request a fresh reviewer run."


def _raise(reason_code: str, path: Path, message: str) -> None:
    raise ProtectedStateError(
        reason_code=reason_code,
        protected_path=path.as_posix(),
        message=message,
        next_action=_default_next_action(),
    )


def _load_raw_findings(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        _raise(REVIEWER_FINDINGS_UNBOUND, path, "raw reviewer findings must load to a mapping")
    return payload


def _current_author_digest(
    *,
    stage_dir: Path,
    required_outputs: Sequence[str],
    required_provenance_paths: Sequence[str],
) -> str:
    return compute_author_materialization_digest_fresh(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=required_outputs,
        required_provenance_paths=required_provenance_paths,
    )


def _validate_review_runtime_state(
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

    review_state = state["review_state"]
    raw_path = stage_dir / "review" / "result" / RAW_REVIEWER_FINDINGS_FILENAME
    if review_state.startswith("review_closed") and raw_path.exists():
        _raise(REVIEWER_FINDINGS_UNBOUND, raw_path, "raw findings cannot exist after review closure")

    current_digest = _current_author_digest(
        stage_dir=stage_dir,
        required_outputs=required_outputs,
        required_provenance_paths=required_provenance_paths,
    )
    bound_digest = state.get("review_bound_author_digest")
    if bound_digest and bound_digest != current_digest:
        if raw_path.exists():
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

    if review_state == "review_in_progress" and (not request_path.exists() or not receipt_path.exists()):
        _raise(
            REVIEW_STATE_PROJECTION_DRIFT,
            state_path,
            "review_in_progress requires active adversarial_review_request.yaml and reviewer_receipt.yaml",
        )
    if review_state.startswith("review_closed"):
        missing = [name for name in _CLOSURE_FILES if not (stage_dir / "review" / "closure" / name).exists()]
        if missing:
            _raise(
                REVIEW_STATE_PROJECTION_DRIFT,
                state_path,
                f"{review_state} requires closure artifacts; missing: {', '.join(missing)}",
            )


def _validate_raw_findings(stage_dir: Path) -> None:
    raw_path = stage_dir / "review" / "result" / RAW_REVIEWER_FINDINGS_FILENAME
    if not raw_path.exists():
        return

    state_path = review_runtime_state_path(stage_dir)
    state = load_review_runtime_state(state_path) if state_path.exists() else {}
    if state.get("review_state", "").startswith("review_closed"):
        _raise(REVIEWER_FINDINGS_UNBOUND, raw_path, "raw findings cannot exist after review closure")

    request_path = stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    receipt_path = stage_dir / "review" / "request" / REVIEWER_RECEIPT_FILENAME
    if not request_path.exists() or not receipt_path.exists():
        _raise(REVIEWER_FINDINGS_UNBOUND, raw_path, "raw findings exist without active request and receipt")

    raw = _load_raw_findings(raw_path)
    request = load_adversarial_review_request(request_path)
    receipt = load_reviewer_receipt(receipt_path)
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
    # 保留 lineage_root 参数，后续入口层会用它生成 lineage 级诊断；当前检查先聚焦 stage-local 状态。
    del lineage_root
    stage_dir = stage_dir.resolve()
    _validate_review_runtime_state(
        stage_dir=stage_dir,
        required_outputs=required_outputs,
        required_provenance_paths=required_provenance_paths,
        allow_missing_state=allow_missing_state,
    )
    _validate_raw_findings(stage_dir)
