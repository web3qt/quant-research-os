from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.context_inference import build_stage_context, infer_review_context


def _resolve_context(
    payload: dict[str, Any],
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if explicit_context is not None:
        context = build_stage_context(Path(explicit_context["stage_dir"]).resolve())
        context["lineage_root"] = Path(explicit_context["lineage_root"]).resolve()
        return context

    probe_path = cwd or Path.cwd()
    return infer_review_context(probe_path)


def _latest_review_pack(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "lineage_id": payload["lineage_id"],
        "stage": payload["stage"],
        "stage_status": payload["stage_status"],
        "final_verdict": payload["final_verdict"],
        "review_loop_outcome": payload.get("review_loop_outcome"),
        "author_identity": payload.get("author_identity"),
        "author_session_id": payload.get("author_session_id"),
        "reviewer_identity": payload.get("reviewer_identity"),
        "reviewer_role": payload.get("reviewer_role"),
        "reviewer_session_id": payload.get("reviewer_session_id"),
        "reviewer_mode": payload.get("reviewer_mode"),
        "review_timestamp_utc": payload["review_timestamp_utc"],
        "blocking_findings": payload["blocking_findings"],
        "reservation_findings": payload["reservation_findings"],
        "info_findings": payload["info_findings"],
        "residual_risks": payload["residual_risks"],
        "review_scope": payload.get("review_scope", {}),
        "evidence_summary": payload.get("evidence_summary", {}),
    }


def _stage_gate_review(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **_latest_review_pack(payload),
        "contract_source": payload.get("contract_source"),
        "checklist_source": payload.get("checklist_source"),
        "required_outputs_checked": payload.get("required_outputs_checked", {}),
        "rollback_stage": payload.get("rollback_stage"),
        "allowed_modifications": list(payload.get("allowed_modifications", [])),
        "downstream_permissions": list(payload.get("downstream_permissions", [])),
        "adversarial_review_request": payload.get("adversarial_review_request", {}),
        "spawned_reviewer_receipt": payload.get("spawned_reviewer_receipt", {}),
        "adversarial_review_result": payload.get("adversarial_review_result", {}),
    }


def write_closure_artifacts(
    payload: dict[str, Any],
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
) -> None:
    context = _resolve_context(payload, cwd=cwd, explicit_context=explicit_context)
    stage_dir = context["stage_dir"]
    lineage_root = context["lineage_root"]
    review_closure_dir = context["review_closure_dir"]
    stage_dir.mkdir(parents=True, exist_ok=True)
    lineage_root.mkdir(parents=True, exist_ok=True)
    review_closure_dir.mkdir(parents=True, exist_ok=True)

    latest_review_pack = _latest_review_pack(payload)
    files = {
        "latest_review_pack.yaml": latest_review_pack,
        "stage_gate_review.yaml": _stage_gate_review(payload),
        "stage_completion_certificate.yaml": _stage_gate_review(payload),
    }

    for filename, content in files.items():
        output_path = review_closure_dir / filename
        output_path.write_text(
            yaml.safe_dump(content, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    lineage_latest_path = lineage_root / "latest_review_pack.yaml"
    lineage_latest_path.write_text(
        yaml.safe_dump(latest_review_pack, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
