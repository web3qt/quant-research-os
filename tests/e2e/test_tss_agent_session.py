"""TSS Agent Session E2E tests — mirrors CSF agent-session coverage."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.agent_harness import AgentHarness, StageStep
from tests.helpers.human_simulator import HumanResponse, HumanSimulator
from tests.helpers.stage_fixtures import (
    prepare_tss_data_ready,
    prepare_tss_mandate,
    prepare_tss_signal_ready,
)


TSS_SIGNAL_RESPONSES = [
    HumanResponse("mandate", ["research question"], "Can BTCUSDT breakout predict its own next-day path?"),
    HumanResponse("mandate", ["hypothesis"], "A positive breakout event raises next-day forward return."),
    HumanResponse("mandate", ["research_route"], "time_series_signal"),
    HumanResponse("mandate", ["data_source"], "binance um futures klines"),
    HumanResponse("mandate", ["time_split", "train window"], "Train: 2024-01 to 2024-06"),
    HumanResponse("tss_data_ready", ["asset_key"], "asset"),
    HumanResponse("tss_data_ready", ["timestamp_key"], "timestamp"),
    HumanResponse("tss_data_ready", ["bar_size"], "1d"),
    HumanResponse("tss_data_ready", ["label"], "return_1d_forward"),
    HumanResponse("tss_signal_ready", ["signal_id"], "breakout_v1"),
    HumanResponse("tss_signal_ready", ["signal_direction"], "high_better"),
    HumanResponse("tss_signal_ready", ["signal_field"], "signal_value"),
    HumanResponse("tss_signal_ready", ["horizon"], "1d"),
]


MANDATE_QUESTIONS = [
    "What is the research question for this mandate?",
    "What is the primary hypothesis?",
    "Confirm research_route.",
    "What data_source will be used?",
    "Confirm the time_split train window.",
]

TSS_DATA_READY_QUESTIONS = [
    "What should the asset_key be?",
    "What should the timestamp_key be?",
    "What bar_size should be frozen?",
    "Which forward label field should be produced?",
]

TSS_SIGNAL_READY_QUESTIONS = [
    "Specify the signal_id for this signal.",
    "What is the signal_direction?",
    "What is the signal_field name?",
    "Which horizon should be frozen?",
]


class TestTssAgentSessionE2E:
    @pytest.fixture()
    def lineage_root(self, tmp_path: Path) -> Path:
        return tmp_path / "outputs" / "tss_signal_session"

    def test_full_session_passes_all_gates(self, lineage_root: Path) -> None:
        human = HumanSimulator(TSS_SIGNAL_RESPONSES)
        harness = AgentHarness(
            lineage_root,
            stages=[
                StageStep(stage_id="mandate", questions=MANDATE_QUESTIONS, builder=prepare_tss_mandate),
                StageStep(stage_id="tss_data_ready", questions=TSS_DATA_READY_QUESTIONS, builder=prepare_tss_data_ready),
                StageStep(stage_id="tss_signal_ready", questions=TSS_SIGNAL_READY_QUESTIONS, builder=prepare_tss_signal_ready),
            ],
        )

        result = harness.run_session(human)

        assert result.failed_stage is None, f"Session failed at {result.failed_stage}: {result.failure_reason}"
        assert result.completed_stages == ["mandate", "tss_data_ready", "tss_signal_ready"]
        assert result.interactions > 0

    def test_session_tracks_stage_progress(self, lineage_root: Path) -> None:
        human = HumanSimulator(TSS_SIGNAL_RESPONSES)
        harness = AgentHarness(
            lineage_root,
            stages=[
                StageStep(stage_id="mandate", questions=MANDATE_QUESTIONS, builder=prepare_tss_mandate),
                StageStep(stage_id="tss_data_ready", questions=TSS_DATA_READY_QUESTIONS, builder=prepare_tss_data_ready),
            ],
        )

        assert harness.current_stage == "mandate"
        assert not harness.is_complete

        stage = harness.run_stage(human)
        assert stage == "mandate"
        assert harness.current_stage == "tss_data_ready"

        stage = harness.run_stage(human)
        assert stage == "tss_data_ready"
        assert harness.is_complete
        assert harness.completed_stages == ["mandate", "tss_data_ready"]

    def test_human_simulator_tracks_tss_interactions(self) -> None:
        human = HumanSimulator(TSS_SIGNAL_RESPONSES)

        answer = human.respond("What signal_id should we use?", "tss_signal_ready")
        assert answer == "breakout_v1"
        assert human.interactions_count == 1

        answer = human.respond("Confirm signal_direction", "tss_signal_ready")
        assert answer == "high_better"
        assert human.interactions_count == 2

    def test_human_simulator_returns_default_on_unmatched(self) -> None:
        human = HumanSimulator([
            HumanResponse("test_stage", ["specific_keyword"], "specific_answer"),
        ])
        answer = human.respond("Something completely unrelated", "test_stage")
        assert answer == "confirmed"

    def test_session_fails_on_broken_builder(self, lineage_root: Path) -> None:
        def broken_builder(root: Path) -> Path:
            raise RuntimeError("simulated failure")

        human = HumanSimulator(TSS_SIGNAL_RESPONSES)
        harness = AgentHarness(
            lineage_root,
            stages=[
                StageStep(stage_id="mandate", questions=MANDATE_QUESTIONS, builder=broken_builder),
            ],
        )

        result = harness.run_session(human)
        assert result.failed_stage == "mandate"
        assert "simulated failure" in result.failure_reason
