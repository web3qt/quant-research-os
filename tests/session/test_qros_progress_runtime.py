from __future__ import annotations

from dataclasses import replace
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

import runtime.tools.progress_runtime as progress_runtime_module
from runtime.tools.progress_runtime import ProgressError, latest_lineage_id, progress_status_payload
from runtime.tools.research_session import run_research_session
from runtime.tools.review_eligibility import ReviewEligibilityStatus
from tests.helpers.lineage_program_support import write_fake_stage_provenance
from tests.session.test_research_session_runtime import (
    _prepare_csf_train_freeze_closed_with_unreadable_route_and_legacy_mandate_request,
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request,
    _review_request_payload,
    _write_adversarial_review_request,
    _write_minimal_stage_outputs,
    _write_next_stage_confirmation,
    _write_reviewer_receipt,
    _write_yaml,
)


def _touch_lineage(outputs_root: Path, lineage_id: str, filename: str = "marker.txt") -> Path:
    lineage_root = outputs_root / lineage_id
    lineage_root.mkdir(parents=True)
    marker = lineage_root / filename
    marker.write_text(lineage_id + "\n", encoding="utf-8")
    return lineage_root


def _write_review_eligibility(lineage_root: Path, payload: dict) -> None:
    path = lineage_root / "review_eligibility.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_data_inventory(data_root: Path, *, data_min_ts: str, data_max_ts: str) -> Path:
    data_root.mkdir(parents=True, exist_ok=True)
    (data_root / "data_inventory.json").write_text(
        yaml.safe_dump(
            {
                "data_min_ts": data_min_ts,
                "data_max_ts": data_max_ts,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return data_root


def _write_failure_post_retry_decision(lineage_root: Path) -> None:
    package_dir = (
        lineage_root
        / "06_csf_backtest_ready"
        / "failure_packages"
        / "backtest_exec_fail_20260423T045312Z"
    )
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "post_retry_decision.yaml").write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "failed_stage": "csf_backtest_ready",
                "failure_class": "EXEC_FAIL",
                "retry_result": "hard_gate_still_failed",
                "recommended_next_decision": "NO_GO_OR_CHILD_LINEAGE_REQUIRED",
                "normal_progression_allowed": False,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _prepare_review_complete_mandate(outputs_root: Path, lineage_id: str) -> Path:
    stage_dir = outputs_root / lineage_id / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "mandate.md",
        "research_scope.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ):
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    (formal_dir / "research_route.yaml").write_text(
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
        encoding="utf-8",
    )
    (formal_dir / "time_split.json").write_text("{}\n", encoding="utf-8")
    (formal_dir / "parameter_grid.yaml").write_text("parameters: []\n", encoding="utf-8")
    (formal_dir / "run_config.toml").write_text("version = 1\n", encoding="utf-8")
    (formal_dir / "program_execution_manifest.json").write_text("{}\n", encoding="utf-8")
    for name in (
        "latest_review_pack.yaml",
        "stage_completion_certificate.yaml",
        "stage_gate_review.yaml",
    ):
        (stage_dir / "review" / "closure" / name).parent.mkdir(parents=True, exist_ok=True)
        (stage_dir / "review" / "closure" / name).write_text(
            "final_verdict: PASS\nstage_status: PASS\n",
            encoding="utf-8",
        )
    return stage_dir


def test_latest_lineage_id_selects_most_recent_existing_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _touch_lineage(outputs_root, "old_lineage")
    time.sleep(0.01)
    _touch_lineage(outputs_root, "new_lineage")

    assert latest_lineage_id(outputs_root) == "new_lineage"


def test_latest_lineage_id_does_not_create_outputs_root(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    try:
        latest_lineage_id(outputs_root)
    except ProgressError as exc:
        assert "No QROS outputs directory found" in str(exc)
    else:
        raise AssertionError("expected ProgressError")

    assert not outputs_root.exists()


def test_progress_status_payload_requires_existing_explicit_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    outputs_root.mkdir()

    try:
        progress_status_payload(outputs_root=outputs_root, lineage_id="missing")
    except ProgressError as exc:
        assert "QROS lineage not found" in str(exc)
    else:
        raise AssertionError("expected ProgressError")

    assert not (outputs_root / "missing").exists()


def test_progress_json_outputs_stable_status_fields_for_explicit_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "btc_leads_alts")
    (lineage_root / "00_idea_intake").mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "runtime/scripts/run_progress.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["lineage_id"] == "btc_leads_alts"
    assert payload["selection_mode"] == "explicit"
    assert payload["current_stage"] == "mandate_admission"
    assert "current_skill" in payload
    assert "gate_status" in payload
    assert "next_action" in payload
    assert payload["artifacts_written"] == []


def test_progress_cli_without_lineage_id_uses_latest_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _touch_lineage(outputs_root, "old_lineage")
    time.sleep(0.01)
    latest_root = _touch_lineage(outputs_root, "latest_lineage")
    (latest_root / "00_idea_intake").mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "runtime/scripts/run_progress.py",
            "--outputs-root",
            str(outputs_root),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "QROS Progress" in result.stdout
    assert "Lineage: latest_lineage (latest)" in result.stdout
    assert "Current stage: mandate_admission" in result.stdout


def test_qros_progress_wrapper_uses_current_repo_outputs(tmp_path: Path) -> None:
    project_root = tmp_path / "research_repo"
    outputs_root = project_root / "outputs"
    lineage_root = _touch_lineage(outputs_root, "btc_leads_alts")
    (lineage_root / "00_idea_intake").mkdir()

    result = subprocess.run(
        [
            "runtime/bin/qros-progress",
            "--cwd",
            str(project_root),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["lineage_id"] == "btc_leads_alts"
    assert payload["selection_mode"] == "latest"
    assert payload["current_stage"] == "mandate_admission"


def test_progress_payload_exposes_skill_first_direct_handoff(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _prepare_review_complete_mandate(outputs_root, "btc_alt")

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="btc_alt")

    assert payload["current_stage"] == "mandate_next_stage_confirmation_pending"
    assert payload["current_skill"] == "qros-research-session"
    assert payload["recommended_skill"] == "qros-research-session"
    assert payload["handoff_hint"] == "Continue with qros-research-session."
    assert payload["next_action"] == "Continue with qros-research-session."
    assert payload["resume_hint"] == "Continue with qros-research-session."
    assert "qros-session" not in payload["handoff_hint"]
    assert "qros-resume" not in payload["handoff_hint"]
    assert "qros-session" not in payload["next_action"]
    assert "qros-resume" not in payload["next_action"]


def test_progress_reports_latest_csf_closed_stage_over_legacy_upstream_request(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_legacy_upstream_case"
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request(lineage_root)

    payload = progress_status_payload(
        outputs_root=outputs_root,
        lineage_id=lineage_root.name,
    )

    assert payload["current_stage"] == "csf_train_freeze_next_stage_confirmation_pending"
    assert payload["current_skill"] == "qros-research-session"
    assert payload["recommended_skill"] == "qros-research-session"


def test_progress_infers_csf_route_from_materialized_downstream_stage_when_route_file_unreadable(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_unreadable_route_case"
    _prepare_csf_train_freeze_closed_with_unreadable_route_and_legacy_mandate_request(lineage_root)

    payload = progress_status_payload(
        outputs_root=outputs_root,
        lineage_id=lineage_root.name,
    )

    assert payload["current_stage"] == "csf_train_freeze_next_stage_confirmation_pending"
    assert payload["current_skill"] == "qros-research-session"


def test_progress_infers_csf_route_from_materialized_downstream_stage_when_route_file_permission_denied(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_permission_denied_route_case"
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request(lineage_root)
    route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
    route_path.chmod(0)

    try:
        payload = progress_status_payload(
            outputs_root=outputs_root,
            lineage_id=lineage_root.name,
        )

        assert payload["current_stage"] == "csf_train_freeze_next_stage_confirmation_pending"
    finally:
        route_path.chmod(0o644)


def test_progress_reports_csf_test_evidence_after_train_next_stage_confirmation(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_legacy_upstream_case"
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request(lineage_root)
    _write_next_stage_confirmation(
        lineage_root / "04_csf_train_freeze",
        stage="csf_train_freeze",
    )

    payload = progress_status_payload(
        outputs_root=outputs_root,
        lineage_id=lineage_root.name,
    )

    assert payload["current_stage"] == "csf_test_evidence_confirmation_pending"
    assert payload["current_skill"] == "qros-csf-test-evidence-author"


def test_progress_reports_same_review_scope_mismatch_as_session(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    request_payload = _review_request_payload(stage_dir)
    _write_yaml(
        stage_dir / "review" / "final_review.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "reviewer_identity": "reviewer-agent",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewed_artifact_paths": [],
            "reviewed_program_path": "program/mandate/run_stage.py",
            "reviewed_artifact_digest": request_payload["bound_author_materialization_digest"],
            "reviewed_program_digest": request_payload["author_program_hash"],
            "verdict": "PASS",
            "review_summary": "scope mismatch fixture",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "rollback_stage": None,
            "downstream_permissions": [],
            "recommended_next_action": "rewrite final review",
        },
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)
    session_status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert payload["blocking_reason_code"] == session_status.blocking_reason_code == "REVIEW_SCOPE_MISMATCH"
    assert payload["stage_status"] == session_status.stage_status == "review_scope_mismatch"


@pytest.mark.parametrize(
    "protected_code",
    sorted(progress_runtime_module.PROTECTED_REVIEW_BLOCKING_REASON_CODES),
)
def test_progress_preserves_built_review_operation_code_before_eligibility_override(
    protected_code: str,
    tmp_path: Path,
    monkeypatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "built_scope_mismatch_case")
    (lineage_root / "01_mandate").mkdir(parents=True)
    monkeypatch.setattr(
        "runtime.tools.progress_runtime.detect_session_stage",
        lambda root: "mandate_review_confirmation_pending",
    )

    eligibility_called = False
    original_summarize = progress_runtime_module.summarize_session_status

    def summarize_with_candidate_review_operation(**kwargs):
        status = original_summarize(**kwargs)
        if eligibility_called:
            return status
        return replace(
            status,
            stage_status=protected_code.lower(),
            blocking_reason_code=protected_code,
            blocking_reason="reviewed_artifact_paths do not match active request scope",
            next_action="Rewrite review/final_review.yaml against the active request.",
        )

    def ineligible_author_output_blocker(**kwargs) -> ReviewEligibilityStatus:
        nonlocal eligibility_called
        eligibility_called = True
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="AUTHOR_OUTPUTS_INVALID",
            blocking_reason="Author outputs must be repaired before review entry.",
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=False,
            failure_stage=None,
            failure_reason_summary=None,
        )

    monkeypatch.setattr(
        progress_runtime_module,
        "summarize_session_status",
        summarize_with_candidate_review_operation,
    )
    monkeypatch.setattr(
        progress_runtime_module,
        "compute_review_eligibility",
        ineligible_author_output_blocker,
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert eligibility_called is False
    assert payload["current_stage"] == "mandate_review_confirmation_pending"
    assert payload["blocking_reason_code"] == protected_code
    assert payload["stage_status"] == protected_code.lower()


def test_progress_status_payload_surfaces_failure_disposition_gate(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "btc_alt_k")
    _write_failure_post_retry_decision(lineage_root)

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="btc_alt_k")

    assert payload["gate_status"] == "FAILURE_DISPOSITION_REQUIRED"
    assert payload["blocking_reason_code"] == "FAILURE_DISPOSITION_REQUIRED"
    assert payload["stage_status"] == "failure_disposition_required"
    assert payload["current_skill"] == "qros-stage-failure-handler"
    assert payload["requires_failure_handling"] is True
    assert payload["failure_stage"] == "csf_backtest_ready"
    assert "failure_disposition.yaml" in payload["next_action"]


def test_progress_does_not_recommend_review_skill_when_stage_is_not_review_eligible(
    tmp_path: Path,
    monkeypatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "blocked_case")
    _write_review_eligibility(
        lineage_root,
        {
            "failure_package": {
                "stage": "csf_test_evidence",
                "reason_code": "CSF_TEST_EVIDENCE_FAILURE_HANDLER_REQUIRED",
                "reason": "Canonical review eligibility blocked review entry for csf_test_evidence.",
                "failure_reason_summary": "Canonical review eligibility requires failure handling for csf_test_evidence.",
            }
        },
    )
    monkeypatch.setattr(
        "runtime.tools.progress_runtime.detect_session_stage",
        lambda root: "csf_test_evidence_review_confirmation_pending",
    )
    monkeypatch.setattr(
        "runtime.tools.progress_runtime.compute_review_eligibility",
        lambda **kwargs: ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="CSF_TEST_EVIDENCE_FAILURE_HANDLER_REQUIRED",
            blocking_reason="Canonical review eligibility blocked review entry for csf_test_evidence.",
            review_blocking_surface="failure_package",
            authorized_review_skill=None,
            requires_failure_handling=True,
            failure_stage="csf_test_evidence",
            failure_reason_summary="Canonical review eligibility requires failure handling for csf_test_evidence.",
        ),
        raising=False,
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="blocked_case")

    assert payload["current_stage"] == "csf_test_evidence_review_confirmation_pending"
    assert payload["stage_status"] == "blocked_requires_failure_handling"
    assert payload["gate_status"] == "FAILURE_HANDLING_REQUIRED"
    assert payload["current_skill"] == "qros-stage-failure-handler"
    assert payload["recommended_skill"] == "qros-stage-failure-handler"
    assert payload["blocking_reason_code"] == "CSF_TEST_EVIDENCE_FAILURE_HANDLER_REQUIRED"
    assert payload["requires_failure_handling"] is True
    assert payload["failure_stage"] == "csf_test_evidence"
    assert payload["failure_reason_summary"] == (
        "Canonical review eligibility requires failure handling for csf_test_evidence."
    )


def test_progress_non_failure_review_blocker_preserves_author_fix_skill_handoff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "preflight_blocked_case")
    _write_review_eligibility(
        lineage_root,
        {
            "semantic_gate": {
                "status": "pass",
            }
        },
    )
    monkeypatch.setattr(
        "runtime.tools.progress_runtime.detect_session_stage",
        lambda root: "csf_test_evidence_review_confirmation_pending",
    )
    summarize_call_count = 0
    original_summarize = progress_runtime_module.summarize_session_status

    def count_summarize_calls(**kwargs):
        nonlocal summarize_call_count
        summarize_call_count += 1
        return original_summarize(**kwargs)

    monkeypatch.setattr(
        progress_runtime_module,
        "summarize_session_status",
        count_summarize_calls,
    )
    monkeypatch.setattr(
        "runtime.tools.progress_runtime.compute_review_eligibility",
        lambda **kwargs: ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="AUTHOR_OUTPUTS_INVALID",
            blocking_reason="Author outputs must be repaired before review entry.",
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=False,
            failure_stage=None,
            failure_reason_summary=None,
        ),
        raising=False,
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="preflight_blocked_case")

    assert payload["current_stage"] == "csf_test_evidence_review_confirmation_pending"
    assert payload["stage_status"] == "awaiting_author_fix"
    assert payload["gate_status"] == "OUTPUTS_INVALID"
    assert payload["current_skill"] == "qros-csf-test-evidence-author"
    assert payload["recommended_skill"] == "qros-csf-test-evidence-author"
    assert payload["blocking_reason_code"] == "OUTPUTS_INVALID"
    assert payload["blocking_reason"] == "Author outputs must be repaired before review entry."
    assert payload["requires_failure_handling"] is False
    assert summarize_call_count == 1


def test_progress_real_review_eligibility_failure_handler_normalizes_failure_stage_name(
    tmp_path: Path,
    monkeypatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "real_helper_blocked_case")
    _write_review_eligibility(
        lineage_root,
        {
            "failure_package": {
                "stage": "csf_test_evidence_review_confirmation_pending",
                "reason_code": "CSF_TEST_EVIDENCE_FAILURE_HANDLER_REQUIRED",
                "reason": "Canonical review eligibility blocked review entry for csf_test_evidence.",
                "failure_reason_summary": "Canonical review eligibility requires failure handling for csf_test_evidence.",
            }
        },
    )
    monkeypatch.setattr(
        "runtime.tools.progress_runtime.detect_session_stage",
        lambda root: "csf_test_evidence_review_confirmation_pending",
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="real_helper_blocked_case")

    assert payload["current_stage"] == "csf_test_evidence_review_confirmation_pending"
    assert payload["stage_status"] == "blocked_requires_failure_handling"
    assert payload["gate_status"] == "FAILURE_HANDLING_REQUIRED"
    assert payload["failure_stage"] == "csf_test_evidence"
    assert payload["next_action"] == (
        "Enter failure handling for csf_test_evidence via qros-stage-failure-handler"
    )


def test_progress_blocked_mandate_review_stays_in_author_fix_lane(
    tmp_path: Path,
    monkeypatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "blocked_mandate_case")
    _write_review_eligibility(
        lineage_root,
        {
            "failure_package": {
                "stage": "mandate",
                "reason_code": "MANDATE_REVIEW_BLOCKED",
                "reason": "Canonical review eligibility blocked mandate review entry.",
                "failure_reason_summary": "Canonical review eligibility blocked mandate review entry.",
            }
        },
    )
    monkeypatch.setattr(
        "runtime.tools.progress_runtime.detect_session_stage",
        lambda root: "mandate_review_confirmation_pending",
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="blocked_mandate_case")

    assert payload["current_stage"] == "mandate_review_confirmation_pending"
    assert payload["stage_status"] == "awaiting_author_fix"
    assert payload["gate_status"] == "OUTPUTS_INVALID"
    assert payload["current_skill"] == "qros-mandate-author"
    assert payload["recommended_skill"] == "qros-mandate-author"
    assert payload["blocking_reason_code"] == "OUTPUTS_INVALID"
    assert payload["blocking_reason"] == "Canonical review eligibility blocked mandate review entry."
    assert payload["requires_failure_handling"] is False
    assert payload["failure_stage"] is None
    assert payload["failure_reason_summary"] is None


def test_progress_mandate_preflight_failure_keeps_outputs_invalid_when_review_eligibility_is_absent(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "preflight_priority_case")
    mandate_dir = lineage_root / "01_mandate" / "author" / "formal"
    mandate_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ):
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")
    (mandate_dir / "research_route.yaml").write_text(
        yaml.safe_dump(
            {
                "research_route": "time_series_signal",
                "excluded_routes": ["cross_sectional_factor"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (mandate_dir / "time_split.json").write_text(
        json.dumps(
            {
                "train": "",
                "test": "",
                "backtest": "",
                "holdout": "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (mandate_dir / "parameter_grid.yaml").write_text(
        yaml.safe_dump({"parameters": []}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    write_fake_stage_provenance(lineage_root, "mandate")

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="preflight_priority_case")

    assert payload["current_stage"] == "mandate_review_confirmation_pending"
    assert payload["stage_status"] == "awaiting_author_fix"
    assert payload["gate_status"] == "OUTPUTS_INVALID"
    assert payload["current_skill"] == "qros-mandate-author"
    assert payload["blocking_reason_code"] == "OUTPUTS_INVALID"
    assert "time_split.json" in (payload["blocking_reason"] or "")


def test_qros_progress_projects_data_viability_blocker_without_saying_review_ready(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "coverage_blocked_case")
    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    draft_dir.mkdir(parents=True, exist_ok=True)
    inventory_root = _write_data_inventory(
        tmp_path / "inventory",
        data_min_ts="2024-03-01",
        data_max_ts="2024-12-31",
    )
    (draft_dir / "mandate_admission.yaml").write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "raw_idea": "BTC leads ALTs",
                "observation": "BTC shocks precede ALT reactions.",
                "primary_hypothesis": "BTC leads price discovery.",
                "counter_hypothesis": "Moves are shared beta.",
                "research_questions": ["Do ALTs follow BTC after shocks?"],
                "scope": {
                    "market": "binance perp",
                    "instrument_type": "perpetual",
                    "universe": "high liquidity alts",
                    "data_source": "binance um futures klines",
                    "bar_size": "5m",
                    "holding_horizons": ["15m", "30m"],
                    "target_task": "event-driven relative return study",
                    "excluded_scope": ["low liquidity tails"],
                    "budget_days": 5,
                    "max_iterations": 3,
                },
                "qualification": {
                    "summary": "Researchable.",
                    "dimensions": {
                        name: {
                            "score": 3,
                            "evidence": ["present"],
                            "uncertainty": [],
                            "kill_reason": [],
                        }
                        for name in (
                            "observability",
                            "mechanism_plausibility",
                            "tradeability",
                            "data_feasibility",
                            "scoping_clarity",
                            "distinctiveness",
                        )
                    },
                },
                "route_assessment": {
                    "candidate_routes": ["time_series_signal", "cross_sectional_factor"],
                    "recommended_route": "time_series_signal",
                    "why_recommended": ["Single-asset direction is the main expression."],
                    "why_not_other_routes": {
                        "cross_sectional_factor": ["Cross-asset sorting is secondary."]
                    },
                    "route_risks": ["Universe breadth may be limited."],
                    "route_decision_pending": False,
                },
                "admission_decision": {
                    "verdict": "ACCEPT_FOR_MANDATE",
                    "why": ["Scope is concrete."],
                    "kill_criteria": ["No edge after costs."],
                    "required_reframe_actions": [],
                },
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (draft_dir / "mandate_freeze_draft.yaml").write_text(
        yaml.safe_dump(
            {
                "groups": {
                    "research_intent": {
                        "confirmed": False,
                        "draft": {
                            "research_question": "q",
                            "research_route": "time_series_signal",
                            "excluded_routes": ["cross_sectional_factor"],
                            "route_rationale": [
                                "Single-asset direction is the primary expression."
                            ],
                        },
                    },
                    "scope_contract": {
                        "confirmed": False,
                        "draft": {
                            "market": "binance perp",
                            "time_boundary": "2023-01-01/2026-03-01",
                        },
                    },
                    "data_contract": {
                        "confirmed": False,
                        "draft": {
                            "data_source": str(inventory_root),
                            "bar_size": "5m",
                        },
                    },
                    "execution_contract": {
                        "confirmed": False,
                        "draft": {"time_split_note": "frozen"},
                    },
                }
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="coverage_blocked_case")

    assert payload["current_stage"] == "mandate_freeze_confirmation_pending"
    assert payload["stage_status"] == "awaiting_author_fix"
    assert payload["gate_status"] == "OUTPUTS_INVALID"
    assert payload["blocking_reason_code"] == "TIME_COVERAGE_OUT_OF_RANGE"
    assert payload["current_skill"] == "qros-research-session"
    assert "Adjust train/test/backtest/holdout" in payload["next_action"]
    assert "review-ready" not in payload["next_action"].lower()
