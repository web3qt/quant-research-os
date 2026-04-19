from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.tools.review_skillgen.context_inference import build_stage_context, infer_review_context
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


ROOT = Path(__file__).resolve().parents[3]
GATES_PATH = ROOT / "contracts" / "stages" / "workflow_stage_gates.yaml"
CHECKLIST_PATH = ROOT / "contracts" / "review" / "review_checklist_master.yaml"


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
    content_findings.extend(
        f"Missing required output: {item}"
        for item in check_required_outputs(author_formal_dir, stage_contract.get("required_outputs", []))
    )
    content_findings.extend(check_global_evidence(author_formal_dir, stage_checks))
    content_blocking, _ = check_stage_evidence(author_formal_dir, stage_content_review_checks)
    content_findings.extend(content_blocking)
    content_findings.extend(check_structural_gates(author_formal_dir, stage_content_checks))
    content_findings.extend(check_metric_gates(author_formal_dir, stage_contract.get("metric_gate_checks", [])))

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
