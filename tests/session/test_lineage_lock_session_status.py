from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from runtime.tools.lineage_lock_ledger import FROZEN_ARTIFACT_MUTATED, lock_reviewed_stage
from runtime.tools.progress_runtime import progress_status_payload
from runtime.tools.research_session import (
    CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS,
    run_research_session,
    write_review_transition_decision,
)
from runtime.tools.review_skillgen.adversarial_review_contract import ensure_adversarial_review_request
from runtime.tools.review_skillgen.protected_state_guard import REVIEWER_FINDINGS_UNBOUND
from runtime.tools.review_skillgen.review_result_writer import RAW_REVIEWER_FINDINGS_FILENAME
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest,
    write_review_runtime_state,
)
from runtime.tools.stage_entry_guard import StageEntryGuardError, check_stage_entry_for_lineage


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _locked_mutated_lineage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    _write(
        stage_dir / "author" / "formal" / "research_route.yaml",
        "\n".join(
            [
                "research_route: cross_sectional_factor",
                "factor_role: standalone_alpha",
                "factor_structure: single_factor",
                "portfolio_expression: long_short_rank_based",
                "neutralization_policy: market_beta_neutral",
                "",
            ]
        ),
    )
    _write(stage_dir / "author" / "formal" / "program_execution_manifest.json", "{}\n")
    for name in (
        "latest_review_pack.yaml",
        "stage_completion_certificate.yaml",
        "stage_gate_review.yaml",
    ):
        _write(stage_dir / "review" / "closure" / name, "final_verdict: PASS\n")
    lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T00:00:00+00:00",
    )
    _write(
        stage_dir / "author" / "formal" / "research_route.yaml",
        "research_route: cross_sectional_factor\nfactor_role: changed\n",
    )
    return lineage_root


def _build_review_pending_lineage(tmp_path: Path) -> tuple[Path, Path, Path]:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    for name in (
        "mandate.md",
        "research_scope.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ):
        _write(formal_dir / name, "ok\n")
    _write(
        formal_dir / "research_route.yaml",
        "\n".join(
            [
                "research_route: cross_sectional_factor",
                "factor_role: standalone_alpha",
                "factor_structure: single_factor",
                "portfolio_expression: long_short_rank_based",
                "neutralization_policy: market_beta_neutral",
                "",
            ]
        ),
    )
    _write(formal_dir / "time_split.json", "{}\n")
    _write(formal_dir / "parameter_grid.yaml", "parameters: []\n")
    _write(formal_dir / "run_config.toml", "version = 1\n")
    _write(formal_dir / "program_execution_manifest.json", "{}\n")
    return outputs_root, lineage_root, stage_dir


def _build_csf_train_freeze_review_lineage(tmp_path: Path) -> tuple[Path, Path, Path]:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "lineage_a"
    stage_dir = lineage_root / "04_csf_train_freeze"
    formal_dir = stage_dir / "author" / "formal"
    for name in CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS:
        _write(formal_dir / name, "ok\n")
    _write(formal_dir / "program_execution_manifest.json", "{}\n")
    _write(
        lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml",
        "\n".join(
            [
                "research_route: cross_sectional_factor",
                "factor_role: standalone_alpha",
                "factor_structure: single_factor",
                "portfolio_expression: long_short_rank_based",
                "neutralization_policy: market_beta_neutral",
                "",
            ]
        ),
    )
    write_review_transition_decision(
        lineage_root,
        current_stage="csf_train_freeze_review_confirmation_pending",
    )
    ensure_adversarial_review_request(
        stage_dir,
        lineage_id=lineage_root.name,
        stage="csf_train_freeze",
        author_identity="author-agent",
        author_session_id="author-session",
        required_program_dir="program/cross_sectional_factor/train_freeze",
        required_program_entrypoint="run_stage.py",
        required_artifact_paths=list(CSF_TRAIN_FREEZE_REQUIRED_OUTPUTS),
        required_provenance_paths=["program_execution_manifest.json"],
    )
    return outputs_root, lineage_root, stage_dir


def test_progress_status_surfaces_frozen_artifact_mutation(tmp_path: Path) -> None:
    lineage_root = _locked_mutated_lineage(tmp_path)

    payload = progress_status_payload(outputs_root=lineage_root.parent, lineage_id=lineage_root.name)

    assert payload["stage_status"] == "blocked"
    assert payload["blocking_reason_code"] == FROZEN_ARTIFACT_MUTATED
    assert payload["gate_status"] == FROZEN_ARTIFACT_MUTATED
    assert "Restore 01_mandate/author/formal/research_route.yaml" in payload["next_action"]
    assert FROZEN_ARTIFACT_MUTATED in payload["blocking_reason"]


def test_research_session_surfaces_frozen_artifact_mutation_before_writes(tmp_path: Path) -> None:
    lineage_root = _locked_mutated_lineage(tmp_path)

    status = run_research_session(outputs_root=lineage_root.parent, lineage_id=lineage_root.name)

    assert status.stage_status == "blocked"
    assert status.blocking_reason_code == FROZEN_ARTIFACT_MUTATED
    assert status.gate_status == FROZEN_ARTIFACT_MUTATED
    assert "Restore 01_mandate/author/formal/research_route.yaml" in status.next_action
    assert status.artifacts_written == []


def test_stage_entry_guard_blocks_frozen_artifact_mutation(tmp_path: Path) -> None:
    lineage_root = _locked_mutated_lineage(tmp_path)

    with pytest.raises(StageEntryGuardError) as exc_info:
        check_stage_entry_for_lineage(lineage_root, stage="csf_data_ready", lane="author")

    result = exc_info.value.result
    assert result.allowed is False
    assert result.current_active_skill == "qros-research-session"
    assert FROZEN_ARTIFACT_MUTATED in result.message
    assert "Restore 01_mandate/author/formal/research_route.yaml" in result.message


def test_progress_surfaces_protected_review_state_drift(tmp_path: Path) -> None:
    outputs_root, lineage_root, stage_dir = _build_review_pending_lineage(tmp_path)
    _write(
        stage_dir / "review" / "state" / "review_runtime_state.yaml",
        yaml.safe_dump(
            {
                "review_state": "review_closed_pass",
                "active_review_cycle_id": "manual-cycle",
                "review_bound_author_digest": "0" * 64,
                "last_review_verdict": "PASS",
                "closure_written_at": "2026-05-11T00:00:00Z",
                "updated_at": "2026-05-11T00:00:00Z",
            },
            sort_keys=False,
        ),
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert payload["stage_status"] == "blocked"
    assert payload["gate_status"] == "PROTECTED_STATE_DRIFT"
    assert payload["blocking_reason_code"] == "REVIEW_STATE_PROJECTION_DRIFT"
    assert "qros-review-cycle reset --archive-stale-cycle" in payload["next_action"]


def test_progress_blocks_raw_findings_after_closed_review_state(tmp_path: Path) -> None:
    outputs_root, lineage_root, stage_dir = _build_review_pending_lineage(tmp_path)
    required_outputs = [
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "program_execution_manifest.json",
    ]
    author_digest = compute_author_materialization_digest(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=required_outputs,
        required_provenance_paths=["program_execution_manifest.json"],
    )
    write_review_runtime_state(
        stage_dir,
        review_state="review_closed_pass",
        active_review_cycle_id="manual-cycle",
        review_requested_at="2026-05-11T00:00:00Z",
        review_bound_author_digest=author_digest,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="reviewer-session",
        last_review_verdict="PASS",
        closure_written_at="2026-05-11T00:00:00Z",
    )
    for name in (
        "latest_review_pack.yaml",
        "stage_completion_certificate.yaml",
        "stage_gate_review.yaml",
    ):
        _write(stage_dir / "review" / "closure" / name, "final_verdict: PASS\n")
    _write(
        stage_dir / "review" / "result" / RAW_REVIEWER_FINDINGS_FILENAME,
        yaml.safe_dump(
            {
                "review_cycle_id": "manual-cycle",
                "reviewer_agent_id": "reviewer-child-agent",
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
            },
            sort_keys=False,
        ),
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert payload["stage_status"] == "blocked"
    assert payload["gate_status"] == "PROTECTED_STATE_DRIFT"
    assert payload["blocking_reason_code"] == REVIEWER_FINDINGS_UNBOUND


def test_progress_payload_exposes_direct_handoff_for_review_complete(tmp_path: Path) -> None:
    outputs_root, lineage_root, stage_dir = _build_review_pending_lineage(tmp_path)
    for name in (
        "latest_review_pack.yaml",
        "stage_completion_certificate.yaml",
        "stage_gate_review.yaml",
    ):
        _write(stage_dir / "review" / "closure" / name, "final_verdict: PASS\nstage_status: PASS\n")

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert payload["current_stage"] == "mandate_next_stage_confirmation_pending"
    assert payload["recommended_skill"] == "qros-research-session"
    assert payload["handoff_hint"] == "Continue with qros-research-session."
    assert payload["next_action"] == "Continue with qros-research-session."
    assert payload["resume_hint"] == "Continue with qros-research-session."
    assert "qros-session" not in payload["handoff_hint"]
    assert "qros-resume" not in payload["handoff_hint"]
    assert "qros-session" not in payload["next_action"]
    assert "qros-resume" not in payload["next_action"]
    assert "clear_required" not in payload
    assert "clear_instruction" not in payload
    assert "qros-resume" not in payload["next_action"]


def test_research_session_surfaces_protected_review_state_drift_before_writes(tmp_path: Path) -> None:
    _outputs_root, lineage_root, stage_dir = _build_review_pending_lineage(tmp_path)
    _write(
        stage_dir / "review" / "state" / "review_runtime_state.yaml",
        yaml.safe_dump(
            {
                "review_state": "review_closed_pass",
                "active_review_cycle_id": "manual-cycle",
                "review_bound_author_digest": "0" * 64,
                "last_review_verdict": "PASS",
                "closure_written_at": "2026-05-11T00:00:00Z",
                "updated_at": "2026-05-11T00:00:00Z",
            },
            sort_keys=False,
        ),
    )

    status = run_research_session(outputs_root=lineage_root.parent, lineage_id=lineage_root.name)

    assert status.stage_status == "blocked"
    assert status.gate_status == "PROTECTED_STATE_DRIFT"
    assert status.blocking_reason_code == "REVIEW_STATE_PROJECTION_DRIFT"
    assert status.artifacts_written == []


def test_stage_entry_guard_blocks_protected_review_state_drift(tmp_path: Path) -> None:
    _outputs_root, lineage_root, stage_dir = _build_review_pending_lineage(tmp_path)
    _write(
        stage_dir / "review" / "state" / "review_runtime_state.yaml",
        yaml.safe_dump(
            {
                "review_state": "review_closed_pass",
                "active_review_cycle_id": "manual-cycle",
                "review_bound_author_digest": "0" * 64,
                "last_review_verdict": "PASS",
                "closure_written_at": "2026-05-11T00:00:00Z",
                "updated_at": "2026-05-11T00:00:00Z",
            },
            sort_keys=False,
        ),
    )

    with pytest.raises(StageEntryGuardError) as exc_info:
        check_stage_entry_for_lineage(lineage_root, stage="mandate", lane="review")

    result = exc_info.value.result
    assert result.allowed is False
    assert result.current_active_skill == "qros-research-session"
    assert "REVIEW_STATE_PROJECTION_DRIFT" in result.message


def test_session_routes_fix_required_and_retry_differently_from_final_review(tmp_path: Path) -> None:
    outputs_root, lineage_root, stage_dir = _build_csf_train_freeze_review_lineage(tmp_path)
    review_dir = stage_dir / "review"
    fix_required_payload = {
        "lineage_id": lineage_root.name,
        "stage_id": "csf_train_freeze",
        "reviewer_identity": "reviewer",
        "reviewer_agent_id": "agent-1",
        "reviewed_artifact_paths": ["author/formal/csf_train_freeze.yaml"],
        "reviewed_program_path": "program/cross_sectional_factor/train_freeze/run_stage.py",
        "reviewed_artifact_digest": "sha256:a",
        "reviewed_program_digest": "sha256:b",
        "verdict": "FIX_REQUIRED",
        "review_summary": "binding mismatch",
        "blocking_findings": ["binding mismatch"],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": ["refresh current stage formal artifacts"],
        "rollback_stage": "csf_train_freeze",
        "downstream_permissions": [],
        "recommended_next_action": "resume author-fix",
    }
    _write(
        review_dir / "final_review.yaml",
        yaml.safe_dump(fix_required_payload, sort_keys=False),
    )

    fix_status = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert fix_status["current_stage"] == "csf_train_freeze_review"
    assert fix_status["current_skill"] == "qros-csf-train-freeze-author"
    assert fix_status["review_state"] == "awaiting_author_fix"
    assert fix_status["blocking_reason_code"] == "AUTHOR_FIX_REQUIRED"
    assert "author" in fix_status["next_action"]
    assert "failure" not in fix_status["next_action"]

    for verdict in ("RETRY", "NO-GO", "CHILD LINEAGE"):
        retry_payload = dict(fix_required_payload)
        retry_payload["verdict"] = verdict
        retry_payload["recommended_next_action"] = "enter failure handling"
        _write(
            review_dir / "final_review.yaml",
            yaml.safe_dump(retry_payload, sort_keys=False),
        )

        retry_status = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

        assert retry_status["current_stage"] == "csf_train_freeze_review"
        assert retry_status["current_skill"] == "qros-stage-failure-handler"
        assert retry_status["review_state"] == "review_blocked_failure_handling"
        assert retry_status["blocking_reason_code"] == "FAILURE_HANDLING_REQUIRED"
        assert "failure" in retry_status["next_action"]
        assert "author" not in retry_status["next_action"]
