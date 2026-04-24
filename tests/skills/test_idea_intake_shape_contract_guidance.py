from __future__ import annotations

from pathlib import Path

from tests.helpers.skill_test_utils import skill_text


def test_idea_intake_author_skill_delegates_artifact_shape_to_contract() -> None:
    content = skill_text("qros-idea-intake-author")

    assert "contracts/artifacts/idea_intake_artifacts.yaml" in content
    assert "不得手写第一阶段 artifact shape" in content
    assert "不得新增未声明 YAML top-level 字段" in content
    assert "qros-validate-stage --stage idea_intake" in content
    assert "validator 不通过，不得进入 GO_TO_MANDATE" in content


def test_research_session_skill_mentions_idea_intake_shape_validator() -> None:
    content = skill_text("qros-research-session")

    assert "contracts/artifacts/idea_intake_artifacts.yaml" in content
    assert "qros-validate-stage --stage idea_intake" in content
    assert "artifact shape 以 contract 为准" in content


def test_idea_intake_docs_explain_contract_runtime_skill_boundary() -> None:
    sop = Path("docs/sop/main-flow/00_idea_intake_sop_cn.md").read_text(encoding="utf-8")
    guide = Path("docs/guides/idea-intake-to-mandate-flow.md").read_text(encoding="utf-8")
    combined = "\n".join([sop, guide])

    assert "contracts/artifacts/idea_intake_artifacts.yaml" in combined
    assert "字段一致" in combined
    assert "内容一致" in combined
    assert "qros-validate-stage --stage idea_intake" in combined
    assert "skill 是执行引导" in combined
