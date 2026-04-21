"""Pre-recorded human response simulator for agent E2E tests.

Maps (stage, question_keyword) → answer, simulating what a researcher
would type when the agent asks questions during a research session.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HumanResponse:
    """A pre-recorded human answer keyed by stage and trigger keywords."""

    stage: str
    trigger_keywords: list[str]
    answer: str


@dataclass
class InteractionLog:
    """Record of a single agent-human interaction."""

    stage: str
    agent_output: str
    matched_keywords: list[str]
    human_response: str


class HumanSimulator:
    """Keyword-matching human response simulator.

    Usage:
        sim = HumanSimulator(responses)
        answer = sim.respond("What factor_direction should we use?", "csf_signal_ready")
    """

    def __init__(self, responses: list[HumanResponse]) -> None:
        self.responses = responses
        self.log: list[InteractionLog] = []
        self._used_indices: set[int] = set()

    def respond(self, agent_output: str, current_stage: str) -> str:
        """Match agent output against pre-recorded responses for the current stage."""
        output_lower = agent_output.lower()
        for idx, r in enumerate(self.responses):
            if r.stage != current_stage:
                continue
            if idx in self._used_indices:
                continue
            if any(kw.lower() in output_lower for kw in r.trigger_keywords):
                self._used_indices.add(idx)
                self.log.append(
                    InteractionLog(
                        stage=current_stage,
                        agent_output=agent_output[:200],
                        matched_keywords=[kw for kw in r.trigger_keywords if kw.lower() in output_lower],
                        human_response=r.answer,
                    )
                )
                return r.answer

        return "confirmed"

    @property
    def interactions_count(self) -> int:
        return len(self.log)

    def assert_all_responses_used(self) -> None:
        unused = [r for idx, r in enumerate(self.responses) if idx not in self._used_indices]
        assert not unused, f"Unused responses: {[(r.stage, r.trigger_keywords) for r in unused]}"
