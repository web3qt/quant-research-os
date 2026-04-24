from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


EXPECTED_SELECTED_VARIANTS_REFERENCE = "../05_csf_test_evidence/author/formal/csf_selected_variants_test.csv"
EXPECTED_TEST_GATE_REFERENCE = "../05_csf_test_evidence/author/formal/csf_test_gate_table.csv"
REQUIRED_STAGE_OUTPUTS = {
    "portfolio_contract.yaml",
    "portfolio_weight_panel.parquet",
    "rebalance_ledger.csv",
    "turnover_capacity_report.parquet",
    "cost_assumption_report.md",
    "portfolio_summary.parquet",
    "name_level_metrics.parquet",
    "drawdown_report.json",
    "target_strategy_compare.parquet",
    "csf_backtest_gate_table.csv",
    "csf_backtest_contract.md",
    "csf_backtest_gate_decision.md",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
}


def validate_csf_backtest_ready_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    lineage_root = lineage_root.resolve() if lineage_root is not None else _infer_lineage_root(stage_formal_dir)
    errors: list[str] = []

    portfolio_contract = _load_yaml_mapping(stage_formal_dir / "portfolio_contract.yaml", errors)
    run_manifest = _load_json_mapping(stage_formal_dir / "run_manifest.json", errors)
    gate_rows = _read_csv_rows(stage_formal_dir / "csf_backtest_gate_table.csv", errors)
    if portfolio_contract is None or run_manifest is None:
        return ArtifactValidationResult(errors=errors)

    selected_variant_ids = _read_test_selected_variant_ids(lineage_root, errors)
    errors.extend(_validate_portfolio_expression(portfolio_contract, lineage_root))
    errors.extend(_validate_gate_rows(gate_rows, selected_variant_ids))
    errors.extend(_validate_parquet_variant_ids(stage_formal_dir / "portfolio_weight_panel.parquet", selected_variant_ids))
    errors.extend(_validate_parquet_variant_ids(stage_formal_dir / "portfolio_summary.parquet", selected_variant_ids))
    errors.extend(_validate_parquet_variant_ids(stage_formal_dir / "turnover_capacity_report.parquet", selected_variant_ids))
    errors.extend(_validate_run_manifest(run_manifest))

    return ArtifactValidationResult(errors=errors)


def _infer_lineage_root(stage_formal_dir: Path) -> Path | None:
    parts = stage_formal_dir.parts
    if "06_csf_backtest_ready" not in parts:
        return None
    stage_index = parts.index("06_csf_backtest_ready")
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


def _read_test_selected_variant_ids(lineage_root: Path | None, errors: list[str]) -> list[str]:
    if lineage_root is None:
        return []
    path = lineage_root / "05_csf_test_evidence" / "author" / "formal" / "csf_selected_variants_test.csv"
    rows = _read_csv_rows(path, errors)
    return [
        str(row.get("variant_id", "")).strip()
        for row in rows
        if str(row.get("status", "")).strip() == "selected" and str(row.get("variant_id", "")).strip()
    ]


def _validate_portfolio_expression(portfolio_contract: dict[str, Any], lineage_root: Path | None) -> list[str]:
    if lineage_root is None:
        return []
    route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
    try:
        route_payload = yaml.safe_load(route_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return [f"portfolio_contract.yaml: mandate research_route.yaml read failed: {exc}"]
    expected = str(route_payload.get("portfolio_expression", "")).strip()
    observed = str(portfolio_contract.get("portfolio_expression", "")).strip()
    if expected and observed != expected:
        return [
            "portfolio_contract.yaml: portfolio_expression must match mandate research_route.yaml; "
            f"expected={expected!r}; observed={observed!r}"
        ]
    return []


def _validate_gate_rows(gate_rows: list[dict[str, str]], selected_variant_ids: list[str]) -> list[str]:
    errors: list[str] = []
    gate_ids = {str(row.get("variant_id", "")).strip() for row in gate_rows if str(row.get("variant_id", "")).strip()}
    missing = sorted(set(selected_variant_ids) - gate_ids)
    if missing:
        errors.append(f"csf_backtest_gate_table.csv: missing selected variants {missing!r}")

    for row in gate_rows:
        variant_id = str(row.get("variant_id", "")).strip()
        if variant_id and variant_id not in selected_variant_ids:
            errors.append(
                "csf_backtest_gate_table.csv: variant_id rows must stay within test-selected variants; "
                f"outside={[variant_id]!r}"
            )
        try:
            mean_net_return = float(str(row.get("mean_net_return", "")).strip())
        except ValueError:
            errors.append("csf_backtest_gate_table.csv: mean_net_return must be numeric")
            continue
        if mean_net_return <= 0:
            errors.append("csf_backtest_gate_table.csv: mean_net_return must be > 0 for every selected variant")
    return errors


def _validate_parquet_variant_ids(path: Path, selected_variant_ids: list[str]) -> list[str]:
    errors: list[str] = []
    rows = _read_parquet_rows(path, errors)
    if not rows:
        return errors
    observed = {str(row.get("variant_id", "")).strip() for row in rows if str(row.get("variant_id", "")).strip()}
    outside = sorted(observed - set(selected_variant_ids))
    if outside:
        errors.append(f"{path.name}: variant_id rows must stay within test-selected variants; outside={outside!r}")
    return errors


def _validate_run_manifest(run_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    input_roots = _string_list(run_manifest.get("input_roots"))
    for expected in [EXPECTED_SELECTED_VARIANTS_REFERENCE, EXPECTED_TEST_GATE_REFERENCE]:
        if expected not in input_roots:
            errors.append(f"run_manifest.json: input_roots must bind to {expected}")

    stage_outputs = set(_string_list(run_manifest.get("stage_outputs")))
    missing_outputs = sorted(REQUIRED_STAGE_OUTPUTS - stage_outputs)
    if missing_outputs:
        errors.append(f"run_manifest.json: stage_outputs missing required outputs {missing_outputs!r}")
    if str(run_manifest.get("source_stage", "")).strip() != "csf_test_evidence":
        errors.append("run_manifest.json: source_stage must be csf_test_evidence")
    return errors


if __name__ == "__main__":
    raise SystemExit("Use validate_csf_backtest_ready_semantics() from runtime/preflight.")
