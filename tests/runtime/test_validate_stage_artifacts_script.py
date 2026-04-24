from __future__ import annotations

from pathlib import Path
from subprocess import run
import sys

import yaml

from runtime.tools.idea_runtime import scaffold_idea_intake
from tests.helpers.repo_paths import REPO_ROOT


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_validate_stage_artifacts_script_accepts_valid_idea_intake(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_transmission_v1"
    scaffold_idea_intake(lineage_root)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "idea_intake",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "idea_intake artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_reports_invalid_shape(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    payload = yaml.safe_load((intake_dir / "scope_canvas.yaml").read_text(encoding="utf-8"))
    payload["holding_horizons"] = "15m"
    _write_yaml(intake_dir / "scope_canvas.yaml", payload)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "idea_intake",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "scope_canvas.yaml: holding_horizons expected list[string], found str" in result.stderr


def test_validate_stage_artifacts_script_accepts_valid_mandate(tmp_path: Path) -> None:
    from tests.helpers.lineage_program_support import ensure_stage_program
    from tests.session.test_idea_runtime_scripts import _mandate_freeze_draft, _route_assessment

    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "route_assessment": _route_assessment(),
            "approved_scope": {},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {
            "market": "Binance perpetual",
            "data_source": "Binance UM futures klines",
            "instrument_type": "perpetual",
            "universe": "top liquidity alts",
            "bar_size": "5m",
            "holding_horizons": ["15m"],
            "target_task": "event-driven relative return study",
            "excluded_scope": [],
            "budget_days": 10,
            "max_iterations": 3,
        },
    )
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n", encoding="utf-8")
    (intake_dir / "qualification_scorecard.yaml").write_text("idea_id: btc_alt_transmission_v1\n", encoding="utf-8")
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "mandate")

    build = run(
        [sys.executable, "runtime/scripts/build_mandate_from_intake.py", "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert build.returncode == 0, build.stderr

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "mandate",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "mandate artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_reports_invalid_mandate_shape(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "btc_alt_transmission_v1" / "01_mandate" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "mandate.md").write_text("# Mandate\n", encoding="utf-8")

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "mandate",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "research_scope.md: missing required artifact" in result.stderr
