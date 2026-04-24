from __future__ import annotations

from pathlib import Path


AUTHOR_SKILL = Path("skills/csf_train_freeze/qros-csf-train-freeze-author/SKILL.md")
REVIEW_SKILL = Path("skills/csf_train_freeze/qros-csf-train-freeze-review/SKILL.md")


def test_csf_train_freeze_author_skill_defers_artifact_shape_to_contract() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    assert "contracts/artifacts/csf_train_freeze_artifacts.yaml" in content
    assert "qros-validate-stage --stage csf_train_freeze" in content
    assert "csf_train_freeze semantic validator" in content
    assert "不得手写或自行扩展 formal artifact shape" in content


def test_csf_train_freeze_author_skill_uses_runtime_facing_output_names() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    for name in (
        "train_factor_quality.parquet",
        "train_variant_ledger.csv",
        "train_variant_rejects.csv",
        "train_bucket_diagnostics.parquet",
        "train_neutralization_diagnostics.parquet",
        "csf_train_freeze_gate_decision.md",
    ):
        assert name in content

    assert "train_quality.parquet" not in content
    assert "train_rejects.csv" not in content
    assert "stage_completion_certificate.yaml" not in content


def test_csf_train_freeze_review_skill_mentions_deterministic_contract_preflight() -> None:
    content = REVIEW_SKILL.read_text(encoding="utf-8")

    assert "ARTIFACT-CONTRACT-001" in content
    assert "CSF-TRAIN-SEMANTIC-001" in content
    assert "qros-validate-stage --stage csf_train_freeze" in content
