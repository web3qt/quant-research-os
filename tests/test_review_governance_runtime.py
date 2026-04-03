from pathlib import Path

import yaml

from tools.review_governance_runtime import governance_root_for_lineage, record_review_governance, update_governance_candidates
from tools.review_skillgen.adversarial_review_contract import FIX_REQUIRED_OUTCOME
from tools.review_skillgen.governance_signal import load_review_governance_policy


def _request_payload(*, lineage_id: str, cycle_id: str, started_at: str) -> dict:
    return {
        "review_cycle_id": cycle_id,
        "lineage_id": lineage_id,
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


def _review_result(*, cycle_id: str, outcome: str = "CLOSURE_READY_PASS") -> dict:
    return {
        "review_cycle_id": cycle_id,
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


def _record_case(
    tmp_path: Path,
    *,
    lineage_id: str,
    cycle_id: str,
    started_at: str = "2026-04-03T09:30:00Z",
    finding: str = "Missing required output: parameter_grid.yaml",
    outcome: str = "CLOSURE_READY_PASS",
) -> tuple[Path, dict]:
    lineage_root = tmp_path / "outputs" / lineage_id
    stage_dir = lineage_root / "mandate"
    stage_dir.mkdir(parents=True, exist_ok=True)
    result = record_review_governance(
        stage_dir=stage_dir,
        lineage_root=lineage_root,
        stage="mandate",
        request_payload=_request_payload(lineage_id=lineage_id, cycle_id=cycle_id, started_at=started_at),
        review_result=_review_result(cycle_id=cycle_id, outcome=outcome),
        review_loop_outcome=outcome,
        final_verdict=None if outcome == FIX_REQUIRED_OUTCOME else "PASS",
        blocking_findings=[finding],
        reservation_findings=[],
        info_findings=[],
    )
    return lineage_root, result


def test_record_review_governance_opens_candidate_after_threshold(tmp_path: Path) -> None:
    _record_case(tmp_path, lineage_id="case_a", cycle_id="cycle-a")
    _record_case(tmp_path, lineage_id="case_b", cycle_id="cycle-b")
    lineage_root, result = _record_case(tmp_path, lineage_id="case_c", cycle_id="cycle-c")

    governance_root = governance_root_for_lineage(lineage_root)
    ledger_path = governance_root / "review_findings_ledger.jsonl"
    lines = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 3
    assert result["ledger_entries_written"] == 1

    candidates = sorted((governance_root / "candidates").glob("*.yaml"))
    assert len(candidates) == 1
    payload = yaml.safe_load(candidates[0].read_text(encoding="utf-8"))
    assert payload["candidate_class"] == "hard_gate"
    assert payload["policy_activation_state"] == "inactive"
    assert payload["status"] == "awaiting_governance_decision"


def test_record_review_governance_dedupes_same_review_cycle(tmp_path: Path) -> None:
    lineage_root, first = _record_case(tmp_path, lineage_id="case_a", cycle_id="cycle-a")
    _, second = _record_case(tmp_path, lineage_id="case_a", cycle_id="cycle-a")

    ledger_path = governance_root_for_lineage(lineage_root) / "review_findings_ledger.jsonl"
    lines = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    assert first["ledger_entries_written"] == 1
    assert second["ledger_entries_written"] == 0


def test_record_review_governance_skips_pre_rollout_entries(tmp_path: Path) -> None:
    lineage_root, result = _record_case(
        tmp_path,
        lineage_id="historical_case",
        cycle_id="cycle-historical",
        started_at="2026-04-02T23:59:59Z",
    )

    governance_root = governance_root_for_lineage(lineage_root)
    assert result["bundle"]["post_rollout_only"] is False
    assert not (governance_root / "review_findings_ledger.jsonl").exists()
    assert result["ledger_entries_written"] == 0


def test_update_governance_candidates_requires_decision_artifact_for_approved_status(tmp_path: Path) -> None:
    _record_case(tmp_path, lineage_id="case_a", cycle_id="cycle-a")
    _record_case(tmp_path, lineage_id="case_b", cycle_id="cycle-b")
    lineage_root, _ = _record_case(tmp_path, lineage_id="case_c", cycle_id="cycle-c")

    governance_root = governance_root_for_lineage(lineage_root)
    candidate_path = next((governance_root / "candidates").glob("*.yaml"))
    candidate = yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
    assert candidate["status"] == "awaiting_governance_decision"

    decisions_dir = governance_root / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    decision_path = decisions_dir / "decision-1.md"
    decision_path.write_text(
        "---\n"
        f"candidate_id: {candidate['candidate_id']}\n"
        "decision_outcome: approve\n"
        "planned_change_ref: issue-123\n"
        "---\n",
        encoding="utf-8",
    )
    update_governance_candidates(governance_root=governance_root, policy=load_review_governance_policy())

    updated = yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
    assert updated["status"] == "approved"
    assert updated["policy_activation_state"] == "inactive"
