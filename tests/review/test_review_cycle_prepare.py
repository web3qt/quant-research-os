import json
import hashlib
from pathlib import Path
from subprocess import run
import sys

import pytest
import yaml

from tests.helpers.repo_paths import REPO_ROOT
from tests.review.test_start_review_session import _prepare_mandate_stage
from runtime.tools import review_session_runtime
from runtime.tools.review_session_runtime import (
    prepare_review_cycle_for_handoff,
    reset_review_cycle,
    start_review_cycle,
)
from runtime.tools.review_skillgen.review_engine import ReviewRuntimeConfigurationError
from runtime.tools.review_skillgen.reviewer_write_scope_audit import current_unexpected_result_files


def _rewrite_active_request_to_old_subset(stage_dir: Path, *, required_artifact_paths: list[str]) -> None:
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    request_payload = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    manifest_path = stage_dir / request_payload["handoff_manifest_path"]
    manifest_payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    for payload in (request_payload, manifest_payload):
        payload["required_artifact_paths"] = list(required_artifact_paths)
        payload["required_provenance_paths"] = ["program_execution_manifest.json"]
        payload["launcher_checked_artifact_paths"] = list(required_artifact_paths)
        payload["launcher_checked_provenance_paths"] = ["program_execution_manifest.json"]
        payload["launcher_handoff_context_paths"] = [
            path for path in ("artifact_catalog.md", "field_dictionary.md", "run_manifest.json") if path in required_artifact_paths
        ]
        payload["stage_content_artifact_paths"] = []
        payload["stage_content_provenance_paths"] = []
        payload["upstream_binding_artifact_paths"] = []
        payload["upstream_binding_provenance_paths"] = []

    manifest_text = yaml.safe_dump(manifest_payload, sort_keys=False, allow_unicode=True)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    request_payload["handoff_manifest_digest"] = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
    request_payload["bound_author_materialization_digest"] = review_session_runtime.compute_author_materialization_digest_fresh(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=required_artifact_paths,
        required_provenance_paths=("program_execution_manifest.json",),
    )
    request_path.write_text(yaml.safe_dump(request_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _patch_review_ready_preflight_pass(monkeypatch: pytest.MonkeyPatch, *, lineage_id: str) -> None:
    def _fake_run_review_preflight(*, explicit_context: dict[str, object]) -> dict[str, object]:
        return {
            "stage": "mandate",
            "lineage_id": lineage_id,
            "status": "PASS",
            "content_findings": [],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }

    monkeypatch.setattr("runtime.tools.review_session_runtime.run_review_preflight", _fake_run_review_preflight)


def test_review_cycle_prepare_script_emits_handoff_prompt(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = REPO_ROOT / "runtime" / "scripts" / "review_cycle.py"

    result = run(
        [
            sys.executable,
            str(script_path),
            "prepare",
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
            "--json",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["stage"] == "mandate"
    assert payload["review_cycle_id"]
    assert "Permitted reads only" in payload["reviewer_handoff_prompt"]
    assert "outputs/topic_a/01_mandate/review/request/*" in payload["reviewer_handoff_prompt"]
    assert "review/final_review.yaml" in payload["reviewer_handoff_prompt"]
    assert "reviewer_findings.raw.yaml" not in payload["reviewer_handoff_prompt"]
    assert "stage_contract_context.yaml" in payload["reviewer_handoff_prompt"]
    assert "stage_contract_context.md" in payload["reviewer_handoff_prompt"]

    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    assert receipt_payload["reviewer_agent_id"] == "reviewer-child-1"


def test_review_cycle_prepare_preflights_runtime_config_before_writing_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    checklist_path = tmp_path / "review_checklist_master.yaml"
    checklist_path.write_text("stages: {}\n", encoding="utf-8")
    monkeypatch.setattr(review_session_runtime, "CHECKLIST_PATH", checklist_path, raising=False)

    with pytest.raises(ReviewRuntimeConfigurationError) as excinfo:
        start_review_cycle(
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

    message = str(excinfo.value)
    assert "missing review checklist stage: mandate" in message
    assert not (stage_dir / "review" / "request" / "adversarial_review_request.yaml").exists()
    assert not (stage_dir / "review" / "request" / "reviewer_receipt.yaml").exists()


def test_prepare_writes_stage_contract_context_files(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    payload = prepare_review_cycle_for_handoff(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="launcher-session-1",
        launcher_thread_id="launcher-thread-1",
        reviewer_agent_id="reviewer-child-1",
        host="codex",
    )

    request_dir = stage_dir / "review" / "request"
    assert (request_dir / "stage_contract_context.yaml").exists()
    assert (request_dir / "stage_contract_context.md").exists()
    assert "stage_contract_context.yaml" in payload["reviewer_handoff_prompt"]
    assert "stage_contract_context.md" in payload["reviewer_handoff_prompt"]


def test_review_cycle_prepare_rejects_review_ready_preflight_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    def _fake_run_review_preflight(*, explicit_context: dict[str, object]) -> dict[str, object]:
        return {
            "stage": "mandate",
            "lineage_id": lineage_root.name,
            "status": "FAIL",
            "content_findings": ["Missing required output: run_manifest.json"],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }

    monkeypatch.setattr("runtime.tools.review_session_runtime.run_review_preflight", _fake_run_review_preflight)

    with pytest.raises(ValueError, match="AUTHOR_FIX_REQUIRED_BEFORE_REVIEW"):
        prepare_review_cycle_for_handoff(
            explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
            reviewer_identity="reviewer-agent",
            reviewer_session_id="review-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
            host="codex",
        )

    assert not (stage_dir / "review" / "request" / "adversarial_review_request.yaml").exists()


def test_review_cycle_prepare_rejects_existing_request_when_review_ready_preflight_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    start_review_cycle(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session-1",
        launcher_session_id="launcher-session-1",
        launcher_thread_id="launcher-thread-1",
        reviewer_agent_id="reviewer-child-agent-1",
    )
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    original_request_text = request_path.read_text(encoding="utf-8")

    def _fake_run_review_preflight(*, explicit_context: dict[str, object]) -> dict[str, object]:
        return {
            "stage": "mandate",
            "lineage_id": lineage_root.name,
            "status": "FAIL",
            "content_findings": ["Missing required output: run_manifest.json"],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }

    monkeypatch.setattr("runtime.tools.review_session_runtime.run_review_preflight", _fake_run_review_preflight)

    with pytest.raises(ValueError, match="AUTHOR_FIX_REQUIRED_BEFORE_REVIEW"):
        prepare_review_cycle_for_handoff(
            explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
            reviewer_identity="reviewer-agent",
            reviewer_session_id="review-session-2",
            launcher_session_id="launcher-session-2",
            launcher_thread_id="launcher-thread-2",
            reviewer_agent_id="reviewer-child-agent-2",
            host="codex",
        )

    assert request_path.read_text(encoding="utf-8") == original_request_text
    receipt_payload = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    assert receipt_payload["reviewer_agent_id"] == "reviewer-child-agent-1"


def test_prepare_rejects_active_cycle_when_request_bound_digest_is_stale_even_without_runtime_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    start_review_cycle(
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
    (stage_dir / "review" / "state" / "review_runtime_state.yaml").unlink()
    (stage_dir / "author" / "formal" / "mandate.md").write_text("changed after prepare\n", encoding="utf-8")
    _patch_review_ready_preflight_pass(monkeypatch, lineage_id=lineage_root.name)

    with pytest.raises(ValueError, match="is stale"):
        prepare_review_cycle_for_handoff(
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": lineage_root,
            },
            reviewer_identity="codex-mandate-reviewer",
            reviewer_session_id="review-session-2",
            launcher_session_id="launcher-session-2",
            launcher_thread_id="launcher-thread-2",
            reviewer_agent_id="reviewer-child-2",
            host="codex",
        )


def test_prepare_rejects_divergent_request_and_state_digests_when_one_binding_is_old(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    start_review_cycle(
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
    (stage_dir / "author" / "formal" / "mandate.md").write_text("changed after prepare\n", encoding="utf-8")

    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    request_payload = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    state_path = stage_dir / "review" / "state" / "review_runtime_state.yaml"
    state_payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    state_payload["review_bound_author_digest"] = "manually-diverged-current-digest"
    state_path.write_text(yaml.safe_dump(state_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    _patch_review_ready_preflight_pass(monkeypatch, lineage_id=lineage_root.name)

    with pytest.raises(ValueError, match="is stale"):
        prepare_review_cycle_for_handoff(
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": lineage_root,
            },
            reviewer_identity="codex-mandate-reviewer",
            reviewer_session_id="review-session-2",
            launcher_session_id="launcher-session-2",
            launcher_thread_id="launcher-thread-2",
            reviewer_agent_id="reviewer-child-2",
            host="codex",
        )


def test_prepare_rejects_stale_cycle_when_old_request_omitted_now_required_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    start_review_cycle(
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
    _rewrite_active_request_to_old_subset(
        stage_dir,
        required_artifact_paths=[
            "mandate.md",
            "research_scope.md",
            "research_route.yaml",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
        ],
    )
    (stage_dir / "review" / "state" / "review_runtime_state.yaml").unlink()
    (stage_dir / "author" / "formal" / "field_dictionary.md").write_text("changed later-added truth\n", encoding="utf-8")
    _patch_review_ready_preflight_pass(monkeypatch, lineage_id=lineage_root.name)

    with pytest.raises(ValueError, match="is stale"):
        prepare_review_cycle_for_handoff(
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": lineage_root,
            },
            reviewer_identity="codex-mandate-reviewer",
            reviewer_session_id="review-session-2",
            launcher_session_id="launcher-session-2",
            launcher_thread_id="launcher-thread-2",
            reviewer_agent_id="reviewer-child-2",
            host="codex",
        )


def test_qros_review_cycle_wrapper_exists() -> None:
    assert Path("runtime/bin/qros-review-cycle").exists()


def test_review_cycle_reset_archives_stale_cycle(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    payload = start_review_cycle(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="reviewer",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-agent",
    )
    nested_result_path = stage_dir / "review" / "result" / "sidecar" / "launcher_notes.yaml"
    nested_result_path.parent.mkdir(parents=True, exist_ok=True)
    nested_result_path.write_text("notes: stale\n", encoding="utf-8")
    assert (stage_dir / "review" / "request" / "reviewer_receipt.yaml").exists()

    reset_payload = reset_review_cycle(
        stage_dir=stage_dir,
        review_cycle_id=payload["review_cycle_id"],
        reason="stale",
    )

    assert reset_payload["archived_paths"]
    assert not (stage_dir / "review" / "request" / "reviewer_receipt.yaml").exists()
    assert not nested_result_path.exists()
    assert current_unexpected_result_files(stage_dir) == []
    assert any(
        "review/archive/result/sidecar/launcher_notes." in path
        and ".stale." in path
        and path.endswith(".yaml")
        for path in reset_payload["archived_paths"]
    )
    assert reset_payload["next_action"] == "run qros-review-cycle prepare and request a fresh reviewer run"


def test_review_cycle_reset_script_archives_stale_cycle(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    start_review_cycle(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="reviewer",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-agent",
    )
    script_path = REPO_ROOT / "runtime" / "scripts" / "review_cycle.py"

    result = run(
        [
            sys.executable,
            str(script_path),
            "reset",
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(lineage_root),
            "--archive-stale-cycle",
            "--json",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["archived_paths"]
    assert payload["next_action"] == "run qros-review-cycle prepare and request a fresh reviewer run"
    assert not (stage_dir / "review" / "request" / "reviewer_receipt.yaml").exists()


def test_review_cycle_validate_script_reports_preflight_status(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = REPO_ROOT / "runtime" / "scripts" / "review_cycle.py"

    result = run(
        [
            sys.executable,
            str(script_path),
            "validate",
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(lineage_root),
            "--json",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["stage"] == "mandate"
    assert payload["lineage_id"] == lineage_root.name
    assert payload["status"] == "PASS"
