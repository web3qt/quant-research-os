from pathlib import Path

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ReviewerRuntimeIdentity,
    ensure_adversarial_review_request,
    issue_spawned_reviewer_receipt,
)
from runtime.tools.review_skillgen.review_result_writer import ensure_runtime_review_result
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.session.test_research_session_runtime import _write_minimal_stage_outputs


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_review_case(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "writer_case"
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    (stage_dir / "author" / "formal" / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    ensure_stage_program(lineage_root, "mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    ensure_adversarial_review_request(
        stage_dir,
        lineage_id=lineage_root.name,
        stage="mandate",
        author_identity="author-agent",
        author_session_id="author-session",
        required_program_dir="program/mandate",
        required_program_entrypoint="run_stage.py",
        required_artifact_paths=[
            "mandate.md",
            "research_scope.md",
            "research_route.yaml",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
            "run_manifest.json",
        ],
        required_provenance_paths=["program_execution_manifest.json"],
        program_hash="writer-hash",
        stage_invoked_at="2026-04-19T00:00:00+00:00",
    )
    issue_spawned_reviewer_receipt(
        stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="leader-thread",
        spawned_agent_id="reviewer-child-agent",
    )
    return stage_dir


def test_ensure_runtime_review_result_materializes_canonical_result_from_raw_findings(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_review_case(tmp_path)
    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "spawned_reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    _write_yaml(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        {
            "review_loop_outcome": "CLOSURE_READY_PASS",
            "blocking_findings": [],
            "reservation_findings": ["Document the remaining manual replay caveat."],
            "info_findings": ["Reviewer focused on stage-local mandate content only."],
            "residual_risks": ["Replay root still depends on local data availability."],
            "allowed_modifications": [],
            "downstream_permissions": ["mandate_next_stage_confirmation_pending"],
            "review_summary": "Stage-local content review passed after deterministic protocol checks.",
        },
    )

    payload = ensure_runtime_review_result(
        review_result_dir=stage_dir / "review" / "result",
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=ReviewerRuntimeIdentity(
            reviewer_identity="reviewer-agent",
            reviewer_role="reviewer",
            reviewer_session_id="review-session",
            reviewer_mode="adversarial",
        ),
    )

    assert payload["review_loop_outcome"] == "CLOSURE_READY_PASS"
    assert payload["reviewed_artifact_paths"] == sorted(request_payload["stage_content_artifact_paths"])
    assert payload["reviewed_provenance_paths"] == ["program_execution_manifest.json"]
    assert (stage_dir / "review" / "result" / "adversarial_review_result.yaml").exists()
    assert (stage_dir / "review" / "result" / "review_findings.yaml").exists()
