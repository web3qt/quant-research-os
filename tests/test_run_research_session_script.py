from pathlib import Path
from subprocess import run

import yaml


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "research_intent": {
                "confirmed": confirmed,
                "draft": {
                    "research_question": "Does BTC lead ALTs?",
                    "primary_hypothesis": "BTC leads price discovery.",
                    "counter_hypothesis": "Shared beta only.",
                },
            },
            "scope_contract": {
                "confirmed": confirmed,
                "draft": {"market": "binance perp", "universe": "high liquidity alts", "target_task": "study"},
            },
            "data_contract": {
                "confirmed": confirmed,
                "draft": {
                    "data_source": "binance um futures klines",
                    "bar_size": "5m",
                    "holding_horizons": ["15m", "30m"],
                    "timestamp_semantics": "close-to-close utc bars",
                    "no_lookahead_guardrail": "labels use completed bars only",
                },
            },
            "execution_contract": {
                "confirmed": confirmed,
                "draft": {
                    "time_split_note": "freeze windows before signal work",
                    "parameter_boundary_note": "event-window params only",
                    "artifact_contract_note": "register every machine-readable artifact",
                    "crowding_capacity_note": "reuse one liquidity proxy later",
                },
            },
        }
    }


def _data_ready_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "extraction_contract": {
                "confirmed": confirmed,
                "draft": {
                    "data_source": "binance um futures klines",
                    "time_boundary": "2024-01-01 to 2024-12-31",
                    "primary_time_key": "close_time",
                    "bar_size": "5m",
                },
                "missing_items": [],
            },
            "quality_semantics": {
                "confirmed": confirmed,
                "draft": {
                    "missing_policy": "preserve nulls explicitly",
                    "stale_policy": "mark stale bars",
                    "bad_price_policy": "flag only",
                    "outlier_policy": "flag only",
                    "dedupe_rule": "dedupe by symbol and close_time",
                },
                "missing_items": [],
            },
            "universe_admission": {
                "confirmed": confirmed,
                "draft": {
                    "benchmark_symbol": "BTCUSDT",
                    "coverage_floor": "99.0%",
                    "admission_rule": "exclude symbols below coverage floor",
                    "exclusion_reporting": "write csv and md reports",
                },
                "missing_items": [],
            },
            "shared_derived_layer": {
                "confirmed": confirmed,
                "draft": {
                    "shared_outputs": [
                        "rolling_stats",
                        "pair_stats",
                        "benchmark_residual",
                        "topic_basket_state",
                    ],
                    "layer_boundary_note": "shared only, not signal layer",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "aligned_bars/",
                        "rolling_stats/",
                        "pair_stats/",
                        "benchmark_residual/",
                        "topic_basket_state/",
                        "qc_report.parquet",
                        "dataset_manifest.json",
                    ],
                    "consumer_stage": "signal_ready",
                    "frozen_inputs_note": "downstream consumes frozen outputs",
                },
                "missing_items": [],
            },
        }
    }


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


def test_run_research_session_stops_at_pending_confirmation_when_intake_admitted(tmp_path: Path) -> None:
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
            "approved_scope": {
                "market": "binance perp",
                "data_source": "binance um futures klines",
                "bar_size": "5m",
            },
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {"market": "binance perp", "data_source": "binance um futures klines", "bar_size": "5m"},
    )
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _freeze_draft(confirmed=False))
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
    assert "Current stage: mandate_confirmation_pending" in result.stdout
    assert "Next action: Complete mandate freeze group: research_intent" in result.stdout
    assert not (lineage_root / "01_mandate" / "mandate.md").exists()


def test_run_research_session_builds_mandate_only_after_explicit_confirmation(tmp_path: Path) -> None:
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
            "approved_scope": {
                "market": "binance perp",
                "data_source": "binance um futures klines",
                "bar_size": "5m",
            },
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {"market": "binance perp", "data_source": "binance um futures klines", "bar_size": "5m"},
    )
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _freeze_draft(confirmed=True))
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n\n- TODO\n", encoding="utf-8")

    confirm_result = run(
        [
            "python",
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-mandate",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert confirm_result.returncode == 0

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
    assert "Current stage: data_ready_confirmation_pending" in result.stdout


def test_run_research_session_reports_data_ready_next_group_after_mandate_review_complete(
    tmp_path: Path,
) -> None:
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
    assert "Current stage: data_ready_confirmation_pending" in result.stdout
    assert "Next action: Complete data_ready freeze group: extraction_contract" in result.stdout


def test_run_research_session_builds_data_ready_only_after_explicit_confirmation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = lineage_root / "02_data_ready"
    mandate_dir.mkdir(parents=True)
    data_ready_dir.mkdir(parents=True)
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
    _write_yaml(data_ready_dir / "data_ready_freeze_draft.yaml", _data_ready_freeze_draft(confirmed=True))

    confirm_result = run(
        [
            "python",
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-data-ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert confirm_result.returncode == 0

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
    assert "Current stage: data_ready_review" in result.stdout
    assert (lineage_root / "02_data_ready" / "data_contract.md").exists()
