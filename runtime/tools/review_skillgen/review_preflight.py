from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactContractError, load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics
from runtime.tools.csf_data_ready_contract_runtime import validate_csf_data_ready_semantics
from runtime.tools.csf_holdout_validation_contract_runtime import validate_csf_holdout_validation_semantics
from runtime.tools.csf_signal_ready_contract_runtime import validate_csf_signal_ready_semantics
from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics
from runtime.tools.csf_train_freeze_contract_runtime import validate_csf_train_freeze_semantics
from runtime.tools.mandate_admission_runtime import assess_time_coverage_preflight
from runtime.tools.mandate_contract_runtime import validate_mandate_semantics
from runtime.tools.review_skillgen.context_inference import build_stage_context, infer_review_context
from runtime.tools.review_skillgen.artifact_realism import check_machine_artifact_realism
from runtime.tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from runtime.tools.review_skillgen.protected_state_guard import assert_protected_review_state_intact
from runtime.tools.review_skillgen.review_engine import _split_review_checks, _split_structural_checks
from runtime.tools.review_skillgen.stage_content_gate import (
    check_global_evidence,
    check_metric_gates,
    check_required_outputs,
    check_stage_evidence,
    check_structural_gates,
)
from runtime.tools.review_skillgen.upstream_binding_validator import validate_upstream_bindings
from runtime.tools.lineage_lock_ledger import assert_lineage_locks_intact
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
    assert_lineage_locks_intact(lineage_root)

    gates = load_gate_schema(GATES_PATH)
    checklist = load_checklist_schema(CHECKLIST_PATH)
    stage_contract = gates["stages"][stage]
    assert_protected_review_state_intact(
        stage_dir=stage_dir,
        lineage_root=lineage_root,
        required_outputs=stage_contract.get("required_outputs", []),
        required_provenance_paths=["program_execution_manifest.json"],
        allow_missing_state=True,
    )

    # 当前 rollout 只对 mandate 接入 research preflight blocker fail-closed；
    # reviewer lane 不负责重做 author 已知的首轮发现，已阻断就直接失败返回。
    research_preflight_findings = _check_research_preflight_blockers(stage, stage_dir)
    if research_preflight_findings:
        return {
            "stage": stage,
            "lineage_id": context["lineage_id"],
            "content_findings": research_preflight_findings,
            "upstream_binding_findings": [],
            "research_preflight_findings": research_preflight_findings,
            "status": "FAIL",
        }
    stage_checks = checklist.get("stages", {}).get(stage, {"checks": []})
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
        "research_preflight_findings": [],
        "status": "PASS" if not content_findings and not upstream_findings else "FAIL",
    }


def _check_research_preflight_blockers(stage: str, stage_dir: Path) -> list[str]:
    if stage != "mandate":
        return []

    draft_path = stage_dir / "author" / "draft" / "mandate_freeze_draft.yaml"
    if not draft_path.exists():
        return []

    payload = _load_yaml_dict(draft_path)
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        return []

    scope_group = groups.get("scope_contract", {})
    data_group = groups.get("data_contract", {})
    if not isinstance(scope_group, dict) or not isinstance(data_group, dict):
        return []

    scope_contract = scope_group.get("draft", {})
    data_contract = data_group.get("draft", {})
    if not isinstance(scope_contract, dict) or not isinstance(data_contract, dict):
        return []

    preflight_status = assess_time_coverage_preflight(
        data_source=data_contract.get("data_source", ""),
        time_boundary=scope_contract.get("time_boundary", ""),
    )
    if preflight_status is None or preflight_status.passable:
        return []

    summary = f"{preflight_status.blocker_code}: {preflight_status.blocker_reason}"
    if preflight_status.next_action:
        summary = f"{summary} {preflight_status.next_action}"
    return [summary]


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


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
    if stage not in {
        "mandate",
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
    }:
        return []
    try:
        result = validate_stage_artifacts(author_formal_dir, load_artifact_contract(stage))
    except ArtifactContractError:
        return []
    return [f"ARTIFACT-CONTRACT-001: {error}" for error in result.errors]


def _check_stage_semantics(stage: str, author_formal_dir: Path, lineage_root: Path) -> list[str]:
    if stage == "mandate":
        result = validate_mandate_semantics(author_formal_dir)
        return [f"MANDATE-SEMANTIC-001: {error}" for error in result.errors]
    if stage == "csf_data_ready":
        result = validate_csf_data_ready_semantics(author_formal_dir)
        return [f"CSF-DATA-SEMANTIC-001: {error}" for error in result.errors]
    if stage == "csf_signal_ready":
        result = validate_csf_signal_ready_semantics(author_formal_dir, lineage_root)
        return [f"CSF-SIGNAL-SEMANTIC-001: {error}" for error in result.errors]
    if stage == "csf_train_freeze":
        result = validate_csf_train_freeze_semantics(author_formal_dir, lineage_root)
        return [f"CSF-TRAIN-SEMANTIC-001: {error}" for error in result.errors]
    if stage == "csf_test_evidence":
        result = validate_csf_test_evidence_semantics(author_formal_dir, lineage_root)
        return [f"CSF-TEST-SEMANTIC-001: {error}" for error in result.errors]
    if stage == "csf_backtest_ready":
        result = validate_csf_backtest_ready_semantics(author_formal_dir, lineage_root)
        return [f"CSF-BACKTEST-SEMANTIC-001: {error}" for error in result.errors]
    if stage == "csf_holdout_validation":
        result = validate_csf_holdout_validation_semantics(author_formal_dir, lineage_root)
        return [f"CSF-HOLDOUT-SEMANTIC-001: {error}" for error in result.errors]
    if stage.startswith("tss_"):
        return _check_tss_stage_semantics(stage, author_formal_dir, lineage_root)
    return []


def _check_tss_stage_semantics(stage: str, author_formal_dir: Path, lineage_root: Path) -> list[str]:
    module_name = f"runtime.tools.{stage}_contract_runtime"
    function_name = f"validate_{stage}_semantics"
    semantic_prefixes = {
        "tss_data_ready": "TSS-DATA-SEMANTIC-001",
        "tss_signal_ready": "TSS-SIGNAL-SEMANTIC-001",
        "tss_train_freeze": "TSS-TRAIN-SEMANTIC-001",
        "tss_test_evidence": "TSS-TEST-SEMANTIC-001",
        "tss_backtest_ready": "TSS-BACKTEST-SEMANTIC-001",
        "tss_holdout_validation": "TSS-HOLDOUT-SEMANTIC-001",
    }
    try:
        module = importlib.import_module(module_name)
        validator = getattr(module, function_name)
    except (ModuleNotFoundError, AttributeError):
        # TSS stage-local runtime 模块由独立批次接入；这里先保持 route-aware，
        # 等 validator 模块存在后自动启用语义检查。
        return []
    result = validator(author_formal_dir, lineage_root)
    prefix = semantic_prefixes.get(stage, "TSS-SEMANTIC-001")
    return [f"{prefix}: {error}" for error in result.errors]
