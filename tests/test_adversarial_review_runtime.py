from pathlib import Path

import pytest
import yaml

from tests.lineage_program_support import STAGE_PROGRAM_SPECS, ensure_stage_program, write_fake_stage_provenance
from tests.test_research_session_runtime import _write_minimal_stage_outputs
from runtime.tools.research_session import _program_spec_for_session_stage, run_research_session
from runtime.tools.review_skillgen.adversarial_review_contract import (
    ensure_adversarial_review_request,
    issue_spawned_reviewer_receipt,
    load_adversarial_review_request,
)
from runtime.tools.review_skillgen.review_engine import run_stage_review
from runtime.tools.review_skillgen.reviewer_write_scope_audit import run_reviewer_write_scope_audit


MANDATE_REQUIRED_OUTPUTS = [
    "mandate.md",
    "research_scope.md",
    "research_route.yaml",
    "time_split.json",
    "parameter_grid.yaml",
    "run_config.toml",
    "artifact_catalog.md",
    "field_dictionary.md",
    "run_manifest.json",
]


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_stage(tmp_path: Path) -> tuple[Path, Path]:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    (stage_dir / "author" / "formal").mkdir(parents=True)
    (stage_dir / "review" / "request").mkdir(parents=True)
    (stage_dir / "review" / "result").mkdir(parents=True)

    for name in MANDATE_REQUIRED_OUTPUTS:
        (stage_dir / "author" / "formal" / name).write_text("ok\n", encoding="utf-8")

    ensure_stage_program(lineage_root, "mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    return lineage_root, stage_dir


def _write_adversarial_review_request(
    stage_dir: Path,
    *,
    stage_key: str = "mandate",
    author_identity: str = "test-agent",
    author_session_id: str = "test-session",
) -> None:
    review_spec = _program_spec_for_session_stage(f"{stage_key}_review")
    assert review_spec is not None
    ensure_adversarial_review_request(
        stage_dir,
        lineage_id=stage_dir.parent.name,
        stage=review_spec.stage_id,
        author_identity=author_identity,
        author_session_id=author_session_id,
        required_program_dir=str(STAGE_PROGRAM_SPECS[stage_key]["program_dir"]),
        required_program_entrypoint="run_stage.py",
        required_artifact_paths=list(review_spec.required_outputs),
        required_provenance_paths=["program_execution_manifest.json"],
        program_hash="test-hash",
        stage_invoked_at="2026-04-03T00:00:00+00:00",
    )


def _review_request_payload(stage_dir: Path) -> dict:
    return load_adversarial_review_request(stage_dir / "review" / "request" / "adversarial_review_request.yaml")


def _request_review_cycle_id(stage_dir: Path) -> str:
    return _review_request_payload(stage_dir)["review_cycle_id"]


def _write_spawned_reviewer_receipt(
    stage_dir: Path,
    *,
    reviewer_identity: str = "reviewer-agent",
    reviewer_session_id: str = "reviewer-session",
    spawned_agent_id: str = "reviewer-child-agent",
) -> None:
    issue_spawned_reviewer_receipt(
        stage_dir,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id="launcher-session",
        launcher_thread_id="leader-thread",
        spawned_agent_id=spawned_agent_id,
    )


def _write_adversarial_review_result(
    stage_dir: Path,
    *,
    stage_key: str = "mandate",
    reviewer_identity: str,
    review_loop_outcome: str,
    reviewer_mode: str = "adversarial",
    write_audit: bool = True,
) -> None:
    spec = STAGE_PROGRAM_SPECS[stage_key]
    request_payload = _review_request_payload(stage_dir)
    _write_yaml(
        stage_dir / "review" / "result" / "adversarial_review_result.yaml",
        {
            "review_cycle_id": request_payload["review_cycle_id"],
            "reviewer_identity": reviewer_identity,
            "reviewer_role": "adversarial-reviewer",
            "reviewer_session_id": "reviewer-session",
            "reviewer_mode": reviewer_mode,
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewer_execution_mode": "spawned_agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
            "reviewed_program_dir": str(spec["program_dir"]),
            "reviewed_program_entrypoint": "run_stage.py",
            "reviewed_artifact_paths": [Path(path).name for path in spec["outputs"][:2]],
            "reviewed_provenance_paths": ["program_execution_manifest.json"],
            "review_loop_outcome": review_loop_outcome,
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )
    if write_audit:
        run_reviewer_write_scope_audit(stage_dir)


def _prepare_review_runtime_case(
    tmp_path: Path,
    *,
    lineage_id: str,
    stage_key: str,
    stage_dir_name: str,
) -> tuple[Path, Path]:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / lineage_id
    stage_dir = lineage_root / stage_dir_name
    _write_minimal_stage_outputs(stage_dir, stage=stage_key)
    ensure_stage_program(lineage_root, stage_key)
    write_fake_stage_provenance(lineage_root, stage_key)
    if stage_key.startswith("csf_"):
        mandate_dir = lineage_root / "01_mandate"
        (mandate_dir / "author" / "formal").mkdir(parents=True, exist_ok=True)
        _write_yaml(
            mandate_dir / "author" / "formal" / "research_route.yaml",
            {
                "research_route": "cross_sectional_factor",
                "factor_role": "standalone_alpha",
                "factor_structure": "single_factor",
                "portfolio_expression": "long_short_market_neutral",
                "neutralization_policy": "group_neutral",
            },
        )
    return outputs_root, stage_dir


def test_run_stage_review_rejects_self_review_from_runtime_contract(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(
        stage_dir,
        stage_key="mandate",
        author_identity="author-agent",
    )
    _write_spawned_reviewer_receipt(stage_dir, reviewer_identity="author-agent")
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="author-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    _write_yaml(
        stage_dir / "review" / "result" / "review_findings.yaml",
        {
            "reviewer_identity": "author-agent",
            "recommended_verdict": "PASS",
        },
    )

    with pytest.raises(ValueError, match="self-review|reviewer.*author"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="author-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_fix_required_does_not_write_closure_artifacts(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(
        stage_dir,
        stage_key="mandate",
        author_identity="author-agent",
    )
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="FIX_REQUIRED",
    )
    _write_yaml(
        stage_dir / "review" / "result" / "review_findings.yaml",
        {
            "reviewer_identity": "reviewer-agent",
            "recommended_verdict": "RETRY",
            "blocking_findings": ["Need stronger provenance linkage."],
            "rollback_stage": "mandate",
            "allowed_modifications": ["artifact corrections only"],
        },
    )

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="adversarial-reviewer",
        reviewer_session_id="reviewer-session",
        reviewer_mode="adversarial",
    )

    assert payload["review_loop_outcome"] == "FIX_REQUIRED"
    assert not (stage_dir / "review" / "closure" / "latest_review_pack.yaml").exists()
    assert not (stage_dir / "review" / "closure" / "stage_gate_review.yaml").exists()
    assert not (stage_dir / "review" / "closure" / "stage_completion_certificate.yaml").exists()


def test_run_stage_review_rejects_non_adversarial_reviewer_mode(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(
        stage_dir,
        stage_key="mandate",
        author_identity="author-agent",
    )
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
        reviewer_mode="observer",
    )
    _write_yaml(
        stage_dir / "review" / "result" / "review_findings.yaml",
        {
            "reviewer_identity": "reviewer-agent",
            "recommended_verdict": "PASS",
        },
    )
    run_reviewer_write_scope_audit(stage_dir)

    with pytest.raises(ValueError, match="adversarial"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="observer",
        )


def test_run_stage_review_rewrites_scope_to_match_runtime_request(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(
        stage_dir,
        stage_key="mandate",
        author_identity="author-agent",
    )
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
        write_audit=False,
    )
    _write_yaml(
        stage_dir / "review" / "result" / "adversarial_review_result.yaml",
        {
            "review_cycle_id": _request_review_cycle_id(stage_dir),
            "reviewer_identity": "reviewer-agent",
            "reviewer_role": "adversarial-reviewer",
            "reviewer_session_id": "reviewer-session",
            "reviewer_mode": "adversarial",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewer_execution_mode": "spawned_agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "handoff_manifest_digest": _review_request_payload(stage_dir)["handoff_manifest_digest"],
            "reviewed_program_dir": "program/unapproved_scope",
            "reviewed_program_entrypoint": "alternate.py",
            "reviewed_artifact_paths": ["mandate.md", "research_scope.md"],
            "reviewed_provenance_paths": ["program_execution_manifest.json"],
            "review_loop_outcome": "CLOSURE_READY_PASS",
        },
    )
    _write_yaml(
        stage_dir / "review" / "result" / "review_findings.yaml",
        {
            "reviewer_identity": "reviewer-agent",
            "recommended_verdict": "PASS",
        },
    )
    run_reviewer_write_scope_audit(stage_dir)

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="adversarial-reviewer",
        reviewer_session_id="reviewer-session",
        reviewer_mode="adversarial",
    )

    result_payload = yaml.safe_load(
        (stage_dir / "review" / "result" / "adversarial_review_result.yaml").read_text(encoding="utf-8")
    )
    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    assert payload["final_verdict"] == "PASS"
    assert result_payload["reviewed_program_dir"] == "program/mandate"
    assert result_payload["reviewed_program_entrypoint"] == "run_stage.py"
    assert sorted(result_payload["reviewed_artifact_paths"]) == sorted(request_payload["required_artifact_paths"])


@pytest.mark.parametrize(
    ("lineage_id", "stage_key", "stage_dir_name", "expected_stage", "expected_skill"),
    [
        (
            "btc_review_case",
            "test_evidence",
            "05_test_evidence",
            "test_evidence_review",
            "qros-test-evidence-review",
        ),
        (
            "csf_review_case",
            "csf_test_evidence",
            "05_csf_test_evidence",
            "csf_test_evidence_review",
            "qros-csf-test-evidence-review",
        ),
    ],
)
def test_run_research_session_reports_awaiting_adversarial_review_with_route_parity(
    tmp_path: Path,
    *,
    lineage_id: str,
    stage_key: str,
    stage_dir_name: str,
    expected_stage: str,
    expected_skill: str,
) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id=lineage_id,
        stage_key=stage_key,
        stage_dir_name=stage_dir_name,
    )
    _write_adversarial_review_request(stage_dir, stage_key=stage_key)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)

    assert status.current_stage == expected_stage
    assert status.current_skill == expected_skill
    assert status.stage_status == "awaiting_adversarial_review"
    assert status.blocking_reason_code == "ADVERSARIAL_REVIEW_PENDING"
    assert "spawned_reviewer_receipt.yaml" in (status.blocking_reason or "")


@pytest.mark.parametrize(
    ("lineage_id", "stage_key", "stage_dir_name", "expected_stage", "expected_author_skill"),
    [
        (
            "btc_fix_loop_case",
            "test_evidence",
            "05_test_evidence",
            "test_evidence_review",
            "qros-test-evidence-author",
        ),
        (
            "csf_fix_loop_case",
            "csf_test_evidence",
            "05_csf_test_evidence",
            "csf_test_evidence_review",
            "qros-csf-test-evidence-author",
        ),
    ],
)
def test_run_research_session_routes_fix_required_back_to_author_with_route_parity(
    tmp_path: Path,
    *,
    lineage_id: str,
    stage_key: str,
    stage_dir_name: str,
    expected_stage: str,
    expected_author_skill: str,
) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id=lineage_id,
        stage_key=stage_key,
        stage_dir_name=stage_dir_name,
    )
    _write_adversarial_review_request(stage_dir, stage_key=stage_key)
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage_key=stage_key,
        reviewer_identity="reviewer-agent",
        review_loop_outcome="FIX_REQUIRED",
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)

    assert status.current_stage == expected_stage
    assert status.current_skill == expected_author_skill
    assert status.stage_status == "awaiting_author_fix"
    assert status.blocking_reason_code == "AUTHOR_FIX_REQUIRED"
    assert "fix" in status.next_action.lower()


def test_run_research_session_waits_for_spawned_reviewer_child_after_receipt(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_spawned_wait_case",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    _write_spawned_reviewer_receipt(stage_dir, spawned_agent_id="reviewer-child-agent")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_spawned_wait_case")

    assert status.current_stage == "test_evidence_review"
    assert status.stage_status == "awaiting_spawned_reviewer_completion"
    assert status.blocking_reason_code == "ADVERSARIAL_REVIEW_PENDING"
    assert "reviewer-child-agent" in (status.blocking_reason or "")
    assert "reviewer-child-agent" in status.next_action


def test_run_research_session_waits_for_reviewer_write_scope_audit_before_closure(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_review_audit_pending",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage_key="test_evidence",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    (stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml").unlink()

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_review_audit_pending")

    assert status.current_stage == "test_evidence_review"
    assert status.stage_status == "awaiting_reviewer_write_scope_audit"
    assert status.blocking_reason_code == "REVIEW_AUDIT_PENDING"
    assert "reviewer_write_scope_audit.yaml" in (status.blocking_reason or "")
    assert "qros-audit-reviewer" in status.next_action


def test_run_research_session_keeps_review_pending_when_result_exists_without_receipt(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_result_without_receipt",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    _write_adversarial_review_result(
        stage_dir,
        stage_key="test_evidence",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="FIX_REQUIRED",
        write_audit=False,
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_result_without_receipt")

    assert status.current_stage == "test_evidence_review"
    assert status.stage_status == "awaiting_adversarial_review"
    assert status.blocking_reason_code == "ADVERSARIAL_REVIEW_PENDING"
    assert "spawned_reviewer_receipt.yaml" in (status.blocking_reason or "")
    assert "spawned_reviewer_receipt.yaml" in status.next_action


def test_run_research_session_keeps_review_pending_when_receipt_is_invalid(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_invalid_receipt",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    _write_spawned_reviewer_receipt(stage_dir)
    _write_yaml(
        stage_dir / "review" / "request" / "spawned_reviewer_receipt.yaml",
        {
            "review_cycle_id": _request_review_cycle_id(stage_dir),
            "launcher_owner": "qros-runtime-launcher",
            "launcher_session_id": "launcher-session",
            "launcher_thread_id": "leader-thread",
            "spawn_mode": "spawned_agent",
            "spawned_agent_id": "reviewer-child-agent",
            "fork_context": True,
            "write_root": "review/result",
            "handoff_manifest_path": "review/request/spawned_reviewer_handoff_manifest.yaml",
            "handoff_manifest_digest": _review_request_payload(stage_dir)["handoff_manifest_digest"],
            "requested_reviewer_identity": "reviewer-agent",
            "requested_reviewer_session_id": "reviewer-session",
            "receipt_written_at": "2026-04-17T03:00:00Z",
        },
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_invalid_receipt")

    assert status.current_stage == "test_evidence_review"
    assert status.stage_status == "awaiting_adversarial_review"
    assert status.blocking_reason_code == "ADVERSARIAL_REVIEW_PENDING"
    assert "proof chain is invalid" in (status.blocking_reason or "")
    assert "spawned_reviewer_receipt.yaml" in status.next_action


def test_run_stage_review_rejects_missing_spawned_reviewer_receipt(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
        write_audit=False,
    )

    with pytest.raises(ValueError, match="spawned_reviewer_receipt"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_rejects_reviewer_binding_mismatch(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_spawned_reviewer_receipt(
        stage_dir,
        reviewer_identity="other-reviewer",
        reviewer_session_id="other-session",
    )
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
        write_audit=False,
    )

    with pytest.raises(ValueError, match="spawned_reviewer_receipt"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_rejects_missing_spawned_agent_id(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_spawned_reviewer_receipt(stage_dir)
    _write_yaml(
        stage_dir / "review" / "request" / "spawned_reviewer_receipt.yaml",
        {
            "review_cycle_id": _request_review_cycle_id(stage_dir),
            "launcher_owner": "qros-runtime-launcher",
            "launcher_session_id": "launcher-session",
            "launcher_thread_id": "leader-thread",
            "spawn_mode": "spawned_agent",
            "fork_context": False,
            "write_root": "review/result",
            "handoff_manifest_path": "review/request/spawned_reviewer_handoff_manifest.yaml",
            "handoff_manifest_digest": _review_request_payload(stage_dir)["handoff_manifest_digest"],
            "requested_reviewer_identity": "reviewer-agent",
            "requested_reviewer_session_id": "reviewer-session",
            "receipt_written_at": "2026-04-17T03:00:00Z",
        },
    )
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
        write_audit=False,
    )

    with pytest.raises(ValueError, match="spawned_agent_id"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_rejects_missing_reviewer_write_scope_audit(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_spawned_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    (stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml").unlink()

    with pytest.raises(ValueError, match="reviewer_write_scope_audit"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )
