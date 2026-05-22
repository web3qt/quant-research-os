from __future__ import annotations

from pathlib import Path

from runtime.tools.research_preflight import (
    ResearchPreflightStatus,
    compute_research_preflight,
)


def test_compute_research_preflight_blocks_when_time_window_exceeds_real_data_coverage(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)

    status = compute_research_preflight(
        stage="mandate",
        user_confirmed={
            "research_route": "cross_sectional_factor",
            "bar_size": "5m",
            "train_start": "2023-01-01",
            "holdout_end": "2026-03-01",
        },
        runtime_facts={
            "data_min_ts": "2024-03-01",
            "data_max_ts": "2024-12-31",
        },
    )

    assert status == ResearchPreflightStatus(
        passable=False,
        blocker_family="time_coverage_contract",
        blocker_code="TIME_COVERAGE_OUT_OF_RANGE",
        blocker_reason="Frozen review windows exceed real data coverage.",
        next_action=(
            "Adjust train/test/backtest/holdout to fit actual data coverage "
            "before mandate freeze."
        ),
    )


def test_compute_research_preflight_allows_route_and_time_window_when_facts_align(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)

    status = compute_research_preflight(
        stage="mandate",
        user_confirmed={
            "research_route": "cross_sectional_factor",
            "bar_size": "5m",
            "train_start": "2024-03-01",
            "holdout_end": "2024-12-31",
        },
        runtime_facts={
            "data_min_ts": "2024-03-01",
            "data_max_ts": "2024-12-31",
        },
    )

    assert status.passable is True
    assert status.blocker_family is None
    assert status.blocker_code is None
