from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml

from runtime.tools.lineage_lock_ledger import (
    FROZEN_ARTIFACT_MUTATED,
    FrozenArtifactMutationError,
    assert_lineage_locks_intact,
)
from runtime.tools.data_ready_runtime import (
    DATA_READY_FREEZE_DRAFT_FILE,
    DATA_READY_FREEZE_GROUP_ORDER,
    scaffold_data_ready,
)
from runtime.tools.csf_backtest_runtime import (
    CSF_BACKTEST_READY_DRAFT_FILE,
    CSF_BACKTEST_READY_GROUP_ORDER,
    scaffold_csf_backtest_ready,
)
from runtime.tools.csf_data_ready_runtime import (
    CSF_DATA_READY_FREEZE_DRAFT_FILE,
    CSF_DATA_READY_FREEZE_GROUP_ORDER,
    scaffold_csf_data_ready,
)
from runtime.tools.csf_holdout_runtime import (
    CSF_HOLDOUT_VALIDATION_DRAFT_FILE,
    CSF_HOLDOUT_VALIDATION_GROUP_ORDER,
    scaffold_csf_holdout_validation,
)
from runtime.tools.csf_signal_ready_runtime import (
    CSF_SIGNAL_READY_FREEZE_DRAFT_FILE,
    CSF_SIGNAL_READY_FREEZE_GROUP_ORDER,
    scaffold_csf_signal_ready,
)
from runtime.tools.csf_test_evidence_runtime import (
    CSF_TEST_EVIDENCE_DRAFT_FILE,
    CSF_TEST_EVIDENCE_GROUP_ORDER,
    scaffold_csf_test_evidence,
)
from runtime.tools.csf_train_runtime import (
    CSF_TRAIN_FREEZE_DRAFT_FILE,
    CSF_TRAIN_FREEZE_GROUP_ORDER,
    scaffold_csf_train_freeze,
)

try:
    from runtime.tools.tss_data_ready_runtime import (
        TSS_DATA_READY_FREEZE_DRAFT_FILE,
        TSS_DATA_READY_FREEZE_GROUP_ORDER,
        scaffold_tss_data_ready,
    )
except ModuleNotFoundError:
    TSS_DATA_READY_FREEZE_DRAFT_FILE = "tss_data_ready_freeze_draft.yaml"
    TSS_DATA_READY_FREEZE_GROUP_ORDER = ("time_index_contract",)

    def scaffold_tss_data_ready(lineage_root: Path) -> Path:
        return _scaffold_tss_stage(
            lineage_root,
            stage_dir_name="02_tss_data_ready",
            draft_file=TSS_DATA_READY_FREEZE_DRAFT_FILE,
            group_order=TSS_DATA_READY_FREEZE_GROUP_ORDER,
        )


try:
    from runtime.tools.tss_signal_ready_runtime import (
        TSS_SIGNAL_READY_FREEZE_DRAFT_FILE,
        TSS_SIGNAL_READY_FREEZE_GROUP_ORDER,
        scaffold_tss_signal_ready,
    )
except ModuleNotFoundError:
    TSS_SIGNAL_READY_FREEZE_DRAFT_FILE = "tss_signal_ready_freeze_draft.yaml"
    TSS_SIGNAL_READY_FREEZE_GROUP_ORDER = ("signal_contract",)

    def scaffold_tss_signal_ready(lineage_root: Path) -> Path:
        return _scaffold_tss_stage(
            lineage_root,
            stage_dir_name="03_tss_signal_ready",
            draft_file=TSS_SIGNAL_READY_FREEZE_DRAFT_FILE,
            group_order=TSS_SIGNAL_READY_FREEZE_GROUP_ORDER,
        )


try:
    from runtime.tools.tss_train_runtime import (
        TSS_TRAIN_FREEZE_DRAFT_FILE,
        TSS_TRAIN_FREEZE_GROUP_ORDER,
        scaffold_tss_train_freeze,
    )
except ModuleNotFoundError:
    TSS_TRAIN_FREEZE_DRAFT_FILE = "tss_train_freeze_draft.yaml"
    TSS_TRAIN_FREEZE_GROUP_ORDER = ("train_freeze_contract",)

    def scaffold_tss_train_freeze(lineage_root: Path) -> Path:
        return _scaffold_tss_stage(
            lineage_root,
            stage_dir_name="04_tss_train_freeze",
            draft_file=TSS_TRAIN_FREEZE_DRAFT_FILE,
            group_order=TSS_TRAIN_FREEZE_GROUP_ORDER,
        )


try:
    from runtime.tools.tss_test_evidence_runtime import (
        TSS_TEST_EVIDENCE_DRAFT_FILE,
        TSS_TEST_EVIDENCE_GROUP_ORDER,
        scaffold_tss_test_evidence,
    )
except ModuleNotFoundError:
    TSS_TEST_EVIDENCE_DRAFT_FILE = "tss_test_evidence_freeze_draft.yaml"
    TSS_TEST_EVIDENCE_GROUP_ORDER = ("test_evidence_contract",)

    def scaffold_tss_test_evidence(lineage_root: Path) -> Path:
        return _scaffold_tss_stage(
            lineage_root,
            stage_dir_name="05_tss_test_evidence",
            draft_file=TSS_TEST_EVIDENCE_DRAFT_FILE,
            group_order=TSS_TEST_EVIDENCE_GROUP_ORDER,
        )


try:
    from runtime.tools.tss_backtest_runtime import (
        TSS_BACKTEST_READY_DRAFT_FILE,
        TSS_BACKTEST_READY_GROUP_ORDER,
        scaffold_tss_backtest_ready,
    )
except ModuleNotFoundError:
    TSS_BACKTEST_READY_DRAFT_FILE = "tss_backtest_ready_freeze_draft.yaml"
    TSS_BACKTEST_READY_GROUP_ORDER = ("backtest_contract",)

    def scaffold_tss_backtest_ready(lineage_root: Path) -> Path:
        return _scaffold_tss_stage(
            lineage_root,
            stage_dir_name="06_tss_backtest_ready",
            draft_file=TSS_BACKTEST_READY_DRAFT_FILE,
            group_order=TSS_BACKTEST_READY_GROUP_ORDER,
        )


try:
    from runtime.tools.tss_holdout_runtime import (
        TSS_HOLDOUT_VALIDATION_DRAFT_FILE,
        TSS_HOLDOUT_VALIDATION_GROUP_ORDER,
        scaffold_tss_holdout_validation,
    )
except ModuleNotFoundError:
    TSS_HOLDOUT_VALIDATION_DRAFT_FILE = "tss_holdout_validation_freeze_draft.yaml"
    TSS_HOLDOUT_VALIDATION_GROUP_ORDER = ("holdout_contract",)

    def scaffold_tss_holdout_validation(lineage_root: Path) -> Path:
        return _scaffold_tss_stage(
            lineage_root,
            stage_dir_name="07_tss_holdout_validation",
            draft_file=TSS_HOLDOUT_VALIDATION_DRAFT_FILE,
            group_order=TSS_HOLDOUT_VALIDATION_GROUP_ORDER,
        )

from runtime.tools.idea_runtime import (
    MANDATE_FREEZE_DRAFT_FILE,
    MANDATE_FREEZE_GROUP_ORDER,
    SUPPORTED_RESEARCH_ROUTES,
    _require_route_assessment,
    scaffold_idea_intake,
)
from runtime.tools.freeze_contract_runtime import (
    confirm_all_freeze_groups,
    first_unconfirmed_or_invalid_group,
    freeze_group_invalid_reason,
    validate_confirmed_freeze_groups,
)
from runtime.tools.lineage_program_runtime import (
    StageProgramRuntimeError,
    StageProgramSpec,
    inspect_stage_program,
    invoke_stage_if_admitted,
    load_provenance_manifest,
    stage_outputs_complete,
)
from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    FIX_REQUIRED_OUTCOME,
    REVIEWER_RECEIPT_FILENAME,
    ensure_adversarial_review_request,
    load_adversarial_review_request,
    load_adversarial_review_result,
    load_reviewer_receipt,
    validate_receipt_contract,
    validate_result_contract,
)
from runtime.tools.review_skillgen.review_engine import run_stage_review
from runtime.tools.review_skillgen.review_freshness import review_cycle_stale_reason
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from runtime.tools.review_skillgen.protected_state_guard import (
    PROTECTED_STATE_DRIFT,
    ProtectedStateError,
    assert_protected_review_state_intact,
)
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest,
    load_review_runtime_state,
    review_runtime_state_path,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    REVIEWER_WRITE_SCOPE_AUDIT_FILENAME,
    load_reviewer_write_scope_audit,
    validate_reviewer_write_scope_audit,
)
from runtime.tools.signal_ready_runtime import (
    SIGNAL_READY_FREEZE_DRAFT_FILE,
    SIGNAL_READY_FREEZE_GROUP_ORDER,
    scaffold_signal_ready,
)
from runtime.tools.backtest_runtime import (
    BACKTEST_READY_DRAFT_FILE,
    BACKTEST_READY_GROUP_ORDER,
    backtest_ready_real_outputs_complete,
    scaffold_backtest_ready,
)
from runtime.tools.holdout_runtime import (
    HOLDOUT_VALIDATION_DRAFT_FILE,
    HOLDOUT_VALIDATION_GROUP_ORDER,
    scaffold_holdout_validation,
)
from runtime.tools.test_evidence_runtime import (
    TEST_EVIDENCE_DRAFT_FILE,
    TEST_EVIDENCE_GROUP_ORDER,
    scaffold_test_evidence,
)
from runtime.tools.train_runtime import (
    TRAIN_FREEZE_DRAFT_FILE,
    TRAIN_FREEZE_GROUP_ORDER,
    scaffold_train_freeze,
)
from runtime.tools.review_skillgen.context_inference import build_stage_context


SessionStage = Literal[
    "idea_intake",
    "idea_intake_confirmation_pending",
    "mandate_next_stage_confirmation_pending",
    "mandate_confirmation_pending",
    "mandate_author",
    "mandate_review_confirmation_pending",
    "mandate_review",
    "mandate_next_stage_confirmation_pending",
    "csf_data_ready_confirmation_pending",
    "csf_data_ready_author",
    "csf_data_ready_review_confirmation_pending",
    "csf_data_ready_review",
    "csf_data_ready_next_stage_confirmation_pending",
    "csf_signal_ready_confirmation_pending",
    "csf_signal_ready_author",
    "csf_signal_ready_review_confirmation_pending",
    "csf_signal_ready_review",
    "csf_signal_ready_next_stage_confirmation_pending",
    "csf_train_freeze_confirmation_pending",
    "csf_train_freeze_author",
    "csf_train_freeze_review_confirmation_pending",
    "csf_train_freeze_review",
    "csf_train_freeze_next_stage_confirmation_pending",
    "csf_test_evidence_confirmation_pending",
    "csf_test_evidence_author",
    "csf_test_evidence_review_confirmation_pending",
    "csf_test_evidence_review",
    "csf_test_evidence_next_stage_confirmation_pending",
    "csf_backtest_ready_confirmation_pending",
    "csf_backtest_ready_author",
    "csf_backtest_ready_review_confirmation_pending",
    "csf_backtest_ready_review",
    "csf_backtest_ready_next_stage_confirmation_pending",
    "csf_holdout_validation_confirmation_pending",
    "csf_holdout_validation_author",
    "csf_holdout_validation_review_confirmation_pending",
    "csf_holdout_validation_review",
    "csf_holdout_validation_next_stage_confirmation_pending",
    "csf_holdout_validation_review_complete",
    "tss_data_ready_confirmation_pending",
    "tss_data_ready_author",
    "tss_data_ready_review_confirmation_pending",
    "tss_data_ready_review",
    "tss_data_ready_next_stage_confirmation_pending",
    "tss_signal_ready_confirmation_pending",
    "tss_signal_ready_author",
    "tss_signal_ready_review_confirmation_pending",
    "tss_signal_ready_review",
    "tss_signal_ready_next_stage_confirmation_pending",
    "tss_train_freeze_confirmation_pending",
    "tss_train_freeze_author",
    "tss_train_freeze_review_confirmation_pending",
    "tss_train_freeze_review",
    "tss_train_freeze_next_stage_confirmation_pending",
    "tss_test_evidence_confirmation_pending",
    "tss_test_evidence_author",
    "tss_test_evidence_review_confirmation_pending",
    "tss_test_evidence_review",
    "tss_test_evidence_next_stage_confirmation_pending",
    "tss_backtest_ready_confirmation_pending",
    "tss_backtest_ready_author",
    "tss_backtest_ready_review_confirmation_pending",
    "tss_backtest_ready_review",
    "tss_backtest_ready_next_stage_confirmation_pending",
    "tss_holdout_validation_confirmation_pending",
    "tss_holdout_validation_author",
    "tss_holdout_validation_review_confirmation_pending",
    "tss_holdout_validation_review",
    "tss_holdout_validation_next_stage_confirmation_pending",
    "tss_holdout_validation_review_complete",
    "data_ready_next_stage_confirmation_pending",
    "data_ready_confirmation_pending",
    "data_ready_author",
    "data_ready_review_confirmation_pending",
    "data_ready_review",
    "data_ready_next_stage_confirmation_pending",
    "signal_ready_confirmation_pending",
    "signal_ready_author",
    "signal_ready_review_confirmation_pending",
    "signal_ready_review",
    "signal_ready_next_stage_confirmation_pending",
    "train_freeze_confirmation_pending",
    "train_freeze_author",
    "train_freeze_review_confirmation_pending",
    "train_freeze_review",
    "train_freeze_next_stage_confirmation_pending",
    "test_evidence_confirmation_pending",
    "test_evidence_author",
    "test_evidence_review_confirmation_pending",
    "test_evidence_review",
    "test_evidence_next_stage_confirmation_pending",
    "backtest_ready_confirmation_pending",
    "backtest_ready_author",
    "backtest_ready_review_confirmation_pending",
    "backtest_ready_review",
    "backtest_ready_next_stage_confirmation_pending",
    "holdout_validation_confirmation_pending",
    "holdout_validation_author",
    "holdout_validation_review_confirmation_pending",
    "holdout_validation_review",
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
    "split_sample_adequacy_report.yaml",
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
    "route_inheritance_contract.yaml",
    "factor_contract.md",
    "factor_field_dictionary.md",
    "csf_signal_ready_gate_decision.md",
    "run_manifest.json",
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
    "csf_train_freeze_gate_decision.md",
    "run_manifest.json",
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
    "csf_test_gate_decision.md",
    "run_manifest.json",
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
    "csf_backtest_gate_decision.md",
    "run_manifest.json",
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


def _stage_context(stage_dir: Path) -> dict[str, Path]:
    return build_stage_context(stage_dir)


def _author_formal_dir(stage_dir: Path) -> Path:
    return _stage_context(stage_dir)["author_formal_dir"]


def _author_draft_dir(stage_dir: Path) -> Path:
    return _stage_context(stage_dir)["author_draft_dir"]


def _review_request_path(stage_dir: Path) -> Path:
    return _stage_context(stage_dir)["review_request_dir"] / ADVERSARIAL_REVIEW_REQUEST_FILENAME


def _review_receipt_path(stage_dir: Path) -> Path:
    return _stage_context(stage_dir)["review_request_dir"] / REVIEWER_RECEIPT_FILENAME


def _review_result_path(stage_dir: Path) -> Path:
    return _stage_context(stage_dir)["review_result_dir"] / ADVERSARIAL_REVIEW_RESULT_FILENAME


def _review_audit_path(stage_dir: Path) -> Path:
    return _stage_context(stage_dir)["review_result_dir"] / REVIEWER_WRITE_SCOPE_AUDIT_FILENAME


def _review_findings_path(stage_dir: Path) -> Path:
    return _stage_context(stage_dir)["review_result_dir"] / "review_findings.yaml"


def _review_closure_path(stage_dir: Path, name: str) -> Path:
    return _stage_context(stage_dir)["review_closure_dir"] / name
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
TSS_DATA_READY_REQUIRED_OUTPUTS = [
    "time_index_manifest.json",
    "asset_time_index.parquet",
    "quality_flags.parquet",
    "split_sample_adequacy_report.yaml",
    "run_manifest.json",
    "rebuild_tss_data_ready.py",
    "artifact_catalog.md",
    "field_dictionary.md",
]
TSS_SIGNAL_READY_REQUIRED_OUTPUTS = [
    "signal_manifest.yaml",
    "param_manifest.csv",
    "signal_panel.parquet",
    "signal_event_panel.parquet",
    "route_inheritance_contract.yaml",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
]
TSS_TRAIN_FREEZE_REQUIRED_OUTPUTS = [
    "tss_train_freeze.yaml",
    "train_threshold_ledger.csv",
    "train_variant_ledger.csv",
    "train_variant_rejects.csv",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
]
TSS_TEST_EVIDENCE_REQUIRED_OUTPUTS = [
    "event_forward_return.parquet",
    "signal_performance_summary.json",
    "tss_test_gate_table.csv",
    "tss_selected_variants_test.csv",
    "split_threshold_attestation.yaml",
    "selected_variant_membership_proof.csv",
    "upstream_binding_digest_ledger.yaml",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
]
TSS_BACKTEST_READY_REQUIRED_OUTPUTS = [
    "strategy_contract.yaml",
    "engine_compare.csv",
    "position_timeseries.parquet",
    "trade_ledger.csv",
    "tss_backtest_gate_table.csv",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
]
TSS_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS = [
    "tss_holdout_run_manifest.json",
    "holdout_signal_diagnostics.parquet",
    "holdout_event_compare.parquet",
    "holdout_backtest_compare.parquet",
    "artifact_catalog.md",
    "field_dictionary.md",
]
ADVANCING_COMPLETION_STATUSES = {"PASS", "CONDITIONAL PASS", "GO"}
NON_ADVANCING_COMPLETION_STATUSES = {"PASS FOR RETRY", "RETRY", "NO-GO", "CHILD LINEAGE"}
SESSION_STAGE_RUNTIME_SUFFIXES = (
    "_next_stage_confirmation_pending",
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


def _scaffold_tss_stage(
    lineage_root: Path,
    *,
    stage_dir_name: str,
    draft_file: str,
    group_order: tuple[str, ...],
) -> Path:
    stage_dir = lineage_root / stage_dir_name
    draft_dir = stage_dir / "author" / "draft"
    (stage_dir / "author" / "formal").mkdir(parents=True, exist_ok=True)
    (stage_dir / "review" / "request").mkdir(parents=True, exist_ok=True)
    (stage_dir / "review" / "result").mkdir(parents=True, exist_ok=True)
    (stage_dir / "review" / "closure").mkdir(parents=True, exist_ok=True)
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_path = draft_dir / draft_file
    if not draft_path.exists():
        # TSS runtime 模块未接入前，只落盘最小 freeze draft 骨架，不伪造正式产物。
        draft_path.write_text(
            yaml.safe_dump(
                {
                    "stage": stage_dir_name[3:],
                    "groups": {
                        name: {"confirmed": False, "draft": {}, "missing_items": []}
                        for name in group_order
                    },
                },
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
    return stage_dir


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
    review_state: str | None = None
    active_review_cycle_id: str | None = None
    review_requested_at: str | None = None
    review_bound_author_digest: str | None = None
    closure_written_at: str | None = None
    requires_failure_handling: bool = False
    failure_stage: str | None = None
    failure_reason_summary: str | None = None
    freeze_groups: list[dict[str, object]] | None = None


@dataclass(frozen=True)
class FailurePackageRuntimeStatus:
    stage_status: str
    blocking_reason_code: str
    gate_status: str
    current_skill: str
    why_this_skill: str
    blocking_reason: str
    next_action: str
    resume_hint: str
    review_verdict: str
    failure_stage: str
    failure_reason_summary: str


def _lineage_lock_blocked_status(
    *,
    lineage_root: Path,
    lineage_mode: str | None,
    lineage_selection_reason: str | None,
    violation: FrozenArtifactMutationError,
) -> SessionContext:
    current_stage = detect_session_stage(lineage_root)
    route_contract = current_route_contract(lineage_root)
    return SessionContext(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        lineage_mode=lineage_mode,
        lineage_selection_reason=lineage_selection_reason,
        current_orchestrator="qros-research-session",
        current_stage=current_stage,
        current_route=current_research_route(lineage_root),
        stage_status="blocked",
        blocking_reason_code=FROZEN_ARTIFACT_MUTATED,
        current_skill="qros-research-session",
        why_this_skill="Lineage immutable ledger blocked normal QROS workflow before stage execution.",
        required_program_dir=None,
        required_program_entrypoint=None,
        program_contract_status="not_checked",
        provenance_status="not_checked",
        blocking_reason=str(violation),
        resume_hint=violation.next_action,
        artifacts_written=[],
        gate_status=FROZEN_ARTIFACT_MUTATED,
        next_action=violation.next_action,
        why_now=[],
        open_risks=[],
        factor_role=route_contract["factor_role"],
        factor_structure=route_contract["factor_structure"],
        portfolio_expression=route_contract["portfolio_expression"],
        neutralization_policy=route_contract["neutralization_policy"],
        review_verdict=None,
        review_state=None,
        active_review_cycle_id=None,
        review_requested_at=None,
        review_bound_author_digest=None,
        closure_written_at=None,
        requires_failure_handling=False,
        failure_stage=None,
        failure_reason_summary=None,
        freeze_groups=None,
    )


def assert_current_protected_review_state_intact(
    *,
    lineage_root: Path,
    current_stage: SessionStage,
) -> None:
    spec = _program_spec_for_session_stage(current_stage)
    if spec is None or _stage_base_name(current_stage) not in REVIEWABLE_STAGE_BASES:
        return
    stage_dir = lineage_root / spec.stage_dir_name
    required_outputs = spec.required_outputs
    required_provenance_paths: tuple[str, ...] | list[str] = ("program_execution_manifest.json",)
    request_path = _review_request_path(stage_dir)
    if request_path.exists():
        try:
            request_payload = load_adversarial_review_request(request_path)
            required_outputs = request_payload["required_artifact_paths"]
            required_provenance_paths = request_payload["required_provenance_paths"]
        except Exception:
            # request 结构错误由 review runtime 状态机报告；protected guard 只负责校验可解析 cycle 的绑定。
            pass
    assert_protected_review_state_intact(
        stage_dir=stage_dir,
        lineage_root=lineage_root,
        required_outputs=required_outputs,
        required_provenance_paths=required_provenance_paths,
        allow_missing_state=True,
    )


def _protected_state_blocked_status(
    *,
    lineage_root: Path,
    lineage_mode: str | None,
    lineage_selection_reason: str | None,
    violation: ProtectedStateError,
) -> SessionContext:
    current_stage = detect_session_stage(lineage_root)
    route_contract = current_route_contract(lineage_root)
    return SessionContext(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        lineage_mode=lineage_mode,
        lineage_selection_reason=lineage_selection_reason,
        current_orchestrator="qros-research-session",
        current_stage=current_stage,
        current_route=current_research_route(lineage_root),
        stage_status="blocked",
        blocking_reason_code=violation.reason_code,
        current_skill="qros-research-session",
        why_this_skill="Protected review state drift blocked normal QROS workflow before stage execution.",
        required_program_dir=None,
        required_program_entrypoint=None,
        program_contract_status="not_checked",
        provenance_status="not_checked",
        blocking_reason=str(violation),
        resume_hint=violation.next_action,
        artifacts_written=[],
        gate_status=PROTECTED_STATE_DRIFT,
        next_action=violation.next_action,
        why_now=["Protected review state drift must be repaired before normal QROS workflow can continue."],
        open_risks=[str(violation)],
        factor_role=route_contract["factor_role"],
        factor_structure=route_contract["factor_structure"],
        portfolio_expression=route_contract["portfolio_expression"],
        neutralization_policy=route_contract["neutralization_policy"],
        review_verdict=None,
        review_state=None,
        active_review_cycle_id=None,
        review_requested_at=None,
        review_bound_author_digest=None,
        closure_written_at=None,
        requires_failure_handling=False,
        failure_stage=None,
        failure_reason_summary=None,
        freeze_groups=None,
    )


STAGE_ACTIVE_SKILLS: dict[SessionStage, str] = {
    "idea_intake": "qros-idea-intake-author",
    "idea_intake_confirmation_pending": "qros-idea-intake-author",
    "mandate_next_stage_confirmation_pending": "qros-research-session",
    "mandate_confirmation_pending": "qros-mandate-author",
    "mandate_author": "qros-mandate-author",
    "mandate_review_confirmation_pending": "qros-mandate-review",
    "mandate_review": "qros-mandate-review",
    "mandate_next_stage_confirmation_pending": "qros-research-session",
    "csf_data_ready_confirmation_pending": "qros-csf-data-ready-author",
    "csf_data_ready_author": "qros-csf-data-ready-author",
    "csf_data_ready_review_confirmation_pending": "qros-csf-data-ready-review",
    "csf_data_ready_review": "qros-csf-data-ready-review",
    "csf_data_ready_next_stage_confirmation_pending": "qros-research-session",
    "csf_signal_ready_confirmation_pending": "qros-csf-signal-ready-author",
    "csf_signal_ready_author": "qros-csf-signal-ready-author",
    "csf_signal_ready_review_confirmation_pending": "qros-csf-signal-ready-review",
    "csf_signal_ready_review": "qros-csf-signal-ready-review",
    "csf_signal_ready_next_stage_confirmation_pending": "qros-research-session",
    "csf_train_freeze_confirmation_pending": "qros-csf-train-freeze-author",
    "csf_train_freeze_author": "qros-csf-train-freeze-author",
    "csf_train_freeze_review_confirmation_pending": "qros-csf-train-freeze-review",
    "csf_train_freeze_review": "qros-csf-train-freeze-review",
    "csf_train_freeze_next_stage_confirmation_pending": "qros-research-session",
    "csf_test_evidence_confirmation_pending": "qros-csf-test-evidence-author",
    "csf_test_evidence_author": "qros-csf-test-evidence-author",
    "csf_test_evidence_review_confirmation_pending": "qros-csf-test-evidence-review",
    "csf_test_evidence_review": "qros-csf-test-evidence-review",
    "csf_test_evidence_next_stage_confirmation_pending": "qros-research-session",
    "csf_backtest_ready_confirmation_pending": "qros-csf-backtest-ready-author",
    "csf_backtest_ready_author": "qros-csf-backtest-ready-author",
    "csf_backtest_ready_review_confirmation_pending": "qros-csf-backtest-ready-review",
    "csf_backtest_ready_review": "qros-csf-backtest-ready-review",
    "csf_backtest_ready_next_stage_confirmation_pending": "qros-research-session",
    "csf_holdout_validation_confirmation_pending": "qros-csf-holdout-validation-author",
    "csf_holdout_validation_author": "qros-csf-holdout-validation-author",
    "csf_holdout_validation_review_confirmation_pending": "qros-csf-holdout-validation-review",
    "csf_holdout_validation_review": "qros-csf-holdout-validation-review",
    "csf_holdout_validation_next_stage_confirmation_pending": "qros-research-session",
    "csf_holdout_validation_review_complete": "qros-research-session",
    "tss_data_ready_confirmation_pending": "qros-tss-data-ready-author",
    "tss_data_ready_author": "qros-tss-data-ready-author",
    "tss_data_ready_review_confirmation_pending": "qros-tss-data-ready-review",
    "tss_data_ready_review": "qros-tss-data-ready-review",
    "tss_data_ready_next_stage_confirmation_pending": "qros-research-session",
    "tss_signal_ready_confirmation_pending": "qros-tss-signal-ready-author",
    "tss_signal_ready_author": "qros-tss-signal-ready-author",
    "tss_signal_ready_review_confirmation_pending": "qros-tss-signal-ready-review",
    "tss_signal_ready_review": "qros-tss-signal-ready-review",
    "tss_signal_ready_next_stage_confirmation_pending": "qros-research-session",
    "tss_train_freeze_confirmation_pending": "qros-tss-train-freeze-author",
    "tss_train_freeze_author": "qros-tss-train-freeze-author",
    "tss_train_freeze_review_confirmation_pending": "qros-tss-train-freeze-review",
    "tss_train_freeze_review": "qros-tss-train-freeze-review",
    "tss_train_freeze_next_stage_confirmation_pending": "qros-research-session",
    "tss_test_evidence_confirmation_pending": "qros-tss-test-evidence-author",
    "tss_test_evidence_author": "qros-tss-test-evidence-author",
    "tss_test_evidence_review_confirmation_pending": "qros-tss-test-evidence-review",
    "tss_test_evidence_review": "qros-tss-test-evidence-review",
    "tss_test_evidence_next_stage_confirmation_pending": "qros-research-session",
    "tss_backtest_ready_confirmation_pending": "qros-tss-backtest-ready-author",
    "tss_backtest_ready_author": "qros-tss-backtest-ready-author",
    "tss_backtest_ready_review_confirmation_pending": "qros-tss-backtest-ready-review",
    "tss_backtest_ready_review": "qros-tss-backtest-ready-review",
    "tss_backtest_ready_next_stage_confirmation_pending": "qros-research-session",
    "tss_holdout_validation_confirmation_pending": "qros-tss-holdout-validation-author",
    "tss_holdout_validation_author": "qros-tss-holdout-validation-author",
    "tss_holdout_validation_review_confirmation_pending": "qros-tss-holdout-validation-review",
    "tss_holdout_validation_review": "qros-tss-holdout-validation-review",
    "tss_holdout_validation_next_stage_confirmation_pending": "qros-research-session",
    "tss_holdout_validation_review_complete": "qros-research-session",
    "data_ready_next_stage_confirmation_pending": "qros-research-session",
    "data_ready_confirmation_pending": "qros-data-ready-author",
    "data_ready_author": "qros-data-ready-author",
    "data_ready_review_confirmation_pending": "qros-data-ready-review",
    "data_ready_review": "qros-data-ready-review",
    "data_ready_next_stage_confirmation_pending": "qros-research-session",
    "signal_ready_confirmation_pending": "qros-signal-ready-author",
    "signal_ready_author": "qros-signal-ready-author",
    "signal_ready_review_confirmation_pending": "qros-signal-ready-review",
    "signal_ready_review": "qros-signal-ready-review",
    "signal_ready_next_stage_confirmation_pending": "qros-research-session",
    "train_freeze_confirmation_pending": "qros-train-freeze-author",
    "train_freeze_author": "qros-train-freeze-author",
    "train_freeze_review_confirmation_pending": "qros-train-freeze-review",
    "train_freeze_review": "qros-train-freeze-review",
    "train_freeze_next_stage_confirmation_pending": "qros-research-session",
    "test_evidence_confirmation_pending": "qros-test-evidence-author",
    "test_evidence_author": "qros-test-evidence-author",
    "test_evidence_review_confirmation_pending": "qros-test-evidence-review",
    "test_evidence_review": "qros-test-evidence-review",
    "test_evidence_next_stage_confirmation_pending": "qros-research-session",
    "backtest_ready_confirmation_pending": "qros-backtest-ready-author",
    "backtest_ready_author": "qros-backtest-ready-author",
    "backtest_ready_review_confirmation_pending": "qros-backtest-ready-review",
    "backtest_ready_review": "qros-backtest-ready-review",
    "backtest_ready_next_stage_confirmation_pending": "qros-research-session",
    "holdout_validation_confirmation_pending": "qros-holdout-validation-author",
    "holdout_validation_author": "qros-holdout-validation-author",
    "holdout_validation_review_confirmation_pending": "qros-holdout-validation-review",
    "holdout_validation_review": "qros-holdout-validation-review",
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
        stage_id="csf_data_ready",
        route="cross_sectional_factor",
        stage_dir_name="02_csf_data_ready",
        required_outputs=tuple(CSF_DATA_READY_REQUIRED_OUTPUTS),
    ),
    "csf_signal_ready": StageProgramSpec(
        stage_id="csf_signal_ready",
        route="cross_sectional_factor",
        stage_dir_name="03_csf_signal_ready",
        required_outputs=tuple(CSF_SIGNAL_READY_REQUIRED_OUTPUTS),
    ),
    "csf_train_freeze": StageProgramSpec(
        stage_id="csf_train_freeze",
        route="cross_sectional_factor",
        stage_dir_name="04_csf_train_freeze",
        required_outputs=tuple(CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS),
    ),
    "csf_test_evidence": StageProgramSpec(
        stage_id="csf_test_evidence",
        route="cross_sectional_factor",
        stage_dir_name="05_csf_test_evidence",
        required_outputs=tuple(CSF_TEST_EVIDENCE_REQUIRED_OUTPUTS),
    ),
    "csf_backtest_ready": StageProgramSpec(
        stage_id="csf_backtest_ready",
        route="cross_sectional_factor",
        stage_dir_name="06_csf_backtest_ready",
        required_outputs=tuple(CSF_BACKTEST_READY_REQUIRED_OUTPUTS),
    ),
    "csf_holdout_validation": StageProgramSpec(
        stage_id="csf_holdout_validation",
        route="cross_sectional_factor",
        stage_dir_name="07_csf_holdout_validation",
        required_outputs=tuple(CSF_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS),
    ),
    "tss_data_ready": StageProgramSpec(
        stage_id="tss_data_ready",
        route="time_series_signal",
        stage_dir_name="02_tss_data_ready",
        required_outputs=tuple(TSS_DATA_READY_REQUIRED_OUTPUTS),
    ),
    "tss_signal_ready": StageProgramSpec(
        stage_id="tss_signal_ready",
        route="time_series_signal",
        stage_dir_name="03_tss_signal_ready",
        required_outputs=tuple(TSS_SIGNAL_READY_REQUIRED_OUTPUTS),
    ),
    "tss_train_freeze": StageProgramSpec(
        stage_id="tss_train_freeze",
        route="time_series_signal",
        stage_dir_name="04_tss_train_freeze",
        required_outputs=tuple(TSS_TRAIN_FREEZE_REQUIRED_OUTPUTS),
    ),
    "tss_test_evidence": StageProgramSpec(
        stage_id="tss_test_evidence",
        route="time_series_signal",
        stage_dir_name="05_tss_test_evidence",
        required_outputs=tuple(TSS_TEST_EVIDENCE_REQUIRED_OUTPUTS),
    ),
    "tss_backtest_ready": StageProgramSpec(
        stage_id="tss_backtest_ready",
        route="time_series_signal",
        stage_dir_name="06_tss_backtest_ready",
        required_outputs=tuple(TSS_BACKTEST_READY_REQUIRED_OUTPUTS),
    ),
    "tss_holdout_validation": StageProgramSpec(
        stage_id="tss_holdout_validation",
        route="time_series_signal",
        stage_dir_name="07_tss_holdout_validation",
        required_outputs=tuple(TSS_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS),
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
    "tss_data_ready",
    "tss_signal_ready",
    "tss_train_freeze",
    "tss_test_evidence",
    "tss_backtest_ready",
    "tss_holdout_validation",
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
    "tss_data_ready": "tss_signal_ready",
    "tss_signal_ready": "tss_train_freeze",
    "tss_train_freeze": "tss_test_evidence",
    "tss_test_evidence": "tss_backtest_ready",
    "tss_backtest_ready": "tss_holdout_validation",
    "tss_holdout_validation": None,
}

FREEZE_DRAFT_STAGE_SPECS: dict[SessionStage, tuple[tuple[str, ...], str, tuple[str, ...], str]] = {
    "mandate_confirmation_pending": (
        ("00_idea_intake",),
        MANDATE_FREEZE_DRAFT_FILE,
        tuple(MANDATE_FREEZE_GROUP_ORDER),
        "mandate",
    ),
    "data_ready_confirmation_pending": (
        ("02_data_ready", "author", "draft"),
        DATA_READY_FREEZE_DRAFT_FILE,
        tuple(DATA_READY_FREEZE_GROUP_ORDER),
        "data_ready",
    ),
    "csf_data_ready_confirmation_pending": (
        ("02_csf_data_ready", "author", "draft"),
        CSF_DATA_READY_FREEZE_DRAFT_FILE,
        tuple(CSF_DATA_READY_FREEZE_GROUP_ORDER),
        "csf_data_ready",
    ),
    "signal_ready_confirmation_pending": (
        ("03_signal_ready", "author", "draft"),
        SIGNAL_READY_FREEZE_DRAFT_FILE,
        tuple(SIGNAL_READY_FREEZE_GROUP_ORDER),
        "signal_ready",
    ),
    "csf_signal_ready_confirmation_pending": (
        ("03_csf_signal_ready", "author", "draft"),
        CSF_SIGNAL_READY_FREEZE_DRAFT_FILE,
        tuple(CSF_SIGNAL_READY_FREEZE_GROUP_ORDER),
        "csf_signal_ready",
    ),
    "train_freeze_confirmation_pending": (
        ("04_train_freeze", "author", "draft"),
        TRAIN_FREEZE_DRAFT_FILE,
        tuple(TRAIN_FREEZE_GROUP_ORDER),
        "train_freeze",
    ),
    "csf_train_freeze_confirmation_pending": (
        ("04_csf_train_freeze", "author", "draft"),
        CSF_TRAIN_FREEZE_DRAFT_FILE,
        tuple(CSF_TRAIN_FREEZE_GROUP_ORDER),
        "csf_train_freeze",
    ),
    "test_evidence_confirmation_pending": (
        ("05_test_evidence", "author", "draft"),
        TEST_EVIDENCE_DRAFT_FILE,
        tuple(TEST_EVIDENCE_GROUP_ORDER),
        "test_evidence",
    ),
    "csf_test_evidence_confirmation_pending": (
        ("05_csf_test_evidence", "author", "draft"),
        CSF_TEST_EVIDENCE_DRAFT_FILE,
        tuple(CSF_TEST_EVIDENCE_GROUP_ORDER),
        "csf_test_evidence",
    ),
    "backtest_ready_confirmation_pending": (
        ("06_backtest", "author", "draft"),
        BACKTEST_READY_DRAFT_FILE,
        tuple(BACKTEST_READY_GROUP_ORDER),
        "backtest_ready",
    ),
    "csf_backtest_ready_confirmation_pending": (
        ("06_csf_backtest_ready", "author", "draft"),
        CSF_BACKTEST_READY_DRAFT_FILE,
        tuple(CSF_BACKTEST_READY_GROUP_ORDER),
        "csf_backtest_ready",
    ),
    "holdout_validation_confirmation_pending": (
        ("07_holdout", "author", "draft"),
        HOLDOUT_VALIDATION_DRAFT_FILE,
        tuple(HOLDOUT_VALIDATION_GROUP_ORDER),
        "holdout_validation",
    ),
    "csf_holdout_validation_confirmation_pending": (
        ("07_csf_holdout_validation", "author", "draft"),
        CSF_HOLDOUT_VALIDATION_DRAFT_FILE,
        tuple(CSF_HOLDOUT_VALIDATION_GROUP_ORDER),
        "csf_holdout_validation",
    ),
    "tss_data_ready_confirmation_pending": (
        ("02_tss_data_ready", "author", "draft"),
        TSS_DATA_READY_FREEZE_DRAFT_FILE,
        tuple(TSS_DATA_READY_FREEZE_GROUP_ORDER),
        "tss_data_ready",
    ),
    "tss_signal_ready_confirmation_pending": (
        ("03_tss_signal_ready", "author", "draft"),
        TSS_SIGNAL_READY_FREEZE_DRAFT_FILE,
        tuple(TSS_SIGNAL_READY_FREEZE_GROUP_ORDER),
        "tss_signal_ready",
    ),
    "tss_train_freeze_confirmation_pending": (
        ("04_tss_train_freeze", "author", "draft"),
        TSS_TRAIN_FREEZE_DRAFT_FILE,
        tuple(TSS_TRAIN_FREEZE_GROUP_ORDER),
        "tss_train_freeze",
    ),
    "tss_test_evidence_confirmation_pending": (
        ("05_tss_test_evidence", "author", "draft"),
        TSS_TEST_EVIDENCE_DRAFT_FILE,
        tuple(TSS_TEST_EVIDENCE_GROUP_ORDER),
        "tss_test_evidence",
    ),
    "tss_backtest_ready_confirmation_pending": (
        ("06_tss_backtest_ready", "author", "draft"),
        TSS_BACKTEST_READY_DRAFT_FILE,
        tuple(TSS_BACKTEST_READY_GROUP_ORDER),
        "tss_backtest_ready",
    ),
    "tss_holdout_validation_confirmation_pending": (
        ("07_tss_holdout_validation", "author", "draft"),
        TSS_HOLDOUT_VALIDATION_DRAFT_FILE,
        tuple(TSS_HOLDOUT_VALIDATION_GROUP_ORDER),
        "tss_holdout_validation",
    ),
}



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
    tss_data_ready_dir = lineage_root / "02_tss_data_ready"
    tss_signal_ready_dir = lineage_root / "03_tss_signal_ready"
    tss_train_dir = lineage_root / "04_tss_train_freeze"
    tss_test_evidence_dir = lineage_root / "05_tss_test_evidence"
    tss_backtest_dir = lineage_root / "06_tss_backtest_ready"
    tss_holdout_dir = lineage_root / "07_tss_holdout_validation"
    csf_data_ready_dir = lineage_root / "02_csf_data_ready"
    csf_signal_ready_dir = lineage_root / "03_csf_signal_ready"
    csf_train_dir = lineage_root / "04_csf_train_freeze"
    csf_test_evidence_dir = lineage_root / "05_csf_test_evidence"
    csf_backtest_dir = lineage_root / "06_csf_backtest_ready"
    csf_holdout_dir = lineage_root / "07_csf_holdout_validation"
    is_csf_route = _is_csf_route(lineage_root)
    is_tss_route = _is_tss_route(lineage_root)

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

    if is_tss_route:
        if _tss_holdout_validation_outputs_complete(tss_holdout_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="tss_holdout_validation",
                stage_dir=tss_holdout_dir,
                closure_complete=_tss_holdout_validation_closure_complete(tss_holdout_dir),
            )

        if _tss_backtest_ready_outputs_complete(tss_backtest_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="tss_backtest_ready",
                stage_dir=tss_backtest_dir,
                closure_complete=_tss_backtest_ready_closure_complete(tss_backtest_dir),
            )

        if _tss_test_evidence_outputs_complete(tss_test_evidence_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="tss_test_evidence",
                stage_dir=tss_test_evidence_dir,
                closure_complete=_tss_test_evidence_closure_complete(tss_test_evidence_dir),
            )

        if _tss_train_freeze_outputs_complete(tss_train_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="tss_train_freeze",
                stage_dir=tss_train_dir,
                closure_complete=_tss_train_freeze_closure_complete(tss_train_dir),
            )

        if _tss_signal_ready_outputs_complete(tss_signal_ready_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="tss_signal_ready",
                stage_dir=tss_signal_ready_dir,
                closure_complete=_tss_signal_ready_closure_complete(tss_signal_ready_dir),
            )

        if _tss_data_ready_outputs_complete(tss_data_ready_dir):
            return _review_or_post_review_stage(
                lineage_root,
                stage_base="tss_data_ready",
                stage_dir=tss_data_ready_dir,
                closure_complete=_tss_data_ready_closure_complete(tss_data_ready_dir),
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
    if data_ready_dir.exists() and (
        data_ready_dir / "author" / "draft" / DATA_READY_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_data_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in data_ready_dir.iterdir())


def build_data_ready_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "data_ready_author")


def ensure_csf_data_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "02_csf_data_ready"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / CSF_DATA_READY_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_csf_data_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_data_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "csf_data_ready_author":
        return []
    if next_csf_data_ready_freeze_group(lineage_root) is not None:
        return []
    return _invoke_author_stage_without_autogen(lineage_root, "csf_data_ready_author")


def ensure_tss_data_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "02_tss_data_ready"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / TSS_DATA_READY_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_tss_data_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_tss_data_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "tss_data_ready_author":
        return []
    if next_tss_data_ready_freeze_group(lineage_root) is not None:
        return []
    return _invoke_author_stage_without_autogen(lineage_root, "tss_data_ready_author")


def ensure_signal_ready_scaffold(lineage_root: Path) -> list[str]:
    signal_ready_dir = lineage_root / "03_signal_ready"
    if signal_ready_dir.exists() and (
        signal_ready_dir / "author" / "draft" / SIGNAL_READY_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_signal_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in signal_ready_dir.iterdir())


def build_signal_ready_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "signal_ready_author")


def ensure_csf_signal_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "03_csf_signal_ready"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_csf_signal_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_signal_ready_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "csf_signal_ready_author")


def ensure_tss_signal_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "03_tss_signal_ready"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / TSS_SIGNAL_READY_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_tss_signal_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_tss_signal_ready_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "tss_signal_ready_author")


def ensure_train_freeze_scaffold(lineage_root: Path) -> list[str]:
    train_dir = lineage_root / "04_train_freeze"
    if train_dir.exists() and (
        train_dir / "author" / "draft" / TRAIN_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_train_freeze(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in train_dir.iterdir())


def build_train_freeze_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "train_freeze_author")


def ensure_csf_train_freeze_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "04_csf_train_freeze"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / CSF_TRAIN_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_csf_train_freeze(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_train_freeze_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "csf_train_freeze_author")


def ensure_tss_train_freeze_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "04_tss_train_freeze"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / TSS_TRAIN_FREEZE_DRAFT_FILE
    ).exists():
        return []

    scaffold_tss_train_freeze(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_tss_train_freeze_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "tss_train_freeze_author")


def ensure_test_evidence_scaffold(lineage_root: Path) -> list[str]:
    test_dir = lineage_root / "05_test_evidence"
    if test_dir.exists() and (
        test_dir / "author" / "draft" / TEST_EVIDENCE_DRAFT_FILE
    ).exists():
        return []

    scaffold_test_evidence(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in test_dir.iterdir())


def build_test_evidence_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "test_evidence_author")


def ensure_csf_test_evidence_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "05_csf_test_evidence"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / CSF_TEST_EVIDENCE_DRAFT_FILE
    ).exists():
        return []

    scaffold_csf_test_evidence(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_test_evidence_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "csf_test_evidence_author")


def ensure_tss_test_evidence_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "05_tss_test_evidence"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / TSS_TEST_EVIDENCE_DRAFT_FILE
    ).exists():
        return []

    scaffold_tss_test_evidence(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_tss_test_evidence_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "tss_test_evidence_author")


def ensure_backtest_ready_scaffold(lineage_root: Path) -> list[str]:
    backtest_dir = lineage_root / "06_backtest"
    if backtest_dir.exists() and (
        backtest_dir / "author" / "draft" / BACKTEST_READY_DRAFT_FILE
    ).exists():
        return []

    scaffold_backtest_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in backtest_dir.iterdir())


def build_backtest_ready_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "backtest_ready_author")


def ensure_csf_backtest_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "06_csf_backtest_ready"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / CSF_BACKTEST_READY_DRAFT_FILE
    ).exists():
        return []

    scaffold_csf_backtest_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_backtest_ready_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "csf_backtest_ready_author")


def ensure_tss_backtest_ready_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "06_tss_backtest_ready"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / TSS_BACKTEST_READY_DRAFT_FILE
    ).exists():
        return []

    scaffold_tss_backtest_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_tss_backtest_ready_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "tss_backtest_ready_author")


def ensure_holdout_validation_scaffold(lineage_root: Path) -> list[str]:
    holdout_dir = lineage_root / "07_holdout"
    if holdout_dir.exists() and (
        holdout_dir / "author" / "draft" / HOLDOUT_VALIDATION_DRAFT_FILE
    ).exists():
        return []

    scaffold_holdout_validation(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in holdout_dir.iterdir())


def build_holdout_validation_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "holdout_validation_author")


def ensure_csf_holdout_validation_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "07_csf_holdout_validation"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / CSF_HOLDOUT_VALIDATION_DRAFT_FILE
    ).exists():
        return []

    scaffold_csf_holdout_validation(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_csf_holdout_validation_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "csf_holdout_validation_author")


def ensure_tss_holdout_validation_scaffold(lineage_root: Path) -> list[str]:
    stage_dir = lineage_root / "07_tss_holdout_validation"
    if stage_dir.exists() and (
        stage_dir / "author" / "draft" / TSS_HOLDOUT_VALIDATION_DRAFT_FILE
    ).exists():
        return []

    scaffold_tss_holdout_validation(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in stage_dir.iterdir())


def build_tss_holdout_validation_if_admitted(lineage_root: Path) -> list[str]:
    return _invoke_author_stage_without_autogen(lineage_root, "tss_holdout_validation_author")


def run_mandate_review_if_ready(lineage_root: Path) -> dict[str, object] | None:
    if detect_session_stage(lineage_root) != "mandate_review":
        return None

    mandate_dir = lineage_root / "01_mandate"
    if not _review_findings_path(mandate_dir).exists():
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
    mandate_route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
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
    mandate_route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
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
    return first_unconfirmed_or_invalid_group(draft_path, MANDATE_FREEZE_GROUP_ORDER)


def next_data_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "02_data_ready" / "author" / "draft" / DATA_READY_FREEZE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, DATA_READY_FREEZE_GROUP_ORDER)


def next_csf_data_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = (
        lineage_root / "02_csf_data_ready" / "author" / "draft" / CSF_DATA_READY_FREEZE_DRAFT_FILE
    )
    return first_unconfirmed_or_invalid_group(draft_path, CSF_DATA_READY_FREEZE_GROUP_ORDER)


def next_tss_data_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = (
        lineage_root / "02_tss_data_ready" / "author" / "draft" / TSS_DATA_READY_FREEZE_DRAFT_FILE
    )
    return first_unconfirmed_or_invalid_group(draft_path, TSS_DATA_READY_FREEZE_GROUP_ORDER)


def next_signal_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "03_signal_ready" / "author" / "draft" / SIGNAL_READY_FREEZE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, SIGNAL_READY_FREEZE_GROUP_ORDER)


def next_csf_signal_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "03_csf_signal_ready" / "author" / "draft" / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, CSF_SIGNAL_READY_FREEZE_GROUP_ORDER)


def next_tss_signal_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "03_tss_signal_ready" / "author" / "draft" / TSS_SIGNAL_READY_FREEZE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, TSS_SIGNAL_READY_FREEZE_GROUP_ORDER)


def next_train_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "04_train_freeze" / "author" / "draft" / TRAIN_FREEZE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, TRAIN_FREEZE_GROUP_ORDER)


def next_csf_train_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "04_csf_train_freeze" / "author" / "draft" / CSF_TRAIN_FREEZE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, CSF_TRAIN_FREEZE_GROUP_ORDER)


def next_tss_train_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "04_tss_train_freeze" / "author" / "draft" / TSS_TRAIN_FREEZE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, TSS_TRAIN_FREEZE_GROUP_ORDER)


def next_test_evidence_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "05_test_evidence" / "author" / "draft" / TEST_EVIDENCE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, TEST_EVIDENCE_GROUP_ORDER)


def next_csf_test_evidence_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "05_csf_test_evidence" / "author" / "draft" / CSF_TEST_EVIDENCE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, CSF_TEST_EVIDENCE_GROUP_ORDER)


def next_tss_test_evidence_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "05_tss_test_evidence" / "author" / "draft" / TSS_TEST_EVIDENCE_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, TSS_TEST_EVIDENCE_GROUP_ORDER)


def next_backtest_ready_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "06_backtest" / "author" / "draft" / BACKTEST_READY_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, BACKTEST_READY_GROUP_ORDER)


def next_csf_backtest_ready_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "06_csf_backtest_ready" / "author" / "draft" / CSF_BACKTEST_READY_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, CSF_BACKTEST_READY_GROUP_ORDER)


def next_tss_backtest_ready_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "06_tss_backtest_ready" / "author" / "draft" / TSS_BACKTEST_READY_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, TSS_BACKTEST_READY_GROUP_ORDER)


def next_holdout_validation_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "07_holdout" / "author" / "draft" / HOLDOUT_VALIDATION_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, HOLDOUT_VALIDATION_GROUP_ORDER)


def next_csf_holdout_validation_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "07_csf_holdout_validation" / "author" / "draft" / CSF_HOLDOUT_VALIDATION_DRAFT_FILE
    return first_unconfirmed_or_invalid_group(draft_path, CSF_HOLDOUT_VALIDATION_GROUP_ORDER)


def next_tss_holdout_validation_group(lineage_root: Path) -> str | None:
    draft_path = (
        lineage_root / "07_tss_holdout_validation" / "author" / "draft" / TSS_HOLDOUT_VALIDATION_DRAFT_FILE
    )
    return first_unconfirmed_or_invalid_group(draft_path, TSS_HOLDOUT_VALIDATION_GROUP_ORDER)


def freeze_groups_for_stage(
    lineage_root: Path, current_stage: SessionStage
) -> list[dict[str, object]] | None:
    spec = FREEZE_DRAFT_STAGE_SPECS.get(current_stage)
    if spec is None:
        return None

    _, _, group_order, _ = spec
    draft_path = _freeze_draft_path(lineage_root, current_stage)
    if not draft_path.exists():
        return [
            {
                "name": name,
                "confirmed": False,
                "missing_items": ["draft_not_scaffolded"],
                "draft": {},
            }
            for name in group_order
        ]

    payload = _read_yaml(draft_path)
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        groups = {}

    statuses: list[dict[str, object]] = []
    for name in group_order:
        group_payload = groups.get(name, {})
        if not isinstance(group_payload, dict):
            statuses.append(
                {
                    "name": name,
                    "confirmed": False,
                    "missing_items": ["group_missing"],
                    "draft": {},
                }
            )
            continue

        draft = group_payload.get("draft", {})
        missing_items = group_payload.get("missing_items", [])
        invalid_reason = freeze_group_invalid_reason(group_payload)
        resolved_missing_items = missing_items if isinstance(missing_items, list) else []
        if invalid_reason is not None:
            resolved_missing_items = [*resolved_missing_items, invalid_reason]
        statuses.append(
            {
                "name": name,
                "confirmed": bool(group_payload.get("confirmed")) and invalid_reason is None,
                "missing_items": resolved_missing_items,
                "draft": draft if isinstance(draft, dict) else {},
            }
        )
    return statuses


def confirm_all_freeze_groups_for_current_stage(
    lineage_root: Path,
    current_stage: SessionStage,
) -> str | None:
    spec = FREEZE_DRAFT_STAGE_SPECS.get(current_stage)
    if spec is None:
        return None

    _, _, group_order, _ = spec
    draft_path = _freeze_draft_path(lineage_root, current_stage)
    if not draft_path.exists():
        return None

    payload = confirm_all_freeze_groups(draft_path, group_order)

    draft_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return str(draft_path.relative_to(lineage_root))


def validate_freeze_groups_for_stage_transition(
    lineage_root: Path,
    current_stage: SessionStage,
) -> None:
    spec = FREEZE_DRAFT_STAGE_SPECS.get(current_stage)
    if spec is None:
        return
    _, _, group_order, _ = spec
    validate_confirmed_freeze_groups(_freeze_draft_path(lineage_root, current_stage), group_order)


def _all_freeze_groups_next_action(stage_label: str) -> str:
    return (
        f"Review all {stage_label} freeze groups, then run with --confirm-all-freeze-groups "
        "or reply 确认全部 to mark them confirmed."
    )


def ensure_freeze_draft_for_stage(lineage_root: Path, current_stage: SessionStage) -> list[str]:
    # 批量确认前先确保当前 confirmation gate 的 draft skeleton 已落盘。
    if current_stage == "data_ready_confirmation_pending":
        return ensure_data_ready_scaffold(lineage_root)
    if current_stage == "csf_data_ready_confirmation_pending":
        return ensure_csf_data_ready_scaffold(lineage_root)
    if current_stage == "tss_data_ready_confirmation_pending":
        return ensure_tss_data_ready_scaffold(lineage_root)
    if current_stage == "signal_ready_confirmation_pending":
        return ensure_signal_ready_scaffold(lineage_root)
    if current_stage == "csf_signal_ready_confirmation_pending":
        return ensure_csf_signal_ready_scaffold(lineage_root)
    if current_stage == "tss_signal_ready_confirmation_pending":
        return ensure_tss_signal_ready_scaffold(lineage_root)
    if current_stage == "train_freeze_confirmation_pending":
        return ensure_train_freeze_scaffold(lineage_root)
    if current_stage == "csf_train_freeze_confirmation_pending":
        return ensure_csf_train_freeze_scaffold(lineage_root)
    if current_stage == "tss_train_freeze_confirmation_pending":
        return ensure_tss_train_freeze_scaffold(lineage_root)
    if current_stage == "test_evidence_confirmation_pending":
        return ensure_test_evidence_scaffold(lineage_root)
    if current_stage == "csf_test_evidence_confirmation_pending":
        return ensure_csf_test_evidence_scaffold(lineage_root)
    if current_stage == "tss_test_evidence_confirmation_pending":
        return ensure_tss_test_evidence_scaffold(lineage_root)
    if current_stage == "backtest_ready_confirmation_pending":
        return ensure_backtest_ready_scaffold(lineage_root)
    if current_stage == "csf_backtest_ready_confirmation_pending":
        return ensure_csf_backtest_ready_scaffold(lineage_root)
    if current_stage == "tss_backtest_ready_confirmation_pending":
        return ensure_tss_backtest_ready_scaffold(lineage_root)
    if current_stage == "holdout_validation_confirmation_pending":
        return ensure_holdout_validation_scaffold(lineage_root)
    if current_stage == "csf_holdout_validation_confirmation_pending":
        return ensure_csf_holdout_validation_scaffold(lineage_root)
    if current_stage == "tss_holdout_validation_confirmation_pending":
        return ensure_tss_holdout_validation_scaffold(lineage_root)
    return []


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
    runtime_stage_status_override: str | None = None,
    runtime_blocking_reason_code_override: str | None = None,
    runtime_next_action_override: str | None = None,
    continue_mode: bool = False,
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
    if runtime_stage_status_override is not None:
        stage_status = runtime_stage_status_override
    if runtime_blocking_reason_code_override is not None:
        blocking_reason_code = runtime_blocking_reason_code_override
    if runtime_next_action_override is not None:
        runtime_next_action = runtime_next_action_override
    resolved_current_skill = current_skill or (
        _orchestrated_current_skill_for_stage(
            current_stage=current_stage,
            requires_failure_handling=requires_failure_handling,
        )
        if continue_mode
        else _current_skill_for_stage(
            current_stage=current_stage,
            requires_failure_handling=requires_failure_handling,
            runtime_stage_status=stage_status,
        )
    )
    resolved_why_this_skill = why_this_skill or (
        _orchestrated_why_this_skill(
            current_stage=current_stage,
            review_verdict=review_verdict,
            requires_failure_handling=requires_failure_handling,
            runtime_stage_status=stage_status,
        )
        if continue_mode
        else _why_this_skill(
            current_stage=current_stage,
            current_skill=resolved_current_skill,
            review_verdict=review_verdict,
            requires_failure_handling=requires_failure_handling,
            runtime_stage_status=stage_status,
        )
    )
    resolved_blocking_reason = (
        blocking_reason
        if blocking_reason is not None
        else (
            _orchestrated_blocking_reason(
                current_stage=current_stage,
                runtime_stage_status=stage_status,
                requires_failure_handling=requires_failure_handling,
                review_verdict=review_verdict,
            )
            if continue_mode
            else runtime_blocking_reason
        )
    )
    resolved_resume_hint = resume_hint or (
        _orchestrated_resume_hint(
            lineage_id=lineage_id,
            current_stage=current_stage,
            requires_failure_handling=requires_failure_handling,
            required_program_dir=required_program_dir,
            runtime_stage_status=stage_status,
        )
        if continue_mode
        else _resume_hint(
            lineage_id=lineage_id,
            current_stage=current_stage,
            current_skill=resolved_current_skill,
            requires_failure_handling=requires_failure_handling,
            required_program_dir=required_program_dir,
            runtime_stage_status=stage_status,
        )
    )
    review_state_snapshot = _review_state_snapshot(
        lineage_root=lineage_root,
        current_stage=current_stage,
    )
    resolved_next_action = (
        runtime_next_action
        if requires_failure_handling
        or current_stage.endswith("_author")
        or (current_stage.endswith("_review_confirmation_pending") and stage_status == "awaiting_author_fix")
        or current_stage.endswith("_review_complete")
        else next_action
    )
    if continue_mode:
        resolved_next_action = _orchestrated_next_action(
            lineage_id=lineage_id,
            current_stage=current_stage,
            runtime_stage_status=stage_status,
            next_action=resolved_next_action,
            requires_failure_handling=requires_failure_handling,
            required_program_dir=required_program_dir,
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
        next_action=resolved_next_action,
        why_now=why_now or [],
        open_risks=open_risks or [],
        factor_role=factor_role,
        factor_structure=factor_structure,
        portfolio_expression=portfolio_expression,
        neutralization_policy=neutralization_policy,
        review_verdict=review_verdict,
        review_state=review_state_snapshot["review_state"],
        active_review_cycle_id=review_state_snapshot["active_review_cycle_id"],
        review_requested_at=review_state_snapshot["review_requested_at"],
        review_bound_author_digest=review_state_snapshot["review_bound_author_digest"],
        closure_written_at=review_state_snapshot["closure_written_at"],
        requires_failure_handling=requires_failure_handling,
        failure_stage=failure_stage,
        failure_reason_summary=failure_reason_summary,
        freeze_groups=freeze_groups_for_stage(lineage_root, current_stage),
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
    if runtime_stage_status == "awaiting_author_fix" and (
        current_stage.endswith("_review") or current_stage.endswith("_review_confirmation_pending")
    ):
        return STAGE_ACTIVE_SKILLS.get(f"{_stage_base_name(current_stage)}_author", "qros-research-session")
    return STAGE_ACTIVE_SKILLS.get(current_stage, "qros-research-session")


def _orchestrated_current_skill_for_stage(
    *,
    current_stage: SessionStage,
    requires_failure_handling: bool,
) -> str:
    if requires_failure_handling:
        return "qros-stage-failure-handler"
    if current_stage.endswith("_review_complete"):
        return "qros-research-session"
    return "qros-research-session"


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
    if current_stage.endswith("_next_stage_confirmation_pending"):
        return f"Current stage {current_stage} is waiting for explicit approval before entering the downstream stage."
    if current_stage.endswith("_review_complete"):
        return "The covered workflow has reached a terminal review-complete state, so qros-research-session is reporting completion status."
    if current_stage.endswith("_review_confirmation_pending"):
        if runtime_stage_status == "awaiting_author_fix":
            return (
                f"Current stage {current_stage} failed deterministic review preflight, "
                f"so {current_skill} is the active author-fix skill before review entry."
            )
        return (
            f"Current stage {current_stage} is waiting for an explicit stage-specific review launch in the current session, "
            f"so {current_skill} is the fixed review skill for that next lane."
        )
    if current_stage.endswith("_review"):
        if runtime_stage_status == "awaiting_author_fix":
            return f"Current stage {current_stage} has fixable adversarial findings, so {current_skill} is the active author-fix skill."
        return f"Current stage {current_stage} requires formal review closure, so {current_skill} is the active review skill."
    if current_stage.endswith("_next_stage_confirmation_pending"):
        return f"Current stage {current_stage} is waiting for explicit next-stage confirmation, so {current_skill} is holding the orchestration gate."
    return f"Current stage {current_stage} is in the authoring/freeze flow, so {current_skill} is the active author skill."


def _orchestrated_why_this_skill(
    *,
    current_stage: SessionStage,
    review_verdict: str | None,
    requires_failure_handling: bool,
    runtime_stage_status: str | None = None,
) -> str:
    if requires_failure_handling:
        verdict = review_verdict or "a failure-class review result"
        return (
            f"Review verdict {verdict} blocks normal progression, so failure handling is now the active workflow."
        )
    stage_base = _stage_base_name(current_stage)
    if current_stage.endswith("_review_complete"):
        return "The covered workflow has reached a terminal review-complete state, so qros-research-session is reporting completion status."
    if current_stage.endswith("_review_confirmation_pending"):
        if runtime_stage_status == "awaiting_author_fix":
            return (
                f"qros-research-session identified {stage_base} author outputs that must be repaired before review entry; "
                "it should use the stage-specific author protocol internally."
            )
        return (
            f"qros-research-session identified {stage_base} as review-ready and is holding the explicit review confirmation gate."
        )
    if current_stage.endswith("_review"):
        if runtime_stage_status == "awaiting_author_fix":
            return (
                f"qros-research-session identified fixable {stage_base} review findings and must return to author repair."
            )
        return (
            f"qros-research-session identified {stage_base} as the active review lane and should run the review protocol internally."
        )
    if current_stage.endswith("_next_stage_confirmation_pending"):
        return (
            f"qros-research-session identified completed {stage_base} review and is holding the explicit next-stage gate."
        )
    if current_stage.endswith("_confirmation_pending"):
        return (
            f"qros-research-session identified {stage_base} as the active freeze-confirmation gate."
        )
    if current_stage.endswith("_author") or runtime_stage_status in {
        "awaiting_stage_program",
        "awaiting_program_validation",
        "awaiting_program_execution",
    }:
        return (
            f"qros-research-session identified {stage_base} as the active author lane; "
            f"stage-specific skills are internal/debug protocols, not user-facing entrypoints."
        )
    return (
        f"qros-research-session identified {current_stage} as the current workflow state and will route the next action."
    )


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
        return f"{_stage_base_name(current_stage)} review has not been started by an explicit qros-*-review launch yet."
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


def _orchestrated_blocking_reason(
    *,
    current_stage: SessionStage,
    runtime_stage_status: str,
    requires_failure_handling: bool,
    review_verdict: str | None,
) -> str | None:
    if requires_failure_handling:
        verdict = review_verdict or "a failure-class review result"
        return f"Normal progression is blocked by review verdict {verdict}."
    stage_base = _stage_base_name(current_stage)
    if current_stage.endswith("_review_confirmation_pending"):
        if runtime_stage_status == "awaiting_author_fix":
            return f"{stage_base} author outputs must be repaired before review can be confirmed."
        return f"{stage_base} review is waiting for explicit CONFIRM_REVIEW in qros-research-session."
    if current_stage.endswith("_review"):
        return f"{stage_base} review lane is active and waiting for reviewer output, audit, or closure."
    return _blocking_reason(
        current_stage=current_stage,
        review_verdict=review_verdict,
        requires_failure_handling=requires_failure_handling,
    )


def _post_mandate_program_comment_requirement(current_stage: SessionStage) -> str:
    if _stage_base_name(current_stage) == "mandate":
        return ""
    return " and include Chinese comments for key generation logic"


def _resume_hint(
    *,
    lineage_id: str,
    current_stage: SessionStage,
    current_skill: str,
    requires_failure_handling: bool,
    required_program_dir: str | None = None,
    runtime_stage_status: str | None = None,
) -> str:
    if requires_failure_handling:
        return (
            f"Invoke {current_skill} for lineage {lineage_id} in the same research repo, "
            f"then rerun qros-session --lineage-id {lineage_id}."
        )
    if runtime_stage_status == "awaiting_stage_program":
        if _stage_base_name(current_stage) == "mandate":
            if required_program_dir is not None:
                return (
                    f"Run {current_skill} to author the lineage-local stage program under "
                    f"{required_program_dir}, then rerun qros-session --lineage-id {lineage_id}."
                )
            return (
                f"Run {current_skill} to author the lineage-local stage program, "
                f"then rerun qros-session --lineage-id {lineage_id}."
            )
        comment_requirement = _post_mandate_program_comment_requirement(current_stage)
        if required_program_dir is not None:
            return (
                f"Run {current_skill}; Codex must explicitly author the lineage-local stage program under "
                f"{required_program_dir}{comment_requirement}, then rerun qros-session --lineage-id {lineage_id}."
            )
        return (
            f"Run {current_skill}; Codex must explicitly author the lineage-local stage program"
            f"{comment_requirement}, then rerun qros-session --lineage-id {lineage_id}."
        )
    if current_stage.endswith("_review_confirmation_pending"):
        if runtime_stage_status == "awaiting_author_fix":
            return (
                f"Run {current_skill} to repair author/formal outputs so review preflight passes, "
                f"then rerun qros-session --lineage-id {lineage_id}."
            )
        return (
            f"Enter {current_skill}, launch a reviewer and run ./.qros/bin/qros-review-cycle prepare for {_stage_base_name(current_stage)}, "
            f"then rerun qros-session --lineage-id {lineage_id}."
        )
    if current_stage.endswith("_review"):
        if runtime_stage_status == "awaiting_author_fix":
            return (
                f"Run {current_skill} to address review/result/review_findings.yaml in the author lane, "
                f"refresh author/formal outputs, then rerun the review workflow and qros-session --lineage-id {lineage_id}."
            )
        return (
            f"Run {current_skill} in the same research repo, or rerun qros-session --lineage-id {lineage_id} "
            "to inspect updated status."
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


def _orchestrated_resume_hint(
    *,
    lineage_id: str,
    current_stage: SessionStage,
    requires_failure_handling: bool,
    required_program_dir: str | None = None,
    runtime_stage_status: str | None = None,
) -> str:
    if requires_failure_handling:
        return (
            f"Invoke qros-stage-failure-handler for lineage {lineage_id}, then rerun "
            f"qros-session {lineage_id} --continue."
        )
    stage_base = _stage_base_name(current_stage)
    if runtime_stage_status == "awaiting_stage_program":
        location = f" under {required_program_dir}" if required_program_dir is not None else ""
        return (
            f"Continue qros-research-session for {lineage_id}; it should author or refresh the {stage_base} "
            f"lineage-local stage program{location}, then rerun qros-session {lineage_id} --continue."
        )
    if runtime_stage_status in {"awaiting_program_validation", "awaiting_program_execution"}:
        return (
            f"Continue qros-research-session for {lineage_id}; it should fix or execute the {stage_base} "
            f"stage program, then rerun qros-session {lineage_id} --continue."
        )
    if current_stage.endswith("_review_confirmation_pending"):
        if runtime_stage_status == "awaiting_author_fix":
            return (
                f"Continue qros-research-session for {lineage_id}; repair {stage_base} author/formal outputs "
                f"and rerun qros-session {lineage_id} --continue before review."
            )
        return (
            f"Confirm review for {stage_base}; then continue qros-research-session for {lineage_id} "
            "to launch the reviewer and close review."
        )
    if current_stage.endswith("_review"):
        return (
            f"Continue qros-research-session for {lineage_id}; it should run the {stage_base} review lane "
            "until reviewer output, audit, and closure are resolved."
        )
    if current_stage.endswith("_next_stage_confirmation_pending"):
        return (
            f"Confirm the next-stage handoff for {stage_base}, then rerun qros-session {lineage_id} --continue."
        )
    if current_stage.endswith("_review_complete"):
        return f"Rerun qros-session {lineage_id} --continue if new downstream work is introduced."
    return (
        f"Continue qros-research-session in the same repo and rerun qros-session {lineage_id} --continue "
        "after completing the prompted confirmation or author step."
    )


def _orchestrated_next_action(
    *,
    lineage_id: str,
    current_stage: SessionStage,
    runtime_stage_status: str,
    next_action: str,
    requires_failure_handling: bool,
    required_program_dir: str | None,
) -> str:
    if requires_failure_handling:
        return next_action
    stage_base = _stage_base_name(current_stage)
    if runtime_stage_status == "awaiting_author_fix":
        return (
            f"Continue qros-research-session for {stage_base}; repair author/formal outputs using the "
            f"stage-specific author protocol internally, then rerun qros-session {lineage_id} --continue."
        )
    if runtime_stage_status == "awaiting_stage_program":
        location = f" under {required_program_dir}" if required_program_dir is not None else ""
        return (
            f"Continue qros-research-session for {stage_base}; author or refresh the lineage-local stage program"
            f"{location} using the stage-specific author protocol internally."
        )
    if runtime_stage_status in {"awaiting_program_validation", "awaiting_program_execution"}:
        return (
            f"Continue qros-research-session for {stage_base}; validate or execute the stage program using the "
            "stage-specific author protocol internally."
        )
    if current_stage.endswith("_review_confirmation_pending"):
        return (
            f"Ask for explicit CONFIRM_REVIEW for {stage_base}. After approval, qros-research-session should "
            "launch the reviewer and run qros-review-cycle prepare / qros-review using the stage-specific review protocol internally; "
            "stage-specific review skills remain advanced/debug entrypoints."
        )
    if current_stage.endswith("_review"):
        return (
            f"Continue qros-research-session review orchestration for {stage_base}: launch or wait for the reviewer, "
            "then run ./.qros/bin/qros-review for closure using the stage-specific review protocol internally."
        )
    return next_action


def session_stage_base_name(current_stage: SessionStage | str) -> str:
    for suffix in (
        "_review_confirmation_pending",
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


def _review_state_snapshot(
    *,
    lineage_root: Path,
    current_stage: SessionStage,
) -> dict[str, str | None]:
    stage_dir = _stage_dir_for_session_stage(lineage_root, current_stage)
    if stage_dir is None or not _stage_base_name(current_stage) in REVIEWABLE_STAGE_BASES:
        return {
            "review_state": None,
            "active_review_cycle_id": None,
            "review_requested_at": None,
            "review_bound_author_digest": None,
            "closure_written_at": None,
        }

    state_path = review_runtime_state_path(stage_dir)
    try:
        state_payload = load_review_runtime_state(state_path) if state_path.exists() else {}
    except Exception:
        state_payload = {}
    try:
        request_payload = (
            load_adversarial_review_request(_review_request_path(stage_dir))
            if _review_request_path(stage_dir).exists()
            else {}
        )
    except Exception:
        request_payload = {}
    review_result = _load_adversarial_review_result_if_present(stage_dir)
    certificate_path = _review_closure_path(stage_dir, "stage_completion_certificate.yaml")
    closure_written_at = (
        datetime.fromtimestamp(certificate_path.stat().st_mtime, timezone.utc).isoformat()
        if certificate_path.exists()
        else None
    )
    if state_payload:
        return {
            "review_state": state_payload.get("review_state"),
            "active_review_cycle_id": state_payload.get("active_review_cycle_id"),
            "review_requested_at": state_payload.get("review_requested_at"),
            "review_bound_author_digest": state_payload.get("review_bound_author_digest"),
            "closure_written_at": state_payload.get("closure_written_at") or closure_written_at,
        }

    review_state = "review_not_started"
    if request_payload:
        review_state = "review_in_progress"
    if review_result and review_result.get("review_loop_outcome") == FIX_REQUIRED_OUTCOME:
        review_state = "awaiting_author_fix"
    if certificate_path.exists():
        verdict = _review_verdict_from_stage_dir(stage_dir)
        if verdict in ADVANCING_COMPLETION_STATUSES:
            review_state = "review_closed_pass"
        elif verdict in NON_ADVANCING_COMPLETION_STATUSES:
            review_state = "review_closed_nonadvancing"
    review_requested_at = None
    if _review_request_path(stage_dir).exists():
        review_requested_at = datetime.fromtimestamp(
            _review_request_path(stage_dir).stat().st_mtime,
            timezone.utc,
        ).isoformat()
    review_bound_author_digest = None
    spec = _program_spec_for_session_stage(current_stage)
    if spec is not None and _author_formal_dir(stage_dir).exists():
        try:
            review_bound_author_digest = compute_author_materialization_digest(
                artifact_root=_author_formal_dir(stage_dir),
                required_outputs=spec.required_outputs,
                required_provenance_paths=("program_execution_manifest.json",),
            )
        except Exception:
            review_bound_author_digest = None
    return {
        "review_state": review_state,
        "active_review_cycle_id": request_payload.get("review_cycle_id") if request_payload else None,
        "review_requested_at": review_requested_at,
        "review_bound_author_digest": review_bound_author_digest,
        "closure_written_at": closure_written_at,
    }


def _review_entry_preflight_payload(
    *,
    lineage_root: Path,
    current_stage: SessionStage,
) -> dict[str, object] | None:
    if not current_stage.endswith("_review_confirmation_pending"):
        return None
    if _stage_base_name(current_stage) != "mandate":
        return None
    spec = _program_spec_for_session_stage(current_stage)
    if spec is None:
        return None
    stage_dir = lineage_root / spec.stage_dir_name
    author_formal_dir = _author_formal_dir(stage_dir)
    if not all((author_formal_dir / name).exists() for name in spec.required_outputs):
        return None
    try:
        # 当前 rollout 只在 mandate review-entry 启用 deterministic preflight；
        # 继续保持“required outputs 已齐才触发”的既有语义，避免把半成品误报成 reviewer-lane 失败。
        return run_review_preflight(
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": lineage_root,
            }
        )
    except Exception as exc:
        return {
            "stage": _stage_base_name(current_stage),
            "lineage_id": lineage_root.name,
            "status": "FAIL",
            "content_findings": [f"review preflight failed: {exc}"],
            "upstream_binding_findings": [],
        }


def _review_entry_preflight_findings(payload: dict[str, object] | None) -> list[str]:
    if payload is None or payload.get("status") == "PASS":
        return []
    findings: list[str] = []
    findings.extend(str(item) for item in payload.get("content_findings", []) or [])
    findings.extend(str(item) for item in payload.get("upstream_binding_findings", []) or [])
    return findings


def _format_preflight_findings(findings: list[str], *, limit: int = 3) -> str:
    if not findings:
        return "unknown preflight failure"
    head = findings[:limit]
    suffix = "" if len(findings) <= limit else f" (and {len(findings) - limit} more)"
    return "; ".join(head) + suffix


def _load_adversarial_review_result_if_present(stage_dir: Path) -> dict | None:
    result_path = _review_result_path(stage_dir)
    if not result_path.exists():
        return None
    return load_adversarial_review_result(result_path)


def _load_reviewer_write_scope_audit_if_present(stage_dir: Path) -> dict | None:
    audit_path = _review_audit_path(stage_dir)
    if not audit_path.exists():
        return None
    return load_reviewer_write_scope_audit(audit_path)


def _load_reviewer_receipt_if_present(stage_dir: Path) -> dict | None:
    receipt_path = _review_receipt_path(stage_dir)
    if not receipt_path.exists():
        return None
    return load_reviewer_receipt(receipt_path)


def _review_proof_chain_error(stage_dir: Path) -> str | None:
    request_path = _review_request_path(stage_dir)
    if not request_path.exists():
        return None

    try:
        request_payload = load_adversarial_review_request(request_path)
    except Exception as exc:
        return str(exc)

    receipt_path = _review_receipt_path(stage_dir)
    result_path = _review_result_path(stage_dir)
    if not receipt_path.exists():
        if result_path.exists():
            return f"{REVIEWER_RECEIPT_FILENAME} is missing"
        return None
    try:
        receipt_payload = load_reviewer_receipt(receipt_path)
        validate_receipt_contract(
            request_payload=request_payload,
            receipt_payload=receipt_payload,
        )
    except Exception as exc:
        return str(exc)

    if not result_path.exists():
        return None
    try:
        result_payload = load_adversarial_review_result(result_path)
        validate_result_contract(
            request_payload=request_payload,
            receipt_payload=receipt_payload,
            result_payload=result_payload,
        )
    except Exception as exc:
        return str(exc)

    spec = next(
        (
            value
            for value in SESSION_STAGE_PROGRAM_SPECS.values()
            if value.stage_dir_name == stage_dir.name
        ),
        None,
    )
    if spec is not None:
        stale_reason = review_cycle_stale_reason(
            stage_dir,
            artifact_root=_author_formal_dir(stage_dir),
            required_outputs=spec.required_outputs,
        )
        if stale_reason is not None:
            return stale_reason
    return None


def _review_write_scope_audit_error(stage_dir: Path) -> str | None:
    receipt_path = _review_receipt_path(stage_dir)
    audit_path = _review_audit_path(stage_dir)
    if not receipt_path.exists() or not audit_path.exists():
        return None
    try:
        receipt_payload = load_reviewer_receipt(receipt_path)
        audit_payload = load_reviewer_write_scope_audit(audit_path)
        validate_reviewer_write_scope_audit(
            receipt_payload=receipt_payload,
            audit_payload=audit_payload,
            stage_dir=stage_dir,
        )
    except Exception as exc:
        return str(exc)
    return None


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
    author_formal_dir = _author_formal_dir(stage_dir)
    if not all((author_formal_dir / output_name).exists() for output_name in spec.required_outputs):
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


def _invoke_author_stage_without_autogen(lineage_root: Path, author_stage: SessionStage) -> list[str]:
    # 生产路径只执行已存在的作者 program，不做任何隐式补齐。
    if detect_session_stage(lineage_root) != author_stage:
        return []
    try:
        return _invoke_program_stage(lineage_root, author_stage)
    except StageProgramRuntimeError:
        return []


def _review_substate(
    *,
    stage_dir: Path,
    current_stage: SessionStage,
    lineage_root: Path,
) -> tuple[str, str, str, str]:
    request_path = _review_request_path(stage_dir)
    review_receipt = _load_reviewer_receipt_if_present(stage_dir)
    review_result = _load_adversarial_review_result_if_present(stage_dir)
    review_audit = _load_reviewer_write_scope_audit_if_present(stage_dir)
    proof_chain_error = _review_proof_chain_error(stage_dir)
    audit_error = _review_write_scope_audit_error(stage_dir)
    stage_base = _stage_base_name(current_stage)
    author_skill = STAGE_ACTIVE_SKILLS.get(f"{stage_base}_author", "qros-research-session")
    review_skill = STAGE_ACTIVE_SKILLS.get(current_stage, "qros-research-session")

    def _review_actor_label(receipt_payload: dict[str, Any]) -> str:
        if receipt_payload.get("execution_mode") == "review_session":
            return f"review session {receipt_payload['requested_reviewer_session_id']}"
        return f"reviewer agent {receipt_payload['reviewer_agent_id']}"

    if not request_path.exists():
        return (
            "awaiting_adversarial_review",
            "ADVERSARIAL_REVIEW_PENDING",
            f"{stage_base} is ready for independent adversarial review, but {ADVERSARIAL_REVIEW_REQUEST_FILENAME} is missing.",
            f"Enter {review_skill} in the current session; launch a reviewer agent, run ./.qros/bin/qros-review-cycle prepare for {stage_base}, and then wait for reviewer output.",
        )
    if review_receipt is None and proof_chain_error is not None:
        if REVIEWER_RECEIPT_FILENAME in proof_chain_error:
            return (
                "awaiting_adversarial_review",
                "ADVERSARIAL_REVIEW_PENDING",
                f"{stage_base} has reviewer artifacts on disk, but {REVIEWER_RECEIPT_FILENAME} is missing.",
                f"Reissue {REVIEWER_RECEIPT_FILENAME} via the runtime launcher before running {review_skill}.",
            )
        return (
            "awaiting_adversarial_review",
            "ADVERSARIAL_REVIEW_PENDING",
            f"{stage_base} has an invalid adversarial review request or handoff proof; the proof chain is invalid: {proof_chain_error}",
            f"Refresh {ADVERSARIAL_REVIEW_REQUEST_FILENAME} and the handoff manifest before launching a reviewer for {review_skill}.",
        )
    if review_result is None:
        if review_receipt is not None and proof_chain_error is not None:
            return (
                "awaiting_adversarial_review",
                "ADVERSARIAL_REVIEW_PENDING",
                f"{stage_base} has a reviewer receipt on disk, but the proof chain is invalid: {proof_chain_error}",
                f"Reissue {REVIEWER_RECEIPT_FILENAME} via the runtime launcher before running {review_skill}.",
            )
        if review_receipt is not None:
            actor_label = _review_actor_label(review_receipt)
            return (
                "awaiting_reviewer_completion",
                "ADVERSARIAL_REVIEW_PENDING",
                f"{stage_base} has an active {actor_label} and is waiting for it to write {ADVERSARIAL_REVIEW_RESULT_FILENAME}.",
                f"Wait for {actor_label} to finish and write {ADVERSARIAL_REVIEW_RESULT_FILENAME}, then rerun {review_skill}.",
            )
        return (
            "awaiting_adversarial_review",
            "ADVERSARIAL_REVIEW_PENDING",
            f"{stage_base} is waiting for a reviewer to register {REVIEWER_RECEIPT_FILENAME} before review can begin.",
            f"Enter {review_skill} in the current session, launch the reviewer, run ./.qros/bin/qros-review-cycle prepare, then wait for {ADVERSARIAL_REVIEW_RESULT_FILENAME}.",
        )
    if proof_chain_error is not None:
        return (
            "awaiting_adversarial_review",
            "ADVERSARIAL_REVIEW_PENDING",
            f"{stage_base} has reviewer artifacts on disk, but the reviewer proof chain is invalid: {proof_chain_error}",
            f"Reissue {REVIEWER_RECEIPT_FILENAME} via the runtime launcher, then rerun {review_skill}.",
        )
    if review_result["review_loop_outcome"] == FIX_REQUIRED_OUTCOME:
        return (
            "awaiting_author_fix",
            "AUTHOR_FIX_REQUIRED",
            f"{stage_base} received fixable adversarial review findings and must return to the author lane before closure.",
            f"Read review/result/review_findings.yaml and adversarial_review_result.yaml, then explicitly resume {author_skill}, refresh author/formal outputs, and later re-enter {review_skill} for a fresh reviewer cycle.",
        )
    if review_audit is None:
        return (
            "awaiting_reviewer_write_scope_audit",
            "REVIEW_AUDIT_PENDING",
            f"{stage_base} has a closure-ready review result, but {REVIEWER_WRITE_SCOPE_AUDIT_FILENAME} is still missing.",
            f"Run ./.qros/bin/qros-review to canonicalize findings, run write-scope audit, and write closure artifacts for {stage_base}.",
        )
    if audit_error is not None:
        return (
            "awaiting_reviewer_write_scope_audit",
            "REVIEW_AUDIT_FAILED",
            f"{stage_base} has a reviewer write-scope audit problem: {audit_error}",
            f"Discard the invalid review cycle, explicitly resume the author lane if needed, then re-enter {review_skill} for a fresh reviewer child cycle.",
        )
    if review_audit["audit_status"] != "PASS":
        return (
            "awaiting_reviewer_write_scope_audit",
            "REVIEW_AUDIT_FAILED",
            f"{stage_base} reviewer write-scope audit did not pass.",
            f"Inspect {REVIEWER_WRITE_SCOPE_AUDIT_FILENAME}, discard the invalid review cycle, and restart review by re-entering {review_skill}.",
        )
    return (
        "awaiting_review_closure",
        "REVIEW_CLOSURE_PENDING",
        f"{stage_base} has a closure-ready adversarial review result and is waiting for deterministic closure artifacts.",
        f"Run ./.qros/bin/qros-review to validate findings, run audit if needed, and write closure artifacts.",
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
        preflight_payload = _review_entry_preflight_payload(
            lineage_root=lineage_root,
            current_stage=current_stage,
        )
        preflight_findings = _review_entry_preflight_findings(preflight_payload)
        if preflight_findings:
            author_skill = STAGE_ACTIVE_SKILLS.get(f"{_stage_base_name(current_stage)}_author", "qros-research-session")
            return (
                "awaiting_author_fix",
                "OUTPUTS_INVALID",
                inspection.required_program_dir,
                inspection.required_program_entrypoint,
                inspection.program_contract_status,
                provenance_status,
                (
                    f"{_stage_base_name(current_stage)} author outputs failed deterministic review preflight: "
                    f"{_format_preflight_findings(preflight_findings)}"
                ),
                (
                    f"Run {author_skill} to repair author/formal outputs before review entry. "
                    f"Preflight findings: {_format_preflight_findings(preflight_findings)}"
                ),
            )
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
        # 关键生成逻辑：缺 program 时不做自动补齐，只把 Codex 要补写的 lineage-local 程序讲清楚。
        if _stage_base_name(current_stage) == "mandate":
            return (
                "awaiting_stage_program",
                "STAGE_PROGRAM_MISSING",
                inspection.required_program_dir,
                inspection.required_program_entrypoint,
                inspection.program_contract_status,
                provenance_status,
                inspection.error_message,
                f"Author the lineage-local stage program under {inspection.required_program_dir} before this stage can run.",
            )
        comment_requirement = _post_mandate_program_comment_requirement(current_stage)
        return (
            "awaiting_stage_program",
            "STAGE_PROGRAM_MISSING",
            inspection.required_program_dir,
            inspection.required_program_entrypoint,
            inspection.program_contract_status,
            provenance_status,
            (
                f"{inspection.error_message} Codex must explicitly author the lineage-local stage program "
                f"under {inspection.required_program_dir}{comment_requirement} before this stage can run."
            ),
            (
                f"Run {STAGE_ACTIVE_SKILLS.get(current_stage, 'qros-research-session')}; Codex must explicitly author "
                f"the lineage-local stage program under {inspection.required_program_dir}{comment_requirement}, then rerun qros-session "
                f"--lineage-id {lineage_root.name}."
            ),
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
    confirm_all_freeze_groups: bool = False,
    continue_mode: bool = False,
) -> SessionContext:
    selection = resolve_lineage_selection(outputs_root, lineage_id=lineage_id, raw_idea=raw_idea)
    lineage_root = selection.lineage_root
    if selection.resume_blocked:
        return _lineage_resume_blocked_status(selection=selection)
    lineage_root.mkdir(parents=True, exist_ok=True)
    try:
        assert_lineage_locks_intact(lineage_root)
    except FrozenArtifactMutationError as exc:
        return _lineage_lock_blocked_status(
            lineage_root=lineage_root,
            lineage_mode=selection.mode,
            lineage_selection_reason=selection.reason,
            violation=exc,
        )

    artifacts_written: list[str] = []
    current_stage = detect_session_stage(lineage_root)
    try:
        assert_current_protected_review_state_intact(
            lineage_root=lineage_root,
            current_stage=current_stage,
        )
    except ProtectedStateError as exc:
        return _protected_state_blocked_status(
            lineage_root=lineage_root,
            lineage_mode=selection.mode,
            lineage_selection_reason=selection.reason,
            violation=exc,
        )
    failure_package_status = _latest_failure_package_runtime_status(lineage_root)

    # 只有当前真正停在对应 confirmation gate，才允许把确认决策正式写盘。
    if failure_package_status is None and idea_intake_decision is not None and current_stage in {
        "idea_intake",
        "idea_intake_confirmation_pending",
    }:
        artifacts_written.append(
            write_idea_intake_transition_decision(lineage_root, decision=idea_intake_decision)
        )
        current_stage = detect_session_stage(lineage_root)
    if failure_package_status is None and mandate_decision is not None and current_stage == "mandate_confirmation_pending":
        validate_freeze_groups_for_stage_transition(lineage_root, current_stage)
        artifacts_written.append(
            write_mandate_transition_decision(lineage_root, decision=mandate_decision)
        )
        current_stage = detect_session_stage(lineage_root)
    if failure_package_status is None and data_ready_decision is not None and current_stage in {
        "data_ready_confirmation_pending",
        "csf_data_ready_confirmation_pending",
        "tss_data_ready_confirmation_pending",
    }:
        validate_freeze_groups_for_stage_transition(lineage_root, current_stage)
        artifacts_written.append(
            write_data_ready_transition_decision(lineage_root, decision=data_ready_decision)
        )
        current_stage = detect_session_stage(lineage_root)
    if failure_package_status is None and signal_ready_decision is not None and current_stage in {
        "signal_ready_confirmation_pending",
        "csf_signal_ready_confirmation_pending",
        "tss_signal_ready_confirmation_pending",
    }:
        validate_freeze_groups_for_stage_transition(lineage_root, current_stage)
        artifacts_written.append(
            write_signal_ready_transition_decision(lineage_root, decision=signal_ready_decision)
        )
        current_stage = detect_session_stage(lineage_root)
    if failure_package_status is None and train_freeze_decision is not None and current_stage in {
        "train_freeze_confirmation_pending",
        "csf_train_freeze_confirmation_pending",
        "tss_train_freeze_confirmation_pending",
    }:
        validate_freeze_groups_for_stage_transition(lineage_root, current_stage)
        artifacts_written.append(
            write_train_freeze_transition_decision(lineage_root, decision=train_freeze_decision)
        )
        current_stage = detect_session_stage(lineage_root)
    if failure_package_status is None and test_evidence_decision is not None and current_stage in {
        "test_evidence_confirmation_pending",
        "csf_test_evidence_confirmation_pending",
        "tss_test_evidence_confirmation_pending",
    }:
        validate_freeze_groups_for_stage_transition(lineage_root, current_stage)
        artifacts_written.append(
            write_test_evidence_transition_decision(lineage_root, decision=test_evidence_decision)
        )
        current_stage = detect_session_stage(lineage_root)
    if failure_package_status is None and backtest_ready_decision is not None and current_stage in {
        "backtest_ready_confirmation_pending",
        "csf_backtest_ready_confirmation_pending",
        "tss_backtest_ready_confirmation_pending",
    }:
        validate_freeze_groups_for_stage_transition(lineage_root, current_stage)
        artifacts_written.append(
            write_backtest_ready_transition_decision(lineage_root, decision=backtest_ready_decision)
        )
        current_stage = detect_session_stage(lineage_root)
    if failure_package_status is None and holdout_validation_decision is not None and current_stage in {
        "holdout_validation_confirmation_pending",
        "csf_holdout_validation_confirmation_pending",
        "tss_holdout_validation_confirmation_pending",
    }:
        validate_freeze_groups_for_stage_transition(lineage_root, current_stage)
        artifacts_written.append(
            write_holdout_validation_transition_decision(
                lineage_root, decision=holdout_validation_decision
            )
        )
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and review_decision is not None and current_stage.endswith("_review_confirmation_pending"):
        preflight_payload = _review_entry_preflight_payload(
            lineage_root=lineage_root,
            current_stage=current_stage,
        )
        if not _review_entry_preflight_findings(preflight_payload):
            written = write_review_transition_decision(
                lineage_root,
                current_stage=current_stage,
                decision=review_decision,
            )
            if written is not None:
                artifacts_written.append(written)
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and next_stage_decision is not None and current_stage.endswith("_next_stage_confirmation_pending"):
        written = write_next_stage_transition_decision(
            lineage_root,
            current_stage=current_stage,
            decision=next_stage_decision,
        )
        if written is not None:
            artifacts_written.append(written)
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and confirm_all_freeze_groups:
        artifacts_written.extend(ensure_freeze_draft_for_stage(lineage_root, current_stage))
        written = confirm_all_freeze_groups_for_current_stage(lineage_root, current_stage)
        if written is not None:
            artifacts_written.append(written)
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "idea_intake":
        artifacts_written.extend(ensure_intake_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "mandate_author":
        artifacts_written.extend(build_mandate_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "data_ready_confirmation_pending":
        artifacts_written.extend(ensure_data_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "data_ready_author":
        artifacts_written.extend(build_data_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "signal_ready_confirmation_pending":
        artifacts_written.extend(ensure_signal_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "signal_ready_author":
        artifacts_written.extend(build_signal_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "train_freeze_confirmation_pending":
        artifacts_written.extend(ensure_train_freeze_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "train_freeze_author":
        artifacts_written.extend(build_train_freeze_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "test_evidence_confirmation_pending":
        artifacts_written.extend(ensure_test_evidence_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "test_evidence_author":
        artifacts_written.extend(build_test_evidence_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "backtest_ready_confirmation_pending":
        artifacts_written.extend(ensure_backtest_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "backtest_ready_author":
        artifacts_written.extend(build_backtest_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "holdout_validation_confirmation_pending":
        artifacts_written.extend(ensure_holdout_validation_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "holdout_validation_author":
        artifacts_written.extend(build_holdout_validation_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_data_ready_confirmation_pending":
        artifacts_written.extend(ensure_csf_data_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_data_ready_author":
        artifacts_written.extend(build_csf_data_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_signal_ready_confirmation_pending":
        artifacts_written.extend(ensure_csf_signal_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_signal_ready_author":
        artifacts_written.extend(build_csf_signal_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_train_freeze_confirmation_pending":
        artifacts_written.extend(ensure_csf_train_freeze_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_train_freeze_author":
        artifacts_written.extend(build_csf_train_freeze_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_test_evidence_confirmation_pending":
        artifacts_written.extend(ensure_csf_test_evidence_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_test_evidence_author":
        artifacts_written.extend(build_csf_test_evidence_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_backtest_ready_confirmation_pending":
        artifacts_written.extend(ensure_csf_backtest_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_backtest_ready_author":
        artifacts_written.extend(build_csf_backtest_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_holdout_validation_confirmation_pending":
        artifacts_written.extend(ensure_csf_holdout_validation_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "csf_holdout_validation_author":
        artifacts_written.extend(build_csf_holdout_validation_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_data_ready_confirmation_pending":
        artifacts_written.extend(ensure_tss_data_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_data_ready_author":
        artifacts_written.extend(build_tss_data_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_signal_ready_confirmation_pending":
        artifacts_written.extend(ensure_tss_signal_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_signal_ready_author":
        artifacts_written.extend(build_tss_signal_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_train_freeze_confirmation_pending":
        artifacts_written.extend(ensure_tss_train_freeze_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_train_freeze_author":
        artifacts_written.extend(build_tss_train_freeze_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_test_evidence_confirmation_pending":
        artifacts_written.extend(ensure_tss_test_evidence_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_test_evidence_author":
        artifacts_written.extend(build_tss_test_evidence_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_backtest_ready_confirmation_pending":
        artifacts_written.extend(ensure_tss_backtest_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_backtest_ready_author":
        artifacts_written.extend(build_tss_backtest_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_holdout_validation_confirmation_pending":
        artifacts_written.extend(ensure_tss_holdout_validation_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if failure_package_status is None and current_stage == "tss_holdout_validation_author":
        artifacts_written.extend(build_tss_holdout_validation_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
    review_verdict, requires_failure_handling, failure_stage, failure_reason_summary = (
        _latest_review_failure_status(lineage_root)
    )
    if requires_failure_handling and failure_stage is not None:
        gate_status = "FAILURE_HANDLING_REQUIRED"
        next_action = f"Enter failure handling for {failure_stage} via qros-stage-failure-handler"
    if failure_package_status is not None:
        gate_status = failure_package_status.gate_status
        next_action = failure_package_status.next_action
        review_verdict = failure_package_status.review_verdict
        requires_failure_handling = True
        failure_stage = failure_package_status.failure_stage
        failure_reason_summary = failure_package_status.failure_reason_summary
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
        current_skill=failure_package_status.current_skill if failure_package_status else None,
        why_this_skill=failure_package_status.why_this_skill if failure_package_status else None,
        blocking_reason=failure_package_status.blocking_reason if failure_package_status else None,
        resume_hint=failure_package_status.resume_hint if failure_package_status else None,
        runtime_stage_status_override=failure_package_status.stage_status if failure_package_status else None,
        runtime_blocking_reason_code_override=(
            failure_package_status.blocking_reason_code if failure_package_status else None
        ),
        runtime_next_action_override=failure_package_status.next_action if failure_package_status else None,
        continue_mode=continue_mode,
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


def _tss_data_ready_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, TSS_DATA_READY_REQUIRED_OUTPUTS)


def _tss_signal_ready_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, TSS_SIGNAL_READY_REQUIRED_OUTPUTS)


def _tss_train_freeze_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, TSS_TRAIN_FREEZE_REQUIRED_OUTPUTS)


def _tss_test_evidence_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, TSS_TEST_EVIDENCE_REQUIRED_OUTPUTS)


def _tss_backtest_ready_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, TSS_BACKTEST_READY_REQUIRED_OUTPUTS)


def _tss_holdout_validation_outputs_complete(stage_dir: Path) -> bool:
    return stage_outputs_complete(stage_dir, TSS_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS)


def _completion_certificate_allows_progress(stage_dir: Path) -> bool:
    payload = _read_yaml(_review_closure_path(stage_dir, "stage_completion_certificate.yaml"))
    if not payload:
        return True

    stage_status = payload.get("stage_status") or payload.get("final_verdict")
    if stage_status in ADVANCING_COMPLETION_STATUSES:
        return True
    if stage_status in NON_ADVANCING_COMPLETION_STATUSES:
        return False
    return True


def _review_closure_complete(stage_dir: Path) -> bool:
    if _review_proof_chain_error(stage_dir) is not None:
        return False
    if _review_write_scope_audit_error(stage_dir) is not None:
        return False
    if _review_closure_path(stage_dir, "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(stage_dir)
    return all(_review_closure_path(stage_dir, name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _review_verdict_from_stage_dir(stage_dir: Path) -> str | None:
    certificate_path = _review_closure_path(stage_dir, "stage_completion_certificate.yaml")
    if not certificate_path.exists():
        return None

    payload = _read_yaml(certificate_path)
    if not payload:
        return None

    verdict = payload.get("stage_status") or payload.get("final_verdict")
    if isinstance(verdict, str) and verdict.strip():
        return verdict
    return None


def _stage_name_from_stage_dir(stage_dir: Path) -> str:
    name = stage_dir.name
    if len(name) > 3 and name[:2].isdigit() and name[2] == "_":
        return name[3:]
    return name


def _read_failure_disposition_decision(failure_package_dir: Path) -> str | None:
    disposition_path = failure_package_dir / "failure_disposition.yaml"
    if not disposition_path.exists():
        return None
    payload = _read_yaml(disposition_path)
    decision = payload.get("decision")
    if isinstance(decision, str) and decision.strip():
        return decision.strip()
    return None


def _latest_failure_package_runtime_status(lineage_root: Path) -> FailurePackageRuntimeStatus | None:
    candidates: list[tuple[float, Path, dict]] = []
    for post_retry_path in lineage_root.glob("*/failure_packages/*/post_retry_decision.yaml"):
        payload = _read_yaml(post_retry_path)
        if payload.get("normal_progression_allowed") is not False:
            continue
        candidates.append((post_retry_path.stat().st_mtime, post_retry_path, payload))
    if not candidates:
        return None

    _, post_retry_path, payload = max(candidates, key=lambda item: (item[0], str(item[1])))
    failure_package_dir = post_retry_path.parent
    stage_dir = failure_package_dir.parent.parent
    failed_stage = str(payload.get("failed_stage") or _stage_name_from_stage_dir(stage_dir))
    disposition_decision = _read_failure_disposition_decision(failure_package_dir)

    if disposition_decision is None:
        blocking_reason = (
            f"Latest failure package for {failed_stage} blocks normal progression until "
            "failure_disposition.yaml records NO_GO or CHILD_LINEAGE."
        )
        next_action = (
            f"Write {failure_package_dir.relative_to(lineage_root)}/failure_disposition.yaml with decision "
            "NO_GO or CHILD_LINEAGE before any review or next-stage action can continue."
        )
        return FailurePackageRuntimeStatus(
            stage_status="failure_disposition_required",
            blocking_reason_code="FAILURE_DISPOSITION_REQUIRED",
            gate_status="FAILURE_DISPOSITION_REQUIRED",
            current_skill="qros-stage-failure-handler",
            why_this_skill=(
                f"{failed_stage} has a blocking failure package after controlled retry, "
                "so failure disposition is the active workflow."
            ),
            blocking_reason=blocking_reason,
            next_action=next_action,
            resume_hint=(
                f"Use qros-stage-failure-handler for lineage {lineage_root.name} and record "
                f"{failure_package_dir.relative_to(lineage_root)}/failure_disposition.yaml, then rerun "
                f"qros-session --lineage-id {lineage_root.name}."
            ),
            review_verdict="FAILURE_DISPOSITION_REQUIRED",
            failure_stage=failed_stage,
            failure_reason_summary=blocking_reason,
        )

    blocking_reason = (
        f"{failed_stage} failure disposition {disposition_decision} is recorded; "
        "normal progression on the original lineage remains blocked."
    )
    next_action = (
        f"Formal failure disposition {disposition_decision} is recorded for {failed_stage}; "
        "the original lineage must not re-enter review or next-stage progression."
    )
    if disposition_decision == "CHILD_LINEAGE":
        next_action += " Open a child lineage before continuing research."
    return FailurePackageRuntimeStatus(
        stage_status="failure_disposition_recorded",
        blocking_reason_code="FAILURE_DISPOSITION_RECORDED",
        gate_status="FAILURE_DISPOSITION_RECORDED",
        current_skill="qros-lineage-change-control",
        why_this_skill=(
            f"{failed_stage} has formal failure disposition {disposition_decision}, "
            "so lineage change control is the active workflow."
        ),
        blocking_reason=blocking_reason,
        next_action=next_action,
        resume_hint=(
            f"Use qros-lineage-change-control for lineage {lineage_root.name}; do not resume ordinary "
            f"review or next-stage progression on {failed_stage}."
        ),
        review_verdict=disposition_decision,
        failure_stage=failed_stage,
        failure_reason_summary=blocking_reason,
    )


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
    elif _is_tss_route(lineage_root):
        review_stage_dirs = [
            ("tss_holdout_validation_review", lineage_root / "07_tss_holdout_validation", True),
            ("tss_backtest_ready_review", lineage_root / "06_tss_backtest_ready", True),
            ("tss_test_evidence_review", lineage_root / "05_tss_test_evidence", True),
            ("tss_train_freeze_review", lineage_root / "04_tss_train_freeze", True),
            ("tss_signal_ready_review", lineage_root / "03_tss_signal_ready", True),
            ("tss_data_ready_review", lineage_root / "02_tss_data_ready", True),
            ("holdout_validation_review", lineage_root / "07_holdout", True),
            ("backtest_ready_review", lineage_root / "06_backtest", True),
            ("test_evidence_review", lineage_root / "05_test_evidence", True),
            ("train_freeze_review", lineage_root / "04_train_freeze", True),
            ("signal_ready_review", lineage_root / "03_signal_ready", True),
            ("data_ready_review", lineage_root / "02_data_ready", True),
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
    if read_review_transition_decision(lineage_root, stage_base=stage_base) == "CONFIRM_REVIEW":
        return f"{stage_base}_review"  # type: ignore[return-value]
    if _review_has_started(stage_dir):
        return f"{stage_base}_review"  # type: ignore[return-value]
    return f"{stage_base}_review_confirmation_pending"  # type: ignore[return-value]


def _review_has_started(stage_dir: Path) -> bool:
    return any(
        path.exists()
        for path in (
            _review_request_path(stage_dir),
            _review_result_path(stage_dir),
            _review_closure_path(stage_dir, "stage_completion_certificate.yaml"),
        )
    )


def _post_review_completion_stage(lineage_root: Path, *, stage_base: str) -> SessionStage:
    next_stage_decision = read_next_stage_transition_decision(lineage_root, stage_base=stage_base)
    if next_stage_decision is None:
        return f"{stage_base}_next_stage_confirmation_pending"  # type: ignore[return-value]

    next_stage_base = _resolved_next_stage_base(lineage_root, stage_base)
    if next_stage_base is None:
        return f"{stage_base}_review_complete"  # type: ignore[return-value]

    return _next_stage_entry_state(lineage_root, next_stage_base=next_stage_base)


def _resolved_next_stage_base(lineage_root: Path, stage_base: str) -> str | None:
    if stage_base == "mandate":
        if _is_csf_route(lineage_root):
            return "csf_data_ready"
        if _is_tss_route(lineage_root):
            return "tss_data_ready"
    return NEXT_STAGE_BY_BASE[stage_base]


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
    if next_stage_base == "tss_data_ready":
        approval_decision = read_data_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_DATA_READY" and next_tss_data_ready_freeze_group(lineage_root) is None:
            return "tss_data_ready_author"
        return "tss_data_ready_confirmation_pending"
    if next_stage_base == "tss_signal_ready":
        approval_decision = read_signal_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_SIGNAL_READY" and next_tss_signal_ready_freeze_group(lineage_root) is None:
            return "tss_signal_ready_author"
        return "tss_signal_ready_confirmation_pending"
    if next_stage_base == "tss_train_freeze":
        approval_decision = read_train_freeze_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_TRAIN_FREEZE" and next_tss_train_freeze_group(lineage_root) is None:
            return "tss_train_freeze_author"
        return "tss_train_freeze_confirmation_pending"
    if next_stage_base == "tss_test_evidence":
        approval_decision = read_test_evidence_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_TEST_EVIDENCE" and next_tss_test_evidence_group(lineage_root) is None:
            return "tss_test_evidence_author"
        return "tss_test_evidence_confirmation_pending"
    if next_stage_base == "tss_backtest_ready":
        approval_decision = read_backtest_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_BACKTEST_READY" and next_tss_backtest_ready_group(lineage_root) is None:
            return "tss_backtest_ready_author"
        return "tss_backtest_ready_confirmation_pending"
    if next_stage_base == "tss_holdout_validation":
        approval_decision = read_holdout_validation_transition_decision(lineage_root)
        if (
            approval_decision == "CONFIRM_HOLDOUT_VALIDATION"
            and next_tss_holdout_validation_group(lineage_root) is None
        ):
            return "tss_holdout_validation_author"
        return "tss_holdout_validation_confirmation_pending"
    raise ValueError(f"Unsupported next stage base: {next_stage_base}")


def _mandate_closure_complete(mandate_dir: Path) -> bool:
    return _review_closure_complete(mandate_dir)


def _data_ready_closure_complete(data_ready_dir: Path) -> bool:
    return _review_closure_complete(data_ready_dir)


def _csf_data_ready_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _signal_ready_closure_complete(signal_ready_dir: Path) -> bool:
    return _review_closure_complete(signal_ready_dir)


def _csf_signal_ready_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _train_freeze_closure_complete(train_dir: Path) -> bool:
    return _review_closure_complete(train_dir)


def _csf_train_freeze_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _test_evidence_closure_complete(test_dir: Path) -> bool:
    return _review_closure_complete(test_dir)


def _csf_test_evidence_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _backtest_ready_closure_complete(backtest_dir: Path) -> bool:
    return _review_closure_complete(backtest_dir)


def _csf_backtest_ready_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _holdout_validation_closure_complete(holdout_dir: Path) -> bool:
    return _review_closure_complete(holdout_dir)


def _csf_holdout_validation_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _tss_data_ready_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _tss_signal_ready_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _tss_train_freeze_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _tss_test_evidence_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _tss_backtest_ready_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _tss_holdout_validation_closure_complete(stage_dir: Path) -> bool:
    return _review_closure_complete(stage_dir)


def _review_gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str]:
    stage_dir = _stage_dir_for_session_stage(lineage_root, current_stage)
    review_skill = STAGE_ACTIVE_SKILLS.get(current_stage, "qros-review")
    if stage_dir is None:
        return "REVIEW_PENDING", "Complete the review workflow."
    request_exists = _review_request_path(stage_dir).exists()
    receipt_exists = _review_receipt_path(stage_dir).exists()
    review_result = _load_adversarial_review_result_if_present(stage_dir)
    review_audit = _load_reviewer_write_scope_audit_if_present(stage_dir)
    proof_chain_error = _review_proof_chain_error(stage_dir)
    audit_error = _review_write_scope_audit_error(stage_dir)
    if not request_exists:
        return (
            "ADVERSARIAL_REVIEW_PENDING",
            f"Enter {review_skill} in the current session; launch a reviewer and run ./.qros/bin/qros-review-cycle prepare to register the active review cycle.",
        )
    if not receipt_exists and proof_chain_error is not None:
        if REVIEWER_RECEIPT_FILENAME in proof_chain_error:
            return (
                "ADVERSARIAL_REVIEW_PENDING",
                f"Reissue {REVIEWER_RECEIPT_FILENAME} via the runtime launcher before producing {ADVERSARIAL_REVIEW_RESULT_FILENAME}; proof chain validation failed.",
            )
        return (
            "ADVERSARIAL_REVIEW_PENDING",
            f"Refresh {ADVERSARIAL_REVIEW_REQUEST_FILENAME} and the handoff manifest before launching a reviewer; proof chain validation failed.",
        )
    if not receipt_exists:
        return (
            "ADVERSARIAL_REVIEW_PENDING",
            f"Launch a reviewer, issue {REVIEWER_RECEIPT_FILENAME}, then wait for "
            f"{ADVERSARIAL_REVIEW_RESULT_FILENAME}.",
        )
    if review_result is None:
        if receipt_exists and proof_chain_error is not None:
            return (
                "ADVERSARIAL_REVIEW_PENDING",
                f"Reissue {REVIEWER_RECEIPT_FILENAME} via the runtime launcher before producing "
                f"{ADVERSARIAL_REVIEW_RESULT_FILENAME}; proof chain validation failed.",
            )
        review_receipt = _load_reviewer_receipt_if_present(stage_dir)
        if review_receipt is not None:
            return (
                "ADVERSARIAL_REVIEW_PENDING",
                f"Wait for reviewer agent {review_receipt['reviewer_agent_id']} to produce {ADVERSARIAL_REVIEW_RESULT_FILENAME}.",
            )
        return (
            "ADVERSARIAL_REVIEW_PENDING",
            f"Wait for the reviewer recorded in {REVIEWER_RECEIPT_FILENAME} to produce {ADVERSARIAL_REVIEW_RESULT_FILENAME}.",
        )
    if proof_chain_error is not None:
        return (
            "ADVERSARIAL_REVIEW_PENDING",
            f"Reissue {REVIEWER_RECEIPT_FILENAME} via the runtime launcher and regenerate "
            f"{ADVERSARIAL_REVIEW_RESULT_FILENAME}; proof chain validation failed.",
        )
    if review_result["review_loop_outcome"] == FIX_REQUIRED_OUTCOME:
        return (
            "AUTHOR_FIX_REQUIRED",
            f"Read review/result/review_findings.yaml and adversarial_review_result.yaml, explicitly resume the author lane, refresh author/formal outputs, then re-enter {review_skill} for a fresh reviewer cycle.",
        )
    if review_audit is None:
        return (
            "REVIEW_AUDIT_PENDING",
            "Run ./.qros/bin/qros-review to canonicalize findings, execute audit, and write deterministic closure artifacts.",
        )
    if audit_error is not None or review_audit["audit_status"] != "PASS":
        return (
            "REVIEW_AUDIT_FAILED",
            f"Reviewer write-scope audit failed; inspect {REVIEWER_WRITE_SCOPE_AUDIT_FILENAME} and discard the invalid review cycle.",
        )
    return (
        "REVIEW_CLOSURE_PENDING",
        "Run ./.qros/bin/qros-review to complete deterministic review closure.",
    )


def _next_stage_gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str]:
    stage_base = _stage_base_name(current_stage)
    next_stage_base = _display_next_stage_base(lineage_root, stage_base)
    if next_stage_base is None:
        return (
            "NEXT_STAGE_CONFIRMATION_PENDING",
            "Run with --confirm-next-stage to mark the session complete.",
        )
    return (
        "NEXT_STAGE_CONFIRMATION_PENDING",
        f"Run with --confirm-next-stage or reply CONFIRM_NEXT_STAGE <lineage_id> to enter {next_stage_base}.",
    )


def _display_next_stage_base(lineage_root: Path, stage_base: str) -> str | None:
    if stage_base == "mandate" and _is_tss_route(lineage_root):
        return "tss_data_ready"
    return NEXT_STAGE_BY_BASE[stage_base]


def _tss_gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str] | None:
    specs = {
        "tss_data_ready": (
            next_tss_data_ready_freeze_group,
            read_data_ready_transition_decision,
            "CONFIRM_DATA_READY",
            "GO_TO_TSS_DATA_READY",
            "data-ready",
        ),
        "tss_signal_ready": (
            next_tss_signal_ready_freeze_group,
            read_signal_ready_transition_decision,
            "CONFIRM_SIGNAL_READY",
            "GO_TO_TSS_SIGNAL_READY",
            "signal-ready",
        ),
        "tss_train_freeze": (
            next_tss_train_freeze_group,
            read_train_freeze_transition_decision,
            "CONFIRM_TRAIN_FREEZE",
            "GO_TO_TSS_TRAIN_FREEZE",
            "train-freeze",
        ),
        "tss_test_evidence": (
            next_tss_test_evidence_group,
            read_test_evidence_transition_decision,
            "CONFIRM_TEST_EVIDENCE",
            "GO_TO_TSS_TEST_EVIDENCE",
            "test-evidence",
        ),
        "tss_backtest_ready": (
            next_tss_backtest_ready_group,
            read_backtest_ready_transition_decision,
            "CONFIRM_BACKTEST_READY",
            "GO_TO_TSS_BACKTEST_READY",
            "backtest-ready",
        ),
        "tss_holdout_validation": (
            next_tss_holdout_validation_group,
            read_holdout_validation_transition_decision,
            "CONFIRM_HOLDOUT_VALIDATION",
            "GO_TO_TSS_HOLDOUT_VALIDATION",
            "holdout-validation",
        ),
    }
    stage_base = _stage_base_name(current_stage)
    spec = specs.get(stage_base)
    if spec is None:
        return None
    next_group_fn, decision_fn, confirm_value, code_prefix, cli_suffix = spec

    if current_stage == f"{stage_base}_confirmation_pending":
        next_group = next_group_fn(lineage_root)
        if next_group is not None:
            return f"{code_prefix}_PENDING_CONFIRMATION", _all_freeze_groups_next_action(stage_base)
        decision = decision_fn(lineage_root)
        if decision == "HOLD":
            return f"{code_prefix}_ON_HOLD", f"Wait for explicit {confirm_value}"
        return (
            f"{code_prefix}_PENDING_CONFIRMATION",
            f"Run with --confirm-{cli_suffix} or reply {confirm_value} <lineage_id>",
        )
    if current_stage == f"{stage_base}_author":
        return f"{code_prefix}_CONFIRMED", f"Freeze {stage_base} artifacts"
    if current_stage == f"{stage_base}_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)
    return None


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
        review_skill = STAGE_ACTIVE_SKILLS.get(current_stage, "qros-review")
        return (
            "REVIEW_CONFIRMATION_PENDING",
            f"Enter {review_skill} in the current session. That stage-specific review skill should launch a reviewer, run ./.qros/bin/qros-review-cycle prepare, and then complete review with ./.qros/bin/qros-review.",
        )


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
            return "GO_TO_MANDATE_PENDING_CONFIRMATION", _all_freeze_groups_next_action("mandate")
        decision = read_mandate_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_MANDATE_ON_HOLD", "Wait for explicit CONFIRM_MANDATE"
        return "GO_TO_MANDATE_PENDING_CONFIRMATION", "Run with --confirm-mandate or reply CONFIRM_MANDATE <lineage_id>"

    if current_stage == "mandate_author":
        return "GO_TO_MANDATE_CONFIRMED", "Freeze mandate artifacts"

    if current_stage == "mandate_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "mandate_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    tss_gate_status = _tss_gate_status_and_next_action(lineage_root, current_stage)
    if tss_gate_status is not None:
        return tss_gate_status

    if current_stage == "csf_data_ready_confirmation_pending":
        next_group = next_csf_data_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_DATA_READY_PENDING_CONFIRMATION", _all_freeze_groups_next_action("csf_data_ready")
        decision = read_data_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_DATA_READY_ON_HOLD", "Wait for explicit CONFIRM_DATA_READY"
        return "GO_TO_CSF_DATA_READY_PENDING_CONFIRMATION", "Run with --confirm-data-ready or reply CONFIRM_DATA_READY <lineage_id>"

    if current_stage == "csf_data_ready_author":
        return "GO_TO_CSF_DATA_READY_CONFIRMED", "Freeze csf_data_ready artifacts"

    if current_stage == "csf_data_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "csf_data_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "data_ready_confirmation_pending":
        next_group = next_data_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_DATA_READY_PENDING_CONFIRMATION", _all_freeze_groups_next_action("data_ready")
        decision = read_data_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_DATA_READY_ON_HOLD", "Wait for explicit CONFIRM_DATA_READY"
        return "GO_TO_DATA_READY_PENDING_CONFIRMATION", "Run with --confirm-data-ready or reply CONFIRM_DATA_READY <lineage_id>"

    if current_stage == "data_ready_author":
        return "GO_TO_DATA_READY_CONFIRMED", "Freeze data_ready artifacts"

    if current_stage == "data_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "data_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "signal_ready_confirmation_pending":
        next_group = next_signal_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_SIGNAL_READY_PENDING_CONFIRMATION", _all_freeze_groups_next_action("signal_ready")
        decision = read_signal_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_SIGNAL_READY_ON_HOLD", "Wait for explicit CONFIRM_SIGNAL_READY"
        return "GO_TO_SIGNAL_READY_PENDING_CONFIRMATION", "Run with --confirm-signal-ready or reply CONFIRM_SIGNAL_READY <lineage_id>"

    if current_stage == "signal_ready_author":
        return "GO_TO_SIGNAL_READY_CONFIRMED", "Freeze signal_ready artifacts"

    if current_stage == "signal_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "signal_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_signal_ready_confirmation_pending":
        next_group = next_csf_signal_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_SIGNAL_READY_PENDING_CONFIRMATION", _all_freeze_groups_next_action("csf_signal_ready")
        decision = read_signal_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_SIGNAL_READY_ON_HOLD", "Wait for explicit CONFIRM_SIGNAL_READY"
        return "GO_TO_CSF_SIGNAL_READY_PENDING_CONFIRMATION", "Run with --confirm-signal-ready or reply CONFIRM_SIGNAL_READY <lineage_id>"

    if current_stage == "csf_signal_ready_author":
        return "GO_TO_CSF_SIGNAL_READY_CONFIRMED", "Freeze csf_signal_ready artifacts"

    if current_stage == "csf_signal_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "csf_signal_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "train_freeze_confirmation_pending":
        next_group = next_train_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_TRAIN_FREEZE_PENDING_CONFIRMATION", _all_freeze_groups_next_action("train_freeze")
        decision = read_train_freeze_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_TRAIN_FREEZE_ON_HOLD", "Wait for explicit CONFIRM_TRAIN_FREEZE"
        return "GO_TO_TRAIN_FREEZE_PENDING_CONFIRMATION", "Run with --confirm-train-freeze or reply CONFIRM_TRAIN_FREEZE <lineage_id>"

    if current_stage == "train_freeze_author":
        return "GO_TO_TRAIN_FREEZE_CONFIRMED", "Freeze train_freeze artifacts"

    if current_stage == "train_freeze_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "train_freeze_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_train_freeze_confirmation_pending":
        next_group = next_csf_train_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_TRAIN_FREEZE_PENDING_CONFIRMATION", _all_freeze_groups_next_action("csf_train_freeze")
        decision = read_train_freeze_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_TRAIN_FREEZE_ON_HOLD", "Wait for explicit CONFIRM_TRAIN_FREEZE"
        return "GO_TO_CSF_TRAIN_FREEZE_PENDING_CONFIRMATION", "Run with --confirm-train-freeze or reply CONFIRM_TRAIN_FREEZE <lineage_id>"

    if current_stage == "csf_train_freeze_author":
        return "GO_TO_CSF_TRAIN_FREEZE_CONFIRMED", "Freeze csf_train_freeze artifacts"

    if current_stage == "csf_train_freeze_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "csf_train_freeze_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "test_evidence_confirmation_pending":
        next_group = next_test_evidence_group(lineage_root)
        if next_group is not None:
            return "GO_TO_TEST_EVIDENCE_PENDING_CONFIRMATION", _all_freeze_groups_next_action("test_evidence")
        decision = read_test_evidence_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_TEST_EVIDENCE_ON_HOLD", "Wait for explicit CONFIRM_TEST_EVIDENCE"
        return "GO_TO_TEST_EVIDENCE_PENDING_CONFIRMATION", "Run with --confirm-test-evidence or reply CONFIRM_TEST_EVIDENCE <lineage_id>"

    if current_stage == "test_evidence_author":
        return "GO_TO_TEST_EVIDENCE_CONFIRMED", "Freeze test_evidence artifacts"

    if current_stage == "test_evidence_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "test_evidence_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_test_evidence_confirmation_pending":
        next_group = next_csf_test_evidence_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_TEST_EVIDENCE_PENDING_CONFIRMATION", _all_freeze_groups_next_action("csf_test_evidence")
        decision = read_test_evidence_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_TEST_EVIDENCE_ON_HOLD", "Wait for explicit CONFIRM_TEST_EVIDENCE"
        return "GO_TO_CSF_TEST_EVIDENCE_PENDING_CONFIRMATION", "Run with --confirm-test-evidence or reply CONFIRM_TEST_EVIDENCE <lineage_id>"

    if current_stage == "csf_test_evidence_author":
        return "GO_TO_CSF_TEST_EVIDENCE_CONFIRMED", "Freeze csf_test_evidence artifacts"

    if current_stage == "csf_test_evidence_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "csf_test_evidence_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "backtest_ready_confirmation_pending":
        next_group = next_backtest_ready_group(lineage_root)
        if next_group is not None:
            return "GO_TO_BACKTEST_READY_PENDING_CONFIRMATION", _all_freeze_groups_next_action("backtest_ready")
        decision = read_backtest_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_BACKTEST_READY_ON_HOLD", "Wait for explicit CONFIRM_BACKTEST_READY"
        return "GO_TO_BACKTEST_READY_PENDING_CONFIRMATION", "Run with --confirm-backtest-ready or reply CONFIRM_BACKTEST_READY <lineage_id>"

    if current_stage == "backtest_ready_author":
        return "GO_TO_BACKTEST_READY_CONFIRMED", "Freeze backtest_ready artifacts"

    if current_stage == "backtest_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "backtest_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "csf_backtest_ready_confirmation_pending":
        next_group = next_csf_backtest_ready_group(lineage_root)
        if next_group is not None:
            return "GO_TO_CSF_BACKTEST_READY_PENDING_CONFIRMATION", _all_freeze_groups_next_action("csf_backtest_ready")
        decision = read_backtest_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_CSF_BACKTEST_READY_ON_HOLD", "Wait for explicit CONFIRM_BACKTEST_READY"
        return "GO_TO_CSF_BACKTEST_READY_PENDING_CONFIRMATION", "Run with --confirm-backtest-ready or reply CONFIRM_BACKTEST_READY <lineage_id>"

    if current_stage == "csf_backtest_ready_author":
        return "GO_TO_CSF_BACKTEST_READY_CONFIRMED", "Freeze csf_backtest_ready artifacts"

    if current_stage == "csf_backtest_ready_review":
        return _review_gate_status_and_next_action(lineage_root, current_stage)


    if current_stage == "csf_backtest_ready_next_stage_confirmation_pending":
        return _next_stage_gate_status_and_next_action(lineage_root, current_stage)

    if current_stage == "holdout_validation_confirmation_pending":
        next_group = next_holdout_validation_group(lineage_root)
        if next_group is not None:
            return (
                "GO_TO_HOLDOUT_VALIDATION_PENDING_CONFIRMATION",
                _all_freeze_groups_next_action("holdout_validation"),
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


    if current_stage == "csf_holdout_validation_confirmation_pending":
        next_group = next_csf_holdout_validation_group(lineage_root)
        if next_group is not None:
            return (
                "GO_TO_CSF_HOLDOUT_VALIDATION_PENDING_CONFIRMATION",
                _all_freeze_groups_next_action("csf_holdout_validation"),
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


    return "REVIEW_COMPLETE", "Stop here. holdout_validation review is the current terminal stage."


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


def _freeze_draft_path(lineage_root: Path, current_stage: SessionStage) -> Path:
    spec = FREEZE_DRAFT_STAGE_SPECS[current_stage]
    path_parts, filename, _, _ = spec
    draft_dir = lineage_root.joinpath(*path_parts)
    return draft_dir / filename


def _optional_payload_value(value: object) -> str | None:
    normalized = str(value).strip()
    return normalized or None


def _is_csf_route(lineage_root: Path) -> bool:
    return current_research_route(lineage_root) == "cross_sectional_factor"


def _is_tss_route(lineage_root: Path) -> bool:
    return current_research_route(lineage_root) == "time_series_signal"


def _idea_intake_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "00_idea_intake" / IDEA_INTAKE_TRANSITION_APPROVAL_FILE


def _approval_path(lineage_root: Path) -> Path:
    return lineage_root / "00_idea_intake" / MANDATE_TRANSITION_APPROVAL_FILE


def _data_ready_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "02_csf_data_ready" / "author" / "draft" / DATA_READY_TRANSITION_APPROVAL_FILE
    if _is_tss_route(lineage_root):
        return lineage_root / "02_tss_data_ready" / "author" / "draft" / DATA_READY_TRANSITION_APPROVAL_FILE
    return lineage_root / "02_data_ready" / "author" / "draft" / DATA_READY_TRANSITION_APPROVAL_FILE


def _signal_ready_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "03_csf_signal_ready" / "author" / "draft" / SIGNAL_READY_TRANSITION_APPROVAL_FILE
    if _is_tss_route(lineage_root):
        return lineage_root / "03_tss_signal_ready" / "author" / "draft" / SIGNAL_READY_TRANSITION_APPROVAL_FILE
    return lineage_root / "03_signal_ready" / "author" / "draft" / SIGNAL_READY_TRANSITION_APPROVAL_FILE


def _train_freeze_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "04_csf_train_freeze" / "author" / "draft" / TRAIN_FREEZE_TRANSITION_APPROVAL_FILE
    if _is_tss_route(lineage_root):
        return lineage_root / "04_tss_train_freeze" / "author" / "draft" / TRAIN_FREEZE_TRANSITION_APPROVAL_FILE
    return lineage_root / "04_train_freeze" / "author" / "draft" / TRAIN_FREEZE_TRANSITION_APPROVAL_FILE


def _test_evidence_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "05_csf_test_evidence" / "author" / "draft" / TEST_EVIDENCE_TRANSITION_APPROVAL_FILE
    if _is_tss_route(lineage_root):
        return lineage_root / "05_tss_test_evidence" / "author" / "draft" / TEST_EVIDENCE_TRANSITION_APPROVAL_FILE
    return lineage_root / "05_test_evidence" / "author" / "draft" / TEST_EVIDENCE_TRANSITION_APPROVAL_FILE


def _backtest_ready_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "06_csf_backtest_ready" / "author" / "draft" / BACKTEST_READY_TRANSITION_APPROVAL_FILE
    if _is_tss_route(lineage_root):
        return lineage_root / "06_tss_backtest_ready" / "author" / "draft" / BACKTEST_READY_TRANSITION_APPROVAL_FILE
    return lineage_root / "06_backtest" / "author" / "draft" / BACKTEST_READY_TRANSITION_APPROVAL_FILE


def _holdout_validation_approval_path(lineage_root: Path) -> Path:
    if _is_csf_route(lineage_root):
        return lineage_root / "07_csf_holdout_validation" / "author" / "draft" / HOLDOUT_VALIDATION_TRANSITION_APPROVAL_FILE
    if _is_tss_route(lineage_root):
        return lineage_root / "07_tss_holdout_validation" / "author" / "draft" / HOLDOUT_VALIDATION_TRANSITION_APPROVAL_FILE
    return lineage_root / "07_holdout" / "author" / "draft" / HOLDOUT_VALIDATION_TRANSITION_APPROVAL_FILE


def _stage_dir_for_stage_base(lineage_root: Path, stage_base: str) -> Path | None:
    spec = SESSION_STAGE_PROGRAM_SPECS.get(stage_base)
    if spec is None:
        return None
    return lineage_root / spec.stage_dir_name


def _review_transition_approval_path(lineage_root: Path, stage_base: str) -> Path | None:
    stage_dir = _stage_dir_for_stage_base(lineage_root, stage_base)
    if stage_dir is None:
        return None
    return _author_draft_dir(stage_dir) / REVIEW_TRANSITION_APPROVAL_FILE


def _next_stage_transition_approval_path(lineage_root: Path, stage_base: str) -> Path | None:
    stage_dir = _stage_dir_for_stage_base(lineage_root, stage_base)
    if stage_dir is None:
        return None
    return _author_draft_dir(stage_dir) / NEXT_STAGE_TRANSITION_APPROVAL_FILE
