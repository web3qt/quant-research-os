from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/csf_train_freeze_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_csf_train_freeze_artifact_contract_exists_and_declares_stage_identity() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["schema_id"] == "csf-train-freeze-artifacts-v1"
    assert contract["schema_version"] == "v1"
    assert contract["stage"] == "csf_train_freeze"
    assert contract["stage_dir"] == "04_csf_train_freeze/author/formal"


def test_csf_train_freeze_artifact_contract_declares_all_formal_outputs() -> None:
    contract = _load_contract()

    assert set(contract["artifacts"]) == {
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


def test_csf_train_freeze_contract_locks_yaml_runtime_facing_fields() -> None:
    contract = _load_contract()
    fields = {
        field["path"]: field
        for field in contract["artifacts"]["csf_train_freeze.yaml"]["fields"]
    }

    for path in (
        "stage",
        "lineage_id",
        "preprocess_contract.winsorize_policy",
        "preprocess_contract.standardize_policy",
        "preprocess_contract.missing_fill_policy",
        "preprocess_contract.coverage_floor_rule",
        "neutralization_contract.neutralization_policy",
        "neutralization_contract.beta_estimation_window",
        "neutralization_contract.group_taxonomy_reference",
        "neutralization_contract.residualization_formula",
        "ranking_bucket_contract.ranking_scope",
        "ranking_bucket_contract.bucket_schema",
        "ranking_bucket_contract.quantile_count",
        "ranking_bucket_contract.min_names_per_bucket",
        "rebalance_contract.rebalance_frequency",
        "rebalance_contract.signal_lag_rule",
        "rebalance_contract.holding_period_rule",
        "rebalance_contract.overlap_policy",
        "search_governance_contract.candidate_variant_ids",
        "search_governance_contract.kept_variant_ids",
        "search_governance_contract.rejected_variant_ids",
        "search_governance_contract.selection_rule",
        "search_governance_contract.frozen_signal_contract_reference",
        "search_governance_contract.train_governable_axes",
        "search_governance_contract.non_governable_axes_after_signal",
        "search_governance_contract.non_governable_axis_reject_rule",
        "delivery_contract.machine_artifacts",
        "delivery_contract.consumer_stage",
        "delivery_contract.reuse_constraints",
    ):
        assert path in fields

    assert fields["stage"]["values"] == ["csf_train_freeze"]
    assert fields["delivery_contract.consumer_stage"]["values"] == ["csf_test_evidence"]


def test_csf_train_freeze_contract_locks_csv_and_parquet_shapes() -> None:
    contract = _load_contract()

    assert contract["artifacts"]["train_factor_quality.parquet"]["required_columns"] == [
        "variant_id",
        "quality_score",
        "quality_status",
    ]
    assert contract["artifacts"]["train_variant_ledger.csv"]["required_columns"] == [
        "variant_id",
        "status",
        "selection_rule",
    ]
    assert contract["artifacts"]["train_variant_rejects.csv"]["required_columns"] == [
        "variant_id",
        "reject_reason",
    ]
    assert contract["artifacts"]["train_bucket_diagnostics.parquet"]["required_columns"] == [
        "bucket_id",
        "min_names",
        "ranking_scope",
    ]
    assert contract["artifacts"]["train_neutralization_diagnostics.parquet"]["required_columns"] == [
        "neutralization_policy",
        "group_taxonomy_reference",
        "beta_estimation_window",
    ]
