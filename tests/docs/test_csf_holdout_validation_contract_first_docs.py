from __future__ import annotations

from pathlib import Path


def test_research_session_usage_documents_csf_holdout_validation_contract_first_gate() -> None:
    content = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_holdout_validation_artifacts.yaml" in content
    assert "qros-validate-stage --stage csf_holdout_validation" in content
    assert "csf_holdout_validation semantic validator" in content
    assert "portfolio_return_series.parquet" in content
    assert "equity_curve.parquet" in content
    assert "portfolio_pnl_ledger.parquet" in content
    assert "asset_pnl_ledger.parquet" in content
    assert "risk_adjusted_metrics.parquet" in content
    assert "不新增 PASS 阈值" in content


def test_review_shared_protocol_documents_csf_holdout_validation_preflight() -> None:
    content = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")

    assert "csf_holdout_validation" in content
    assert "holdout_test_compare.parquet" in content
    assert "semantic validator" in content


def test_freeze_group_guide_keeps_csf_holdout_validation_runtime_facing_fields() -> None:
    content = Path("docs/guides/stage-freeze-group-field-guide.md").read_text(encoding="utf-8")

    assert "qros-validate-stage --stage csf_holdout_validation" in content
    assert "contracts/artifacts/csf_holdout_validation_artifacts.yaml" in content
    assert "delivery_contract.consumer_stage" in content


def test_csf_holdout_validation_sop_uses_contract_facing_artifacts() -> None:
    content = Path("docs/sop/main-flow/07_csf_holdout_validation_sop_cn.md").read_text(encoding="utf-8")

    assert "csf_holdout_run_manifest.json" in content
    assert "holdout_test_compare.parquet" in content
    assert "holdout_portfolio_compare.parquet" in content
    assert "portfolio_return_series.parquet" in content
    assert "equity_curve.parquet" in content
    assert "portfolio_pnl_ledger.parquet" in content
    assert "asset_pnl_ledger.parquet" in content
    assert "risk_adjusted_metrics.parquet" in content
    assert "365" in content
    assert "252" in content
    assert "不新增 PASS 阈值" in content
    assert "holdout_backtest_compare.csv" not in content
    assert "window_results/" not in content
