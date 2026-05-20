from pathlib import Path


def test_review_shared_protocol_documents_stage_contract_context() -> None:
    content = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")
    assert "stage_contract_context.yaml" in content
    assert "stage_contract_context.md" in content
    assert "review-cycle-local rendering of current contracts" in content


def test_codex_review_skill_usage_documents_thin_generated_review_skills() -> None:
    content = Path("docs/guides/codex-stage-review-skill-usage.md").read_text(encoding="utf-8")
    assert "stage_contract_context.yaml" in content
    assert "generated review skills are workflow entrypoints, not stage truth" in content
    assert "review/final_review.yaml" in content
    assert "review/result/reviewer_findings.raw.yaml" not in content


def test_session_review_docs_match_final_review_handoff_contract() -> None:
    session_doc = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    session_skill = Path("skills/core/qros-research-session/SKILL.md").read_text(encoding="utf-8")
    combined = session_doc + "\n" + session_skill

    assert "review/final_review.yaml" in combined
    assert "review/result/reviewer_findings.raw.yaml" not in combined
    assert "closer command" not in combined
