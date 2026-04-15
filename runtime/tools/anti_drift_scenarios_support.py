from __future__ import annotations

import json
from pathlib import Path

import yaml

from runtime.tools.backtest_runtime import BACKTEST_READY_DRAFT_FILE
from runtime.tools.csf_backtest_runtime import CSF_BACKTEST_READY_DRAFT_FILE
from runtime.tools.csf_data_ready_runtime import CSF_DATA_READY_FREEZE_DRAFT_FILE
from runtime.tools.csf_holdout_runtime import CSF_HOLDOUT_VALIDATION_DRAFT_FILE
from runtime.tools.csf_signal_ready_runtime import CSF_SIGNAL_READY_FREEZE_DRAFT_FILE
from runtime.tools.csf_test_evidence_runtime import CSF_TEST_EVIDENCE_DRAFT_FILE
from runtime.tools.csf_train_runtime import CSF_TRAIN_FREEZE_DRAFT_FILE
from runtime.tools.holdout_runtime import HOLDOUT_VALIDATION_DRAFT_FILE
from runtime.tools.signal_ready_runtime import SIGNAL_READY_FREEZE_DRAFT_FILE
from runtime.tools.test_evidence_runtime import TEST_EVIDENCE_DRAFT_FILE
from runtime.tools.train_runtime import TRAIN_FREEZE_DRAFT_FILE


def author_formal_path(stage_dir: Path, name: str) -> Path:
    return stage_dir / "author" / "formal" / name


def author_draft_path(stage_dir: Path, name: str) -> Path:
    return stage_dir / "author" / "draft" / name


def review_closure_path(stage_dir: Path, name: str) -> Path:
    return stage_dir / "review" / "closure" / name


def write_review_closure_markers(stage_dir: Path) -> None:
    write_yaml(review_closure_path(stage_dir, "latest_review_pack.yaml"), {"status": "ok"})
    write_yaml(review_closure_path(stage_dir, "stage_gate_review.yaml"), {"status": "ok"})


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def write_program_execution_manifest(stage_dir: Path, *, stage: str) -> None:
    route = "cross_sectional_factor" if stage.startswith("csf_") else "time_series_signal"
    stage_id = stage.removeprefix("csf_")
    program_dir = (
        Path("program/mandate")
        if stage == "mandate"
        else Path("program") / ("cross_sectional_factor" if stage.startswith("csf_") else "time_series") / stage_id
    )
    payload = {
        "stage_id": "mandate" if stage == "mandate" else stage_id,
        "route": "route_neutral" if stage == "mandate" else route,
        "lineage_id": stage_dir.parent.name,
        "stage_status": "awaiting_review_closure",
        "program_dir": str(program_dir),
        "stage_program_manifest_path": str(program_dir / "stage_program.yaml"),
        "entrypoint": "run_stage.py",
        "entry_type": "python",
        "program_hash": "fixture-hash",
        "framework_revision": "fixture-revision",
        "invoked_at": "2026-04-03T00:00:00+00:00",
        "input_refs": [],
        "output_refs": [],
        "authored_by_agent_id": "fixture-agent",
        "authored_by_agent_role": "executor",
        "authoring_session_id": "fixture-session",
        "status": "success",
    }
    author_formal_path(stage_dir, "program_execution_manifest.json").parent.mkdir(parents=True, exist_ok=True)
    author_formal_path(stage_dir, "program_execution_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_minimal_stage_outputs(stage_dir: Path, *, stage: str) -> None:
    file_outputs: dict[str, list[str]] = {
        "mandate": [
            "mandate.md",
            "research_scope.md",
            "research_route.yaml",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "data_ready": [
            "aligned_bars",
            "rolling_stats",
            "pair_stats",
            "benchmark_residual",
            "topic_basket_state",
            "qc_report.parquet",
            "dataset_manifest.json",
            "validation_report.md",
            "data_contract.md",
            "dedupe_rule.md",
            "universe_summary.md",
            "universe_exclusions.csv",
            "universe_exclusions.md",
            "data_ready_gate_decision.md",
            "run_manifest.json",
            "rebuild_data_ready.py",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "signal_ready": [
            "param_manifest.csv",
            "params",
            "signal_coverage.csv",
            "signal_coverage.md",
            "signal_coverage_summary.md",
            "signal_contract.md",
            "signal_fields_contract.md",
            "signal_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "train_freeze": [
            "train_thresholds.json",
            "train_quality.parquet",
            "train_param_ledger.csv",
            "train_rejects.csv",
            "train_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "test_evidence": [
            "report_by_h.parquet",
            "symbol_summary.parquet",
            "admissibility_report.parquet",
            "test_gate_table.csv",
            "crowding_review.md",
            "selected_symbols_test.csv",
            "selected_symbols_test.parquet",
            "frozen_spec.json",
            "test_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "backtest_ready": [
            "engine_compare.csv",
            "vectorbt",
            "backtrader",
            "strategy_combo_ledger.csv",
            "capacity_review.md",
            "backtest_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "holdout_validation": [
            "holdout_run_manifest.json",
            "holdout_backtest_compare.csv",
            "window_results",
            "holdout_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_data_ready": [
            "panel_manifest.json",
            "asset_universe_membership.parquet",
            "cross_section_coverage.parquet",
            "eligibility_base_mask.parquet",
            "shared_feature_base",
            "asset_taxonomy_snapshot.parquet",
            "csf_data_contract.md",
            "csf_data_ready_gate_decision.md",
            "run_manifest.json",
            "rebuild_csf_data_ready.py",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_signal_ready": [
            "factor_panel.parquet",
            "factor_manifest.yaml",
            "component_factor_manifest.yaml",
            "factor_coverage_report.parquet",
            "factor_group_context.parquet",
            "factor_contract.md",
            "factor_field_dictionary.md",
            "csf_signal_ready_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_train_freeze": [
            "csf_train_freeze.yaml",
            "train_factor_quality.parquet",
            "train_variant_ledger.csv",
            "train_variant_rejects.csv",
            "train_bucket_diagnostics.parquet",
            "train_neutralization_diagnostics.parquet",
            "csf_train_contract.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_test_evidence": [
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
        ],
        "csf_backtest_ready": [
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
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_holdout_validation": [
            "csf_holdout_run_manifest.json",
            "holdout_factor_diagnostics.parquet",
            "holdout_test_compare.parquet",
            "holdout_portfolio_compare.parquet",
            "rolling_holdout_stability.json",
            "regime_shift_audit.json",
            "csf_holdout_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
    }

    author_formal = author_formal_path(stage_dir, ".sentinel").parent
    author_formal.mkdir(parents=True, exist_ok=True)
    for name in file_outputs[stage]:
        target = author_formal_path(stage_dir, name)
        if "." not in target.name:
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.write_text("placeholder\n", encoding="utf-8")
    write_program_execution_manifest(stage_dir, stage=stage)


def write_stage_completion_certificate(
    path: Path,
    *,
    stage_status: str = "PASS",
    final_verdict: str | None = None,
) -> None:
    target_path = path
    if path.name == "stage_completion_certificate.yaml" and path.parent.name != "closure":
        target_path = review_closure_path(path.parent, path.name)
    write_yaml(
        target_path,
        {
            "stage_status": stage_status,
            "final_verdict": final_verdict or stage_status,
        },
    )


def write_placeholder_draft(path: Path) -> None:
    target_path = path
    if "author" not in path.parts or "draft" not in path.parts:
        target_path = author_draft_path(path.parent, path.name)
    write_yaml(target_path, {"groups": {}})


def prepare_csf_mandate_review_complete(lineage_root: Path) -> None:
    stage_dir = lineage_root / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_yaml(
        author_formal_path(stage_dir, "research_route.yaml"),
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "regime_filter",
            "factor_structure": "multi_factor_score",
            "portfolio_expression": "long_only_rank",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "trend_combo_v1",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "02_csf_data_ready" / CSF_DATA_READY_FREEZE_DRAFT_FILE)


def prepare_csf_data_ready_review_complete(lineage_root: Path) -> None:
    prepare_csf_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_data_ready")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "03_csf_signal_ready" / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE)


def prepare_csf_signal_ready_review_complete(lineage_root: Path) -> None:
    prepare_csf_data_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "03_csf_signal_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_signal_ready")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "04_csf_train_freeze" / CSF_TRAIN_FREEZE_DRAFT_FILE)


def prepare_csf_train_freeze_review_complete(lineage_root: Path) -> None:
    prepare_csf_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_csf_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="csf_train_freeze")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "05_csf_test_evidence" / CSF_TEST_EVIDENCE_DRAFT_FILE)


def prepare_csf_test_evidence_review_complete(lineage_root: Path) -> None:
    prepare_csf_train_freeze_review_complete(lineage_root)
    stage_dir = lineage_root / "05_csf_test_evidence"
    write_minimal_stage_outputs(stage_dir, stage="csf_test_evidence")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "06_csf_backtest_ready" / CSF_BACKTEST_READY_DRAFT_FILE)


def prepare_csf_backtest_ready_review_complete(lineage_root: Path) -> None:
    prepare_csf_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_csf_backtest_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_backtest_ready")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "07_csf_holdout_validation" / CSF_HOLDOUT_VALIDATION_DRAFT_FILE)


def prepare_mainline_mandate_review_complete(lineage_root: Path) -> None:
    stage_dir = lineage_root / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_yaml(
        author_formal_path(stage_dir, "research_route.yaml"),
        {
            "research_route": "time_series_signal",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "directional_long_short",
            "neutralization_policy": "none",
            "target_strategy_reference": "",
            "group_taxonomy_reference": "",
        },
    )
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")


def prepare_mainline_data_ready_review_complete(lineage_root: Path) -> None:
    prepare_mainline_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="data_ready")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "03_signal_ready" / SIGNAL_READY_FREEZE_DRAFT_FILE)


def prepare_mainline_signal_ready_review_complete(lineage_root: Path) -> None:
    prepare_mainline_data_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "03_signal_ready"
    write_minimal_stage_outputs(stage_dir, stage="signal_ready")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "04_train_freeze" / TRAIN_FREEZE_DRAFT_FILE)


def prepare_mainline_train_freeze_review_complete(lineage_root: Path) -> None:
    prepare_mainline_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="train_freeze")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "05_test_evidence" / TEST_EVIDENCE_DRAFT_FILE)


def prepare_mainline_test_evidence_review_complete(lineage_root: Path) -> None:
    prepare_mainline_train_freeze_review_complete(lineage_root)
    stage_dir = lineage_root / "05_test_evidence"
    write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "06_backtest" / BACKTEST_READY_DRAFT_FILE)


def prepare_mainline_backtest_ready_review_complete(lineage_root: Path) -> None:
    prepare_mainline_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_backtest"
    write_minimal_stage_outputs(stage_dir, stage="backtest_ready")
    write_review_closure_markers(stage_dir)
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "07_holdout" / HOLDOUT_VALIDATION_DRAFT_FILE)
