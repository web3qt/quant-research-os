from __future__ import annotations

from typing import Any, Protocol


CLEAR_INSTRUCTION = "Run /clear in Codex or Claude Code before continuing."


class ResumeStatus(Protocol):
    lineage_id: str
    current_stage: str
    review_verdict: str | None
    resume_hint: str
    next_action: str


def _resume_command(lineage_id: str, *, continue_mode: bool = False) -> str:
    command = f"./.qros/bin/qros-resume --lineage-id {lineage_id}"
    if continue_mode:
        command += " --continue"
    return command


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
    recommended_command = _resume_command(status.lineage_id, continue_mode=continue_mode) if clear_required else None
    return {
        "clear_required": clear_required,
        "clear_instruction": CLEAR_INSTRUCTION if clear_required else None,
        "recommended_command": recommended_command,
        "resume_hint": (
            f"{CLEAR_INSTRUCTION} Then run {recommended_command}."
            if clear_required and recommended_command is not None
            else status.resume_hint
        ),
        "next_action": (
            f"Run /clear first, then run {recommended_command}."
            if clear_required and recommended_command is not None
            else status.next_action
        ),
    }


def build_review_clear_resume_notice(
    *,
    lineage_id: str,
    final_verdict: str | None,
    continue_mode: bool = False,
) -> dict[str, Any]:
    clear_required = final_verdict in {"PASS", "CONDITIONAL PASS"}
    recommended_command = _resume_command(lineage_id, continue_mode=continue_mode) if clear_required else None
    return {
        "clear_required": clear_required,
        "clear_instruction": CLEAR_INSTRUCTION if clear_required else None,
        "recommended_command": recommended_command,
        "resume_hint": (
            f"{CLEAR_INSTRUCTION} Then run {recommended_command}."
            if clear_required and recommended_command is not None
            else None
        ),
    }
