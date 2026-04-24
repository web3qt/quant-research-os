from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.tools.artifact_contract_runtime import ArtifactContractError, load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_data_ready_contract_runtime import validate_csf_data_ready_semantics
from runtime.tools.csf_signal_ready_contract_runtime import validate_csf_signal_ready_semantics
from runtime.tools.review_skillgen.context_inference import build_stage_context, infer_review_context
from runtime.tools.review_skillgen.artifact_realism import check_machine_artifact_realism
from runtime.tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from runtime.tools.review_skillgen.review_engine import _split_review_checks, _split_structural_checks
from runtime.tools.review_skillgen.stage_content_gate import (
    check_global_evidence,
    check_metric_gates,
    check_required_outputs,
    check_stage_evidence,
    check_structural_gates,
)
from runtime.tools.review_skillgen.upstream_binding_validator import validate_upstream_bindings
from runtime.tools.lineage_program_runtime import StageProgramRuntimeError, validate_stage_program
from runtime.tools.stage_program_scaffold import STAGE_PROGRAM_SPECS


ROOT = Path(__file__).resolve().parents[3]
GATES_PATH = ROOT / "contracts" / "stages" / "workflow_stage_gates.yaml"
CHECKLIST_PATH = ROOT / "contracts" / "review" / "review_checklist_master.yaml"

_STAGE_PROGRAM_SPEC_ALIASES = {
    "train_calibration": "train_freeze",
}


def run_review_preflight(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
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
    stage = context["stage"]

    gates = load_gate_schema(GATES_PATH)
    checklist = load_checklist_schema(CHECKLIST_PATH)
    stage_contract = gates["stages"][stage]
    stage_checks = checklist["stages"][stage]
    stage_content_checks, upstream_binding_checks = _split_structural_checks(
        stage_contract.get("structural_gate_checks", [])
    )
    stage_content_review_checks, upstream_binding_review_checks = _split_review_checks(stage_checks.get("checks", []))

    content_findings: list[str] = []
    content_findings.extend(_validate_stage_program_for_review(stage, lineage_root))
    content_findings.extend(
        f"Missing required output: {item}"
        for item in check_required_outputs(author_formal_dir, stage_contract.get("required_outputs", []))
    )
    content_findings.extend(check_global_evidence(author_formal_dir, stage_checks))
    content_blocking, _ = check_stage_evidence(author_formal_dir, stage_content_review_checks)
    content_findings.extend(content_blocking)
    content_findings.extend(check_structural_gates(author_formal_dir, stage_content_checks))
    content_findings.extend(check_metric_gates(author_formal_dir, stage_contract.get("metric_gate_checks", [])))
    content_findings.extend(check_machine_artifact_realism(author_formal_dir, stage_contract.get("machine_artifacts", [])))
    content_findings.extend(_check_artifact_contract(stage, author_formal_dir))
    content_findings.extend(_check_stage_semantics(stage, author_formal_dir, lineage_root))

    upstream_findings = validate_upstream_bindings(
        stage=stage,
        lineage_root=lineage_root,
        author_formal_dir=author_formal_dir,
        structural_binding_checks=upstream_binding_checks,
    )
    upstream_evidence_findings, _ = check_stage_evidence(author_formal_dir, upstream_binding_review_checks)
    upstream_findings.extend(upstream_evidence_findings)

    return {
        "stage": stage,
        "lineage_id": context["lineage_id"],
        "content_findings": content_findings,
        "upstream_binding_findings": upstream_findings,
        "status": "PASS" if not content_findings and not upstream_findings else "FAIL",
    }


def _validate_stage_program_for_review(stage: str, lineage_root: Path) -> list[str]:
    spec_key = _STAGE_PROGRAM_SPEC_ALIASES.get(stage, stage)
    spec = STAGE_PROGRAM_SPECS.get(spec_key)
    if spec is None:
        return []
    try:
        validate_stage_program(lineage_root, str(spec["stage_id"]), str(spec["route"]))
    except StageProgramRuntimeError as exc:
        return [f"{exc.reason_code}: {exc.message}"]
    return []


def _check_artifact_contract(stage: str, author_formal_dir: Path) -> list[str]:
    if stage not in {"csf_data_ready", "csf_signal_ready"}:
        return []
    try:
        result = validate_stage_artifacts(author_formal_dir, load_artifact_contract(stage))
    except ArtifactContractError:
        return []
    return [f"ARTIFACT-CONTRACT-001: {error}" for error in result.errors]


def _check_stage_semantics(stage: str, author_formal_dir: Path, lineage_root: Path) -> list[str]:
    if stage == "csf_data_ready":
        result = validate_csf_data_ready_semantics(author_formal_dir)
        return [f"CSF-DATA-SEMANTIC-001: {error}" for error in result.errors]
    if stage == "csf_signal_ready":
        result = validate_csf_signal_ready_semantics(author_formal_dir, lineage_root)
        return [f"CSF-SIGNAL-SEMANTIC-001: {error}" for error in result.errors]
    return []
