from pathlib import Path

import pytest
import yaml

from tests.lineage_program_support import STAGE_PROGRAM_SPECS, ensure_stage_program, write_fake_stage_provenance
from tests.test_research_session_runtime import _write_minimal_stage_outputs
from tools.research_session import run_research_session
from tools.review_skillgen.review_engine import run_stage_review


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
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_stage(tmp_path: Path) -> tuple[Path, Path]:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / "01_mandate"
    stage_dir.mkdir(parents=True)

    for name in MANDATE_REQUIRED_OUTPUTS:
        (stage_dir / name).write_text("ok\n", encoding="utf-8")

    ensure_stage_program(lineage_root, "mandate")
    write_fake_stage_provenance(lineage_root, "mandate")
    return lineage_root, stage_dir


def _write_adversarial_review_request(
    stage_dir: Path,
    *,
    stage_key: str = "mandate",
    author_identity: str = "author-agent",
) -> None:
    spec = STAGE_PROGRAM_SPECS[stage_key]
    lineage_id = stage_dir.parent.name
    _write_yaml(
        stage_dir / "adversarial_review_request.yaml",
        {
            "review_cycle_id": "review-cycle-1",
            "lineage_id": lineage_id,
            "stage": spec["stage_id"],
            "author_identity": author_identity,
            "author_session_id": "author-session",
            "required_program_dir": str(spec["program_dir"]),
            "required_program_entrypoint": "run_stage.py",
            "required_artifact_paths": [Path(path).name for path in spec["outputs"][:2]],
            "required_provenance_paths": ["program_execution_manifest.json"],
            "required_reviewer_mode": "adversarial",
        },
    )


def _write_adversarial_review_result(
    stage_dir: Path,
    *,
    stage_key: str = "mandate",
    reviewer_identity: str,
    review_loop_outcome: str,
    reviewer_mode: str = "adversarial",
) -> None:
    spec = STAGE_PROGRAM_SPECS[stage_key]
    _write_yaml(
        stage_dir / "adversarial_review_result.yaml",
        {
            "review_cycle_id": "review-cycle-1",
            "reviewer_identity": reviewer_identity,
            "reviewer_role": "adversarial-reviewer",
            "reviewer_session_id": "reviewer-session",
            "reviewer_mode": reviewer_mode,
            "reviewed_program_dir": str(spec["program_dir"]),
            "reviewed_program_entrypoint": "run_stage.py",
            "reviewed_artifact_paths": [Path(path).name for path in spec["outputs"][:2]],
            "reviewed_provenance_paths": ["program_execution_manifest.json"],
            "review_loop_outcome": review_loop_outcome,
        },
    )


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
        mandate_dir.mkdir(parents=True, exist_ok=True)
        _write_yaml(
            mandate_dir / "research_route.yaml",
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
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="author-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    _write_yaml(
        stage_dir / "review_findings.yaml",
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
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="FIX_REQUIRED",
    )
    _write_yaml(
        stage_dir / "review_findings.yaml",
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
    assert not (stage_dir / "latest_review_pack.yaml").exists()
    assert not (stage_dir / "stage_gate_review.yaml").exists()
    assert not (stage_dir / "stage_completion_certificate.yaml").exists()


def test_run_stage_review_rejects_non_adversarial_reviewer_mode(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
        reviewer_mode="observer",
    )
    _write_yaml(
        stage_dir / "review_findings.yaml",
        {
            "reviewer_identity": "reviewer-agent",
            "recommended_verdict": "PASS",
        },
    )

    with pytest.raises(ValueError, match="adversarial"):
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="reviewer-agent",
            reviewer_role="adversarial-reviewer",
            reviewer_session_id="reviewer-session",
            reviewer_mode="observer",
        )


def test_run_stage_review_rejects_scope_that_does_not_match_runtime_request(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    _write_adversarial_review_result(
        stage_dir,
        stage_key="mandate",
        reviewer_identity="reviewer-agent",
        review_loop_outcome="CLOSURE_READY_PASS",
    )
    _write_yaml(
        stage_dir / "adversarial_review_result.yaml",
        {
            "review_cycle_id": "review-cycle-1",
            "reviewer_identity": "reviewer-agent",
            "reviewer_role": "adversarial-reviewer",
            "reviewer_session_id": "reviewer-session",
            "reviewer_mode": "adversarial",
            "reviewed_program_dir": "program/unapproved_scope",
            "reviewed_program_entrypoint": "alternate.py",
            "reviewed_artifact_paths": ["mandate.md", "research_scope.md"],
            "reviewed_provenance_paths": ["program_execution_manifest.json"],
            "review_loop_outcome": "CLOSURE_READY_PASS",
        },
    )
    _write_yaml(
        stage_dir / "review_findings.yaml",
        {
            "reviewer_identity": "reviewer-agent",
            "recommended_verdict": "PASS",
        },
    )

    with pytest.raises(ValueError, match="program scope|required_program"):
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
    assert "adversarial" in (status.blocking_reason or "").lower()


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
