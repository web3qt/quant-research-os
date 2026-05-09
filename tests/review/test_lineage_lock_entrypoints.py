from __future__ import annotations

from pathlib import Path

import pytest

from runtime.tools.lineage_lock_ledger import FrozenArtifactMutationError, lock_reviewed_stage
from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff
from runtime.tools.review_skillgen.review_engine import run_stage_review
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.review.test_run_stage_review_script import _prepare_mandate_stage


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _lock_then_mutate_mandate(tmp_path: Path) -> Path:
    stage_dir = _prepare_mandate_stage(tmp_path)
    for name in (
        "latest_review_pack.yaml",
        "stage_completion_certificate.yaml",
        "stage_gate_review.yaml",
    ):
        _write(stage_dir / "review" / "closure" / name, "final_verdict: PASS\n")
    lock_reviewed_stage(
        lineage_root=stage_dir.parent,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T00:00:00+00:00",
    )
    _write(stage_dir / "author" / "formal" / "research_route.yaml", "factor_role: changed\n")
    return stage_dir


def test_review_preflight_blocks_when_locked_mandate_changed(tmp_path: Path) -> None:
    stage_dir = _lock_then_mutate_mandate(tmp_path)

    with pytest.raises(FrozenArtifactMutationError) as exc_info:
        run_review_preflight(
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": stage_dir.parent,
            }
        )

    assert exc_info.value.path == "mandate/author/formal/research_route.yaml"


def test_review_cycle_prepare_blocks_when_locked_mandate_changed(tmp_path: Path) -> None:
    stage_dir = _lock_then_mutate_mandate(tmp_path)

    with pytest.raises(FrozenArtifactMutationError) as exc_info:
        prepare_review_cycle_for_handoff(
            cwd=tmp_path,
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": stage_dir.parent,
            },
            reviewer_identity="reviewer-agent",
            reviewer_session_id="review-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
        )

    assert exc_info.value.reason_code == "FROZEN_ARTIFACT_MUTATED"


def test_stage_review_blocks_before_rewriting_closure_when_locked_mandate_changed(tmp_path: Path) -> None:
    stage_dir = _lock_then_mutate_mandate(tmp_path)
    closure_path = stage_dir / "review" / "closure" / "stage_gate_review.yaml"
    before = closure_path.read_text(encoding="utf-8")

    with pytest.raises(FrozenArtifactMutationError):
        run_stage_review(
            cwd=tmp_path,
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": stage_dir.parent,
            },
            reviewer_identity="reviewer-agent",
            reviewer_role="reviewer",
            reviewer_session_id="review-session",
            reviewer_mode="adversarial",
        )

    assert closure_path.read_text(encoding="utf-8") == before
