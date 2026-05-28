from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/csf_holdout_validation_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _artifact(contract: dict, artifact_name: str) -> dict:
    return contract["artifacts"][artifact_name]


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_csf_holdout_validation_artifact_contract_exists_and_declares_stage_shape() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["schema_id"] == "csf-holdout-validation-artifacts-v1"
    assert contract["schema_version"] == "v1"
    assert contract["stage"] == "csf_holdout_validation"
    assert contract["stage_dir"] == "07_csf_holdout_validation/author/formal"
    assert contract["unknown_machine_top_level_fields"] == "forbid"


def test_csf_holdout_validation_artifact_contract_declares_all_formal_outputs() -> None:
    contract = _load_contract()

    assert set(contract["artifacts"]) == {
        "csf_holdout_run_manifest.json",
        "holdout_factor_diagnostics.parquet",
        "holdout_test_compare.parquet",
        "holdout_portfolio_compare.parquet",
        "portfolio_return_series.parquet",
        "equity_curve.parquet",
        "portfolio_pnl_ledger.parquet",
        "asset_pnl_ledger.parquet",
        "risk_adjusted_metrics.parquet",
        "rolling_holdout_stability.json",
        "regime_shift_audit.json",
        "csf_holdout_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    }


def test_csf_holdout_validation_contract_locks_run_manifest_fields() -> None:
    contract = _load_contract()
    run_manifest = _artifact(contract, "csf_holdout_run_manifest.json")

    assert run_manifest["type"] == "json"
    assert run_manifest["unknown_top_level_fields"] == "forbid"
    assert _field_paths(run_manifest) == {
        "stage",
        "lineage_id",
        "source_stage",
        "holdout_window_source",
        "time_split",
        "reuse_rule",
        "drift_scope",
        "backtest_contract_source",
        "test_contract_source",
        "variant_reuse_rule",
        "no_reestimate_rule",
        "direction_flip_rule",
        "coverage_rule",
        "regime_shift_rule",
        "retryable_conditions",
        "child_lineage_trigger",
        "rollback_boundary",
        "input_roots",
        "stage_outputs",
        "program_dir",
        "program_entrypoint",
        "program_execution_manifest",
        "replay_command",
        "selected_variant_ids",
        "portfolio_expression",
        "delivery_contract.machine_artifacts",
        "delivery_contract.consumer_stage",
        "delivery_contract.field_doc_rule",
    }

    consumer_stage = next(
        field for field in run_manifest["fields"] if field["path"] == "delivery_contract.consumer_stage"
    )
    assert consumer_stage["type"] == "enum"
    assert consumer_stage["values"] == ["terminal"]


def test_csf_holdout_validation_contract_locks_machine_artifact_shapes() -> None:
    contract = _load_contract()

    assert _artifact(contract, "holdout_factor_diagnostics.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "coverage_ratio",
        "breadth",
        "direction_match",
        "bucket_stability_score",
    ]
    assert _artifact(contract, "holdout_test_compare.parquet")["required_columns"] == [
        "variant_id",
        "backtest_mean_net_return",
        "holdout_mean_net_return",
        "direction_match",
    ]
    assert _artifact(contract, "holdout_portfolio_compare.parquet")["required_columns"] == [
        "variant_id",
        "backtest_max_drawdown",
        "holdout_max_drawdown",
        "holdout_mean_net_return",
        "net_return_delta",
    ]
    assert _artifact(contract, "portfolio_return_series.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "gross_return",
        "net_return",
        "turnover",
        "cost",
        "asset_count",
        "max_name_weight",
    ]
    assert _artifact(contract, "equity_curve.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "gross_equity",
        "net_equity",
        "drawdown",
    ]
    assert _artifact(contract, "portfolio_pnl_ledger.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "gross_pnl",
        "cost",
        "net_pnl",
        "capital_base",
        "profit_loss_sign",
    ]
    assert _artifact(contract, "asset_pnl_ledger.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "asset",
        "weight",
        "side",
        "asset_return",
        "gross_pnl_contribution",
        "cost_contribution",
        "net_pnl_contribution",
    ]
    assert _artifact(contract, "risk_adjusted_metrics.parquet")["required_columns"] == [
        "variant_id",
        "annualized_return_365d",
        "annualized_return_252d",
        "volatility_365d",
        "volatility_252d",
        "sharpe_365d",
        "sharpe_252d",
        "sortino_365d",
        "sortino_252d",
        "calmar_365d",
        "calmar_252d",
        "profit_factor",
        "max_drawdown",
        "observation_count",
    ]


def test_csf_holdout_validation_contract_locks_json_gate_fields() -> None:
    contract = _load_contract()

    assert _field_paths(_artifact(contract, "rolling_holdout_stability.json")) == {
        "stage",
        "selected_variant_ids",
        "direction_match",
        "stability_status",
        "rolling_window_count",
    }
    assert _field_paths(_artifact(contract, "regime_shift_audit.json")) == {
        "stage",
        "selected_variant_ids",
        "regime_shift_detected",
        "audit_status",
        "explanation",
    }


def test_csf_holdout_validation_contract_field_paths_are_unique() -> None:
    contract = _load_contract()

    for artifact_name, artifact in contract["artifacts"].items():
        paths = [field["path"] for field in artifact.get("fields", [])]
        assert len(paths) == len(set(paths)), artifact_name
