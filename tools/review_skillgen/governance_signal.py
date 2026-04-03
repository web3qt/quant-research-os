from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = ROOT / "docs" / "gates" / "review_governance_policy.yaml"
GOVERNANCE_SIGNAL_FILENAME = "governance_signal.json"
DEFAULT_CANDIDATE_PRIORITY = ["hard_gate", "template_constraint", "regression_test"]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_review_governance_policy(path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must load to a mapping")
    priority = payload.get("candidate_priority_order")
    if priority != DEFAULT_CANDIDATE_PRIORITY:
        raise ValueError(f"{path}: candidate_priority_order must equal {DEFAULT_CANDIDATE_PRIORITY}")
    thresholds = payload.get("thresholds")
    if not isinstance(thresholds, dict):
        raise ValueError(f"{path}: thresholds must be a mapping")
    if not isinstance(thresholds.get("min_distinct_review_cycles"), int):
        raise ValueError(f"{path}: min_distinct_review_cycles must be an integer")
    if not isinstance(thresholds.get("min_distinct_contexts_for_hard_gate"), int):
        raise ValueError(f"{path}: min_distinct_contexts_for_hard_gate must be an integer")
    rollout_started_at = payload.get("rollout_started_at")
    if not isinstance(rollout_started_at, str) or not rollout_started_at.strip():
        raise ValueError(f"{path}: rollout_started_at must be a non-empty string")
    return payload


def _detect_finding_code(text: str) -> str:
    stripped = text.strip()
    match = re.match(r"^([A-Za-z]{1,6}-\d{1,4})\b", stripped)
    if match:
        return match.group(1).upper()
    normalized = _collapse_whitespace(text)
    if normalized.startswith("missing required output:"):
        return "MISSING_REQUIRED_OUTPUT"
    if ": missing evidence for " in normalized:
        return "MISSING_CHECKLIST_EVIDENCE"
    if "missing required global evidence" in normalized:
        return "MISSING_GLOBAL_EVIDENCE"
    return "REVIEW_FINDING"


def _detect_finding_class(text: str) -> str:
    normalized = _collapse_whitespace(text)
    if normalized.startswith("missing required output:"):
        return "artifact_missing"
    if "missing evidence for" in normalized:
        return "checklist_evidence_missing"
    if "missing required global evidence" in normalized:
        return "global_evidence_missing"
    if "leak" in normalized:
        return "leakage"
    if "gate bypass" in normalized or "certificate" in normalized:
        return "governance_bypass"
    return "review_finding"


def _candidate_priority_for_class(finding_class: str) -> list[str]:
    if finding_class in {"artifact_missing", "global_evidence_missing", "governance_bypass", "leakage"}:
        return list(DEFAULT_CANDIDATE_PRIORITY)
    return ["template_constraint", "regression_test", "hard_gate"]


def _fingerprint_payload(*, finding_code: str, finding_class: str, finding_summary: str) -> str:
    digest = hashlib.sha256()
    for item in (finding_code, finding_class, _collapse_whitespace(finding_summary)):
        digest.update(item.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def _normalize_signal_entries(findings: list[str], *, source_kind: str, source_artifacts: list[str]) -> list[dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for item in findings:
        summary = item.strip()
        if not summary:
            continue
        finding_code = _detect_finding_code(summary)
        finding_class = _detect_finding_class(summary)
        priority = _candidate_priority_for_class(finding_class)
        fingerprint = _fingerprint_payload(
            finding_code=finding_code,
            finding_class=finding_class,
            finding_summary=summary,
        )
        entry = normalized.setdefault(
            fingerprint,
            {
                "finding_fingerprint": fingerprint,
                "finding_code": finding_code,
                "finding_class": finding_class,
                "finding_summary": summary,
                "candidate_priority": priority,
                "candidate_class_suggestion": priority[0],
                "source_kinds": [],
                "source_artifacts": set(),
            },
        )
        entry["source_kinds"].append(source_kind)
        entry["source_artifacts"].update(source_artifacts)
    for entry in normalized.values():
        entry["source_kinds"] = sorted(set(entry["source_kinds"]))
        entry["source_artifacts"] = sorted(entry["source_artifacts"])
    return sorted(normalized.values(), key=lambda item: item["finding_fingerprint"])


def infer_route(stage: str) -> str:
    return "cross_sectional_factor" if stage.startswith("csf_") else "time_series_signal"


def build_governance_signal_bundle(
    *,
    stage_dir: Path,
    lineage_root: Path,
    stage: str,
    request_payload: dict[str, Any],
    review_result: dict[str, Any],
    review_loop_outcome: str,
    final_verdict: str | None,
    blocking_findings: list[str],
    reservation_findings: list[str],
    info_findings: list[str],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = policy or load_review_governance_policy()
    emitted_at = review_result.get("review_completed_at") or _utcnow()
    review_cycle_started_at = request_payload.get("author_stage_invoked_at") or emitted_at
    source_artifacts = ["adversarial_review_request.yaml", "adversarial_review_result.yaml"]
    if (stage_dir / "review_findings.yaml").exists():
        source_artifacts.append("review_findings.yaml")
    signals: list[dict[str, Any]] = []
    signals.extend(_normalize_signal_entries(blocking_findings, source_kind="blocking", source_artifacts=source_artifacts))
    signals.extend(_normalize_signal_entries(reservation_findings, source_kind="reservation", source_artifacts=source_artifacts))
    signals.extend(_normalize_signal_entries(info_findings, source_kind="info", source_artifacts=source_artifacts))

    deduped: dict[str, dict[str, Any]] = {}
    for entry in signals:
        current = deduped.get(entry["finding_fingerprint"])
        if current is None:
            deduped[entry["finding_fingerprint"]] = entry
            continue
        current["source_kinds"] = sorted(set(current["source_kinds"]) | set(entry["source_kinds"]))
        current["source_artifacts"] = sorted(set(current["source_artifacts"]) | set(entry["source_artifacts"]))
        if DEFAULT_CANDIDATE_PRIORITY.index(entry["candidate_priority"][0]) < DEFAULT_CANDIDATE_PRIORITY.index(current["candidate_priority"][0]):
            current["candidate_priority"] = entry["candidate_priority"]
            current["candidate_class_suggestion"] = entry["candidate_class_suggestion"]

    if not deduped:
        fallback_summary = f"review cycle observed: {review_loop_outcome}"
        deduped[_fingerprint_payload(
            finding_code="REVIEW_CYCLE_OBSERVATION",
            finding_class="review_cycle_observation",
            finding_summary=fallback_summary,
        )] = {
            "finding_fingerprint": _fingerprint_payload(
                finding_code="REVIEW_CYCLE_OBSERVATION",
                finding_class="review_cycle_observation",
                finding_summary=fallback_summary,
            ),
            "finding_code": "REVIEW_CYCLE_OBSERVATION",
            "finding_class": "review_cycle_observation",
            "finding_summary": fallback_summary,
            "candidate_priority": ["regression_test", "template_constraint", "hard_gate"],
            "candidate_class_suggestion": "regression_test",
            "source_kinds": ["cycle_observation"],
            "source_artifacts": source_artifacts,
        }

    post_rollout_only = _parse_iso8601(review_cycle_started_at) >= _parse_iso8601(policy["rollout_started_at"])
    bundle = {
        "schema_version": "1.0",
        "lineage_id": lineage_root.name,
        "route": infer_route(stage),
        "review_stage": stage,
        "review_cycle_id": request_payload["review_cycle_id"],
        "review_cycle_started_at": review_cycle_started_at,
        "reviewer_identity": review_result["reviewer_identity"],
        "author_identity": request_payload["author_identity"],
        "review_loop_outcome": review_loop_outcome,
        "final_verdict": final_verdict,
        "signal_basis": "fix_required" if review_loop_outcome == "FIX_REQUIRED" else "closure_ready",
        "emitted_at": emitted_at,
        "post_rollout_only": post_rollout_only,
        "signals": sorted(deduped.values(), key=lambda item: item["finding_fingerprint"]),
    }
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / GOVERNANCE_SIGNAL_FILENAME).write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return bundle


def build_governance_signal(
    *,
    stage_dir: Path,
    lineage_id: str,
    stage: str,
    request_payload: dict[str, Any],
    review_result: dict[str, Any],
    blocking_findings: list[str],
    reservation_findings: list[str],
    info_findings: list[str],
    final_verdict: str | None,
    review_loop_outcome: str,
    review_timestamp_utc: str,
) -> dict[str, Any]:
    request = dict(request_payload)
    request.setdefault("lineage_id", lineage_id)
    request.setdefault("author_stage_invoked_at", review_timestamp_utc)
    result = dict(review_result)
    result.setdefault("review_completed_at", review_timestamp_utc)
    return build_governance_signal_bundle(
        stage_dir=stage_dir,
        lineage_root=stage_dir.parent,
        stage=stage,
        request_payload=request,
        review_result=result,
        review_loop_outcome=review_loop_outcome,
        final_verdict=final_verdict,
        blocking_findings=blocking_findings,
        reservation_findings=reservation_findings,
        info_findings=info_findings,
        policy=load_review_governance_policy(),
    )


def write_governance_signal(stage_dir: str | Path, artifact: dict[str, Any]) -> Path:
    output_path = Path(stage_dir) / GOVERNANCE_SIGNAL_FILENAME
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
