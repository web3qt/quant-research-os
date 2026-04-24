from __future__ import annotations

from pathlib import Path


AUTHOR_SKILL = Path("skills/csf_test_evidence/qros-csf-test-evidence-author/SKILL.md")
REVIEW_SKILL = Path("skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md")


def test_csf_test_evidence_author_skill_defers_artifact_shape_to_contract() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_test_evidence_artifacts.yaml" in content
    assert "qros-validate-stage --stage csf_test_evidence" in content
    assert "csf_test_evidence semantic validator" in content
    assert "不得手写或自行扩展 formal artifact shape" in content


def test_csf_test_evidence_author_skill_uses_runtime_facing_output_names() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    for name in (
        "rank_ic_timeseries.parquet",
        "rank_ic_summary.json",
        "bucket_returns.parquet",
        "monotonicity_report.json",
        "breadth_coverage_report.parquet",
        "subperiod_stability_report.json",
        "filter_condition_panel.parquet",
        "target_strategy_condition_compare.parquet",
        "gated_vs_ungated_summary.json",
        "csf_test_gate_table.csv",
        "csf_selected_variants_test.csv",
    ):
        assert name in content

    assert "admissibility_report.parquet" not in content
    assert "factor_selection.csv" not in content
    assert "selected_factor_spec.json" not in content
    assert "stage_completion_certificate.yaml" not in content


def test_csf_test_evidence_review_skill_mentions_deterministic_contract_preflight() -> None:
    content = REVIEW_SKILL.read_text(encoding="utf-8")

    assert "ARTIFACT-CONTRACT-001" in content
    assert "CSF-TEST-SEMANTIC-001" in content
    assert "qros-validate-stage --stage csf_test_evidence" in content
