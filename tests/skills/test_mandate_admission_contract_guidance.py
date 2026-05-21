from pathlib import Path

from tests.helpers.skill_test_utils import skill_text


def test_research_session_skill_uses_mandate_admission_as_first_stage() -> None:
    content = skill_text("qros-research-session")

    assert "contracts/artifacts/mandate_admission_artifacts.yaml" in content
    assert "mandate_admission" in content
    assert "mandate_freeze_confirmation_pending" in content
    assert "01_mandate/author/draft/mandate_admission.yaml" in content
    assert "00_" + "idea" + "_intake" not in content
    assert "qros-" + "idea" + "-intake-author" not in content


def test_mandate_admission_docs_explain_contract_runtime_skill_boundary() -> None:
    guide = Path("docs/guides/mandate-admission-flow.md").read_text(encoding="utf-8")
    combined = "\n".join([guide, skill_text("qros-mandate-author")])

    assert "mandate_admission.yaml" in combined
    assert "mandate_freeze_draft.yaml" in combined
    assert "mandate_transition_approval.yaml" in combined
    assert "qros-validate-stage --stage mandate" in combined
    assert "contracts/artifacts/mandate_artifacts.yaml" in combined
    assert "ACCEPT_FOR_MANDATE" in combined
