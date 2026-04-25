from __future__ import annotations

from pathlib import Path


def test_stage_freeze_group_field_guide_documents_csf_data_ready_contract_truth() -> None:
    content = Path("docs/guides/stage-freeze-group-field-guide.md").read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_data_ready_artifacts.yaml" in content
    assert "contract-first" in content
    assert "qros-validate-stage --stage csf_data_ready" in content
    assert "SKILL.md" in content
    assert "字段真值" in content
    assert "split_sample_adequacy_report.yaml" in content
    assert "cross_section_snapshot" in content


def test_qros_research_session_usage_documents_csf_data_ready_validator_before_review() -> None:
    content = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_data_ready_artifacts.yaml" in content
    assert "qros-validate-stage --stage csf_data_ready" in content
    assert "validator/preflight 不通过" in content
    assert "不得进入 `csf_data_ready` review" in content
    assert "split_sample_adequacy_report.yaml" in content
    assert "不是 mandate 字段扩展" in content


def test_review_shared_protocol_documents_csf_data_ready_contract_and_semantic_preflight() -> None:
    content = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")

    assert "csf_data_ready_artifacts.yaml" in content
    assert "artifact contract validation" in content
    assert "semantic validation" in content
    assert "upstream binding validation" in content
    assert "split_sample_adequacy_report.yaml" in content
    assert "cross_section_snapshot" in content
    assert "placeholder parquet" not in content
