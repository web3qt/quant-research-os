from pathlib import Path

import yaml

from tests.lineage_program_support import write_fake_stage_provenance
from tools.research_session import detect_session_stage, run_research_session


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_stage_completion_certificate(path: Path, stage_status: str = "PASS") -> None:
    _write_yaml(path, {"stage_status": stage_status, "final_verdict": stage_status})


def _write_display_decision(stage_dir: Path, *, stage: str) -> None:
    for review_name in ("latest_review_pack.yaml", "stage_gate_review.yaml"):
        if not (stage_dir / review_name).exists():
            (stage_dir / review_name).write_text("status: ok\n", encoding="utf-8")
    if not (stage_dir / "program_execution_manifest.json").exists():
        (stage_dir / "program_execution_manifest.json").write_text('{"status":"success"}\n', encoding="utf-8")


def _write_next_stage_confirmation(stage_dir: Path, *, stage: str) -> None:
    _write_yaml(
        stage_dir / "next_stage_transition_approval.yaml",
        {
            "lineage_id": stage_dir.parent.name,
            "stage_id": stage,
            "decision": "CONFIRM_NEXT_STAGE",
            "approved_by": "tester",
            "approved_at": "2026-04-06T10:05:00Z",
            "source_stage": f"{stage}_next_stage_confirmation_pending",
        },
    )


def _prepare_mandate_review_complete(lineage_root: Path) -> None:
    mandate_dir = lineage_root / "01_mandate"
    mandate_dir.mkdir(parents=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "latest_review_pack.yaml",
        "stage_gate_review.yaml",
    ]:
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")
    _write_yaml(
        mandate_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "regime_filter",
            "factor_structure": "multi_factor_score",
            "portfolio_expression": "long_only_rank",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "trend_combo_v1",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )
    _write_stage_completion_certificate(mandate_dir / "stage_completion_certificate.yaml")
    write_fake_stage_provenance(lineage_root, "mandate")


def test_detect_session_stage_routes_csf_lineage_into_csf_data_ready(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_mandate_review_complete(lineage_root)

    assert detect_session_stage(lineage_root) == "mandate_next_stage_confirmation_pending"


def test_run_research_session_scaffolds_csf_data_ready_after_mandate_review(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_mandate_review_complete(lineage_root)

    status = run_research_session(outputs_root=tmp_path / "outputs", lineage_id="csf_case")

    assert status.current_stage == "mandate_next_stage_confirmation_pending"
    assert not (lineage_root / "02_csf_data_ready" / "csf_data_ready_freeze_draft.yaml").exists()
    assert status.current_route == "cross_sectional_factor"
    assert status.factor_role == "regime_filter"
    assert status.portfolio_expression == "long_only_rank"


def test_run_research_session_writes_csf_transition_approval_in_csf_directory(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_mandate_review_complete(lineage_root)

    status = run_research_session(
        outputs_root=tmp_path / "outputs",
        lineage_id="csf_case",
        data_ready_decision="CONFIRM_DATA_READY",
    )

    approval_path = lineage_root / "02_csf_data_ready" / "data_ready_transition_approval.yaml"
    assert approval_path.exists()
    assert status.current_stage == "mandate_next_stage_confirmation_pending"

    _write_display_decision(lineage_root / "01_mandate", stage="mandate")
    _write_next_stage_confirmation(lineage_root / "01_mandate", stage="mandate")

    status = run_research_session(outputs_root=tmp_path / "outputs", lineage_id="csf_case")
    assert status.current_stage in {"csf_data_ready_confirmation_pending", "csf_data_ready_author"}
