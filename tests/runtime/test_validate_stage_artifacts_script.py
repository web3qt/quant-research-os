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


def test_validate_stage_artifacts_script_rejects_unsupported_stage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    (outputs_root / "lineage").mkdir(parents=True)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "lineage",
            "--stage",
            "mandate",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 2
    assert "unsupported artifact contract stage: mandate" in result.stderr
