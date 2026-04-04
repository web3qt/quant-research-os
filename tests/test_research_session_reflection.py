from pathlib import Path

from tools.research_session_reflection import build_data_ready_reflection, render_reflection_lines


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("ok\n", encoding="utf-8")


def test_build_data_ready_reflection_returns_none_outside_signal_ready_confirmation(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    stage_dir = lineage_root / "02_data_ready"
    stage_dir.mkdir(parents=True)

    reflection = build_data_ready_reflection(
        lineage_root=lineage_root,
        current_stage="data_ready_review",
        current_route="time_series_signal",
    )

    assert reflection is None


def test_build_data_ready_reflection_returns_none_for_csf_route(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = lineage_root / "02_data_ready"
    stage_dir.mkdir(parents=True)

    reflection = build_data_ready_reflection(
        lineage_root=lineage_root,
        current_stage="signal_ready_confirmation_pending",
        current_route="cross_sectional_factor",
    )

    assert reflection is None


def test_build_data_ready_reflection_reports_present_and_missing_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    stage_dir = lineage_root / "02_data_ready"
    stage_dir.mkdir(parents=True)
    for directory_name in (
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ):
        (stage_dir / directory_name).mkdir()
    for file_name in (
        "dataset_manifest.json",
        "validation_report.md",
        "data_contract.md",
        "dedupe_rule.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "qc_report.parquet",
        "universe_exclusions.csv",
        "universe_exclusions.md",
        "data_ready_gate_decision.md",
        "run_manifest.json",
        "rebuild_data_ready.py",
    ):
        _touch(stage_dir / file_name)

    reflection = build_data_ready_reflection(
        lineage_root=lineage_root,
        current_stage="signal_ready_confirmation_pending",
        current_route="time_series_signal",
    )

    assert reflection is not None
    rendered = "\n".join(render_reflection_lines(reflection))
    assert "Data Ready Reflection:" in rendered
    assert "- Data Coverage And Gaps:" in rendered
    assert "- QC / Anomaly Summary:" in rendered
    assert "- Artifact Directory And Key Files:" in rendered
    assert "core data layers present: 5/5" in rendered
    assert "missing core data layers: none" in rendered
    assert "validation_report.md: available" in rendered
    assert "stage directory: outputs/btc_leads_alts/02_data_ready" in rendered


def test_build_data_ready_reflection_turns_missing_evidence_into_questions(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    stage_dir = lineage_root / "02_data_ready"
    stage_dir.mkdir(parents=True)
    (stage_dir / "aligned_bars").mkdir()
    _touch(stage_dir / "dataset_manifest.json")

    reflection = build_data_ready_reflection(
        lineage_root=lineage_root,
        current_stage="signal_ready_confirmation_pending",
        current_route="time_series_signal",
    )

    assert reflection is not None
    rendered = "\n".join(render_reflection_lines(reflection))
    assert "missing core data layers: rolling_stats, pair_stats, benchmark_residual, topic_basket_state" in rendered
    assert "qc_report.parquet: missing" in rendered
    assert "question: what justifies moving into signal work before the missing coverage artifacts are explained?" in rendered
    assert "question: which missing QC artifacts must be reviewed before the stage can be trusted?" in rendered
