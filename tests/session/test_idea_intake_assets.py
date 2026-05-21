from pathlib import Path

from tests.helpers.skill_test_utils import skill_path


def test_mandate_admission_docs_exist() -> None:
    assert Path("docs/guides/mandate-admission-flow.md").exists()


def test_author_skills_exist_and_reference_key_artifacts() -> None:
    mandate_skill = skill_path("qros-mandate-author")

    assert mandate_skill.exists()

    mandate_text = mandate_skill.read_text(encoding="utf-8")
    assert "ACCEPT_FOR_MANDATE" in mandate_text
    assert "mandate.md" in mandate_text
    assert "post-hoc" in mandate_text.lower()
    assert "contracts/artifacts/mandate_artifacts.yaml" in mandate_text
    assert "qros-validate-stage" in mandate_text
    assert "不得把 SKILL.md 作为字段真值" in mandate_text


def test_mandate_admission_flow_documents_mandate_contract_validation() -> None:
    flow_text = Path("docs/guides/mandate-admission-flow.md").read_text(encoding="utf-8")

    assert "qros-validate-stage --stage mandate" in flow_text
    assert "contracts/artifacts/mandate_artifacts.yaml" in flow_text
