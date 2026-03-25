from pathlib import Path
from subprocess import run

import yaml


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_run_research_session_creates_lineage_from_raw_idea(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"

    result = run(
        [
            "python",
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--raw-idea",
            "BTC leads high-liquidity alts after shock events",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    lineage_root = outputs_root / "btc_leads_high_liquidity_alts_after_shock_events"
    assert (lineage_root / "00_idea_intake").exists()
    assert "Current stage: idea_intake" in result.stdout


def test_run_research_session_reports_mandate_author_when_intake_admitted(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
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
    _write_yaml(intake_dir / "scope_canvas.yaml", {"market": "binance perp"})
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n\n- TODO\n", encoding="utf-8")

    result = run(
        [
            "python",
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    assert "Current stage: mandate_review" in result.stdout
    assert (lineage_root / "01_mandate" / "mandate.md").exists()


def test_run_research_session_reports_mandate_review_when_review_pending(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
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

    result = run(
        [
            "python",
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    assert "Current stage: mandate_review" in result.stdout


def test_run_research_session_reports_mandate_review_complete_when_closure_exists(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
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

    result = run(
        [
            "python",
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    assert "Current stage: mandate_review_complete" in result.stdout
