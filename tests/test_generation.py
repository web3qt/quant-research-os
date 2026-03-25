from pathlib import Path
from subprocess import run
import sys


def test_generator_writes_first_wave_skills(tmp_path: Path) -> None:
    output_root = tmp_path / "generated"
    result = run(
        [sys.executable, "scripts/gen_codex_stage_review_skills.py", "--output-root", str(output_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (output_root / ".agents/skills/qros-mandate-review/SKILL.md").exists()
    assert (output_root / ".agents/skills/qros-data-ready-review/SKILL.md").exists()
    assert (output_root / ".agents/skills/qros-signal-ready-review/SKILL.md").exists()
    assert (output_root / ".agents/skills/qros-train-freeze-review/SKILL.md").exists()
    assert (output_root / ".agents/skills/qros-test-evidence-review/SKILL.md").exists()
    assert (output_root / ".agents/skills/qros-backtest-ready-review/SKILL.md").exists()
    assert (output_root / ".agents/skills/qros-holdout-validation-review/SKILL.md").exists()
    assert (output_root / ".agents/skills/qros-mandate-review/agents/openai.yaml").exists()


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
    assert "FRESH: qros-train-freeze-review" in result.stdout
    assert "FRESH: qros-test-evidence-review" in result.stdout
    assert "FRESH: qros-backtest-ready-review" in result.stdout
    assert "FRESH: qros-holdout-validation-review" in result.stdout
