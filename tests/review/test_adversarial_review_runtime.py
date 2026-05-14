import json
from pathlib import Path

import pytest
import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from tests.helpers.lineage_program_support import STAGE_PROGRAM_SPECS, ensure_stage_program, write_fake_stage_provenance
from tests.session.test_research_session_runtime import _write_minimal_stage_outputs, _write_stage_completion_certificate
from runtime.tools.research_session import _program_spec_for_session_stage, run_research_session
from runtime.tools.review_skillgen.adversarial_review_contract import (
    ensure_adversarial_review_request,
    issue_reviewer_receipt,
    load_adversarial_review_request,
    load_reviewer_handoff_manifest,
    load_reviewer_receipt,
    validate_receipt_contract,
)
from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff
from runtime.tools.review_skillgen.review_engine import run_stage_review
from runtime.tools.review_skillgen.review_cycle_trace import load_review_cycle_trace
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest,
    write_review_runtime_state,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    run_reviewer_write_scope_audit,
    write_reviewer_write_scope_baseline,
)
from runtime.tools.tss_test_evidence_runtime import build_tss_test_evidence_from_train_freeze
from tests.runtime.test_tss_test_evidence_runtime import (
    _prepare_tss_train_freeze_stage,
    _tss_test_evidence_draft,
)


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
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_stage(tmp_path: Path) -> tuple[Path, Path]:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    (stage_dir / "author" / "formal").mkdir(parents=True)
    (stage_dir / "review" / "request").mkdir(parents=True)
    (stage_dir / "review" / "result").mkdir(parents=True)

    for name in MANDATE_REQUIRED_OUTPUTS:
        (stage_dir / "author" / "formal" / name).write_text("ok\n", encoding="utf-8")
    (stage_dir / "author" / "formal" / "time_split.json").write_text(
        json.dumps(
            {
                "train": "2024-01-01/2024-03-31",
                "test": "2024-04-01/2024-06-30",
                "backtest": "2024-07-01/2024-09-30",
                "holdout": "2024-10-01/2024-12-31",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_yaml(
        stage_dir / "author" / "formal" / "parameter_grid.yaml",
        {
            "parameters": [
                {
                    "param_id": "shock_threshold_bp",
                    "values": [30, 50],
                }
            ]
        },
    )

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


def _receipt_canonical_context(stage_dir: Path) -> dict[str, str]:
    request_payload = _review_request_payload(stage_dir)
    return {
        "project_root": request_payload["project_root"],
        "lineage_root": request_payload["lineage_root"],
        "stage_dir": request_payload["stage_dir"],
    }


def _write_reviewer_receipt(
    stage_dir: Path,
    *,
    reviewer_identity: str = "reviewer-agent",
    reviewer_session_id: str = "reviewer-session",
    reviewer_agent_id: str = "reviewer-child-agent",
) -> None:
    receipt = issue_reviewer_receipt(
        stage_dir,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id="launcher-session",
        launcher_thread_id="leader-thread",
        reviewer_agent_id=reviewer_agent_id,
    )
    request_payload = _review_request_payload(stage_dir)
    author_digest = compute_author_materialization_digest(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=request_payload["required_artifact_paths"],
        required_provenance_paths=request_payload["required_provenance_paths"],
    )
    write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id=request_payload["review_cycle_id"],
        review_requested_at=receipt["receipt_written_at"],
        review_bound_author_digest=author_digest,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
    )
    write_reviewer_write_scope_baseline(
        stage_dir,
        review_cycle_id=receipt["review_cycle_id"],
        launcher_thread_id=receipt["launcher_thread_id"],
        reviewer_agent_id=receipt["reviewer_agent_id"],
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
            "reviewed_project_root": request_payload["project_root"],
            "reviewed_lineage_root": request_payload["lineage_root"],
            "reviewed_stage_dir": request_payload["stage_dir"],
            "hard_gate_findings_acknowledged": True,
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


def _write_raw_reviewer_findings(
    stage_dir: Path,
    *,
    review_loop_outcome: str,
    reviewer_session_id: str = "reviewer-session",
    reviewer_agent_id: str = "reviewer-child-agent",
    reviewed_project_root: str | None = None,
    reviewed_lineage_root: str | None = None,
    reviewed_stage_dir: str | None = None,
    hard_gate_findings_acknowledged: bool = True,
    blocking_findings: list[str] | None = None,
    reservation_findings: list[str] | None = None,
    info_findings: list[str] | None = None,
    residual_risks: list[str] | None = None,
    allowed_modifications: list[str] | None = None,
    downstream_permissions: list[str] | None = None,
    rollback_stage: str | None = None,
) -> None:
    request_payload = _review_request_payload(stage_dir)
    payload = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "reviewer_session_id": reviewer_session_id,
        "reviewer_agent_id": reviewer_agent_id,
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "reviewed_project_root": reviewed_project_root or request_payload["project_root"],
        "reviewed_lineage_root": reviewed_lineage_root or request_payload["lineage_root"],
        "reviewed_stage_dir": reviewed_stage_dir or request_payload["stage_dir"],
        "hard_gate_findings_acknowledged": hard_gate_findings_acknowledged,
        "review_loop_outcome": review_loop_outcome,
        "blocking_findings": blocking_findings or [],
        "reservation_findings": reservation_findings or [],
        "info_findings": info_findings or [],
        "residual_risks": residual_risks or [],
        "allowed_modifications": allowed_modifications or [],
        "downstream_permissions": downstream_permissions or [],
    }
    if rollback_stage:
        payload["rollback_stage"] = rollback_stage
    _write_yaml(stage_dir / "review" / "result" / "reviewer_findings.raw.yaml", payload)


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
    _write_reviewer_receipt(stage_dir, reviewer_identity="author-agent")
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
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
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="FIX_REQUIRED",
        blocking_findings=["Need stronger provenance linkage."],
        rollback_stage="mandate",
        allowed_modifications=["artifact corrections only"],
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


def test_run_stage_review_rejects_raw_reviewer_findings_from_launcher_session(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
        reviewer_session_id="launcher-session",
    )

    with pytest.raises(ValueError, match="REVIEWER_IDENTITY_COLLISION"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_rejects_raw_reviewer_findings_session_mismatch(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
        reviewer_session_id="other-reviewer-session",
    )

    with pytest.raises(ValueError, match="REVIEWER_IDENTITY_COLLISION"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_rejects_raw_reviewer_findings_lineage_root_mismatch(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
        reviewed_lineage_root=str((lineage_root.parent / "other_lineage").resolve()),
    )

    with pytest.raises(ValueError, match="REVIEW_CONTEXT_ROOT_MISMATCH"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_ensure_adversarial_review_request_freezes_launcher_review_ready_metadata(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")

    request_payload = _review_request_payload(stage_dir)
    trace_events = load_review_cycle_trace(stage_dir / "review" / "review_cycle_trace.jsonl")

    assert request_payload["launcher_review_ready_status"] == "complete"
    assert sorted(request_payload["launcher_checked_artifact_paths"]) == sorted(request_payload["required_artifact_paths"])
    assert sorted(request_payload["launcher_checked_provenance_paths"]) == sorted(
        request_payload["required_provenance_paths"]
    )
    assert request_payload["launcher_handoff_context_paths"] == ["artifact_catalog.md", "field_dictionary.md"]
    assert request_payload["stage_content_artifact_paths"] == request_payload["required_artifact_paths"]
    assert request_payload["stage_content_provenance_paths"] == request_payload["required_provenance_paths"]
    assert request_payload["upstream_binding_artifact_paths"] == []
    assert trace_events[0]["event_type"] == "request_issued"
    assert trace_events[0]["author_identity"] == "author-agent"


def test_review_cycle_binds_request_receipt_and_handoff_to_canonical_context(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    payload = prepare_review_cycle_for_handoff(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="reviewer-agent",
        reviewer_session_id="reviewer-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child-agent",
    )

    request_payload = load_adversarial_review_request(
        stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    )
    manifest_payload = load_reviewer_handoff_manifest(
        stage_dir / "review" / "request" / "reviewer_handoff_manifest.yaml"
    )
    receipt_payload = load_reviewer_receipt(stage_dir / "review" / "request" / "reviewer_receipt.yaml")
    expected_context = {
        "project_root": str(tmp_path.resolve()),
        "lineage_root": str(lineage_root.resolve()),
        "stage_dir": str(stage_dir.resolve()),
        "author_formal_dir": str((stage_dir / "author" / "formal").resolve()),
        "review_request_dir": str((stage_dir / "review" / "request").resolve()),
        "review_result_dir": str((stage_dir / "review" / "result").resolve()),
    }

    for key, expected_value in expected_context.items():
        assert request_payload[key] == expected_value
        assert manifest_payload[key] == expected_value
    for key in ("project_root", "lineage_root", "stage_dir"):
        assert receipt_payload[key] == request_payload[key]

    handoff_prompt = payload["reviewer_handoff_prompt"]
    assert "Launcher boundary:" in handoff_prompt
    assert "The current/main conversation is the launcher, not the reviewer." in handoff_prompt
    assert "Do not write reviewer_findings.raw.yaml from the launcher conversation." in handoff_prompt
    assert "Send this handoff to an independent reviewer/subagent." in handoff_prompt
    assert f"Active research repo root: {expected_context['project_root']}" in handoff_prompt
    assert f"Lineage root: {expected_context['lineage_root']}" in handoff_prompt
    assert f"Stage dir: {expected_context['stage_dir']}" in handoff_prompt
    assert (
        "The QROS governance repo is not the active research repo unless the canonical paths above point there."
        in handoff_prompt
    )

    mismatched_receipt = dict(receipt_payload)
    mismatched_receipt["stage_dir"] = str((tmp_path / "outputs" / "other_lineage" / "01_mandate").resolve())
    with pytest.raises(ValueError, match="stage_dir"):
        validate_receipt_contract(request_payload=request_payload, receipt_payload=mismatched_receipt)


def test_issue_reviewer_receipt_refreshes_legacy_receipt_with_canonical_context(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    request_payload = _review_request_payload(stage_dir)
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    legacy_receipt = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "host": "codex",
        "launcher_owner": "qros-runtime-launcher",
        "launcher_session_id": "launcher-session",
        "launcher_thread_id": "launcher-thread",
        "execution_mode": "spawned_agent",
        "reviewer_invocation_kind": "codex_spawn_agent",
        "context_isolation_policy": "fork_context_false",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_delivery_method": "send_input",
        "reviewer_agent_id": "reviewer-child-agent",
        "write_root": "review/result",
        "handoff_manifest_path": request_payload["handoff_manifest_path"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "reviewer-session",
        "receipt_written_at": "2026-04-17T03:00:00Z",
    }
    receipt_path.write_text(yaml.safe_dump(legacy_receipt, sort_keys=False, allow_unicode=True), encoding="utf-8")

    returned_payload = issue_reviewer_receipt(
        stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="reviewer-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child-agent",
    )
    file_payload = load_reviewer_receipt(receipt_path)

    for key in ("project_root", "lineage_root", "stage_dir"):
        assert returned_payload[key] == request_payload[key]
        assert file_payload[key] == request_payload[key]


def test_issue_reviewer_receipt_rejects_invalid_receipt_from_different_cycle(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    receipt_path.write_text(
        yaml.safe_dump(
            {
                "review_cycle_id": "different-review-cycle",
                "requested_reviewer_identity": "reviewer-agent",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        issue_reviewer_receipt(
            stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_session_id="reviewer-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
        )


def test_issue_reviewer_receipt_rejects_valid_receipt_from_different_cycle_without_overwrite(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    request_payload = _review_request_payload(stage_dir)
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    existing_receipt = {
        "review_cycle_id": "different-review-cycle",
        **_receipt_canonical_context(stage_dir),
        "host": "codex",
        "launcher_owner": "qros-runtime-launcher",
        "launcher_session_id": "launcher-session",
        "launcher_thread_id": "launcher-thread",
        "execution_mode": "spawned_agent",
        "reviewer_invocation_kind": "codex_spawn_agent",
        "context_isolation_policy": "fork_context_false",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_delivery_method": "send_input",
        "reviewer_agent_id": "reviewer-child-agent",
        "write_root": "review/result",
        "handoff_manifest_path": request_payload["handoff_manifest_path"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "reviewer-session",
        "receipt_written_at": "2026-04-17T03:00:00Z",
    }
    receipt_text = yaml.safe_dump(existing_receipt, sort_keys=False, allow_unicode=True)
    receipt_path.write_text(receipt_text, encoding="utf-8")

    assert load_reviewer_receipt(receipt_path)["review_cycle_id"] == "different-review-cycle"
    with pytest.raises(ValueError, match="review_cycle_id"):
        issue_reviewer_receipt(
            stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_session_id="reviewer-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
        )

    assert receipt_path.read_text(encoding="utf-8") == receipt_text


def test_issue_reviewer_receipt_rejects_same_cycle_receipt_with_mismatched_context_without_overwrite(
    tmp_path: Path,
) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    request_payload = _review_request_payload(stage_dir)
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    existing_receipt = {
        "review_cycle_id": request_payload["review_cycle_id"],
        **_receipt_canonical_context(stage_dir),
        "host": "codex",
        "launcher_owner": "qros-runtime-launcher",
        "launcher_session_id": "launcher-session",
        "launcher_thread_id": "launcher-thread",
        "execution_mode": "spawned_agent",
        "reviewer_invocation_kind": "codex_spawn_agent",
        "context_isolation_policy": "fork_context_false",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_delivery_method": "send_input",
        "reviewer_agent_id": "reviewer-child-agent",
        "write_root": "review/result",
        "handoff_manifest_path": request_payload["handoff_manifest_path"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "reviewer-session",
        "receipt_written_at": "2026-04-17T03:00:00Z",
    }
    existing_receipt["stage_dir"] = str((tmp_path / "outputs" / "other_lineage" / "01_mandate").resolve())
    receipt_text = yaml.safe_dump(existing_receipt, sort_keys=False, allow_unicode=True)
    receipt_path.write_text(receipt_text, encoding="utf-8")

    assert load_reviewer_receipt(receipt_path)["stage_dir"] == existing_receipt["stage_dir"]
    with pytest.raises(ValueError, match="stage_dir"):
        issue_reviewer_receipt(
            stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_session_id="reviewer-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
        )

    assert receipt_path.read_text(encoding="utf-8") == receipt_text


def test_issue_reviewer_receipt_rejects_invalid_same_cycle_receipt_with_mismatched_context_without_overwrite(
    tmp_path: Path,
) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    request_payload = _review_request_payload(stage_dir)
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    existing_receipt = {
        "review_cycle_id": request_payload["review_cycle_id"],
        **_receipt_canonical_context(stage_dir),
        "host": "codex",
        "launcher_owner": "qros-runtime-launcher",
        "launcher_session_id": "launcher-session",
        "launcher_thread_id": "launcher-thread",
        "execution_mode": "spawned_agent",
        "reviewer_invocation_kind": "codex_spawn_agent",
        "context_isolation_policy": "fork_context_false",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_delivery_method": "send_input",
        "reviewer_agent_id": "",
        "write_root": "review/result",
        "handoff_manifest_path": request_payload["handoff_manifest_path"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "reviewer-session",
        "receipt_written_at": "2026-04-17T03:00:00Z",
    }
    existing_receipt["stage_dir"] = str((tmp_path / "outputs" / "other_lineage" / "01_mandate").resolve())
    receipt_text = yaml.safe_dump(existing_receipt, sort_keys=False, allow_unicode=True)
    receipt_path.write_text(receipt_text, encoding="utf-8")

    with pytest.raises(ValueError):
        issue_reviewer_receipt(
            stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_session_id="reviewer-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
        )

    assert receipt_path.read_text(encoding="utf-8") == receipt_text


def test_issue_reviewer_receipt_rejects_invalid_same_cycle_receipt_when_canonical_context_is_complete(
    tmp_path: Path,
) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    request_payload = _review_request_payload(stage_dir)
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    existing_receipt = {
        "review_cycle_id": request_payload["review_cycle_id"],
        **_receipt_canonical_context(stage_dir),
        "host": "codex",
        "launcher_owner": "qros-runtime-launcher",
        "launcher_session_id": "launcher-session",
        "launcher_thread_id": "launcher-thread",
        "execution_mode": "spawned_agent",
        "reviewer_invocation_kind": "codex_spawn_agent",
        "context_isolation_policy": "fork_context_false",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_delivery_method": "send_input",
        "reviewer_agent_id": "",
        "write_root": "review/result",
        "handoff_manifest_path": request_payload["handoff_manifest_path"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "reviewer-session",
        "receipt_written_at": "2026-04-17T03:00:00Z",
    }
    receipt_text = yaml.safe_dump(existing_receipt, sort_keys=False, allow_unicode=True)
    receipt_path.write_text(receipt_text, encoding="utf-8")

    with pytest.raises(ValueError):
        issue_reviewer_receipt(
            stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_session_id="reviewer-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
        )

    assert receipt_path.read_text(encoding="utf-8") == receipt_text


def test_issue_reviewer_receipt_rejects_legacy_receipt_with_non_context_corruption_without_overwrite(
    tmp_path: Path,
) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    request_payload = _review_request_payload(stage_dir)
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    legacy_receipt = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "host": "codex",
        "launcher_owner": "qros-runtime-launcher",
        "launcher_session_id": "launcher-session",
        "launcher_thread_id": "launcher-thread",
        "execution_mode": "spawned_agent",
        "reviewer_invocation_kind": "codex_spawn_agent",
        "context_isolation_policy": "fork_context_false",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_delivery_method": "send_input",
        "reviewer_agent_id": "",
        "write_root": "review/result",
        "handoff_manifest_path": request_payload["handoff_manifest_path"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "reviewer-session",
        "receipt_written_at": "2026-04-17T03:00:00Z",
    }
    receipt_text = yaml.safe_dump(legacy_receipt, sort_keys=False, allow_unicode=True)
    receipt_path.write_text(receipt_text, encoding="utf-8")

    with pytest.raises(ValueError):
        issue_reviewer_receipt(
            stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_session_id="reviewer-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
        )

    assert receipt_path.read_text(encoding="utf-8") == receipt_text


def test_ensure_adversarial_review_request_splits_signal_ready_stage_content_and_binding_scope(tmp_path: Path) -> None:
    _, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="signal_scope_case",
        stage_key="csf_signal_ready",
        stage_dir_name="03_csf_signal_ready",
    )
    _write_adversarial_review_request(stage_dir, stage_key="csf_signal_ready", author_identity="author-agent")

    request_payload = _review_request_payload(stage_dir)

    assert "route_inheritance_contract.yaml" in request_payload["required_artifact_paths"]
    assert "route_inheritance_contract.yaml" not in request_payload["stage_content_artifact_paths"]
    assert request_payload["upstream_binding_artifact_paths"] == ["route_inheritance_contract.yaml"]
    assert request_payload["stage_content_provenance_paths"] == ["program_execution_manifest.json"]
    assert request_payload["upstream_binding_provenance_paths"] == []


def test_ensure_adversarial_review_request_includes_tss_test_evidence_proof_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_review_scope_case"
    _prepare_tss_train_freeze_stage(lineage_root)
    ensure_stage_program(lineage_root, "tss_test_evidence")
    write_fake_stage_provenance(lineage_root, "tss_test_evidence")
    stage_dir = lineage_root / "05_tss_test_evidence"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml",
        _tss_test_evidence_draft(confirmed=True),
    )
    build_tss_test_evidence_from_train_freeze(lineage_root)

    _write_adversarial_review_request(stage_dir, stage_key="tss_test_evidence", author_identity="author-agent")

    request_payload = _review_request_payload(stage_dir)
    proof_artifacts = {
        "split_threshold_attestation.yaml",
        "selected_variant_membership_proof.csv",
        "upstream_binding_digest_ledger.yaml",
    }
    assert proof_artifacts.issubset(set(request_payload["required_artifact_paths"]))
    assert request_payload["upstream_binding_artifact_paths"] == [
        "selected_variant_membership_proof.csv",
        "split_threshold_attestation.yaml",
        "upstream_binding_digest_ledger.yaml",
    ]


def test_run_stage_review_rejects_non_adversarial_reviewer_mode(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(
        stage_dir,
        stage_key="mandate",
        author_identity="author-agent",
    )
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
    )

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
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
    )

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
    assert result_payload["reviewed_project_root"] == request_payload["project_root"]
    assert result_payload["reviewed_lineage_root"] == request_payload["lineage_root"]
    assert result_payload["reviewed_stage_dir"] == request_payload["stage_dir"]
    assert result_payload["hard_gate_findings_acknowledged"] is True
    assert sorted(result_payload["reviewed_artifact_paths"]) == sorted(request_payload["required_artifact_paths"])


def test_run_stage_review_rejects_unexpected_result_file(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(
        stage_dir,
        stage_key="mandate",
        author_identity="author-agent",
    )
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    _write_yaml(
        stage_dir / "review" / "result" / "launcher_notes.yaml",
        {
            "notes": ["launcher-authored result drift"],
        },
    )

    with pytest.raises(ValueError, match="REVIEWER_WRITE_SCOPE_VIOLATION"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_rejects_unexpected_nested_result_file(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(
        stage_dir,
        stage_key="mandate",
        author_identity="author-agent",
    )
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    _write_yaml(
        stage_dir / "review" / "result" / "sidecar" / "launcher_notes.yaml",
        {
            "notes": ["launcher-authored nested result drift"],
        },
    )

    with pytest.raises(ValueError, match="REVIEWER_WRITE_SCOPE_VIOLATION"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


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
    assert "reviewer_receipt.yaml" in (status.blocking_reason or "")


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
    _write_reviewer_receipt(stage_dir)
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
    assert "review_findings.yaml" in status.next_action
    assert "fresh reviewer cycle" in status.next_action


def test_run_research_session_waits_for_reviewer_child_after_receipt(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_reviewer_wait_case",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    _write_reviewer_receipt(stage_dir, reviewer_agent_id="reviewer-child-agent")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_reviewer_wait_case")

    assert status.current_stage == "test_evidence_review"
    assert status.stage_status == "awaiting_reviewer_completion"
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
    _write_reviewer_receipt(stage_dir)
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
    assert "./.qros/bin/qros-review" in status.next_action


def test_run_research_session_rejects_result_file_added_after_pass_audit(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_review_stale_pass_audit",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    _write_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage_key="test_evidence",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    run_reviewer_write_scope_audit(stage_dir)
    _write_yaml(
        stage_dir / "review" / "result" / "sidecar" / "launcher_notes.yaml",
        {
            "notes": ["launcher-authored nested result drift after audit"],
        },
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_review_stale_pass_audit")

    assert status.current_stage == "test_evidence_review"
    assert status.stage_status == "awaiting_reviewer_write_scope_audit"
    assert status.blocking_reason_code == "REVIEW_AUDIT_FAILED"
    assert "REVIEWER_WRITE_SCOPE_VIOLATION" in (status.blocking_reason or "")


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
    assert "reviewer_receipt.yaml" in (status.blocking_reason or "")
    assert "reviewer_receipt.yaml" in status.next_action


def test_run_research_session_keeps_review_pending_when_receipt_is_invalid(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_invalid_receipt",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    _write_reviewer_receipt(stage_dir)
    _write_yaml(
        stage_dir / "review" / "request" / "reviewer_receipt.yaml",
        {
            "review_cycle_id": "bad-mismatched-cycle-id",
            **_receipt_canonical_context(stage_dir),
            "launcher_owner": "qros-runtime-launcher",
            "launcher_session_id": "launcher-session",
            "launcher_thread_id": "leader-thread",
            "host": "codex",
            "execution_mode": "spawned_agent",
            "reviewer_invocation_kind": "codex_spawn_agent",
            "context_isolation_policy": "fork_context_false",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "handoff_delivery_method": "send_input",
            "reviewer_agent_id": "reviewer-child-agent",
            "write_root": "review/result",
            "handoff_manifest_path": "review/request/reviewer_handoff_manifest.yaml",
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
    assert "reviewer_receipt.yaml" in status.next_action


def test_run_research_session_keeps_review_pending_when_request_handoff_is_invalid(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_invalid_review_handoff",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    request_payload = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    request_payload["launcher_checked_artifact_paths"] = []
    _write_yaml(request_path, request_payload)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_invalid_review_handoff")

    assert status.current_stage == "test_evidence_review"
    assert status.stage_status == "awaiting_adversarial_review"
    assert status.blocking_reason_code == "ADVERSARIAL_REVIEW_PENDING"
    assert "proof chain is invalid" in (status.blocking_reason or "")
    assert "launcher_checked_artifact_paths" in (status.blocking_reason or "")


def test_run_research_session_invalidates_stale_review_cycle_after_author_output_changes(tmp_path: Path) -> None:
    outputs_root, stage_dir = _prepare_review_runtime_case(
        tmp_path,
        lineage_id="btc_stale_review_cycle",
        stage_key="test_evidence",
        stage_dir_name="05_test_evidence",
    )
    _write_adversarial_review_request(stage_dir, stage_key="test_evidence")
    _write_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage_key="test_evidence",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")

    changed_output = stage_dir / "author" / "formal" / "test_gate_decision.md"
    changed_output.write_text("changed after review\n", encoding="utf-8")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_stale_review_cycle")

    assert status.current_stage == "test_evidence_review"
    assert status.stage_status == "blocked"
    assert status.gate_status == "PROTECTED_STATE_DRIFT"
    assert status.blocking_reason_code == "REVIEW_STATE_PROJECTION_DRIFT"
    assert "review_bound_author_digest" in (status.blocking_reason or "")
    assert "qros-review-cycle reset --archive-stale-cycle" in status.next_action


def test_run_stage_review_rejects_missing_reviewer_receipt(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
        write_audit=False,
    )

    with pytest.raises(ValueError, match="reviewer_receipt"):
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
    _write_reviewer_receipt(
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

    with pytest.raises(ValueError, match="reviewer_receipt"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_rejects_missing_reviewer_agent_id(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_reviewer_receipt(stage_dir)
    _write_yaml(
        stage_dir / "review" / "request" / "reviewer_receipt.yaml",
        {
            "review_cycle_id": _request_review_cycle_id(stage_dir),
            **_receipt_canonical_context(stage_dir),
            "launcher_owner": "qros-runtime-launcher",
            "launcher_session_id": "launcher-session",
            "launcher_thread_id": "leader-thread",
            "execution_mode": "spawned_agent",
            "host": "codex",
            "reviewer_invocation_kind": "codex_spawn_agent",
            "context_isolation_policy": "fork_context_false",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "handoff_delivery_method": "send_input",
            "write_root": "review/result",
            "handoff_manifest_path": "review/request/reviewer_handoff_manifest.yaml",
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

    with pytest.raises(ValueError, match="reviewer_agent_id"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="adversarial",
        )


def test_run_stage_review_recreates_missing_reviewer_write_scope_audit(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_reviewer_receipt(stage_dir)
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    (stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml").unlink(missing_ok=True)

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="adversarial-reviewer",
        reviewer_session_id="reviewer-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "PASS"
    assert (stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml").exists()
