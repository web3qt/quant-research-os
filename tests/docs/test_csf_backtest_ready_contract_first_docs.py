from __future__ import annotations

from pathlib import Path


def test_research_session_usage_documents_csf_backtest_ready_contract_first_gate() -> None:
    content = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_backtest_ready_artifacts.yaml" in content
    assert "qros-validate-stage --stage csf_backtest_ready" in content
    assert "csf_backtest_ready semantic validator" in content


def test_review_shared_protocol_documents_csf_backtest_ready_preflight() -> None:
    content = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")

    assert "csf_backtest_ready" in content
    assert "portfolio_weight_panel.parquet" in content
    assert "csf_backtest_gate_decision.md" in content
    assert "semantic validator" in content


def test_freeze_group_guide_keeps_csf_backtest_ready_runtime_facing_fields() -> None:
    content = Path("docs/guides/stage-freeze-group-field-guide.md").read_text(encoding="utf-8")

    assert "qros-validate-stage --stage csf_backtest_ready" in content
    assert "contracts/artifacts/csf_backtest_ready_artifacts.yaml" in content
    assert "delivery_contract.consumer_stage" in content


def test_csf_backtest_ready_sop_uses_contract_facing_artifacts() -> None:
    content = Path("docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md").read_text(encoding="utf-8")

    assert "target_strategy_compare.parquet" in content
    assert "csf_backtest_gate_decision.md" in content
    assert "run_manifest.json" in content
    assert "engine_compare.csv" not in content
