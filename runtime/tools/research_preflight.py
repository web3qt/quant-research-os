from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchPreflightStatus:
    passable: bool
    blocker_family: str | None
    blocker_code: str | None
    blocker_reason: str | None
    next_action: str | None


def compute_research_preflight(
    *,
    stage: str,
    user_confirmed: dict[str, str],
    runtime_facts: dict[str, str],
) -> ResearchPreflightStatus:
    # 先只锁定 mandate 阶段最基础的真实数据覆盖边界，避免后续评审再做一轮发现式排错。
    if stage == "mandate":
        train_start = user_confirmed["train_start"]
        holdout_end = user_confirmed["holdout_end"]
        data_min_ts = runtime_facts["data_min_ts"]
        data_max_ts = runtime_facts["data_max_ts"]
        if train_start < data_min_ts or holdout_end > data_max_ts:
            return ResearchPreflightStatus(
                passable=False,
                blocker_family="time_coverage_contract",
                blocker_code="TIME_COVERAGE_OUT_OF_RANGE",
                blocker_reason="Frozen review windows exceed real data coverage.",
                next_action=(
                    "Adjust train/test/backtest/holdout to fit actual data "
                    "coverage before mandate freeze."
                ),
            )

    return ResearchPreflightStatus(
        passable=True,
        blocker_family=None,
        blocker_code=None,
        blocker_reason=None,
        next_action=None,
    )
