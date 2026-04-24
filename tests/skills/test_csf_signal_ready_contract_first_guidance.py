from __future__ import annotations

from tests.helpers.skill_test_utils import skill_text


def test_csf_signal_ready_author_skill_treats_artifact_contract_as_shape_truth() -> None:
    content = skill_text("qros-csf-signal-ready-author")

    assert "contracts/artifacts/csf_signal_ready_artifacts.yaml" in content
    assert "不得把 `SKILL.md` 当作字段真值" in content
    assert "qros-validate-stage --stage csf_signal_ready" in content
    assert "semantic validator" in content
    assert "validator/preflight 不通过，不得进入 `csf_signal_ready` review" in content


def test_csf_signal_ready_author_skill_names_runtime_freeze_groups() -> None:
    content = skill_text("qros-csf-signal-ready-author")

    for group_name in [
        "factor_identity",
        "panel_contract",
        "factor_expression",
        "context_contract",
        "delivery_contract",
    ]:
        assert group_name in content

    assert "factor_role_contract" not in content
    assert "factor_structure_contract" not in content
    assert "- `neutralization_policy`" not in content


def test_csf_signal_ready_author_skill_does_not_reference_old_output_names() -> None:
    content = skill_text("qros-csf-signal-ready-author")

    assert "factor_coverage_report.parquet" in content
    assert "csf_signal_ready_gate_decision.md" in content
    assert "factor_coverage.parquet" not in content
    assert "signal_gate_decision.md" not in content


def test_csf_signal_ready_review_skill_defers_shape_truth_to_runtime_preflight() -> None:
    content = skill_text("qros-csf-signal-ready-review")

    assert "reviewer 不替 runtime 重定义字段" in content
    assert "deterministic preflight" in content
    assert "contracts/artifacts/csf_signal_ready_artifacts.yaml" in content
    assert "semantic validation" in content
    assert "upstream binding validation" in content
