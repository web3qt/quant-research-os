from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import run
import sys

from tests.helpers.repo_paths import REPO_ROOT


def test_generator_dry_run_reports_fresh_outputs() -> None:
    result = run(
        [sys.executable, "runtime/scripts/gen_stage_review_skills.py", "--host", "codex", "--dry-run"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "FRESH:" in result.stdout
    assert "qros-mandate-review" in result.stdout
    assert "qros-data-ready-review" in result.stdout
    assert "qros-csf-data-ready-review" in result.stdout
    assert "qros-tss-data-ready-review" in result.stdout
    assert "qros-signal-ready-review" in result.stdout
    assert "qros-csf-signal-ready-review" in result.stdout
    assert "qros-tss-signal-ready-review" in result.stdout
    assert "qros-train-freeze-review" in result.stdout
    assert "qros-csf-train-freeze-review" in result.stdout
    assert "qros-tss-train-freeze-review" in result.stdout
    assert "qros-test-evidence-review" in result.stdout
    assert "qros-csf-test-evidence-review" in result.stdout
    assert "qros-tss-test-evidence-review" in result.stdout
    assert "qros-backtest-ready-review" in result.stdout
    assert "qros-csf-backtest-ready-review" in result.stdout
    assert "qros-tss-backtest-ready-review" in result.stdout
    assert "qros-holdout-validation-review" in result.stdout
    assert "qros-csf-holdout-validation-review" in result.stdout
    assert "qros-tss-holdout-validation-review" in result.stdout
    assert "STALE:" not in result.stdout


def test_generator_dry_run_reports_stale_outputs_when_generated_file_drifts(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    temp_root = tmp_path / "output-root"
    try:
        shutil.copytree(repo_root / "skills", temp_root / "skills")
        skill_path = temp_root / "skills" / "mandate" / "qros-mandate-review" / "SKILL.md"
        original = skill_path.read_text(encoding="utf-8")
        skill_path.write_text(original + "\n<!-- drift -->\n", encoding="utf-8")

        result = run(
            [
                sys.executable,
                "runtime/scripts/gen_stage_review_skills.py",
                "--host",
                "codex",
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


def test_generated_review_skill_points_to_stage_contract_context_instead_of_inlining_stage_truth(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "rendered"
    result = run(
        [
            sys.executable,
            "runtime/scripts/gen_stage_review_skills.py",
            "--host",
            "codex",
            "--output-root",
            str(output_root),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    skill_path = output_root / "skills" / "csf_data_ready" / "qros-csf-data-ready-review" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")

    assert "stage_contract_context.yaml" in content
    assert "stage_contract_context.md" in content
    assert "review/final_review.yaml" in content
    assert "reviewer_findings.raw.yaml" not in content
    assert "qros-review-cycle prepare" in content
    assert "## 正式门禁" not in content
    assert "## 审查清单" not in content
    assert "## 本阶段下游权限" not in content
