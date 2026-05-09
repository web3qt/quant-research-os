from __future__ import annotations

from pathlib import Path

import pytest

from runtime.tools.lineage_lock_ledger import FROZEN_ARTIFACT_MUTATED, lock_reviewed_stage
from runtime.tools.progress_runtime import progress_status_payload
from runtime.tools.research_session import run_research_session
from runtime.tools.stage_entry_guard import StageEntryGuardError, check_stage_entry_for_lineage


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _locked_mutated_lineage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    _write(
        stage_dir / "author" / "formal" / "research_route.yaml",
        "\n".join(
            [
                "research_route: cross_sectional_factor",
                "factor_role: standalone_alpha",
                "factor_structure: single_factor",
                "portfolio_expression: long_short_rank_based",
                "neutralization_policy: market_beta_neutral",
                "",
            ]
        ),
    )
    _write(stage_dir / "author" / "formal" / "program_execution_manifest.json", "{}\n")
    for name in (
        "latest_review_pack.yaml",
        "stage_completion_certificate.yaml",
        "stage_gate_review.yaml",
    ):
        _write(stage_dir / "review" / "closure" / name, "final_verdict: PASS\n")
    lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T00:00:00+00:00",
    )
    _write(
        stage_dir / "author" / "formal" / "research_route.yaml",
        "research_route: cross_sectional_factor\nfactor_role: changed\n",
    )
    return lineage_root


def test_progress_status_surfaces_frozen_artifact_mutation(tmp_path: Path) -> None:
    lineage_root = _locked_mutated_lineage(tmp_path)

    payload = progress_status_payload(outputs_root=lineage_root.parent, lineage_id=lineage_root.name)

    assert payload["stage_status"] == "blocked"
    assert payload["blocking_reason_code"] == FROZEN_ARTIFACT_MUTATED
    assert payload["gate_status"] == FROZEN_ARTIFACT_MUTATED
    assert "Restore 01_mandate/author/formal/research_route.yaml" in payload["next_action"]
    assert FROZEN_ARTIFACT_MUTATED in payload["blocking_reason"]


def test_research_session_surfaces_frozen_artifact_mutation_before_writes(tmp_path: Path) -> None:
    lineage_root = _locked_mutated_lineage(tmp_path)

    status = run_research_session(outputs_root=lineage_root.parent, lineage_id=lineage_root.name)

    assert status.stage_status == "blocked"
    assert status.blocking_reason_code == FROZEN_ARTIFACT_MUTATED
    assert status.gate_status == FROZEN_ARTIFACT_MUTATED
    assert "Restore 01_mandate/author/formal/research_route.yaml" in status.next_action
    assert status.artifacts_written == []


def test_stage_entry_guard_blocks_frozen_artifact_mutation(tmp_path: Path) -> None:
    lineage_root = _locked_mutated_lineage(tmp_path)

    with pytest.raises(StageEntryGuardError) as exc_info:
        check_stage_entry_for_lineage(lineage_root, stage="csf_data_ready", lane="author")

    result = exc_info.value.result
    assert result.allowed is False
    assert result.current_active_skill == "qros-research-session"
    assert FROZEN_ARTIFACT_MUTATED in result.message
    assert "Restore 01_mandate/author/formal/research_route.yaml" in result.message
