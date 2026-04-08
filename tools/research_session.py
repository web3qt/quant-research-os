from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml

from tools.data_ready_runtime import (
    DATA_READY_FREEZE_DRAFT_FILE,
    DATA_READY_FREEZE_GROUP_ORDER,
    scaffold_data_ready,
)
from tools.csf_backtest_runtime import (
    CSF_BACKTEST_READY_DRAFT_FILE,
    CSF_BACKTEST_READY_GROUP_ORDER,
    scaffold_csf_backtest_ready,
)
from tools.csf_data_ready_runtime import (
    CSF_DATA_READY_FREEZE_DRAFT_FILE,
    CSF_DATA_READY_FREEZE_GROUP_ORDER,
    scaffold_csf_data_ready,
)
from tools.csf_holdout_runtime import (
    CSF_HOLDOUT_VALIDATION_DRAFT_FILE,
    CSF_HOLDOUT_VALIDATION_GROUP_ORDER,
    scaffold_csf_holdout_validation,
)
from tools.csf_signal_ready_runtime import (
    CSF_SIGNAL_READY_FREEZE_DRAFT_FILE,
    CSF_SIGNAL_READY_FREEZE_GROUP_ORDER,
    scaffold_csf_signal_ready,
)
from tools.csf_test_evidence_runtime import (
    CSF_TEST_EVIDENCE_DRAFT_FILE,
    CSF_TEST_EVIDENCE_GROUP_ORDER,
    scaffold_csf_test_evidence,
)
from tools.csf_train_runtime import (
    CSF_TRAIN_FREEZE_DRAFT_FILE,
    CSF_TRAIN_FREEZE_GROUP_ORDER,
    scaffold_csf_train_freeze,
)
from tools.idea_runtime import (
    MANDATE_FREEZE_DRAFT_FILE,
    MANDATE_FREEZE_GROUP_ORDER,
    SUPPORTED_RESEARCH_ROUTES,
    _require_route_assessment,
    scaffold_idea_intake,
)
from tools.lineage_program_runtime import (
    StageProgramRuntimeError,
    StageProgramSpec,
    inspect_stage_program,
    invoke_stage_if_admitted,
    load_provenance_manifest,
    stage_outputs_complete,
    validate_stage_program,
)
from tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    FIX_REQUIRED_OUTCOME,
    ensure_adversarial_review_request,
    load_adversarial_review_result,
)
from tools.review_skillgen.review_engine import run_stage_review
from tools.signal_ready_runtime import (
    SIGNAL_READY_FREEZE_DRAFT_FILE,
    SIGNAL_READY_FREEZE_GROUP_ORDER,
    scaffold_signal_ready,
)
from tools.stage_program_scaffold import materialize_stage_program
from tools.stage_display_runtime import (
    resolve_stage_display_config,
    supported_stage_ids as supported_stage_display_ids,
    write_stage_display_report,
)
from tools.backtest_runtime import (
    BACKTEST_READY_DRAFT_FILE,
    BACKTEST_READY_GROUP_ORDER,
    backtest_ready_real_outputs_complete,
    scaffold_backtest_ready,
)
from tools.holdout_runtime import (
    HOLDOUT_VALIDATION_DRAFT_FILE,
    HOLDOUT_VALIDATION_GROUP_ORDER,
    scaffold_holdout_validation,
)
from tools.test_evidence_runtime import (
    TEST_EVIDENCE_DRAFT_FILE,
    TEST_EVIDENCE_GROUP_ORDER,
    scaffold_test_evidence,
)
from tools.train_runtime import (
    TRAIN_FREEZE_DRAFT_FILE,
    TRAIN_FREEZE_GROUP_ORDER,
    scaffold_train_freeze,
)


SessionStage = Literal[
    "idea_intake",
    "idea_intake_confirmation_pending",
    "mandate_display_pending",
    "mandate_next_stage_confirmation_pending",
    "mandate_confirmation_pending",
    "mandate_author",
    "mandate_review_confirmation_pending",
    "mandate_review",
    "mandate_display_pending",
    "mandate_next_stage_confirmation_pending",
    "csf_data_ready_confirmation_pending",
    "csf_data_ready_author",
    "csf_data_ready_review_confirmation_pending",
    "csf_data_ready_review",
    "csf_data_ready_display_pending",
    "csf_data_ready_next_stage_confirmation_pending",
    "csf_signal_ready_confirmation_pending",
    "csf_signal_ready_author",
    "csf_signal_ready_review_confirmation_pending",
    "csf_signal_ready_review",
    "csf_signal_ready_display_pending",
    "csf_signal_ready_next_stage_confirmation_pending",
    "csf_train_freeze_confirmation_pending",
    "csf_train_freeze_author",
    "csf_train_freeze_review_confirmation_pending",
    "csf_train_freeze_review",
    "csf_train_freeze_display_pending",
    "csf_train_freeze_next_stage_confirmation_pending",
    "csf_test_evidence_confirmation_pending",
    "csf_test_evidence_author",
    "csf_test_evidence_review_confirmation_pending",
    "csf_test_evidence_review",
    "csf_test_evidence_display_pending",
    "csf_test_evidence_next_stage_confirmation_pending",
    "csf_backtest_ready_confirmation_pending",
    "csf_backtest_ready_author",
    "csf_backtest_ready_review_confirmation_pending",
    "csf_backtest_ready_review",
    "csf_backtest_ready_display_pending",
    "csf_backtest_ready_next_stage_confirmation_pending",
    "csf_holdout_validation_confirmation_pending",
    "csf_holdout_validation_author",
    "csf_holdout_validation_review_confirmation_pending",
    "csf_holdout_validation_review",
    "csf_holdout_validation_display_pending",
    "csf_holdout_validation_next_stage_confirmation_pending",
    "csf_holdout_validation_review_complete",
    "data_ready_display_pending",
    "data_ready_next_stage_confirmation_pending",
    "data_ready_confirmation_pending",
    "data_ready_author",
    "data_ready_review_confirmation_pending",
    "data_ready_review",
    "data_ready_display_pending",
    "data_ready_next_stage_confirmation_pending",
    "signal_ready_confirmation_pending",
    "signal_ready_author",
    "signal_ready_review_confirmation_pending",
    "signal_ready_review",
    "signal_ready_display_pending",
    "signal_ready_next_stage_confirmation_pending",
    "train_freeze_confirmation_pending",
    "train_freeze_author",
    "train_freeze_review_confirmation_pending",
    "train_freeze_review",
    "train_freeze_display_pending",
    "train_freeze_next_stage_confirmation_pending",
    "test_evidence_confirmation_pending",
    "test_evidence_author",
    "test_evidence_review_confirmation_pending",
    "test_evidence_review",
    "test_evidence_display_pending",
    "test_evidence_next_stage_confirmation_pending",
    "backtest_ready_confirmation_pending",
    "backtest_ready_author",
    "backtest_ready_review_confirmation_pending",
    "backtest_ready_review",
    "backtest_ready_display_pending",
    "backtest_ready_next_stage_confirmation_pending",
    "holdout_validation_confirmation_pending",
    "holdout_validation_author",
    "holdout_validation_review_confirmation_pending",
    "holdout_validation_review",
    "holdout_validation_display_pending",
    "holdout_validation_next_stage_confirmation_pending",
    "holdout_validation_review_complete",
]
IdeaIntakeTransitionDecision = Literal["CONFIRM_IDEA_INTAKE", "HOLD", "REFRAME"]
MandateTransitionDecision = Literal["CONFIRM_MANDATE", "HOLD", "REFRAME"]
DataReadyTransitionDecision = Literal["CONFIRM_DATA_READY", "HOLD", "REFRAME"]
SignalReadyTransitionDecision = Literal["CONFIRM_SIGNAL_READY", "HOLD", "REFRAME"]
TrainFreezeTransitionDecision = Literal["CONFIRM_TRAIN_FREEZE", "HOLD", "REFRAME"]
TestEvidenceTransitionDecision = Literal["CONFIRM_TEST_EVIDENCE", "HOLD", "REFRAME"]
BacktestReadyTransitionDecision = Literal["CONFIRM_BACKTEST_READY", "HOLD", "REFRAME"]
HoldoutValidationTransitionDecision = Literal["CONFIRM_HOLDOUT_VALIDATION", "HOLD", "REFRAME"]
ReviewTransitionDecision = Literal["CONFIRM_REVIEW"]
NextStageTransitionDecision = Literal["CONFIRM_NEXT_STAGE"]
MANDATE_REQUIRED_OUTPUTS = [
    "mandate.md",
    "research_scope.md",
    "research_route.yaml",
    "time_split.json",
    "parameter_grid.yaml",
    "run_config.toml",
    "artifact_catalog.md",
    "field_dictionary.md",
]
MANDATE_CLOSURE_OUTPUTS = [
    "latest_review_pack.yaml",
    "stage_gate_review.yaml",
    "stage_completion_certificate.yaml",
]
DATA_READY_REQUIRED_OUTPUTS = [
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
]
CSF_DATA_READY_REQUIRED_OUTPUTS = [
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
]
SIGNAL_READY_REQUIRED_OUTPUTS = [
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
]
CSF_SIGNAL_READY_REQUIRED_OUTPUTS = [
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
]
TRAIN_FREEZE_REQUIRED_OUTPUTS = [
    "train_thresholds.json",
    "train_quality.parquet",
    "train_param_ledger.csv",
    "train_rejects.csv",
    "train_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS = [
    "csf_train_freeze.yaml",
    "train_factor_quality.parquet",
    "train_variant_ledger.csv",
    "train_variant_rejects.csv",
    "train_bucket_diagnostics.parquet",
    "train_neutralization_diagnostics.parquet",
    "csf_train_contract.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
TEST_EVIDENCE_REQUIRED_OUTPUTS = [
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
]
CSF_TEST_EVIDENCE_REQUIRED_OUTPUTS = [
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
]
BACKTEST_READY_REQUIRED_OUTPUTS = [
    "engine_compare.csv",
    "vectorbt",
    "backtrader",
    "strategy_combo_ledger.csv",
    "capacity_review.md",
    "backtest_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
CSF_BACKTEST_READY_REQUIRED_OUTPUTS = [
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
]
HOLDOUT_VALIDATION_REQUIRED_OUTPUTS = [
    "holdout_run_manifest.json",
    "holdout_backtest_compare.csv",
    "window_results",
    "holdout_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
CSF_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS = [
    "csf_holdout_run_manifest.json",
    "holdout_factor_diagnostics.parquet",
    "holdout_test_compare.parquet",
    "holdout_portfolio_compare.parquet",
    "rolling_holdout_stability.json",
    "regime_shift_audit.json",
    "csf_holdout_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
ADVANCING_COMPLETION_STATUSES = {"PASS", "CONDITIONAL PASS", "GO"}
NON_ADVANCING_COMPLETION_STATUSES = {"PASS FOR RETRY", "RETRY", "NO-GO", "CHILD LINEAGE"}
SESSION_STAGE_RUNTIME_SUFFIXES = (
    "_next_stage_confirmation_pending",
    "_display_pending",
    "_review_confirmation_pending",
    "_confirmation_pending",
    "_review_complete",
    "_author",
    "_review",
)
IDEA_INTAKE_TRANSITION_APPROVAL_FILE = "idea_intake_transition_approval.yaml"
MANDATE_TRANSITION_APPROVAL_FILE = "mandate_transition_approval.yaml"
DATA_READY_TRANSITION_APPROVAL_FILE = "data_ready_transition_approval.yaml"
SIGNAL_READY_TRANSITION_APPROVAL_FILE = "signal_ready_transition_approval.yaml"
TRAIN_FREEZE_TRANSITION_APPROVAL_FILE = "train_transition_approval.yaml"
TEST_EVIDENCE_TRANSITION_APPROVAL_FILE = "test_evidence_transition_approval.yaml"
BACKTEST_READY_TRANSITION_APPROVAL_FILE = "backtest_ready_transition_approval.yaml"
HOLDOUT_VALIDATION_TRANSITION_APPROVAL_FILE = "holdout_validation_transition_approval.yaml"
REVIEW_TRANSITION_APPROVAL_FILE = "review_transition_approval.yaml"
NEXT_STAGE_TRANSITION_APPROVAL_FILE = "next_stage_transition_approval.yaml"
DISPLAY_RETRY_STATE_FILE = "display_retry_state.json"
MANDATORY_DISPLAY_MAX_RETRIES = 3


@dataclass(frozen=True)
class SessionContext:
    lineage_id: str
    lineage_root: Path
    lineage_mode: str | None
    lineage_selection_reason: str | None
    current_orchestrator: str
    current_stage: SessionStage
    current_route: str | None
    stage_status: str
    blocking_reason_code: str
    current_skill: str
    why_this_skill: str
    required_program_dir: str | None
    required_program_entrypoint: str | None
    program_contract_status: str
    provenance_status: str
    blocking_reason: str | None
    resume_hint: str
    artifacts_written: list[str]
    gate_status: str
    next_action: str
    why_now: list[str]
    open_risks: list[str]
    factor_role: str | None = None
    factor_structure: str | None = None
    portfolio_expression: str | None = None
    neutralization_policy: str | None = None
    review_verdict: str | None = None
    requires_failure_handling: bool = False
    failure_stage: str | None = None
    failure_reason_summary: str | None = None


STAGE_ACTIVE_SKILLS: dict[SessionStage, str] = {
    "idea_intake": "qros-idea-intake-author",
    "idea_intake_confirmation_pending": "qros-idea-intake-author",
    "mandate_display_pending": "qros-research-session",
    "mandate_next_stage_confirmation_pending": "qros-research-session",
    "mandate_confirmation_pending": "qros-mandate-author",
    "mandate_author": "qros-mandate-author",
    "mandate_review_confirmation_pending": "qros-mandate-review",
    "mandate_review": "qros-mandate-review",
    "mandate_display_pending": "qros-research-session",
    "mandate_next_stage_confirmation_pending": "qros-research-session",
    "csf_data_ready_confirmation_pending": "qros-csf-data-ready-author",
    "csf_data_ready_author": "qros-csf-data-ready-author",
    "csf_data_ready_review_confirmation_pending": "qros-csf-data-ready-review",
    "csf_data_ready_review": "qros-csf-data-ready-review",
    "csf_data_ready_display_pending": "qros-research-session",
    "csf_data_ready_next_stage_confirmation_pending": "qros-research-session",
    "csf_signal_ready_confirmation_pending": "qros-csf-signal-ready-author",
    "csf_signal_ready_author": "qros-csf-signal-ready-author",
    "csf_signal_ready_review_confirmation_pending": "qros-csf-signal-ready-review",
    "csf_signal_ready_review": "qros-csf-signal-ready-review",
    "csf_signal_ready_display_pending": "qros-research-session",
    "csf_signal_ready_next_stage_confirmation_pending": "qros-research-session",
    "csf_train_freeze_confirmation_pending": "qros-csf-train-freeze-author",
    "csf_train_freeze_author": "qros-csf-train-freeze-author",
    "csf_train_freeze_review_confirmation_pending": "qros-csf-train-freeze-review",
    "csf_train_freeze_review": "qros-csf-train-freeze-review",
    "csf_train_freeze_display_pending": "qros-research-session",
    "csf_train_freeze_next_stage_confirmation_pending": "qros-research-session",
    "csf_test_evidence_confirmation_pending": "qros-csf-test-evidence-author",
    "csf_test_evidence_author": "qros-csf-test-evidence-author",
    "csf_test_evidence_review_confirmation_pending": "qros-csf-test-evidence-review",
    "csf_test_evidence_review": "qros-csf-test-evidence-review",
    "csf_test_evidence_display_pending": "qros-research-session",
    "csf_test_evidence_next_stage_confirmation_pending": "qros-research-session",
    "csf_backtest_ready_confirmation_pending": "qros-csf-backtest-ready-author",
    "csf_backtest_ready_author": "qros-csf-backtest-ready-author",
    "csf_backtest_ready_review_confirmation_pending": "qros-csf-backtest-ready-review",
    "csf_backtest_ready_review": "qros-csf-backtest-ready-review",
    "csf_backtest_ready_display_pending": "qros-research-session",
    "csf_backtest_ready_next_stage_confirmation_pending": "qros-research-session",
    "csf_holdout_validation_confirmation_pending": "qros-csf-holdout-validation-author",
    "csf_holdout_validation_author": "qros-csf-holdout-validation-author",
    "csf_holdout_validation_review_confirmation_pending": "qros-csf-holdout-validation-review",
    "csf_holdout_validation_review": "qros-csf-holdout-validation-review",
    "csf_holdout_validation_display_pending": "qros-research-session",
    "csf_holdout_validation_next_stage_confirmation_pending": "qros-research-session",
    "csf_holdout_validation_review_complete": "qros-research-session",
    "data_ready_display_pending": "qros-research-session",
    "data_ready_next_stage_confirmation_pending": "qros-research-session",
    "data_ready_confirmation_pending": "qros-data-ready-author",
    "data_ready_author": "qros-data-ready-author",
    "data_ready_review_confirmation_pending": "qros-data-ready-review",
    "data_ready_review": "qros-data-ready-review",
    "data_ready_display_pending": "qros-research-session",
    "data_ready_next_stage_confirmation_pending": "qros-research-session",
    "signal_ready_confirmation_pending": "qros-signal-ready-author",
    "signal_ready_author": "qros-signal-ready-author",
    "signal_ready_review_confirmation_pending": "qros-signal-ready-review",
    "signal_ready_review": "qros-signal-ready-review",
    "signal_ready_display_pending": "qros-research-session",
    "signal_ready_next_stage_confirmation_pending": "qros-research-session",
    "train_freeze_confirmation_pending": "qros-train-freeze-author",
    "train_freeze_author": "qros-train-freeze-author",
    "train_freeze_review_confirmation_pending": "qros-train-freeze-review",
    "train_freeze_review": "qros-train-freeze-review",
    "train_freeze_display_pending": "qros-research-session",
    "train_freeze_next_stage_confirmation_pending": "qros-research-session",
    "test_evidence_confirmation_pending": "qros-test-evidence-author",
    "test_evidence_author": "qros-test-evidence-author",
    "test_evidence_review_confirmation_pending": "qros-test-evidence-review",
    "test_evidence_review": "qros-test-evidence-review",
    "test_evidence_display_pending": "qros-research-session",
    "test_evidence_next_stage_confirmation_pending": "qros-research-session",
    "backtest_ready_confirmation_pending": "qros-backtest-ready-author",
    "backtest_ready_author": "qros-backtest-ready-author",
    "backtest_ready_review_confirmation_pending": "qros-backtest-ready-review",
    "backtest_ready_review": "qros-backtest-ready-review",
    "backtest_ready_display_pending": "qros-research-session",
    "backtest_ready_next_stage_confirmation_pending": "qros-research-session",
    "holdout_validation_confirmation_pending": "qros-holdout-validation-author",
    "holdout_validation_author": "qros-holdout-validation-author",
    "holdout_validation_review_confirmation_pending": "qros-holdout-validation-review",
    "holdout_validation_review": "qros-holdout-validation-review",
    "holdout_validation_display_pending": "qros-research-session",
    "holdout_validation_next_stage_confirmation_pending": "qros-research-session",
    "holdout_validation_review_complete": "qros-research-session",
}

SESSION_STAGE_PROGRAM_SPECS: dict[str, StageProgramSpec] = {
    "mandate": StageProgramSpec(
        stage_id="mandate",
        route="route_neutral",
        stage_dir_name="01_mandate",
        required_outputs=tuple(MANDATE_REQUIRED_OUTPUTS),
    ),
    "data_ready": StageProgramSpec(
        stage_id="data_ready",
        route="time_series_signal",
        stage_dir_name="02_data_ready",
        required_outputs=tuple(DATA_READY_REQUIRED_OUTPUTS),
    ),
    "signal_ready": StageProgramSpec(
        stage_id="signal_ready",
        route="time_series_signal",
        stage_dir_name="03_signal_ready",
        required_outputs=tuple(SIGNAL_READY_REQUIRED_OUTPUTS),
    ),
    "train_freeze": StageProgramSpec(
        stage_id="train_freeze",
        route="time_series_signal",
        stage_dir_name="04_train_freeze",
        required_outputs=tuple(TRAIN_FREEZE_REQUIRED_OUTPUTS),
    ),
    "test_evidence": StageProgramSpec(
        stage_id="test_evidence",
        route="time_series_signal",
        stage_dir_name="05_test_evidence",
        required_outputs=tuple(TEST_EVIDENCE_REQUIRED_OUTPUTS),
    ),
    "backtest_ready": StageProgramSpec(
        stage_id="backtest_ready",
        route="time_series_signal",
        stage_dir_name="06_backtest",
        required_outputs=tuple(BACKTEST_READY_REQUIRED_OUTPUTS),
    ),
    "holdout_validation": StageProgramSpec(
        stage_id="holdout_validation",
        route="time_series_signal",
        stage_dir_name="07_holdout",
        required_outputs=tuple(HOLDOUT_VALIDATION_REQUIRED_OUTPUTS),
    ),
    "csf_data_ready": StageProgramSpec(
        stage_id="data_ready",
        route="cross_sectional_factor",
        stage_dir_name="02_csf_data_ready",
        required_outputs=tuple(CSF_DATA_READY_REQUIRED_OUTPUTS),
    ),
    "csf_signal_ready": StageProgramSpec(
        stage_id="signal_ready",
        route="cross_sectional_factor",
        stage_dir_name="03_csf_signal_ready",
        required_outputs=tuple(CSF_SIGNAL_READY_REQUIRED_OUTPUTS),
    ),
    "csf_train_freeze": StageProgramSpec(
        stage_id="train_freeze",
        route="cross_sectional_factor",
        stage_dir_name="04_csf_train_freeze",
        required_outputs=tuple(CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS),
    ),
    "csf_test_evidence": StageProgramSpec(
        stage_id="test_evidence",
        route="cross_sectional_factor",
        stage_dir_name="05_csf_test_evidence",
        required_outputs=tuple(CSF_TEST_EVIDENCE_REQUIRED_OUTPUTS),
    ),
    "csf_backtest_ready": StageProgramSpec(
        stage_id="backtest_ready",
        route="cross_sectional_factor",
        stage_dir_name="06_csf_backtest_ready",
        required_outputs=tuple(CSF_BACKTEST_READY_REQUIRED_OUTPUTS),
    ),
    "csf_holdout_validation": StageProgramSpec(
        stage_id="holdout_validation",
        route="cross_sectional_factor",
        stage_dir_name="07_csf_holdout_validation",
        required_outputs=tuple(CSF_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS),
    ),
}

REVIEWABLE_STAGE_BASES = (
    "mandate",
    "data_ready",
    "signal_ready",
    "train_freeze",
    "test_evidence",
    "backtest_ready",
    "holdout_validation",
    "csf_data_ready",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
)

NEXT_STAGE_BY_BASE: dict[str, str | None] = {
    "mandate": "data_ready",
    "data_ready": "signal_ready",
    "signal_ready": "train_freeze",
    "train_freeze": "test_evidence",
    "test_evidence": "backtest_ready",
    "backtest_ready": "holdout_validation",
    "holdout_validation": None,
    "csf_data_ready": "csf_signal_ready",
    "csf_signal_ready": "csf_train_freeze",
    "csf_train_freeze": "csf_test_evidence",
    "csf_test_evidence": "csf_backtest_ready",
    "csf_backtest_ready": "csf_holdout_validation",
    "csf_holdout_validation": None,
}

DISPLAY_IMPLEMENTED_STAGE_BASES = set(supported_stage_display_ids())


def slugify_idea(raw_idea: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", raw_idea.strip().lower())
    normalized = normalized.strip("_")
    if not normalized:
        raise ValueError("raw_idea must contain at least one alphanumeric character")
    return normalized


def resolve_lineage_root(outputs_root: Path, lineage_id: str | None, raw_idea: str | None) -> Path:
    selection = resolve_lineage_selection(outputs_root, lineage_id=lineage_id, raw_idea=raw_idea)
    if selection.resume_blocked:
        raise ValueError(
            f"raw_idea resolved to existing lineage {selection.lineage_id}; use explicit lineage_id to resume it"
        )
    return selection.lineage_root


@dataclass(frozen=True)
class LineageSelection:
    lineage_root: Path
    lineage_id: str
    mode: str
    reason: str
    resume_blocked: bool = False


def resolve_lineage_selection(outputs_root: Path, lineage_id: str | None, raw_idea: str | None) -> LineageSelection:
    if lineage_id:
        lineage_root = outputs_root / lineage_id
        mode = "explicit_resume" if lineage_root.exists() and any(lineage_root.iterdir()) else "explicit_lineage_target"
        reason = (
            f"Explicit lineage_id {lineage_id} was provided, so qros-session is targeting that lineage directly."
        )
        return LineageSelection(
            lineage_root=lineage_root,
            lineage_id=lineage_id,
            mode=mode,
            reason=reason,
        )
    if raw_idea:
        derived_lineage_id = slugify_idea(raw_idea)
        lineage_root = outputs_root / derived_lineage_id
        if lineage_root.exists() and any(lineage_root.iterdir()):
            return LineageSelection(
                lineage_root=lineage_root,
                lineage_id=derived_lineage_id,
                mode="resume_blocked_existing_slug",
                reason=(
                    f"raw_idea resolved to existing lineage {derived_lineage_id}, but explicit resume intent was not provided."
                ),
                resume_blocked=True,
            )
        return LineageSelection(
            lineage_root=lineage_root,
            lineage_id=derived_lineage_id,
            mode="fresh_start",
            reason=f"raw_idea resolved to fresh lineage slug {derived_lineage_id}.",
        )
    raise ValueError("Either lineage_id or raw_idea must be provided")


def detect_session_stage(lineage_root: Path) -> SessionStage:
    intake_dir = lineage_root / "00_idea_intake"
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = lineage_root / "02_data_ready"
    signal_ready_dir = lineage_root / "03_signal_ready"
    train_dir = lineage_root / "04_train_freeze"
    test_evidence_dir = lineage_root / "05_test_evidence"
    backtest_dir = lineage_root / "06_backtest"
    holdout_dir = lineage_root / "07_holdout"
    csf_data_ready_dir = lineage_root / "02_csf_data_ready"
    csf_signal_ready_dir = lineage_root / "03_csf_signal_ready"
    csf_train_dir = lineage_root / "04_csf_train_freeze"
    csf_test_evidence_dir = lineage_root / "05_csf_test_evidence"
    csf_backtest_dir = lineage_root / "06_csf_backtest_ready"
    csf_holdout_dir = lineage_root / "07_csf_holdout_validation"
    is_csf_route = _is_csf_route(lineage_root)

    if is_csf_route:
        if _csf_holdout_validation_outputs_complete(csf_holdout_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="csf_holdout_validation",
                stage_dir=csf_holdout_dir,
                closure_complete=_csf_holdout_validation_closure_complete(csf_holdout_dir),
            )

        if _csf_backtest_ready_outputs_complete(csf_backtest_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="csf_backtest_ready",
                stage_dir=csf_backtest_dir,
                closure_complete=_csf_backtest_ready_closure_complete(csf_backtest_dir),
            )

        if _csf_test_evidence_outputs_complete(csf_test_evidence_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="csf_test_evidence",
                stage_dir=csf_test_evidence_dir,
                closure_complete=_csf_test_evidence_closure_complete(csf_test_evidence_dir),
            )

        if _csf_train_freeze_outputs_complete(csf_train_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="csf_train_freeze",
                stage_dir=csf_train_dir,
                closure_complete=_csf_train_freeze_closure_complete(csf_train_dir),
            )

        if _csf_signal_ready_outputs_complete(csf_signal_ready_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="csf_signal_ready",
                stage_dir=csf_signal_ready_dir,
                closure_complete=_csf_signal_ready_closure_complete(csf_signal_ready_dir),
            )

        if _csf_data_ready_outputs_complete(csf_data_ready_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="csf_data_ready",
                stage_dir=csf_data_ready_dir,
                closure_complete=_csf_data_ready_closure_complete(csf_data_ready_dir),
            )

        if _mandate_outputs_complete(mandate_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="mandate",
                stage_dir=mandate_dir,
                closure_complete=_mandate_closure_complete(mandate_dir),
            )

    if _holdout_validation_outputs_complete(holdout_dir):
        return _review_or_post_review_stage(
            lineage_root,
            stage_base="holdout_validation",
            stage_dir=holdout_dir,
            closure_complete=_holdout_validation_closure_complete(holdout_dir),
        )

    if _backtest_ready_outputs_complete(backtest_dir):
        return _review_or_post_review_stage(
            lineage_root,
            stage_base="backtest_ready",
            stage_dir=backtest_dir,
            closure_complete=_backtest_ready_closure_complete(backtest_dir),
        )

    if _test_evidence_outputs_complete(test_evidence_dir):
        return _review_or_post_review_stage(
            lineage_root,
            stage_base="test_evidence",
            stage_dir=test_evidence_dir,
            closure_complete=_test_evidence_closure_complete(test_evidence_dir),
        )

    if _train_freeze_outputs_complete(train_dir):
        return _review_or_post_review_stage(
            lineage_root,
            stage_base="train_freeze",
            stage_dir=train_dir,
            closure_complete=_train_freeze_closure_complete(train_dir),
        )

    if _signal_ready_outputs_complete(signal_ready_dir):
        return _review_or_post_review_stage(
            lineage_root,
            stage_base="signal_ready",
            stage_dir=signal_ready_dir,
            closure_complete=_signal_ready_closure_complete(signal_ready_dir),
        )

    if _data_ready_outputs_complete(data_ready_dir):
        return _review_or_post_review_stage(
            lineage_root,
            stage_base="data_ready",
            stage_dir=data_ready_dir,
            closure_complete=_data_ready_closure_complete(data_ready_dir),
        )

    if _mandate_outputs_complete(mandate_dir):
        return _review_or_post_review_stage(
            lineage_root,
            stage_base="mandate",
            stage_dir=mandate_dir,
            closure_complete=_mandate_closure_complete(mandate_dir),
        )

    if not intake_dir.exists():
        return "idea_intake"

    intake_approval = read_idea_intake_transition_decision(lineage_root)
    if intake_approval != "CONFIRM_IDEA_INTAKE":
        return "idea_intake_confirmation_pending"

    gate_path = intake_dir / "idea_gate_decision.yaml"
    if not gate_path.exists():
        return "idea_intake"

    gate_decision = _read_yaml(gate_path)
    if gate_decision.get("verdict") != "GO_TO_MANDATE":
        return "idea_intake"
    if _route_assessment_error(gate_decision) is not None:
        return "idea_intake"

    approval_decision = read_mandate_transition_decision(lineage_root)
    if approval_decision == "CONFIRM_MANDATE" and next_mandate_freeze_group(lineage_root) is None:
        return "mandate_author"
    if approval_decision == "REFRAME":
        return "idea_intake"

    return "mandate_confirmation_pending"


def ensure_intake_scaffold(lineage_root: Path) -> list[str]:
    intake_dir = lineage_root / "00_idea_intake"
    if intake_dir.exists():
        return []

    scaffold_idea_intake(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in intake_dir.iterdir())


def build_mandate_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "mandate_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "mandate_author")
    except StageProgramRuntimeError:
        return []


def ensure_data_ready_scaffold(lineage_root: Path) -> list[str]:
    data_ready_dir = lineage_root / "02_data_ready"
    if data_ready_dir.exists() and (data_ready_dir / DATA_READY_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_data_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in data_ready_dir.iterdir())


def build_data_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "data_ready_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "data_ready_author")
    except StageProgramRuntimeError:
        return []


def ensure_csf_data_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "02_csf_data_ready"
    if stage_dir.exists() and (stage_dir / CSF_DATA_READY_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_csf_data_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_data_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "csf_data_ready_author":
        return []
    if next_csf_data_ready_freeze_group(lineage_root) is not None:
        return []
    inspection = inspect_stage_program(lineage_root, "data_ready", "cross_sectional_factor")
    if inspection.error_code == "STAGE_PROGRAM_MISSING":
        try:
            materialize_stage_program(
                lineage_root,
                "csf_data_ready",
                authored_by_agent_id="codex",
                authored_by_agent_role="executor",
                authoring_session_id="auto-csf-data-ready-program",
            )
            validate_stage_program(lineage_root, "data_ready", "cross_sectional_factor")
        except StageProgramRuntimeError:
            return []
    try:
        return _invoke_program_stage(lineage_root, "csf_data_ready_author")
    except StageProgramRuntimeError:
        return []


def ensure_signal_ready_scaffold(lineage_root: Path) -> list[str]:
    signal_ready_dir = lineage_root / "03_signal_ready"
    if signal_ready_dir.exists() and (signal_ready_dir / SIGNAL_READY_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_signal_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in signal_ready_dir.iterdir())


def build_signal_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "signal_ready_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "signal_ready_author")
    except StageProgramRuntimeError:
        return []


def ensure_csf_signal_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "03_csf_signal_ready"
    if stage_dir.exists() and (stage_dir / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_csf_signal_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_signal_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "csf_signal_ready_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "csf_signal_ready_author")
    except StageProgramRuntimeError:
        return []


def ensure_train_freeze_scaffold(lineage_root: Path) -> list[str]:
    train_dir = lineage_root / "04_train_freeze"
    if train_dir.exists() and (train_dir / TRAIN_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_train_freeze(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in train_dir.iterdir())


def build_train_freeze_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "train_freeze_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "train_freeze_author")
    except StageProgramRuntimeError:
        return []


def ensure_csf_train_freeze_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "04_csf_train_freeze"
    if stage_dir.exists() and (stage_dir / CSF_TRAIN_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_csf_train_freeze(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_train_freeze_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "csf_train_freeze_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "csf_train_freeze_author")
    except StageProgramRuntimeError:
        return []


def ensure_test_evidence_scaffold(lineage_root: Path) -> list[str]:
    test_dir = lineage_root / "05_test_evidence"
    if test_dir.exists() and (test_dir / TEST_EVIDENCE_DRAFT_FILE).exists():
        return []

    scaffold_test_evidence(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in test_dir.iterdir())


def build_test_evidence_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "test_evidence_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "test_evidence_author")
    except StageProgramRuntimeError:
        return []


def ensure_csf_test_evidence_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "05_csf_test_evidence"
    if stage_dir.exists() and (stage_dir / CSF_TEST_EVIDENCE_DRAFT_FILE).exists():
        return []

    scaffold_csf_test_evidence(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_test_evidence_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "csf_test_evidence_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "csf_test_evidence_author")
    except StageProgramRuntimeError:
        return []


def ensure_backtest_ready_scaffold(lineage_root: Path) -> list[str]:
    backtest_dir = lineage_root / "06_backtest"
    if backtest_dir.exists() and (backtest_dir / BACKTEST_READY_DRAFT_FILE).exists():
        return []

    scaffold_backtest_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in backtest_dir.iterdir())


def build_backtest_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "backtest_ready_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "backtest_ready_author")
    except StageProgramRuntimeError:
        return []


def ensure_csf_backtest_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "06_csf_backtest_ready"
    if stage_dir.exists() and (stage_dir / CSF_BACKTEST_READY_DRAFT_FILE).exists():
        return []

    scaffold_csf_backtest_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_backtest_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "csf_backtest_ready_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "csf_backtest_ready_author")
    except StageProgramRuntimeError:
        return []


def ensure_holdout_validation_scaffold(lineage_root: Path) -> list[str]:
    holdout_dir = lineage_root / "07_holdout"
    if holdout_dir.exists() and (holdout_dir / HOLDOUT_VALIDATION_DRAFT_FILE).exists():
        return []

    scaffold_holdout_validation(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in holdout_dir.iterdir())


def build_holdout_validation_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "holdout_validation_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "holdout_validation_author")
    except StageProgramRuntimeError:
        return []


def ensure_csf_holdout_validation_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "07_csf_holdout_validation"
    if stage_dir.exists() and (stage_dir / CSF_HOLDOUT_VALIDATION_DRAFT_FILE).exists():
        return []

    scaffold_csf_holdout_validation(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_holdout_validation_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "csf_holdout_validation_author":
        return []
    try:
        return _invoke_program_stage(lineage_root, "csf_holdout_validation_author")
    except StageProgramRuntimeError:
        return []


def run_mandate_review_if_ready(lineage_root: Path) -> dict[str, object] | None:
    if detect_session_stage(lineage_root) != "mandate_review":
        return None

    mandate_dir = lineage_root / "01_mandate"
    if not (mandate_dir / "review_findings.yaml").exists():
        return None

    return run_stage_review(
        explicit_context={
            "lineage_id": lineage_root.name,
            "lineage_root": lineage_root,
            "stage": "mandate",
            "stage_dir": mandate_dir,
        }
    )


def write_mandate_transition_decision(
    lineage_root: Path,
    *,
    decision: MandateTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    gate_decision = _read_yaml(approval_path.parent / "idea_gate_decision.yaml")
    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_gate_verdict": gate_decision.get("verdict", ""),
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_idea_intake_transition_decision(
    lineage_root: Path,
    *,
    decision: IdeaIntakeTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _idea_intake_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "idea_intake_interview",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_data_ready_transition_decision(
    lineage_root: Path,
    *,
    decision: DataReadyTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _data_ready_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "mandate_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_signal_ready_transition_decision(
    lineage_root: Path,
    *,
    decision: SignalReadyTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _signal_ready_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "data_ready_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_train_freeze_transition_decision(
    lineage_root: Path,
    *,
    decision: TrainFreezeTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _train_freeze_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "signal_ready_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_test_evidence_transition_decision(
    lineage_root: Path,
    *,
    decision: TestEvidenceTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _test_evidence_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "train_freeze_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_backtest_ready_transition_decision(
    lineage_root: Path,
    *,
    decision: BacktestReadyTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _backtest_ready_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "test_evidence_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_holdout_validation_transition_decision(
    lineage_root: Path,
    *,
    decision: HoldoutValidationTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _holdout_validation_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "backtest_ready_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_review_transition_decision(
    lineage_root: Path,
    *,
    current_stage: SessionStage,
    decision: ReviewTransitionDecision = "CONFIRM_REVIEW",
    approved_by: str = "codex",
) -> str | None:
    stage_base = _stage_base_name(current_stage)
    approval_path = _review_transition_approval_path(lineage_root, stage_base)
    if approval_path is None:
        return None

    approval_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "stage_id": stage_base,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": f"{stage_base}_review_confirmation_pending",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_next_stage_transition_decision(
    lineage_root: Path,
    *,
    current_stage: SessionStage,
    decision: NextStageTransitionDecision = "CONFIRM_NEXT_STAGE",
    approved_by: str = "codex",
) -> str | None:
    stage_base = _stage_base_name(current_stage)
    approval_path = _next_stage_transition_approval_path(lineage_root, stage_base)
    if approval_path is None:
        return None

    approval_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "stage_id": stage_base,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": f"{stage_base}_next_stage_confirmation_pending",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def read_mandate_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_MANDATE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_idea_intake_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _idea_intake_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_IDEA_INTAKE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_data_ready_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _data_ready_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_DATA_READY", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_signal_ready_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _signal_ready_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_SIGNAL_READY", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_train_freeze_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _train_freeze_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_TRAIN_FREEZE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_test_evidence_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _test_evidence_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_TEST_EVIDENCE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_backtest_ready_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _backtest_ready_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_BACKTEST_READY", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_holdout_validation_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _holdout_validation_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_HOLDOUT_VALIDATION", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_review_transition_decision(lineage_root: Path, *, stage_base: str) -> str | None:
    approval_path = _review_transition_approval_path(lineage_root, stage_base)
    if approval_path is None or not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision == "CONFIRM_REVIEW":
        return str(decision)
    return None


def _supports_stage_display(stage_base: str) -> bool:
    return stage_base in DISPLAY_IMPLEMENTED_STAGE_BASES


def _stage_display_artifact_paths(lineage_root: Path, *, stage_base: str) -> tuple[Path, Path] | None:
    if not _supports_stage_display(stage_base):
        return None
    config = resolve_stage_display_config(stage_base)
    display_dir = (lineage_root / "reports" / "stage_display").resolve()
    return display_dir / config.summary_filename, display_dir / config.html_filename


def _read_stage_display_summary(lineage_root: Path, *, stage_base: str) -> dict | None:
    artifact_paths = _stage_display_artifact_paths(lineage_root, stage_base=stage_base)
    if artifact_paths is None:
        return None
    summary_path, _ = artifact_paths
    if not summary_path.exists():
        return None
    try:
        loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _stage_display_render_status(lineage_root: Path, *, stage_base: str) -> str | None:
    summary = _read_stage_display_summary(lineage_root, stage_base=stage_base)
    if summary is None:
        return None
    status = summary.get("render_status")
    return str(status) if isinstance(status, str) and status.strip() else None


def _stage_display_render_error(lineage_root: Path, *, stage_base: str) -> str | None:
    summary = _read_stage_display_summary(lineage_root, stage_base=stage_base)
    if summary is None:
        return None
    error = summary.get("render_error")
    return str(error) if isinstance(error, str) and error.strip() else None


def _stage_display_retry_state_path(lineage_root: Path, *, stage_base: str) -> Path | None:
    if not _supports_stage_display(stage_base):
        return None
    config = resolve_stage_display_config(stage_base)
    return (lineage_root / "reports" / "stage_display" / f"{config.stage_id}.{DISPLAY_RETRY_STATE_FILE}").resolve()


def _read_stage_display_retry_state(lineage_root: Path, *, stage_base: str) -> dict | None:
    path = _stage_display_retry_state_path(lineage_root, stage_base=stage_base)
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _write_stage_display_retry_state(
    lineage_root: Path,
    *,
    stage_base: str,
    attempt_count: int,
    status: str,
    last_error: str | None = None,
) -> Path | None:
    path = _stage_display_retry_state_path(lineage_root, stage_base=stage_base)
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "stage_id": stage_base,
                "lineage_id": lineage_root.name,
                "attempt_count": attempt_count,
                "status": status,
                "last_error": last_error,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _stage_display_summary_status(lineage_root: Path, *, stage_base: str) -> str | None:
    summary = _read_stage_display_summary(lineage_root, stage_base=stage_base)
    if summary is None:
        return None
    status = summary.get("status")
    return str(status) if isinstance(status, str) and status.strip() else None


def _stage_display_missing_required_inputs(lineage_root: Path, *, stage_base: str) -> list[str]:
    summary = _read_stage_display_summary(lineage_root, stage_base=stage_base)
    if summary is None:
        return []
    raw_value = summary.get("missing_required_inputs")
    if not isinstance(raw_value, list):
        return []
    return [str(item) for item in raw_value if str(item).strip()]


def _stage_display_html_path(lineage_root: Path, *, stage_base: str) -> Path | None:
    paths = _stage_display_artifact_paths(lineage_root, stage_base=stage_base)
    if paths is None:
        return None
    _, html_path = paths
    return html_path


def _invoke_stage_display(
    lineage_root: Path,
    *,
    current_stage: SessionStage,
) -> list[str]:
    stage_base = _stage_base_name(current_stage)
    if not _supports_stage_display(stage_base):
        return []
    result = write_stage_display_report(lineage_root=lineage_root, stage_id=stage_base)
    written: list[str] = []
    for key in ("structured_summary_path", "html_path"):
        path = Path(result[key]).resolve()
        if path.exists():
            written.append(str(path.relative_to(lineage_root.resolve())))
    return written


def _auto_progress_display(lineage_root: Path, *, current_stage: SessionStage) -> list[str]:
    if not current_stage.endswith("_display_pending"):
        return []

    stage_base = _stage_base_name(current_stage)
    if not _supports_stage_display(stage_base):
        return []

    render_status = _stage_display_render_status(lineage_root, stage_base=stage_base)
    retry_state = _read_stage_display_retry_state(lineage_root, stage_base=stage_base) or {}
    attempt_count = int(retry_state.get("attempt_count", 0))

    if render_status == "complete":
        _write_stage_display_retry_state(
            lineage_root,
            stage_base=stage_base,
            attempt_count=max(attempt_count, 1),
            status="complete",
        )
        return []

    if render_status == "failed" and attempt_count >= MANDATORY_DISPLAY_MAX_RETRIES:
        _write_stage_display_retry_state(
            lineage_root,
            stage_base=stage_base,
            attempt_count=attempt_count,
            status="failed",
            last_error=_stage_display_render_error(lineage_root, stage_base=stage_base),
        )
        return []

    next_attempt = attempt_count + 1 if attempt_count else 1
    written = _invoke_stage_display(lineage_root, current_stage=current_stage)
    updated_render_status = _stage_display_render_status(lineage_root, stage_base=stage_base)
    updated_error = _stage_display_render_error(lineage_root, stage_base=stage_base)
    retry_path = _write_stage_display_retry_state(
        lineage_root,
        stage_base=stage_base,
        attempt_count=next_attempt,
        status=updated_render_status or "failed",
        last_error=updated_error,
    )
    if retry_path is not None:
        written.append(str(retry_path.relative_to(lineage_root.resolve())))
    return sorted(set(written))


def _stage_display_ready_for_handoff(lineage_root: Path, *, stage_base: str) -> bool:
    return (
        _stage_display_render_status(lineage_root, stage_base=stage_base) == "complete"
        and _stage_display_summary_status(lineage_root, stage_base=stage_base) == "complete"
    )


def read_next_stage_transition_decision(lineage_root: Path, *, stage_base: str) -> str | None:
    approval_path = _next_stage_transition_approval_path(lineage_root, stage_base)
    if approval_path is None or not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision == "CONFIRM_NEXT_STAGE":
        return str(decision)
    return None


def session_transition_summary(
    lineage_root: Path, current_stage: SessionStage
) -> tuple[list[str], list[str]]:
    gate_path = lineage_root / "00_idea_intake" / "idea_gate_decision.yaml"
    if not gate_path.exists():
        return [], []

    gate_decision = _read_yaml(gate_path)
    why_now = [str(item) for item in gate_decision.get("why", []) if item]
    open_risks: list[str] = []
    if current_stage in {"idea_intake", "idea_intake_confirmation_pending"}:
        open_risks = [str(item) for item in gate_decision.get("required_reframe_actions", []) if item]
        if not open_risks and gate_decision.get("rollback_target"):
            open_risks = [f"rollback_target remains {gate_decision['rollback_target']}"]
    return why_now, open_risks


def current_research_route(lineage_root: Path) -> str | None:
    mandate_route_path = lineage_root / "01_mandate" / "research_route.yaml"
    if mandate_route_path.exists():
        route_payload = _read_yaml(mandate_route_path)
        route_value = str(route_payload.get("research_route", "")).strip()
        if route_value in SUPPORTED_RESEARCH_ROUTES:
            return route_value

    gate_path = lineage_root / "00_idea_intake" / "idea_gate_decision.yaml"
    if gate_path.exists():
        gate_payload = _read_yaml(gate_path)
        if _route_assessment_error(gate_payload) is None:
            route_assessment = gate_payload.get("route_assessment", {})
            if isinstance(route_assessment, dict):
                route_value = str(route_assessment.get("recommended_route", "")).strip()
                if route_value in SUPPORTED_RESEARCH_ROUTES:
                    return route_value

    return None


def current_route_contract(lineage_root: Path) -> dict[str, str | None]:
    mandate_route_path = lineage_root / "01_mandate" / "research_route.yaml"
    if not mandate_route_path.exists():
        return {
            "factor_role": None,
            "factor_structure": None,
            "portfolio_expression": None,
            "neutralization_policy": None,
        }

    route_payload = _read_yaml(mandate_route_path)
    return {
        "factor_role": _optional_payload_value(route_payload.get("factor_role")),
        "factor_structure": _optional_payload_value(route_payload.get("factor_structure")),
        "portfolio_expression": _optional_payload_value(route_payload.get("portfolio_expression")),
        "neutralization_policy": _optional_payload_value(route_payload.get("neutralization_policy")),
    }


def next_mandate_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "00_idea_intake" / MANDATE_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return MANDATE_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in MANDATE_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_data_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "02_data_ready" / DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return DATA_READY_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in DATA_READY_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_csf_data_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "02_csf_data_ready" / CSF_DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return CSF_DATA_READY_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in CSF_DATA_READY_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_signal_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "03_signal_ready" / SIGNAL_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return SIGNAL_READY_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in SIGNAL_READY_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_csf_signal_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "03_csf_signal_ready" / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return CSF_SIGNAL_READY_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in CSF_SIGNAL_READY_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_train_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "04_train_freeze" / TRAIN_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return TRAIN_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in TRAIN_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_csf_train_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "04_csf_train_freeze" / CSF_TRAIN_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return CSF_TRAIN_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in CSF_TRAIN_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_test_evidence_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "05_test_evidence" / TEST_EVIDENCE_DRAFT_FILE
    if not draft_path.exists():
        return TEST_EVIDENCE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in TEST_EVIDENCE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_csf_test_evidence_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "05_csf_test_evidence" / CSF_TEST_EVIDENCE_DRAFT_FILE
    if not draft_path.exists():
        return CSF_TEST_EVIDENCE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in CSF_TEST_EVIDENCE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_backtest_ready_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "06_backtest" / BACKTEST_READY_DRAFT_FILE
    if not draft_path.exists():
        return BACKTEST_READY_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in BACKTEST_READY_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_csf_backtest_ready_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "06_csf_backtest_ready" / CSF_BACKTEST_READY_DRAFT_FILE
    if not draft_path.exists():
        return CSF_BACKTEST_READY_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in CSF_BACKTEST_READY_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_holdout_validation_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "07_holdout" / HOLDOUT_VALIDATION_DRAFT_FILE
    if not draft_path.exists():
        return HOLDOUT_VALIDATION_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in HOLDOUT_VALIDATION_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_csf_holdout_validation_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "07_csf_holdout_validation" / CSF_HOLDOUT_VALIDATION_DRAFT_FILE
    if not draft_path.exists():
        return CSF_HOLDOUT_VALIDATION_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in CSF_HOLDOUT_VALIDATION_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def summarize_session_status(
    *,
    lineage_id: str,
    lineage_root: Path,
    lineage_mode: str | None,
    lineage_selection_reason: str | None,
    current_stage: SessionStage,
    current_route: str | None,
    artifacts_written: list[str],
    gate_status: str,
    next_action: str,
    why_now: list[str] | None = None,
    open_risks: list[str] | None = None,
    factor_role: str | None = None,
    factor_structure: str | None = None,
    portfolio_expression: str | None = None,
    neutralization_policy: str | None = None,
    current_skill: str | None = None,
    why_this_skill: str | None = None,
    blocking_reason: str | None = None,
    resume_hint: str | None = None,
    review_verdict: str | None = None,
    requires_failure_handling: bool = False,
    failure_stage: str | None = None,
    failure_reason_summary: str | None = None,
) -> SessionContext:
    (
        stage_status,
        blocking_reason_code,
        required_program_dir,
        required_program_entrypoint,
        program_contract_status,
        provenance_status,
        runtime_blocking_reason,
        runtime_next_action,
    ) = _program_runtime_status(
        lineage_root=lineage_root,
        current_stage=current_stage,
        review_verdict=review_verdict,
        requires_failure_handling=requires_failure_handling,
    )
    resolved_current_skill = current_skill or _current_skill_for_stage(
        current_stage=current_stage,
        requires_failure_handling=requires_failure_handling,
        runtime_stage_status=stage_status,
    )
    resolved_why_this_skill = why_this_skill or _why_this_skill(
        current_stage=current_stage,
        current_skill=resolved_current_skill,
        review_verdict=review_verdict,
        requires_failure_handling=requires_failure_handling,
        runtime_stage_status=stage_status,
    )
    resolved_blocking_reason = (
        blocking_reason
        if blocking_reason is not None
        else runtime_blocking_reason
    )
    resolved_resume_hint = resume_hint or _resume_hint(
        lineage_id=lineage_id,
        current_stage=current_stage,
        current_skill=resolved_current_skill,
        requires_failure_handling=requires_failure_handling,
        runtime_stage_status=stage_status,
    )
    return SessionContext(
        lineage_id=lineage_id,
        lineage_root=lineage_root,
        lineage_mode=lineage_mode,
        lineage_selection_reason=lineage_selection_reason,
        current_orchestrator="qros-research-session",
        current_stage=current_stage,
        current_route=current_route,
        stage_status=stage_status,
        blocking_reason_code=blocking_reason_code,
        current_skill=resolved_current_skill,
        why_this_skill=resolved_why_this_skill,
        required_program_dir=required_program_dir,
        required_program_entrypoint=required_program_entrypoint,
        program_contract_status=program_contract_status,
        provenance_status=provenance_status,
        blocking_reason=resolved_blocking_reason,
        resume_hint=resolved_resume_hint,
        artifacts_written=artifacts_written,
        gate_status=gate_status,
        next_action=(
            runtime_next_action
            if requires_failure_handling or current_stage.endswith("_author") or current_stage.endswith("_review_complete")
            else next_action
        ),
        why_now=why_now or [],
        open_risks=open_risks or [],
        factor_role=factor_role,
        factor_structure=factor_structure,
        portfolio_expression=portfolio_expression,
        neutralization_policy=neutralization_policy,
        review_verdict=review_verdict,
        requires_failure_handling=requires_failure_handling,
        failure_stage=failure_stage,
        failure_reason_summary=failure_reason_summary,
    )


def _lineage_resume_blocked_status(*, selection: LineageSelection) -> SessionContext:
    return SessionContext(
        lineage_id=selection.lineage_id,
        lineage_root=selection.lineage_root,
        lineage_mode=selection.mode,
        lineage_selection_reason=selection.reason,
        current_orchestrator="qros-research-session",
        current_stage="idea_intake_confirmation_pending",
        current_route=None,
        stage_status="awaiting_lineage_selection",
        blocking_reason_code="LINEAGE_RESUME_BLOCKED",
        current_skill="qros-research-session",
        why_this_skill=(
            "Current run started from raw_idea, but that slug already exists as an older lineage, "
            "so qros-session blocked implicit resume."
        ),
        required_program_dir=None,
        required_program_entrypoint=None,
        program_contract_status="not_applicable",
        provenance_status="not_applicable",
        blocking_reason=(
            f"Implicit resume of existing lineage {selection.lineage_id} is blocked until you explicitly choose to continue it."
        ),
        resume_hint=(
            f"Rerun with --lineage-id {selection.lineage_id} to continue that lineage, or change the raw idea text to start a different branch."
        ),
        artifacts_written=[],
        gate_status="LINEAGE_RESUME_BLOCKED",
        next_action=(
            f"Resume blocked for existing lineage {selection.lineage_id}. Use --lineage-id {selection.lineage_id} to continue it explicitly."
        ),
        why_now=[],
        open_risks=[],
    )


def _current_skill_for_stage(
    *,
    current_stage: SessionStage,
    requires_failure_handling: bool,
    runtime_stage_status: str | None = None,
) -> str:
    if requires_failure_handling:
        return "qros-stage-failure-handler"
    if runtime_stage_status == "awaiting_author_fix" and current_stage.endswith("_review"):
        return STAGE_ACTIVE_SKILLS.get(f"{_stage_base_name(current_stage)}_author", "qros-research-session")
    return STAGE_ACTIVE_SKILLS.get(current_stage, "qros-research-session")


def _why_this_skill(
    *,
    current_stage: SessionStage,
    current_skill: str,
    review_verdict: str | None,
    requires_failure_handling: bool,
    runtime_stage_status: str | None = None,
) -> str:
    if requires_failure_handling:
        verdict = review_verdict or "a failure-class review result"
        return (
            f"Review verdict {verdict} blocks normal progression, so failure handling is now the active workflow."
        )
    if current_stage.endswith("_display_pending"):
        return f"Current stage {current_stage} is running the mandatory post-review display phase before progression can continue."
    if current_stage.endswith("_next_stage_confirmation_pending"):
        return f"Current stage {current_stage} is waiting for explicit approval before entering the downstream stage."
    if current_stage.endswith("_review_complete"):
        return "The covered workflow has reached a terminal review-complete state, so qros-research-session is reporting completion status."
    if current_stage.endswith("_review_confirmation_pending"):
        return f"Current stage {current_stage} is paused before review entry, so {current_skill} is the active review-confirm skill."
    if current_stage.endswith("_review"):
        if runtime_stage_status == "awaiting_author_fix":
            return f"Current stage {current_stage} has fixable adversarial findings, so {current_skill} is the active author-fix skill."
        return f"Current stage {current_stage} requires formal review closure, so {current_skill} is the active review skill."
    if current_stage.endswith("_display_pending"):
        return f"Current stage {current_stage} is in the mandatory display phase, so {current_skill} is holding the orchestration gate."
    if current_stage.endswith("_next_stage_confirmation_pending"):
        return f"Current stage {current_stage} is waiting for explicit next-stage confirmation, so {current_skill} is holding the orchestration gate."
    return f"Current stage {current_stage} is in the authoring/freeze flow, so {current_skill} is the active author skill."


def _blocking_reason(
    *,
    current_stage: SessionStage,
    review_verdict: str | None,
    requires_failure_handling: bool,
) -> str | None:
    if requires_failure_handling:
        verdict = review_verdict or "a failure-class review result"
        return f"Normal progression is blocked by review verdict {verdict}."
    if current_stage == "idea_intake":
        return "Idea intake inputs or admission evidence are still incomplete."
    if current_stage.endswith("_review_confirmation_pending"):
        return f"{_stage_base_name(current_stage)} review entry is still waiting for explicit confirmation."
    if current_stage.endswith("_display_pending"):
        return f"{_stage_base_name(current_stage)} mandatory display has not completed yet."
    if current_stage.endswith("_next_stage_confirmation_pending"):
        next_stage_base = NEXT_STAGE_BY_BASE.get(_stage_base_name(current_stage))
        if next_stage_base is None:
            return f"{_stage_base_name(current_stage)} terminal completion confirmation is still incomplete."
        return f"Explicit confirmation to enter {next_stage_base} is still incomplete."
    if current_stage.endswith("_confirmation_pending"):
        if current_stage == "idea_intake_confirmation_pending":
            return "Explicit idea intake confirmation is still incomplete."
        return f"{_stage_base_name(current_stage)} freeze confirmation is still incomplete."
    if current_stage.endswith("_review"):
        return f"{_stage_base_name(current_stage)} review closure is still incomplete."
    if current_stage.endswith("_author"):
        return f"{_stage_base_name(current_stage)} authoring outputs are still incomplete."
    return None


def _resume_hint(
    *,
    lineage_id: str,
    current_stage: SessionStage,
    current_skill: str,
    requires_failure_handling: bool,
    runtime_stage_status: str | None = None,
) -> str:
    if requires_failure_handling:
        return (
            f"Invoke {current_skill} for lineage {lineage_id} in the same research repo, "
            f"then rerun qros-session --lineage-id {lineage_id}."
        )
    if current_stage.endswith("_review_confirmation_pending"):
        return (
            f"Confirm review entry for {_stage_base_name(current_stage)}, then rerun "
            f"qros-session --lineage-id {lineage_id}."
        )
    if current_stage.endswith("_review"):
        if runtime_stage_status == "awaiting_author_fix":
            return (
                f"Run {current_skill} to address fix-required findings, then rerun the review workflow and "
                f"qros-session --lineage-id {lineage_id}."
            )
        return (
            f"Run {current_skill} in the same research repo, or rerun qros-session --lineage-id {lineage_id} "
            "to inspect updated status."
        )
    if current_stage.endswith("_display_pending"):
        return (
            f"Rerun qros-session --lineage-id {lineage_id} to continue the mandatory display phase for "
            f"{_stage_base_name(current_stage)}."
        )
    if current_stage.endswith("_next_stage_confirmation_pending"):
        return (
            f"Confirm the next-stage handoff for {_stage_base_name(current_stage)}, then rerun "
            f"qros-session --lineage-id {lineage_id}."
        )
    if current_stage.endswith("_review_complete"):
        return f"Rerun qros-session --lineage-id {lineage_id} if new downstream work is introduced."
    return (
        f"Continue in the same research repo and rerun qros-session --lineage-id {lineage_id} "
        "after completing the next required step."
    )


def session_stage_base_name(current_stage: SessionStage | str) -> str:
    for suffix in (
        "_review_confirmation_pending",
        "_display_pending",
        "_next_stage_confirmation_pending",
        "_confirmation_pending",
        "_author",
        "_review_complete",
        "_review",
    ):
        if current_stage.endswith(suffix):
            return current_stage[: -len(suffix)]
    return current_stage


def _stage_base_name(current_stage: SessionStage) -> str:
    return session_stage_base_name(current_stage)


def _program_spec_for_session_stage(current_stage: SessionStage) -> StageProgramSpec | None:
    return SESSION_STAGE_PROGRAM_SPECS.get(_stage_base_name(current_stage))


def _stage_dir_for_session_stage(lineage_root: Path, current_stage: SessionStage) -> Path | None:
    spec = _program_spec_for_session_stage(current_stage)
    if spec is None:
        return None
    return lineage_root / spec.stage_dir_name


def _load_adversarial_review_result_if_present(stage_dir: Path) -> dict | None:
    result_path = stage_dir / ADVERSARIAL_REVIEW_RESULT_FILENAME
    if not result_path.exists():
        return None
    return load_adversarial_review_result(result_path)


def _ensure_review_request_for_stage(lineage_root: Path, current_stage: SessionStage) -> None:
    if not current_stage.endswith("_review"):
        return
    spec = _program_spec_for_session_stage(current_stage)
    if spec is None:
        return
    inspection = inspect_stage_program(lineage_root, spec.stage_id, spec.route)
    if inspection.error_code is not None or inspection.required_program_entrypoint is None:
        return
    stage_dir = lineage_root / spec.stage_dir_name
    provenance = load_provenance_manifest(stage_dir)
    if provenance is None:
        return
    if not all((stage_dir / output_name).exists() for output_name in spec.required_outputs):
        return
    author_identity = provenance.get("authored_by_agent_id")
    author_session_id = provenance.get("authoring_session_id")
    if not isinstance(author_identity, str) or not author_identity.strip():
        return
    if not isinstance(author_session_id, str) or not author_session_id.strip():
        return
    ensure_adversarial_review_request(
        stage_dir,
        lineage_id=lineage_root.name,
        stage=spec.stage_id,
        author_identity=author_identity.strip(),
        author_session_id=author_session_id.strip(),
        required_program_dir=inspection.required_program_dir,
        required_program_entrypoint=inspection.required_program_entrypoint,
        required_artifact_paths=list(spec.required_outputs),
        required_provenance_paths=["program_execution_manifest.json"],
        program_hash=provenance.get("program_hash") if isinstance(provenance.get("program_hash"), str) else None,
        stage_invoked_at=provenance.get("invoked_at") if isinstance(provenance.get("invoked_at"), str) else None,
    )


def _invoke_program_stage(lineage_root: Path, current_stage: SessionStage) -> list[str]:
    spec = _program_spec_for_session_stage(current_stage)
    if spec is None:
        return []
    resolved_lineage_root = lineage_root.resolve()
    result = invoke_stage_if_admitted(resolved_lineage_root, spec)
    written = {
        str(result.provenance_path.resolve().relative_to(resolved_lineage_root)),
        str(result.manifest_path.resolve().relative_to(resolved_lineage_root)),
    }
    for ref in result.output_refs:
        written.add(ref)
    return sorted(written)


def _review_substate(
    *,
    stage_dir: Path,
    current_stage: SessionStage,
    lineage_root: Path,
) -> tuple[str, str, str, str]:
    request_path = stage_dir / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    review_result = _load_adversarial_review_result_if_present(stage_dir)
    stage_base = _stage_base_name(current_stage)
    author_skill = STAGE_ACTIVE_SKILLS.get(f"{stage_base}_author", "qros-research-session")
    review_skill = STAGE_ACTIVE_SKILLS.get(current_stage, "qros-research-session")
    if not request_path.exists():
        return (
            "awaiting_adversarial_review",
            "ADVERSARIAL_REVIEW_PENDING",
            f"{stage_base} is ready for independent adversarial review, but {ADVERSARIAL_REVIEW_REQUEST_FILENAME} is missing.",
            f"Rerun qros-session --lineage-id {lineage_root.name} to issue the review request, then run {review_skill}.",
        )
    if review_result is None:
        return (
            "awaiting_adversarial_review",
            "ADVERSARIAL_REVIEW_PENDING",
            f"{stage_base} is waiting for an independent adversarial reviewer to inspect artifacts and source code.",
            f"Run {review_skill} to produce {ADVERSARIAL_REVIEW_RESULT_FILENAME}.",
        )
    if review_result["review_loop_outcome"] == FIX_REQUIRED_OUTCOME:
        return (
            "awaiting_author_fix",
            "AUTHOR_FIX_REQUIRED",
            f"{stage_base} received fixable adversarial review findings and must return to the author lane before closure.",
            f"Run {author_skill} to fix findings, then rerun {review_skill}.",
        )
    return (
        "awaiting_review_closure",
        "REVIEW_CLOSURE_PENDING",
        f"{stage_base} has a closure-ready adversarial review result and is waiting for deterministic closure artifacts.",
        f"Run {review_skill} to validate findings and write closure artifacts.",
    )


def _program_runtime_status(
    *,
    lineage_root: Path,
    current_stage: SessionStage,
    review_verdict: str | None,
    requires_failure_handling: bool,
) -> tuple[str, str, str | None, str | None, str, str, str | None, str]:
    spec = _program_spec_for_session_stage(current_stage)
    if spec is None:
        if requires_failure_handling:
            return (
                "blocked_requires_failure_handling",
                "FAILURE_HANDLER_REQUIRED",
                None,
                None,
                "n/a",
                "n/a",
                f"Normal progression is blocked by review verdict {review_verdict or 'a failure-class review result'}.",
                f"Enter failure handling for {_stage_base_name(current_stage)} via qros-stage-failure-handler",
            )
        if current_stage.endswith("_review_complete"):
            return ("review_complete", "NONE", None, None, "n/a", "n/a", None, "No further action required.")
        return (
            "awaiting_freeze_approval",
            "FREEZE_APPROVAL_MISSING",
            None,
            None,
            "n/a",
            "missing",
            _blocking_reason(
                current_stage=current_stage,
                review_verdict=review_verdict,
                requires_failure_handling=requires_failure_handling,
            ),
            "",
        )

    inspection = inspect_stage_program(lineage_root, spec.stage_id, spec.route)
    provenance = load_provenance_manifest(lineage_root / spec.stage_dir_name)
    provenance_status = "recorded" if provenance is not None else "missing"

    if requires_failure_handling:
        return (
            "blocked_requires_failure_handling",
            "FAILURE_HANDLER_REQUIRED",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            f"Normal progression is blocked by review verdict {review_verdict or 'a failure-class review result'}.",
            f"Enter failure handling for {_stage_base_name(current_stage)} via qros-stage-failure-handler",
        )
    if current_stage.endswith("_review_complete"):
        return (
            "review_complete",
            "NONE",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            None,
            "No further action required.",
        )
    if current_stage.endswith("_review_confirmation_pending"):
        next_action = _gate_status_and_next_action(lineage_root, current_stage)[1]
        return (
            "awaiting_review_confirmation",
            "REVIEW_CONFIRMATION_REQUIRED",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            _blocking_reason(
                current_stage=current_stage,
                review_verdict=review_verdict,
                requires_failure_handling=requires_failure_handling,
            ),
            next_action,
        )
    if current_stage.endswith("_review"):
        review_stage_dir = lineage_root / spec.stage_dir_name
        review_state, review_reason_code, review_blocking_reason, review_next_action = _review_substate(
            stage_dir=review_stage_dir,
            current_stage=current_stage,
            lineage_root=lineage_root,
        )
        return (
            review_state,
            review_reason_code,
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            review_blocking_reason,
            review_next_action,
        )
    if current_stage.endswith("_display_pending"):
        gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
        reason_code = {
            "DISPLAY_RENDER_PENDING": "DISPLAY_RENDER_PENDING",
            "DISPLAY_RETRYING": "DISPLAY_RETRYING",
            "DISPLAY_RENDER_FAILED": "DISPLAY_RENDER_FAILED",
            "DISPLAY_RETRY_EXHAUSTED": "DISPLAY_RETRY_EXHAUSTED",
            "DISPLAY_NOT_IMPLEMENTED": "DISPLAY_NOT_IMPLEMENTED",
            "DISPLAY_RENDER_COMPLETE": "DISPLAY_RENDER_PENDING",
        }.get(gate_status, "DISPLAY_RENDER_PENDING")
        stage_status = "display_running" if gate_status in {"DISPLAY_RENDER_PENDING", "DISPLAY_RETRYING"} else "display_blocked"
        return (
            stage_status,
            reason_code,
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            _blocking_reason(
                current_stage=current_stage,
                review_verdict=review_verdict,
                requires_failure_handling=requires_failure_handling,
            ),
            next_action,
        )
    if current_stage.endswith("_next_stage_confirmation_pending"):
        gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
        reason_code = "NEXT_STAGE_CONFIRMATION_REQUIRED" if gate_status == "NEXT_STAGE_CONFIRMATION_PENDING" else gate_status
        return (
            "awaiting_next_stage_confirmation",
            reason_code,
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            _blocking_reason(
                current_stage=current_stage,
                review_verdict=review_verdict,
                requires_failure_handling=requires_failure_handling,
            ),
            next_action,
        )
    if current_stage.endswith("_confirmation_pending"):
        next_action = _gate_status_and_next_action(lineage_root, current_stage)[1]
        return (
            "awaiting_freeze_approval",
            "FREEZE_APPROVAL_MISSING",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            _blocking_reason(
                current_stage=current_stage,
                review_verdict=review_verdict,
                requires_failure_handling=requires_failure_handling,
            ),
            next_action,
        )
    if inspection.error_code == "STAGE_PROGRAM_MISSING":
        return (
            "awaiting_stage_program",
            "STAGE_PROGRAM_MISSING",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            inspection.error_message,
            f"Author the lineage-local stage program under {inspection.required_program_dir}.",
        )
    if inspection.error_code is not None:
        return (
            "awaiting_program_validation",
            "STAGE_PROGRAM_INVALID",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            inspection.error_message,
            f"Fix {inspection.required_program_dir}/stage_program.yaml and its entrypoint contract.",
        )
    stage_dir = lineage_root / spec.stage_dir_name
    missing_outputs = [name for name in spec.required_outputs if not (stage_dir / name).exists()]
    if provenance is None and not missing_outputs:
        return (
            "awaiting_program_execution",
            "PROVENANCE_MISSING",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            f"{_stage_base_name(current_stage)} outputs cannot advance without program_execution_manifest.json provenance.",
            f"Run the lineage-local entrypoint {inspection.required_program_entrypoint} from {inspection.required_program_dir}.",
        )
    if missing_outputs:
        return (
            "awaiting_program_execution",
            "OUTPUTS_INVALID",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            "Stage program has not produced all required outputs: " + ", ".join(missing_outputs),
            f"Run or fix the lineage-local entrypoint {inspection.required_program_entrypoint} in {inspection.required_program_dir}.",
        )
    return (
        "awaiting_program_execution",
        "PROGRAM_EXECUTION_FAILED",
        inspection.required_program_dir,
        inspection.required_program_entrypoint,
        inspection.program_contract_status,
        provenance_status,
        f"{_stage_base_name(current_stage)} authoring outputs are still incomplete.",
        f"Run the lineage-local entrypoint {inspection.required_program_entrypoint} from {inspection.required_program_dir}.",
    )


def run_research_session(
    *,
    outputs_root: Path,
    lineage_id: str | None = None,
    raw_idea: str | None = None,
    idea_intake_decision: IdeaIntakeTransitionDecision | None = None,
    mandate_decision: MandateTransitionDecision | None = None,
    data_ready_decision: DataReadyTransitionDecision | None = None,
    signal_ready_decision: SignalReadyTransitionDecision | None = None,
    train_freeze_decision: TrainFreezeTransitionDecision | None = None,
    test_evidence_decision: TestEvidenceTransitionDecision | None = None,
    backtest_ready_decision: BacktestReadyTransitionDecision | None = None,
    holdout_validation_decision: HoldoutValidationTransitionDecision | None = None,
    review_decision: ReviewTransitionDecision | None = None,
    next_stage_decision: NextStageTransitionDecision | None = None,
) -> SessionContext:
    selection = resolve_lineage_selection(outputs_root, lineage_id=lineage_id, raw_idea=raw_idea)
    lineage_root = selection.lineage_root
    if selection.resume_blocked:
        return _lineage_resume_blocked_status(selection=selection)
    lineage_root.mkdir(parents=True, exist_ok=True)

    artifacts_written: list[str] = []
    if idea_intake_decision is not None:
        artifacts_written.append(
            write_idea_intake_transition_decision(lineage_root, decision=idea_intake_decision)
        )
    if mandate_decision is not None:
        artifacts_written.append(
            write_mandate_transition_decision(lineage_root, decision=mandate_decision)
        )
    if data_ready_decision is not None:
        artifacts_written.append(
            write_data_ready_transition_decision(lineage_root, decision=data_ready_decision)
        )
    if signal_ready_decision is not None:
        artifacts_written.append(
            write_signal_ready_transition_decision(lineage_root, decision=signal_ready_decision)
        )
    if train_freeze_decision is not None:
        artifacts_written.append(
            write_train_freeze_transition_decision(lineage_root, decision=train_freeze_decision)
        )
    if test_evidence_decision is not None:
        artifacts_written.append(
            write_test_evidence_transition_decision(lineage_root, decision=test_evidence_decision)
        )
    if backtest_ready_decision is not None:
        artifacts_written.append(
            write_backtest_ready_transition_decision(lineage_root, decision=backtest_ready_decision)
        )
    if holdout_validation_decision is not None:
        artifacts_written.append(
            write_holdout_validation_transition_decision(
                lineage_root, decision=holdout_validation_decision
            )
        )
    current_stage = detect_session_stage(lineage_root)

    if review_decision is not None:
        written = write_review_transition_decision(
            lineage_root,
            current_stage=current_stage,
            decision=review_decision,
        )
        if written is not None:
            artifacts_written.append(written)
        current_stage = detect_session_stage(lineage_root)

    if next_stage_decision is not None:
        written = write_next_stage_transition_decision(
            lineage_root,
            current_stage=current_stage,
            decision=next_stage_decision,
        )
        if written is not None:
            artifacts_written.append(written)
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "idea_intake":
        artifacts_written.extend(ensure_intake_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "mandate_author":
        artifacts_written.extend(build_mandate_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "data_ready_confirmation_pending":
        artifacts_written.extend(ensure_data_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "data_ready_author":
        artifacts_written.extend(build_data_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "signal_ready_confirmation_pending":
        artifacts_written.extend(ensure_signal_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "signal_ready_author":
        artifacts_written.extend(build_signal_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "train_freeze_confirmation_pending":
        artifacts_written.extend(ensure_train_freeze_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "train_freeze_author":
        artifacts_written.extend(build_train_freeze_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "test_evidence_confirmation_pending":
        artifacts_written.extend(ensure_test_evidence_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "test_evidence_author":
        artifacts_written.extend(build_test_evidence_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "backtest_ready_confirmation_pending":
        artifacts_written.extend(ensure_backtest_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "backtest_ready_author":
        artifacts_written.extend(build_backtest_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "holdout_validation_confirmation_pending":
        artifacts_written.extend(ensure_holdout_validation_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "holdout_validation_author":
        artifacts_written.extend(build_holdout_validation_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_data_ready_confirmation_pending":
        artifacts_written.extend(ensure_csf_data_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_data_ready_author":
        artifacts_written.extend(build_csf_data_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_signal_ready_confirmation_pending":
        artifacts_written.extend(ensure_csf_signal_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_signal_ready_author":
        artifacts_written.extend(build_csf_signal_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_train_freeze_confirmation_pending":
        artifacts_written.extend(ensure_csf_train_freeze_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_train_freeze_author":
        artifacts_written.extend(build_csf_train_freeze_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_test_evidence_confirmation_pending":
        artifacts_written.extend(ensure_csf_test_evidence_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_test_evidence_author":
        artifacts_written.extend(build_csf_test_evidence_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_backtest_ready_confirmation_pending":
        artifacts_written.extend(ensure_csf_backtest_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_backtest_ready_author":
        artifacts_written.extend(build_csf_backtest_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_holdout_validation_confirmation_pending":
        artifacts_written.extend(ensure_csf_holdout_validation_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "csf_holdout_validation_author":
        artifacts_written.extend(build_csf_holdout_validation_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage.endswith("_display_pending"):
        artifacts_written.extend(
            _auto_progress_display(
                lineage_root,
                current_stage=current_stage,
            )
        )
        current_stage = detect_session_stage(lineage_root)

    _ensure_review_request_for_stage(lineage_root, current_stage)
    gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
    review_verdict, requires_failure_handling, failure_stage, failure_reason_summary = (
        _latest_review_failure_status(lineage_root)
    )
    if requires_failure_handling and failure_stage is not None:
        gate_status = "FAILURE_HANDLING_REQUIRED"
        next_action = f"Enter failure handling for {failure_stage} via qros-stage-failure-handler"
    why_now, open_risks = session_transition_summary(lineage_root, current_stage)
    current_route = current_research_route(lineage_root)
    route_contract = current_route_contract(lineage_root)
    return summarize_session_status(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        lineage_mode=selection.mode,
        lineage_selection_reason=selection.reason,
        current_stage=current_stage,
        current_route=current_route,
        artifacts_written=artifacts_written,
        gate_status=gate_status,
        next_action=next_action,
        why_now=why_now,
        open_risks=open_risks,
        factor_role=route_contract["factor_role"],
        factor_structure=route_contract["factor_structure"],
        portfolio_expression=route_contract["portfolio_expression"],
        neutralization_policy=route_contract["neutralization_policy"],
        review_verdict=review_verdict,
        requires_failure_handling=requires_failure_handling,
        failure_stage=failure_stage,
        failure_reason_summary=failure_reason_summary,
    )


def _mandate_outputs_complete(mandate_dir: Path) -> bool:
    return stage_outputs_complete(mandate_dir, MANDATE_REQUIRED_OUTPUTS)


def _data_ready_outputs_complete(data_ready_dir: Path) -> bool:
    return stage_outputs_complete(data_ready_dir, DATA_READY_REQUIRED_OUTPUTS)


def _csf_data_ready_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, CSF_DATA_READY_REQUIRED_OUTPUTS)


def _signal_ready_outputs_complete(signal_ready_dir: Path) -> bool:
    return stage_outputs_complete(signal_ready_dir, SIGNAL_READY_REQUIRED_OUTPUTS)


def _csf_signal_ready_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, CSF_SIGNAL_READY_REQUIRED_OUTPUTS)


def _train_freeze_outputs_complete(train_dir: Path) -> bool:
    return stage_outputs_complete(train_dir, TRAIN_FREEZE_REQUIRED_OUTPUTS)


def _csf_train_freeze_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS)


def _test_evidence_outputs_complete(test_dir: Path) -> bool:
    return stage_outputs_complete(test_dir, TEST_EVIDENCE_REQUIRED_OUTPUTS)


def _csf_test_evidence_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, CSF_TEST_EVIDENCE_REQUIRED_OUTPUTS)


def _backtest_ready_outputs_complete(backtest_dir: Path) -> bool:
    return stage_outputs_complete(backtest_dir, BACKTEST_READY_REQUIRED_OUTPUTS) and backtest_ready_real_outputs_complete(
        backtest_dir
    )


def _csf_backtest_ready_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, CSF_BACKTEST_READY_REQUIRED_OUTPUTS)


def _holdout_validation_outputs_complete(holdout_dir: Path) -> bool:
    return stage_outputs_complete(holdout_dir, HOLDOUT_VALIDATION_REQUIRED_OUTPUTS)


def _csf_holdout_validation_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, CSF_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS)


def _completion_certificate_allows_progress(stage_dir: Path) -> bool:
    payload = _read_yaml(stage_dir / "stage_completion_certificate.yaml")
    if not payload:
        return True

    stage_status = payload.get("stage_status") or payload.get("final_verdict")
    if stage_status in ADVANCING_COMPLETION_STATUSES:
        return True
    if stage_status in NON_ADVANCING_COMPLETION_STATUSES:
        return False
    return True


def _review_verdict_from_stage_dir(stage_dir: Path) -> str | None:
    certificate_path = stage_dir / "stage_completion_certificate.yaml"
    if not certificate_path.exists():
        return None

    payload = _read_yaml(certificate_path)
    if not payload:
        return None

    verdict = payload.get("stage_status") or payload.get("final_verdict")
    if isinstance(verdict, str) and verdict.strip():
        return verdict
    return None


def _latest_review_failure_status(
    lineage_root: Path,
) -> tuple[str | None, bool, str | None, str | None]:
    if _is_csf_route(lineage_root):
        review_stage_dirs = [
            ("csf_holdout_validation_review", lineage_root / "07_csf_holdout_validation", True),
            ("csf_backtest_ready_review", lineage_root / "06_csf_backtest_ready", True),
            ("csf_test_evidence_review", lineage_root / "05_csf_test_evidence", True),
            ("csf_train_freeze_review", lineage_root / "04_csf_train_freeze", True),
            ("csf_signal_ready_review", lineage_root / "03_csf_signal_ready", True),
            ("csf_data_ready_review", lineage_root / "02_csf_data_ready", True),
            ("mandate_review", lineage_root / "01_mandate", False),
        ]
    else:
        review_stage_dirs = [
            ("holdout_validation_review", lineage_root / "07_holdout", True),
            ("backtest_ready_review", lineage_root / "06_backtest", True),
            ("test_evidence_review", lineage_root / "05_test_evidence", True),
            ("train_freeze_review", lineage_root / "04_train_freeze", True),
            ("signal_ready_review", lineage_root / "03_signal_ready", True),
            ("data_ready_review", lineage_root / "02_data_ready", True),
            ("mandate_review", lineage_root / "01_mandate", False),
        ]

    for review_stage, stage_dir, routes_into_failure_handler in review_stage_dirs:
        verdict = _review_verdict_from_stage_dir(stage_dir)
        if verdict is None:
            continue
        if verdict in NON_ADVANCING_COMPLETION_STATUSES and routes_into_failure_handler:
            return (
                verdict,
                True,
                review_stage,
                f"{review_stage} requires failure handling because review verdict is {verdict}.",
            )
        return verdict, False, None, None

    return None, False, None, None


def _review_or_post_review_stage(
    lineage_root: Path,
    *,
    stage_base: str,
    stage_dir: Path,
    closure_complete: bool,
) -> SessionStage:
    if closure_complete:
        return _post_review_completion_stage(lineage_root, stage_base=stage_base)
    if _review_has_started(stage_dir):
        return f"{stage_base}_review"  # type: ignore[return-value]
    return f"{stage_base}_review_confirmation_pending"  # type: ignore[return-value]


def _review_has_started(stage_dir: Path) -> bool:
    return any(
        (stage_dir / name).exists()
        for name in (
            ADVERSARIAL_REVIEW_REQUEST_FILENAME,
            ADVERSARIAL_REVIEW_RESULT_FILENAME,
            "stage_completion_certificate.yaml",
        )
    )


def _post_review_completion_stage(lineage_root: Path, *, stage_base: str) -> SessionStage:
    if not _supports_stage_display(stage_base):
        return f"{stage_base}_display_pending"  # type: ignore[return-value]
    if not _stage_display_ready_for_handoff(lineage_root, stage_base=stage_base):
        return f"{stage_base}_display_pending"  # type: ignore[return-value]

    next_stage_decision = read_next_stage_transition_decision(lineage_root, stage_base=stage_base)
    if next_stage_decision is None:
        return f"{stage_base}_next_stage_confirmation_pending"  # type: ignore[return-value]

    next_stage_base = NEXT_STAGE_BY_BASE[stage_base]
    if next_stage_base is None:
        return f"{stage_base}_review_complete"  # type: ignore[return-value]

    return _next_stage_entry_state(lineage_root, next_stage_base=next_stage_base)


def _next_stage_entry_state(lineage_root: Path, *, next_stage_base: str) -> SessionStage:
    if next_stage_base == "data_ready":
        approval_decision = read_data_ready_transition_decision(lineage_root)
        if _is_csf_route(lineage_root):
            if approval_decision == "CONFIRM_DATA_READY" and next_csf_data_ready_freeze_group(lineage_root) is None:
                return "csf_data_ready_author"
            return "csf_data_ready_confirmation_pending"
        if approval_decision == "CONFIRM_DATA_READY" and next_data_ready_freeze_group(lineage_root) is None:
            return "data_ready_author"
        return "data_ready_confirmation_pending"
    if next_stage_base == "signal_ready":
        approval_decision = read_signal_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_SIGNAL_READY" and next_signal_ready_freeze_group(lineage_root) is None:
            return "signal_ready_author"
        return "signal_ready_confirmation_pending"
    if next_stage_base == "train_freeze":
        approval_decision = read_train_freeze_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_TRAIN_FREEZE" and next_train_freeze_group(lineage_root) is None:
            return "train_freeze_author"
        return "train_freeze_confirmation_pending"
    if next_stage_base == "test_evidence":
        approval_decision = read_test_evidence_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_TEST_EVIDENCE" and next_test_evidence_group(lineage_root) is None:
            return "test_evidence_author"
        return "test_evidence_confirmation_pending"
    if next_stage_base == "backtest_ready":
        approval_decision = read_backtest_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_BACKTEST_READY" and next_backtest_ready_group(lineage_root) is None:
            return "backtest_ready_author"
        return "backtest_ready_confirmation_pending"
    if next_stage_base == "holdout_validation":
        approval_decision = read_holdout_validation_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_HOLDOUT_VALIDATION" and next_holdout_validation_group(lineage_root) is None:
            return "holdout_validation_author"
        return "holdout_validation_confirmation_pending"
    if next_stage_base == "csf_data_ready":
        approval_decision = read_data_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_DATA_READY" and next_csf_data_ready_freeze_group(lineage_root) is None:
            return "csf_data_ready_author"
        return "csf_data_ready_confirmation_pending"
    if next_stage_base == "csf_signal_ready":
        approval_decision = read_signal_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_SIGNAL_READY" and next_csf_signal_ready_freeze_group(lineage_root) is None:
            return "csf_signal_ready_author"
        return "csf_signal_ready_confirmation_pending"
    if next_stage_base == "csf_train_freeze":
        approval_decision = read_train_freeze_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_TRAIN_FREEZE" and next_csf_train_freeze_group(lineage_root) is None:
            return "csf_train_freeze_author"
        return "csf_train_freeze_confirmation_pending"
    if next_stage_base == "csf_test_evidence":
        approval_decision = read_test_evidence_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_TEST_EVIDENCE" and next_csf_test_evidence_group(lineage_root) is None:
            return "csf_test_evidence_author"
        return "csf_test_evidence_confirmation_pending"
    if next_stage_base == "csf_backtest_ready":
        approval_decision = read_backtest_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_BACKTEST_READY" and next_csf_backtest_ready_group(lineage_root) is None:
            return "csf_backtest_ready_author"
        return "csf_backtest_ready_confirmation_pending"
    if next_stage_base == "csf_holdout_validation":
        approval_decision = read_holdout_validation_transition_decision(lineage_root)
        if (
            approval_decision == "CONFIRM_HOLDOUT_VALIDATION"
            and next_csf_holdout_validation_group(lineage_root) is None
        ):
            return "csf_holdout_validation_author"
        return "csf_holdout_validation_confirmation_pending"
    raise ValueError(f"Unsupported next stage base: {next_stage_base}")


def _mandate_closure_complete(mandate_dir: Path) -> bool:
    if (mandate_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(mandate_dir)
    return all((mandate_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _data_ready_closure_complete(data_ready_dir: Path) -> bool:
    if (data_ready_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(data_ready_dir)
    return all((data_ready_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _csf_data_ready_closure_complete(stage_dir: Path) -> bool:
    if (stage_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(stage_dir)
    return all((stage_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _signal_ready_closure_complete(signal_ready_dir: Path) -> bool:
    if (signal_ready_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(signal_ready_dir)
    return all((signal_ready_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _csf_signal_ready_closure_complete(stage_dir: Path) -> bool:
    if (stage_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(stage_dir)
    return all((stage_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _train_freeze_closure_complete(train_dir: Path) -> bool:
    if (train_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(train_dir)
    return all((train_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _csf_train_freeze_closure_complete(stage_dir: Path) -> bool:
    if (stage_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(stage_dir)
    return all((stage_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _test_evidence_closure_complete(test_dir: Path) -> bool:
    if (test_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(test_dir)
    return all((test_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _csf_test_evidence_closure_complete(stage_dir: Path) -> bool:
    if (stage_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(stage_dir)
    return all((stage_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _backtest_ready_closure_complete(backtest_dir: Path) -> bool:
    if (backtest_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(backtest_dir)
    return all((backtest_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _csf_backtest_ready_closure_complete(stage_dir: Path) -> bool:
    if (stage_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(stage_dir)
    return all((stage_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _holdout_validation_closure_complete(holdout_dir: Path) -> bool:
    if (holdout_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(holdout_dir)
    return all((holdout_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _csf_holdout_validation_closure_complete(stage_dir: Path) -> bool:
    if (stage_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(stage_dir)
    return all((stage_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _review_gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str]:
    stage_dir = _stage_dir_for_session_stage(lineage_root, current_stage)
    if stage_dir is None:
        return "REVIEW_PENDING", "Complete the review workflow."
    request_exists = (stage_dir / ADVERSARIAL_REVIEW_REQUEST_FILENAME).exists()
    review_result = _load_adversarial_review_result_if_present(stage_dir)
    if not request_exists or review_result is None:
        return (
            "ADVERSARIAL_REVIEW_PENDING",
            f"Produce {ADVERSARIAL_REVIEW_RESULT_FILENAME} via independent adversarial review.",
        )
    if review_result["review_loop_outcome"] == FIX_REQUIRED_OUTCOME:
        return (
            "AUTHOR_FIX_REQUIRED",
            "Fix adversarial review findings in the author lane, then resubmit for review.",
        )
    return (
        "REVIEW_CLOSURE_PENDING",
        "Run deterministic review closure after the adversarial reviewer outcome is closure-ready.",
    )


def _display_gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str]:
    stage_base = _stage_base_name(current_stage)
    if _supports_stage_display(stage_base):
        render_status = _stage_display_render_status(lineage_root, stage_base=stage_base)
        render_error = _stage_display_render_error(lineage_root, stage_base=stage_base)
        summary_status = _stage_display_summary_status(lineage_root, stage_base=stage_base)
        missing_inputs = _stage_display_missing_required_inputs(lineage_root, stage_base=stage_base)
        retry_state = _read_stage_display_retry_state(lineage_root, stage_base=stage_base) or {}
        attempt_count = int(retry_state.get("attempt_count", 0))
        html_path = _stage_display_html_path(lineage_root, stage_base=stage_base)
        if render_status == "complete" and summary_status == "complete":
            return (
                "DISPLAY_RENDER_COMPLETE",
                f"Display completed for {stage_base}. HTML: {html_path}. Run with --confirm-next-stage or reply CONFIRM_NEXT_STAGE <lineage_id> to continue.",
            )
        if render_status == "complete" and summary_status != "complete":
            missing_text = ", ".join(missing_inputs) if missing_inputs else "missing required display inputs"
            return (
                "DISPLAY_RENDER_FAILED",
                f"The {stage_base} display summary is incomplete ({missing_text}), so the mandatory display phase is blocked.",
            )
        if render_status == "failed":
            if attempt_count >= MANDATORY_DISPLAY_MAX_RETRIES:
                if render_error:
                    return (
                        "DISPLAY_RETRY_EXHAUSTED",
                        f"Mandatory display failed after {attempt_count}/{MANDATORY_DISPLAY_MAX_RETRIES} attempts for {stage_base}: {render_error}",
                    )
                return (
                    "DISPLAY_RETRY_EXHAUSTED",
                    f"Mandatory display failed after {attempt_count}/{MANDATORY_DISPLAY_MAX_RETRIES} attempts for {stage_base}.",
                )
            if render_error:
                return (
                    "DISPLAY_RETRYING",
                    f"Mandatory display retry {attempt_count + 1}/{MANDATORY_DISPLAY_MAX_RETRIES} will be prepared for {stage_base} after previous error: {render_error}",
                )
            return (
                "DISPLAY_RETRYING",
                f"Mandatory display retry {attempt_count + 1}/{MANDATORY_DISPLAY_MAX_RETRIES} will be prepared for {stage_base}.",
            )
        return (
            "DISPLAY_RENDER_PENDING",
            f"Mandatory display runtime render has not completed yet for {stage_base}.",
        )
    return (
        "DISPLAY_NOT_IMPLEMENTED",
        f"Mandatory display for {stage_base} is not implemented yet, so stage progression is blocked until display support exists.",
    )


def _next_stage_gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str]:
    stage_base = _stage_base_name(current_stage)
    next_stage_base = NEXT_STAGE_BY_BASE[stage_base]
    if _supports_stage_display(stage_base):
        render_status = _stage_display_render_status(lineage_root, stage_base=stage_base)
        render_error = _stage_display_render_error(lineage_root, stage_base=stage_base)
        summary_status = _stage_display_summary_status(lineage_root, stage_base=stage_base)
        missing_inputs = _stage_display_missing_required_inputs(lineage_root, stage_base=stage_base)
        html_path = _stage_display_html_path(lineage_root, stage_base=stage_base)
        if render_status != "complete" or summary_status != "complete":
            if render_status == "complete" and summary_status != "complete":
                missing_text = ", ".join(missing_inputs) if missing_inputs else "missing required display inputs"
                return (
                    "DISPLAY_RENDER_FAILED",
                    f"Fix the incomplete {stage_base} display summary ({missing_text}) before confirming the next stage.",
                )
            if render_error:
                return (
                    "DISPLAY_RENDER_FAILED",
                    f"Mandatory display for {stage_base} has not completed successfully ({render_error}).",
                )
            return (
                "DISPLAY_RENDER_PENDING",
                f"Mandatory display for {stage_base} must complete before next-stage confirmation.",
            )
    if stage_base not in DISPLAY_IMPLEMENTED_STAGE_BASES:
        return (
            "DISPLAY_NOT_IMPLEMENTED",
            f"Mandatory display for {stage_base} is not implemented yet, so next-stage confirmation is blocked.",
        )
    if next_stage_base is None:
        return (
            "NEXT_STAGE_CONFIRMATION_PENDING",
            "Run with --confirm-next-stage to mark the session complete.",
        )
    return (
        "NEXT_STAGE_CONFIRMATION_PENDING",
        f"Display completed. HTML: {html_path}. Run with --confirm-next-stage or reply CONFIRM_NEXT_STAGE <lineage_id> to enter {next_stage_base}.",
    )


def _gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str]:
    intake_gate = lineage_root / "00_idea_intake" / "idea_gate_decision.yaml"
    if current_stage == "idea_intake":
        if intake_gate.exists():
            gate_payload = _read_yaml(intake_gate)
            verdict = gate_payload.get("verdict", "")
            if verdict == "GO_TO_MANDATE":
                route_issue = _route_assessment_error(gate_payload)
                if route_issue is not None:
                    return "IN_PROGRESS", f"Complete route_assessment before mandate: {route_issue}"
                return "GO_TO_MANDATE_PENDING_CONFIRMATION", "Await explicit CONFIRM_MANDATE"
            if verdict == "DROP":
                return "DROP", "Reframe or terminate the idea"
        return (
            "IN_PROGRESS",
            "Finalize qualification artifacts only after intake interview approval",
        )

    if current_stage.endswith("_review_confirmation_pending"):
        return (
            "REVIEW_CONFIRMATION_PENDING",
            "Run with --confirm-review or reply CONFIRM_REVIEW <lineage_id>",
        )

    if current_stage.endswith("_display_pending"):
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage.endswith("_next_stage_confirmation_pending"):
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "idea_intake_confirmation_pending":
        decision = read_idea_intake_transition_decision(lineage_root)
        if decision == "HOLD":
            return "IDEA_INTAKE_ON_HOLD", "Wait for explicit CONFIRM_IDEA_INTAKE"
        return (
            "IDEA_INTAKE_PENDING_CONFIRMATION",
            "Run with --confirm-intake or reply CONFIRM_IDEA_INTAKE <lineage_id> after finishing the intake interview",
        )

    if current_stage == "mandate_confirmation_pending":
        next_group = next_mandate_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_MANDATE_PENDING_CONFIRMATION", f"Complete mandate freeze group: {next_group}"
        decision = read_mandate_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_MANDATE_ON_HOLD", "Wait for explicit CONFIRM_MANDATE"
        return "GO_TO_MANDATE_PENDING_CONFIRMATION", "Run with --confirm-mandate or reply CONFIRM_MANDATE <lineage_id>"

    if current_stage == "mandate_author":
        return "GO_TO_MANDATE_CONFIRMED", "Freeze mandate artifacts"

    if current_stage == "mandate_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "mandate_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "mandate_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_data_ready_confirmation_pending":
        next_group = next_csf_data_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_DATA_READY_PENDING_CONFIRMATION", f"Complete csf_data_ready freeze group: {next_group}"
        decision = read_data_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_DATA_READY_ON_HOLD", "Wait for explicit CONFIRM_DATA_READY"
        return "GO_TO_CSF_DATA_READY_PENDING_CONFIRMATION", "Run with --confirm-data-ready or reply CONFIRM_DATA_READY <lineage_id>"

    if current_stage == "csf_data_ready_author":
        return "GO_TO_CSF_DATA_READY_CONFIRMED", "Freeze csf_data_ready artifacts"

    if current_stage == "csf_data_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_data_ready_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_data_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "data_ready_confirmation_pending":
        next_group = next_data_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_DATA_READY_PENDING_CONFIRMATION", f"Complete data_ready freeze group: {next_group}"
        decision = read_data_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_DATA_READY_ON_HOLD", "Wait for explicit CONFIRM_DATA_READY"
        return "GO_TO_DATA_READY_PENDING_CONFIRMATION", "Run with --confirm-data-ready or reply CONFIRM_DATA_READY <lineage_id>"

    if current_stage == "data_ready_author":
        return "GO_TO_DATA_READY_CONFIRMED", "Freeze data_ready artifacts"

    if current_stage == "data_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "data_ready_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "data_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "signal_ready_confirmation_pending":
        next_group = next_signal_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_SIGNAL_READY_PENDING_CONFIRMATION", f"Complete signal_ready freeze group: {next_group}"
        decision = read_signal_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_SIGNAL_READY_ON_HOLD", "Wait for explicit CONFIRM_SIGNAL_READY"
        return "GO_TO_SIGNAL_READY_PENDING_CONFIRMATION", "Run with --confirm-signal-ready or reply CONFIRM_SIGNAL_READY <lineage_id>"

    if current_stage == "signal_ready_author":
        return "GO_TO_SIGNAL_READY_CONFIRMED", "Freeze signal_ready artifacts"

    if current_stage == "signal_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "signal_ready_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "signal_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_signal_ready_confirmation_pending":
        next_group = next_csf_signal_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_SIGNAL_READY_PENDING_CONFIRMATION", f"Complete csf_signal_ready freeze group: {next_group}"
        decision = read_signal_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_SIGNAL_READY_ON_HOLD", "Wait for explicit CONFIRM_SIGNAL_READY"
        return "GO_TO_CSF_SIGNAL_READY_PENDING_CONFIRMATION", "Run with --confirm-signal-ready or reply CONFIRM_SIGNAL_READY <lineage_id>"

    if current_stage == "csf_signal_ready_author":
        return "GO_TO_CSF_SIGNAL_READY_CONFIRMED", "Freeze csf_signal_ready artifacts"

    if current_stage == "csf_signal_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_signal_ready_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_signal_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "train_freeze_confirmation_pending":
        next_group = next_train_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_TRAIN_FREEZE_PENDING_CONFIRMATION", f"Complete train_freeze group: {next_group}"
        decision = read_train_freeze_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_TRAIN_FREEZE_ON_HOLD", "Wait for explicit CONFIRM_TRAIN_FREEZE"
        return "GO_TO_TRAIN_FREEZE_PENDING_CONFIRMATION", "Run with --confirm-train-freeze or reply CONFIRM_TRAIN_FREEZE <lineage_id>"

    if current_stage == "train_freeze_author":
        return "GO_TO_TRAIN_FREEZE_CONFIRMED", "Freeze train_freeze artifacts"

    if current_stage == "train_freeze_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "train_freeze_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "train_freeze_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_train_freeze_confirmation_pending":
        next_group = next_csf_train_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_TRAIN_FREEZE_PENDING_CONFIRMATION", f"Complete csf_train_freeze group: {next_group}"
        decision = read_train_freeze_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_TRAIN_FREEZE_ON_HOLD", "Wait for explicit CONFIRM_TRAIN_FREEZE"
        return "GO_TO_CSF_TRAIN_FREEZE_PENDING_CONFIRMATION", "Run with --confirm-train-freeze or reply CONFIRM_TRAIN_FREEZE <lineage_id>"

    if current_stage == "csf_train_freeze_author":
        return "GO_TO_CSF_TRAIN_FREEZE_CONFIRMED", "Freeze csf_train_freeze artifacts"

    if current_stage == "csf_train_freeze_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_train_freeze_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_train_freeze_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "test_evidence_confirmation_pending":
        next_group = next_test_evidence_group(lineage_root)
        if next_group is not None:
            return "GO_TO_TEST_EVIDENCE_PENDING_CONFIRMATION", f"Complete test_evidence group: {next_group}"
        decision = read_test_evidence_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_TEST_EVIDENCE_ON_HOLD", "Wait for explicit CONFIRM_TEST_EVIDENCE"
        return "GO_TO_TEST_EVIDENCE_PENDING_CONFIRMATION", "Run with --confirm-test-evidence or reply CONFIRM_TEST_EVIDENCE <lineage_id>"

    if current_stage == "test_evidence_author":
        return "GO_TO_TEST_EVIDENCE_CONFIRMED", "Freeze test_evidence artifacts"

    if current_stage == "test_evidence_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "test_evidence_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "test_evidence_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_test_evidence_confirmation_pending":
        next_group = next_csf_test_evidence_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_TEST_EVIDENCE_PENDING_CONFIRMATION", f"Complete csf_test_evidence group: {next_group}"
        decision = read_test_evidence_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_TEST_EVIDENCE_ON_HOLD", "Wait for explicit CONFIRM_TEST_EVIDENCE"
        return "GO_TO_CSF_TEST_EVIDENCE_PENDING_CONFIRMATION", "Run with --confirm-test-evidence or reply CONFIRM_TEST_EVIDENCE <lineage_id>"

    if current_stage == "csf_test_evidence_author":
        return "GO_TO_CSF_TEST_EVIDENCE_CONFIRMED", "Freeze csf_test_evidence artifacts"

    if current_stage == "csf_test_evidence_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_test_evidence_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_test_evidence_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "backtest_ready_confirmation_pending":
        next_group = next_backtest_ready_group(lineage_root)
        if next_group is not None:
            return "GO_TO_BACKTEST_READY_PENDING_CONFIRMATION", f"Complete backtest_ready group: {next_group}"
        decision = read_backtest_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_BACKTEST_READY_ON_HOLD", "Wait for explicit CONFIRM_BACKTEST_READY"
        return "GO_TO_BACKTEST_READY_PENDING_CONFIRMATION", "Run with --confirm-backtest-ready or reply CONFIRM_BACKTEST_READY <lineage_id>"

    if current_stage == "backtest_ready_author":
        return "GO_TO_BACKTEST_READY_CONFIRMED", "Freeze backtest_ready artifacts"

    if current_stage == "backtest_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "backtest_ready_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "backtest_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_backtest_ready_confirmation_pending":
        next_group = next_csf_backtest_ready_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_BACKTEST_READY_PENDING_CONFIRMATION", f"Complete csf_backtest_ready group: {next_group}"
        decision = read_backtest_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_BACKTEST_READY_ON_HOLD", "Wait for explicit CONFIRM_BACKTEST_READY"
        return "GO_TO_CSF_BACKTEST_READY_PENDING_CONFIRMATION", "Run with --confirm-backtest-ready or reply CONFIRM_BACKTEST_READY <lineage_id>"

    if current_stage == "csf_backtest_ready_author":
        return "GO_TO_CSF_BACKTEST_READY_CONFIRMED", "Freeze csf_backtest_ready artifacts"

    if current_stage == "csf_backtest_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_backtest_ready_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_backtest_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "holdout_validation_confirmation_pending":
        next_group = next_holdout_validation_group(lineage_root)
        if next_group is not None:
            return (
                "GO_TO_HOLDOUT_VALIDATION_PENDING_CONFIRMATION",
                f"Complete holdout_validation group: {next_group}",
            )
        decision = read_holdout_validation_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_HOLDOUT_VALIDATION_ON_HOLD", "Wait for explicit CONFIRM_HOLDOUT_VALIDATION"
        return (
            "GO_TO_HOLDOUT_VALIDATION_PENDING_CONFIRMATION",
            "Run with --confirm-holdout-validation or reply CONFIRM_HOLDOUT_VALIDATION <lineage_id>",
        )

    if current_stage == "holdout_validation_author":
        return "GO_TO_HOLDOUT_VALIDATION_CONFIRMED", "Freeze holdout_validation artifacts"

    if current_stage == "holdout_validation_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "holdout_validation_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_holdout_validation_confirmation_pending":
        next_group = next_csf_holdout_validation_group(lineage_root)
        if next_group is not None:
            return (
                "GO_TO_CSF_HOLDOUT_VALIDATION_PENDING_CONFIRMATION",
                f"Complete csf_holdout_validation group: {next_group}",
            )
        decision = read_holdout_validation_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_HOLDOUT_VALIDATION_ON_HOLD", "Wait for explicit CONFIRM_HOLDOUT_VALIDATION"
        return (
            "GO_TO_CSF_HOLDOUT_VALIDATION_PENDING_CONFIRMATION",
            "Run with --confirm-holdout-validation or reply CONFIRM_HOLDOUT_VALIDATION <lineage_id>",
        )

    if current_stage == "csf_holdout_validation_author":
        return "GO_TO_CSF_HOLDOUT_VALIDATION_CONFIRMED", "Freeze csf_holdout_validation artifacts"

    if current_stage == "csf_holdout_validation_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_holdout_validation_display_pending":
        return _display_gate_status_and_next_action(lineage_root, current_stage)

    return "REVIEW_COMPLETE", "Stop here until promotion_decision orchestration exists"


def _route_assessment_error(gate_decision: dict) -> str | None:
    try:
        _require_route_assessment(gate_decision)
    except ValueError as exc:
        return str(exc)
    return None


def _read_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    return {}


def _optional_payload_value(value: object) -> str | None:
    normalized = str(value).strip()
    return normalized or None


def _is_csf_route(lineage_root: Path) -> bool:
    return current_research_route(lineage_root) == "cross_sectional_factor"


def _idea_intake_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "00_idea_intake" / IDEA_INTAKE_TRANSITION_APPROVAL_FILE


def _approval_path(lineage_root: Path) -> Path:
    return lineage_root / "00_idea_intake" / MANDATE_TRANSITION_APPROVAL_FILE


def _data_ready_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "02_csf_data_ready" / DATA_READY_TRANSITION_APPROVAL_FILE
    return lineage_root / "02_data_ready" / DATA_READY_TRANSITION_APPROVAL_FILE


def _signal_ready_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "03_csf_signal_ready" / SIGNAL_READY_TRANSITION_APPROVAL_FILE
    return lineage_root / "03_signal_ready" / SIGNAL_READY_TRANSITION_APPROVAL_FILE


def _train_freeze_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "04_csf_train_freeze" / TRAIN_FREEZE_TRANSITION_APPROVAL_FILE
    return lineage_root / "04_train_freeze" / TRAIN_FREEZE_TRANSITION_APPROVAL_FILE


def _test_evidence_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "05_csf_test_evidence" / TEST_EVIDENCE_TRANSITION_APPROVAL_FILE
    return lineage_root / "05_test_evidence" / TEST_EVIDENCE_TRANSITION_APPROVAL_FILE


def _backtest_ready_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "06_csf_backtest_ready" / BACKTEST_READY_TRANSITION_APPROVAL_FILE
    return lineage_root / "06_backtest" / BACKTEST_READY_TRANSITION_APPROVAL_FILE


def _holdout_validation_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "07_csf_holdout_validation" / HOLDOUT_VALIDATION_TRANSITION_APPROVAL_FILE
    return lineage_root / "07_holdout" / HOLDOUT_VALIDATION_TRANSITION_APPROVAL_FILE


def _stage_dir_for_stage_base(lineage_root: Path, stage_base: str) -> Path | None:
    spec = SESSION_STAGE_PROGRAM_SPECS.get(stage_base)
    if spec is None:
        return None
    return lineage_root / spec.stage_dir_name


def _review_transition_approval_path(lineage_root: Path, stage_base: str) -> Path | None:
    stage_dir = _stage_dir_for_stage_base(lineage_root, stage_base)
    if stage_dir is None:
        return None
    return stage_dir / REVIEW_TRANSITION_APPROVAL_FILE


def _next_stage_transition_approval_path(lineage_root: Path, stage_base: str) -> Path | None:
    stage_dir = _stage_dir_for_stage_base(lineage_root, stage_base)
    if stage_dir is None:
        return None
    return stage_dir / NEXT_STAGE_TRANSITION_APPROVAL_FILE
