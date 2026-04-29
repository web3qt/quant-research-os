from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


REQUIRED_INPUT_ROOTS = {
    "../01_mandate/author/formal/time_split.json",
    "../04_tss_train_freeze/author/formal/tss_train_freeze.yaml",
    "../04_tss_train_freeze/author/formal/train_variant_ledger.csv",
    "../04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
    "../04_tss_train_freeze/author/formal/train_variant_rejects.csv",
    "../04_tss_train_freeze/review/closure/stage_completion_certificate.yaml",
}
REQUIRED_STAGE_OUTPUTS = {
    "event_forward_return.parquet",
    "signal_performance_summary.json",
    "tss_test_gate_table.csv",
    "tss_selected_variants_test.csv",
    "split_threshold_attestation.yaml",
    "selected_variant_membership_proof.csv",
    "upstream_binding_digest_ledger.yaml",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
}

_REQUIRED_INPUT_ROOTS_ORDER = [
    "../04_tss_train_freeze/author/formal/tss_train_freeze.yaml",
    "../01_mandate/author/formal/time_split.json",
    "../04_tss_train_freeze/author/formal/train_variant_ledger.csv",
    "../04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
    "../04_tss_train_freeze/author/formal/train_variant_rejects.csv",
    "../04_tss_train_freeze/review/closure/stage_completion_certificate.yaml",
]
_REQUIRED_BINDING_NAMES = {
    "time_split",
    "train_freeze_contract",
    "train_variant_ledger",
    "train_threshold_ledger",
    "train_variant_rejects",
    "train_freeze_review_closure",
}
_EXPECTED_BINDING_PATHS = {
    "time_split": "01_mandate/author/formal/time_split.json",
    "train_freeze_contract": "04_tss_train_freeze/author/formal/tss_train_freeze.yaml",
    "train_variant_ledger": "04_tss_train_freeze/author/formal/train_variant_ledger.csv",
    "train_threshold_ledger": "04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
    "train_variant_rejects": "04_tss_train_freeze/author/formal/train_variant_rejects.csv",
    "train_freeze_review_closure": "04_tss_train_freeze/review/closure/stage_completion_certificate.yaml",
}
_EXPECTED_THRESHOLD_SOURCE = "04_tss_train_freeze/author/formal/train_threshold_ledger.csv"
_EXPECTED_THRESHOLD_ARTIFACT = "04_tss_train_freeze/author/formal/tss_train_freeze.yaml"
_PASS_LIKE_REVIEW_STATUSES = {"PASS", "CONDITIONAL PASS"}


def validate_tss_test_evidence_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    lineage_root = lineage_root.resolve() if lineage_root is not None else _infer_lineage_root(stage_formal_dir)
    errors: list[str] = []

    selected_rows = _read_csv_rows(stage_formal_dir / "tss_selected_variants_test.csv", errors)
    selected_keys = _selected_keys(selected_rows)
    selected_ids = _selected_variant_ids(selected_rows)
    train_kept_ids = _read_train_kept_variant_ids(lineage_root, errors)
    summary = _load_json_mapping(stage_formal_dir / "signal_performance_summary.json", errors)
    gate_rows = _read_csv_rows(stage_formal_dir / "tss_test_gate_table.csv", errors)
    attestation = _load_yaml_mapping(stage_formal_dir / "split_threshold_attestation.yaml", errors)
    digest_ledger = _load_yaml_mapping(stage_formal_dir / "upstream_binding_digest_ledger.yaml", errors)
    run_manifest = _load_json_mapping(stage_formal_dir / "run_manifest.json", errors)

    errors.extend(_validate_selected_variants(selected_ids, train_kept_ids))
    errors.extend(_validate_membership_proof(stage_formal_dir / "selected_variant_membership_proof.csv", selected_keys))
    if summary is not None:
        errors.extend(_validate_summary(summary, selected_ids))
    errors.extend(_validate_gate_table(gate_rows, selected_keys))
    if attestation is not None:
        errors.extend(_validate_attestation(attestation))
        errors.extend(_validate_event_forward_returns(stage_formal_dir / "event_forward_return.parquet", selected_keys, attestation))
    if digest_ledger is not None:
        errors.extend(_validate_digest_ledger(digest_ledger, lineage_root))
    if run_manifest is not None:
        errors.extend(_validate_run_manifest(run_manifest))

    return ArtifactValidationResult(errors=errors)


def _infer_lineage_root(stage_formal_dir: Path) -> Path | None:
    parts = stage_formal_dir.parts
    if "05_tss_test_evidence" not in parts:
        return None
    stage_index = parts.index("05_tss_test_evidence")
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


def _selected_keys(rows: list[dict[str, str]]) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    for row in rows:
        if str(row.get("status", "")).strip() != "selected":
            continue
        variant_id = str(row.get("variant_id", "")).strip()
        horizon = str(row.get("horizon", "")).strip()
        if variant_id and horizon:
            keys.append((variant_id, horizon))
    return keys


def _selected_variant_ids(rows: list[dict[str, str]]) -> list[str]:
    variant_ids: list[str] = []
    for row in rows:
        if str(row.get("status", "")).strip() != "selected":
            continue
        variant_id = str(row.get("variant_id", "")).strip()
        if variant_id:
            variant_ids.append(variant_id)
    return variant_ids


def _read_train_kept_variant_ids(lineage_root: Path | None, errors: list[str]) -> list[str]:
    if lineage_root is None:
        return []
    ledger_path = lineage_root / "04_tss_train_freeze" / "author" / "formal" / "train_variant_ledger.csv"
    rows = _read_csv_rows(ledger_path, errors)
    return [
        str(row.get("variant_id", "")).strip()
        for row in rows
        if str(row.get("status", "")).strip() == "kept" and str(row.get("variant_id", "")).strip()
    ]


def _validate_selected_variants(selected_ids: list[str], train_kept_ids: list[str]) -> list[str]:
    errors: list[str] = []
    if not selected_ids:
        errors.append("tss_selected_variants_test.csv: expected at least one selected variant")
        return errors
    outside = sorted(set(selected_ids) - set(train_kept_ids))
    if outside:
        errors.append(
            "tss_selected_variants_test.csv: selected variants must be a subset of train kept variants; "
            f"outside={outside!r}"
        )
    return errors


def _validate_membership_proof(path: Path, selected_keys: list[tuple[str, str]]) -> list[str]:
    errors: list[str] = []
    rows = _read_csv_rows(path, errors)
    selected_set = set(selected_keys)
    proof_counts: dict[tuple[str, str], int] = {}

    for row in rows:
        key = (str(row.get("variant_id", "")).strip(), str(row.get("horizon", "")).strip())
        if key not in selected_set:
            continue
        proof_counts[key] = proof_counts.get(key, 0) + 1
        if str(row.get("status", "")).strip() != "selected":
            errors.append(f"{path.name}: status must be selected for {key!r}")
        if str(row.get("train_kept_status", "")).strip() != "kept":
            errors.append(f"{path.name}: train_kept_status must be kept for {key!r}")
        if str(row.get("membership_verdict", "")).strip() != "pass":
            errors.append(f"{path.name}: membership_verdict must be pass for {key!r}")
        if str(row.get("threshold_source", "")).strip() != _EXPECTED_THRESHOLD_SOURCE:
            errors.append(f"{path.name}: threshold_source must be {_EXPECTED_THRESHOLD_SOURCE} for {key!r}")

    missing = sorted(key for key in selected_keys if proof_counts.get(key, 0) == 0)
    if missing:
        errors.append(f"{path.name}: missing selected rows {missing!r}")
    duplicates = sorted(key for key, count in proof_counts.items() if count > 1)
    if duplicates:
        errors.append(f"{path.name}: duplicate selected rows {duplicates!r}")
    return errors


def _validate_summary(summary: dict[str, Any], selected_ids: list[str]) -> list[str]:
    summary_ids = _string_list(summary.get("selected_variant_ids"))
    missing = sorted(set(selected_ids) - set(summary_ids))
    extra = sorted(set(summary_ids) - set(selected_ids))
    if missing or extra:
        return [
            "signal_performance_summary.json: selected_variant_ids must match tss_selected_variants_test.csv; "
            f"missing={missing!r}; extra={extra!r}"
        ]
    return []


def _validate_gate_table(gate_rows: list[dict[str, str]], selected_keys: list[tuple[str, str]]) -> list[str]:
    gate_keys = {
        (str(row.get("variant_id", "")).strip(), str(row.get("horizon", "")).strip())
        for row in gate_rows
        if str(row.get("variant_id", "")).strip() and str(row.get("horizon", "")).strip()
    }
    missing = sorted(set(selected_keys) - gate_keys)
    if missing:
        return [f"tss_test_gate_table.csv: missing selected rows {missing!r}"]
    return []


def _validate_event_forward_returns(
    path: Path,
    selected_keys: list[tuple[str, str]],
    attestation: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    rows = _read_parquet_rows(path, errors)
    if not rows:
        return errors

    selected_set = set(selected_keys)
    test_window = attestation.get("test_window") if isinstance(attestation.get("test_window"), dict) else {}
    label_window = attestation.get("label_window") if isinstance(attestation.get("label_window"), dict) else {}
    start = _parse_timestamp(test_window.get("start"), f"{path.name}: invalid test_window.start", errors, boundary="start")
    end = _parse_timestamp(test_window.get("end"), f"{path.name}: invalid test_window.end", errors, boundary="end")
    max_label = _parse_timestamp(
        label_window.get("max_label_timestamp"),
        f"{path.name}: invalid label_window.max_label_timestamp",
        errors,
        boundary="end",
    )

    for index, row in enumerate(rows):
        key = (str(row.get("variant_id", "")).strip(), str(row.get("horizon", "")).strip())
        if key not in selected_set:
            errors.append(f"{path.name}: rows must stay within selected variants; row={index}; key={key!r}")
        timestamp = _parse_timestamp(row.get("timestamp"), f"{path.name}: invalid timestamp at row {index}", errors)
        label_timestamp = _parse_timestamp(
            row.get("label_timestamp"), f"{path.name}: invalid label_timestamp at row {index}", errors
        )
        if timestamp is not None and start is not None and end is not None and not start <= timestamp <= end:
            errors.append(f"{path.name}: timestamp outside test_window at row {index}")
        if timestamp is not None and label_timestamp is not None and label_timestamp <= timestamp:
            errors.append(f"{path.name}: label_timestamp must be after timestamp at row {index}")
        if label_timestamp is not None and max_label is not None and label_timestamp > max_label:
            errors.append(f"{path.name}: label_timestamp exceeds label_window.max_label_timestamp at row {index}")
    return errors


def _validate_attestation(attestation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if str(attestation.get("stage", "")).strip() != "tss_test_evidence":
        errors.append("split_threshold_attestation.yaml: stage must be tss_test_evidence")
    if str(attestation.get("research_route", "")).strip() != "time_series_signal":
        errors.append("split_threshold_attestation.yaml: research_route must be time_series_signal")

    train_window = attestation.get("train_window") if isinstance(attestation.get("train_window"), dict) else {}
    test_window = attestation.get("test_window") if isinstance(attestation.get("test_window"), dict) else {}
    train_end = _parse_timestamp(
        train_window.get("end"), "split_threshold_attestation.yaml: invalid train_window.end", errors, boundary="end"
    )
    test_start = _parse_timestamp(
        test_window.get("start"), "split_threshold_attestation.yaml: invalid test_window.start", errors, boundary="start"
    )
    _parse_timestamp(
        train_window.get("start"), "split_threshold_attestation.yaml: invalid train_window.start", errors, boundary="start"
    )
    _parse_timestamp(
        test_window.get("end"), "split_threshold_attestation.yaml: invalid test_window.end", errors, boundary="end"
    )
    if train_end is not None and test_start is not None and test_start <= train_end:
        errors.append("split_threshold_attestation.yaml: test_window.start must be after train_window.end")

    provenance = attestation.get("threshold_provenance")
    if not isinstance(provenance, dict):
        return [*errors, "split_threshold_attestation.yaml: threshold_provenance must be a map"]
    if provenance.get("no_test_window_retuning") is not True:
        errors.append("split_threshold_attestation.yaml: threshold_provenance.no_test_window_retuning must be true")
    if str(provenance.get("source_stage", "")).strip() != "tss_train_freeze":
        errors.append("split_threshold_attestation.yaml: threshold_provenance.source_stage must be tss_train_freeze")
    if str(provenance.get("threshold_artifact", "")).strip() != _EXPECTED_THRESHOLD_ARTIFACT:
        errors.append(f"split_threshold_attestation.yaml: threshold_artifact must be {_EXPECTED_THRESHOLD_ARTIFACT}")
    if str(provenance.get("threshold_ledger", "")).strip() != _EXPECTED_THRESHOLD_SOURCE:
        errors.append(f"split_threshold_attestation.yaml: threshold_ledger must be {_EXPECTED_THRESHOLD_SOURCE}")
    return errors


def _validate_digest_ledger(digest_ledger: dict[str, Any], lineage_root: Path | None) -> list[str]:
    errors: list[str] = []
    if lineage_root is None:
        return ["upstream_binding_digest_ledger.yaml: lineage_root is required for digest validation"]
    bindings = digest_ledger.get("bindings")
    if not isinstance(bindings, list):
        return ["upstream_binding_digest_ledger.yaml: bindings must be a list"]

    by_name = {
        str(binding.get("logical_name", "")).strip(): binding
        for binding in bindings
        if isinstance(binding, dict) and str(binding.get("logical_name", "")).strip()
    }
    binding_counts: dict[str, int] = {}
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        logical_name = str(binding.get("logical_name", "")).strip()
        if logical_name:
            binding_counts[logical_name] = binding_counts.get(logical_name, 0) + 1
    missing = sorted(_REQUIRED_BINDING_NAMES - set(by_name))
    if missing:
        errors.append(f"upstream_binding_digest_ledger.yaml: missing required bindings {missing!r}")
    duplicates = sorted(name for name in _REQUIRED_BINDING_NAMES if binding_counts.get(name, 0) > 1)
    if duplicates:
        errors.append(f"upstream_binding_digest_ledger.yaml: duplicate required bindings {duplicates!r}")

    for logical_name in sorted(_REQUIRED_BINDING_NAMES):
        binding = by_name.get(logical_name)
        if not isinstance(binding, dict):
            continue
        if binding.get("required") is not True:
            errors.append(f"upstream_binding_digest_ledger.yaml: required must be true for {logical_name}")
        expected_path = _EXPECTED_BINDING_PATHS[logical_name]
        observed_path = str(binding.get("path", "")).strip()
        if observed_path != expected_path:
            errors.append(
                f"upstream_binding_digest_ledger.yaml: path for {logical_name} must be {expected_path}; "
                f"observed={observed_path!r}"
            )
            continue
        bound_path = _resolve_lineage_relative_path(lineage_root, binding.get("path"))
        if bound_path is None:
            errors.append(f"upstream_binding_digest_ledger.yaml: invalid path for {logical_name}")
            continue
        if not bound_path.exists():
            errors.append(f"upstream_binding_digest_ledger.yaml: path missing for {logical_name}: {binding.get('path')}")
            continue
        expected_digest = str(binding.get("digest", "")).strip()
        actual_digest = hashlib.sha256(bound_path.read_bytes()).hexdigest()
        if expected_digest != actual_digest:
            errors.append(
                f"upstream_binding_digest_ledger.yaml: digest mismatch for {logical_name}; "
                f"expected={expected_digest}; actual={actual_digest}"
            )
        if logical_name == "train_freeze_review_closure":
            errors.extend(_validate_train_freeze_review_closure(bound_path))
    return errors


def _resolve_lineage_relative_path(lineage_root: Path, value: Any) -> Path | None:
    relative = str(value or "").strip()
    if not relative:
        return None
    candidate = (lineage_root / relative).resolve()
    try:
        if not candidate.is_relative_to(lineage_root):
            return None
    except ValueError:
        return None
    return candidate


def _validate_train_freeze_review_closure(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return [f"upstream_binding_digest_ledger.yaml: train_freeze_review_closure yaml read failed: {exc}"]
    if not isinstance(payload, dict):
        return ["upstream_binding_digest_ledger.yaml: train_freeze_review_closure must be a yaml map"]
    if str(payload.get("stage", "")).strip() != "tss_train_freeze":
        errors.append("upstream_binding_digest_ledger.yaml: train_freeze_review_closure stage must be tss_train_freeze")
    for field_name in ["final_verdict", "stage_status"]:
        raw_status = str(payload.get(field_name, "")).strip()
        status = raw_status.upper()
        if status not in _PASS_LIKE_REVIEW_STATUSES:
            errors.append(
                "upstream_binding_digest_ledger.yaml: train_freeze_review_closure "
                f"{field_name} must be PASS-like; got {raw_status!r}"
            )
    return errors


def _validate_run_manifest(run_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    input_roots = set(_string_list(run_manifest.get("input_roots")))
    for expected in _REQUIRED_INPUT_ROOTS_ORDER:
        if expected not in input_roots:
            errors.append(f"run_manifest.json: input_roots must bind to {expected}")
            break

    stage_outputs = set(_string_list(run_manifest.get("stage_outputs")))
    missing_outputs = sorted(REQUIRED_STAGE_OUTPUTS - stage_outputs)
    if missing_outputs:
        errors.append(f"run_manifest.json: stage_outputs missing required outputs {missing_outputs!r}")
    if str(run_manifest.get("source_stage", "")).strip() != "tss_train_freeze":
        errors.append("run_manifest.json: source_stage must be tss_train_freeze")
    return errors


def _parse_timestamp(
    value: Any,
    message: str,
    errors: list[str],
    *,
    boundary: str = "start",
) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            if "T" in text:
                parsed = datetime.fromisoformat(text)
            else:
                boundary_time = time.max if boundary == "end" else time.min
                parsed = datetime.combine(datetime.fromisoformat(text).date(), boundary_time)
        except ValueError:
            errors.append(message)
            return None
    else:
        errors.append(message)
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


if __name__ == "__main__":
    raise SystemExit("Use validate_tss_test_evidence_semantics() from runtime/preflight.")
