from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_backtest_runtime import build_csf_backtest_ready_from_test_evidence, scaffold_csf_backtest_ready
from tests.runtime.test_csf_backtest_runtime import (
    _csf_backtest_ready_draft,
    _prepare_csf_test_stage,
    _write_yaml,
)


def _prepare_valid_csf_backtest_ready(lineage_root: Path) -> Path:
    _prepare_csf_test_stage(lineage_root)
    stage_dir = scaffold_csf_backtest_ready(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_backtest_ready_draft.yaml", _csf_backtest_ready_draft(confirmed=True))
    build_csf_backtest_ready_from_test_evidence(lineage_root)
    return stage_dir


def test_csf_backtest_ready_scaffold_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_test_stage(lineage_root)

    stage_dir = scaffold_csf_backtest_ready(lineage_root)

    draft = yaml.safe_load(
        (stage_dir / "author" / "draft" / "csf_backtest_ready_draft.yaml").read_text(encoding="utf-8")
    )
    assert set(draft["groups"]) == {
        "portfolio_contract",
        "execution_contract",
        "risk_contract",
        "diagnostic_contract",
        "delivery_contract",
    }
    assert set(draft["groups"]["portfolio_contract"]["draft"]) == {
        "portfolio_expression",
        "selection_rule",
        "weight_mapping_rule",
        "gross_exposure_rule",
    }


def test_csf_backtest_ready_build_shape_matches_contract(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_backtest_ready(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("csf_backtest_ready"))

    assert result.valid is True
    assert result.errors == []


def test_csf_backtest_ready_portfolio_contract_key_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_backtest_ready(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = yaml.safe_load((formal_dir / "portfolio_contract.yaml").read_text(encoding="utf-8"))

    assert set(payload) == {
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
        "delivery_contract",
    }
    assert payload["delivery_contract"]["consumer_stage"] == "csf_holdout_validation"


def test_csf_backtest_ready_return_accounting_provenance_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_backtest_ready(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))

    assert set(payload) == {
        "stage",
        "lineage_id",
        "return_source",
        "accounting",
        "formal_outputs",
    }
    assert set(payload["return_source"]) == {
        "source_type",
        "input_paths",
        "price_field",
        "return_field",
        "source_stage",
        "is_signal_derived",
    }
    assert set(payload["accounting"]) == {
        "rebalance_timing",
        "holding_period",
        "fee_model",
        "slippage_model",
        "funding_model",
        "missing_price_policy",
        "gross_return_formula",
        "net_return_formula",
    }
    assert payload["return_source"]["input_paths"] == [
        "../02_csf_data_ready/author/formal/shared_feature_base/returns_panel.parquet"
    ]
    assert payload["return_source"]["price_field"] == ""
    assert payload["return_source"]["return_field"] == "return_1d"
    assert payload["return_source"]["is_signal_derived"] is False
    assert payload["accounting"]["gross_return_formula"] == "sum(weight * return_1d)"
    assert payload["accounting"]["net_return_formula"] == "gross_return - fees - slippage - funding"


def test_csf_backtest_ready_weight_panel_columns_are_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_backtest_ready(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    table = pq.read_table(formal_dir / "portfolio_weight_panel.parquet")

    assert set(table.column_names) == {"date", "asset", "variant_id", "weight", "side"}
    assert table.num_rows > 0
