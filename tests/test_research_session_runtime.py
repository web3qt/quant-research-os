from __future__ import annotations

from pathlib import Path

import pytest

from tools.research_session import (
    SessionContext,
    detect_session_stage,
    resolve_lineage_root,
    slugify_idea,
    summarize_session_status,
)


def test_slugify_idea_derives_stable_lineage_slug() -> None:
    assert slugify_idea("BTC leads high-liquidity alts after shock events") == "btc_leads_high_liquidity_alts_after_shock_events"


def test_detect_session_stage_returns_idea_intake_for_empty_lineage(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    lineage_root.mkdir(parents=True)

    assert detect_session_stage(lineage_root) == "idea_intake"


def test_detect_session_stage_returns_idea_intake_when_gate_not_admitted(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    (intake_dir / "idea_gate_decision.yaml").write_text("verdict: NEEDS_REFRAME\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "idea_intake"


def test_detect_session_stage_returns_mandate_author_when_intake_is_admitted(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    (intake_dir / "idea_gate_decision.yaml").write_text("verdict: GO_TO_MANDATE\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "mandate_author"


def test_detect_session_stage_returns_mandate_review_when_mandate_exists_but_no_closure(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    mandate_dir = lineage_root / "01_mandate"
    mandate_dir.mkdir(parents=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "run_manifest.json",
    ]:
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")
    (lineage_root / "00_idea_intake").mkdir(parents=True)
    (lineage_root / "00_idea_intake" / "idea_gate_decision.yaml").write_text("verdict: GO_TO_MANDATE\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "mandate_review"


def test_detect_session_stage_returns_mandate_review_complete_when_closure_exists(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    mandate_dir = lineage_root / "01_mandate"
    mandate_dir.mkdir(parents=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "run_manifest.json",
        "stage_completion_certificate.yaml",
    ]:
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")
    (lineage_root / "00_idea_intake").mkdir(parents=True)
    (lineage_root / "00_idea_intake" / "idea_gate_decision.yaml").write_text("verdict: GO_TO_MANDATE\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "mandate_review_complete"


def test_summarize_session_status_includes_required_fields(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    lineage_root.mkdir(parents=True)

    context = SessionContext(
        lineage_id="btc_alt_transmission_v1",
        lineage_root=lineage_root,
        current_stage="idea_intake",
        artifacts_written=["00_idea_intake/idea_brief.md"],
        gate_status="NEEDS_REFRAME",
        next_action="fill intake artifacts",
    )

    summary = summarize_session_status(context)

    assert summary["lineage"] == "btc_alt_transmission_v1"
    assert summary["current_stage"] == "idea_intake"
    assert summary["artifacts_written"] == ["00_idea_intake/idea_brief.md"]
    assert summary["gate_status"] == "NEEDS_REFRAME"
    assert summary["next_action"] == "fill intake artifacts"


def test_resolve_lineage_root_uses_raw_idea_when_no_lineage_id(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    outputs_root.mkdir()

    resolved = resolve_lineage_root(outputs_root, lineage_id=None, raw_idea="BTC leads high-liquidity alts after shock events")

    assert resolved == outputs_root / "btc_leads_high_liquidity_alts_after_shock_events"
