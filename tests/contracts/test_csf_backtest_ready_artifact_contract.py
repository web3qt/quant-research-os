from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/csf_backtest_ready_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _artifact(contract: dict, artifact_name: str) -> dict:
    return contract["artifacts"][artifact_name]


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_csf_backtest_ready_artifact_contract_exists_and_declares_stage_shape() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["schema_id"] == "csf-backtest-ready-artifacts-v1"
    assert contract["schema_version"] == "v1"
    assert contract["stage"] == "csf_backtest_ready"
    assert contract["stage_dir"] == "06_csf_backtest_ready/author/formal"
    assert contract["unknown_machine_top_level_fields"] == "forbid"


def test_csf_backtest_ready_artifact_contract_declares_all_formal_outputs() -> None:
    contract = _load_contract()

    assert set(contract["artifacts"]) == {
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


def test_csf_backtest_ready_contract_locks_portfolio_contract_fields() -> None:
    contract = _load_contract()
    portfolio_contract = _artifact(contract, "portfolio_contract.yaml")

    assert portfolio_contract["type"] == "yaml"
    assert portfolio_contract["unknown_top_level_fields"] == "forbid"
    assert _field_paths(portfolio_contract) == {
        "stage",
        "lineage_id",
        "portfolio_expression",
        "selection_rule",
        "weight_mapping_rule",
        "gross_exposure_rule",
        "rebalance_execution_lag",
        "turnover_budget_rule",
        "cost_model",
        "capacity_model",
        "max_name_weight_rule",
        "net_exposure_rule",
        "group_neutral_overlay",
        "target_strategy_reference",
        "required_diagnostics",
        "delivery_contract.machine_artifacts",
        "delivery_contract.consumer_stage",
        "delivery_contract.frozen_config_note",
    }

    stage = next(field for field in portfolio_contract["fields"] if field["path"] == "stage")
    assert stage["type"] == "enum"
    assert stage["values"] == ["csf_backtest_ready"]

    consumer_stage = next(
        field for field in portfolio_contract["fields"] if field["path"] == "delivery_contract.consumer_stage"
    )
    assert consumer_stage["type"] == "enum"
    assert consumer_stage["values"] == ["csf_holdout_validation"]


def test_csf_backtest_ready_contract_locks_machine_artifact_shapes() -> None:
    contract = _load_contract()

    assert _artifact(contract, "portfolio_weight_panel.parquet")["required_columns"] == [
        "date",
        "asset",
        "variant_id",
        "weight",
        "side",
    ]
    assert _artifact(contract, "turnover_capacity_report.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "turnover",
        "capacity_utilization",
    ]
    assert _artifact(contract, "portfolio_summary.parquet")["required_columns"] == [
        "variant_id",
        "mean_gross_return",
        "mean_net_return",
        "max_drawdown",
    ]
    assert _artifact(contract, "target_strategy_compare.parquet")["required_columns"] == [
        "variant_id",
        "target_strategy_reference",
        "portfolio_mean_net_return",
        "target_mean_net_return",
    ]
    assert _artifact(contract, "csf_backtest_gate_table.csv")["required_columns"] == [
        "variant_id",
        "portfolio_expression",
        "mean_net_return",
        "after_cost_rule",
        "name_level_rule",
    ]


def test_csf_backtest_ready_contract_locks_run_manifest_fields() -> None:
    contract = _load_contract()
    run_manifest = _artifact(contract, "run_manifest.json")

    assert run_manifest["type"] == "json"
    assert run_manifest["unknown_top_level_fields"] == "forbid"
    assert _field_paths(run_manifest) == {
        "stage",
        "lineage_id",
        "source_stage",
        "input_roots",
        "stage_outputs",
        "program_dir",
        "program_entrypoint",
        "program_execution_manifest",
        "replay_command",
        "selected_variant_ids",
        "portfolio_expression",
    }


def test_csf_backtest_ready_contract_field_paths_are_unique() -> None:
    contract = _load_contract()

    for artifact_name, artifact in contract["artifacts"].items():
        paths = [field["path"] for field in artifact.get("fields", [])]
        assert len(paths) == len(set(paths)), artifact_name
