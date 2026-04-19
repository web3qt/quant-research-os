from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    FIX_REQUIRED_OUTCOME,
    SPAWNED_REVIEWER_RECEIPT_FILENAME,
    load_adversarial_review_result,
)
from runtime.tools.review_skillgen.review_findings import load_review_findings_if_present
from runtime.tools.review_skillgen.review_freshness import review_cycle_stale_reason
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    REVIEWER_WRITE_SCOPE_AUDIT_FILENAME,
    load_reviewer_write_scope_audit,
)


ROOT = Path(__file__).resolve().parents[2]
STAGE_EVALUATOR_SCHEMA_VERSION = 1
STAGE_EVALUATOR_FILENAME = "stage_evaluator.json"
STAGE_EVALUATOR_RESULTS_FILENAME = "stage_evaluator_results.jsonl"


@dataclass(frozen=True)
class StageEvaluatorSpec:
    stage: str
    stage_dir_name: str
    route_family: str
    required_outputs: tuple[str, ...]
    artifact_root_kind: str
    reviewable: bool


IDEA_INTAKE_REQUIRED_OUTPUTS = (
    "idea_brief.md",
    "observation_hypothesis_map.md",
    "research_question_set.md",
    "scope_canvas.yaml",
    "qualification_scorecard.yaml",
    "idea_gate_decision.yaml",
    "artifact_catalog.md",
)

MANDATE_REQUIRED_OUTPUTS = (
    "mandate.md",
    "research_scope.md",
    "research_route.yaml",
    "time_split.json",
    "parameter_grid.yaml",
    "run_config.toml",
    "artifact_catalog.md",
    "field_dictionary.md",
)

DATA_READY_REQUIRED_OUTPUTS = (
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
)

SIGNAL_READY_REQUIRED_OUTPUTS = (
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
)

TRAIN_FREEZE_REQUIRED_OUTPUTS = (
    "train_thresholds.json",
    "train_quality.parquet",
    "train_param_ledger.csv",
    "train_rejects.csv",
    "train_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
)

TEST_EVIDENCE_REQUIRED_OUTPUTS = (
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
)

BACKTEST_READY_REQUIRED_OUTPUTS = (
    "engine_compare.csv",
    "vectorbt",
    "backtrader",
    "strategy_combo_ledger.csv",
    "capacity_review.md",
    "backtest_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
)

HOLDOUT_VALIDATION_REQUIRED_OUTPUTS = (
    "holdout_run_manifest.json",
    "holdout_backtest_compare.csv",
    "window_results",
    "holdout_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
)

CSF_DATA_READY_REQUIRED_OUTPUTS = (
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
)

CSF_SIGNAL_READY_REQUIRED_OUTPUTS = (
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
)

CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS = (
    "csf_train_freeze.yaml",
    "train_factor_quality.parquet",
    "train_variant_ledger.csv",
    "train_variant_rejects.csv",
    "train_bucket_diagnostics.parquet",
    "train_neutralization_diagnostics.parquet",
    "csf_train_contract.md",
    "artifact_catalog.md",
    "field_dictionary.md",
)

CSF_TEST_EVIDENCE_REQUIRED_OUTPUTS = (
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
)

CSF_BACKTEST_READY_REQUIRED_OUTPUTS = (
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
)

CSF_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS = (
    "csf_holdout_run_manifest.json",
    "holdout_factor_diagnostics.parquet",
    "holdout_test_compare.parquet",
    "holdout_portfolio_compare.csv",
    "rolling_holdout_stability.json",
    "regime_shift_audit.json",
    "csf_holdout_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
)

NON_ADVANCING_COMPLETION_STATUSES = {"PASS FOR RETRY", "RETRY", "NO-GO", "CHILD LINEAGE"}

STAGE_EVALUATOR_SPECS: dict[str, StageEvaluatorSpec] = {
    "00_idea_intake": StageEvaluatorSpec(
        stage="idea_intake",
        stage_dir_name="00_idea_intake",
        route_family="route_neutral",
        required_outputs=IDEA_INTAKE_REQUIRED_OUTPUTS,
        artifact_root_kind="stage_root",
        reviewable=False,
    ),
    "01_mandate": StageEvaluatorSpec(
        stage="mandate",
        stage_dir_name="01_mandate",
        route_family="route_neutral",
        required_outputs=tuple(MANDATE_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "02_data_ready": StageEvaluatorSpec(
        stage="data_ready",
        stage_dir_name="02_data_ready",
        route_family="time_series_signal",
        required_outputs=tuple(DATA_READY_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "03_signal_ready": StageEvaluatorSpec(
        stage="signal_ready",
        stage_dir_name="03_signal_ready",
        route_family="time_series_signal",
        required_outputs=tuple(SIGNAL_READY_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "04_train_freeze": StageEvaluatorSpec(
        stage="train_freeze",
        stage_dir_name="04_train_freeze",
        route_family="time_series_signal",
        required_outputs=tuple(TRAIN_FREEZE_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "05_test_evidence": StageEvaluatorSpec(
        stage="test_evidence",
        stage_dir_name="05_test_evidence",
        route_family="time_series_signal",
        required_outputs=tuple(TEST_EVIDENCE_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "06_backtest": StageEvaluatorSpec(
        stage="backtest_ready",
        stage_dir_name="06_backtest",
        route_family="time_series_signal",
        required_outputs=tuple(BACKTEST_READY_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "07_holdout": StageEvaluatorSpec(
        stage="holdout_validation",
        stage_dir_name="07_holdout",
        route_family="time_series_signal",
        required_outputs=tuple(HOLDOUT_VALIDATION_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "02_csf_data_ready": StageEvaluatorSpec(
        stage="csf_data_ready",
        stage_dir_name="02_csf_data_ready",
        route_family="cross_sectional_factor",
        required_outputs=tuple(CSF_DATA_READY_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "03_csf_signal_ready": StageEvaluatorSpec(
        stage="csf_signal_ready",
        stage_dir_name="03_csf_signal_ready",
        route_family="cross_sectional_factor",
        required_outputs=tuple(CSF_SIGNAL_READY_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "04_csf_train_freeze": StageEvaluatorSpec(
        stage="csf_train_freeze",
        stage_dir_name="04_csf_train_freeze",
        route_family="cross_sectional_factor",
        required_outputs=tuple(CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "05_csf_test_evidence": StageEvaluatorSpec(
        stage="csf_test_evidence",
        stage_dir_name="05_csf_test_evidence",
        route_family="cross_sectional_factor",
        required_outputs=tuple(CSF_TEST_EVIDENCE_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "06_csf_backtest_ready": StageEvaluatorSpec(
        stage="csf_backtest_ready",
        stage_dir_name="06_csf_backtest_ready",
        route_family="cross_sectional_factor",
        required_outputs=tuple(CSF_BACKTEST_READY_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
    "07_csf_holdout_validation": StageEvaluatorSpec(
        stage="csf_holdout_validation",
        stage_dir_name="07_csf_holdout_validation",
        route_family="cross_sectional_factor",
        required_outputs=tuple(CSF_HOLDOUT_VALIDATION_REQUIRED_OUTPUTS),
        artifact_root_kind="author_formal",
        reviewable=True,
    ),
}

STAGE_EVALUATOR_SPEC_ALIASES: dict[str, str] = {
    "idea_intake": "00_idea_intake",
    "mandate": "01_mandate",
    "data_ready": "02_data_ready",
    "signal_ready": "03_signal_ready",
    "train_freeze": "04_train_freeze",
    "test_evidence": "05_test_evidence",
    "backtest_ready": "06_backtest",
    "holdout_validation": "07_holdout",
    "csf_data_ready": "02_csf_data_ready",
    "csf_signal_ready": "03_csf_signal_ready",
    "csf_train_freeze": "04_csf_train_freeze",
    "csf_test_evidence": "05_csf_test_evidence",
    "csf_backtest_ready": "06_csf_backtest_ready",
    "csf_holdout_validation": "07_csf_holdout_validation",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_yaml_if_present(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _spec_for_stage_dir(stage_dir: Path) -> StageEvaluatorSpec:
    alias = STAGE_EVALUATOR_SPEC_ALIASES.get(stage_dir.name)
    if alias is not None:
        return STAGE_EVALUATOR_SPECS[alias]
    try:
        return STAGE_EVALUATOR_SPECS[stage_dir.name]
    except KeyError as exc:
        raise ValueError(f"Unsupported stage directory for evaluator: {stage_dir}") from exc


def _artifact_root(stage_dir: Path, spec: StageEvaluatorSpec) -> Path:
    if spec.artifact_root_kind == "stage_root":
        return stage_dir
    if spec.artifact_root_kind == "author_formal":
        return stage_dir / "author" / "formal"
    raise ValueError(f"Unsupported artifact_root_kind: {spec.artifact_root_kind}")


def _evaluation_dir(stage_dir: Path) -> Path:
    return stage_dir / "evaluation"


def _review_transition_confirmed(stage_dir: Path) -> bool:
    return (stage_dir / "author" / "draft" / "review_transition_approval.yaml").exists()


def _review_request_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME


def _review_receipt_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "request" / SPAWNED_REVIEWER_RECEIPT_FILENAME


def _review_result_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "result" / ADVERSARIAL_REVIEW_RESULT_FILENAME


def _review_findings_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "result" / "review_findings.yaml"


def _review_audit_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "result" / REVIEWER_WRITE_SCOPE_AUDIT_FILENAME


def _stage_gate_review_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "closure" / "stage_gate_review.yaml"


def _stage_completion_certificate_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "closure" / "stage_completion_certificate.yaml"


def _closure_complete(stage_dir: Path) -> bool:
    certificate_path = _stage_completion_certificate_path(stage_dir)
    if certificate_path.exists():
        return True
    closure_dir = stage_dir / "review" / "closure"
    return all(
        (closure_dir / name).exists()
        for name in ("latest_review_pack.yaml", "stage_gate_review.yaml", "stage_completion_certificate.yaml")
    )


def _required_outputs_checked(stage_dir: Path, spec: StageEvaluatorSpec) -> dict[str, Any]:
    artifact_root = _artifact_root(stage_dir, spec)
    missing = [name for name in spec.required_outputs if not (artifact_root / name).exists()]
    return {
        "expected": list(spec.required_outputs),
        "missing": missing,
        "present_count": len(spec.required_outputs) - len(missing),
        "missing_count": len(missing),
    }


def _review_summary(stage_dir: Path, *, reviewable: bool) -> dict[str, Any]:
    request_present = _review_request_path(stage_dir).exists()
    receipt_present = _review_receipt_path(stage_dir).exists()
    result_path = _review_result_path(stage_dir)
    result_present = result_path.exists()
    audit_path = _review_audit_path(stage_dir)
    audit_present = audit_path.exists()
    review_transition_confirmed = _review_transition_confirmed(stage_dir)
    closure_complete = _closure_complete(stage_dir)
    review_result = load_adversarial_review_result(result_path) if result_present else {}
    audit_payload = load_reviewer_write_scope_audit(audit_path) if audit_present else {}
    certificate_payload = _read_yaml_if_present(_stage_completion_certificate_path(stage_dir))
    stage_gate_review = _read_yaml_if_present(_stage_gate_review_path(stage_dir))

    return {
        "reviewable": reviewable,
        "review_transition_confirmed": review_transition_confirmed,
        "review_request_present": request_present,
        "spawned_reviewer_receipt_present": receipt_present,
        "review_result_present": result_present,
        "review_audit_present": audit_present,
        "audit_status": audit_payload.get("audit_status"),
        "closure_complete": closure_complete,
        "review_loop_outcome": review_result.get("review_loop_outcome"),
        "final_verdict": certificate_payload.get("final_verdict")
        or certificate_payload.get("stage_status")
        or stage_gate_review.get("final_verdict"),
    }


def _review_blocking_and_warnings(stage_dir: Path) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    warnings: list[str] = []

    review_result_path = _review_result_path(stage_dir)
    if review_result_path.exists():
        review_result = load_adversarial_review_result(review_result_path)
        blocking.extend(str(item) for item in review_result.get("blocking_findings", []))
        warnings.extend(str(item) for item in review_result.get("reservation_findings", []))
        warnings.extend(str(item) for item in review_result.get("residual_risks", []))

    findings_path = _review_findings_path(stage_dir)
    if findings_path.exists():
        review_findings = load_review_findings_if_present(findings_path)
        blocking.extend(str(item) for item in review_findings.get("blocking_findings", []))
        warnings.extend(str(item) for item in review_findings.get("reservation_findings", []))
        warnings.extend(str(item) for item in review_findings.get("residual_risks", []))

    stage_gate_review = _read_yaml_if_present(_stage_gate_review_path(stage_dir))
    blocking.extend(str(item) for item in stage_gate_review.get("blocking_findings", []))
    warnings.extend(str(item) for item in stage_gate_review.get("reservation_findings", []))
    warnings.extend(str(item) for item in stage_gate_review.get("residual_risks", []))

    return _dedupe(blocking), _dedupe(warnings)


def _evaluate_idea_intake(stage_dir: Path, lineage_root: Path, spec: StageEvaluatorSpec) -> dict[str, Any]:
    required = _required_outputs_checked(stage_dir, spec)
    gate_payload = _read_yaml_if_present(stage_dir / "idea_gate_decision.yaml")
    gate_verdict = gate_payload.get("verdict")
    confirmation_present = (stage_dir / "idea_intake_transition_approval.yaml").exists()

    blocking = [f"Missing required output: {item}" for item in required["missing"]]
    warnings: list[str] = []

    if required["missing"]:
        status = "author_incomplete"
        reason = "idea_intake required outputs are incomplete"
        passed = False
        can_progress = False
    elif gate_verdict == "GO_TO_MANDATE" and not confirmation_present:
        status = "confirmation_pending"
        reason = "explicit idea_intake confirmation is still pending"
        passed = False
        can_progress = False
    elif gate_verdict == "GO_TO_MANDATE" and confirmation_present:
        status = "passed"
        reason = "idea_intake has explicit approval to progress into mandate"
        passed = True
        can_progress = True
    elif gate_verdict == "NEEDS_REFRAME":
        status = "needs_reframe"
        reason = "idea_intake verdict requires reframe before progression"
        passed = False
        can_progress = False
    elif gate_verdict == "DROP":
        status = "dropped"
        reason = "idea_intake verdict dropped the research idea"
        passed = False
        can_progress = False
    else:
        status = "author_incomplete"
        reason = "idea_intake gate decision is missing or incomplete"
        passed = False
        can_progress = False

    return {
        "schema_version": STAGE_EVALUATOR_SCHEMA_VERSION,
        "lineage_id": lineage_root.name,
        "stage": spec.stage,
        "stage_dir": str(stage_dir),
        "route_family": spec.route_family,
        "pass": passed,
        "can_progress": can_progress,
        "status": status,
        "reason": reason,
        "blocking_findings": _dedupe(blocking),
        "warnings": warnings,
        "required_outputs_checked": required,
        "review_summary": {
            "reviewable": False,
            "review_transition_confirmed": False,
            "review_request_present": False,
            "spawned_reviewer_receipt_present": False,
            "review_result_present": False,
            "review_audit_present": False,
            "audit_status": None,
            "closure_complete": confirmation_present,
            "review_loop_outcome": None,
            "final_verdict": gate_verdict if isinstance(gate_verdict, str) else None,
        },
        "evaluated_at": _now_iso(),
    }


def _evaluate_reviewable_stage(stage_dir: Path, lineage_root: Path, spec: StageEvaluatorSpec) -> dict[str, Any]:
    required = _required_outputs_checked(stage_dir, spec)
    blocking = [f"Missing required output: {item}" for item in required["missing"]]
    review_blocking, warnings = _review_blocking_and_warnings(stage_dir)
    blocking.extend(review_blocking)
    blocking = _dedupe(blocking)
    review_summary = _review_summary(stage_dir, reviewable=True)
    stale_reason = review_cycle_stale_reason(
        stage_dir,
        artifact_root=_artifact_root(stage_dir, spec),
        required_outputs=spec.required_outputs,
    )
    if stale_reason is not None:
        blocking.append(stale_reason)
        blocking = _dedupe(blocking)

    if required["missing"]:
        status = "author_incomplete"
        reason = "author/formal required outputs are incomplete"
        passed = False
        can_progress = False
    elif stale_reason is not None:
        status = "review_pending"
        reason = stale_reason
        passed = False
        can_progress = False
    elif not review_summary["review_transition_confirmed"] and not review_summary["review_request_present"]:
        status = "review_confirmation_pending"
        reason = "explicit review confirmation is still pending"
        passed = False
        can_progress = False
    elif not review_summary["review_request_present"]:
        status = "review_pending"
        reason = "review confirmation exists, but adversarial review request is missing"
        passed = False
        can_progress = False
    elif not review_summary["spawned_reviewer_receipt_present"]:
        status = "review_pending"
        reason = "review request exists, but spawned reviewer receipt is still missing"
        passed = False
        can_progress = False
    elif not review_summary["review_result_present"]:
        status = "review_in_progress"
        reason = "spawned reviewer is still expected to produce adversarial_review_result.yaml"
        passed = False
        can_progress = False
    elif review_summary["review_loop_outcome"] == FIX_REQUIRED_OUTCOME:
        status = "review_fix_required"
        reason = "reviewer requested author fixes before closure"
        passed = False
        can_progress = False
    elif not review_summary["review_audit_present"]:
        status = "review_audit_pending"
        reason = "review result exists, but reviewer write-scope audit is still missing"
        passed = False
        can_progress = False
    elif review_summary["audit_status"] != "PASS":
        status = "review_audit_failed"
        reason = "reviewer write-scope audit did not pass"
        passed = False
        can_progress = False
    elif not review_summary["closure_complete"]:
        status = "review_closure_pending"
        reason = "review is closure-ready, but deterministic closure artifacts are still incomplete"
        passed = False
        can_progress = False
    elif review_summary["final_verdict"] in NON_ADVANCING_COMPLETION_STATUSES:
        status = "failed"
        reason = f"stage completion verdict {review_summary['final_verdict']} blocks progression"
        passed = False
        can_progress = False
    else:
        status = "passed"
        final_verdict = review_summary["final_verdict"] or "PASS"
        reason = f"stage completion verdict {final_verdict} allows progression"
        passed = True
        can_progress = True

    return {
        "schema_version": STAGE_EVALUATOR_SCHEMA_VERSION,
        "lineage_id": lineage_root.name,
        "stage": spec.stage,
        "stage_dir": str(stage_dir),
        "route_family": spec.route_family,
        "pass": passed,
        "can_progress": can_progress,
        "status": status,
        "reason": reason,
        "blocking_findings": blocking,
        "warnings": warnings,
        "required_outputs_checked": required,
        "review_summary": review_summary,
        "evaluated_at": _now_iso(),
    }


def evaluate_stage(stage_dir: str | Path, *, lineage_root: str | Path | None = None) -> dict[str, Any]:
    resolved_stage_dir = Path(stage_dir).resolve()
    resolved_lineage_root = Path(lineage_root).resolve() if lineage_root is not None else resolved_stage_dir.parent
    spec = _spec_for_stage_dir(resolved_stage_dir)
    if spec.reviewable:
        return _evaluate_reviewable_stage(resolved_stage_dir, resolved_lineage_root, spec)
    return _evaluate_idea_intake(resolved_stage_dir, resolved_lineage_root, spec)


def write_stage_evaluator_artifacts(
    stage_dir: str | Path,
    *,
    lineage_root: str | Path | None = None,
) -> dict[str, Any]:
    payload = evaluate_stage(stage_dir, lineage_root=lineage_root)
    resolved_stage_dir = Path(stage_dir).resolve()
    evaluation_dir = _evaluation_dir(resolved_stage_dir)
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    current_path = evaluation_dir / STAGE_EVALUATOR_FILENAME
    current_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ledger_path = evaluation_dir / STAGE_EVALUATOR_RESULTS_FILENAME
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    return payload
