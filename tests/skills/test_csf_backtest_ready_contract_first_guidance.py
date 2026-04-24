from __future__ import annotations

from pathlib import Path


AUTHOR_SKILL = Path("skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md")
REVIEW_SKILL = Path("skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md")


def test_csf_backtest_ready_author_skill_defers_artifact_shape_to_contract() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_backtest_ready_artifacts.yaml" in content
    assert "qros-validate-stage --stage csf_backtest_ready" in content
    assert "csf_backtest_ready semantic validator" in content
    assert "不得手写或自行扩展 formal artifact shape" in content


def test_csf_backtest_ready_author_skill_uses_runtime_facing_output_names() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    for name in (
        "portfolio_contract.yaml",
        "portfolio_weight_panel.parquet",
        "rebalance_ledger.csv",
        "turnover_capacity_report.parquet",
        "portfolio_summary.parquet",
        "name_level_metrics.parquet",
        "drawdown_report.json",
        "target_strategy_compare.parquet",
        "csf_backtest_gate_table.csv",
        "csf_backtest_gate_decision.md",
        "run_manifest.json",
    ):
        assert name in content

    assert "engine_compare.csv" not in content
    assert "selected_factor_spec.json" not in content
    assert "stage_completion_certificate.yaml" not in content


def test_csf_backtest_ready_review_skill_mentions_deterministic_contract_preflight() -> None:
    content = REVIEW_SKILL.read_text(encoding="utf-8")

    assert "ARTIFACT-CONTRACT-001" in content
    assert "CSF-BACKTEST-SEMANTIC-001" in content
    assert "qros-validate-stage --stage csf_backtest_ready" in content
