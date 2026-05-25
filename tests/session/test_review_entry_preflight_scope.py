from pathlib import Path
import json

import pytest

from runtime.tools.research_session import (
    SESSION_STAGE_PROGRAM_SPECS,
    _review_entry_preflight_payload,
    detect_session_stage,
    run_research_session,
)
from tests.helpers.lineage_program_support import write_fake_stage_provenance


POST_MANDATE_REVIEW_CONFIRMATION_STAGES = (
    "data_ready_review_confirmation_pending",
    "signal_ready_review_confirmation_pending",
    "train_freeze_review_confirmation_pending",
    "test_evidence_review_confirmation_pending",
    "backtest_ready_review_confirmation_pending",
    "holdout_validation_review_confirmation_pending",
    "csf_data_ready_review_confirmation_pending",
    "csf_signal_ready_review_confirmation_pending",
    "csf_train_freeze_review_confirmation_pending",
    "csf_test_evidence_review_confirmation_pending",
    "csf_backtest_ready_review_confirmation_pending",
    "csf_holdout_validation_review_confirmation_pending",
)

CSF_SESSION_STAGE_KEYS = (
    "csf_data_ready",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
)


def test_csf_data_ready_gate_required_outputs_match_stage_spec() -> None:
    from runtime.tools.stage_evaluator import STAGE_EVALUATOR_SPECS
    from runtime.tools.review_skillgen.loaders import load_gate_schema
    from runtime.tools.review_skillgen.review_engine import GATES_PATH
    from runtime.tools.review_skillgen.review_scope import normalize_review_paths

    gates = load_gate_schema(GATES_PATH)
    gate_outputs = gates["stages"]["csf_data_ready"]["required_outputs"]
    spec_outputs = STAGE_EVALUATOR_SPECS["02_csf_data_ready"].required_outputs

    assert normalize_review_paths(gate_outputs) == normalize_review_paths(spec_outputs)


def _write_required_author_outputs(lineage_root: Path, current_stage: str) -> Path:
    spec = SESSION_STAGE_PROGRAM_SPECS[current_stage.removesuffix("_review_confirmation_pending")]
    author_formal_dir = lineage_root / spec.stage_dir_name / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    for output_name in spec.required_outputs:
        output_path = author_formal_dir / output_name
        if "." in Path(output_name).name:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("placeholder\n", encoding="utf-8")
        else:
            output_path.mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, current_stage.removesuffix("_review_confirmation_pending"))
    (lineage_root / "review_eligibility.json").write_text(
        json.dumps({"semantic_gate": {"status": "pass"}}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return author_formal_dir.parent.parent


def test_csf_session_stage_program_specs_use_canonical_stage_ids() -> None:
    for stage_key in CSF_SESSION_STAGE_KEYS:
        assert SESSION_STAGE_PROGRAM_SPECS[stage_key].stage_id == stage_key


def test_review_entry_preflight_runs_for_mandate_review_confirmation_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    current_stage = "mandate_review_confirmation_pending"
    stage_dir = _write_required_author_outputs(lineage_root, current_stage)
    captured_stage_dirs: list[Path] = []

    def _fake_run_review_preflight(*, explicit_context: dict[str, object]) -> dict[str, object]:
        captured_stage_dirs.append(explicit_context["stage_dir"])  # type: ignore[arg-type]
        return {
            "stage": current_stage.removesuffix("_review_confirmation_pending"),
            "lineage_id": lineage_root.name,
            "status": "FAIL",
            "content_findings": ["synthetic preflight failure"],
            "upstream_binding_findings": [],
        }

    monkeypatch.setattr("runtime.tools.research_session.run_review_preflight", _fake_run_review_preflight)

    payload = _review_entry_preflight_payload(
        lineage_root=lineage_root,
        current_stage=current_stage,  # type: ignore[arg-type]
    )

    assert payload is not None
    assert payload["status"] == "FAIL"
    assert captured_stage_dirs == [stage_dir]


@pytest.mark.parametrize("current_stage", POST_MANDATE_REVIEW_CONFIRMATION_STAGES)
def test_review_entry_preflight_does_not_expand_to_post_mandate_review_confirmation_pending_stages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    current_stage: str,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _write_required_author_outputs(lineage_root, current_stage)
    captured_stage_dirs: list[Path] = []

    monkeypatch.setattr(
        "runtime.tools.research_session.run_review_preflight",
        lambda *, explicit_context: captured_stage_dirs.append(explicit_context["stage_dir"]),
    )

    payload = _review_entry_preflight_payload(
        lineage_root=lineage_root,
        current_stage=current_stage,  # type: ignore[arg-type]
    )

    assert payload is None
    assert captured_stage_dirs == []


def test_run_research_session_keeps_post_mandate_review_entry_pending_without_preflight_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = _write_required_author_outputs(lineage_root, "data_ready_review_confirmation_pending")

    def _unexpected_preflight(*, explicit_context: dict[str, object]) -> dict[str, object]:
        raise AssertionError(f"unexpected preflight for {explicit_context['stage_dir']}")

    monkeypatch.setattr("runtime.tools.research_session.run_review_preflight", _unexpected_preflight)

    assert stage_dir == lineage_root / "02_data_ready"
    assert detect_session_stage(lineage_root) == "data_ready_review_confirmation_pending"

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "data_ready_review_confirmation_pending"
    assert status.stage_status == "awaiting_review_confirmation"
    assert status.blocking_reason_code == "REVIEW_CONFIRMATION_REQUIRED"
    assert "qros-data-ready-review" in (status.next_action or "")


def test_continue_mode_keeps_review_confirmation_user_facing_on_research_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    _write_required_author_outputs(lineage_root, "data_ready_review_confirmation_pending")

    def _unexpected_preflight(*, explicit_context: dict[str, object]) -> dict[str, object]:
        raise AssertionError(f"unexpected preflight for {explicit_context['stage_dir']}")

    monkeypatch.setattr("runtime.tools.research_session.run_review_preflight", _unexpected_preflight)

    status = run_research_session(
        outputs_root=outputs_root,
        lineage_id="btc_leads_alts",
        continue_mode=True,
    )

    assert status.current_stage == "data_ready_review_confirmation_pending"
    assert status.current_skill == "qros-research-session"
    assert status.stage_status == "awaiting_review_confirmation"
    assert status.blocking_reason == "data_ready review is waiting for explicit CONFIRM_REVIEW in qros-research-session."
    assert "CONFIRM_REVIEW" in status.next_action
    assert "stage-specific review protocol internally" in status.next_action
    assert "qros-data-ready-review" not in status.next_action


def test_confirm_review_moves_continue_mode_into_review_lane(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = _write_required_author_outputs(lineage_root, "data_ready_review_confirmation_pending")

    status = run_research_session(
        outputs_root=outputs_root,
        lineage_id="btc_leads_alts",
        review_decision="CONFIRM_REVIEW",
        continue_mode=True,
    )

    assert status.current_stage == "data_ready_review"
    assert status.current_skill == "qros-research-session"
    assert status.blocking_reason_code == "ADVERSARIAL_REVIEW_PENDING"
    assert status.blocking_reason == "data_ready review lane is active and waiting for reviewer output, audit, or closure."
    assert "review orchestration for data_ready" in status.next_action
    assert (stage_dir / "author" / "draft" / "review_transition_approval.yaml").exists()
