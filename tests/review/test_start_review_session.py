import json
from pathlib import Path
from subprocess import run
import sys

import yaml

from tests.helpers.repo_paths import REPO_ROOT
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.session.test_research_session_runtime import _write_minimal_stage_outputs
from runtime.tools import review_session_runtime
from runtime.tools.review_session_runtime import start_review_session
from runtime.tools.review_skillgen.review_runtime_state import load_review_runtime_state


def _prepare_mandate_stage(tmp_path: Path) -> tuple[Path, Path]:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    (stage_dir / "author" / "formal" / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    ensure_stage_program(lineage_root, "mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    return lineage_root, stage_dir


def test_start_review_session_registers_active_cycle_and_receipt(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    payload = start_review_session(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="review-session-1",
        launcher_thread_id="review-thread-1",
    )

    assert payload["stage"] == "mandate"
    assert (stage_dir / "review" / "request" / "adversarial_review_request.yaml").exists()
    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    assert receipt_payload["execution_mode"] == "review_session"
    assert receipt_payload["reviewer_agent_id"] == "review-session-1"
    state_payload = load_review_runtime_state(stage_dir / "review" / "state" / "review_runtime_state.yaml")
    assert state_payload["review_state"] == "review_in_progress"
    assert state_payload["active_review_cycle_id"] == payload["review_cycle_id"]


def test_start_review_cycle_registers_spawned_agent_receipt(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    start_review_cycle = getattr(review_session_runtime, "start_review_cycle", None)

    assert callable(start_review_cycle)

    payload = start_review_cycle(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="launcher-session-1",
        launcher_thread_id="launcher-thread-1",
        reviewer_agent_id="reviewer-child-1",
    )

    assert payload["stage"] == "mandate"
    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    assert receipt_payload["execution_mode"] == "spawned_agent"
    assert receipt_payload["reviewer_agent_id"] == "reviewer-child-1"
    state_payload = load_review_runtime_state(stage_dir / "review" / "state" / "review_runtime_state.yaml")
    assert state_payload["review_state"] == "review_in_progress"
    assert state_payload["active_review_cycle_id"] == payload["review_cycle_id"]


def test_start_review_session_rejects_second_active_cycle_without_author_changes(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    start_review_session(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="review-session-1",
        launcher_thread_id="review-thread-1",
    )

    try:
        start_review_session(
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": lineage_root,
            },
            reviewer_identity="codex-mandate-reviewer",
            reviewer_session_id="review-session-2",
            launcher_session_id="review-session-2",
            launcher_thread_id="review-thread-2",
        )
    except ValueError as exc:
        assert "active review cycle" in str(exc)
    else:
        raise AssertionError("expected active review cycle rejection")


def test_start_review_session_archives_stale_cycle_after_author_changes(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    first = start_review_session(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="review-session-1",
        launcher_thread_id="review-thread-1",
    )
    (stage_dir / "author" / "formal" / "mandate.md").write_text("changed after review start\n", encoding="utf-8")

    second = start_review_session(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-2",
        launcher_session_id="review-session-2",
        launcher_thread_id="review-thread-2",
    )

    assert first["review_cycle_id"] == second["review_cycle_id"]
    archived = second["archived_paths"]
    assert any("review/archive/request" in item for item in archived)
    assert any("review/archive/state" in item for item in archived)


def test_start_review_session_script_emits_registered_cycle(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = REPO_ROOT / "runtime" / "scripts" / "start_review_session.py"

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(lineage_root),
            "--reviewer-id",
            "codex-mandate-reviewer",
            "--reviewer-session-id",
            "review-session-1",
            "--launcher-session-id",
            "review-session-1",
            "--launcher-thread-id",
            "review-thread-1",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Review cycle:" in result.stdout


def test_start_review_cycle_script_emits_spawned_agent_receipt(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = REPO_ROOT / "runtime" / "scripts" / "start_review_cycle.py"

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(lineage_root),
            "--reviewer-id",
            "codex-mandate-reviewer",
            "--reviewer-session-id",
            "review-session-1",
            "--launcher-session-id",
            "launcher-session-1",
            "--launcher-thread-id",
            "launcher-thread-1",
            "--reviewer-agent-id",
            "reviewer-child-1",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Execution mode: spawned_agent" in result.stdout
    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    assert receipt_payload["execution_mode"] == "spawned_agent"
    assert receipt_payload["reviewer_agent_id"] == "reviewer-child-1"


def test_qros_review_script_can_infer_identity_from_review_session_receipt(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    start_review_session(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="review-session-1",
        launcher_thread_id="review-thread-1",
    )
    raw_path = stage_dir / "review" / "result" / "reviewer_findings.raw.yaml"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        yaml.safe_dump(
            {
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": ["review session mode"],
                "residual_risks": [],
                "allowed_modifications": [],
                "downstream_permissions": ["data_ready"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    script_path = REPO_ROOT / "runtime" / "scripts" / "run_stage_review.py"
    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(lineage_root),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    result_payload = yaml.safe_load(
        (stage_dir / "review" / "result" / "adversarial_review_result.yaml").read_text(encoding="utf-8")
    )
    assert result_payload["reviewer_identity"] == "codex-mandate-reviewer"
    assert result_payload["reviewer_session_id"] == "review-session-1"
    assert result_payload["reviewer_execution_mode"] == "review_session"
    state_payload = load_review_runtime_state(stage_dir / "review" / "state" / "review_runtime_state.yaml")
    assert state_payload["review_state"] == "review_closed_pass"
