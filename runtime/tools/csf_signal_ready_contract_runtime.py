from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


def validate_csf_signal_ready_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    lineage_root = lineage_root.resolve() if lineage_root is not None else _infer_lineage_root(stage_formal_dir)
    errors: list[str] = []

    factor_manifest = _load_yaml_mapping(stage_formal_dir / "factor_manifest.yaml", errors)
    component_manifest = _load_yaml_mapping(stage_formal_dir / "component_factor_manifest.yaml", errors)
    route_contract = _load_yaml_mapping(stage_formal_dir / "route_inheritance_contract.yaml", errors)
    run_manifest = _load_json_mapping(stage_formal_dir / "run_manifest.json", errors)
    if factor_manifest is None or component_manifest is None or route_contract is None or run_manifest is None:
        return ArtifactValidationResult(errors=errors)

    upstream_formal_dir = lineage_root / "02_csf_data_ready" / "author" / "formal" if lineage_root else None
    if upstream_formal_dir is not None:
        upstream_panel_manifest = _load_json_mapping(upstream_formal_dir / "panel_manifest.json", errors)
        if upstream_panel_manifest is not None:
            errors.extend(_validate_panel_key_binding(factor_manifest, upstream_panel_manifest))

    panel_key = _string_list(factor_manifest.get("panel_primary_key"))
    factor_panel_rows = _read_parquet_rows(stage_formal_dir / "factor_panel.parquet", errors)
    coverage_rows = _read_parquet_rows(stage_formal_dir / "factor_coverage_report.parquet", errors)
    group_context_rows = _read_parquet_rows(stage_formal_dir / "factor_group_context.parquet", errors)

    errors.extend(_require_non_empty("factor_panel.parquet", factor_panel_rows))
    errors.extend(_require_unique_key("factor_panel.parquet", factor_panel_rows, panel_key))
    errors.extend(_validate_final_score_field(factor_panel_rows, factor_manifest))
    errors.extend(_validate_input_field_map(factor_manifest, upstream_formal_dir))
    errors.extend(_validate_coverage_report(coverage_rows, factor_panel_rows, factor_manifest))
    errors.extend(_validate_group_context(group_context_rows, route_contract, factor_manifest, panel_key))
    errors.extend(_validate_component_manifest(component_manifest, factor_manifest))
    errors.extend(_validate_factor_structure_consistency(factor_manifest, component_manifest, route_contract, run_manifest))
    errors.extend(_validate_run_manifest(run_manifest))

    return ArtifactValidationResult(errors=errors)


def _infer_lineage_root(stage_formal_dir: Path) -> Path | None:
    parts = stage_formal_dir.parts
    if "03_csf_signal_ready" not in parts:
        return None
    stage_index = parts.index("03_csf_signal_ready")
    return Path(*parts[:stage_index])


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


def _read_parquet_columns(path: Path) -> set[str]:
    try:
        import pyarrow.parquet as pq

        return set(pq.ParquetFile(path).schema_arrow.names)
    except Exception:
        return set()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _require_non_empty(artifact_name: str, rows: list[dict[str, Any]]) -> list[str]:
    if rows:
        return []
    return [f"{artifact_name}: expected non-empty rows"]


def _require_unique_key(artifact_name: str, rows: list[dict[str, Any]], key_fields: list[str]) -> list[str]:
    if not key_fields:
        return [f"{artifact_name}: key fields must be non-empty"]
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        key = tuple(row.get(field) for field in key_fields)
        if key in seen:
            return [f"{artifact_name}: duplicate key {key!r} for {key_fields!r}"]
        seen.add(key)
    return []


def _validate_panel_key_binding(
    factor_manifest: dict[str, Any],
    upstream_panel_manifest: dict[str, Any],
) -> list[str]:
    if factor_manifest.get("panel_primary_key") == upstream_panel_manifest.get("panel_primary_key"):
        return []
    return [
        "factor_manifest.yaml: panel_primary_key must match csf_data_ready panel_manifest.json panel_primary_key"
    ]


def _validate_final_score_field(
    factor_panel_rows: list[dict[str, Any]],
    factor_manifest: dict[str, Any],
) -> list[str]:
    final_score_field = str(factor_manifest.get("final_score_field", "")).strip()
    if not final_score_field:
        return ["factor_manifest.yaml: final_score_field must be non-empty"]
    if not factor_panel_rows:
        return []
    if final_score_field not in factor_panel_rows[0]:
        return [f"factor_panel.parquet: missing final_score_field column {final_score_field}"]

    has_non_null_score = False
    for row in factor_panel_rows:
        value = row.get(final_score_field)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return [f"factor_panel.parquet: final_score_field {final_score_field} must be numeric or null"]
        has_non_null_score = True
    if not has_non_null_score:
        return [f"factor_panel.parquet: final_score_field {final_score_field} requires at least one non-null value"]
    return []


def _validate_input_field_map(
    factor_manifest: dict[str, Any],
    upstream_formal_dir: Path | None,
) -> list[str]:
    raw_fields = _string_list(factor_manifest.get("raw_factor_fields"))
    mappings = factor_manifest.get("input_field_map")
    if not isinstance(mappings, list) or not all(isinstance(item, dict) for item in mappings):
        return ["factor_manifest.yaml: input_field_map must be a list of mappings"]

    errors: list[str] = []
    by_raw_field = {str(item.get("raw_field", "")).strip(): item for item in mappings}
    for raw_field in raw_fields:
        mapping = by_raw_field.get(raw_field)
        if mapping is None:
            errors.append(f"factor_manifest.yaml: raw_factor_fields missing input_field_map binding for {raw_field}")
            continue
        source_artifact = str(mapping.get("source_artifact", "")).strip()
        source_column = str(mapping.get("source_column", "")).strip()
        if not _is_allowed_csf_data_source(source_artifact):
            errors.append(
                "factor_manifest.yaml: input_field_map source_artifact must stay under csf_data_ready formal artifacts"
            )
            continue
        if upstream_formal_dir is None:
            continue
        source_path = upstream_formal_dir / source_artifact
        if not source_path.exists():
            errors.append(f"factor_manifest.yaml: input_field_map source artifact missing: {source_artifact}")
            continue
        if source_path.suffix == ".parquet" and source_column not in _read_parquet_columns(source_path):
            errors.append(
                f"factor_manifest.yaml: input_field_map source column {source_column} missing from {source_artifact}"
            )
    return errors


def _is_allowed_csf_data_source(source_artifact: str) -> bool:
    if not source_artifact or source_artifact.startswith("../") or source_artifact.startswith("/"):
        return False
    allowed_prefixes = (
        "shared_feature_base/",
        "asset_universe_membership.parquet",
        "eligibility_base_mask.parquet",
        "cross_section_coverage.parquet",
        "asset_taxonomy_snapshot.parquet",
    )
    return source_artifact.startswith(allowed_prefixes)


def _validate_coverage_report(
    coverage_rows: list[dict[str, Any]],
    factor_panel_rows: list[dict[str, Any]],
    factor_manifest: dict[str, Any],
) -> list[str]:
    if not coverage_rows:
        return ["factor_coverage_report.parquet: expected non-empty rows"]

    values: list[float] = []
    for row in coverage_rows:
        value = row.get("coverage_ratio")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ["factor_coverage_report.parquet: coverage_ratio must be numeric"]
        numeric_value = float(value)
        if numeric_value < 0 or numeric_value > 1:
            return ["factor_coverage_report.parquet: coverage_ratio must be within [0, 1]"]
        values.append(numeric_value)

    floor = factor_manifest.get("coverage_min_ratio")
    if isinstance(floor, bool) or not isinstance(floor, (int, float)):
        return ["factor_manifest.yaml: coverage_min_ratio must be numeric"]
    floor_value = float(floor)
    min_value = min(values)
    if min_value < floor_value:
        return [
            f"factor_coverage_report.parquet: min coverage_ratio {min_value:g} below coverage_min_ratio {floor_value:g}"
        ]

    coverage_dates = {str(row.get("date")) for row in coverage_rows}
    factor_dates = {str(row.get("date")) for row in factor_panel_rows}
    missing_dates = sorted(factor_dates - coverage_dates)
    if missing_dates:
        return [f"factor_coverage_report.parquet: missing factor_panel dates {missing_dates!r}"]
    return []


def _validate_group_context(
    group_context_rows: list[dict[str, Any]],
    route_contract: dict[str, Any],
    factor_manifest: dict[str, Any],
    panel_key: list[str],
) -> list[str]:
    group_required = (
        str(route_contract.get("neutralization_policy", "")).strip() == "group_neutral"
        or bool(_string_list(factor_manifest.get("group_context_fields")))
    )
    if group_required and not group_context_rows:
        return ["factor_group_context.parquet: expected non-empty rows when group context is required"]
    if not group_context_rows:
        return []
    return _require_unique_key("factor_group_context.parquet", group_context_rows, panel_key)


def _validate_component_manifest(
    component_manifest: dict[str, Any],
    factor_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    formula = str(component_manifest.get("score_combination_formula", "")).strip()
    if not formula:
        errors.append("component_factor_manifest.yaml: score_combination_formula must be non-empty")
    forbidden_tokens = ("learned_weight", "optimize_on_test", "backtest_selected", "from_backtest")
    if any(token in formula for token in forbidden_tokens):
        errors.append(
            "component_factor_manifest.yaml: score_combination_formula must be deterministic before train/test"
        )

    factor_structure = str(factor_manifest.get("factor_structure", "")).strip()
    component_ids = _string_list(component_manifest.get("component_factor_ids"))
    if factor_structure == "single_factor" and len(component_ids) > 1:
        errors.append("component_factor_manifest.yaml: single_factor cannot declare multiple component_factor_ids")
    if factor_structure == "multi_factor_score" and not component_ids:
        errors.append("component_factor_manifest.yaml: multi_factor_score requires component_factor_ids")
    return errors


def _validate_factor_structure_consistency(
    factor_manifest: dict[str, Any],
    component_manifest: dict[str, Any],
    route_contract: dict[str, Any],
    run_manifest: dict[str, Any],
) -> list[str]:
    values = {
        factor_manifest.get("factor_structure"),
        component_manifest.get("factor_structure"),
        route_contract.get("factor_structure"),
        run_manifest.get("factor_structure"),
    }
    if len(values) == 1:
        return []
    return [
        "factor_structure must match across factor_manifest.yaml, component_factor_manifest.yaml, route_inheritance_contract.yaml, and run_manifest.json"
    ]


def _validate_run_manifest(run_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if run_manifest.get("source_stage") != "csf_data_ready":
        errors.append("run_manifest.json: source_stage must be csf_data_ready")
    input_roots = run_manifest.get("input_roots")
    if not isinstance(input_roots, list) or not any("02_csf_data_ready" in str(item) for item in input_roots):
        errors.append("run_manifest.json: input_roots must include 02_csf_data_ready formal artifacts")
    if not isinstance(input_roots, list) or not any("01_mandate" in str(item) for item in input_roots):
        errors.append("run_manifest.json: input_roots must include 01_mandate research_route.yaml")
    return errors
