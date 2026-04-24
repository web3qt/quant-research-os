from __future__ import annotations

from pathlib import Path


AUTHOR_SKILL = Path("skills/csf_holdout_validation/qros-csf-holdout-validation-author/SKILL.md")
REVIEW_SKILL = Path("skills/csf_holdout_validation/qros-csf-holdout-validation-review/SKILL.md")


def test_csf_holdout_validation_author_skill_defers_artifact_shape_to_contract() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_holdout_validation_artifacts.yaml" in content
    assert "qros-validate-stage --stage csf_holdout_validation" in content
    assert "csf_holdout_validation semantic validator" in content
    assert "不得手写或自行扩展 formal artifact shape" in content


def test_csf_holdout_validation_author_skill_uses_runtime_facing_output_names() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    for name in (
        "csf_holdout_run_manifest.json",
        "holdout_factor_diagnostics.parquet",
        "holdout_test_compare.parquet",
        "holdout_portfolio_compare.parquet",
        "rolling_holdout_stability.json",
        "regime_shift_audit.json",
        "csf_holdout_gate_decision.md",
    ):
        assert name in content

    assert "- `holdout_run_manifest.json`" not in content
    assert "holdout_backtest_compare.csv" not in content
    assert "window_results/" not in content


def test_csf_holdout_validation_review_skill_mentions_deterministic_contract_preflight() -> None:
    content = REVIEW_SKILL.read_text(encoding="utf-8")

    assert "ARTIFACT-CONTRACT-001" in content
    assert "CSF-HOLDOUT-SEMANTIC-001" in content
    assert "qros-validate-stage --stage csf_holdout_validation" in content
