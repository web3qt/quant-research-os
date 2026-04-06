from pathlib import Path


def test_public_skill_tree_exists() -> None:
    assert Path("skills").exists()
    assert Path("skills/qros-research-session/SKILL.md").exists()
    assert Path("skills/qros-mandate-review/SKILL.md").exists()
    assert Path("skills/qros-data-ready-review/SKILL.md").exists()
    assert Path("skills/qros-signal-ready-review/SKILL.md").exists()
    assert Path("skills/qros-train-freeze-review/SKILL.md").exists()
    assert Path("skills/qros-test-evidence-review/SKILL.md").exists()
    assert Path("skills/qros-backtest-ready-review/SKILL.md").exists()
    assert Path("skills/qros-holdout-validation-review/SKILL.md").exists()
    assert Path("skills/qros-stage-display/SKILL.md").exists()


def test_stage_display_skill_assets_exist() -> None:
    assert Path(".agents/skills/qros-stage-display/SKILL.md").exists()
    assert Path(".agents/skills/qros-stage-display/agents/openai.yaml").exists()


def test_codex_install_doc_exists() -> None:
    assert Path(".codex/INSTALL.md").exists()
