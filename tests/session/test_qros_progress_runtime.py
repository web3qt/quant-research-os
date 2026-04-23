from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from runtime.tools.progress_runtime import ProgressError, latest_lineage_id, progress_status_payload


def _touch_lineage(outputs_root: Path, lineage_id: str, filename: str = "marker.txt") -> Path:
    lineage_root = outputs_root / lineage_id
    lineage_root.mkdir(parents=True)
    marker = lineage_root / filename
    marker.write_text(lineage_id + "\n", encoding="utf-8")
    return lineage_root


def test_latest_lineage_id_selects_most_recent_existing_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _touch_lineage(outputs_root, "old_lineage")
    time.sleep(0.01)
    _touch_lineage(outputs_root, "new_lineage")

    assert latest_lineage_id(outputs_root) == "new_lineage"


def test_latest_lineage_id_does_not_create_outputs_root(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    try:
        latest_lineage_id(outputs_root)
    except ProgressError as exc:
        assert "No QROS outputs directory found" in str(exc)
    else:
        raise AssertionError("expected ProgressError")

    assert not outputs_root.exists()


def test_progress_status_payload_requires_existing_explicit_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    outputs_root.mkdir()

    try:
        progress_status_payload(outputs_root=outputs_root, lineage_id="missing")
    except ProgressError as exc:
        assert "QROS lineage not found" in str(exc)
    else:
        raise AssertionError("expected ProgressError")

    assert not (outputs_root / "missing").exists()


def test_progress_json_outputs_stable_status_fields_for_explicit_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "btc_leads_alts")
    (lineage_root / "00_idea_intake").mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "runtime/scripts/run_progress.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["lineage_id"] == "btc_leads_alts"
    assert payload["selection_mode"] == "explicit"
    assert payload["current_stage"] == "idea_intake_confirmation_pending"
    assert "current_skill" in payload
    assert "gate_status" in payload
    assert "next_action" in payload
    assert payload["artifacts_written"] == []


def test_progress_cli_without_lineage_id_uses_latest_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _touch_lineage(outputs_root, "old_lineage")
    time.sleep(0.01)
    latest_root = _touch_lineage(outputs_root, "latest_lineage")
    (latest_root / "00_idea_intake").mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "runtime/scripts/run_progress.py",
            "--outputs-root",
            str(outputs_root),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "QROS Progress" in result.stdout
    assert "Lineage: latest_lineage (latest)" in result.stdout
    assert "Current stage: idea_intake_confirmation_pending" in result.stdout


def test_qros_progress_wrapper_uses_current_repo_outputs(tmp_path: Path) -> None:
    project_root = tmp_path / "research_repo"
    outputs_root = project_root / "outputs"
    lineage_root = _touch_lineage(outputs_root, "btc_leads_alts")
    (lineage_root / "00_idea_intake").mkdir()

    result = subprocess.run(
        [
            "runtime/bin/qros-progress",
            "--cwd",
            str(project_root),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["lineage_id"] == "btc_leads_alts"
    assert payload["selection_mode"] == "latest"
    assert payload["current_stage"] == "idea_intake_confirmation_pending"
