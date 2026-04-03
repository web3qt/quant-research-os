from pathlib import Path
from subprocess import run
import sys


EXPECTED_REVIEW_SKILLS = [
    "qros-mandate-review",
    "qros-data-ready-review",
    "qros-signal-ready-review",
    "qros-train-freeze-review",
    "qros-test-evidence-review",
    "qros-backtest-ready-review",
    "qros-holdout-validation-review",
    "qros-csf-data-ready-review",
    "qros-csf-signal-ready-review",
    "qros-csf-train-freeze-review",
    "qros-csf-test-evidence-review",
    "qros-csf-backtest-ready-review",
    "qros-csf-holdout-validation-review",
]


def test_generator_writes_mainline_and_csf_review_skills(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_root = tmp_path / "generated"

    result = run(
        [sys.executable, "scripts/gen_codex_stage_review_skills.py", "--output-root", str(output_root)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for skill_name in EXPECTED_REVIEW_SKILLS:
        assert (output_root / ".agents" / "skills" / skill_name / "SKILL.md").exists(), skill_name


def test_generated_review_skill_template_contains_adversarial_contract_language(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_root = tmp_path / "generated"

    result = run(
        [sys.executable, "scripts/gen_codex_stage_review_skills.py", "--output-root", str(output_root)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    skill_text = (output_root / ".agents" / "skills" / "qros-test-evidence-review" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "adversarial reviewer-agent" in skill_text
    assert "adversarial_review_request.yaml" in skill_text
    assert "adversarial_review_result.yaml" in skill_text
    assert "source-code inspection" in skill_text
    assert "FIX_REQUIRED" in skill_text
    assert "closure-ready adverse verdict" in skill_text
