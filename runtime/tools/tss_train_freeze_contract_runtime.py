from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


def validate_tss_train_freeze_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    del lineage_root
    stage_formal_dir = stage_formal_dir.resolve()
    errors: list[str] = []
    payload = _load_yaml_mapping(stage_formal_dir / "tss_train_freeze.yaml", errors)
    if payload is None:
        return ArtifactValidationResult(errors=errors)
    governance = payload.get("search_governance_contract")
    if not isinstance(governance, dict):
        errors.append("tss_train_freeze.yaml: search_governance_contract must be a map")
        return ArtifactValidationResult(errors=errors)

    candidate_ids = _string_list(governance.get("candidate_variant_ids"))
    kept_ids = _string_list(governance.get("kept_variant_ids"))
    rejected_ids = _string_list(governance.get("rejected_variant_ids"))
    candidate_set = set(candidate_ids)
    kept_outside = sorted(set(kept_ids) - candidate_set)
    rejected_outside = sorted(set(rejected_ids) - candidate_set)
    if kept_outside:
        errors.append(
            f"tss_train_freeze.yaml: kept_variant_ids must be a subset of candidate_variant_ids; outside={kept_outside!r}"
        )
    if rejected_outside:
        errors.append(
            "tss_train_freeze.yaml: rejected_variant_ids must be a subset of candidate_variant_ids; "
            f"outside={rejected_outside!r}"
        )
    return ArtifactValidationResult(errors=errors)


def _load_yaml_mapping(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"{path.name}: yaml read failed: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: expected yaml map, found {type(payload).__name__}")
        return None
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
