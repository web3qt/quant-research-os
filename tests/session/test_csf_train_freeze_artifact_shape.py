from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_train_runtime import build_csf_train_freeze_from_signal_ready, scaffold_csf_train_freeze
from tests.runtime.test_csf_signal_ready_semantic_validation import _build_valid_formal_dir
from tests.runtime.test_csf_signal_ready_runtime import _write_yaml
from tests.runtime.test_csf_train_runtime import _csf_train_freeze_draft


def _valid_train_draft() -> dict:
    draft = _csf_train_freeze_draft(confirmed=True)
    search = draft["groups"]["search_governance_contract"]["draft"]
    search["candidate_variant_ids"] = ["baseline_v1", "beta_neutral_v1"]
    search["kept_variant_ids"] = ["baseline_v1"]
    search["rejected_variant_ids"] = ["beta_neutral_v1"]
    search["frozen_signal_contract_reference"] = "03_csf_signal_ready/author/formal/factor_contract.md"
    delivery = draft["groups"]["delivery_contract"]["draft"]
    delivery["machine_artifacts"] = [
        "csf_train_freeze.yaml",
        "train_factor_quality.parquet",
        "train_variant_ledger.csv",
        "train_variant_rejects.csv",
    ]
    delivery["consumer_stage"] = "csf_test_evidence"
    return draft


def _prepare_valid_csf_train_freeze(lineage_root: Path) -> Path:
    _build_valid_formal_dir(lineage_root)
    stage_dir = scaffold_csf_train_freeze(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_train_freeze_draft.yaml", _valid_train_draft())
    build_csf_train_freeze_from_signal_ready(lineage_root)
    return stage_dir


def test_csf_train_freeze_scaffold_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _build_valid_formal_dir(lineage_root)

    stage_dir = scaffold_csf_train_freeze(lineage_root)

    draft = yaml.safe_load(
        (stage_dir / "author" / "draft" / "csf_train_freeze_draft.yaml").read_text(encoding="utf-8")
    )
    assert set(draft["groups"]) == {
        "preprocess_contract",
        "neutralization_contract",
        "ranking_bucket_contract",
        "rebalance_contract",
        "search_governance_contract",
        "delivery_contract",
    }
    assert set(draft["groups"]["search_governance_contract"]["draft"]) == {
        "candidate_variant_ids",
        "kept_variant_ids",
        "rejected_variant_ids",
        "selection_rule",
        "frozen_signal_contract_reference",
        "train_governable_axes",
        "non_governable_axes_after_signal",
        "non_governable_axis_reject_rule",
    }


def test_csf_train_freeze_build_shape_matches_contract(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("csf_train_freeze"))

    assert result.valid is True
    assert result.errors == []


def test_csf_train_freeze_yaml_key_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = yaml.safe_load((formal_dir / "csf_train_freeze.yaml").read_text(encoding="utf-8"))

    assert set(payload) == {
        "stage",
        "lineage_id",
        "preprocess_contract",
        "neutralization_contract",
        "ranking_bucket_contract",
        "rebalance_contract",
        "search_governance_contract",
        "delivery_contract",
    }
    assert isinstance(payload["ranking_bucket_contract"]["quantile_count"], int)
    assert isinstance(payload["ranking_bucket_contract"]["min_names_per_bucket"], int)


def test_csf_train_freeze_bucket_diagnostics_uses_min_names_per_bucket(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_train_freeze(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    rows = pq.read_table(formal_dir / "train_bucket_diagnostics.parquet").to_pylist()

    assert rows == [{"bucket_id": "q1", "min_names": 10, "ranking_scope": "full_universe"}]
