from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from runtime.tools.lineage_lock_ledger import FrozenArtifactMutationError, assert_lineage_locks_intact
from runtime.tools.progress_runtime import latest_lineage_id
from runtime.tools.research_session import (
    STAGE_ACTIVE_SKILLS,
    SessionStage,
    assert_current_protected_review_state_intact,
    detect_session_stage,
)
from runtime.tools.review_skillgen.protected_state_guard import ProtectedStateError


StageEntryLane = Literal["author", "review"]


@dataclass(frozen=True)
class StageEntryGuardResult:
    allowed: bool
    lineage_id: str
    current_stage: str
    current_active_skill: str
    requested_stage: str
    requested_lane: StageEntryLane
    expected_stages: tuple[str, ...]
    recovery_command: str
    message: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["expected_stages"] = list(self.expected_stages)
        return payload


class StageEntryGuardError(RuntimeError):
    def __init__(self, result: StageEntryGuardResult) -> None:
        super().__init__(result.message)
        self.result = result


def expected_stages_for_entry(*, stage: str, lane: StageEntryLane) -> tuple[str, ...]:
    if lane == "author":
        if stage == "idea_intake":
            return ("idea_intake", "idea_intake_confirmation_pending")
        return (f"{stage}_confirmation_pending", f"{stage}_author")
    if lane == "review":
        return (f"{stage}_review_confirmation_pending", f"{stage}_review")
    raise ValueError(f"unsupported lane: {lane}")


def _active_skill_for_stage(current_stage: str) -> str:
    return STAGE_ACTIVE_SKILLS.get(current_stage, "qros-research-session")  # type: ignore[arg-type]


def _recovery_command(lineage_id: str) -> str:
    return f"qros-research-session --lineage-id {lineage_id}"


def check_stage_entry_for_lineage(
    lineage_root: Path,
    *,
    stage: str,
    lane: StageEntryLane,
    raise_on_block: bool = True,
) -> StageEntryGuardResult:
    current_stage: SessionStage = detect_session_stage(lineage_root)
    expected_stages = expected_stages_for_entry(stage=stage, lane=lane)
    lineage_id = lineage_root.name
    recovery_command = _recovery_command(lineage_id)
    try:
        assert_lineage_locks_intact(lineage_root)
    except FrozenArtifactMutationError as exc:
        result = StageEntryGuardResult(
            allowed=False,
            lineage_id=lineage_id,
            current_stage=current_stage,
            current_active_skill="qros-research-session",
            requested_stage=stage,
            requested_lane=lane,
            expected_stages=expected_stages,
            recovery_command=recovery_command,
            message=str(exc),
        )
        if raise_on_block:
            raise StageEntryGuardError(result)
        return result
    try:
        assert_current_protected_review_state_intact(
            lineage_root=lineage_root,
            current_stage=current_stage,
        )
    except ProtectedStateError as exc:
        result = StageEntryGuardResult(
            allowed=False,
            lineage_id=lineage_id,
            current_stage=current_stage,
            current_active_skill="qros-research-session",
            requested_stage=stage,
            requested_lane=lane,
            expected_stages=expected_stages,
            recovery_command=exc.next_action,
            message=str(exc),
        )
        if raise_on_block:
            raise StageEntryGuardError(result)
        return result

    current_active_skill = _active_skill_for_stage(current_stage)

    if current_stage in expected_stages:
        result = StageEntryGuardResult(
            allowed=True,
            lineage_id=lineage_id,
            current_stage=current_stage,
            current_active_skill=current_active_skill,
            requested_stage=stage,
            requested_lane=lane,
            expected_stages=expected_stages,
            recovery_command=recovery_command,
            message=(
                f"Stage entry allowed for requested {stage} {lane}; "
                f"observed current_stage={current_stage}."
            ),
        )
        return result

    # stage-specific skill 的第一步必须给出可恢复的错位诊断，不能让 agent 继续猜。
    result = StageEntryGuardResult(
        allowed=False,
        lineage_id=lineage_id,
        current_stage=current_stage,
        current_active_skill=current_active_skill,
        requested_stage=stage,
        requested_lane=lane,
        expected_stages=expected_stages,
        recovery_command=recovery_command,
        message=(
            f"Stage entry blocked: observed current_stage={current_stage}, "
            f"but requested {stage} {lane}. Expected one of: "
            f"{', '.join(expected_stages)}. Current active skill is {current_active_skill}. "
            f"Recover through {recovery_command}."
        ),
    )
    if raise_on_block:
        raise StageEntryGuardError(result)
    return result


def check_stage_entry(
    *,
    outputs_root: Path,
    stage: str,
    lane: StageEntryLane,
    lineage_id: str | None = None,
    raise_on_block: bool = True,
) -> StageEntryGuardResult:
    selected_lineage_id = lineage_id or latest_lineage_id(outputs_root)
    lineage_root = outputs_root / selected_lineage_id
    if not lineage_root.exists() or not lineage_root.is_dir():
        result = StageEntryGuardResult(
            allowed=False,
            lineage_id=selected_lineage_id,
            current_stage="unknown",
            current_active_skill="qros-research-session",
            requested_stage=stage,
            requested_lane=lane,
            expected_stages=expected_stages_for_entry(stage=stage, lane=lane),
            recovery_command=_recovery_command(selected_lineage_id),
            message=f"QROS lineage not found: {lineage_root}. Recover through {_recovery_command(selected_lineage_id)}.",
        )
        if raise_on_block:
            raise StageEntryGuardError(result)
        return result
    return check_stage_entry_for_lineage(
        lineage_root,
        stage=stage,
        lane=lane,
        raise_on_block=raise_on_block,
    )
