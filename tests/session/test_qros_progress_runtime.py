from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

from runtime.tools.progress_runtime import ProgressError, latest_lineage_id, progress_status_payload


def _touch_lineage(outputs_root: Path, lineage_id: str, filename: str = "marker.txt") -> Path:
    lineage_root = outputs_root / lineage_id
    lineage_root.mkdir(parents=True)
    marker = lineage_root / filename
    marker.write_text(lineage_id + "\n", encoding="utf-8")
    return lineage_root


def _write_failure_post_retry_decision(lineage_root: Path) -> None:
    package_dir = (
        lineage_root
        / "06_csf_backtest_ready"
        / "failure_packages"
        / "backtest_exec_fail_20260423T045312Z"
    )
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "post_retry_decision.yaml").write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "failed_stage": "csf_backtest_ready",
                "failure_class": "EXEC_FAIL",
                "retry_result": "hard_gate_still_failed",
                "recommended_next_decision": "NO_GO_OR_CHILD_LINEAGE_REQUIRED",
                "normal_progression_allowed": False,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _prepare_review_complete_mandate(outputs_root: Path, lineage_id: str) -> Path:
    stage_dir = outputs_root / lineage_id / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "mandate.md",
        "research_scope.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ):
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    (formal_dir / "research_route.yaml").write_text(
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
        encoding="utf-8",
    )
    (formal_dir / "time_split.json").write_text("{}\n", encoding="utf-8")
    (formal_dir / "parameter_grid.yaml").write_text("parameters: []\n", encoding="utf-8")
    (formal_dir / "run_config.toml").write_text("version = 1\n", encoding="utf-8")
    (formal_dir / "program_execution_manifest.json").write_text("{}\n", encoding="utf-8")
    for name in (
        "latest_review_pack.yaml",
        "stage_completion_certificate.yaml",
        "stage_gate_review.yaml",
    ):
        (stage_dir / "review" / "closure" / name).parent.mkdir(parents=True, exist_ok=True)
        (stage_dir / "review" / "closure" / name).write_text(
            "final_verdict: PASS\nstage_status: PASS\n",
            encoding="utf-8",
        )
    return stage_dir


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


def test_progress_payload_exposes_skill_first_direct_handoff(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _prepare_review_complete_mandate(outputs_root, "btc_alt")

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="btc_alt")

    assert payload["current_stage"] == "mandate_next_stage_confirmation_pending"
    assert payload["current_skill"] == "qros-research-session"
    assert payload["recommended_skill"] == "qros-research-session"
    assert payload["handoff_hint"] == "Continue with qros-research-session."
    assert payload["next_action"] == "Continue with qros-research-session."
    assert payload["resume_hint"] == "Continue with qros-research-session."
    assert "qros-session" not in payload["handoff_hint"]
    assert "qros-resume" not in payload["handoff_hint"]
    assert "qros-session" not in payload["next_action"]
    assert "qros-resume" not in payload["next_action"]


def test_progress_status_payload_surfaces_failure_disposition_gate(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "btc_alt_k")
    _write_failure_post_retry_decision(lineage_root)

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="btc_alt_k")

    assert payload["gate_status"] == "FAILURE_DISPOSITION_REQUIRED"
    assert payload["blocking_reason_code"] == "FAILURE_DISPOSITION_REQUIRED"
    assert payload["stage_status"] == "failure_disposition_required"
    assert payload["current_skill"] == "qros-stage-failure-handler"
    assert payload["requires_failure_handling"] is True
    assert payload["failure_stage"] == "csf_backtest_ready"
    assert "failure_disposition.yaml" in payload["next_action"]
