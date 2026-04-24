from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


EXPECTED_TRAIN_FREEZE_REFERENCE = "../04_csf_train_freeze/author/formal/csf_train_freeze.yaml"
EXPECTED_TRAIN_VARIANT_LEDGER_REFERENCE = "../04_csf_train_freeze/author/formal/train_variant_ledger.csv"
REQUIRED_STAGE_OUTPUTS = {
    "rank_ic_timeseries.parquet",
    "rank_ic_summary.json",
    "bucket_returns.parquet",
    "monotonicity_report.json",
    "breadth_coverage_report.parquet",
    "subperiod_stability_report.json",
    "filter_condition_panel.parquet",
    "target_strategy_condition_compare.parquet",
    "gated_vs_ungated_summary.json",
    "csf_test_gate_table.csv",
    "csf_selected_variants_test.csv",
    "csf_test_gate_decision.md",
    "csf_test_contract.md",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
}


def validate_csf_test_evidence_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    lineage_root = lineage_root.resolve() if lineage_root is not None else _infer_lineage_root(stage_formal_dir)
    errors: list[str] = []

    rank_ic_summary = _load_json_mapping(stage_formal_dir / "rank_ic_summary.json", errors)
    run_manifest = _load_json_mapping(stage_formal_dir / "run_manifest.json", errors)
    selected_rows = _read_csv_rows(stage_formal_dir / "csf_selected_variants_test.csv", errors)
    gate_rows = _read_csv_rows(stage_formal_dir / "csf_test_gate_table.csv", errors)
    if rank_ic_summary is None or run_manifest is None:
        return ArtifactValidationResult(errors=errors)

    selected_variant_ids = _csv_variant_ids(selected_rows, status_filter="selected")
    summary_variant_ids = _string_list(rank_ic_summary.get("selected_variant_ids"))
    train_kept_ids = _read_train_kept_variant_ids(lineage_root, errors)

    errors.extend(_validate_selected_variants(selected_variant_ids, train_kept_ids))
    errors.extend(_validate_summary_variant_ids(summary_variant_ids, selected_variant_ids))
    errors.extend(_validate_gate_table(gate_rows, selected_variant_ids))
    errors.extend(_validate_standalone_rank_ic(rank_ic_summary))
    errors.extend(_validate_parquet_variant_ids(stage_formal_dir / "rank_ic_timeseries.parquet", selected_variant_ids))
    errors.extend(_validate_run_manifest(run_manifest))

    return ArtifactValidationResult(errors=errors)


def _infer_lineage_root(stage_formal_dir: Path) -> Path | None:
    parts = stage_formal_dir.parts
    if "05_csf_test_evidence" not in parts:
        return None
    stage_index = parts.index("05_csf_test_evidence")
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


def _csv_variant_ids(rows: list[dict[str, str]], *, status_filter: str | None = None) -> list[str]:
    variant_ids: list[str] = []
    for row in rows:
        if status_filter is not None and str(row.get("status", "")).strip() != status_filter:
            continue
        variant_id = str(row.get("variant_id", "")).strip()
        if variant_id:
            variant_ids.append(variant_id)
    return variant_ids


def _read_train_kept_variant_ids(lineage_root: Path | None, errors: list[str]) -> list[str]:
    if lineage_root is None:
        return []
    ledger_path = lineage_root / "04_csf_train_freeze" / "author" / "formal" / "train_variant_ledger.csv"
    rows = _read_csv_rows(ledger_path, errors)
    return [
        str(row.get("variant_id", "")).strip()
        for row in rows
        if str(row.get("status", "")).strip() == "kept" and str(row.get("variant_id", "")).strip()
    ]


def _validate_selected_variants(selected_variant_ids: list[str], train_kept_ids: list[str]) -> list[str]:
    errors: list[str] = []
    if not selected_variant_ids:
        errors.append("csf_selected_variants_test.csv: expected at least one selected variant")
        return errors
    outside = sorted(set(selected_variant_ids) - set(train_kept_ids))
    if outside:
        errors.append(
            "csf_selected_variants_test.csv: selected variants must be a subset of train kept variants; "
            f"outside={outside!r}"
        )
    return errors


def _validate_summary_variant_ids(summary_variant_ids: list[str], selected_variant_ids: list[str]) -> list[str]:
    missing = sorted(set(selected_variant_ids) - set(summary_variant_ids))
    extra = sorted(set(summary_variant_ids) - set(selected_variant_ids))
    if missing or extra:
        return [
            "rank_ic_summary.json: selected_variant_ids must match csf_selected_variants_test.csv; "
            f"missing={missing!r}; extra={extra!r}"
        ]
    return []


def _validate_gate_table(gate_rows: list[dict[str, str]], selected_variant_ids: list[str]) -> list[str]:
    gate_ids = {str(row.get("variant_id", "")).strip() for row in gate_rows if str(row.get("variant_id", "")).strip()}
    missing = sorted(set(selected_variant_ids) - gate_ids)
    if missing:
        return [f"csf_test_gate_table.csv: missing selected variants {missing!r}"]
    return []


def _validate_standalone_rank_ic(rank_ic_summary: dict[str, Any]) -> list[str]:
    if str(rank_ic_summary.get("factor_role", "")).strip() != "standalone_alpha":
        return []
    mean_rank_ic = rank_ic_summary.get("mean_rank_ic")
    if not isinstance(mean_rank_ic, (int, float)) or isinstance(mean_rank_ic, bool) or mean_rank_ic <= 0:
        return ["rank_ic_summary.json: standalone_alpha mean_rank_ic must be > 0 before review"]
    return []


def _validate_parquet_variant_ids(path: Path, selected_variant_ids: list[str]) -> list[str]:
    errors: list[str] = []
    rows = _read_parquet_rows(path, errors)
    if not rows:
        return errors
    observed = {str(row.get("variant_id", "")).strip() for row in rows if str(row.get("variant_id", "")).strip()}
    outside = sorted(observed - set(selected_variant_ids))
    if outside:
        errors.append(f"{path.name}: variant_id rows must stay within selected variants; outside={outside!r}")
    return errors


def _validate_run_manifest(run_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    input_roots = _string_list(run_manifest.get("input_roots"))
    for expected in [EXPECTED_TRAIN_FREEZE_REFERENCE, EXPECTED_TRAIN_VARIANT_LEDGER_REFERENCE]:
        if expected not in input_roots:
            errors.append(f"run_manifest.json: input_roots must bind to {expected}")

    stage_outputs = set(_string_list(run_manifest.get("stage_outputs")))
    missing_outputs = sorted(REQUIRED_STAGE_OUTPUTS - stage_outputs)
    if missing_outputs:
        errors.append(f"run_manifest.json: stage_outputs missing required outputs {missing_outputs!r}")
    if str(run_manifest.get("source_stage", "")).strip() != "csf_train_freeze":
        errors.append("run_manifest.json: source_stage must be csf_train_freeze")
    return errors


if __name__ == "__main__":
    raise SystemExit("Use validate_csf_test_evidence_semantics() from runtime/preflight.")
