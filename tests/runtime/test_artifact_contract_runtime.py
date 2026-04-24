from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.idea_runtime import scaffold_idea_intake


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_empty_parquet(path: Path, schema: dict[str, pa.DataType]) -> None:
    pq.write_table(pa.table({key: pa.array([], type=value) for key, value in schema.items()}), path)


def _write_minimal_valid_mandate_formal(stage_dir: Path) -> None:
    (stage_dir / "mandate.md").write_text(
        "\n".join(
            [
                "# Mandate",
                "## 目标",
                "## 研究意图",
                "## 路线理由",
                "## 成功标准",
                "## 失败标准",
                "## 已冻结执行输入",
                "## 执行合同",
                "## Gate 依据",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "research_scope.md").write_text("# Research Scope\n", encoding="utf-8")
    _write_yaml(
        stage_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "",
            "group_taxonomy_reference": "sector_bucket_v1",
            "excluded_routes": ["time_series_signal"],
            "route_rationale": ["Cross-asset ranking expresses the edge best."],
            "route_change_policy": {
                "before_downstream_freeze": "rollback_to_mandate",
                "after_downstream_freeze": "child_lineage",
            },
            "route_contract_version": "v1",
        },
    )
    (stage_dir / "time_split.json").write_text(
        '{"train":"","test":"","backtest":"","holdout":"","bar_size":"5m","holding_horizons":["15m"],"policy_note":"locked"}\n',
        encoding="utf-8",
    )
    _write_yaml(stage_dir / "parameter_grid.yaml", {"parameters": [], "note": "locked parameter family"})
    (stage_dir / "run_config.toml").write_text(
        "\n".join(
            [
                'stage = "mandate"',
                'lineage_id = "btc_alt_transmission_v1"',
                'market = "Binance perpetual"',
                'universe = "top liquidity alts"',
                'target_task = "event-driven relative return study"',
                'data_source = "Binance UM futures klines"',
                'bar_size = "5m"',
                "non_rust_exceptions = []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "artifact_catalog.md").write_text("# 产物清单\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("# 字段字典\n", encoding="utf-8")


def _write_minimal_valid_csf_data_ready_formal(stage_dir: Path) -> None:
    stage_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        stage_dir / "panel_manifest.json",
        {
            "stage": "csf_data_ready",
            "lineage_id": "btc_alt_transmission_v1",
            "panel_primary_key": ["date", "asset"],
            "cross_section_time_key": "date",
            "asset_key": "asset",
            "shared_feature_outputs": ["returns_panel", "liquidity_panel", "beta_inputs"],
            "machine_artifacts": [
                "panel_manifest.json",
                "asset_universe_membership.parquet",
                "cross_section_coverage.parquet",
                "eligibility_base_mask.parquet",
            ],
            "coverage_floor_min_ratio": 0.95,
        },
    )
    _write_parquet_rows(
        stage_dir / "asset_universe_membership.parquet",
        [{"date": "2024-01-01", "asset": "BTCUSDT", "in_universe": True}],
    )
    _write_parquet_rows(
        stage_dir / "cross_section_coverage.parquet",
        [{"date": "2024-01-01", "coverage_ratio": 1.0, "asset_count": 1}],
    )
    _write_parquet_rows(
        stage_dir / "eligibility_base_mask.parquet",
        [{"date": "2024-01-01", "asset": "BTCUSDT", "eligible": True}],
    )
    shared_feature_base = stage_dir / "shared_feature_base"
    shared_feature_base.mkdir()
    _write_parquet_rows(
        shared_feature_base / "returns_panel.parquet",
        [{"date": "2024-01-01", "asset": "BTCUSDT", "return_1d": 0.01}],
    )
    _write_parquet_rows(
        shared_feature_base / "liquidity_panel.parquet",
        [{"date": "2024-01-01", "asset": "BTCUSDT", "dollar_volume": 1000.0}],
    )
    _write_parquet_rows(
        shared_feature_base / "beta_inputs.parquet",
        [{"date": "2024-01-01", "asset": "BTCUSDT", "beta_proxy": 1.0}],
    )
    _write_parquet_rows(
        stage_dir / "asset_taxonomy_snapshot.parquet",
        [
            {
                "asset": "BTCUSDT",
                "date": "2024-01-01",
                "group_taxonomy_reference": "sector_bucket_v1",
                "group_bucket": "core",
            }
        ],
    )
    (stage_dir / "csf_data_contract.md").write_text("# CSF 数据合同\n", encoding="utf-8")
    (stage_dir / "csf_data_ready_gate_decision.md").write_text("# CSF Data Ready Gate Decision\n", encoding="utf-8")
    _write_json(
        stage_dir / "run_manifest.json",
        {
            "stage": "csf_data_ready",
            "lineage_id": "btc_alt_transmission_v1",
            "source_stage": "mandate",
            "panel_primary_key": ["date", "asset"],
            "cross_section_time_key": "date",
            "asset_key": "asset",
            "universe_membership_rule": "Use frozen mandate universe per date.",
            "group_taxonomy_reference": "sector_bucket_v1",
            "eligibility_base_rule": "Drop illiquid assets.",
            "coverage_floor_rule": "Require 95% coverage.",
            "shared_feature_outputs": ["returns_panel", "liquidity_panel", "beta_inputs"],
            "machine_artifacts": [
                "panel_manifest.json",
                "asset_universe_membership.parquet",
                "cross_section_coverage.parquet",
                "eligibility_base_mask.parquet",
            ],
            "consumer_stage": "csf_signal_ready",
            "frozen_inputs_note": "Downstream consumes frozen panel base.",
            "runtime_root_hint": "/tmp/qros",
            "runtime_module": "tools/csf_data_ready_runtime.py",
            "runtime_function": "build_csf_data_ready_from_mandate",
            "source_git_revision": "abc123",
            "program_artifacts": ["rebuild_csf_data_ready.py"],
            "replay_working_directory": "02_csf_data_ready",
            "replay_command": "python3 rebuild_csf_data_ready.py",
        },
    )
    rebuild_script = stage_dir / "rebuild_csf_data_ready.py"
    rebuild_script.write_text("#!/usr/bin/env python3\nprint('rebuild')\n", encoding="utf-8")
    rebuild_script.chmod(0o755)
    (stage_dir / "artifact_catalog.md").write_text("# 产物清单\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("# 字段字典\n", encoding="utf-8")


def _write_minimal_valid_csf_signal_ready_formal(stage_dir: Path) -> None:
    stage_dir.mkdir(parents=True, exist_ok=True)
    _write_parquet_rows(
        stage_dir / "factor_panel.parquet",
        [{"date": "2024-01-01", "asset": "BTCUSDT", "factor_value": 1.0}],
    )
    _write_yaml(
        stage_dir / "factor_manifest.yaml",
        {
            "stage": "csf_signal_ready",
            "lineage_id": "btc_alt_transmission_v1",
            "factor_id": "btc_lead_alt_follow",
            "factor_version": "v1",
            "factor_direction": "high_better",
            "factor_structure": "single_factor",
            "panel_primary_key": ["date", "asset"],
            "raw_factor_fields": ["return_1d", "dollar_volume", "beta_proxy"],
            "derived_factor_fields": ["lead_follow_score"],
            "final_score_field": "factor_value",
            "as_of_semantics": "Factor values are frozen at the cross-section close.",
            "coverage_min_ratio": 1.0,
            "coverage_contract": "Require complete coverage for the fixture.",
            "missing_value_policy": "Preserve nulls and report eligibility separately.",
            "input_field_map": [
                {
                    "raw_field": "return_1d",
                    "source_artifact": "shared_feature_base/returns_panel.parquet",
                    "source_column": "return_1d",
                }
            ],
        },
    )
    _write_yaml(
        stage_dir / "component_factor_manifest.yaml",
        {
            "stage": "csf_signal_ready",
            "lineage_id": "btc_alt_transmission_v1",
            "factor_structure": "single_factor",
            "component_factor_ids": [],
            "score_combination_formula": "single_factor_passthrough",
            "combination_policy": "deterministic_passthrough",
        },
    )
    _write_parquet_rows(
        stage_dir / "factor_coverage_report.parquet",
        [{"date": "2024-01-01", "coverage_ratio": 1.0, "asset_count": 1}],
    )
    _write_parquet_rows(
        stage_dir / "factor_group_context.parquet",
        [{"date": "2024-01-01", "asset": "BTCUSDT", "group_context": "core"}],
    )
    _write_yaml(
        stage_dir / "route_inheritance_contract.yaml",
        {
            "source_route_artifact": "../../01_mandate/author/formal/research_route.yaml",
            "source_route_digest_sha256": "abc123",
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "",
            "group_taxonomy_reference": "sector_bucket_v1",
            "target_strategy_reference_requirement_status": "not_required",
            "group_taxonomy_reference_requirement_status": "required_satisfied",
            "inheritance_mode": "exact_copy",
        },
    )
    (stage_dir / "factor_contract.md").write_text("# 因子合同\n", encoding="utf-8")
    (stage_dir / "factor_field_dictionary.md").write_text("# 因子字段字典\n", encoding="utf-8")
    (stage_dir / "csf_signal_ready_gate_decision.md").write_text(
        "# CSF Signal Ready Gate Decision\n",
        encoding="utf-8",
    )
    _write_json(
        stage_dir / "run_manifest.json",
        {
            "stage": "csf_signal_ready",
            "lineage_id": "btc_alt_transmission_v1",
            "source_stage": "csf_data_ready",
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "program_dir": "program/cross_sectional_factor/signal_ready",
            "program_entrypoint": "run_stage.py",
            "program_execution_manifest": "program_execution_manifest.json",
            "input_roots": [
                "../02_csf_data_ready/author/formal/panel_manifest.json",
                "../../01_mandate/author/formal/research_route.yaml",
            ],
            "stage_outputs": ["factor_panel.parquet", "factor_manifest.yaml"],
            "replay_command": "python3 program/cross_sectional_factor/signal_ready/run_stage.py",
        },
    )
    (stage_dir / "artifact_catalog.md").write_text("# 产物清单\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("# 字段字典\n", encoding="utf-8")


def _write_minimal_valid_csf_train_freeze_formal(stage_dir: Path) -> None:
    stage_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(
        stage_dir / "csf_train_freeze.yaml",
        {
            "stage": "csf_train_freeze",
            "lineage_id": "btc_alt_transmission_v1",
            "preprocess_contract": {
                "winsorize_policy": "cross_section_2sided_quantile",
                "standardize_policy": "zscore_by_date",
                "missing_fill_policy": "no_fill",
                "coverage_floor_rule": "drop cross-sections below 95% coverage",
            },
            "neutralization_contract": {
                "neutralization_policy": "group_neutral",
                "beta_estimation_window": "60d",
                "group_taxonomy_reference": "sector_bucket_v1",
                "residualization_formula": "factor_value - group_mean(factor_value)",
            },
            "ranking_bucket_contract": {
                "ranking_scope": "full_universe",
                "bucket_schema": "quintile",
                "quantile_count": 5,
                "min_names_per_bucket": 10,
            },
            "rebalance_contract": {
                "rebalance_frequency": "1d",
                "signal_lag_rule": "trade next bar after score freeze",
                "holding_period_rule": "hold 5 trading days",
                "overlap_policy": "allow_overlap",
            },
            "search_governance_contract": {
                "candidate_variant_ids": ["baseline_v1", "beta_neutral_v1"],
                "kept_variant_ids": ["baseline_v1"],
                "rejected_variant_ids": ["beta_neutral_v1"],
                "selection_rule": "exclude variants that change frozen signal-expression axes",
                "frozen_signal_contract_reference": "03_csf_signal_ready/author/formal/factor_contract.md",
                "train_governable_axes": ["winsorize_policy", "bucket_schema", "rebalance_frequency"],
                "non_governable_axes_after_signal": [
                    "raw_factor_fields",
                    "derived_factor_fields",
                    "score_combination_formula",
                ],
                "non_governable_axis_reject_rule": "reject variant and reopen csf_signal_ready for signal-axis changes",
            },
            "delivery_contract": {
                "machine_artifacts": [
                    "csf_train_freeze.yaml",
                    "train_factor_quality.parquet",
                    "train_variant_ledger.csv",
                    "train_variant_rejects.csv",
                ],
                "consumer_stage": "csf_test_evidence",
                "reuse_constraints": "test must reuse frozen train rules without re-estimating them",
            },
        },
    )
    _write_parquet_rows(
        stage_dir / "train_factor_quality.parquet",
        [{"variant_id": "baseline_v1", "quality_score": 1.0, "quality_status": "kept"}],
    )
    (stage_dir / "train_variant_ledger.csv").write_text(
        "\n".join(
            [
                "variant_id,status,selection_rule",
                "baseline_v1,kept,exclude variants that change frozen signal-expression axes",
                "beta_neutral_v1,rejected,exclude variants that change frozen signal-expression axes",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "train_variant_rejects.csv").write_text(
        "\n".join(
            [
                "variant_id,reject_reason",
                "beta_neutral_v1,attempted to change a frozen signal axis",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_parquet_rows(
        stage_dir / "train_bucket_diagnostics.parquet",
        [{"bucket_id": "q1", "min_names": 10, "ranking_scope": "full_universe"}],
    )
    _write_parquet_rows(
        stage_dir / "train_neutralization_diagnostics.parquet",
        [
            {
                "neutralization_policy": "group_neutral",
                "group_taxonomy_reference": "sector_bucket_v1",
                "beta_estimation_window": "60d",
            }
        ],
    )
    (stage_dir / "csf_train_contract.md").write_text("# CSF Train Contract\n", encoding="utf-8")
    (stage_dir / "csf_train_freeze_gate_decision.md").write_text(
        "# CSF Train Freeze Gate Decision\n",
        encoding="utf-8",
    )
    _write_json(
        stage_dir / "run_manifest.json",
        {
            "stage": "csf_train_freeze",
            "lineage_id": "btc_alt_transmission_v1",
            "source_stage": "csf_signal_ready",
            "program_dir": "program/cross_sectional_factor/train_freeze",
            "program_entrypoint": "run_stage.py",
            "program_execution_manifest": "program_execution_manifest.json",
            "input_roots": [
                "../03_csf_signal_ready/author/formal/factor_manifest.yaml",
                "../03_csf_signal_ready/author/formal/factor_contract.md",
                "author/draft/csf_train_freeze_draft.yaml",
            ],
            "stage_outputs": [
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
            ],
            "replay_command": "python3 program/cross_sectional_factor/train_freeze/run_stage.py",
            "candidate_variant_ids": ["baseline_v1", "beta_neutral_v1"],
            "kept_variant_ids": ["baseline_v1"],
            "rejected_variant_ids": ["beta_neutral_v1"],
            "selection_rule": "exclude variants that change frozen signal-expression axes",
            "frozen_signal_contract_reference": "03_csf_signal_ready/author/formal/factor_contract.md",
        },
    )
    (stage_dir / "artifact_catalog.md").write_text("# 产物清单\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("# 字段字典\n", encoding="utf-8")


def _write_minimal_valid_csf_test_evidence_formal(stage_dir: Path) -> None:
    stage_dir.mkdir(parents=True, exist_ok=True)
    _write_parquet_rows(
        stage_dir / "rank_ic_timeseries.parquet",
        [{"date": "2024-07-01", "variant_id": "baseline_v1", "rank_ic": 0.12}],
    )
    _write_json(
        stage_dir / "rank_ic_summary.json",
        {
            "stage": "csf_test_evidence",
            "lineage_id": "btc_alt_transmission_v1",
            "factor_role": "standalone_alpha",
            "selected_variant_ids": ["baseline_v1"],
            "primary_evidence_contract": "rank_ic_and_bucket_spread",
            "mean_rank_ic": 0.12,
            "median_rank_ic": 0.10,
            "num_dates": 29,
        },
    )
    _write_parquet_rows(
        stage_dir / "bucket_returns.parquet",
        [{"date": "2024-07-01", "variant_id": "baseline_v1", "bucket_id": "q5", "mean_return": 0.02}],
    )
    _write_json(
        stage_dir / "monotonicity_report.json",
        {
            "stage": "csf_test_evidence",
            "selected_variant_ids": ["baseline_v1"],
            "status": "pass",
            "monotonic_direction": "high_bucket_outperforms_low_bucket",
        },
    )
    _write_parquet_rows(
        stage_dir / "breadth_coverage_report.parquet",
        [{"date": "2024-07-01", "variant_id": "baseline_v1", "coverage_ratio": 0.98, "asset_count": 120}],
    )
    _write_json(
        stage_dir / "subperiod_stability_report.json",
        {
            "stage": "csf_test_evidence",
            "selected_variant_ids": ["baseline_v1"],
            "status": "pass",
            "subperiod_count": 3,
            "subperiod_rule": "Report stability over equal subperiods.",
        },
    )
    _write_parquet_rows(
        stage_dir / "filter_condition_panel.parquet",
        [{"date": "2024-07-01", "asset": "SOLUSDT", "variant_id": "baseline_v1", "condition_active": True}],
    )
    _write_parquet_rows(
        stage_dir / "target_strategy_condition_compare.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "target_strategy_reference": "",
                "gated_mean_return": 0.03,
                "ungated_mean_return": 0.01,
                "delta_mean_return": 0.02,
            }
        ],
    )
    _write_json(
        stage_dir / "gated_vs_ungated_summary.json",
        {
            "stage": "csf_test_evidence",
            "selected_variant_ids": ["baseline_v1"],
            "status": "pass",
            "mean_delta": 0.02,
        },
    )
    (stage_dir / "csf_test_gate_table.csv").write_text(
        "variant_id,verdict,primary_evidence_contract,reason\nbaseline_v1,selected,rank_ic_and_bucket_spread,baseline-only\n",
        encoding="utf-8",
    )
    (stage_dir / "csf_selected_variants_test.csv").write_text(
        "variant_id,status\nbaseline_v1,selected\n",
        encoding="utf-8",
    )
    (stage_dir / "csf_test_contract.md").write_text("# CSF Test Contract\n", encoding="utf-8")
    (stage_dir / "csf_test_gate_decision.md").write_text("# CSF Test Gate Decision\n", encoding="utf-8")
    _write_json(
        stage_dir / "run_manifest.json",
        {
            "stage": "csf_test_evidence",
            "lineage_id": "btc_alt_transmission_v1",
            "source_stage": "csf_train_freeze",
            "input_roots": [
                "../04_csf_train_freeze/author/formal/csf_train_freeze.yaml",
                "../04_csf_train_freeze/author/formal/train_variant_ledger.csv",
                "author/draft/csf_test_evidence_draft.yaml",
            ],
            "stage_outputs": [
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
                "csf_test_gate_decision.md",
                "csf_test_contract.md",
                "run_manifest.json",
                "artifact_catalog.md",
                "field_dictionary.md",
            ],
            "program_dir": "program/cross_sectional_factor/test_evidence",
            "program_entrypoint": "run_stage.py",
            "program_execution_manifest": "program_execution_manifest.json",
            "replay_command": "python3 program/cross_sectional_factor/test_evidence/run_stage.py",
            "selected_variant_ids": ["baseline_v1"],
            "selection_rule": "baseline-only",
            "primary_evidence_contract": "rank_ic_and_bucket_spread",
        },
    )
    (stage_dir / "artifact_catalog.md").write_text("# 产物清单\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("# 字段字典\n", encoding="utf-8")


def test_validate_stage_artifacts_accepts_scaffolded_idea_intake(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is True
    assert result.errors == []


def test_validate_stage_artifacts_reports_missing_required_artifact(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    (intake_dir / "scope_canvas.yaml").unlink()

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is False
    assert "scope_canvas.yaml: missing required artifact" in result.errors


def test_validate_stage_artifacts_reports_yaml_type_mismatch(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    payload = yaml.safe_load((intake_dir / "scope_canvas.yaml").read_text(encoding="utf-8"))
    payload["budget_days"] = "ten"
    _write_yaml(intake_dir / "scope_canvas.yaml", payload)

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is False
    assert "scope_canvas.yaml: budget_days expected integer, found str" in result.errors


def test_validate_stage_artifacts_reports_unknown_top_level_yaml_field(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    payload = yaml.safe_load((intake_dir / "idea_gate_decision.yaml").read_text(encoding="utf-8"))
    payload["uncontracted_field"] = "leak"
    _write_yaml(intake_dir / "idea_gate_decision.yaml", payload)

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is False
    assert "idea_gate_decision.yaml: unknown top-level field uncontracted_field" in result.errors


def test_validate_stage_artifacts_reports_missing_markdown_section(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    (intake_dir / "observation_hypothesis_map.md").write_text("# Observation Hypothesis Map\n", encoding="utf-8")

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is False
    assert "observation_hypothesis_map.md: missing markdown section 观察" in result.errors


def test_validate_stage_artifacts_reports_json_type_mismatch(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    stage_dir.mkdir()
    _write_minimal_valid_mandate_formal(stage_dir)
    (stage_dir / "time_split.json").write_text(
        '{"train":"","test":"","backtest":"","holdout":"","bar_size":"5m","holding_horizons":"15m","policy_note":"locked"}\n',
        encoding="utf-8",
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("mandate"))

    assert result.valid is False
    assert "time_split.json: holding_horizons expected list[string], found str" in result.errors


def test_validate_stage_artifacts_reports_toml_missing_field(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    stage_dir.mkdir()
    _write_minimal_valid_mandate_formal(stage_dir)
    (stage_dir / "run_config.toml").write_text(
        "\n".join(
            [
                'stage = "mandate"',
                'lineage_id = "btc_alt_transmission_v1"',
                'market = "Binance perpetual"',
                'universe = "top liquidity alts"',
                'target_task = "event-driven relative return study"',
                'data_source = "Binance UM futures klines"',
                'bar_size = "5m"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("mandate"))

    assert result.valid is False
    assert "run_config.toml: missing required field non_rust_exceptions" in result.errors


def test_validate_stage_artifacts_accepts_list_of_maps(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    stage_dir.mkdir()
    _write_minimal_valid_mandate_formal(stage_dir)
    _write_yaml(
        stage_dir / "parameter_grid.yaml",
        {
            "parameters": [{"name": "lookback", "type": "integer", "min": 5, "max": 60, "step": 5}],
            "note": "locked parameter family",
        },
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("mandate"))

    assert result.valid is True
    assert result.errors == []


def test_validate_stage_artifacts_reports_missing_required_directory_file(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_data_ready_formal(stage_dir)
    (stage_dir / "shared_feature_base" / "returns_panel.parquet").unlink()

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_data_ready"))

    assert result.valid is False
    assert "shared_feature_base/returns_panel.parquet: missing required artifact" in result.errors


def test_validate_stage_artifacts_reports_parquet_missing_required_column(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_data_ready_formal(stage_dir)
    _write_parquet_rows(
        stage_dir / "asset_universe_membership.parquet",
        [{"date": "2024-01-01", "asset": "BTCUSDT"}],
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_data_ready"))

    assert result.valid is False
    assert "asset_universe_membership.parquet: missing required parquet column in_universe" in result.errors


def test_validate_stage_artifacts_reports_empty_parquet_when_non_empty_required(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_data_ready_formal(stage_dir)
    _write_empty_parquet(
        stage_dir / "asset_universe_membership.parquet",
        {
            "date": pa.string(),
            "asset": pa.string(),
            "in_universe": pa.bool_(),
        },
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_data_ready"))

    assert result.valid is False
    assert "asset_universe_membership.parquet: expected non-empty parquet rows" in result.errors


def test_validate_stage_artifacts_accepts_valid_csf_data_ready_shape(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_data_ready_formal(stage_dir)

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_data_ready"))

    assert result.valid is True
    assert result.errors == []


def test_validate_stage_artifacts_accepts_valid_csf_signal_ready_shape(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_signal_ready_formal(stage_dir)

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_signal_ready"))

    assert result.valid is True
    assert result.errors == []


def test_validate_stage_artifacts_reports_csf_signal_ready_missing_required_artifact(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_signal_ready_formal(stage_dir)
    (stage_dir / "component_factor_manifest.yaml").unlink()

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_signal_ready"))

    assert result.valid is False
    assert "component_factor_manifest.yaml: missing required artifact" in result.errors


def test_validate_stage_artifacts_reports_csf_signal_ready_factor_manifest_unknown_field(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_signal_ready_formal(stage_dir)
    payload = yaml.safe_load((stage_dir / "factor_manifest.yaml").read_text(encoding="utf-8"))
    payload["uncontracted_signal_axis"] = "leak"
    _write_yaml(stage_dir / "factor_manifest.yaml", payload)

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_signal_ready"))

    assert result.valid is False
    assert "factor_manifest.yaml: unknown top-level field uncontracted_signal_axis" in result.errors


def test_validate_stage_artifacts_reports_csf_signal_ready_factor_panel_missing_static_column(
    tmp_path: Path,
) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_signal_ready_formal(stage_dir)
    _write_parquet_rows(stage_dir / "factor_panel.parquet", [{"asset": "BTCUSDT", "factor_value": 1.0}])

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_signal_ready"))

    assert result.valid is False
    assert "factor_panel.parquet: missing required parquet column date" in result.errors


def test_validate_stage_artifacts_reports_csf_signal_ready_empty_factor_panel(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_signal_ready_formal(stage_dir)
    _write_empty_parquet(
        stage_dir / "factor_panel.parquet",
        {
            "date": pa.string(),
            "asset": pa.string(),
            "factor_value": pa.float64(),
        },
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_signal_ready"))

    assert result.valid is False
    assert "factor_panel.parquet: expected non-empty parquet rows" in result.errors


def test_validate_stage_artifacts_accepts_valid_csf_train_freeze_shape(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_train_freeze_formal(stage_dir)

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_train_freeze"))

    assert result.valid is True
    assert result.errors == []


def test_validate_stage_artifacts_reports_csf_train_freeze_missing_csv_column(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_train_freeze_formal(stage_dir)
    (stage_dir / "train_variant_ledger.csv").write_text(
        "variant_id,status\nbaseline_v1,kept\n",
        encoding="utf-8",
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_train_freeze"))

    assert result.valid is False
    assert "train_variant_ledger.csv: missing required csv column selection_rule" in result.errors


def test_validate_stage_artifacts_reports_csf_train_freeze_unknown_yaml_field(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_train_freeze_formal(stage_dir)
    payload = yaml.safe_load((stage_dir / "csf_train_freeze.yaml").read_text(encoding="utf-8"))
    payload["test_selected_winner"] = "leak"
    _write_yaml(stage_dir / "csf_train_freeze.yaml", payload)

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_train_freeze"))

    assert result.valid is False
    assert "csf_train_freeze.yaml: unknown top-level field test_selected_winner" in result.errors


def test_validate_stage_artifacts_accepts_valid_csf_test_evidence_shape(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_test_evidence_formal(stage_dir)

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_test_evidence"))

    assert result.valid is True
    assert result.errors == []


def test_validate_stage_artifacts_reports_csf_test_evidence_missing_parquet_column(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    _write_minimal_valid_csf_test_evidence_formal(stage_dir)
    _write_parquet_rows(
        stage_dir / "rank_ic_timeseries.parquet",
        [{"date": "2024-07-01", "variant_id": "baseline_v1", "other_metric": 0.12}],
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("csf_test_evidence"))

    assert result.valid is False
    assert "rank_ic_timeseries.parquet: missing required parquet column rank_ic" in result.errors
