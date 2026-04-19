from __future__ import annotations

import json
import os
from pathlib import Path
from subprocess import run
import sys

from runtime.tools.stage_evaluator import (
    STAGE_EVALUATOR_FILENAME,
    STAGE_EVALUATOR_RESULTS_FILENAME,
    evaluate_stage,
    write_stage_evaluator_artifacts,
)
from tests.helpers.repo_paths import REPO_ROOT
from tests.helpers.lineage_program_support import write_fake_stage_provenance
from tests.session.test_research_session_runtime import (
    _write_adversarial_review_request,
    _write_adversarial_review_result,
    _write_spawned_reviewer_receipt,
    _write_stage_completion_certificate,
    _write_minimal_stage_outputs,
)
from runtime.tools.research_session import run_research_session


def test_evaluate_stage_reports_review_confirmation_pending_before_review_starts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_fake_stage_provenance(lineage_root, "mandate")

    payload = evaluate_stage(stage_dir, lineage_root=lineage_root)

    assert payload["stage"] == "mandate"
    assert payload["pass"] is False
    assert payload["can_progress"] is False
    assert payload["status"] == "review_confirmation_pending"
    assert payload["required_outputs_checked"]["missing"] == []
    assert payload["review_summary"]["review_request_present"] is False
    assert payload["review_summary"]["closure_complete"] is False


def test_write_stage_evaluator_artifacts_writes_current_and_ledger_for_passed_stage(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage="mandate",
        program_dir="program/mandate",
        outcome="CLOSURE_READY_PASS",
    )
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")

    payload = write_stage_evaluator_artifacts(stage_dir, lineage_root=lineage_root)
    second_payload = write_stage_evaluator_artifacts(stage_dir, lineage_root=lineage_root)

    assert payload["stage"] == "mandate"
    assert payload["pass"] is True
    assert payload["can_progress"] is True
    assert payload["status"] == "passed"
    assert payload["review_summary"]["review_result_present"] is True
    assert payload["review_summary"]["review_audit_present"] is True
    assert payload["review_summary"]["closure_complete"] is True
    assert payload["review_summary"]["final_verdict"] == "PASS"

    evaluation_dir = stage_dir / "evaluation"
    current_path = evaluation_dir / STAGE_EVALUATOR_FILENAME
    ledger_path = evaluation_dir / STAGE_EVALUATOR_RESULTS_FILENAME
    assert current_path.exists()
    assert ledger_path.exists()

    current_payload = json.loads(current_path.read_text(encoding="utf-8"))
    assert current_payload["status"] == "passed"

    lines = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    assert lines[0]["status"] == "passed"
    assert lines[1]["status"] == "passed"
    assert second_payload["status"] == "passed"


def test_evaluate_stage_script_emits_json_for_pre_review_stage(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    script_path = REPO_ROOT / "runtime" / "scripts" / "evaluate_stage.py"

    result = run(
        [sys.executable, str(script_path), "--stage-dir", str(stage_dir), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["stage"] == "mandate"
    assert payload["status"] == "review_confirmation_pending"


def test_stage_evaluator_matches_runtime_for_fix_required_review_state(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage="mandate",
        program_dir="program/mandate",
        outcome="FIX_REQUIRED",
    )

    evaluator = evaluate_stage(stage_dir, lineage_root=lineage_root)
    session = run_research_session(outputs_root=outputs_root, lineage_id="topic_a")

    assert evaluator["status"] == "review_fix_required"
    assert evaluator["pass"] is False
    assert evaluator["can_progress"] is False
    assert session.blocking_reason_code == "AUTHOR_FIX_REQUIRED"
    assert session.current_stage == "mandate_review"


def test_stage_evaluator_matches_runtime_for_review_audit_pending_state(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage="mandate",
        program_dir="program/mandate",
        outcome="CLOSURE_READY_PASS",
    )
    audit_path = stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml"
    if audit_path.exists():
        audit_path.unlink()

    evaluator = evaluate_stage(stage_dir, lineage_root=lineage_root)
    session = run_research_session(outputs_root=outputs_root, lineage_id="topic_a")

    assert evaluator["status"] == "review_audit_pending"
    assert evaluator["pass"] is False
    assert evaluator["can_progress"] is False
    assert session.blocking_reason_code == "REVIEW_AUDIT_PENDING"
    assert session.current_stage == "mandate_review"


def test_stage_evaluator_invalidates_stale_review_cycle_after_author_output_changes(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage="mandate",
        program_dir="program/mandate",
        outcome="CLOSURE_READY_PASS",
    )
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")

    mandate_path = stage_dir / "author" / "formal" / "mandate.md"
    mandate_path.write_text("changed after review\n", encoding="utf-8")
    os.utime(mandate_path, None)

    evaluator = evaluate_stage(stage_dir, lineage_root=lineage_root)
    session = run_research_session(outputs_root=outputs_root, lineage_id="topic_a")

    assert evaluator["status"] == "review_pending"
    assert evaluator["pass"] is False
    assert evaluator["can_progress"] is False
    assert "stale" in evaluator["reason"].lower()
    assert session.current_stage == "mandate_review"
    assert session.blocking_reason_code == "ADVERSARIAL_REVIEW_PENDING"
    assert "stale" in (session.blocking_reason or "").lower()
