from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


CSF_DATA_READY_REQUIRED_SPLITS = ("train", "test", "backtest", "holdout")


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
    errors.extend(_validate_split_sample_adequacy_report(stage_formal_dir))
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


def _load_yaml_mapping(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: yaml read failed: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: expected yaml map, found {type(payload).__name__}")
        return None
    return payload


def _read_parquet_rows(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq

        return pq.read_table(path).to_pylist()
    except Exception as exc:
        errors.append(f"{path.name}: parquet read failed: {exc}")
    return []


def _validate_split_sample_adequacy_report(stage_formal_dir: Path) -> list[str]:
    errors: list[str] = []
    report = _load_yaml_mapping(stage_formal_dir / "split_sample_adequacy_report.yaml", errors)
    if report is None:
        return errors

    if report.get("sample_unit") != "cross_section_snapshot":
        errors.append("split_sample_adequacy_report.yaml: sample_unit must equal cross_section_snapshot")
    if report.get("source_artifact") != "cross_section_coverage.parquet":
        errors.append("split_sample_adequacy_report.yaml: source_artifact must equal cross_section_coverage.parquet")

    counts = report.get("split_sample_counts")
    minimums = report.get("minimum_required")
    adequacy = report.get("adequacy")
    if not isinstance(counts, dict):
        errors.append("split_sample_adequacy_report.yaml: split_sample_counts must be a map")
        counts = {}
    if not isinstance(minimums, dict):
        errors.append("split_sample_adequacy_report.yaml: minimum_required must be a map")
        minimums = {}
    if not isinstance(adequacy, dict):
        errors.append("split_sample_adequacy_report.yaml: adequacy must be a map")
        adequacy = {}

    split_statuses: list[bool] = []
    for split in CSF_DATA_READY_REQUIRED_SPLITS:
        count = counts.get(split)
        minimum = minimums.get(split)
        status = adequacy.get(split)

        if isinstance(count, bool) or not isinstance(count, int):
            errors.append(f"split_sample_adequacy_report.yaml: {split} sample_count must be an integer")
            split_statuses.append(False)
            continue
        if isinstance(minimum, bool) or not isinstance(minimum, int):
            errors.append(f"split_sample_adequacy_report.yaml: {split} minimum_required must be an integer")
            split_statuses.append(False)
            continue
        if status not in {"pass", "fail"}:
            errors.append(f"split_sample_adequacy_report.yaml: {split} adequacy must be pass or fail")
            split_statuses.append(False)
            continue

        enough_samples = count >= minimum
        split_statuses.append(enough_samples)
        if not enough_samples:
            errors.append(
                f"split_sample_adequacy_report.yaml: {split} sample_count {count} "
                f"below minimum_required {minimum}"
            )
        expected_status = "pass" if enough_samples else "fail"
        if status != expected_status:
            errors.append(
                f"split_sample_adequacy_report.yaml: {split} adequacy {status!r} "
                f"does not match sample_count {count} and minimum_required {minimum}"
            )

    final_verdict = report.get("final_verdict")
    expected_verdict = "PASS" if all(split_statuses) and len(split_statuses) == len(CSF_DATA_READY_REQUIRED_SPLITS) else "FAIL"
    if final_verdict != expected_verdict:
        errors.append(
            f"split_sample_adequacy_report.yaml: final_verdict {final_verdict!r} "
            f"does not match split adequacy {expected_verdict}"
        )
    if final_verdict != "PASS":
        errors.append("split_sample_adequacy_report.yaml: final_verdict must be PASS before csf_data_ready review")

    return errors


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
