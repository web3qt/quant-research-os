from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.tss_test_evidence_contract_runtime import validate_tss_test_evidence_semantics
from runtime.tools.tss_test_evidence_runtime import build_tss_test_evidence_from_train_freeze
from tests.runtime.test_tss_test_evidence_runtime import (
    _prepare_tss_train_freeze_stage,
    _tss_test_evidence_draft,
    _write_yaml,
)


def _build_valid_tss_test_evidence(tmp_path: Path) -> tuple[Path, Path]:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_train_freeze_stage(lineage_root)
    stage_dir = lineage_root / "05_tss_test_evidence"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml",
        _tss_test_evidence_draft(confirmed=True),
    )

    build_tss_test_evidence_from_train_freeze(lineage_root)
    return lineage_root, stage_dir / "author" / "formal"


def test_valid_runtime_output_passes_tss_test_evidence_semantic_validation(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert result.errors == []


def test_rejects_missing_selected_variant_membership_proof_row(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    membership_path = formal_dir / "selected_variant_membership_proof.csv"
    membership_path.write_text(membership_path.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert result.errors == [
        "selected_variant_membership_proof.csv: missing selected rows [('baseline_v1', '1d')]"
    ]


def test_rejects_stale_upstream_binding_digest_ledger(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    train_variant_ledger = lineage_root / "04_tss_train_freeze" / "author" / "formal" / "train_variant_ledger.csv"
    train_variant_ledger.write_text(
        "variant_id,status,selection_rule\nbaseline_v1,kept,changed-after-build\n",
        encoding="utf-8",
    )

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any(
        "upstream_binding_digest_ledger.yaml: digest mismatch for train_variant_ledger" in error
        for error in result.errors
    )


def test_rejects_digest_ledger_binding_with_wrong_canonical_path(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    ledger_path = formal_dir / "upstream_binding_digest_ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    for binding in ledger["bindings"]:
        if binding["logical_name"] == "train_threshold_ledger":
            binding["path"] = "04_tss_train_freeze/author/formal/train_variant_ledger.csv"
            binding["digest"] = next(
                item["digest"] for item in ledger["bindings"] if item["logical_name"] == "train_variant_ledger"
            )
            break
    ledger_path.write_text(yaml.safe_dump(ledger, sort_keys=False), encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any(
        "upstream_binding_digest_ledger.yaml: path for train_threshold_ledger must be "
        "04_tss_train_freeze/author/formal/train_threshold_ledger.csv" in error
        for error in result.errors
    )


def test_rejects_duplicate_required_digest_ledger_bindings(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    ledger_path = formal_dir / "upstream_binding_digest_ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    duplicate = next(item for item in ledger["bindings"] if item["logical_name"] == "train_variant_ledger")
    ledger["bindings"].append(dict(duplicate))
    ledger_path.write_text(yaml.safe_dump(ledger, sort_keys=False), encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "upstream_binding_digest_ledger.yaml: duplicate required bindings ['train_variant_ledger']"
        in result.errors
    )


def test_rejects_stale_train_variant_rejects_digest(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    train_variant_rejects = lineage_root / "04_tss_train_freeze" / "author" / "formal" / "train_variant_rejects.csv"
    train_variant_rejects.write_text("variant_id,reject_reason\nleaked_variant,changed-after-build\n", encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any(
        "upstream_binding_digest_ledger.yaml: digest mismatch for train_variant_rejects" in error
        for error in result.errors
    )


def test_rejects_non_pass_train_freeze_review_closure_status(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    closure_path = lineage_root / "04_tss_train_freeze" / "review" / "closure" / "stage_completion_certificate.yaml"
    closure = yaml.safe_load(closure_path.read_text(encoding="utf-8"))
    closure["final_verdict"] = "WARN"
    closure["stage_status"] = ""
    closure_path.write_text(yaml.safe_dump(closure, sort_keys=False), encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any(
        "upstream_binding_digest_ledger.yaml: train_freeze_review_closure final_verdict must be PASS-like; got 'WARN'"
        in error
        for error in result.errors
    )
    assert any(
        "upstream_binding_digest_ledger.yaml: train_freeze_review_closure stage_status must be PASS-like; got ''"
        in error
        for error in result.errors
    )


def test_rejects_selected_variant_outside_train_kept_set(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    selected_path = formal_dir / "tss_selected_variants_test.csv"
    selected_path.write_text("variant_id,horizon,status\nleaked_variant,1d,selected\n", encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "tss_selected_variants_test.csv: selected variants must be a subset of train kept variants; "
        "outside=['leaked_variant']"
    ) in result.errors


def test_rejects_selected_variant_outside_train_kept_set_without_horizon_column(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    selected_path = formal_dir / "tss_selected_variants_test.csv"
    selected_path.write_text("variant_id,status\nleaked_variant,selected\n", encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "tss_selected_variants_test.csv: selected variants must be a subset of train kept variants; "
        "outside=['leaked_variant']"
    ) in result.errors


def test_accepts_date_only_test_window_end_for_intraday_event_on_same_date(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    attestation_path = formal_dir / "split_threshold_attestation.yaml"
    attestation = yaml.safe_load(attestation_path.read_text(encoding="utf-8"))
    attestation["test_window"]["start"] = "2024-01-02"
    attestation["test_window"]["end"] = "2024-01-02"
    attestation["label_window"]["max_label_timestamp"] = "2024-01-02"
    attestation_path.write_text(yaml.safe_dump(attestation, sort_keys=False), encoding="utf-8")

    event_path = formal_dir / "event_forward_return.parquet"
    rows = pq.read_table(event_path).to_pylist()
    rows[0]["timestamp"] = "2024-01-02T12:00:00+00:00"
    rows[0]["label_timestamp"] = "2024-01-02T13:00:00+00:00"
    pq.write_table(pa.Table.from_pylist(rows), event_path)

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert not any("event_forward_return.parquet: timestamp outside test_window" in error for error in result.errors)
    assert not any(
        "event_forward_return.parquet: label_timestamp exceeds label_window.max_label_timestamp" in error
        for error in result.errors
    )


def test_rejects_event_timestamp_outside_test_window(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    event_path = formal_dir / "event_forward_return.parquet"
    rows = pq.read_table(event_path).to_pylist()
    rows[0]["timestamp"] = "2024-01-01T23:59:59+00:00"
    pq.write_table(pa.Table.from_pylist(rows), event_path)

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any("event_forward_return.parquet: timestamp outside test_window" in error for error in result.errors)


def test_rejects_label_timestamp_not_after_timestamp(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    event_path = formal_dir / "event_forward_return.parquet"
    rows = pq.read_table(event_path).to_pylist()
    rows[0]["label_timestamp"] = rows[0]["timestamp"]
    pq.write_table(pa.Table.from_pylist(rows), event_path)

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any(
        "event_forward_return.parquet: label_timestamp must be after timestamp" in error
        for error in result.errors
    )


def test_rejects_run_manifest_missing_upstream_binding(tmp_path: Path) -> None:
    lineage_root, formal_dir = _build_valid_tss_test_evidence(tmp_path)
    manifest_path = formal_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["input_roots"] = []
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert result.errors == [
        "run_manifest.json: input_roots must bind to ../04_tss_train_freeze/author/formal/tss_train_freeze.yaml"
    ]
