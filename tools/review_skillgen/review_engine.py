from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.review_skillgen.closure_models import build_review_payload
from tools.review_skillgen.closure_writer import write_closure_artifacts
from tools.review_skillgen.context_inference import infer_review_context
from tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from tools.review_skillgen.review_findings import load_review_findings


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
    reviewer_findings: dict[str, Any],
    blocking_findings: list[str],
    reservation_findings: list[str],
) -> str:
    recommended = reviewer_findings.get("recommended_verdict")
    if recommended:
        if blocking_findings and recommended in {"PASS", "CONDITIONAL PASS"}:
            return "RETRY"
        if recommended in {"PASS FOR RETRY", "RETRY"}:
            if not reviewer_findings.get("rollback_stage") or not reviewer_findings.get("allowed_modifications"):
                raise ValueError(f"{recommended} requires rollback_stage and allowed_modifications")
        return recommended

    if blocking_findings:
        return "RETRY"
    if reservation_findings:
        return "CONDITIONAL PASS"
    return "PASS"


def run_stage_review(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if explicit_context is not None:
        inferred = infer_review_context(Path(explicit_context["stage_dir"]))
        context = {
            **inferred,
            **explicit_context,
        }
    else:
        context = infer_review_context(cwd or Path.cwd())
    stage_dir = Path(context["stage_dir"]).resolve()
    lineage_root = Path(context["lineage_root"]).resolve()
    stage = context["stage"]
    lineage_id = context["lineage_id"]

    gates = load_gate_schema(GATES_PATH)
    checklist = load_checklist_schema(CHECKLIST_PATH)
    stage_contract = gates["stages"][stage]
    stage_checks = checklist["stages"][stage]

    reviewer_findings = load_review_findings(stage_dir / "review_findings.yaml")

    missing_required_outputs = _check_required_outputs(stage_dir, stage_contract.get("required_outputs", []))
    blocking_findings = [f"Missing required output: {item}" for item in missing_required_outputs]
    blocking_findings.extend(_check_global_evidence(stage_dir, stage_checks))

    auto_stage_blocking, auto_stage_reservations = _check_stage_evidence(stage_dir, stage_checks.get("checks", []))
    blocking_findings.extend(auto_stage_blocking)

    reservation_findings = list(auto_stage_reservations)
    reservation_findings.extend(reviewer_findings["reservation_findings"])

    blocking_findings.extend(reviewer_findings["blocking_findings"])
    info_findings = list(reviewer_findings["info_findings"])
    residual_risks = list(reviewer_findings["residual_risks"])

    final_verdict = _resolve_verdict(reviewer_findings, blocking_findings, reservation_findings)
    rollback_stage = reviewer_findings.get("rollback_stage") or stage_contract.get("rollback_rules", {}).get(
        "default_rollback_stage"
    )
    allowed_modifications = reviewer_findings.get("allowed_modifications") or list(
        stage_contract.get("rollback_rules", {}).get("allowed_modifications", [])
    )
    downstream_permissions = reviewer_findings.get("downstream_permissions") or list(
        stage_contract.get("downstream_permissions", {}).get("may_advance_to", [])
    )

    payload = build_review_payload(
        lineage_id=lineage_id,
        stage=stage,
        final_verdict=final_verdict,
        stage_status=final_verdict,
        blocking_findings=blocking_findings,
        reservation_findings=reservation_findings,
        info_findings=info_findings,
        residual_risks=residual_risks,
        reviewer_identity=reviewer_findings["reviewer_identity"],
        rollback_stage=rollback_stage,
        allowed_modifications=allowed_modifications,
        downstream_permissions=downstream_permissions,
        contract_source=str(GATES_PATH.relative_to(ROOT)),
        checklist_source=str(CHECKLIST_PATH.relative_to(ROOT)),
        required_outputs_checked={
            "expected": list(stage_contract.get("required_outputs", [])),
            "missing": missing_required_outputs,
        },
        evidence_summary={
            "recommended_gate_doc": stage_checks.get("recommended_gate_doc"),
        },
    )

    write_closure_artifacts(
        payload,
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
    )
    return payload
