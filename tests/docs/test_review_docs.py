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
