from __future__ import annotations

from pathlib import Path

import pytest

from runtime.tools.review_skillgen.stage_contract_context import (
    build_stage_contract_context,
    render_stage_contract_context_markdown,
)


def test_build_stage_contract_context_renders_expected_sources_for_csf_data_ready() -> None:
    payload = build_stage_contract_context(
        stage_id="csf_data_ready",
        lineage_id="lineage_a",
        review_cycle_id="cycle-1",
        author_materialization_digest="abc123",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/02_csf_data_ready"),
    )

    assert payload["stage_id"] == "csf_data_ready"
    assert payload["contract_sources"]["workflow_stage_gate"] == "contracts/stages/workflow_stage_gates.yaml"
    assert payload["contract_sources"]["review_checklist"] == "contracts/review/review_checklist_master.yaml"
    assert payload["contract_sources"]["artifact_contract"] == "contracts/artifacts/csf_data_ready_artifacts.yaml"
    assert payload["author_materialization_digest"] == "abc123"
    assert "formal_gate" in payload
    assert "review_checks" in payload


def test_render_stage_contract_context_markdown_includes_source_paths_and_summary() -> None:
    payload = build_stage_contract_context(
        stage_id="csf_data_ready",
        lineage_id="lineage_a",
        review_cycle_id="cycle-1",
        author_materialization_digest="abc123",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/02_csf_data_ready"),
    )

    markdown = render_stage_contract_context_markdown(payload)

    assert "contracts/stages/workflow_stage_gates.yaml" in markdown
    assert "contracts/review/review_checklist_master.yaml" in markdown
    assert "contracts/artifacts/csf_data_ready_artifacts.yaml" in markdown
    assert "CSF Data Ready" in markdown
    assert "review-cycle-local rendering of current contracts" in markdown


def test_build_stage_contract_context_fails_for_unknown_stage() -> None:
    with pytest.raises(ValueError, match="REVIEW_CONTRACT_CONTEXT_MISSING"):
        build_stage_contract_context(
            stage_id="unknown_stage",
            lineage_id="lineage_a",
            review_cycle_id="cycle-1",
            author_materialization_digest="abc123",
            review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/99_unknown_stage"),
        )
