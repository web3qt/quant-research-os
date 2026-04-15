from __future__ import annotations

import json
from pathlib import Path
from subprocess import run
import sys

import yaml

from runtime.tools.review_governance_runtime import governance_root_for_lineage, record_review_governance


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


def _review_result(*, cycle_id: str) -> dict:
    return {
        "review_cycle_id": cycle_id,
        "reviewer_identity": "reviewer-agent",
        "reviewer_role": "reviewer",
        "reviewer_session_id": "review-session",
        "reviewer_mode": "adversarial",
        "review_loop_outcome": "CLOSURE_READY_PASS",
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


def _open_candidate(tmp_path: Path) -> tuple[Path, str]:
    for lineage_id, cycle_id in (("case_a", "cycle-a"), ("case_b", "cycle-b"), ("case_c", "cycle-c")):
        lineage_root = tmp_path / "outputs" / lineage_id
        stage_dir = lineage_root / "mandate"
        stage_dir.mkdir(parents=True, exist_ok=True)
        record_review_governance(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            stage="mandate",
            request_payload=_request_payload(lineage_id=lineage_id, cycle_id=cycle_id, started_at="2026-04-03T09:30:00Z"),
            review_result=_review_result(cycle_id=cycle_id),
            review_loop_outcome="CLOSURE_READY_PASS",
            final_verdict="PASS",
            blocking_findings=["Missing required output: parameter_grid.yaml"],
            reservation_findings=[],
            info_findings=[],
        )
    governance_root = governance_root_for_lineage(tmp_path / "outputs" / "case_c")
    candidate_path = next((governance_root / "candidates").glob("*.yaml"))
    candidate = yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
    return governance_root, candidate["candidate_id"]


def test_record_governance_decision_script_captures_and_records(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "runtime" / "scripts" / "record_governance_decision.py"
    governance_root, candidate_id = _open_candidate(tmp_path)

    capture = run(
        [
            sys.executable,
            str(script),
            "--action",
            "capture",
            "--governance-root",
            str(governance_root),
            "--candidate-id",
            candidate_id,
            "--decision",
            "approved",
            "--note",
            "Human approved this for follow-up repo work.",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert capture.returncode == 0, capture.stderr
    capture_payload = json.loads(capture.stdout)
    pending_path = Path(capture_payload["pending_decision_path"])
    assert pending_path.exists()

    record = run(
        [
            sys.executable,
            str(script),
            "--action",
            "record",
            "--governance-root",
            str(governance_root),
            "--candidate-id",
            candidate_id,
            "--decision",
            "approved",
            "--note",
            "Human approved this for follow-up repo work.",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert record.returncode == 0, record.stderr
    record_payload = json.loads(record.stdout)
    assert Path(record_payload["decision_path"]).exists()
    assert not pending_path.exists()
