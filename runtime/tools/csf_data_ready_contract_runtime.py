from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


def validate_csf_data_ready_semantics(stage_formal_dir: Path) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    errors: list[str] = []

    panel_manifest = _load_json_mapping(stage_formal_dir / "panel_manifest.json", errors)
    if panel_manifest is None:
        return ArtifactValidationResult(errors=errors)

    panel_primary_key = panel_manifest.get("panel_primary_key")
    if panel_primary_key != ["date", "asset"]:
        errors.append("panel_manifest.json: panel_primary_key must equal ['date', 'asset']")

    membership_rows = _read_parquet_rows(stage_formal_dir / "asset_universe_membership.parquet", errors)
    eligibility_rows = _read_parquet_rows(stage_formal_dir / "eligibility_base_mask.parquet", errors)
    coverage_rows = _read_parquet_rows(stage_formal_dir / "cross_section_coverage.parquet", errors)

    errors.extend(_require_non_empty("asset_universe_membership.parquet", membership_rows))
    errors.extend(_require_non_empty("eligibility_base_mask.parquet", eligibility_rows))
    errors.extend(_require_unique_key("asset_universe_membership.parquet", membership_rows, ["date", "asset"]))
    errors.extend(_require_unique_key("eligibility_base_mask.parquet", eligibility_rows, ["date", "asset"]))
    errors.extend(_require_coverage_floor(coverage_rows, panel_manifest))
    errors.extend(_validate_shared_feature_outputs(stage_formal_dir, panel_manifest))

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


def _read_parquet_rows(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq

        return pq.read_table(path).to_pylist()
    except Exception as exc:
        errors.append(f"{path.name}: parquet read failed: {exc}")
        return []


def _require_non_empty(artifact_name: str, rows: list[dict[str, Any]]) -> list[str]:
    if rows:
        return []
    return [f"{artifact_name}: expected non-empty rows"]


def _require_unique_key(
    artifact_name: str,
    rows: list[dict[str, Any]],
    key_fields: list[str],
) -> list[str]:
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        key = tuple(row.get(field) for field in key_fields)
        if key in seen:
            return [f"{artifact_name}: duplicate key {key!r} for {key_fields!r}"]
        seen.add(key)
    return []


def _require_coverage_floor(rows: list[dict[str, Any]], panel_manifest: dict[str, Any]) -> list[str]:
    if not rows:
        return ["cross_section_coverage.parquet: expected non-empty rows"]

    values: list[float] = []
    for row in rows:
        value = row.get("coverage_ratio")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ["cross_section_coverage.parquet: coverage_ratio must be numeric"]
        values.append(float(value))

    floor = panel_manifest.get("coverage_floor_min_ratio")
    if isinstance(floor, bool) or not isinstance(floor, (int, float)):
        return ["panel_manifest.json: coverage_floor_min_ratio must be numeric"]

    min_value = min(values)
    floor_value = float(floor)
    if min_value < floor_value:
        return [
            f"cross_section_coverage.parquet: min coverage_ratio {min_value:g} "
            f"below coverage_floor_min_ratio {floor_value:g}"
        ]
    return []


def _validate_shared_feature_outputs(stage_formal_dir: Path, panel_manifest: dict[str, Any]) -> list[str]:
    outputs = panel_manifest.get("shared_feature_outputs")
    if not isinstance(outputs, list) or not all(isinstance(item, str) and item.strip() for item in outputs):
        return ["panel_manifest.json: shared_feature_outputs must be a non-empty list of strings"]

    errors: list[str] = []
    shared_feature_base = stage_formal_dir / "shared_feature_base"
    for output in outputs:
        artifact_name = f"shared_feature_base/{output}.parquet"
        rows = _read_parquet_rows(shared_feature_base / f"{output}.parquet", errors)
        errors.extend(_require_non_empty(artifact_name, rows))
    return errors
