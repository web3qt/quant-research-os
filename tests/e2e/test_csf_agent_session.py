"""CSF Agent Session E2E tests — Layer 3.

Simulates a full CSF momentum research session driven by a mock agent.
The agent asks pre-scripted questions, a HumanSimulator answers them,
and the harness verifies all gates pass at each stage.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.agent_harness import AgentHarness, StageStep
from tests.helpers.human_simulator import HumanResponse, HumanSimulator
from tests.helpers.stage_fixtures import (
    prepare_csf_data_ready,
    prepare_csf_signal_ready,
    prepare_mandate,
)


# ---------------------------------------------------------------------------
# Pre-recorded human responses for a CSF momentum research line
# ---------------------------------------------------------------------------

CSF_MOMENTUM_RESPONSES = [
    # Mandate stage
    HumanResponse("mandate", ["research question"], "Does BTC momentum predict ALT returns cross-sectionally?"),
    HumanResponse("mandate", ["hypothesis"], "BTC lead effect transfers to ALTs within the same cross-section."),
    HumanResponse("mandate", ["factor_role"], "standalone_alpha"),
    HumanResponse("mandate", ["factor_structure"], "single_factor"),
    HumanResponse("mandate", ["portfolio_expression"], "long_short_market_neutral"),
    HumanResponse("mandate", ["neutralization"], "group_neutral"),
    HumanResponse("mandate", ["data_source"], "binance um futures klines"),
    HumanResponse("mandate", ["time_split", "train window"], "Train: 2024-01 to 2024-06"),
    # CSF data_ready stage
    HumanResponse("csf_data_ready", ["panel_primary_key", "panel key"], "date, asset"),
    HumanResponse("csf_data_ready", ["coverage_floor", "coverage rule"], "95% minimum coverage per cross-section"),
    HumanResponse("csf_data_ready", ["eligibility", "exclusion"], "Drop assets below minimum dollar volume"),
    HumanResponse("csf_data_ready", ["taxonomy", "group"], "sector_bucket_v1"),
    # CSF signal_ready stage
    HumanResponse("csf_signal_ready", ["factor_id"], "btc_lead_alt_follow"),
    HumanResponse("csf_signal_ready", ["factor_direction"], "high_better"),
    HumanResponse("csf_signal_ready", ["final_score"], "factor_value"),
    HumanResponse("csf_signal_ready", ["score_combination", "combination formula"], "single_factor_passthrough"),
    HumanResponse("csf_signal_ready", ["missing_value", "null"], "Preserve nulls and report eligibility separately"),
]


# ---------------------------------------------------------------------------
# Session scripts — define the agent's question flow per stage
# ---------------------------------------------------------------------------

MANDATE_QUESTIONS = [
    "What is the research question for this mandate?",
    "What is the primary hypothesis?",
    "What factor_role should be assigned? (standalone_alpha / regime_filter / combo_filter)",
    "What factor_structure? (single_factor / multi_factor_score)",
    "What portfolio_expression is appropriate?",
    "What neutralization_policy should be applied?",
    "What data_source will be used?",
    "Confirm the time_split train window.",
]

CSF_DATA_READY_QUESTIONS = [
    "What should the panel_primary_key be?",
    "What coverage_floor_rule should we set?",
    "Define the eligibility_base_rule.",
    "Which group_taxonomy_reference should we freeze?",
]

CSF_SIGNAL_READY_QUESTIONS = [
    "Specify the factor_id for this signal.",
    "What is the factor_direction? (high_better / low_better)",
    "What is the final_score_field name?",
    "Define the score_combination_formula.",
    "What is the missing_value_policy?",
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCsfAgentSessionE2E:
    """Full agent session: mandate → data_ready → signal_ready with human interaction."""

    @pytest.fixture()
    def lineage_root(self, tmp_path: Path) -> Path:
        return tmp_path / "outputs" / "csf_momentum_session"

    def test_full_session_passes_all_gates(self, lineage_root: Path) -> None:
        human = HumanSimulator(CSF_MOMENTUM_RESPONSES)
        harness = AgentHarness(
            lineage_root,
            stages=[
                StageStep(
                    stage_id="mandate",
                    questions=MANDATE_QUESTIONS,
                    builder=prepare_mandate,
                ),
                StageStep(
                    stage_id="csf_data_ready",
                    questions=CSF_DATA_READY_QUESTIONS,
                    builder=prepare_csf_data_ready,
                ),
                StageStep(
                    stage_id="csf_signal_ready",
                    questions=CSF_SIGNAL_READY_QUESTIONS,
                    builder=prepare_csf_signal_ready,
                ),
            ],
        )

        result = harness.run_session(human)

        assert result.failed_stage is None, f"Session failed at {result.failed_stage}: {result.failure_reason}"
        assert result.completed_stages == ["mandate", "csf_data_ready", "csf_signal_ready"]
        assert result.interactions > 0

    def test_session_tracks_stage_progress(self, lineage_root: Path) -> None:
        human = HumanSimulator(CSF_MOMENTUM_RESPONSES)
        harness = AgentHarness(
            lineage_root,
            stages=[
                StageStep(stage_id="mandate", questions=MANDATE_QUESTIONS, builder=prepare_mandate),
                StageStep(stage_id="csf_data_ready", questions=CSF_DATA_READY_QUESTIONS, builder=prepare_csf_data_ready),
            ],
        )

        assert harness.current_stage == "mandate"
        assert not harness.is_complete

        stage = harness.run_stage(human)
        assert stage == "mandate"
        assert harness.current_stage == "csf_data_ready"

        stage = harness.run_stage(human)
        assert stage == "csf_data_ready"
        assert harness.is_complete
        assert harness.completed_stages == ["mandate", "csf_data_ready"]

    def test_human_simulator_tracks_interactions(self, lineage_root: Path) -> None:
        human = HumanSimulator(CSF_MOMENTUM_RESPONSES)

        # Simulate agent asking questions
        answer = human.respond("What factor_id should we use?", "csf_signal_ready")
        assert answer == "btc_lead_alt_follow"
        assert human.interactions_count == 1

        answer = human.respond("Confirm factor_direction", "csf_signal_ready")
        assert answer == "high_better"
        assert human.interactions_count == 2

    def test_human_simulator_returns_default_on_unmatched(self) -> None:
        human = HumanSimulator([
            HumanResponse("test_stage", ["specific_keyword"], "specific_answer"),
        ])
        answer = human.respond("Something completely unrelated", "test_stage")
        assert answer == "confirmed"

    def test_session_fails_on_broken_builder(self, lineage_root: Path) -> None:
        """If a builder crashes, session result captures the failure."""

        def broken_builder(root: Path) -> Path:
            raise RuntimeError("simulated failure")

        human = HumanSimulator(CSF_MOMENTUM_RESPONSES)
        harness = AgentHarness(
            lineage_root,
            stages=[
                StageStep(stage_id="mandate", questions=MANDATE_QUESTIONS, builder=broken_builder),
            ],
        )

        result = harness.run_session(human)
        assert result.failed_stage == "mandate"
        assert "simulated failure" in result.failure_reason
