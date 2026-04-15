from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import run
import sys


def test_generator_dry_run_reports_fresh_outputs() -> None:
    result = run(
        [sys.executable, "runtime/scripts/gen_codex_stage_review_skills.py", "--dry-run"],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "FRESH:" in result.stdout
    assert "qros-mandate-review" in result.stdout
    assert "qros-data-ready-review" in result.stdout
    assert "qros-csf-data-ready-review" in result.stdout
    assert "qros-signal-ready-review" in result.stdout
    assert "qros-csf-signal-ready-review" in result.stdout
    assert "qros-train-freeze-review" in result.stdout
    assert "qros-csf-train-freeze-review" in result.stdout
    assert "qros-test-evidence-review" in result.stdout
    assert "qros-csf-test-evidence-review" in result.stdout
    assert "qros-backtest-ready-review" in result.stdout
    assert "qros-csf-backtest-ready-review" in result.stdout
    assert "qros-holdout-validation-review" in result.stdout
    assert "qros-csf-holdout-validation-review" in result.stdout
    assert "STALE:" not in result.stdout


def test_generator_dry_run_reports_stale_outputs_when_generated_file_drifts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    temp_root = tmp_path / "output-root"
    try:
        shutil.copytree(repo_root / "skills", temp_root / "skills")
        skill_path = temp_root / "skills" / "mandate" / "qros-mandate-review" / "SKILL.md"
        original = skill_path.read_text(encoding="utf-8")
        skill_path.write_text(original + "\n<!-- drift -->\n", encoding="utf-8")

        result = run(
            [
                sys.executable,
                "runtime/scripts/gen_codex_stage_review_skills.py",
                "--dry-run",
                "--output-root",
                str(temp_root),
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "STALE: qros-mandate-review" in result.stdout
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)
