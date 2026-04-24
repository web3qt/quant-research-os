from __future__ import annotations

from pathlib import Path


def test_research_session_usage_documents_csf_train_freeze_contract_first_gate() -> None:
    content = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_train_freeze_artifacts.yaml" in content
    assert "qros-validate-stage --stage csf_train_freeze" in content
    assert "csf_train_freeze semantic validator" in content


def test_review_shared_protocol_documents_csf_train_freeze_preflight() -> None:
    content = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")

    assert "csf_train_freeze" in content
    assert "train_variant_ledger.csv" in content
    assert "semantic validator" in content


def test_freeze_group_guide_keeps_csf_train_freeze_runtime_facing_fields() -> None:
    content = Path("docs/guides/stage-freeze-group-field-guide.md").read_text(encoding="utf-8")

    assert "qros-validate-stage --stage csf_train_freeze" in content
    assert "contracts/artifacts/csf_train_freeze_artifacts.yaml" in content
    assert "delivery_contract.consumer_stage" in content
