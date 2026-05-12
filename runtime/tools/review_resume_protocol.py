from __future__ import annotations

from typing import Any, Protocol


CLEAR_INSTRUCTION = "Run /clear in Codex or Claude Code before continuing."

NEXT_AUTHOR_SKILL_BY_REVIEWED_STAGE: dict[str, str] = {
    "mandate:cross_sectional_factor": "qros-csf-data-ready-author",
    "mandate:time_series_signal": "qros-tss-data-ready-author",
    "data_ready": "qros-signal-ready-author",
    "signal_ready": "qros-train-freeze-author",
    "train_freeze": "qros-test-evidence-author",
    "test_evidence": "qros-backtest-ready-author",
    "backtest_ready": "qros-holdout-validation-author",
    "csf_data_ready": "qros-csf-signal-ready-author",
    "csf_signal_ready": "qros-csf-train-freeze-author",
    "csf_train_freeze": "qros-csf-test-evidence-author",
    "csf_test_evidence": "qros-csf-backtest-ready-author",
    "csf_backtest_ready": "qros-csf-holdout-validation-author",
    "tss_data_ready": "qros-tss-signal-ready-author",
    "tss_signal_ready": "qros-tss-train-freeze-author",
    "tss_train_freeze": "qros-tss-test-evidence-author",
    "tss_test_evidence": "qros-tss-backtest-ready-author",
    "tss_backtest_ready": "qros-tss-holdout-validation-author",
}


class ResumeStatus(Protocol):
    lineage_id: str
    current_stage: str
    current_route: str | None
    review_verdict: str | None
    resume_hint: str
    next_action: str


def _resume_command(lineage_id: str, *, continue_mode: bool = False) -> str:
    command = f"./.qros/bin/qros-resume --lineage-id {lineage_id}"
    if continue_mode:
        command += " --continue"
    return command


def _stage_base(current_stage: str) -> str:
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


def _recommended_skill_for_stage(stage_base: str, current_route: str | None) -> str | None:
    if stage_base == "mandate" and current_route is not None:
        return NEXT_AUTHOR_SKILL_BY_REVIEWED_STAGE.get(f"mandate:{current_route}")
    return NEXT_AUTHOR_SKILL_BY_REVIEWED_STAGE.get(stage_base)


def _recommended_skill_reason(
    *,
    stage_base: str,
    review_verdict: str | None,
    recommended_skill: str | None,
) -> str | None:
    if recommended_skill is None or review_verdict is None:
        return None
    next_stage = recommended_skill.removeprefix("qros-").removesuffix("-author").replace("-", "_")
    return f"{stage_base} {review_verdict} allows {next_stage} authoring after next-stage handoff."


def _should_request_clear(status: ResumeStatus) -> bool:
    if status.review_verdict not in {"PASS", "CONDITIONAL PASS"}:
        return False
    return status.current_stage.endswith("_review_complete") or status.current_stage.endswith(
        "_next_stage_confirmation_pending"
    )


def build_clear_resume_capsule(
    status: ResumeStatus,
    *,
    continue_mode: bool = False,
) -> dict[str, Any]:
    clear_required = _should_request_clear(status)
    stage_base = _stage_base(status.current_stage)
    recommended_skill = (
        _recommended_skill_for_stage(stage_base, status.current_route)
        if clear_required
        else None
    )
    backend_resume_command = _resume_command(status.lineage_id, continue_mode=continue_mode) if clear_required else None
    recommended_skill_reason = _recommended_skill_reason(
        stage_base=stage_base,
        review_verdict=status.review_verdict,
        recommended_skill=recommended_skill,
    )
    return {
        "clear_required": clear_required,
        "clear_instruction": CLEAR_INSTRUCTION if clear_required else None,
        "recommended_skill": recommended_skill,
        "recommended_skill_reason": recommended_skill_reason,
        "backend_resume_command": backend_resume_command,
        "resume_hint": (
            f"{CLEAR_INSTRUCTION} Then enter {recommended_skill} in the new session."
            if clear_required and recommended_skill is not None
            else status.resume_hint
        ),
        "next_action": (
            f"Run /clear first, then enter {recommended_skill} in the new session."
            if clear_required and recommended_skill is not None
            else status.next_action
        ),
    }


def build_review_clear_resume_notice(
    *,
    lineage_id: str,
    final_verdict: str | None,
    stage: str | None = None,
    current_route: str | None = None,
    continue_mode: bool = False,
) -> dict[str, Any]:
    clear_required = final_verdict in {"PASS", "CONDITIONAL PASS"}
    stage_base = _stage_base(stage or "")
    recommended_skill = (
        _recommended_skill_for_stage(stage_base, current_route)
        if clear_required and stage is not None
        else None
    )
    backend_resume_command = _resume_command(lineage_id, continue_mode=continue_mode) if clear_required else None
    recommended_skill_reason = _recommended_skill_reason(
        stage_base=stage_base,
        review_verdict=final_verdict,
        recommended_skill=recommended_skill,
    )
    return {
        "clear_required": clear_required,
        "clear_instruction": CLEAR_INSTRUCTION if clear_required else None,
        "recommended_skill": recommended_skill,
        "recommended_skill_reason": recommended_skill_reason,
        "backend_resume_command": backend_resume_command,
        "resume_hint": (
            f"{CLEAR_INSTRUCTION} Then enter {recommended_skill} in the new session."
            if clear_required and recommended_skill is not None
            else None
        ),
    }
