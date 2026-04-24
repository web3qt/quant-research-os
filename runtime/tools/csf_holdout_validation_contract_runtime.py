from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


EXPECTED_BACKTEST_CONTRACT_REFERENCE = "../06_csf_backtest_ready/author/formal/portfolio_contract.yaml"
EXPECTED_BACKTEST_WEIGHT_REFERENCE = "../06_csf_backtest_ready/author/formal/portfolio_weight_panel.parquet"
EXPECTED_BACKTEST_GATE_REFERENCE = "../06_csf_backtest_ready/author/formal/csf_backtest_gate_table.csv"
EXPECTED_BACKTEST_RUN_MANIFEST_REFERENCE = "../06_csf_backtest_ready/author/formal/run_manifest.json"
REQUIRED_STAGE_OUTPUTS = {
    "csf_holdout_run_manifest.json",
    "holdout_factor_diagnostics.parquet",
    "holdout_test_compare.parquet",
    "holdout_portfolio_compare.parquet",
    "rolling_holdout_stability.json",
    "regime_shift_audit.json",
    "csf_holdout_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
}


def validate_csf_holdout_validation_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    lineage_root = lineage_root.resolve() if lineage_root is not None else _infer_lineage_root(stage_formal_dir)
    errors: list[str] = []

    run_manifest = _load_json_mapping(stage_formal_dir / "csf_holdout_run_manifest.json", errors)
    if run_manifest is None:
        return ArtifactValidationResult(errors=errors)

    selected_variant_ids, upstream_portfolio_expression = _read_backtest_manifest(lineage_root, errors)
    errors.extend(_validate_run_manifest(run_manifest, upstream_portfolio_expression))
    errors.extend(_validate_holdout_test_compare(stage_formal_dir / "holdout_test_compare.parquet", selected_variant_ids))
    errors.extend(_validate_parquet_variant_ids(stage_formal_dir / "holdout_factor_diagnostics.parquet", selected_variant_ids))
    errors.extend(_validate_parquet_variant_ids(stage_formal_dir / "holdout_portfolio_compare.parquet", selected_variant_ids))
    errors.extend(_validate_json_selected_variants(stage_formal_dir / "rolling_holdout_stability.json", selected_variant_ids))
    errors.extend(_validate_json_selected_variants(stage_formal_dir / "regime_shift_audit.json", selected_variant_ids))

    return ArtifactValidationResult(errors=errors)


def _infer_lineage_root(stage_formal_dir: Path) -> Path | None:
    parts = stage_formal_dir.parts
    if "07_csf_holdout_validation" not in parts:
        return None
    stage_index = parts.index("07_csf_holdout_validation")
    return Path(*parts[:stage_index])


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


def _read_csv_rows(path: Path, errors: list[str]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception as exc:
        errors.append(f"{path.name}: csv read failed: {exc}")
        return []


def _read_parquet_rows(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq

        return pq.read_table(path).to_pylist()
    except Exception as exc:
        errors.append(f"{path.name}: parquet read failed: {exc}")
        return []


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _read_backtest_manifest(lineage_root: Path | None, errors: list[str]) -> tuple[list[str], str]:
    if lineage_root is None:
        return [], ""
    path = lineage_root / "06_csf_backtest_ready" / "author" / "formal" / "run_manifest.json"
    payload = _load_json_mapping(path, errors)
    if payload is None:
        gate_path = lineage_root / "06_csf_backtest_ready" / "author" / "formal" / "csf_backtest_gate_table.csv"
        gate_rows = _read_csv_rows(gate_path, errors)
        return [str(row.get("variant_id", "")).strip() for row in gate_rows if str(row.get("variant_id", "")).strip()], ""
    return _string_list(payload.get("selected_variant_ids")), str(payload.get("portfolio_expression", "")).strip()


def _validate_run_manifest(run_manifest: dict[str, Any], upstream_portfolio_expression: str) -> list[str]:
    errors: list[str] = []
    input_roots = _string_list(run_manifest.get("input_roots"))
    for expected in [
        EXPECTED_BACKTEST_CONTRACT_REFERENCE,
        EXPECTED_BACKTEST_WEIGHT_REFERENCE,
        EXPECTED_BACKTEST_GATE_REFERENCE,
        EXPECTED_BACKTEST_RUN_MANIFEST_REFERENCE,
    ]:
        if expected not in input_roots:
            errors.append(f"csf_holdout_run_manifest.json: input_roots must bind to {expected}")

    stage_outputs = set(_string_list(run_manifest.get("stage_outputs")))
    missing_outputs = sorted(REQUIRED_STAGE_OUTPUTS - stage_outputs)
    if missing_outputs:
        errors.append(f"csf_holdout_run_manifest.json: stage_outputs missing required outputs {missing_outputs!r}")
    if str(run_manifest.get("source_stage", "")).strip() != "csf_backtest_ready":
        errors.append("csf_holdout_run_manifest.json: source_stage must be csf_backtest_ready")

    observed_portfolio_expression = str(run_manifest.get("portfolio_expression", "")).strip()
    if upstream_portfolio_expression and observed_portfolio_expression != upstream_portfolio_expression:
        errors.append(
            "csf_holdout_run_manifest.json: portfolio_expression must match upstream backtest run_manifest; "
            f"expected={upstream_portfolio_expression!r}; observed={observed_portfolio_expression!r}"
        )
    return errors


def _validate_holdout_test_compare(path: Path, selected_variant_ids: list[str]) -> list[str]:
    errors: list[str] = []
    rows = _read_parquet_rows(path, errors)
    if not rows:
        return errors
    errors.extend(_validate_variant_rows(path.name, rows, selected_variant_ids))
    row_ids = {str(row.get("variant_id", "")).strip() for row in rows if str(row.get("variant_id", "")).strip()}
    missing = sorted(set(selected_variant_ids) - row_ids)
    if missing:
        errors.append(f"{path.name}: missing backtest-selected variants {missing!r}")
    for row in rows:
        if row.get("direction_match") is not True:
            errors.append(f"{path.name}: direction_match must be true for every selected variant")
        try:
            holdout_mean_net_return = float(str(row.get("holdout_mean_net_return", "")).strip())
        except ValueError:
            errors.append(f"{path.name}: holdout_mean_net_return must be numeric")
            continue
        if holdout_mean_net_return <= 0:
            errors.append(f"{path.name}: holdout_mean_net_return must be > 0 for every selected variant")
    return errors


def _validate_parquet_variant_ids(path: Path, selected_variant_ids: list[str]) -> list[str]:
    errors: list[str] = []
    rows = _read_parquet_rows(path, errors)
    if not rows:
        return errors
    return [*errors, *_validate_variant_rows(path.name, rows, selected_variant_ids)]


def _validate_variant_rows(artifact_name: str, rows: list[dict[str, Any]], selected_variant_ids: list[str]) -> list[str]:
    observed = {str(row.get("variant_id", "")).strip() for row in rows if str(row.get("variant_id", "")).strip()}
    outside = sorted(observed - set(selected_variant_ids))
    if outside:
        return [f"{artifact_name}: variant_id rows must stay within backtest-selected variants; outside={outside!r}"]
    return []


def _validate_json_selected_variants(path: Path, selected_variant_ids: list[str]) -> list[str]:
    errors: list[str] = []
    payload = _load_json_mapping(path, errors)
    if payload is None:
        return errors
    observed = set(_string_list(payload.get("selected_variant_ids")))
    outside = sorted(observed - set(selected_variant_ids))
    if outside:
        errors.append(f"{path.name}: selected_variant_ids must stay within backtest-selected variants; outside={outside!r}")
    return errors


if __name__ == "__main__":
    raise SystemExit("Use validate_csf_holdout_validation_semantics() from runtime/preflight.")
