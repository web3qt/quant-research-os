from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.research_session import SessionContext, session_stage_base_name
from tools.review_skillgen.loaders import load_gate_schema


ROOT = Path(__file__).resolve().parents[1]
GATE_SCHEMA_PATH = ROOT / "docs" / "gates" / "workflow_stage_gates.yaml"
SNAPSHOT_VERSION = "v1"
SCHEMA_VERSION = "workflow_stage_gates@v1"

_SESSION_STAGE_TO_GATE_STAGE = {
    "idea_intake": "idea_intake",
    "mandate": "mandate",
    "data_ready": "data_ready",
    "signal_ready": "signal_ready",
    "train_freeze": "train_calibration",
    "test_evidence": "test_evidence",
    "backtest_ready": "backtest_ready",
    "holdout_validation": "holdout_validation",
    "csf_data_ready": "csf_data_ready",
    "csf_signal_ready": "csf_signal_ready",
    "csf_train_freeze": "csf_train_freeze",
    "csf_test_evidence": "csf_test_evidence",
    "csf_backtest_ready": "csf_backtest_ready",
    "csf_holdout_validation": "csf_holdout_validation",
}

_SESSION_STAGE_SUFFIXES = (
    "_review_confirmation_pending",
    "_display_confirmation_pending",
    "_next_stage_confirmation_pending",
    "_confirmation_pending",
    "_review_complete",
    "_review",
    "_author",
)

_NEXT_STAGE_SNAPSHOT = {
    "mandate": "data_ready_confirmation_pending",
    "data_ready": "signal_ready_confirmation_pending",
    "signal_ready": "train_freeze_confirmation_pending",
    "train_freeze": "test_evidence_confirmation_pending",
    "test_evidence": "backtest_ready_confirmation_pending",
    "backtest_ready": "holdout_validation_confirmation_pending",
    "holdout_validation": "holdout_validation_review_complete",
    "csf_data_ready": "csf_signal_ready_confirmation_pending",
    "csf_signal_ready": "csf_train_freeze_confirmation_pending",
    "csf_train_freeze": "csf_test_evidence_confirmation_pending",
    "csf_test_evidence": "csf_backtest_ready_confirmation_pending",
    "csf_backtest_ready": "csf_holdout_validation_confirmation_pending",
    "csf_holdout_validation": "csf_holdout_validation_review_complete",
}


@dataclass(frozen=True)
class CanonicalDecisionSnapshot:
    fixture_id: str
    input_digest: str
    snapshot_version: str
    schema_version: str
    route_skill: str
    stage_id: str
    session_stage: str
    formal_decision: str
    required_artifacts: tuple[str, ...]
    downstream_permissions: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    lineage_transition: str
    evidence_refs: tuple[str, ...] = ()
    failure_class: str | None = None
    severity: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def session_stage_to_gate_stage(session_stage: str) -> str:
    normalized = session_stage_base_name(session_stage)
    try:
        return _SESSION_STAGE_TO_GATE_STAGE[normalized]
    except KeyError as exc:
        raise KeyError(f"Unsupported session stage for canonical snapshot: {session_stage}") from exc


def canonicalize_snapshot_session_stage(session_stage: str, *, current_route: str | None) -> str:
    if session_stage.endswith("_review_confirmation_pending"):
        return session_stage
    if session_stage.endswith("_display_confirmation_pending") or session_stage.endswith(
        "_next_stage_confirmation_pending"
    ):
        stage_base = session_stage.rsplit("_", 3)[0]
        if stage_base == "mandate" and current_route == "cross_sectional_factor":
            return "csf_data_ready_confirmation_pending"
        return _NEXT_STAGE_SNAPSHOT.get(stage_base, session_stage)
    return session_stage


@lru_cache(maxsize=1)
def _gate_stages() -> dict[str, Any]:
    return load_gate_schema(GATE_SCHEMA_PATH)["stages"]


def required_artifacts_for_session_stage(session_stage: str) -> tuple[str, ...]:
    gate_stage = session_stage_to_gate_stage(session_stage)
    return tuple(str(item) for item in _gate_stages()[gate_stage].get("required_outputs", []))


def downstream_permissions_for_session_stage(session_stage: str) -> tuple[str, ...]:
    gate_stage = session_stage_to_gate_stage(session_stage)
    permissions = (
        _gate_stages()[gate_stage]
        .get("downstream_permissions", {})
        .get("may_advance_to", [])
    )
    return tuple(str(item) for item in permissions)


def _input_digest(parts: Iterable[str | None]) -> str:
    normalized = "|".join(part or "" for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def canonical_snapshot_from_session_context(
    context: SessionContext,
    *,
    fixture_id: str,
    evidence_refs: Iterable[str] = (),
    failure_class: str | None = None,
    severity: str | None = None,
) -> CanonicalDecisionSnapshot:
    canonical_session_stage = canonicalize_snapshot_session_stage(
        context.current_stage,
        current_route=context.current_route,
    )
    formal_decision = context.review_verdict or context.gate_status
    blocking_reasons = tuple(
        item for item in [context.blocking_reason, *context.open_risks] if item
    )
    return CanonicalDecisionSnapshot(
        fixture_id=fixture_id,
        input_digest=_input_digest(
            [
                fixture_id,
                context.lineage_id,
                canonical_session_stage,
                context.current_route,
                context.current_skill,
                formal_decision,
            ]
        ),
        snapshot_version=SNAPSHOT_VERSION,
        schema_version=SCHEMA_VERSION,
        route_skill=context.current_skill,
        stage_id=session_stage_to_gate_stage(canonical_session_stage),
        session_stage=canonical_session_stage,
        formal_decision=formal_decision,
        required_artifacts=required_artifacts_for_session_stage(canonical_session_stage),
        downstream_permissions=downstream_permissions_for_session_stage(canonical_session_stage),
        blocking_reasons=blocking_reasons,
        lineage_transition=context.next_action,
        evidence_refs=tuple(evidence_refs),
        failure_class=failure_class,
        severity=severity,
    )


def diff_snapshot(
    expected: Mapping[str, Any],
    actual: CanonicalDecisionSnapshot | Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    actual_dict = actual.to_dict() if isinstance(actual, CanonicalDecisionSnapshot) else dict(actual)
    expected_normalized = json.loads(json.dumps(expected, ensure_ascii=False))
    actual_normalized = json.loads(json.dumps(actual_dict, ensure_ascii=False))
    all_keys = sorted(set(expected) | set(actual_dict))
    return {
        key: {"expected": expected_normalized.get(key), "actual": actual_normalized.get(key)}
        for key in all_keys
        if expected_normalized.get(key) != actual_normalized.get(key)
    }


def semantic_projection(
    snapshot: CanonicalDecisionSnapshot | Mapping[str, Any],
) -> dict[str, Any]:
    payload = snapshot.to_dict() if isinstance(snapshot, CanonicalDecisionSnapshot) else dict(snapshot)
    ignored = {"fixture_id", "input_digest", "snapshot_version", "schema_version", "evidence_refs"}
    return {key: payload[key] for key in sorted(payload) if key not in ignored}
