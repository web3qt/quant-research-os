from __future__ import annotations

from pathlib import Path


def test_agent_behavior_eval_docs_explain_manual_boundary() -> None:
    content = Path("docs/guides/qros-agent-behavior-eval.md").read_text(encoding="utf-8")

    assert "qros-agent-eval" in content
    assert "--agent-command-template" in content
    assert "manual" in content.lower() or "nightly" in content.lower()
    assert "不进入默认 pytest" in content
    assert "不进入 smoke" in content
    assert "fake transcript" in content


def test_agent_behavior_eval_docs_list_mvp_cases() -> None:
    content = Path("docs/guides/qros-agent-behavior-eval.md").read_text(encoding="utf-8")

    for case_id in (
        "naive_raw_idea_triggers_research_session",
        "explicit_idea_intake_author_skill_first",
        "partial_intake_does_not_go_to_mandate",
        "no_confirmation_no_mandate_formal_artifacts",
        "raw_idea_scaffold_passes_artifact_shape_validator",
    ):
        assert case_id in content


def test_agent_behavior_eval_docs_list_csf_data_ready_cases() -> None:
    content = Path("docs/guides/qros-agent-behavior-eval.md").read_text(encoding="utf-8")

    for case_id in (
        "explicit_csf_data_ready_author_skill_first",
        "csf_data_ready_rejects_non_csf_mandate",
        "csf_data_ready_rejects_unreviewed_mandate",
        "csf_data_ready_rejects_unconfirmed_freeze_groups",
        "csf_data_ready_rejects_placeholder_parquet_completion",
        "csf_data_ready_runs_validator_before_review",
    ):
        assert case_id in content

    assert "expected_events" in content
    assert "qros-validate-stage --stage csf_data_ready" in content
    assert "qros-review-preflight" in content
