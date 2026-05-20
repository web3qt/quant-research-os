from __future__ import annotations

from pathlib import Path

import pytest

from runtime.tools.author_context_runtime import (
    STAGE_AUTHOR_CONTEXT_MD_FILENAME,
    STAGE_AUTHOR_CONTEXT_YAML_FILENAME,
    build_stage_author_context,
    render_stage_author_context_markdown,
)
from runtime.tools.research_session import (
    _author_context_for_current_stage,
    _next_author_action_from_context,
    _write_stage_author_context_for_current_stage,
)


def test_stage_author_context_filenames_are_stable() -> None:
    assert STAGE_AUTHOR_CONTEXT_YAML_FILENAME == "stage_author_context.yaml"
    assert STAGE_AUTHOR_CONTEXT_MD_FILENAME == "stage_author_context.md"


def test_build_stage_author_context_for_mandate_contains_truth_and_orchestration() -> None:
    payload = build_stage_author_context(
        stage_id="mandate",
        current_stage="mandate_confirmation_pending",
        lineage_id="lineage_a",
        route="route_neutral",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/01_mandate"),
    )

    assert payload["stage_id"] == "mandate"
    assert payload["stage_name"] == "Mandate"
    assert payload["truth"]["artifact_contract"] == "contracts/artifacts/mandate_artifacts.yaml"
    assert payload["orchestration"]["requires_final_author_confirmation"] is True
    assert payload["orchestration"]["allowed_runtime_stages"] == [
        "mandate_confirmation_pending",
        "mandate_author",
    ]
    assert payload["guidance"]["author_focus"]


def test_build_stage_author_context_for_csf_stage_contains_freeze_group_order() -> None:
    payload = build_stage_author_context(
        stage_id="csf_data_ready",
        current_stage="csf_data_ready_confirmation_pending",
        lineage_id="lineage_a",
        route="cross_sectional_factor",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/02_csf_data_ready"),
    )

    assert payload["stage_id"] == "csf_data_ready"
    assert payload["orchestration"]["freeze_group_order"] == [
        "panel_contract",
        "taxonomy_contract",
        "eligibility_contract",
        "shared_feature_base",
        "delivery_contract",
    ]
    assert "qros-validate-stage --stage csf_data_ready" in payload["truth"]["validator_requirements"]


def test_render_stage_author_context_markdown_mentions_author_entrypoint() -> None:
    payload = build_stage_author_context(
        stage_id="idea_intake",
        current_stage="idea_intake_confirmation_pending",
        lineage_id="lineage_a",
        route="route_neutral",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/00_idea_intake"),
    )

    markdown = render_stage_author_context_markdown(payload)

    assert "stage_author_context" not in markdown
    assert "current-stage author truth entrypoint" in markdown
    assert "idea_intake" in markdown
    assert "confirm all" in markdown.lower()


def test_build_stage_author_context_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="AUTHOR_CONTEXT_MISSING"):
        build_stage_author_context(
            stage_id="unknown_stage",
            current_stage="unknown_stage_confirmation_pending",
            lineage_id="lineage_a",
            route="route_neutral",
            review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/99_unknown_stage"),
        )


def test_author_context_for_current_stage_maps_confirmation_pending_to_stage_context() -> None:
    payload = _author_context_for_current_stage(
        lineage_id="lineage_a",
        current_stage="csf_data_ready_confirmation_pending",
        lineage_root=Path("/tmp/outputs/lineage_a"),
    )

    assert payload["stage_id"] == "csf_data_ready"
    assert payload["current_stage"] == "csf_data_ready_confirmation_pending"


def test_next_author_action_from_context_stops_at_final_confirmation_once_groups_are_done() -> None:
    payload = build_stage_author_context(
        stage_id="mandate",
        current_stage="mandate_author",
        lineage_id="lineage_a",
        route="route_neutral",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/01_mandate"),
    )
    action = _next_author_action_from_context(
        payload,
        unresolved_groups=[],
        all_groups_confirmed=True,
        final_confirmation_complete=False,
    )

    assert action["kind"] == "request_final_author_confirmation"


def test_write_stage_author_context_for_current_stage_materializes_context_files(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "lineage_a"
    (lineage_root / "02_csf_data_ready" / "author").mkdir(parents=True, exist_ok=True)

    written = _write_stage_author_context_for_current_stage(
        lineage_id="lineage_a",
        current_stage="csf_data_ready_confirmation_pending",
        lineage_root=lineage_root,
    )

    yaml_path = lineage_root / written["yaml_path"]
    md_path = lineage_root / written["md_path"]
    assert yaml_path.exists()
    assert md_path.exists()
    assert "stage_author_context.yaml" in written["yaml_path"]
    assert "stage_author_context.md" in written["md_path"]
