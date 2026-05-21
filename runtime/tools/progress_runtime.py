from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from runtime.tools.lineage_lock_ledger import FrozenArtifactMutationError, assert_lineage_locks_intact
from runtime.tools.review_eligibility import compute_review_eligibility
from runtime.tools.research_session import (
    STAGE_ACTIVE_SKILLS,
    _stage_base_name,
    assert_current_protected_review_state_intact,
    _gate_status_and_next_action,
    _latest_failure_package_runtime_status,
    _latest_review_failure_status,
    _lineage_lock_blocked_status,
    _protected_state_blocked_status,
    current_research_route,
    current_route_contract,
    detect_session_stage,
    session_transition_summary,
    summarize_session_status,
)
from runtime.tools.review_skillgen.protected_state_guard import ProtectedStateError
from runtime.tools.review_resume_protocol import build_direct_handoff_capsule


class ProgressError(RuntimeError):
    pass


def _lineage_latest_mtime(lineage_root: Path) -> float:
    latest = lineage_root.stat().st_mtime
    for path in lineage_root.rglob("*"):
        latest = max(latest, path.stat().st_mtime)
    return latest


def latest_lineage_id(outputs_root: Path) -> str:
    if not outputs_root.exists():
        raise ProgressError(f"No QROS outputs directory found: {outputs_root}")
    lineage_dirs = [path for path in outputs_root.iterdir() if path.is_dir()]
    if not lineage_dirs:
        raise ProgressError(f"No QROS lineage directories found under: {outputs_root}")
    latest = max(lineage_dirs, key=lambda path: (_lineage_latest_mtime(path), path.name))
    return latest.name


def _read_only_session_status(lineage_root: Path, *, selection_mode: str):
    # qros-progress 只能读现有状态，不能走会 scaffold 或写 confirmation 的 session 入口。
    try:
        assert_lineage_locks_intact(lineage_root)
    except FrozenArtifactMutationError as exc:
        return _lineage_lock_blocked_status(
            lineage_root=lineage_root,
            lineage_mode=f"progress_{selection_mode}",
            lineage_selection_reason=f"qros-progress selected {lineage_root.name} using {selection_mode} mode",
            violation=exc,
        )
    current_stage = detect_session_stage(lineage_root)
    try:
        assert_current_protected_review_state_intact(
            lineage_root=lineage_root,
            current_stage=current_stage,
        )
    except ProtectedStateError as exc:
        return _protected_state_blocked_status(
            lineage_root=lineage_root,
            lineage_mode=f"progress_{selection_mode}",
            lineage_selection_reason=f"qros-progress selected {lineage_root.name} using {selection_mode} mode",
            violation=exc,
        )
    gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
    review_verdict, requires_failure_handling, failure_stage, failure_reason_summary = (
        _latest_review_failure_status(lineage_root)
    )
    failure_package_status = _latest_failure_package_runtime_status(lineage_root)
    current_skill_override = failure_package_status.current_skill if failure_package_status else None
    why_this_skill_override = failure_package_status.why_this_skill if failure_package_status else None
    blocking_reason_override = failure_package_status.blocking_reason if failure_package_status else None
    resume_hint_override = failure_package_status.resume_hint if failure_package_status else None
    runtime_stage_status_override = failure_package_status.stage_status if failure_package_status else None
    runtime_blocking_reason_code_override = (
        failure_package_status.blocking_reason_code if failure_package_status else None
    )
    runtime_next_action_override = failure_package_status.next_action if failure_package_status else None
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
    elif current_stage.endswith("_review_confirmation_pending"):
        review_skill = STAGE_ACTIVE_SKILLS.get(current_stage, "qros-review")
        eligibility = compute_review_eligibility(
            lineage_root=lineage_root,
            current_stage=current_stage,
            review_skill=review_skill,
        )
        if not eligibility.eligible_for_review:
            requires_failure_handling = eligibility.requires_failure_handling
            failure_stage = (
                _stage_base_name(str(eligibility.failure_stage))
                if eligibility.failure_stage is not None
                else None
            )
            failure_reason_summary = eligibility.failure_reason_summary
            blocking_reason_override = eligibility.blocking_reason
            runtime_blocking_reason_code_override = eligibility.blocking_reason_code
            if eligibility.requires_failure_handling:
                gate_status = "FAILURE_HANDLING_REQUIRED"
                next_action = (
                    f"Enter failure handling for {failure_stage} via qros-stage-failure-handler"
                )
                current_skill_override = "qros-stage-failure-handler"
                runtime_stage_status_override = "blocked_requires_failure_handling"
                runtime_next_action_override = next_action
            else:
                gate_status = "OUTPUTS_INVALID"
                next_action = str(
                    eligibility.blocking_reason
                    or "Resolve canonical review eligibility blockers before entering review."
                )
                runtime_stage_status_override = "awaiting_author_fix"
                runtime_next_action_override = next_action

    why_now, open_risks = session_transition_summary(lineage_root, current_stage)
    route_contract = current_route_contract(lineage_root)
    return summarize_session_status(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        lineage_mode=f"progress_{selection_mode}",
        lineage_selection_reason=f"qros-progress selected {lineage_root.name} using {selection_mode} mode",
        current_stage=current_stage,
        current_route=current_research_route(lineage_root),
        artifacts_written=[],
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
        current_skill=current_skill_override,
        why_this_skill=why_this_skill_override,
        blocking_reason=blocking_reason_override,
        resume_hint=resume_hint_override,
        runtime_stage_status_override=runtime_stage_status_override,
        runtime_blocking_reason_code_override=runtime_blocking_reason_code_override,
        runtime_next_action_override=runtime_next_action_override,
    )


def progress_status_payload(*, outputs_root: Path, lineage_id: str | None = None) -> dict[str, object]:
    selection_mode = "explicit" if lineage_id else "latest"
    selected_lineage_id = lineage_id or latest_lineage_id(outputs_root)
    lineage_root = outputs_root / selected_lineage_id
    if not lineage_root.exists() or not lineage_root.is_dir():
        raise ProgressError(f"QROS lineage not found: {lineage_root}")

    status = _read_only_session_status(lineage_root, selection_mode=selection_mode)
    payload = asdict(status)
    payload["lineage_root"] = str(status.lineage_root)
    payload["selection_mode"] = selection_mode
    direct_handoff = build_direct_handoff_capsule(status)
    payload.update(direct_handoff)
    return payload
