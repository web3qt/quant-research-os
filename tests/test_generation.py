from pathlib import Path
from subprocess import run


def test_generator_writes_first_wave_skills() -> None:
    result = run(
        ["python", "scripts/gen_codex_stage_review_skills.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert Path(".agents/skills/qros-mandate-review/SKILL.md").exists()
    assert Path(".agents/skills/qros-data-ready-review/SKILL.md").exists()
    assert Path(".agents/skills/qros-signal-ready-review/SKILL.md").exists()
    assert Path(".agents/skills/qros-mandate-review/agents/openai.yaml").exists()


def test_generator_runs_outside_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "gen_codex_stage_review_skills.py"
    result = run(
        ["python", str(script_path), "--dry-run"],
        cwd=repo_root.parent,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "FRESH: qros-mandate-review" in result.stdout
