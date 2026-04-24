from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.csf_train_freeze_contract_runtime import validate_csf_train_freeze_semantics
from tests.session.test_csf_train_freeze_artifact_shape import _prepare_valid_csf_train_freeze
from tests.runtime.test_csf_signal_ready_runtime import _write_yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def test_csf_train_freeze_semantics_accepts_runtime_built_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)

    result = validate_csf_train_freeze_semantics(stage_dir / "author" / "formal", lineage_root)

    assert result.valid is True
    assert result.errors == []


def test_csf_train_freeze_semantics_rejects_kept_variant_outside_candidate_set(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = _load_yaml(formal_dir / "csf_train_freeze.yaml")
    payload["search_governance_contract"]["kept_variant_ids"] = ["winner_from_backtest"]
    _write_yaml(formal_dir / "csf_train_freeze.yaml", payload)

    result = validate_csf_train_freeze_semantics(formal_dir, lineage_root)

    assert (
        "csf_train_freeze.yaml: kept_variant_ids must be a subset of candidate_variant_ids; outside=['winner_from_backtest']"
        in result.errors
    )


def test_csf_train_freeze_semantics_rejects_governable_axis_overlap(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = _load_yaml(formal_dir / "csf_train_freeze.yaml")
    payload["search_governance_contract"]["train_governable_axes"].append("raw_factor_fields")
    _write_yaml(formal_dir / "csf_train_freeze.yaml", payload)

    result = validate_csf_train_freeze_semantics(formal_dir, lineage_root)

    assert (
        "csf_train_freeze.yaml: train_governable_axes overlap non_governable_axes_after_signal; observed=['raw_factor_fields']"
        in result.errors
    )


def test_csf_train_freeze_semantics_rejects_missing_reject_ledger_rows(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    (formal_dir / "train_variant_rejects.csv").write_text(
        "variant_id,reject_reason\n",
        encoding="utf-8",
    )

    result = validate_csf_train_freeze_semantics(formal_dir, lineage_root)

    assert (
        "train_variant_rejects.csv: rejected_variant_ids require explicit reject_reason rows; missing=['beta_neutral_v1']"
        in result.errors
    )


def test_csf_train_freeze_semantics_rejects_quality_without_kept_variant(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet_rows(
        formal_dir / "train_factor_quality.parquet",
        [{"variant_id": "rejected_only", "quality_score": 1.0, "quality_status": "rejected"}],
    )

    result = validate_csf_train_freeze_semantics(formal_dir, lineage_root)

    assert (
        "train_factor_quality.parquet: requires at least one row for each kept_variant_id; missing=['baseline_v1']"
        in result.errors
    )


def test_csf_train_freeze_semantics_rejects_missing_signal_contract_binding(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = _load_yaml(formal_dir / "csf_train_freeze.yaml")
    payload["search_governance_contract"]["frozen_signal_contract_reference"] = "03_csf_signal_ready/old.md"
    _write_yaml(formal_dir / "csf_train_freeze.yaml", payload)

    result = validate_csf_train_freeze_semantics(formal_dir, lineage_root)

    assert (
        "csf_train_freeze.yaml: frozen_signal_contract_reference must bind to 03_csf_signal_ready/author/formal/factor_contract.md"
        in result.errors
    )


def test_csf_train_freeze_semantics_rejects_run_manifest_missing_signal_inputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    run_manifest = yaml.safe_load((formal_dir / "run_manifest.json").read_text(encoding="utf-8"))
    run_manifest["input_roots"] = ["author/draft/csf_train_freeze_draft.yaml"]
    (formal_dir / "run_manifest.json").write_text(
        __import__("json").dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_train_freeze_semantics(formal_dir, lineage_root)

    assert "run_manifest.json: input_roots must include 03_csf_signal_ready formal artifacts" in result.errors
