from pathlib import Path
from subprocess import run
import sys

from scripts.gen_codex_stage_review_skills import CHECKLIST_SCHEMA_PATH, GATE_SCHEMA_PATH


def test_generator_writes_review_skills_with_csf_parity(tmp_path: Path) -> None:
    output_root = tmp_path / "generated"
    result = run(
        [sys.executable, "scripts/gen_codex_stage_review_skills.py", "--output-root", str(output_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (output_root / "skills/mandate/qros-mandate-review/SKILL.md").exists()
    assert (output_root / "skills/data_ready/qros-data-ready-review/SKILL.md").exists()
    assert (output_root / "skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md").exists()
    assert (output_root / "skills/signal_ready/qros-signal-ready-review/SKILL.md").exists()
    assert (output_root / "skills/csf_signal_ready/qros-csf-signal-ready-review/SKILL.md").exists()
    assert (output_root / "skills/train_freeze/qros-train-freeze-review/SKILL.md").exists()
    assert (output_root / "skills/csf_train_freeze/qros-csf-train-freeze-review/SKILL.md").exists()
    assert (output_root / "skills/test_evidence/qros-test-evidence-review/SKILL.md").exists()
    assert (output_root / "skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md").exists()
    assert (output_root / "skills/backtest_ready/qros-backtest-ready-review/SKILL.md").exists()
    assert (output_root / "skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md").exists()
    assert (output_root / "skills/holdout_validation/qros-holdout-validation-review/SKILL.md").exists()
    assert (output_root / "skills/csf_holdout_validation/qros-csf-holdout-validation-review/SKILL.md").exists()
    assert (output_root / "skills/mandate/qros-mandate-review/agents/openai.yaml").exists()


def test_generator_runs_outside_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "gen_codex_stage_review_skills.py"
    result = run(
        [sys.executable, str(script_path), "--dry-run"],
        cwd=repo_root.parent,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "FRESH: qros-mandate-review" in result.stdout
    assert "FRESH: qros-csf-data-ready-review" in result.stdout
    assert "FRESH: qros-train-freeze-review" in result.stdout
    assert "FRESH: qros-csf-train-freeze-review" in result.stdout
    assert "FRESH: qros-test-evidence-review" in result.stdout
    assert "FRESH: qros-csf-test-evidence-review" in result.stdout
    assert "FRESH: qros-backtest-ready-review" in result.stdout
    assert "FRESH: qros-csf-backtest-ready-review" in result.stdout
    assert "FRESH: qros-holdout-validation-review" in result.stdout
    assert "FRESH: qros-csf-holdout-validation-review" in result.stdout


def test_generator_source_schema_paths_exist() -> None:
    assert GATE_SCHEMA_PATH.exists()
    assert CHECKLIST_SCHEMA_PATH.exists()
