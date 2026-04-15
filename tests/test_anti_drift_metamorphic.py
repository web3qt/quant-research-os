from pathlib import Path

from runtime.tools.anti_drift import canonical_snapshot_from_session_context, semantic_projection
from runtime.tools.anti_drift_scenarios import (
    prepare_mainline_mandate_review_complete,
    prepare_mainline_signal_ready_review_complete,
    write_minimal_stage_outputs,
    write_stage_completion_certificate,
)
from runtime.tools.research_session import run_research_session


def test_idea_intake_confirmation_semantics_are_stable_across_equivalent_raw_ideas(tmp_path: Path) -> None:
    outputs_root_a = tmp_path / "outputs_a"
    outputs_root_b = tmp_path / "outputs_b"

    status_a = run_research_session(
        outputs_root=outputs_root_a,
        raw_idea="BTC leads high-liquidity alts after shock events",
    )
    status_b = run_research_session(
        outputs_root=outputs_root_b,
        raw_idea="BTC leads high liquidity alts after shock events!!!",
    )

    snapshot_a = canonical_snapshot_from_session_context(status_a, fixture_id="idea-variant-a")
    snapshot_b = canonical_snapshot_from_session_context(status_b, fixture_id="idea-variant-b")

    assert semantic_projection(snapshot_a) == semantic_projection(snapshot_b)


def test_data_ready_confirmation_semantics_are_stable_across_lineage_ids(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    lineage_root_a = outputs_root / "mainline_case_a"
    prepare_mainline_mandate_review_complete(lineage_root_a)
    status_a = run_research_session(outputs_root=outputs_root, lineage_id="mainline_case_a")

    lineage_root_b = outputs_root / "mainline_case_b"
    prepare_mainline_mandate_review_complete(lineage_root_b)
    status_b = run_research_session(outputs_root=outputs_root, lineage_id="mainline_case_b")

    snapshot_a = canonical_snapshot_from_session_context(status_a, fixture_id="mainline-a")
    snapshot_b = canonical_snapshot_from_session_context(status_b, fixture_id="mainline-b")

    assert semantic_projection(snapshot_a) == semantic_projection(snapshot_b)


def test_failure_handling_semantics_are_stable_across_equivalent_retry_cases(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    lineage_root_a = outputs_root / "retry_case_a"
    prepare_mainline_signal_ready_review_complete(lineage_root_a)
    stage_dir_a = lineage_root_a / "04_train_freeze"
    write_minimal_stage_outputs(stage_dir_a, stage="train_freeze")
    write_stage_completion_certificate(stage_dir_a / "stage_completion_certificate.yaml", stage_status="PASS FOR RETRY")
    status_a = run_research_session(outputs_root=outputs_root, lineage_id="retry_case_a")

    lineage_root_b = outputs_root / "retry_case_b"
    prepare_mainline_signal_ready_review_complete(lineage_root_b)
    stage_dir_b = lineage_root_b / "04_train_freeze"
    write_minimal_stage_outputs(stage_dir_b, stage="train_freeze")
    write_stage_completion_certificate(stage_dir_b / "stage_completion_certificate.yaml", stage_status="PASS FOR RETRY")
    status_b = run_research_session(outputs_root=outputs_root, lineage_id="retry_case_b")

    snapshot_a = canonical_snapshot_from_session_context(status_a, fixture_id="retry-a")
    snapshot_b = canonical_snapshot_from_session_context(status_b, fixture_id="retry-b")

    assert semantic_projection(snapshot_a) == semantic_projection(snapshot_b)
