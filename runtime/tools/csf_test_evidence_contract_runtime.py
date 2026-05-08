from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import yaml

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
    errors.extend(_validate_rank_ic_input_binding(run_manifest, stage_formal_dir, lineage_root))

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


def _validate_rank_ic_input_binding(
    run_manifest: dict[str, Any],
    stage_formal_dir: Path,
    lineage_root: Path | None,
) -> list[str]:
    binding = run_manifest.get("rank_ic_input_binding")
    if not isinstance(binding, dict):
        return ["run_manifest.json: rank_ic_input_binding must bind factor_panel and forward_return_panel before review"]

    errors: list[str] = []
    if str(binding.get("execution_mode", "")).strip() != "real_input":
        errors.append("run_manifest.json: rank_ic_input_binding.execution_mode must be real_input before review")
    for field in ("source_data_digest", "min_ts", "max_ts", "factor_panel", "forward_return_panel"):
        if not str(binding.get(field, "")).strip():
            errors.append(f"run_manifest.json: rank_ic_input_binding.{field} must be non-empty")
    for field in ("rows_read", "symbol_count", "event_count"):
        value = binding.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            errors.append(f"run_manifest.json: rank_ic_input_binding.{field} must be a positive integer")
    if errors or lineage_root is None:
        return errors

    factor_panel_path = _resolve_lineage_artifact(lineage_root, str(binding["factor_panel"]))
    forward_return_path = _resolve_lineage_artifact(lineage_root, str(binding["forward_return_panel"]))
    factor_manifest_path = lineage_root / "03_csf_signal_ready" / "author" / "formal" / "factor_manifest.yaml"
    factor_manifest = _load_yaml_mapping(factor_manifest_path, errors)
    factor_rows = _read_parquet_rows(factor_panel_path, errors)
    forward_rows = _read_parquet_rows(forward_return_path, errors)
    observed_rows = _read_parquet_rows(stage_formal_dir / "rank_ic_timeseries.parquet", errors)
    if errors:
        return errors
    if factor_manifest is None:
        return errors
    score_field = str(factor_manifest.get("final_score_field", "")).strip()
    if not score_field:
        return ["factor_manifest.yaml: final_score_field must be non-empty for rank IC validation"]

    expected_by_date = _expected_rank_ic_by_date(factor_rows, forward_rows, score_field)
    observed_by_key = {
        (str(row.get("date", "")).strip(), str(row.get("variant_id", "")).strip()): row.get("rank_ic")
        for row in observed_rows
    }
    for (date, variant_id), value in sorted(observed_by_key.items()):
        expected = expected_by_date.get(date)
        if expected is None:
            errors.append(f"rank_ic_timeseries.parquet: no computable factor/forward_return rows for date={date}")
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"rank_ic_timeseries.parquet: rank_ic for date={date} variant_id={variant_id} must be numeric")
            continue
        if not math.isclose(float(value), expected, rel_tol=1e-9, abs_tol=1e-9):
            errors.append(
                f"rank_ic_timeseries.parquet: rank_ic for date={date} variant_id={variant_id} "
                "must be computed from factor_panel.parquet and forward_return_panel.parquet; "
                f"expected {expected:g}, found {float(value):g}"
            )
    return errors


def _resolve_lineage_artifact(lineage_root: Path, relpath: str) -> Path:
    return lineage_root / relpath.strip().lstrip("./")


def _expected_rank_ic_by_date(
    factor_rows: list[dict[str, Any]],
    forward_rows: list[dict[str, Any]],
    score_field: str,
) -> dict[str, float]:
    forward_lookup = {
        (str(row.get("date", "")).strip(), str(row.get("asset", "")).strip()): row.get("forward_return")
        for row in forward_rows
    }
    values_by_date: dict[str, list[tuple[float, float]]] = {}
    for row in factor_rows:
        date = str(row.get("date", "")).strip()
        asset = str(row.get("asset", "")).strip()
        score = row.get(score_field)
        forward_return = forward_lookup.get((date, asset))
        if isinstance(score, bool) or isinstance(forward_return, bool):
            continue
        if not isinstance(score, (int, float)) or not isinstance(forward_return, (int, float)):
            continue
        values_by_date.setdefault(date, []).append((float(score), float(forward_return)))
    return {
        date: _spearman_rank_correlation(values)
        for date, values in values_by_date.items()
        if len(values) >= 2
    }


def _spearman_rank_correlation(values: list[tuple[float, float]]) -> float:
    score_ranks = _average_ranks([score for score, _ in values])
    return_ranks = _average_ranks([forward_return for _, forward_return in values])
    score_mean = sum(score_ranks) / len(score_ranks)
    return_mean = sum(return_ranks) / len(return_ranks)
    numerator = sum((x - score_mean) * (y - return_mean) for x, y in zip(score_ranks, return_ranks, strict=True))
    score_var = sum((x - score_mean) ** 2 for x in score_ranks)
    return_var = sum((y - return_mean) ** 2 for y in return_ranks)
    if score_var == 0 or return_var == 0:
        return 0.0
    return numerator / math.sqrt(score_var * return_var)


def _average_ranks(values: list[float]) -> list[float]:
    sorted_values = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    position = 0
    while position < len(sorted_values):
        end = position + 1
        while end < len(sorted_values) and sorted_values[end][0] == sorted_values[position][0]:
            end += 1
        average_rank = (position + 1 + end) / 2.0
        for _, original_index in sorted_values[position:end]:
            ranks[original_index] = average_rank
        position = end
    return ranks


if __name__ == "__main__":
    raise SystemExit("Use validate_csf_test_evidence_semantics() from runtime/preflight.")
