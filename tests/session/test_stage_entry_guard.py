from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from runtime.tools.stage_entry_guard import (
    StageEntryGuardError,
    check_stage_entry_for_lineage,
    expected_stages_for_entry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_expected_author_stages_include_confirmation_and_author_state() -> None:
    assert expected_stages_for_entry(stage="csf_data_ready", lane="author") == (
        "csf_data_ready_confirmation_pending",
        "csf_data_ready_author",
    )


def test_expected_review_stages_include_confirmation_and_review_state() -> None:
    assert expected_stages_for_entry(stage="csf_data_ready", lane="review") == (
        "csf_data_ready_review_confirmation_pending",
        "csf_data_ready_review",
    )


def test_stage_entry_guard_allows_matching_intake_author_state(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    lineage_root.mkdir(parents=True)

    result = check_stage_entry_for_lineage(
        lineage_root,
        stage="idea_intake",
        lane="author",
    )

    assert result.allowed is True
    assert result.current_stage == "idea_intake"
    assert result.current_active_skill == "qros-idea-intake-author"
    assert result.recovery_command == "qros-research-session --lineage-id btc_leads_alts"


def test_stage_entry_guard_blocks_mismatched_author_stage_with_recovery_details(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    lineage_root.mkdir(parents=True)

    with pytest.raises(StageEntryGuardError) as exc_info:
        check_stage_entry_for_lineage(
            lineage_root,
            stage="csf_data_ready",
            lane="author",
        )

    result = exc_info.value.result
    assert result.allowed is False
    assert result.current_stage == "idea_intake"
    assert result.requested_stage == "csf_data_ready"
    assert result.requested_lane == "author"
    assert result.expected_stages == (
        "csf_data_ready_confirmation_pending",
        "csf_data_ready_author",
    )
    assert result.current_active_skill == "qros-idea-intake-author"
    assert result.recovery_command == "qros-research-session --lineage-id btc_leads_alts"
    assert "observed current_stage=idea_intake" in result.message
    assert "requested csf_data_ready author" in result.message


def test_check_stage_entry_script_exits_nonzero_on_mismatch(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    lineage_root.mkdir(parents=True)

    script = REPO_ROOT / "runtime" / "scripts" / "check_stage_entry.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--stage",
            "csf_data_ready",
            "--lane",
            "author",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "observed current_stage=idea_intake" in result.stderr
    assert "qros-research-session --lineage-id btc_leads_alts" in result.stderr


def test_check_stage_entry_script_outputs_json_on_success(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    lineage_root.mkdir(parents=True)

    script = REPO_ROOT / "runtime" / "scripts" / "check_stage_entry.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--stage",
            "idea_intake",
            "--lane",
            "author",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["allowed"] is True
    assert payload["current_stage"] == "idea_intake"
    assert payload["current_active_skill"] == "qros-idea-intake-author"
