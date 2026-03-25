from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from tools.review_skillgen.context_inference import infer_review_context


def _resolve_context(
    payload: dict[str, Any],
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if explicit_context is not None:
        return {
            "stage_dir": Path(explicit_context["stage_dir"]).resolve(),
            "lineage_root": Path(explicit_context["lineage_root"]).resolve(),
        }

    probe_path = cwd or Path.cwd()
    inferred = infer_review_context(probe_path)
    return {
        "stage_dir": inferred["stage_dir"],
        "lineage_root": inferred["lineage_root"],
    }


def _latest_review_pack(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "lineage_id": payload["lineage_id"],
        "stage": payload["stage"],
        "stage_status": payload["stage_status"],
        "final_verdict": payload["final_verdict"],
        "review_timestamp_utc": payload["review_timestamp_utc"],
        "blocking_findings": payload["blocking_findings"],
        "reservation_findings": payload["reservation_findings"],
        "info_findings": payload["info_findings"],
        "residual_risks": payload["residual_risks"],
    }


def _stage_gate_review(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **_latest_review_pack(payload),
        "rollback_stage": payload.get("rollback_stage"),
        "allowed_modifications": list(payload.get("allowed_modifications", [])),
        "downstream_permissions": list(payload.get("downstream_permissions", [])),
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
    stage_dir.mkdir(parents=True, exist_ok=True)
    lineage_root.mkdir(parents=True, exist_ok=True)

    latest_review_pack = _latest_review_pack(payload)
    files = {
        "latest_review_pack.yaml": latest_review_pack,
        "stage_gate_review.yaml": _stage_gate_review(payload),
        "stage_completion_certificate.yaml": _stage_gate_review(payload),
    }

    for filename, content in files.items():
        output_path = stage_dir / filename
        output_path.write_text(
            yaml.safe_dump(content, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    lineage_latest_path = lineage_root / "latest_review_pack.yaml"
    lineage_latest_path.write_text(
        yaml.safe_dump(latest_review_pack, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
