from pathlib import Path
from subprocess import run
import sys

import yaml

from tests.lineage_program_support import ensure_stage_program

def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _route_assessment(
    *,
    candidate_routes: list[str] | None = None,
    recommended_route: str = "cross_sectional_factor",
    why_not_other_routes: dict[str, list[str]] | None = None,
) -> dict:
    candidate_routes = candidate_routes or ["cross_sectional_factor", "time_series_signal"]
    why_not_other_routes = why_not_other_routes or {
        "time_series_signal": ["Single-asset direction is secondary to the ranking thesis."]
    }
    return {
        "candidate_routes": candidate_routes,
        "recommended_route": recommended_route,
        "why_recommended": ["Cross-asset ranking expresses the edge best."],
        "why_not_other_routes": why_not_other_routes,
        "route_risks": ["Universe breadth may still be tight."],
        "route_decision_pending": True,
    }


def _mandate_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "research_intent": {
                "confirmed": confirmed,
                "draft": {
                    "research_question": "Does BTC shock lead ALT follow-through?",
                    "primary_hypothesis": "BTC drives price discovery for high-liquidity ALTs.",
                    "counter_hypothesis": "Observed moves are only shared beta.",
                    "research_route": "cross_sectional_factor",
                    "factor_role": "standalone_alpha",
                    "factor_structure": "single_factor",
                    "portfolio_expression": "long_short_market_neutral",
                    "neutralization_policy": "group_neutral",
                    "target_strategy_reference": "",
                    "group_taxonomy_reference": "sector_bucket_v1",
                    "excluded_routes": ["time_series_signal"],
                    "route_rationale": [
                        "The thesis is expressed as cross-asset ranking rather than single-asset direction."
                    ],
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


def _data_ready_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "extraction_contract": {
                "confirmed": confirmed,
                "draft": {
                    "data_source": "Binance UM futures klines",
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
                    "bad_price_policy": "flag bad prices",
                    "outlier_policy": "flag outliers only",
                    "dedupe_rule": "dedupe on symbol plus close_time",
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
                    "layer_boundary_note": "shared layer only, no thesis-specific signals",
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
                    "frozen_inputs_note": "signal stage must consume frozen outputs",
                },
                "missing_items": [],
            },
        }
    }


def _signal_ready_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "signal_expression": {
                "confirmed": confirmed,
                "draft": {
                    "baseline_signal": "btc_alt_residual_response",
                    "upstream_inputs": ["benchmark_residual", "topic_basket_state"],
                    "state_fields": ["btc_residual_z"],
                    "filter_fields": ["alt_liquidity_bucket"],
                },
                "missing_items": [],
            },
            "param_identity": {
                "confirmed": confirmed,
                "draft": {
                    "param_id": "baseline_v1",
                    "parameter_values": {
                        "event_window": "15m",
                        "response_horizon": "30m",
                        "normalization": "residual_z_v1",
                    },
                    "identity_note": "baseline only, no search batch",
                },
                "missing_items": [],
            },
            "time_semantics": {
                "confirmed": confirmed,
                "draft": {
                    "signal_timestamp": "close_time",
                    "label_alignment": "future returns start after the completed signal bar",
                    "no_lookahead_guardrail": "labels use only completed bars",
                },
                "missing_items": [],
            },
            "signal_schema": {
                "confirmed": confirmed,
                "draft": {
                    "timeseries_schema": ["ts", "symbol", "param_id", "signal_value"],
                    "quality_fields": ["coverage_rate", "low_sample_rate", "pair_missing_rate"],
                    "schema_note": "baseline signal schema frozen",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["param_manifest.csv", "params/", "signal_coverage.csv"],
                    "doc_artifacts": [
                        "signal_coverage.md",
                        "signal_coverage_summary.md",
                        "signal_contract.md",
                        "signal_fields_contract.md",
                    ],
                    "consumer_stage": "train_calibration",
                },
                "missing_items": [],
            },
        }
    }


def test_scaffold_idea_intake_creates_stage_templates(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "scaffold_idea_intake.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    intake_dir = lineage_root / "00_idea_intake"
    assert intake_dir.exists()
    assert (intake_dir / "idea_brief.md").exists()
    assert (intake_dir / "intake_interview.md").exists()
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
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "GO_TO_MANDATE" in result.stderr
    assert not (lineage_root / "01_mandate" / "author" / "formal" / "mandate.md").exists()


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
                "route_assessment": _route_assessment(),
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
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    mandate_dir = lineage_root / "01_mandate"
    mandate_formal_dir = mandate_dir / "author" / "formal"
    assert (mandate_formal_dir / "mandate.md").exists()
    assert (mandate_formal_dir / "research_scope.md").exists()
    assert (mandate_formal_dir / "time_split.json").exists()
    assert (mandate_formal_dir / "parameter_grid.yaml").exists()
    assert (mandate_formal_dir / "run_config.toml").exists()
    assert (mandate_formal_dir / "research_route.yaml").exists()
    assert (mandate_formal_dir / "artifact_catalog.md").exists()
    assert (mandate_formal_dir / "field_dictionary.md").exists()
    route_payload = yaml.safe_load((mandate_formal_dir / "research_route.yaml").read_text(encoding="utf-8"))
    assert route_payload["research_route"] == "cross_sectional_factor"
    assert route_payload["factor_role"] == "standalone_alpha"
    assert route_payload["factor_structure"] == "single_factor"
    assert route_payload["portfolio_expression"] == "long_short_market_neutral"
    assert route_payload["neutralization_policy"] == "group_neutral"
    assert route_payload["group_taxonomy_reference"] == "sector_bucket_v1"
    assert route_payload["excluded_routes"] == ["time_series_signal"]
    assert "BTC drives price discovery for high-liquidity ALTs." in (mandate_formal_dir / "mandate.md").read_text(
        encoding="utf-8"
    )
    assert "数据来源: Binance UM futures klines" in (mandate_formal_dir / "research_scope.md").read_text(
        encoding="utf-8"
    )
    assert 'data_source = "Binance UM futures klines"' in (mandate_formal_dir / "run_config.toml").read_text(
        encoding="utf-8"
    )
    assert "Built mandate artifacts" in result.stdout


def test_build_mandate_from_intake_requires_route_assessment_for_go_to_mandate(tmp_path: Path) -> None:
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
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "route_assessment" in result.stderr
    assert not (lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml").exists()


def test_build_mandate_from_intake_rejects_unsupported_recommended_route(tmp_path: Path) -> None:
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
            "route_assessment": _route_assessment(
                candidate_routes=["cross_sectional_factor", "event_trigger"],
                why_not_other_routes={"event_trigger": ["The thesis is not event-first."]},
            ),
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
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "unsupported route: event_trigger" in result.stderr
    assert not (lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml").exists()


def test_build_mandate_from_intake_rejects_excluded_routes_mismatch(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_mandate_from_intake.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)

    freeze_draft = _mandate_freeze_draft(confirmed=True)
    freeze_draft["groups"]["research_intent"]["draft"]["excluded_routes"] = ["cross_sectional_factor"]

    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "route_assessment": _route_assessment(),
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
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", freeze_draft)
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "excluded_routes" in result.stderr
    assert not (lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml").exists()


def test_build_mandate_from_intake_accepts_extended_standalone_alpha_portfolio_expressions(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_mandate_from_intake.py"

    for portfolio_expression in [
        "short_only_rank",
        "benchmark_relative_long_only",
        "group_relative_long_short",
    ]:
        lineage_root = tmp_path / portfolio_expression / "outputs" / "btc_alt_transmission_v1"
        intake_dir = lineage_root / "00_idea_intake"
        intake_dir.mkdir(parents=True)

        draft_payload = _mandate_freeze_draft(confirmed=True)
        draft_payload["groups"]["research_intent"]["draft"]["portfolio_expression"] = portfolio_expression

        _write_yaml(
            intake_dir / "idea_gate_decision.yaml",
            {
                "idea_id": "btc_alt_transmission_v1",
                "verdict": "GO_TO_MANDATE",
                "why": ["variables are observable"],
                "route_assessment": _route_assessment(),
                "approved_scope": {
                    "market": "Binance perpetual",
                    "data_source": "Binance UM futures klines",
                    "universe": "top liquidity alts",
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
        _write_yaml(intake_dir / "mandate_freeze_draft.yaml", draft_payload)
        ensure_stage_program(lineage_root, "mandate")

        result = run(
            [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
            check=False,
            capture_output=True,
            text=True,
            cwd=repo_root,
        )

        assert result.returncode == 0, result.stderr
        route_payload = yaml.safe_load(
            (lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml").read_text(encoding="utf-8")
        )
        assert route_payload["portfolio_expression"] == portfolio_expression


def test_build_mandate_from_intake_accepts_filter_and_overlay_expressions_for_non_standalone_roles(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_mandate_from_intake.py"

    cases = [
        ("regime_filter", "target_strategy_filter"),
        ("combo_filter", "target_strategy_filter"),
        ("combo_filter", "target_strategy_overlay"),
    ]

    for factor_role, portfolio_expression in cases:
        lineage_root = tmp_path / f"{factor_role}-{portfolio_expression}" / "outputs" / "btc_alt_transmission_v1"
        intake_dir = lineage_root / "00_idea_intake"
        intake_dir.mkdir(parents=True)

        draft_payload = _mandate_freeze_draft(confirmed=True)
        draft_payload["groups"]["research_intent"]["draft"]["factor_role"] = factor_role
        draft_payload["groups"]["research_intent"]["draft"]["portfolio_expression"] = portfolio_expression
        draft_payload["groups"]["research_intent"]["draft"]["target_strategy_reference"] = "trend_combo_v1"

        _write_yaml(
            intake_dir / "idea_gate_decision.yaml",
            {
                "idea_id": "btc_alt_transmission_v1",
                "verdict": "GO_TO_MANDATE",
                "why": ["variables are observable"],
                "route_assessment": _route_assessment(),
                "approved_scope": {
                    "market": "Binance perpetual",
                    "data_source": "Binance UM futures klines",
                    "universe": "top liquidity alts",
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
        _write_yaml(intake_dir / "mandate_freeze_draft.yaml", draft_payload)
        ensure_stage_program(lineage_root, "mandate")

        result = run(
            [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
            check=False,
            capture_output=True,
            text=True,
            cwd=repo_root,
        )

        assert result.returncode == 0, result.stderr


def test_build_mandate_from_intake_rejects_invalid_factor_role_and_portfolio_expression_pairs(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_mandate_from_intake.py"

    cases = [
        ("standalone_alpha", "target_strategy_filter"),
        ("standalone_alpha", "target_strategy_overlay"),
        ("regime_filter", "target_strategy_overlay"),
        ("regime_filter", "long_short_market_neutral"),
        ("combo_filter", "long_only_rank"),
    ]

    for factor_role, portfolio_expression in cases:
        lineage_root = tmp_path / f"invalid-{factor_role}-{portfolio_expression}" / "outputs" / "btc_alt_transmission_v1"
        intake_dir = lineage_root / "00_idea_intake"
        intake_dir.mkdir(parents=True)

        draft_payload = _mandate_freeze_draft(confirmed=True)
        draft_payload["groups"]["research_intent"]["draft"]["factor_role"] = factor_role
        draft_payload["groups"]["research_intent"]["draft"]["portfolio_expression"] = portfolio_expression
        draft_payload["groups"]["research_intent"]["draft"]["target_strategy_reference"] = "trend_combo_v1"

        _write_yaml(
            intake_dir / "idea_gate_decision.yaml",
            {
                "idea_id": "btc_alt_transmission_v1",
                "verdict": "GO_TO_MANDATE",
                "why": ["variables are observable"],
                "route_assessment": _route_assessment(),
                "approved_scope": {
                    "market": "Binance perpetual",
                    "data_source": "Binance UM futures klines",
                    "universe": "top liquidity alts",
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
        _write_yaml(intake_dir / "mandate_freeze_draft.yaml", draft_payload)
        ensure_stage_program(lineage_root, "mandate")

        result = run(
            [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
            check=False,
            capture_output=True,
            text=True,
            cwd=repo_root,
        )

        assert result.returncode != 0
        assert "portfolio_expression" in result.stderr


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
                "route_assessment": _route_assessment(),
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
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "data_source" in result.stderr
    assert "bar_size" in result.stderr


def test_build_data_ready_from_mandate_creates_data_ready_artifacts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_data_ready_from_mandate.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    mandate_dir = lineage_root / "01_mandate"
    mandate_formal_dir = mandate_dir / "author" / "formal"
    data_ready_dir = lineage_root / "02_data_ready"
    data_ready_draft_dir = data_ready_dir / "author" / "draft"
    data_ready_formal_dir = data_ready_dir / "author" / "formal"
    mandate_formal_dir.mkdir(parents=True)
    data_ready_draft_dir.mkdir(parents=True)

    for name, content in {
        "mandate.md": "# Mandate\n",
        "research_scope.md": "# Research Scope\n- Data source: Binance UM futures klines\n- Bar size: 5m\n",
        "time_split.json": "{}\n",
        "parameter_grid.yaml": "parameters: []\n",
        "run_config.toml": 'stage = "mandate"\nlineage_id = "btc_alt_transmission_v1"\n',
        "artifact_catalog.md": "# Artifact Catalog\n",
        "field_dictionary.md": "# Field Dictionary\n",
    }.items():
        (mandate_formal_dir / name).write_text(content, encoding="utf-8")

    _write_yaml(data_ready_draft_dir / "data_ready_freeze_draft.yaml", _data_ready_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "data_ready")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    assert (data_ready_formal_dir / "aligned_bars").exists()
    assert (data_ready_formal_dir / "rolling_stats").exists()
    assert (data_ready_formal_dir / "pair_stats").exists()
    assert (data_ready_formal_dir / "benchmark_residual").exists()
    assert (data_ready_formal_dir / "topic_basket_state").exists()
    assert (data_ready_formal_dir / "dataset_manifest.json").exists()
    assert (data_ready_formal_dir / "data_contract.md").exists()
    assert (data_ready_formal_dir / "run_manifest.json").exists()
    assert (data_ready_formal_dir / "rebuild_data_ready.py").exists()
    assert (data_ready_formal_dir / "artifact_catalog.md").exists()
    assert "Built data_ready artifacts" in result.stdout


def test_build_signal_ready_from_data_ready_creates_signal_ready_artifacts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_signal_ready_from_data_ready.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    data_ready_dir = lineage_root / "02_data_ready"
    data_ready_formal_dir = data_ready_dir / "author" / "formal"
    signal_ready_dir = lineage_root / "03_signal_ready"
    signal_ready_draft_dir = signal_ready_dir / "author" / "draft"
    signal_ready_formal_dir = signal_ready_dir / "author" / "formal"
    data_ready_formal_dir.mkdir(parents=True)
    signal_ready_draft_dir.mkdir(parents=True)

    for name in [
        "qc_report.parquet",
        "dataset_manifest.json",
        "validation_report.md",
        "data_contract.md",
        "dedupe_rule.md",
        "universe_summary.md",
        "universe_exclusions.csv",
        "universe_exclusions.md",
        "data_ready_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (data_ready_formal_dir / name).write_text("ok\n", encoding="utf-8")
    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (data_ready_formal_dir / name).mkdir()

    _write_yaml(signal_ready_draft_dir / "signal_ready_freeze_draft.yaml", _signal_ready_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "signal_ready")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    assert (signal_ready_formal_dir / "param_manifest.csv").exists()
    assert (signal_ready_formal_dir / "params").exists()
    assert (signal_ready_formal_dir / "signal_coverage.csv").exists()
    assert (signal_ready_formal_dir / "signal_contract.md").exists()
    assert (signal_ready_formal_dir / "signal_fields_contract.md").exists()
    assert (signal_ready_formal_dir / "artifact_catalog.md").exists()
    assert "Built signal_ready artifacts" in result.stdout


def test_build_data_ready_from_mandate_requires_confirmed_freeze_groups(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_data_ready_from_mandate.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    mandate_dir = lineage_root / "01_mandate"
    mandate_formal_dir = mandate_dir / "author" / "formal"
    data_ready_dir = lineage_root / "02_data_ready"
    data_ready_draft_dir = data_ready_dir / "author" / "draft"
    mandate_formal_dir.mkdir(parents=True)
    data_ready_draft_dir.mkdir(parents=True)

    for name, content in {
        "mandate.md": "# Mandate\n",
        "research_scope.md": "# Research Scope\n- Data source: Binance UM futures klines\n- Bar size: 5m\n",
        "time_split.json": "{}\n",
        "parameter_grid.yaml": "parameters: []\n",
        "run_config.toml": 'stage = "mandate"\nlineage_id = "btc_alt_transmission_v1"\n',
        "artifact_catalog.md": "# Artifact Catalog\n",
        "field_dictionary.md": "# Field Dictionary\n",
    }.items():
        (mandate_formal_dir / name).write_text(content, encoding="utf-8")

    _write_yaml(data_ready_draft_dir / "data_ready_freeze_draft.yaml", _data_ready_freeze_draft(confirmed=False))

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "data_ready_freeze_draft.yaml has unconfirmed groups" in result.stderr
    assert "extraction_contract" in result.stderr


def test_build_signal_ready_from_data_ready_requires_confirmed_freeze_groups(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_signal_ready_from_data_ready.py"
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    data_ready_dir = lineage_root / "02_data_ready"
    data_ready_formal_dir = data_ready_dir / "author" / "formal"
    signal_ready_dir = lineage_root / "03_signal_ready"
    signal_ready_draft_dir = signal_ready_dir / "author" / "draft"
    data_ready_formal_dir.mkdir(parents=True)
    signal_ready_draft_dir.mkdir(parents=True)

    for name in [
        "qc_report.parquet",
        "dataset_manifest.json",
        "validation_report.md",
        "data_contract.md",
        "dedupe_rule.md",
        "universe_summary.md",
        "universe_exclusions.csv",
        "universe_exclusions.md",
        "data_ready_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (data_ready_formal_dir / name).write_text("ok\n", encoding="utf-8")
    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (data_ready_formal_dir / name).mkdir()

    _write_yaml(signal_ready_draft_dir / "signal_ready_freeze_draft.yaml", _signal_ready_freeze_draft(confirmed=False))

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "signal_ready_freeze_draft.yaml has unconfirmed groups" in result.stderr
    assert "signal_expression" in result.stderr


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
                "route_assessment": _route_assessment(),
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
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, str(script_path), "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert "mandate_freeze_draft" in result.stderr
    assert "research_intent" in result.stderr
