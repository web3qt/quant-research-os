from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
from typing import Any

from tools.review_governance_runtime import record_review_governance
from tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    FIX_REQUIRED_OUTCOME,
    ReviewerRuntimeIdentity,
    assign_runtime_reviewer_to_request,
    load_adversarial_review_request,
    load_adversarial_review_result,
    resolve_closure_verdict,
    validate_result_against_request,
)
from tools.review_skillgen.closure_models import build_review_payload
from tools.review_skillgen.closure_writer import write_closure_artifacts
from tools.review_skillgen.context_inference import build_stage_context, infer_review_context
from tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from tools.review_skillgen.review_findings import load_review_findings_if_present


ROOT = Path(__file__).resolve().parents[2]
GATES_PATH = ROOT / "docs" / "gates" / "workflow_stage_gates.yaml"
CHECKLIST_PATH = ROOT / "docs" / "review-sop" / "review_checklist_master.yaml"


def _find_stage_file(stage_dir: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        if "*" in pattern:
            matches = sorted(stage_dir.glob(pattern))
            if matches:
                return matches[0]
            continue

        candidate = stage_dir / pattern
        if candidate.exists():
            return candidate

    return None


def _check_required_outputs(stage_dir: Path, required_outputs: list[str]) -> list[str]:
    missing: list[str] = []
    for item in required_outputs:
        if not (stage_dir / item).exists():
            missing.append(item)
    return missing


def _check_global_evidence(stage_dir: Path, stage_checks: dict[str, Any]) -> list[str]:
    findings: list[str] = []

    if not (stage_dir / "artifact_catalog.md").exists():
        findings.append("Missing required global evidence: artifact_catalog.md")

    if _find_stage_file(stage_dir, ["field_dictionary.md", "*_fields.md"]) is None:
        findings.append("Missing required global evidence: field_dictionary.md or *_fields.md")

    if _find_stage_file(stage_dir, ["run_manifest.json", "repro_manifest.json"]) is None:
        findings.append("Missing required global evidence: run_manifest.json or repro_manifest.json")

    recommended_gate_doc = stage_checks.get("recommended_gate_doc")
    if recommended_gate_doc and not (stage_dir / recommended_gate_doc).exists():
        findings.append(f"Missing recommended gate document: {recommended_gate_doc}")

    return findings


def _is_automatable_evidence(pattern: str) -> bool:
    return pattern.endswith("/") or "*" in pattern or "." in Path(pattern).name


def _check_stage_evidence(stage_dir: Path, checks: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    reservations: list[str] = []

    for check in checks:
        evidence_patterns = [item for item in check.get("evidence", []) if _is_automatable_evidence(item)]
        if not evidence_patterns:
            continue

        if any(_find_stage_file(stage_dir, [pattern]) is not None for pattern in evidence_patterns):
            continue

        message = f"{check['id']}: missing evidence for '{check['check']}'"
        if check.get("severity") == "reservation":
            reservations.append(message)
        else:
            blocking.append(message)

    return blocking, reservations


def _resolve_verdict(
    review_result: dict[str, Any],
    reviewer_findings: dict[str, Any],
    blocking_findings: list[str],
    reservation_findings: list[str],
) -> tuple[str | None, str]:
    review_loop_outcome = review_result["review_loop_outcome"]
    recommended = reviewer_findings.get("recommended_verdict")
    final_verdict = resolve_closure_verdict(review_loop_outcome)
    if review_loop_outcome == FIX_REQUIRED_OUTCOME:
        return None, FIX_REQUIRED_OUTCOME

    if recommended:
        if blocking_findings and recommended in {"PASS", "CONDITIONAL PASS"}:
            return "RETRY", "CLOSURE_READY_RETRY"
        if recommended in {"PASS FOR RETRY", "RETRY"}:
            if not reviewer_findings.get("rollback_stage") or not reviewer_findings.get("allowed_modifications"):
                raise ValueError(f"{recommended} requires rollback_stage and allowed_modifications")
        return recommended, review_loop_outcome

    if blocking_findings:
        return "RETRY", review_loop_outcome
    if reservation_findings:
        return final_verdict or "CONDITIONAL PASS", review_loop_outcome
    return final_verdict or "PASS", review_loop_outcome


def _runtime_identity(
    *,
    reviewer_identity: str | None,
    reviewer_role: str | None,
    reviewer_session_id: str | None,
    reviewer_mode: str | None,
) -> ReviewerRuntimeIdentity:
    resolved_identity = reviewer_identity or os.environ.get("QROS_REVIEWER_ID") or "codex-reviewer"
    resolved_role = reviewer_role or os.environ.get("QROS_REVIEWER_ROLE") or "reviewer"
    resolved_session = reviewer_session_id or os.environ.get("QROS_REVIEWER_SESSION_ID") or "local-review-session"
    resolved_mode = reviewer_mode or os.environ.get("QROS_REVIEWER_MODE") or "adversarial"
    return ReviewerRuntimeIdentity(
        reviewer_identity=resolved_identity,
        reviewer_role=resolved_role,
        reviewer_session_id=resolved_session,
        reviewer_mode=resolved_mode,
    )


def run_stage_review(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
    reviewer_identity: str | None = None,
    reviewer_role: str | None = None,
    reviewer_session_id: str | None = None,
    reviewer_mode: str | None = None,
) -> dict[str, Any]:
    if explicit_context is not None:
        inferred = build_stage_context(Path(explicit_context["stage_dir"]))
        context = {
            **inferred,
            **explicit_context,
        }
    else:
        context = infer_review_context(cwd or Path.cwd())
    stage_dir = Path(context["stage_dir"]).resolve()
    lineage_root = Path(context["lineage_root"]).resolve()
    author_formal_dir = Path(context["author_formal_dir"]).resolve()
    review_request_dir = Path(context["review_request_dir"]).resolve()
    review_result_dir = Path(context["review_result_dir"]).resolve()
    stage = context["stage"]
    lineage_id = context["lineage_id"]

    gates = load_gate_schema(GATES_PATH)
    checklist = load_checklist_schema(CHECKLIST_PATH)
    stage_contract = gates["stages"][stage]
    stage_checks = checklist["stages"][stage]

    request_path = review_request_dir / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    result_path = review_result_dir / ADVERSARIAL_REVIEW_RESULT_FILENAME
    request_payload = load_adversarial_review_request(request_path)
    runtime_identity = _runtime_identity(
        reviewer_identity=reviewer_identity,
        reviewer_role=reviewer_role,
        reviewer_session_id=reviewer_session_id,
        reviewer_mode=reviewer_mode,
    )
    request_payload = assign_runtime_reviewer_to_request(request_path, request_payload, runtime_identity)
    review_result = load_adversarial_review_result(result_path)
    validate_result_against_request(
        request_payload=request_payload,
        result_payload=review_result,
        runtime_identity=runtime_identity,
    )
    reviewer_findings = load_review_findings_if_present(review_result_dir / "review_findings.yaml")

    missing_required_outputs = _check_required_outputs(author_formal_dir, stage_contract.get("required_outputs", []))
    blocking_findings = [f"Missing required output: {item}" for item in missing_required_outputs]
    blocking_findings.extend(_check_global_evidence(author_formal_dir, stage_checks))

    auto_stage_blocking, auto_stage_reservations = _check_stage_evidence(author_formal_dir, stage_checks.get("checks", []))
    blocking_findings.extend(auto_stage_blocking)

    reservation_findings = list(auto_stage_reservations)
    reservation_findings.extend(reviewer_findings["reservation_findings"])

    blocking_findings.extend(reviewer_findings["blocking_findings"])
    blocking_findings.extend(review_result["blocking_findings"])
    info_findings = list(reviewer_findings["info_findings"])
    info_findings.extend(review_result["info_findings"])
    residual_risks = list(reviewer_findings["residual_risks"])
    residual_risks.extend(review_result["residual_risks"])

    final_verdict, review_loop_outcome = _resolve_verdict(
        review_result,
        reviewer_findings,
        blocking_findings,
        reservation_findings,
    )
    rollback_stage = review_result.get("rollback_stage") or reviewer_findings.get("rollback_stage") or stage_contract.get("rollback_rules", {}).get(
        "default_rollback_stage"
    )
    allowed_modifications = review_result.get("allowed_modifications") or reviewer_findings.get("allowed_modifications") or list(
        stage_contract.get("rollback_rules", {}).get("allowed_modifications", [])
    )
    downstream_permissions = review_result.get("downstream_permissions") or reviewer_findings.get("downstream_permissions") or list(
        stage_contract.get("downstream_permissions", {}).get("may_advance_to", [])
    )
    review_timestamp_utc = datetime.now(timezone.utc).isoformat()

    common_payload = {
        "lineage_id": lineage_id,
        "stage": stage,
        "review_loop_outcome": review_loop_outcome,
        "stage_status": review_loop_outcome,
        "blocking_findings": blocking_findings,
        "reservation_findings": reservation_findings,
        "info_findings": info_findings,
        "residual_risks": residual_risks,
        "review_timestamp_utc": review_timestamp_utc,
        "reviewer_identity": review_result["reviewer_identity"],
        "reviewer_role": review_result["reviewer_role"],
        "reviewer_session_id": review_result["reviewer_session_id"],
        "reviewer_mode": review_result["reviewer_mode"],
        "author_identity": request_payload["author_identity"],
        "author_session_id": request_payload["author_session_id"],
        "rollback_stage": rollback_stage,
        "allowed_modifications": allowed_modifications,
        "downstream_permissions": downstream_permissions,
        "review_scope": {
            "required_program_dir": request_payload["required_program_dir"],
            "required_program_entrypoint": request_payload["required_program_entrypoint"],
            "required_artifact_paths": request_payload["required_artifact_paths"],
            "required_provenance_paths": request_payload["required_provenance_paths"],
            "reviewed_program_dir": review_result["reviewed_program_dir"],
            "reviewed_program_entrypoint": review_result["reviewed_program_entrypoint"],
            "reviewed_artifact_paths": review_result["reviewed_artifact_paths"],
            "reviewed_provenance_paths": review_result["reviewed_provenance_paths"],
        },
        "adversarial_review_request": request_payload,
        "adversarial_review_result": review_result,
        "contract_source": str(GATES_PATH.relative_to(ROOT)),
        "checklist_source": str(CHECKLIST_PATH.relative_to(ROOT)),
        "required_outputs_checked": {
            "expected": list(stage_contract.get("required_outputs", [])),
            "missing": missing_required_outputs,
        },
        "evidence_summary": {
            "recommended_gate_doc": stage_checks.get("recommended_gate_doc"),
            "review_summary": review_result.get("review_summary"),
        },
    }

    governance_result = record_review_governance(
        stage_dir=stage_dir,
        lineage_root=lineage_root,
        stage=stage,
        request_payload=request_payload,
        review_result=review_result,
        review_loop_outcome=review_loop_outcome,
        final_verdict=final_verdict,
        blocking_findings=blocking_findings,
        reservation_findings=reservation_findings,
        info_findings=info_findings,
    )
    common_payload["governance_signal_path"] = "review/governance/governance_signal.json"
    common_payload["governance_candidate_summary"] = {
        "ledger_entries_written": governance_result["ledger_entries_written"],
        "candidates_updated": governance_result["candidates_updated"],
        "post_rollout": governance_result["bundle"]["post_rollout_only"],
    }
    common_payload["governance"] = {
        "appended_entries": governance_result["ledger_entries_written"],
        "candidates_updated": governance_result["candidates_updated"],
        "post_rollout": governance_result["bundle"]["post_rollout_only"],
    }

    if review_loop_outcome == FIX_REQUIRED_OUTCOME:
        return {
            **common_payload,
            "final_verdict": None,
        }

    payload = build_review_payload(
        lineage_id=lineage_id,
        stage=stage,
        final_verdict=final_verdict,
        stage_status=final_verdict,
        blocking_findings=blocking_findings,
        reservation_findings=reservation_findings,
        info_findings=info_findings,
        residual_risks=residual_risks,
        review_timestamp_utc=review_timestamp_utc,
        reviewer_identity=review_result["reviewer_identity"],
        reviewer_role=review_result["reviewer_role"],
        reviewer_session_id=review_result["reviewer_session_id"],
        reviewer_mode=review_result["reviewer_mode"],
        author_identity=request_payload["author_identity"],
        author_session_id=request_payload["author_session_id"],
        review_loop_outcome=review_loop_outcome,
        rollback_stage=rollback_stage,
        allowed_modifications=allowed_modifications,
        downstream_permissions=downstream_permissions,
        review_scope=common_payload["review_scope"],
        adversarial_review_request=request_payload,
        adversarial_review_result=review_result,
        contract_source=common_payload["contract_source"],
        checklist_source=common_payload["checklist_source"],
        required_outputs_checked=common_payload["required_outputs_checked"],
        evidence_summary=common_payload["evidence_summary"],
        governance_signal_path=common_payload["governance_signal_path"],
        governance_candidate_summary=common_payload["governance_candidate_summary"],
        governance=common_payload["governance"],
    )

    write_closure_artifacts(
        payload,
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
    )
    return payload
