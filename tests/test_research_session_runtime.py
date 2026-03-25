from pathlib import Path

import yaml

from tools.research_session import (
    detect_session_stage,
    resolve_lineage_root,
    slugify_idea,
    summarize_session_status,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_slugify_idea_derives_stable_lineage_id() -> None:
    assert slugify_idea("BTC leads high-liquidity alts after shock events") == (
        "btc_leads_high_liquidity_alts_after_shock_events"
    )


def test_resolve_lineage_root_creates_slug_from_raw_idea(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    lineage_root = resolve_lineage_root(outputs_root, lineage_id=None, raw_idea="BTC leads ALTs")

    assert lineage_root == outputs_root / "btc_leads_alts"


def test_detect_session_stage_returns_idea_intake_when_lineage_missing(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"

    assert detect_session_stage(lineage_root) == "idea_intake"


def test_detect_session_stage_returns_idea_intake_when_gate_not_admitted(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_leads_alts",
            "verdict": "NEEDS_REFRAME",
            "why": ["scope unclear"],
            "approved_scope": {},
            "required_reframe_actions": ["narrow universe"],
            "rollback_target": "00_idea_intake",
        },
    )

    assert detect_session_stage(lineage_root) == "idea_intake"


def test_detect_session_stage_returns_pending_confirmation_when_admitted_but_not_approved(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_leads_alts",
            "verdict": "GO_TO_MANDATE",
            "why": ["qualified"],
            "approved_scope": {"market": "binance perp"},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )

    assert detect_session_stage(lineage_root) == "mandate_confirmation_pending"


def test_detect_session_stage_returns_mandate_author_when_admitted_and_explicitly_approved(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_leads_alts",
            "verdict": "GO_TO_MANDATE",
            "why": ["qualified"],
            "approved_scope": {"market": "binance perp"},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "mandate_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_MANDATE",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_gate_verdict": "GO_TO_MANDATE",
        },
    )

    assert detect_session_stage(lineage_root) == "mandate_author"


def test_detect_session_stage_returns_mandate_review_when_mandate_artifacts_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
    ]:
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "mandate_review"


def test_detect_session_stage_returns_mandate_review_complete_when_closure_artifacts_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
        "stage_completion_certificate.yaml",
    ]:
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "mandate_review_complete"


def test_summarize_session_status_contains_required_fields(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"

    status = summarize_session_status(
        lineage_id="btc_leads_alts",
        lineage_root=lineage_root,
        current_stage="idea_intake",
        artifacts_written=["00_idea_intake/idea_brief.md"],
        gate_status="NEEDS_REFRAME",
        next_action="Fill qualification inputs",
    )

    assert status.lineage_id == "btc_leads_alts"
    assert status.lineage_root == lineage_root
    assert status.current_stage == "idea_intake"
    assert status.artifacts_written == ["00_idea_intake/idea_brief.md"]
    assert status.gate_status == "NEEDS_REFRAME"
    assert status.next_action == "Fill qualification inputs"
