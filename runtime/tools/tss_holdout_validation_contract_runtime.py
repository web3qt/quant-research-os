from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


def validate_tss_holdout_validation_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    del lineage_root
    stage_formal_dir = stage_formal_dir.resolve()
    errors: list[str] = []
    payload = _load_json_mapping(stage_formal_dir / "tss_holdout_run_manifest.json", errors)
    if payload is None:
        return ArtifactValidationResult(errors=errors)
    tuning_performed = payload.get("tuning_performed")
    if tuning_performed is True or str(tuning_performed).strip().lower() == "true":
        errors.append("tss_holdout_run_manifest.json: must not declare tuning_performed: true")
    return ArtifactValidationResult(errors=errors)


def _load_json_mapping(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: json read failed: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: expected json map, found {type(payload).__name__}")
        return None
    return payload
