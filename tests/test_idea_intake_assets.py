from pathlib import Path


def test_idea_intake_docs_and_examples_exist() -> None:
    assert Path("docs/experience/idea-intake-to-mandate-flow.md").exists()
    assert Path("docs/intake-sop/examples/qualification_scorecard.example.yaml").exists()
    assert Path("docs/intake-sop/examples/idea_gate_decision.example.yaml").exists()


def test_author_skills_exist_and_reference_key_artifacts() -> None:
    intake_skill = Path(".agents/skills/qros-idea-intake-author/SKILL.md")
    mandate_skill = Path(".agents/skills/qros-mandate-author/SKILL.md")

    assert intake_skill.exists()
    assert mandate_skill.exists()

    intake_text = intake_skill.read_text(encoding="utf-8")
    assert "qualification_scorecard.yaml" in intake_text
    assert "idea_gate_decision.yaml" in intake_text
    assert "counter-hypothesis" in intake_text.lower()

    mandate_text = mandate_skill.read_text(encoding="utf-8")
    assert "GO_TO_MANDATE" in mandate_text
    assert "mandate.md" in mandate_text
    assert "post-hoc" in mandate_text.lower()
