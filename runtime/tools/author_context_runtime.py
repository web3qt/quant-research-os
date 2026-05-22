from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ARTIFACT_CONTRACTS
from runtime.tools.data_ready_runtime import DATA_READY_FREEZE_GROUP_ORDER
from runtime.tools.backtest_runtime import BACKTEST_READY_GROUP_ORDER
from runtime.tools.csf_backtest_runtime import CSF_BACKTEST_READY_GROUP_ORDER
from runtime.tools.csf_data_ready_runtime import CSF_DATA_READY_FREEZE_GROUP_ORDER
from runtime.tools.csf_holdout_runtime import CSF_HOLDOUT_VALIDATION_GROUP_ORDER
from runtime.tools.csf_signal_ready_runtime import CSF_SIGNAL_READY_FREEZE_GROUP_ORDER
from runtime.tools.csf_test_evidence_runtime import CSF_TEST_EVIDENCE_GROUP_ORDER
from runtime.tools.csf_train_runtime import CSF_TRAIN_FREEZE_GROUP_ORDER
from runtime.tools.holdout_runtime import HOLDOUT_VALIDATION_GROUP_ORDER
from runtime.tools.idea_runtime import MANDATE_FREEZE_GROUP_ORDER
from runtime.tools.mandate_admission_runtime import assess_time_coverage_preflight
from runtime.tools.review_skillgen.loaders import load_gate_schema
from runtime.tools.review_skillgen.review_engine import GATES_PATH, ROOT
from runtime.tools.signal_ready_runtime import SIGNAL_READY_FREEZE_GROUP_ORDER
from runtime.tools.test_evidence_runtime import TEST_EVIDENCE_GROUP_ORDER
from runtime.tools.train_runtime import TRAIN_FREEZE_GROUP_ORDER

try:
    from runtime.tools.tss_backtest_runtime import TSS_BACKTEST_READY_GROUP_ORDER
except ModuleNotFoundError:
    TSS_BACKTEST_READY_GROUP_ORDER = ("execution_policy", "portfolio_policy", "risk_overlay", "engine_contract", "delivery_contract")

try:
    from runtime.tools.tss_data_ready_runtime import TSS_DATA_READY_FREEZE_GROUP_ORDER
except ModuleNotFoundError:
    TSS_DATA_READY_FREEZE_GROUP_ORDER = ("extraction_contract", "quality_semantics", "universe_admission", "shared_derived_layer", "delivery_contract")

try:
    from runtime.tools.tss_holdout_runtime import TSS_HOLDOUT_VALIDATION_GROUP_ORDER
except ModuleNotFoundError:
    TSS_HOLDOUT_VALIDATION_GROUP_ORDER = ("reuse_contract", "drift_audit", "failure_governance", "delivery_contract", "audit_contract")

try:
    from runtime.tools.tss_signal_ready_runtime import TSS_SIGNAL_READY_FREEZE_GROUP_ORDER
except ModuleNotFoundError:
    TSS_SIGNAL_READY_FREEZE_GROUP_ORDER = ("signal_expression", "param_identity", "time_semantics", "signal_schema", "delivery_contract")

try:
    from runtime.tools.tss_test_evidence_runtime import TSS_TEST_EVIDENCE_GROUP_ORDER
except ModuleNotFoundError:
    TSS_TEST_EVIDENCE_GROUP_ORDER = ("formal_gate_contract", "admissibility_contract", "audit_contract", "delivery_contract", "window_contract")

try:
    from runtime.tools.tss_train_runtime import TSS_TRAIN_FREEZE_GROUP_ORDER
except ModuleNotFoundError:
    TSS_TRAIN_FREEZE_GROUP_ORDER = ("window_contract", "threshold_contract", "quality_filters", "param_governance", "delivery_contract")


STAGE_AUTHOR_CONTEXT_YAML_FILENAME = "stage_author_context.yaml"
STAGE_AUTHOR_CONTEXT_MD_FILENAME = "stage_author_context.md"

_STAGE_GATE_KEY_BY_STAGE_ID = {
    "train_freeze": "train_calibration",
}


_STAGE_FREEZE_GROUP_ORDER: dict[str, tuple[str, ...]] = {
    "idea_intake": ("research_intent", "observation_contract", "qualification_contract"),
    "mandate": tuple(MANDATE_FREEZE_GROUP_ORDER),
    "data_ready": tuple(DATA_READY_FREEZE_GROUP_ORDER),
    "signal_ready": tuple(SIGNAL_READY_FREEZE_GROUP_ORDER),
    "train_freeze": tuple(TRAIN_FREEZE_GROUP_ORDER),
    "test_evidence": tuple(TEST_EVIDENCE_GROUP_ORDER),
    "backtest_ready": tuple(BACKTEST_READY_GROUP_ORDER),
    "holdout_validation": tuple(HOLDOUT_VALIDATION_GROUP_ORDER),
    "csf_data_ready": tuple(CSF_DATA_READY_FREEZE_GROUP_ORDER),
    "csf_signal_ready": tuple(CSF_SIGNAL_READY_FREEZE_GROUP_ORDER),
    "csf_train_freeze": tuple(CSF_TRAIN_FREEZE_GROUP_ORDER),
    "csf_test_evidence": tuple(CSF_TEST_EVIDENCE_GROUP_ORDER),
    "csf_backtest_ready": tuple(CSF_BACKTEST_READY_GROUP_ORDER),
    "csf_holdout_validation": tuple(CSF_HOLDOUT_VALIDATION_GROUP_ORDER),
    "tss_data_ready": tuple(TSS_DATA_READY_FREEZE_GROUP_ORDER),
    "tss_signal_ready": tuple(TSS_SIGNAL_READY_FREEZE_GROUP_ORDER),
    "tss_train_freeze": tuple(TSS_TRAIN_FREEZE_GROUP_ORDER),
    "tss_test_evidence": tuple(TSS_TEST_EVIDENCE_GROUP_ORDER),
    "tss_backtest_ready": tuple(TSS_BACKTEST_READY_GROUP_ORDER),
    "tss_holdout_validation": tuple(TSS_HOLDOUT_VALIDATION_GROUP_ORDER),
}

_NEXT_SUCCESS_STAGE: dict[str, str] = {
    "idea_intake": "mandate_confirmation_pending",
    "mandate": "mandate_review_confirmation_pending",
    "data_ready": "data_ready_review_confirmation_pending",
    "signal_ready": "signal_ready_review_confirmation_pending",
    "train_freeze": "train_freeze_review_confirmation_pending",
    "test_evidence": "test_evidence_review_confirmation_pending",
    "backtest_ready": "backtest_ready_review_confirmation_pending",
    "holdout_validation": "holdout_validation_review_confirmation_pending",
    "csf_data_ready": "csf_data_ready_review_confirmation_pending",
    "csf_signal_ready": "csf_signal_ready_review_confirmation_pending",
    "csf_train_freeze": "csf_train_freeze_review_confirmation_pending",
    "csf_test_evidence": "csf_test_evidence_review_confirmation_pending",
    "csf_backtest_ready": "csf_backtest_ready_review_confirmation_pending",
    "csf_holdout_validation": "csf_holdout_validation_review_confirmation_pending",
    "tss_data_ready": "tss_data_ready_review_confirmation_pending",
    "tss_signal_ready": "tss_signal_ready_review_confirmation_pending",
    "tss_train_freeze": "tss_train_freeze_review_confirmation_pending",
    "tss_test_evidence": "tss_test_evidence_review_confirmation_pending",
    "tss_backtest_ready": "tss_backtest_ready_review_confirmation_pending",
    "tss_holdout_validation": "tss_holdout_validation_review_confirmation_pending",
}


def _repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def _gate_stage_contract(stage_id: str) -> dict[str, Any]:
    gates = load_gate_schema(GATES_PATH)
    gate_stage_id = _STAGE_GATE_KEY_BY_STAGE_ID.get(stage_id, stage_id)
    stage_contract = gates["stages"].get(gate_stage_id)
    if not isinstance(stage_contract, dict):
        raise ValueError(f"AUTHOR_CONTEXT_MISSING: missing stage gate contract for stage {stage_id}")
    return stage_contract


def _artifact_contract_for_stage(stage_id: str) -> str | None:
    contract_path = ARTIFACT_CONTRACTS.get(stage_id)
    if contract_path is None:
        inferred = ROOT / "contracts" / "artifacts" / f"{stage_id}_artifacts.yaml"
        if inferred.exists():
            return _repo_relative(inferred)
        return None
    return _repo_relative(contract_path)


def _default_orchestration_for_stage(stage_id: str) -> dict[str, Any]:
    freeze_group_order = _STAGE_FREEZE_GROUP_ORDER.get(stage_id)
    if freeze_group_order is None:
        raise ValueError(f"AUTHOR_CONTEXT_MISSING: missing freeze group order for stage {stage_id}")
    if stage_id == "idea_intake":
        allowed_runtime_stages = ["idea_intake_confirmation_pending", "idea_intake"]
        author_fix_reentry_stage = "idea_intake_confirmation_pending"
        interaction_mode = "interactive_intake"
    else:
        allowed_runtime_stages = [f"{stage_id}_confirmation_pending", f"{stage_id}_author"]
        author_fix_reentry_stage = f"{stage_id}_author"
        interaction_mode = "contract_freeze"
    next_success_stage = _NEXT_SUCCESS_STAGE.get(stage_id)
    if next_success_stage is None:
        raise ValueError(f"AUTHOR_CONTEXT_MISSING: missing next success stage for stage {stage_id}")
    return {
        "allowed_runtime_stages": allowed_runtime_stages,
        "freeze_group_order": list(freeze_group_order),
        "supports_confirm_all": True,
        "requires_final_author_confirmation": True,
        "next_success_stage": next_success_stage,
        "author_fix_reentry_stage": author_fix_reentry_stage,
        "failure_handoff_skill": "qros-stage-failure-handler",
        "interaction_mode": interaction_mode,
    }


def _truth_for_stage(stage_id: str) -> dict[str, Any]:
    stage_contract = _gate_stage_contract(stage_id)
    validator_requirements = []
    preflight_requirements = []
    if stage_id == "idea_intake":
        validator_requirements.append("qros-validate-stage --stage idea_intake")
    else:
        validator_requirements.append(f"qros-validate-stage --stage {stage_id}")
        preflight_requirements.append("deterministic_preflight")
    return {
        "artifact_contract": _artifact_contract_for_stage(stage_id),
        "required_inputs": list(stage_contract.get("required_inputs", [])),
        "required_outputs": list(stage_contract.get("required_outputs", [])),
        "validator_requirements": validator_requirements,
        "preflight_requirements": preflight_requirements,
        "failure_route_conditions": [
            "current_stage_mismatch",
            "freeze_groups_unconfirmed",
            "validator_failed",
            "preflight_failed",
            "placeholder_outputs",
        ],
    }


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _research_preflight_truth(stage_id: str, review_cycle_stage_dir: Path) -> dict[str, Any] | None:
    if stage_id != "mandate":
        return None

    draft_path = review_cycle_stage_dir / "author" / "draft" / "mandate_freeze_draft.yaml"
    if not draft_path.exists():
        return None

    payload = _read_yaml(draft_path)
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        return None

    scope_group = groups.get("scope_contract", {})
    data_group = groups.get("data_contract", {})
    if not isinstance(scope_group, dict) or not isinstance(data_group, dict):
        return None

    scope_contract = scope_group.get("draft", {})
    data_contract = data_group.get("draft", {})
    if not isinstance(scope_contract, dict) or not isinstance(data_contract, dict):
        return None

    preflight_status = assess_time_coverage_preflight(
        data_source=data_contract.get("data_source", ""),
        time_boundary=scope_contract.get("time_boundary", ""),
    )
    if preflight_status is None:
        return None

    return {
        "passable": preflight_status.passable,
        "blocker_family": preflight_status.blocker_family,
        "blocker_code": preflight_status.blocker_code,
        "blocker_reason": preflight_status.blocker_reason,
        "next_action": preflight_status.next_action,
    }


def _guidance_for_stage(stage_id: str) -> dict[str, Any]:
    author_focus = [
        "Confirm unresolved freeze groups before build.",
        "Do not treat placeholder outputs as complete.",
        "Run validation before claiming the stage is author-complete.",
    ]
    if stage_id == "idea_intake":
        author_focus.insert(0, "Stop and ask clarifying questions before qualification claims.")
    return {
        "author_focus": author_focus,
        "user_prompt_hints": [
            "Summarize the next unresolved group before asking for confirmation.",
        ],
        "group_summary_template": "Show unresolved groups and confirmed groups before the next question.",
        "build_readiness_message": "All required groups are confirmed. Request final author confirmation before build.",
        "common_pitfalls": [
            "Do not bypass current_stage.",
            "Do not skip final author confirmation.",
        ],
        "do_not_claim_complete_until": [
            "validator passes",
            "preflight passes or is not required",
        ],
    }


def build_stage_author_context(
    *,
    stage_id: str,
    current_stage: str,
    lineage_id: str,
    route: str,
    review_cycle_stage_dir: Path,
) -> dict[str, Any]:
    stage_contract = _gate_stage_contract(stage_id)
    truth = _truth_for_stage(stage_id)
    research_preflight = _research_preflight_truth(stage_id, review_cycle_stage_dir)
    if research_preflight is not None:
        truth["research_preflight"] = research_preflight
    return {
        "lineage_id": lineage_id,
        "stage_id": stage_id,
        "stage_name": stage_contract["stage_name"],
        "route": route,
        "current_stage": current_stage,
        "truth": truth,
        "orchestration": _default_orchestration_for_stage(stage_id),
        "guidance": _guidance_for_stage(stage_id),
        "stage_dir": str(review_cycle_stage_dir),
    }


def render_stage_author_context_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['stage_name']} Author Context",
        "",
        "This file is the current-stage author truth entrypoint for session author orchestration.",
        f"Stage id: {payload['stage_id']}",
        "",
        "## Interaction Order",
    ]
    for item in payload["orchestration"]["freeze_group_order"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Author Focus",
            *[f"- {item}" for item in payload["guidance"]["author_focus"]],
            "",
            "## Notes",
            f"- supports confirm all: {payload['orchestration']['supports_confirm_all']}",
            f"- requires final author confirmation: {payload['orchestration']['requires_final_author_confirmation']}",
        ]
    )
    return "\n".join(lines) + "\n"
