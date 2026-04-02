from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

import yaml

from tools.anti_drift import CanonicalDecisionSnapshot, canonical_snapshot_from_session_context
from tools.backtest_runtime import BACKTEST_READY_DRAFT_FILE
from tools.csf_data_ready_runtime import CSF_DATA_READY_FREEZE_DRAFT_FILE
from tools.csf_signal_ready_runtime import CSF_SIGNAL_READY_FREEZE_DRAFT_FILE
from tools.csf_backtest_runtime import CSF_BACKTEST_READY_DRAFT_FILE
from tools.csf_holdout_runtime import CSF_HOLDOUT_VALIDATION_DRAFT_FILE
from tools.csf_test_evidence_runtime import CSF_TEST_EVIDENCE_DRAFT_FILE
from tools.csf_train_runtime import CSF_TRAIN_FREEZE_DRAFT_FILE
from tools.research_session import run_research_session
from tools.holdout_runtime import HOLDOUT_VALIDATION_DRAFT_FILE
from tools.signal_ready_runtime import SIGNAL_READY_FREEZE_DRAFT_FILE
from tools.test_evidence_runtime import TEST_EVIDENCE_DRAFT_FILE
from tools.train_runtime import TRAIN_FREEZE_DRAFT_FILE


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


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

    stage_dir.mkdir(parents=True, exist_ok=True)
    for name in file_outputs[stage]:
        target = stage_dir / name
        if "." not in target.name:
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.write_text("placeholder\n", encoding="utf-8")


def write_stage_completion_certificate(
    path: Path,
    *,
    stage_status: str = "PASS",
    final_verdict: str | None = None,
) -> None:
    write_yaml(
        path,
        {
            "stage_status": stage_status,
            "final_verdict": final_verdict or stage_status,
        },
    )


def write_placeholder_draft(path: Path) -> None:
    write_yaml(path, {"groups": {}})


def prepare_csf_mandate_review_complete(lineage_root: Path) -> None:
    stage_dir = lineage_root / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_yaml(
        stage_dir / "research_route.yaml",
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
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "02_csf_data_ready" / CSF_DATA_READY_FREEZE_DRAFT_FILE)


def prepare_csf_data_ready_review_complete(lineage_root: Path) -> None:
    prepare_csf_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_data_ready")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "03_csf_signal_ready" / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE)


def prepare_csf_signal_ready_review_complete(lineage_root: Path) -> None:
    prepare_csf_data_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "03_csf_signal_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_signal_ready")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "04_csf_train_freeze" / CSF_TRAIN_FREEZE_DRAFT_FILE)


def prepare_csf_train_freeze_review_complete(lineage_root: Path) -> None:
    prepare_csf_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_csf_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="csf_train_freeze")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "05_csf_test_evidence" / CSF_TEST_EVIDENCE_DRAFT_FILE)


def prepare_csf_test_evidence_review_complete(lineage_root: Path) -> None:
    prepare_csf_train_freeze_review_complete(lineage_root)
    stage_dir = lineage_root / "05_csf_test_evidence"
    write_minimal_stage_outputs(stage_dir, stage="csf_test_evidence")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "06_csf_backtest_ready" / CSF_BACKTEST_READY_DRAFT_FILE)


def prepare_csf_backtest_ready_review_complete(lineage_root: Path) -> None:
    prepare_csf_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_csf_backtest_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_backtest_ready")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "07_csf_holdout_validation" / CSF_HOLDOUT_VALIDATION_DRAFT_FILE)


def prepare_mainline_mandate_review_complete(lineage_root: Path) -> None:
    stage_dir = lineage_root / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_yaml(
        stage_dir / "research_route.yaml",
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
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")


def prepare_mainline_data_ready_review_complete(lineage_root: Path) -> None:
    prepare_mainline_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="data_ready")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "03_signal_ready" / SIGNAL_READY_FREEZE_DRAFT_FILE)


def prepare_mainline_signal_ready_review_complete(lineage_root: Path) -> None:
    prepare_mainline_data_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "03_signal_ready"
    write_minimal_stage_outputs(stage_dir, stage="signal_ready")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "04_train_freeze" / TRAIN_FREEZE_DRAFT_FILE)


def prepare_mainline_train_freeze_review_complete(lineage_root: Path) -> None:
    prepare_mainline_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="train_freeze")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "05_test_evidence" / TEST_EVIDENCE_DRAFT_FILE)


def prepare_mainline_test_evidence_review_complete(lineage_root: Path) -> None:
    prepare_mainline_train_freeze_review_complete(lineage_root)
    stage_dir = lineage_root / "05_test_evidence"
    write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "06_backtest" / BACKTEST_READY_DRAFT_FILE)


def prepare_mainline_backtest_ready_review_complete(lineage_root: Path) -> None:
    prepare_mainline_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_backtest"
    write_minimal_stage_outputs(stage_dir, stage="backtest_ready")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_placeholder_draft(lineage_root / "07_holdout" / HOLDOUT_VALIDATION_DRAFT_FILE)


def snapshot_idea_intake_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    status = run_research_session(
        outputs_root=outputs_root,
        raw_idea="BTC leads high-liquidity alts after shock events",
    )
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="idea-intake-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::idea_intake_confirmation",),
    )


def snapshot_mandate_review(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="mandate-review-replay",
        evidence_refs=("tools/anti_drift_scenarios.py::mandate_review",),
    )


def snapshot_test_evidence_retry(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "05_test_evidence"
    write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="RETRY")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-retry-replay",
        evidence_refs=("tools/anti_drift_scenarios.py::test_evidence_retry",),
    )


def snapshot_train_freeze_pass_for_retry(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "train_retry_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="train_freeze")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS FOR RETRY")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="train-freeze-pass-for-retry",
        evidence_refs=("tools/anti_drift_scenarios.py::train_freeze_pass_for_retry",),
    )


def snapshot_backtest_ready_no_go(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "backtest_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_backtest"
    write_minimal_stage_outputs(stage_dir, stage="backtest_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="backtest-ready-no-go",
        evidence_refs=("tools/anti_drift_scenarios.py::backtest_ready_no_go",),
    )


def snapshot_data_ready_child_lineage(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "data_ready_child_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="data_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="CHILD LINEAGE")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-child-lineage",
        evidence_refs=("tools/anti_drift_scenarios.py::data_ready_child_lineage",),
    )


def snapshot_csf_data_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_case"
    prepare_csf_mandate_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-data-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::csf_data_ready_confirmation",),
    )


def snapshot_csf_signal_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_signal_case"
    prepare_csf_data_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-signal-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::csf_signal_ready_confirmation",),
    )


def snapshot_csf_train_freeze_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_train_case"
    prepare_csf_signal_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-train-freeze-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::csf_train_freeze_confirmation",),
    )


def snapshot_csf_test_evidence_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_test_case"
    prepare_csf_train_freeze_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-test-evidence-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::csf_test_evidence_confirmation",),
    )


def snapshot_csf_backtest_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_backtest_case"
    prepare_csf_test_evidence_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-backtest-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::csf_backtest_ready_confirmation",),
    )


def snapshot_csf_holdout_validation_review_complete(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_holdout_complete_case"
    prepare_csf_backtest_ready_review_complete(outputs_root / lineage_id)
    stage_dir = outputs_root / lineage_id / "07_csf_holdout_validation"
    write_minimal_stage_outputs(stage_dir, stage="csf_holdout_validation")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-holdout-validation-review-complete",
        evidence_refs=("tools/anti_drift_scenarios.py::csf_holdout_validation_review_complete",),
    )


def snapshot_data_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "mainline_case"
    prepare_mainline_mandate_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::data_ready_confirmation",),
    )


def snapshot_signal_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "signal_ready_case"
    prepare_mainline_data_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="signal-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::signal_ready_confirmation",),
    )


def snapshot_train_freeze_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "train_freeze_case"
    prepare_mainline_signal_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="train-freeze-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::train_freeze_confirmation",),
    )


def snapshot_test_evidence_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "test_evidence_case"
    prepare_mainline_train_freeze_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::test_evidence_confirmation",),
    )


def snapshot_backtest_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "backtest_ready_case"
    prepare_mainline_test_evidence_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="backtest-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::backtest_ready_confirmation",),
    )


def snapshot_holdout_validation_review_complete(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "holdout_complete_case"
    prepare_mainline_backtest_ready_review_complete(outputs_root / lineage_id)
    stage_dir = outputs_root / lineage_id / "07_holdout"
    write_minimal_stage_outputs(stage_dir, stage="holdout_validation")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="holdout-validation-review-complete",
        evidence_refs=("tools/anti_drift_scenarios.py::holdout_validation_review_complete",),
    )


SCENARIOS: dict[str, Callable[[Path], CanonicalDecisionSnapshot]] = {
    "idea_intake_confirmation_snapshot.json": snapshot_idea_intake_confirmation,
    "mandate_review_snapshot.json": snapshot_mandate_review,
    "test_evidence_retry_snapshot.json": snapshot_test_evidence_retry,
    "train_freeze_pass_for_retry_snapshot.json": snapshot_train_freeze_pass_for_retry,
    "backtest_ready_no_go_snapshot.json": snapshot_backtest_ready_no_go,
    "data_ready_child_lineage_snapshot.json": snapshot_data_ready_child_lineage,
    "csf_data_ready_confirmation_snapshot.json": snapshot_csf_data_ready_confirmation,
    "csf_signal_ready_confirmation_snapshot.json": snapshot_csf_signal_ready_confirmation,
    "csf_train_freeze_confirmation_snapshot.json": snapshot_csf_train_freeze_confirmation,
    "csf_test_evidence_confirmation_snapshot.json": snapshot_csf_test_evidence_confirmation,
    "csf_backtest_ready_confirmation_snapshot.json": snapshot_csf_backtest_ready_confirmation,
    "csf_holdout_validation_review_complete_snapshot.json": snapshot_csf_holdout_validation_review_complete,
    "data_ready_confirmation_snapshot.json": snapshot_data_ready_confirmation,
    "signal_ready_confirmation_snapshot.json": snapshot_signal_ready_confirmation,
    "train_freeze_confirmation_snapshot.json": snapshot_train_freeze_confirmation,
    "test_evidence_confirmation_snapshot.json": snapshot_test_evidence_confirmation,
    "backtest_ready_confirmation_snapshot.json": snapshot_backtest_ready_confirmation,
    "holdout_validation_review_complete_snapshot.json": snapshot_holdout_validation_review_complete,
}


def export_default_snapshots(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with TemporaryDirectory() as tmp:
        outputs_root = Path(tmp) / "outputs"
        for file_name, builder in SCENARIOS.items():
            snapshot = builder(outputs_root)
            target = output_dir / file_name
            target.write_text(
                json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            written.append(target)
    return written
