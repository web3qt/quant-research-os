from pathlib import Path

from tests.helpers.skill_test_utils import skill_path


def test_idea_intake_docs_and_examples_exist() -> None:
    assert Path("docs/guides/idea-intake-to-mandate-flow.md").exists()
    assert Path("docs/sop/intake/examples/qualification_scorecard.example.yaml").exists()
    assert Path("docs/sop/intake/examples/idea_gate_decision.example.yaml").exists()


def test_author_skills_exist_and_reference_key_artifacts() -> None:
    intake_skill = skill_path("qros-idea-intake-author")
    mandate_skill = skill_path("qros-mandate-author")

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
