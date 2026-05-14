from __future__ import annotations

from typing import Any, Protocol


class HandoffStatus(Protocol):
    current_stage: str
    current_skill: str | None
    why_this_skill: str | None
    next_action: str
    resume_hint: str


def _is_direct_handoff_boundary(current_stage: str) -> bool:
    return current_stage.endswith("_next_stage_confirmation_pending") or current_stage.endswith("_review_complete")


def build_direct_handoff_capsule(status: HandoffStatus) -> dict[str, Any]:
    recommended_skill = (
        None
        if status.current_stage.endswith("holdout_validation_review_complete")
        else status.current_skill
    )
    if recommended_skill is not None and _is_direct_handoff_boundary(status.current_stage):
        handoff_hint = f"Continue with {recommended_skill}."
        next_action = handoff_hint
    else:
        handoff_hint = status.resume_hint
        next_action = status.next_action
    direct_handoff = {
        "recommended_skill": recommended_skill,
        "recommended_skill_reason": status.why_this_skill,
        "handoff_hint": handoff_hint,
        "next_action": next_action,
        "resume_hint": handoff_hint,
    }
    return direct_handoff


def build_review_handoff_notice(
    *,
    final_verdict: str | None,
    stage: str | None = None,
) -> dict[str, Any]:
    if final_verdict not in {"PASS", "CONDITIONAL PASS"}:
        return {
            "recommended_skill": None,
            "recommended_skill_reason": None,
            "handoff_hint": None,
        }
    if stage in {"holdout_validation", "csf_holdout_validation"}:
        return {
            "recommended_skill": None,
            "recommended_skill_reason": None,
            "handoff_hint": None,
        }
    recommended_skill = "qros-research-session"
    return {
        "recommended_skill": recommended_skill,
        "recommended_skill_reason": (
            f"{stage or 'review'} {final_verdict} hands control back to qros-research-session "
            "for next-stage confirmation."
        ),
        "handoff_hint": f"Continue with {recommended_skill}.",
    }
