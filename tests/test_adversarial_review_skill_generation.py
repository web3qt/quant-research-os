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
    expected_paths = {
        "qros-mandate-review": output_root / "skills/mandate/qros-mandate-review/SKILL.md",
        "qros-data-ready-review": output_root / "skills/data_ready/qros-data-ready-review/SKILL.md",
        "qros-signal-ready-review": output_root / "skills/signal_ready/qros-signal-ready-review/SKILL.md",
        "qros-train-freeze-review": output_root / "skills/train_freeze/qros-train-freeze-review/SKILL.md",
        "qros-test-evidence-review": output_root / "skills/test_evidence/qros-test-evidence-review/SKILL.md",
        "qros-backtest-ready-review": output_root / "skills/backtest_ready/qros-backtest-ready-review/SKILL.md",
        "qros-holdout-validation-review": output_root / "skills/holdout_validation/qros-holdout-validation-review/SKILL.md",
        "qros-csf-data-ready-review": output_root / "skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md",
        "qros-csf-signal-ready-review": output_root / "skills/csf_signal_ready/qros-csf-signal-ready-review/SKILL.md",
        "qros-csf-train-freeze-review": output_root / "skills/csf_train_freeze/qros-csf-train-freeze-review/SKILL.md",
        "qros-csf-test-evidence-review": output_root / "skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md",
        "qros-csf-backtest-ready-review": output_root / "skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md",
        "qros-csf-holdout-validation-review": output_root / "skills/csf_holdout_validation/qros-csf-holdout-validation-review/SKILL.md",
    }
    assert set(expected_paths) == set(EXPECTED_REVIEW_SKILLS)
    for skill_name, path in expected_paths.items():
        assert path.exists(), skill_name


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
    skill_text = (output_root / "skills" / "test_evidence" / "qros-test-evidence-review" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "adversarial reviewer-agent" in skill_text
    assert "adversarial_review_request.yaml" in skill_text
    assert "adversarial_review_result.yaml" in skill_text
    assert "source-code inspection" in skill_text
    assert "FIX_REQUIRED" in skill_text
    assert "closure-ready adverse verdict" in skill_text
