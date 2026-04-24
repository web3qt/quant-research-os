from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


EXPECTED_SIGNAL_CONTRACT_REFERENCE = "03_csf_signal_ready/author/formal/factor_contract.md"
REQUIRED_STAGE_OUTPUTS = {
    "csf_train_freeze.yaml",
    "train_factor_quality.parquet",
    "train_variant_ledger.csv",
    "train_variant_rejects.csv",
    "train_bucket_diagnostics.parquet",
    "train_neutralization_diagnostics.parquet",
    "csf_train_contract.md",
    "csf_train_freeze_gate_decision.md",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
}


def validate_csf_train_freeze_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    lineage_root = lineage_root.resolve() if lineage_root is not None else _infer_lineage_root(stage_formal_dir)
    errors: list[str] = []

    freeze_payload = _load_yaml_mapping(stage_formal_dir / "csf_train_freeze.yaml", errors)
    run_manifest = _load_json_mapping(stage_formal_dir / "run_manifest.json", errors)
    if freeze_payload is None or run_manifest is None:
        return ArtifactValidationResult(errors=errors)

    governance = _mapping(freeze_payload.get("search_governance_contract"))
    ranking = _mapping(freeze_payload.get("ranking_bucket_contract"))
    neutralization = _mapping(freeze_payload.get("neutralization_contract"))
    delivery = _mapping(freeze_payload.get("delivery_contract"))

    candidate_ids = _string_list(governance.get("candidate_variant_ids"))
    kept_ids = _string_list(governance.get("kept_variant_ids"))
    rejected_ids = _string_list(governance.get("rejected_variant_ids"))

    errors.extend(_validate_variant_sets(candidate_ids, kept_ids, rejected_ids, governance))
    errors.extend(_validate_signal_contract_reference(governance, lineage_root))
    errors.extend(_validate_variant_ledger(stage_formal_dir / "train_variant_ledger.csv", candidate_ids, kept_ids, rejected_ids))
    errors.extend(_validate_reject_ledger(stage_formal_dir / "train_variant_rejects.csv", rejected_ids))
    errors.extend(_validate_train_quality(stage_formal_dir / "train_factor_quality.parquet", kept_ids))
    errors.extend(_validate_bucket_diagnostics(stage_formal_dir / "train_bucket_diagnostics.parquet", ranking))
    errors.extend(_validate_neutralization_diagnostics(stage_formal_dir / "train_neutralization_diagnostics.parquet", neutralization))
    errors.extend(_validate_delivery_contract(delivery))
    errors.extend(_validate_run_manifest(run_manifest, candidate_ids, kept_ids, rejected_ids, governance))

    return ArtifactValidationResult(errors=errors)


def _infer_lineage_root(stage_formal_dir: Path) -> Path | None:
    parts = stage_formal_dir.parts
    if "04_csf_train_freeze" not in parts:
        return None
    stage_index = parts.index("04_csf_train_freeze")
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


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


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


def _validate_variant_sets(
    candidate_ids: list[str],
    kept_ids: list[str],
    rejected_ids: list[str],
    governance: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    candidate_set = set(candidate_ids)
    kept_outside = sorted(set(kept_ids) - candidate_set)
    rejected_outside = sorted(set(rejected_ids) - candidate_set)
    if kept_outside:
        errors.append(
            f"csf_train_freeze.yaml: kept_variant_ids must be a subset of candidate_variant_ids; outside={kept_outside!r}"
        )
    if rejected_outside:
        errors.append(
            f"csf_train_freeze.yaml: rejected_variant_ids must be a subset of candidate_variant_ids; outside={rejected_outside!r}"
        )

    overlap = sorted(set(kept_ids) & set(rejected_ids))
    if overlap:
        errors.append(f"csf_train_freeze.yaml: kept_variant_ids overlap rejected_variant_ids; observed={overlap!r}")
    missing_disposition = sorted(candidate_set - set(kept_ids) - set(rejected_ids))
    if missing_disposition:
        errors.append(
            f"csf_train_freeze.yaml: every candidate_variant_id must be kept or rejected; missing={missing_disposition!r}"
        )

    governable = _string_list(governance.get("train_governable_axes"))
    non_governable = _string_list(governance.get("non_governable_axes_after_signal"))
    axis_overlap = sorted(set(governable) & set(non_governable))
    if axis_overlap:
        errors.append(
            f"csf_train_freeze.yaml: train_governable_axes overlap non_governable_axes_after_signal; observed={axis_overlap!r}"
        )
    return errors


def _validate_signal_contract_reference(governance: dict[str, Any], lineage_root: Path | None) -> list[str]:
    reference = str(governance.get("frozen_signal_contract_reference", "")).strip()
    if reference != EXPECTED_SIGNAL_CONTRACT_REFERENCE:
        return [
            "csf_train_freeze.yaml: frozen_signal_contract_reference must bind to "
            f"{EXPECTED_SIGNAL_CONTRACT_REFERENCE}"
        ]
    if lineage_root is None:
        return []
    if not (lineage_root / EXPECTED_SIGNAL_CONTRACT_REFERENCE).exists():
        return ["csf_train_freeze.yaml: referenced csf_signal_ready factor_contract.md is missing"]
    return []


def _validate_variant_ledger(
    path: Path,
    candidate_ids: list[str],
    kept_ids: list[str],
    rejected_ids: list[str],
) -> list[str]:
    errors: list[str] = []
    rows = _read_csv_rows(path, errors)
    if not rows:
        return errors

    ledger_by_id = {str(row.get("variant_id", "")).strip(): row for row in rows if str(row.get("variant_id", "")).strip()}
    missing_candidates = sorted(set(candidate_ids) - set(ledger_by_id))
    if missing_candidates:
        errors.append(f"train_variant_ledger.csv: candidate_variant_ids missing ledger rows; missing={missing_candidates!r}")

    for variant_id in kept_ids:
        status = str(ledger_by_id.get(variant_id, {}).get("status", "")).strip()
        if status and status != "kept":
            errors.append(f"train_variant_ledger.csv: kept variant {variant_id} must have status kept")
    for variant_id in rejected_ids:
        status = str(ledger_by_id.get(variant_id, {}).get("status", "")).strip()
        if status and status != "rejected":
            errors.append(f"train_variant_ledger.csv: rejected variant {variant_id} must have status rejected")
    return errors


def _validate_reject_ledger(path: Path, rejected_ids: list[str]) -> list[str]:
    errors: list[str] = []
    rows = _read_csv_rows(path, errors)
    rows_with_reason = {
        str(row.get("variant_id", "")).strip()
        for row in rows
        if str(row.get("variant_id", "")).strip() and str(row.get("reject_reason", "")).strip()
    }
    missing = sorted(set(rejected_ids) - rows_with_reason)
    if missing:
        errors.append(f"train_variant_rejects.csv: rejected_variant_ids require explicit reject_reason rows; missing={missing!r}")
    return errors


def _validate_train_quality(path: Path, kept_ids: list[str]) -> list[str]:
    errors: list[str] = []
    rows = _read_parquet_rows(path, errors)
    if not rows:
        return errors

    quality_ids = {str(row.get("variant_id", "")).strip() for row in rows if str(row.get("variant_id", "")).strip()}
    missing = sorted(set(kept_ids) - quality_ids)
    if missing:
        errors.append(f"train_factor_quality.parquet: requires at least one row for each kept_variant_id; missing={missing!r}")

    for row in rows:
        score = row.get("quality_score")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            errors.append("train_factor_quality.parquet: quality_score must be numeric")
            break
    return errors


def _validate_bucket_diagnostics(path: Path, ranking: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = _read_parquet_rows(path, errors)
    if not rows:
        return errors

    min_names = ranking.get("min_names_per_bucket")
    ranking_scope = str(ranking.get("ranking_scope", "")).strip()
    if not isinstance(min_names, int) or isinstance(min_names, bool):
        return ["csf_train_freeze.yaml: ranking_bucket_contract.min_names_per_bucket must be integer"]
    for row in rows:
        if row.get("min_names") != min_names:
            errors.append("train_bucket_diagnostics.parquet: min_names must match ranking_bucket_contract.min_names_per_bucket")
            break
        if str(row.get("ranking_scope", "")).strip() != ranking_scope:
            errors.append("train_bucket_diagnostics.parquet: ranking_scope must match csf_train_freeze.yaml")
            break
    return errors


def _validate_neutralization_diagnostics(path: Path, neutralization: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = _read_parquet_rows(path, errors)
    if not rows:
        return errors

    policy = str(neutralization.get("neutralization_policy", "")).strip()
    group_reference = str(neutralization.get("group_taxonomy_reference", "")).strip()
    beta_window = str(neutralization.get("beta_estimation_window", "")).strip()
    for row in rows:
        if str(row.get("neutralization_policy", "")).strip() != policy:
            errors.append("train_neutralization_diagnostics.parquet: neutralization_policy must match csf_train_freeze.yaml")
            break
        if str(row.get("group_taxonomy_reference", "")).strip() != group_reference:
            errors.append("train_neutralization_diagnostics.parquet: group_taxonomy_reference must match csf_train_freeze.yaml")
            break
        if str(row.get("beta_estimation_window", "")).strip() != beta_window:
            errors.append("train_neutralization_diagnostics.parquet: beta_estimation_window must match csf_train_freeze.yaml")
            break
    return errors


def _validate_delivery_contract(delivery: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if delivery.get("consumer_stage") != "csf_test_evidence":
        errors.append("csf_train_freeze.yaml: delivery_contract.consumer_stage must be csf_test_evidence")
    machine_artifacts = set(_string_list(delivery.get("machine_artifacts")))
    missing = sorted({"csf_train_freeze.yaml", "train_factor_quality.parquet", "train_variant_ledger.csv"} - machine_artifacts)
    if missing:
        errors.append(f"csf_train_freeze.yaml: delivery_contract.machine_artifacts missing required machine artifacts; missing={missing!r}")
    return errors


def _validate_run_manifest(
    run_manifest: dict[str, Any],
    candidate_ids: list[str],
    kept_ids: list[str],
    rejected_ids: list[str],
    governance: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if run_manifest.get("source_stage") != "csf_signal_ready":
        errors.append("run_manifest.json: source_stage must be csf_signal_ready")

    input_roots = run_manifest.get("input_roots")
    if not isinstance(input_roots, list) or not any("03_csf_signal_ready" in str(item) for item in input_roots):
        errors.append("run_manifest.json: input_roots must include 03_csf_signal_ready formal artifacts")
    if not isinstance(input_roots, list) or not any("csf_train_freeze_draft.yaml" in str(item) for item in input_roots):
        errors.append("run_manifest.json: input_roots must include author/draft/csf_train_freeze_draft.yaml")

    stage_outputs = run_manifest.get("stage_outputs")
    if not isinstance(stage_outputs, list):
        errors.append("run_manifest.json: stage_outputs must be a list")
    else:
        missing_outputs = sorted(REQUIRED_STAGE_OUTPUTS - set(map(str, stage_outputs)))
        if missing_outputs:
            errors.append(f"run_manifest.json: stage_outputs missing required artifacts; missing={missing_outputs!r}")

    if _string_list(run_manifest.get("candidate_variant_ids")) != candidate_ids:
        errors.append("run_manifest.json: candidate_variant_ids must match csf_train_freeze.yaml")
    if _string_list(run_manifest.get("kept_variant_ids")) != kept_ids:
        errors.append("run_manifest.json: kept_variant_ids must match csf_train_freeze.yaml")
    if _string_list(run_manifest.get("rejected_variant_ids")) != rejected_ids:
        errors.append("run_manifest.json: rejected_variant_ids must match csf_train_freeze.yaml")
    if run_manifest.get("frozen_signal_contract_reference") != governance.get("frozen_signal_contract_reference"):
        errors.append("run_manifest.json: frozen_signal_contract_reference must match csf_train_freeze.yaml")
    return errors


if __name__ == "__main__":
    raise SystemExit("Use validate_csf_train_freeze_semantics() from runtime/preflight.")
