from pathlib import Path
from subprocess import run

import yaml


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _mandate_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "research_intent": {
                "confirmed": confirmed,
                "draft": {
                    "research_question": "Does BTC shock lead ALT follow-through?",
                    "primary_hypothesis": "BTC drives price discovery for high-liquidity ALTs.",
                    "counter_hypothesis": "Observed moves are only shared beta.",
                    "success_criteria": ["ALT response remains after cost and beta controls."],
                    "failure_criteria": ["Lead-lag disappears after beta normalization."],
                    "excluded_topics": ["Low liquidity tails"],
                },
            },
            "scope_contract": {
                "confirmed": confirmed,
                "draft": {
                    "market": "Binance perpetual",
                    "universe": "top liquidity alts",
                    "target_task": "event-driven relative return study",
                    "excluded_scope": ["low liquidity tails"],
                    "budget_days": 10,
                    "max_iterations": 3,
                },
            },
            "data_contract": {
                "confirmed": confirmed,
                "draft": {
                    "data_source": "Binance UM futures klines",
                    "bar_size": "5m",
                    "holding_horizons": ["15m", "30m", "60m"],
                    "timestamp_semantics": "close-to-close bars in UTC",
                    "no_lookahead_guardrail": "All labels use only completed bars.",
                },
            },
            "execution_contract": {
                "confirmed": confirmed,
                "draft": {
                    "time_split_note": "Freeze train/test/backtest windows before signal work.",
                    "parameter_boundary_note": "Only event-window and decay parameters are allowed.",
                    "artifact_contract_note": "All machine-readable outputs must be registered.",
                    "crowding_capacity_note": "Capacity review uses identical liquidity proxy later.",
                },
            },
        }
    }


def test_scaffold_idea_intake_creates_stage_templates(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "scaffold_idea_intake.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"

    result = run(
        ["python", str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    intake_dir = lineage_root / "00_idea_intake"
    assert intake_dir.exists()
    assert (intake_dir / "idea_brief.md").exists()
    assert (intake_dir / "qualification_scorecard.yaml").exists()
    assert (intake_dir / "idea_gate_decision.yaml").exists()
    assert (intake_dir / "mandate_freeze_draft.yaml").exists()
    scope_canvas = yaml.safe_load((intake_dir / "scope_canvas.yaml").read_text(encoding="utf-8"))
    freeze_draft = yaml.safe_load((intake_dir / "mandate_freeze_draft.yaml").read_text(encoding="utf-8"))
    assert "data_source" in scope_canvas
    assert "bar_size" in scope_canvas
    assert set(freeze_draft["groups"]) == {
        "research_intent",
        "scope_contract",
        "data_contract",
        "execution_contract",
    }
    assert "Scaffolded idea intake" in result.stdout


def test_build_mandate_from_intake_requires_go_to_mandate(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_mandate_from_intake.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)

    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "NEEDS_REFRAME",
            "why": ["scope not ready"],
            "approved_scope": {},
            "required_reframe_actions": ["narrow universe"],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(intake_dir / "scope_canvas.yaml", {})

    result = run(
        ["python", str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "GO_TO_MANDATE" in result.stderr
    assert not (lineage_root / "01_mandate").exists()


def test_build_mandate_from_intake_creates_mandate_artifacts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_mandate_from_intake.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)

    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "approved_scope": {
                "market": "Binance perpetual",
                "data_source": "Binance UM futures klines",
                "universe": "top liquidity alts",
                "bar_size": "5m",
                "horizons": ["15m", "30m", "60m"],
                "target_task": "event-driven relative return study",
                "excluded_scope": ["low liquidity tails"],
            },
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {
            "market": "Binance perpetual",
            "data_source": "Binance UM futures klines",
            "instrument_type": "perpetual",
            "universe": "top liquidity alts",
            "bar_size": "5m",
            "holding_horizons": ["15m", "30m", "60m"],
            "target_task": "event-driven relative return study",
            "excluded_scope": ["low liquidity tails"],
            "budget_days": 10,
            "max_iterations": 3,
        },
    )
    (intake_dir / "research_question_set.md").write_text(
        "# Research Questions\n\n- Does BTC shock lead ALT follow-through?\n",
        encoding="utf-8",
    )
    (intake_dir / "qualification_scorecard.yaml").write_text("idea_id: btc_alt_transmission_v1\n", encoding="utf-8")
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))

    result = run(
        ["python", str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    mandate_dir = lineage_root / "01_mandate"
    assert (mandate_dir / "mandate.md").exists()
    assert (mandate_dir / "research_scope.md").exists()
    assert (mandate_dir / "time_split.json").exists()
    assert (mandate_dir / "parameter_grid.yaml").exists()
    assert (mandate_dir / "run_config.toml").exists()
    assert (mandate_dir / "artifact_catalog.md").exists()
    assert (mandate_dir / "field_dictionary.md").exists()
    assert "BTC drives price discovery for high-liquidity ALTs." in (mandate_dir / "mandate.md").read_text(
        encoding="utf-8"
    )
    assert "Data source: Binance UM futures klines" in (mandate_dir / "research_scope.md").read_text(
        encoding="utf-8"
    )
    assert 'data_source = "Binance UM futures klines"' in (mandate_dir / "run_config.toml").read_text(
        encoding="utf-8"
    )
    assert "Built mandate artifacts" in result.stdout


def test_build_mandate_from_intake_requires_confirmed_data_source_and_bar_size(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_mandate_from_intake.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)

    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "approved_scope": {
                "market": "Binance perpetual",
                "universe": "top liquidity alts",
                "target_task": "event-driven relative return study",
                "excluded_scope": ["low liquidity tails"],
            },
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {
            "market": "Binance perpetual",
            "instrument_type": "perpetual",
            "universe": "top liquidity alts",
            "bar_size": "",
            "holding_horizons": ["15m", "30m", "60m"],
            "target_task": "event-driven relative return study",
            "excluded_scope": ["low liquidity tails"],
            "budget_days": 10,
            "max_iterations": 3,
            "data_source": "",
        },
    )
    (intake_dir / "research_question_set.md").write_text(
        "# Research Questions\n\n- Does BTC shock lead ALT follow-through?\n",
        encoding="utf-8",
    )
    draft_payload = _mandate_freeze_draft(confirmed=True)
    draft_payload["groups"]["data_contract"]["draft"]["data_source"] = ""
    draft_payload["groups"]["data_contract"]["draft"]["bar_size"] = ""
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", draft_payload)

    result = run(
        ["python", str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "data_source" in result.stderr
    assert "bar_size" in result.stderr


def test_build_mandate_from_intake_requires_confirmed_freeze_groups(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_mandate_from_intake.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)

    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "approved_scope": {
                "market": "Binance perpetual",
                "data_source": "Binance UM futures klines",
                "bar_size": "5m",
            },
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {
            "market": "Binance perpetual",
            "data_source": "Binance UM futures klines",
            "bar_size": "5m",
        },
    )
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=False))
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n\n- TODO\n", encoding="utf-8")

    result = run(
        ["python", str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "mandate_freeze_draft" in result.stderr
    assert "research_intent" in result.stderr
