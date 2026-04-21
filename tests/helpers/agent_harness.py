"""Agent harness for simulating QROS research session E2E flows.

Simulates the agent loop: read skill → ask questions → get human answers →
execute runtime → verify gates → advance to next stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from tests.helpers.gate_assertions import assert_all_gates_pass
from tests.helpers.human_simulator import HumanSimulator


@dataclass
class StageStep:
    """One stage in the agent session script."""

    stage_id: str
    questions: list[str]
    builder: Callable[[Path], Path]
    formal_subpath: str = "author/formal"


@dataclass
class SessionResult:
    """Result of a completed agent session."""

    lineage_root: Path
    completed_stages: list[str]
    failed_stage: str | None = None
    failure_reason: str | None = None
    interactions: int = 0


class AgentHarness:
    """Drives a mock QROS research session through scripted stages.

    For each stage:
    1. Agent "asks" the pre-scripted questions
    2. HumanSimulator provides answers
    3. Builder function produces artifacts
    4. Gate assertions verify correctness
    5. Session advances to next stage
    """

    def __init__(self, lineage_root: Path, stages: list[StageStep]) -> None:
        self.lineage_root = lineage_root
        self.stages = stages
        self.completed_stages: list[str] = []
        self._current_stage_idx = 0

    @property
    def current_stage(self) -> str:
        if self._current_stage_idx < len(self.stages):
            return self.stages[self._current_stage_idx].stage_id
        return "__complete__"

    @property
    def is_complete(self) -> bool:
        return self._current_stage_idx >= len(self.stages)

    def run_session(self, human: HumanSimulator) -> SessionResult:
        """Execute the full session: ask → answer → build → verify for each stage."""
        for step in self.stages:
            self._current_stage_idx = self.stages.index(step)

            # 1. Agent asks questions, human answers
            for question in step.questions:
                human.respond(question, step.stage_id)

            # 2. Builder produces artifacts
            try:
                step.builder(self.lineage_root)
            except Exception as exc:
                return SessionResult(
                    lineage_root=self.lineage_root,
                    completed_stages=list(self.completed_stages),
                    failed_stage=step.stage_id,
                    failure_reason=f"Builder failed: {exc}",
                    interactions=human.interactions_count,
                )

            # 3. Gate verification
            formal_dir = self.lineage_root / self._stage_dir_name(step.stage_id) / step.formal_subpath
            if formal_dir.exists():
                try:
                    assert_all_gates_pass(formal_dir, step.stage_id)
                except AssertionError as exc:
                    return SessionResult(
                        lineage_root=self.lineage_root,
                        completed_stages=list(self.completed_stages),
                        failed_stage=step.stage_id,
                        failure_reason=f"Gate failed: {exc}",
                        interactions=human.interactions_count,
                    )

            self.completed_stages.append(step.stage_id)

        self._current_stage_idx = len(self.stages)
        return SessionResult(
            lineage_root=self.lineage_root,
            completed_stages=list(self.completed_stages),
            interactions=human.interactions_count,
        )

    def run_stage(self, human: HumanSimulator) -> str:
        """Execute a single stage step and return the stage_id."""
        if self.is_complete:
            return "__complete__"

        step = self.stages[self._current_stage_idx]
        for question in step.questions:
            human.respond(question, step.stage_id)

        step.builder(self.lineage_root)
        formal_dir = self.lineage_root / self._stage_dir_name(step.stage_id) / step.formal_subpath
        if formal_dir.exists():
            assert_all_gates_pass(formal_dir, step.stage_id)

        self.completed_stages.append(step.stage_id)
        self._current_stage_idx += 1
        return step.stage_id

    @staticmethod
    def _stage_dir_name(stage_id: str) -> str:
        """Map stage_id to directory name (e.g. csf_signal_ready → 03_csf_signal_ready)."""
        mapping = {
            "mandate": "01_mandate",
            "csf_data_ready": "02_csf_data_ready",
            "csf_signal_ready": "03_csf_signal_ready",
            "csf_train_freeze": "04_csf_train_freeze",
            "csf_test_evidence": "05_csf_test_evidence",
            "csf_backtest_ready": "06_csf_backtest_ready",
            "csf_holdout_validation": "07_csf_holdout_validation",
        }
        return mapping.get(stage_id, stage_id)
