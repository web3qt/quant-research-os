from pathlib import Path

import yaml

from runtime.tools.research_session import run_research_session
from tests.helpers.lineage_program_support import write_fake_stage_provenance


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_tss_mandate_review_complete(lineage_root: Path) -> None:
    mandate_dir = lineage_root / "01_mandate"
    formal_dir = mandate_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    _write_yaml(
        formal_dir / "research_route.yaml",
        {
            "research_route": "time_series_signal",
            "excluded_routes": ["cross_sectional_factor"],
        },
    )
    closure_dir = mandate_dir / "review" / "closure"
    closure_dir.mkdir(parents=True)
    _write_yaml(
        closure_dir / "stage_completion_certificate.yaml",
        {"stage_status": "PASS", "final_verdict": "PASS"},
    )
    (closure_dir / "latest_review_pack.yaml").write_text("status: ok\n", encoding="utf-8")
    (closure_dir / "stage_gate_review.yaml").write_text("status: ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")


def _write_mandate_next_stage_confirmation(lineage_root: Path) -> None:
    _write_yaml(
        lineage_root / "01_mandate" / "author" / "draft" / "next_stage_transition_approval.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "decision": "CONFIRM_NEXT_STAGE",
            "approved_by": "tester",
            "approved_at": "2026-04-28T10:00:00Z",
            "source_stage": "mandate_next_stage_confirmation_pending",
        },
    )


def test_time_series_route_waits_at_mandate_handoff_without_legacy_data_ready_scaffold(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_mandate_review_complete(lineage_root)

    status = run_research_session(outputs_root=tmp_path / "outputs", lineage_id="tss_case")

    assert status.current_route == "time_series_signal"
    assert status.current_stage == "mandate_next_stage_confirmation_pending"
    assert "tss_data_ready" in status.next_action
    assert not (lineage_root / "02_data_ready").exists()
    assert not (lineage_root / "02_tss_data_ready").exists()


def test_time_series_route_scaffolds_tss_data_ready_after_mandate_next_stage_confirmation(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_mandate_review_complete(lineage_root)
    _write_mandate_next_stage_confirmation(lineage_root)

    status = run_research_session(outputs_root=tmp_path / "outputs", lineage_id="tss_case")

    assert status.current_stage in {"tss_data_ready_confirmation_pending", "tss_data_ready_author"}
    assert status.current_skill == "qros-tss-data-ready-author"
    assert (
        lineage_root
        / "02_tss_data_ready"
        / "author"
        / "draft"
        / "tss_data_ready_freeze_draft.yaml"
    ).exists()
    assert not (lineage_root / "02_data_ready").exists()
