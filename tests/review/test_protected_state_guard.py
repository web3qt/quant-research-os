from pathlib import Path

import pytest
import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ensure_adversarial_review_request,
    issue_reviewer_receipt,
)
from runtime.tools.review_skillgen.protected_state_guard import (
    REVIEW_STATE_PROJECTION_DRIFT,
    REVIEWER_FINDINGS_UNBOUND,
    ProtectedStateError,
    assert_protected_review_state_intact,
)
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest,
    write_review_runtime_state,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _stage(tmp_path: Path) -> tuple[Path, Path, dict[str, object], str]:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    _write(formal_dir / "research_route.yaml", "route: csf\n")
    _write(formal_dir / "program_execution_manifest.json", "{}\n")
    request = ensure_adversarial_review_request(
        stage_dir,
        lineage_id="btc_alt",
        stage="mandate",
        author_identity="author-1",
        author_session_id="session-1",
        required_program_dir="programs/mandate",
        required_program_entrypoint="run.py",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        program_hash="abc123",
        stage_invoked_at="2026-05-11T00:00:00Z",
    )
    digest = compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    return lineage_root, stage_dir, request, digest


def _issue_receipt(stage_dir: Path) -> dict[str, object]:
    return issue_reviewer_receipt(
        stage_dir,
        reviewer_identity="reviewer-1",
        reviewer_session_id="review-session-1",
        launcher_session_id="launcher-session-1",
        launcher_thread_id="launcher-thread-1",
        reviewer_agent_id="reviewer-agent-1",
    )


def test_guard_rejects_closed_state_without_closure(tmp_path: Path) -> None:
    lineage_root, stage_dir, request, digest = _stage(tmp_path)
    write_review_runtime_state(
        stage_dir,
        review_state="review_closed_pass",
        active_review_cycle_id=str(request["review_cycle_id"]),
        review_requested_at="2026-05-11T00:00:00Z",
        review_bound_author_digest=digest,
        reviewer_identity="reviewer-1",
        reviewer_session_id="review-session-1",
        last_review_verdict="PASS",
        closure_written_at="2026-05-11T00:01:00Z",
    )

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=["research_route.yaml"],
            required_provenance_paths=["program_execution_manifest.json"],
            allow_missing_state=True,
        )

    assert exc_info.value.reason_code == REVIEW_STATE_PROJECTION_DRIFT
    assert "review_closed_pass" in str(exc_info.value)


def test_guard_rejects_state_bound_to_stale_author_digest(tmp_path: Path) -> None:
    lineage_root, stage_dir, request, digest = _stage(tmp_path)
    _issue_receipt(stage_dir)
    write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id=str(request["review_cycle_id"]),
        review_requested_at="2026-05-11T00:00:00Z",
        review_bound_author_digest=digest,
        reviewer_identity="reviewer-1",
        reviewer_session_id="review-session-1",
    )
    _write(stage_dir / "author" / "formal" / "research_route.yaml", "route: changed\n")

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=["research_route.yaml"],
            required_provenance_paths=["program_execution_manifest.json"],
            allow_missing_state=True,
        )

    assert exc_info.value.reason_code == REVIEW_STATE_PROJECTION_DRIFT
    assert "review_bound_author_digest" in str(exc_info.value)


def test_guard_rejects_raw_findings_without_receipt(tmp_path: Path) -> None:
    lineage_root, stage_dir, _request, _digest = _stage(tmp_path)
    _write(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        yaml.safe_dump(
            {
                "review_cycle_id": "bad",
                "reviewer_agent_id": "reviewer-1",
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
            },
            sort_keys=False,
        ),
    )

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=["research_route.yaml"],
            required_provenance_paths=["program_execution_manifest.json"],
            allow_missing_state=True,
        )

    assert exc_info.value.reason_code == REVIEWER_FINDINGS_UNBOUND


def test_guard_accepts_valid_in_progress_state_and_bound_raw_findings(tmp_path: Path) -> None:
    lineage_root, stage_dir, request, digest = _stage(tmp_path)
    receipt = _issue_receipt(stage_dir)
    write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id=str(request["review_cycle_id"]),
        review_requested_at="2026-05-11T00:00:00Z",
        review_bound_author_digest=digest,
        reviewer_identity="reviewer-1",
        reviewer_session_id="review-session-1",
    )
    _write(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        yaml.safe_dump(
            {
                "review_cycle_id": request["review_cycle_id"],
                "reviewer_agent_id": receipt["reviewer_agent_id"],
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
            },
            sort_keys=False,
        ),
    )

    assert_protected_review_state_intact(
        stage_dir=stage_dir,
        lineage_root=lineage_root,
        required_outputs=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        allow_missing_state=True,
    )
