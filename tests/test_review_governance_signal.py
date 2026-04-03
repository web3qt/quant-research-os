from pathlib import Path

import pytest

from tools.review_skillgen.governance_signal import (
    build_governance_signal_bundle,
    load_review_governance_policy,
)


def _request_payload(*, started_at: str) -> dict:
    return {
        "review_cycle_id": "cycle-1",
        "lineage_id": "topic_a",
        "stage": "mandate",
        "author_identity": "author-agent",
        "author_session_id": "author-session",
        "required_program_dir": "program/mandate",
        "required_program_entrypoint": "run_stage.py",
        "required_artifact_paths": ["mandate.md"],
        "required_provenance_paths": ["program_execution_manifest.json"],
        "required_reviewer_mode": "adversarial",
        "author_stage_invoked_at": started_at,
    }


def _review_result(*, outcome: str = "CLOSURE_READY_PASS") -> dict:
    return {
        "review_cycle_id": "cycle-1",
        "reviewer_identity": "reviewer-agent",
        "reviewer_role": "reviewer",
        "reviewer_session_id": "review-session",
        "reviewer_mode": "adversarial",
        "review_loop_outcome": outcome,
        "reviewed_program_dir": "program/mandate",
        "reviewed_program_entrypoint": "run_stage.py",
        "reviewed_artifact_paths": ["mandate.md"],
        "reviewed_provenance_paths": ["program_execution_manifest.json"],
        "blocking_findings": [],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "downstream_permissions": [],
        "review_completed_at": "2026-04-03T10:00:00Z",
    }


def test_build_governance_signal_dedupes_semantically_identical_findings(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "mandate"
    stage_dir.mkdir(parents=True)
    policy = load_review_governance_policy()

    bundle = build_governance_signal_bundle(
        stage_dir=stage_dir,
        lineage_root=lineage_root,
        stage="mandate",
        request_payload=_request_payload(started_at="2026-04-03T09:30:00Z"),
        review_result=_review_result(),
        review_loop_outcome="CLOSURE_READY_PASS",
        final_verdict="PASS",
        blocking_findings=[
            "Missing required output: parameter_grid.yaml",
            "  Missing   required output: parameter_grid.yaml  ",
        ],
        reservation_findings=[],
        info_findings=[],
        policy=policy,
    )

    assert bundle["post_rollout_only"] is True
    assert len(bundle["signals"]) == 1
    assert bundle["signals"][0]["candidate_class_suggestion"] == "hard_gate"
    assert (stage_dir / "governance_signal.json").exists()


def test_build_governance_signal_marks_fix_required_basis(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "mandate"
    stage_dir.mkdir(parents=True)
    policy = load_review_governance_policy()

    bundle = build_governance_signal_bundle(
        stage_dir=stage_dir,
        lineage_root=lineage_root,
        stage="mandate",
        request_payload=_request_payload(started_at="2026-04-03T09:30:00Z"),
        review_result=_review_result(outcome="FIX_REQUIRED"),
        review_loop_outcome="FIX_REQUIRED",
        final_verdict=None,
        blocking_findings=["Need stronger provenance linkage."],
        reservation_findings=[],
        info_findings=[],
        policy=policy,
    )

    assert bundle["signal_basis"] == "fix_required"


def test_build_governance_signal_marks_pre_rollout_artifacts_as_non_counting(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "mandate"
    stage_dir.mkdir(parents=True)
    policy = load_review_governance_policy()

    bundle = build_governance_signal_bundle(
        stage_dir=stage_dir,
        lineage_root=lineage_root,
        stage="mandate",
        request_payload=_request_payload(started_at="2026-04-02T23:59:59Z"),
        review_result=_review_result(),
        review_loop_outcome="CLOSURE_READY_PASS",
        final_verdict="PASS",
        blocking_findings=["Missing required output: parameter_grid.yaml"],
        reservation_findings=[],
        info_findings=[],
        policy=policy,
    )

    assert bundle["post_rollout_only"] is False


def test_load_review_governance_policy_rejects_invalid_priority_order(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "future_only: true",
                "requires_human_confirmation: true",
                'rollout_started_at: "2026-04-03T00:00:00+00:00"',
                "candidate_priority_order:",
                "  - template_constraint",
                "  - hard_gate",
                "  - regression_test",
                "thresholds:",
                "  min_distinct_review_cycles: 3",
                "  min_distinct_contexts_for_hard_gate: 2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="candidate_priority_order"):
        load_review_governance_policy(policy_path)
