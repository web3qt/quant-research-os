from pathlib import Path

import yaml

from tools.csf_backtest_runtime import (
    build_csf_backtest_ready_from_test_evidence,
    scaffold_csf_backtest_ready,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _csf_backtest_ready_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "portfolio_contract": {
                "confirmed": confirmed,
                "draft": {
                    "portfolio_expression": "long_short_market_neutral",
                    "selection_rule": "Long top quintile and short bottom quintile.",
                    "weight_mapping_rule": "Equal-weight within each side.",
                    "gross_exposure_rule": "100/100 gross",
                },
                "missing_items": [],
            },
            "execution_contract": {
                "confirmed": confirmed,
                "draft": {
                    "rebalance_execution_lag": "1 bar",
                    "turnover_budget_rule": "Cap one-way turnover at 20% per rebalance.",
                    "cost_model": "Frozen fee plus slippage schedule.",
                    "capacity_model": "Limit participation versus rolling ADV.",
                },
                "missing_items": [],
            },
            "risk_contract": {
                "confirmed": confirmed,
                "draft": {
                    "max_name_weight_rule": "Cap any single name at 10%.",
                    "net_exposure_rule": "Net exposure must stay inside +/-5%.",
                    "group_neutral_overlay": "sector_bucket_v1",
                    "target_strategy_reference": "",
                },
                "missing_items": [],
            },
            "diagnostic_contract": {
                "confirmed": confirmed,
                "draft": {
                    "required_diagnostics": ["turnover", "capacity", "concentration", "drawdown"],
                    "after_cost_rule": "Backtest gate uses net-of-cost results.",
                    "name_level_rule": "Do not approve if one name dominates the result.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["portfolio_contract.yaml", "portfolio_weight_panel.parquet"],
                    "consumer_stage": "csf_holdout_validation",
                    "frozen_config_note": "Holdout must consume this frozen portfolio contract.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_csf_test_stage(lineage_root: Path) -> None:
    stage_dir = lineage_root / "05_csf_test_evidence"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
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
        "csf_test_contract.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    (formal_dir / "csf_selected_variants_test.csv").write_text(
        "variant_id,status\nbaseline_v1,selected\n",
        encoding="utf-8",
    )
    mandate_dir = lineage_root / "01_mandate"
    mandate_formal_dir = mandate_dir / "author" / "formal"
    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(
        mandate_formal_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "portfolio_expression": "long_short_market_neutral",
        },
    )


def test_scaffold_csf_backtest_ready_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_test_stage(lineage_root)

    stage_dir = scaffold_csf_backtest_ready(lineage_root)

    draft = yaml.safe_load((stage_dir / "author" / "draft" / "csf_backtest_ready_draft.yaml").read_text(encoding="utf-8"))
    assert stage_dir == lineage_root / "06_csf_backtest_ready"
    assert set(draft["groups"]) == {
        "portfolio_contract",
        "execution_contract",
        "risk_contract",
        "diagnostic_contract",
        "delivery_contract",
    }


def test_build_csf_backtest_ready_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_test_stage(lineage_root)
    stage_dir = lineage_root / "06_csf_backtest_ready"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_backtest_ready_draft.yaml", _csf_backtest_ready_draft(confirmed=True))

    built_dir = build_csf_backtest_ready_from_test_evidence(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "portfolio_contract.yaml").exists()
    assert (formal_dir / "portfolio_weight_panel.parquet").exists()
    assert (formal_dir / "rebalance_ledger.csv").exists()
    assert (formal_dir / "turnover_capacity_report.parquet").exists()
    assert (formal_dir / "cost_assumption_report.md").exists()
    assert (formal_dir / "portfolio_summary.parquet").exists()
    assert (formal_dir / "name_level_metrics.parquet").exists()
    assert (formal_dir / "drawdown_report.json").exists()
    assert (formal_dir / "target_strategy_compare.parquet").exists()
    assert (formal_dir / "csf_backtest_gate_table.csv").exists()
    assert (formal_dir / "csf_backtest_contract.md").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()


def test_build_csf_backtest_ready_accepts_new_standalone_alpha_expression(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_test_stage(lineage_root)
    mandate_route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
    _write_yaml(
        mandate_route_path,
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "portfolio_expression": "group_relative_long_short",
        },
    )
    stage_dir = lineage_root / "06_csf_backtest_ready"
    stage_dir.mkdir(parents=True)
    draft_payload = _csf_backtest_ready_draft(confirmed=True)
    draft_payload["groups"]["portfolio_contract"]["draft"]["portfolio_expression"] = "group_relative_long_short"
    _write_yaml(stage_dir / "author" / "draft" / "csf_backtest_ready_draft.yaml", draft_payload)

    built_dir = build_csf_backtest_ready_from_test_evidence(lineage_root)

    formal_dir = built_dir / "author" / "formal"
    payload = yaml.safe_load((formal_dir / "portfolio_contract.yaml").read_text(encoding="utf-8"))
    assert payload["portfolio_expression"] == "group_relative_long_short"
