from pathlib import Path
from subprocess import run
import sys
import json
import os

import yaml

from tests.lineage_program_support import ensure_stage_program, write_fake_stage_provenance

def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _stage_output_path(stage_dir: Path, name: str) -> Path:
    if name in {"latest_review_pack.yaml", "stage_gate_review.yaml", "stage_completion_certificate.yaml"}:
        path = stage_dir / "review" / "closure" / name
    else:
        path = stage_dir / "author" / "formal" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _stage_draft_path(stage_dir: Path, name: str) -> Path:
    path = stage_dir / "author" / "draft" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _route_assessment() -> dict:
    return {
        "candidate_routes": ["cross_sectional_factor", "time_series_signal"],
        "recommended_route": "cross_sectional_factor",
        "why_recommended": ["Cross-asset sorting is the primary expression."],
        "why_not_other_routes": {"time_series_signal": ["Single-asset direction is secondary."]},
        "route_risks": ["Universe breadth may be limited."],
        "route_decision_pending": True,
    }


def _write_stage_completion_certificate(
    path: Path,
    *,
    stage_status: str = "PASS",
    final_verdict: str | None = None,
) -> None:
    target_path = path
    if path.name == "stage_completion_certificate.yaml" and path.parent.name != "closure":
        target_path = path.parent / "review" / "closure" / path.name
    _write_yaml(
        target_path,
        {
            "stage_status": stage_status,
            "final_verdict": final_verdict or stage_status,
        },
    )


def _write_display_decision(stage_dir: Path, *, stage: str) -> None:
    # Dedicated stage display has been removed from the formal workflow.
    return None


def _write_next_stage_confirmation(stage_dir: Path, *, stage: str) -> None:
    _write_yaml(
        _stage_draft_path(stage_dir, "next_stage_transition_approval.yaml"),
        {
            "lineage_id": stage_dir.parent.name,
            "stage_id": stage,
            "decision": "CONFIRM_NEXT_STAGE",
            "approved_by": "tester",
            "approved_at": "2026-04-06T10:05:00Z",
            "source_stage": f"{stage}_next_stage_confirmation_pending",
        },
    )


def _write_fake_parquet(path: Path) -> None:
    path.write_bytes(b"PAR1test-payloadPAR1")


def _prepare_real_backtest_engine_outputs(backtest_dir: Path) -> None:
    (_stage_output_path(backtest_dir, "engine_compare.csv")).write_text(
        "\n".join(
            [
                "engine,gross_return,net_return,max_drawdown,semantic_gap",
                "vectorbt,0.12,0.09,-0.08,false",
                "backtrader,0.119,0.089,-0.081,false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for engine_name in ("vectorbt", "backtrader"):
        engine_dir = _stage_output_path(backtest_dir, engine_name)
        engine_dir.mkdir(parents=True, exist_ok=True)
        for name in (
            "trades.parquet",
            "symbol_metrics.parquet",
            "portfolio_timeseries.parquet",
            "portfolio_summary.parquet",
        ):
            _write_fake_parquet(engine_dir / name)


def _freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "research_intent": {
                "confirmed": confirmed,
                "draft": {
                    "research_question": "Does BTC lead ALTs?",
                    "primary_hypothesis": "BTC leads price discovery.",
                    "counter_hypothesis": "Shared beta only.",
                    "research_route": "cross_sectional_factor",
                    "factor_role": "standalone_alpha",
                    "factor_structure": "single_factor",
                    "portfolio_expression": "long_short_market_neutral",
                    "neutralization_policy": "group_neutral",
                    "target_strategy_reference": "",
                    "group_taxonomy_reference": "sector_bucket_v1",
                    "excluded_routes": ["time_series_signal"],
                    "route_rationale": ["Cross-asset ranking is the primary expression."],
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
                    "label_alignment": "future returns start after the completed bar",
                    "no_lookahead_guardrail": "labels use only completed bars",
                },
                "missing_items": [],
            },
            "signal_schema": {
                "confirmed": confirmed,
                "draft": {
                    "timeseries_schema": ["ts", "symbol", "param_id", "signal_value"],
                    "quality_fields": ["coverage_rate", "low_sample_rate", "pair_missing_rate"],
                    "schema_note": "baseline-only signal schema",
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


def _train_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "train_window_source": "time_split.json::train",
                    "train_window_note": "Freeze train split from mandate only.",
                    "leakage_guardrail": "Do not inspect test or backtest while freezing train.",
                },
                "missing_items": [],
            },
            "threshold_contract": {
                "confirmed": confirmed,
                "draft": {
                    "threshold_targets": ["signal_value"],
                    "threshold_rule": "Estimate thresholds on train only.",
                    "regime_cut_rule": "Freeze regime buckets on train only.",
                    "frozen_outputs_note": "Downstream test reuses frozen train outputs only.",
                },
                "missing_items": [],
            },
            "quality_filters": {
                "confirmed": confirmed,
                "draft": {
                    "quality_metrics": ["coverage_rate"],
                    "filter_rule": "Reject low coverage pairs on train.",
                    "symbol_param_admission_rule": "Only train-admissible pairs may proceed.",
                    "audit_note": "Audit-only observations remain outside formal gate.",
                },
                "missing_items": [],
            },
            "param_governance": {
                "confirmed": confirmed,
                "draft": {
                    "candidate_param_ids": ["baseline_v1"],
                    "kept_param_ids": ["baseline_v1"],
                    "rejected_param_ids": [],
                    "selection_rule": "Keep baseline-only candidate set.",
                    "reject_log_note": "No rejected params in baseline-only freeze.",
                    "coarse_to_fine_note": "No extra parameter expansion in first wave.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "train_thresholds.json",
                        "train_quality.parquet",
                        "train_param_ledger.csv",
                        "train_rejects.csv",
                    ],
                    "consumer_stage": "test_evidence",
                    "reuse_constraints": "Test consumes train outputs as frozen inputs.",
                },
                "missing_items": [],
            },
        }
    }


def _test_evidence_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "test_window_source": "time_split.json::test",
                    "test_window_note": "Freeze test split from mandate only.",
                    "train_reuse_note": "Reuse train outputs without re-estimation.",
                },
                "missing_items": [],
            },
            "formal_gate_contract": {
                "confirmed": confirmed,
                "draft": {
                    "selected_param_ids": ["baseline_v1"],
                    "candidate_best_h": ["15m", "30m"],
                    "best_h": "30m",
                    "formal_gate_note": "Formal gate uses frozen train outputs only.",
                    "threshold_reuse_note": "No train threshold re-estimation in test.",
                },
                "missing_items": [],
            },
            "admissibility_contract": {
                "confirmed": confirmed,
                "draft": {
                    "selected_symbols": ["ETHUSDT"],
                    "admissibility_rule": "Admit only symbols passing formal test gate.",
                    "rejection_rule": "Reject symbols failing structure continuation checks.",
                    "summary_note": "Whitelist is frozen for downstream backtest.",
                },
                "missing_items": [],
            },
            "audit_contract": {
                "confirmed": confirmed,
                "draft": {
                    "audit_items": ["HAC t value"],
                    "formal_vs_audit_boundary": "Audit evidence stays separate from formal gate.",
                    "crowding_scope": "Review overlap against crowded benchmarks.",
                    "condition_analysis_note": "Condition analysis remains explanatory only.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "report_by_h.parquet",
                        "symbol_summary.parquet",
                        "admissibility_report.parquet",
                        "test_gate_table.csv",
                        "selected_symbols_test.csv",
                        "selected_symbols_test.parquet",
                        "frozen_spec.json",
                    ],
                    "consumer_stage": "backtest_ready",
                    "frozen_spec_note": "Backtest must consume frozen whitelist and best_h only.",
                },
                "missing_items": [],
            },
        }
    }


def _backtest_ready_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "execution_policy": {
                "confirmed": confirmed,
                "draft": {
                    "selected_symbols": ["ETHUSDT"],
                    "best_h": "30m",
                    "entry_rule": "Enter on frozen continuation signal.",
                    "exit_rule": "Exit at frozen best_h or risk stop.",
                    "cost_model_note": "Use formal fee and slippage schedule only.",
                },
                "missing_items": [],
            },
            "portfolio_policy": {
                "confirmed": confirmed,
                "draft": {
                    "position_sizing_rule": "Equal-notional baseline sizing.",
                    "capital_base": "100000 USD",
                    "max_concurrent_positions": "5",
                    "combo_scope_note": "Baseline combo only.",
                },
                "missing_items": [],
            },
            "risk_overlay": {
                "confirmed": confirmed,
                "draft": {
                    "risk_controls": ["kill_switch"],
                    "stop_or_kill_switch_rule": "Disable entries under exchange anomalies.",
                    "abnormal_performance_sanity_check": "Required if net results look abnormal.",
                    "reservation_note": "Capacity assumptions may still need hardening.",
                },
                "missing_items": [],
            },
            "engine_contract": {
                "confirmed": confirmed,
                "draft": {
                    "required_engines": ["vectorbt", "backtrader"],
                    "semantic_compare_rule": "Both engines must agree on semantic_gap = false.",
                    "repro_rule": "Same frozen config must reproduce stable aggregates.",
                    "engine_scope_note": "Both engines consume the same frozen whitelist and best_h.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "engine_compare.csv",
                        "vectorbt/",
                        "backtrader/",
                        "strategy_combo_ledger.csv",
                    ],
                    "consumer_stage": "holdout_validation",
                    "frozen_config_note": "Holdout must consume frozen backtest config only.",
                },
                "missing_items": [],
            },
        }
    }


def _holdout_validation_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "holdout_window_source": "time_split.json::holdout",
                    "window_plan": ["single_window", "merged_window"],
                    "window_note": "Freeze final untouched validation window only.",
                    "no_redefinition_guardrail": "Do not redefine the research question in holdout.",
                },
                "missing_items": [],
            },
            "reuse_contract": {
                "confirmed": confirmed,
                "draft": {
                    "frozen_config_source": "06_backtest/backtest_frozen_config.json",
                    "selected_combo_source": "06_backtest/selected_strategy_combo.json",
                    "selected_symbols": ["ETHUSDT"],
                    "best_h": "30m",
                    "no_reestimate_rule": "Do not re-estimate parameters in holdout.",
                    "no_whitelist_change_rule": "Do not change whitelist in holdout.",
                },
                "missing_items": [],
            },
            "drift_audit": {
                "confirmed": confirmed,
                "draft": {
                    "required_views": ["single_window", "merged_window"],
                    "direction_flip_rule": "Escalate unexplained direction flips.",
                    "sparse_activity_rule": "Explain sparse trading without changing frozen rules.",
                    "explanatory_note": "Low activity may be normal under frozen filters.",
                },
                "missing_items": [],
            },
            "failure_governance": {
                "confirmed": confirmed,
                "draft": {
                    "retryable_conditions": ["execution defect"],
                    "no_go_conditions": ["unexplained direction flip"],
                    "child_lineage_trigger": "Open child lineage when a new mechanism is needed.",
                    "rollback_boundary": "Only holdout rerun and reporting may be changed in place.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "holdout_run_manifest.json",
                        "holdout_backtest_compare.csv",
                        "window_results/",
                    ],
                    "consumer_stage": "promotion_decision",
                    "field_doc_rule": "Every machine artifact requires field documentation.",
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
            sys.executable,
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

    assert result.returncode == 2
    lineage_root = outputs_root / "btc_leads_high_liquidity_alts_after_shock_events"
    assert (lineage_root / "00_idea_intake").exists()
    assert "📍 Current stage: idea_intake_confirmation_pending" in result.stdout
    assert "🧭 Current orchestrator: qros-research-session" in result.stdout
    assert "🔨 Current active skill: qros-idea-intake-author" in result.stdout


def test_run_research_session_supports_json_output(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"

    result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--raw-idea",
            "BTC leads high-liquidity alts after shock events",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["current_orchestrator"] == "qros-research-session"
    assert payload["current_stage"] == "idea_intake_confirmation_pending"
    assert payload["current_skill"] == "qros-idea-intake-author"
    assert payload["lineage_root"].endswith("btc_leads_high_liquidity_alts_after_shock_events")
    assert payload["lineage_mode"] == "fresh_start"
    assert "fresh lineage slug" in payload["lineage_selection_reason"]
    assert "reflection" not in payload
    assert "🧭" not in result.stdout


def test_run_research_session_blocks_implicit_resume_for_existing_same_slug_raw_idea_in_cli(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    mandate_dir = lineage_root / "01_mandate"
    mandate_dir.mkdir(parents=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")

    result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--raw-idea",
            "BTC leads ALTs",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 2
    assert "📍 Current stage: idea_intake_confirmation_pending" in result.stdout
    assert "🧬 Lineage mode: resume_blocked_existing_slug" in result.stdout
    assert "Resume blocked for existing lineage btc_leads_alts" in result.stdout
    assert "--lineage-id btc_leads_alts" in result.stdout


def test_run_research_session_explicit_lineage_id_resume_is_visible_in_json(tmp_path: Path) -> None:
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
            "verdict": "NEEDS_REFRAME",
            "why": ["scope unclear"],
            "approved_scope": {},
        },
    )

    result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["lineage_mode"] == "explicit_resume"
    assert "Explicit lineage_id btc_leads_alts" in payload["lineage_selection_reason"]


def test_run_research_session_supports_snapshot_output(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"

    result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--raw-idea",
            "BTC leads high-liquidity alts after shock events",
            "--snapshot",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["fixture_id"] == "btc_leads_high_liquidity_alts_after_shock_events"
    assert payload["route_skill"] == "qros-idea-intake-author"
    assert payload["stage_id"] == "idea_intake"
    assert payload["session_stage"] == "idea_intake_confirmation_pending"
    assert payload["formal_decision"] == "IDEA_INTAKE_PENDING_CONFIRMATION"
    assert "artifact_catalog.md" in payload["required_artifacts"]
    assert "scripts/run_research_session.py" in payload["evidence_refs"]
    assert "🧭" not in result.stdout
    assert "Data Ready Reflection" not in result.stdout


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
            "route_assessment": _route_assessment(),
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
            sys.executable,
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

    assert result.returncode == 2
    assert "Current stage: idea_intake_confirmation_pending" in result.stdout
    assert "CONFIRM_IDEA_INTAKE" in result.stdout
    assert "Why now:" in result.stdout
    assert "- qualified" in result.stdout
    assert "Open risks:" in result.stdout
    assert "- rollback_target remains 00_idea_intake" in result.stdout
    assert not (_stage_output_path(lineage_root / "01_mandate", "mandate.md")).exists()


def test_run_research_session_accepts_explicit_intake_confirmation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)

    result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-intake",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 2
    assert (intake_dir / "idea_intake_transition_approval.yaml").exists()
    assert "Confirmation recorded: CONFIRM_IDEA_INTAKE" in result.stdout
    assert "Confirmation did not advance the workflow because intake gate requirements are still incomplete." in result.stdout


def test_run_research_session_confirm_intake_advances_to_mandate_confirmation_when_gate_ready(tmp_path: Path) -> None:
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
            "route_assessment": _route_assessment(),
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

    result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-intake",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 2
    assert "Confirmation recorded: CONFIRM_IDEA_INTAKE" in result.stdout
    assert "Confirmation advanced the workflow." in result.stdout
    assert "Current stage: mandate_confirmation_pending" in result.stdout


def test_run_research_session_requires_route_assessment_before_mandate_pending(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_intake_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_IDEA_INTAKE",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "idea_intake_interview",
        },
    )
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
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n\n- TODO\n", encoding="utf-8")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 2
    assert "Current stage: idea_intake" in result.stdout
    assert "route_assessment" in result.stdout
    assert "Research route:" not in result.stdout
    assert not (_stage_output_path(lineage_root / "01_mandate", "mandate.md")).exists()


def test_run_research_session_builds_mandate_only_after_explicit_confirmation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_intake_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_IDEA_INTAKE",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "idea_intake_interview",
        },
    )
    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_leads_alts",
            "verdict": "GO_TO_MANDATE",
            "why": ["qualified"],
            "route_assessment": _route_assessment(),
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
    ensure_stage_program(lineage_root, "mandate")

    confirm_result = run(
        [
            sys.executable,
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

    assert confirm_result.returncode == 7

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 7
    assert "📍 Current stage: mandate_review_confirmation_pending" in result.stdout
    assert "▶ Next action: Run with --confirm-review or reply CONFIRM_REVIEW <lineage_id>" in result.stdout
    assert "Research route: cross_sectional_factor" in result.stdout
    assert (_stage_output_path(lineage_root / "01_mandate", "mandate.md")).exists()


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
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 7
    assert "📍 Current stage: mandate_review_confirmation_pending" in result.stdout


def test_run_research_session_omits_stale_intake_open_risks_after_csf_route_activation(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_case"
    intake_dir = lineage_root / "00_idea_intake"
    mandate_dir = lineage_root / "01_mandate"
    intake_dir.mkdir(parents=True)
    mandate_dir.mkdir(parents=True)

    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "csf_case",
            "verdict": "GO_TO_MANDATE",
            "why": ["qualified"],
            "route_assessment": {
                "candidate_routes": ["cross_sectional_factor", "time_series_signal"],
                "recommended_route": "cross_sectional_factor",
                "why_recommended": ["Cross-asset ranking is the primary expression."],
                "why_not_other_routes": {
                    "time_series_signal": ["Single-asset path prediction is secondary."]
                },
                "route_risks": ["Breadth may be limited."],
                "route_decision_pending": False,
            },
            "approved_scope": {"market": "binance perp"},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    for name in [
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "latest_review_pack.yaml",
        "stage_gate_review.yaml",
    ]:
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    _write_yaml(
        _stage_output_path(mandate_dir, "research_route.yaml"),
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "regime_filter",
            "factor_structure": "multi_factor_score",
            "portfolio_expression": "long_only_rank",
            "neutralization_policy": "group_neutral",
        },
    )
    _write_stage_completion_certificate(mandate_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_fake_stage_provenance(lineage_root, "mandate")

    result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 2
    assert "📍 Current stage: mandate_next_stage_confirmation_pending" in result.stdout
    assert "⚠ Open risks:" not in result.stdout
    assert "rollback_target remains 00_idea_intake" not in result.stdout


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
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 2
    assert "📍 Current stage: mandate_next_stage_confirmation_pending" in result.stdout


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
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 2
    assert "🧭 Current orchestrator: qros-research-session" in result.stdout
    assert "📍 Current stage: mandate_next_stage_confirmation_pending" in result.stdout
    assert "🔨 Current active skill: qros-research-session" in result.stdout
    assert "CONFIRM_NEXT_STAGE" in result.stdout
    assert "Data Ready Reflection:" not in result.stdout





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
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")
    _write_yaml(_stage_draft_path(data_ready_dir, "data_ready_freeze_draft.yaml"), _data_ready_freeze_draft(confirmed=True))
    _write_display_decision(mandate_dir, stage="mandate")
    _write_next_stage_confirmation(mandate_dir, stage="mandate")
    ensure_stage_program(lineage_root, "data_ready")

    skip_result = run(
        [
            sys.executable,
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

    assert skip_result.returncode == 2

    skip_result = run(
        [
            sys.executable,
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

    assert skip_result.returncode == 2

    confirm_result = run(
        [
            sys.executable,
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

    assert confirm_result.returncode == 7

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 7
    assert "📍 Current stage: data_ready_review_confirmation_pending" in result.stdout
    assert (_stage_output_path(lineage_root / "02_data_ready", "data_contract.md")).exists()
    assert "Data Ready Reflection:" not in result.stdout


def test_run_research_session_reports_signal_ready_next_group_after_data_ready_review_complete(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = lineage_root / "02_data_ready"
    mandate_dir.mkdir(parents=True)
    data_ready_dir.mkdir(parents=True)
    _write_yaml(
        _stage_output_path(mandate_dir, "research_route.yaml"),
        {
            "research_route": "time_series_signal",
        },
    )
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
        "run_manifest.json",
        "rebuild_data_ready.py",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(data_ready_dir, name)).write_text("ok\n", encoding="utf-8")
    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (_stage_output_path(data_ready_dir, name)).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "data_ready")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 2
    assert "📍 Current stage: data_ready_next_stage_confirmation_pending" in result.stdout
    assert "CONFIRM_NEXT_STAGE" in result.stdout
    assert "Data Ready Reflection:" in result.stdout


def test_run_research_session_builds_signal_ready_only_after_explicit_confirmation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    data_ready_dir = lineage_root / "02_data_ready"
    signal_ready_dir = lineage_root / "03_signal_ready"
    data_ready_dir.mkdir(parents=True)
    signal_ready_dir.mkdir(parents=True)
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
        "run_manifest.json",
        "rebuild_data_ready.py",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(data_ready_dir, name)).write_text("ok\n", encoding="utf-8")
    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (_stage_output_path(data_ready_dir, name)).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "data_ready")
    _write_yaml(_stage_draft_path(signal_ready_dir, "signal_ready_freeze_draft.yaml"), _signal_ready_freeze_draft(confirmed=True))
    _write_display_decision(data_ready_dir, stage="data_ready")
    _write_next_stage_confirmation(data_ready_dir, stage="data_ready")
    ensure_stage_program(lineage_root, "signal_ready")

    skip_result = run(
        [
            sys.executable,
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

    assert skip_result.returncode == 2

    confirm_result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-signal-ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert confirm_result.returncode == 7

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 7
    assert "📍 Current stage: signal_ready_review_confirmation_pending" in result.stdout
    assert (_stage_output_path(lineage_root / "03_signal_ready", "signal_contract.md")).exists()


def test_run_research_session_reports_train_freeze_next_group_after_signal_ready_review_complete(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    signal_ready_dir = lineage_root / "03_signal_ready"
    signal_ready_dir.mkdir(parents=True)
    for name in [
        "param_manifest.csv",
        "signal_coverage.csv",
        "signal_coverage.md",
        "signal_coverage_summary.md",
        "signal_contract.md",
        "signal_fields_contract.md",
        "signal_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(signal_ready_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(signal_ready_dir, "params")).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "signal_ready")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 2
    assert "📍 Current stage: signal_ready_next_stage_confirmation_pending" in result.stdout
    assert "CONFIRM_NEXT_STAGE" in result.stdout


def test_run_research_session_builds_train_freeze_only_after_explicit_confirmation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    signal_ready_dir = lineage_root / "03_signal_ready"
    train_dir = lineage_root / "04_train_freeze"
    signal_ready_dir.mkdir(parents=True)
    train_dir.mkdir(parents=True)
    for name in [
        "signal_coverage.csv",
        "signal_coverage.md",
        "signal_coverage_summary.md",
        "signal_contract.md",
        "signal_fields_contract.md",
        "signal_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(signal_ready_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(signal_ready_dir, "params")).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "signal_ready")
    (_stage_output_path(signal_ready_dir, "param_manifest.csv")).write_text(
        "\n".join(
            [
                "param_id,scope,baseline_signal,parameter_values",
                'baseline_v1,baseline,btc_alt_residual_response,"event_window: 15m"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_yaml(_stage_draft_path(train_dir, "train_freeze_draft.yaml"), _train_freeze_draft(confirmed=True))
    _write_display_decision(signal_ready_dir, stage="signal_ready")
    _write_next_stage_confirmation(signal_ready_dir, stage="signal_ready")
    ensure_stage_program(lineage_root, "train_freeze")

    skip_result = run(
        [
            sys.executable,
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

    assert skip_result.returncode == 2

    confirm_result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-train-freeze",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert confirm_result.returncode == 7

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 7
    assert "📍 Current stage: train_freeze_review_confirmation_pending" in result.stdout
    assert (_stage_output_path(lineage_root / "04_train_freeze", "train_thresholds.json")).exists()


def test_run_research_session_reports_test_evidence_next_group_after_train_review_complete(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    train_dir = lineage_root / "04_train_freeze"
    train_dir.mkdir(parents=True)
    for name in [
        "train_thresholds.json",
        "train_quality.parquet",
        "train_param_ledger.csv",
        "train_rejects.csv",
        "train_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(train_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "train_freeze")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 2
    assert "📍 Current stage: train_freeze_next_stage_confirmation_pending" in result.stdout
    assert "CONFIRM_NEXT_STAGE" in result.stdout


def test_run_research_session_builds_test_evidence_only_after_explicit_confirmation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = lineage_root / "02_data_ready"
    signal_ready_dir = lineage_root / "03_signal_ready"
    train_dir = lineage_root / "04_train_freeze"
    test_dir = lineage_root / "05_test_evidence"
    mandate_dir.mkdir(parents=True)
    data_ready_dir.mkdir(parents=True)
    signal_ready_dir.mkdir(parents=True)
    train_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    (_stage_output_path(mandate_dir, "time_split.json")).write_text(
        '{"train":"","test":"","holding_horizons":["15m","30m"]}\n',
        encoding="utf-8",
    )
    (_stage_output_path(data_ready_dir, "aligned_bars")).mkdir(parents=True, exist_ok=True)
    (_stage_output_path(signal_ready_dir, "params")).mkdir(parents=True, exist_ok=True)
    (_stage_output_path(signal_ready_dir, "param_manifest.csv")).write_text(
        "\n".join(
            [
                "param_id,scope,baseline_signal,parameter_values",
                'baseline_v1,baseline,btc_alt_residual_response,"event_window: 15m"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for name in [
        "train_thresholds.json",
        "train_quality.parquet",
        "train_param_ledger.csv",
        "train_rejects.csv",
        "train_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(train_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(train_dir, "train_param_ledger.csv")).write_text(
        "\n".join(
            [
                "param_id,status,selection_rule,train_window_source,notes",
                "baseline_v1,kept,baseline-only,time_split.json::train,ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_yaml(_stage_draft_path(test_dir, "test_evidence_draft.yaml"), _test_evidence_draft(confirmed=True))
    _write_display_decision(train_dir, stage="train_freeze")
    _write_next_stage_confirmation(train_dir, stage="train_freeze")
    write_fake_stage_provenance(lineage_root, "train_freeze")
    ensure_stage_program(lineage_root, "test_evidence")

    skip_result = run(
        [
            sys.executable,
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

    assert skip_result.returncode == 2

    confirm_result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-test-evidence",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert confirm_result.returncode == 7

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 7
    assert "📍 Current stage: test_evidence_review_confirmation_pending" in result.stdout
    assert (_stage_output_path(lineage_root / "05_test_evidence", "frozen_spec.json")).exists()


def test_run_research_session_reports_backtest_ready_next_group_after_test_review_complete(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    test_dir = lineage_root / "05_test_evidence"
    test_dir.mkdir(parents=True)
    for name in [
        "report_by_h.parquet",
        "symbol_summary.parquet",
        "admissibility_report.parquet",
        "test_gate_table.csv",
        "crowding_review.md",
        "selected_symbols_test.csv",
        "selected_symbols_test.parquet",
        "frozen_spec.json",
        "test_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(test_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "test_evidence")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 2
    assert "📍 Current stage: test_evidence_next_stage_confirmation_pending" in result.stdout
    assert "CONFIRM_NEXT_STAGE" in result.stdout


def test_run_research_session_reports_failure_routing_for_failed_test_review(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    test_dir = lineage_root / "05_test_evidence"
    test_dir.mkdir(parents=True)
    for name in [
        "report_by_h.parquet",
        "symbol_summary.parquet",
        "admissibility_report.parquet",
        "test_gate_table.csv",
        "crowding_review.md",
        "selected_symbols_test.csv",
        "selected_symbols_test.parquet",
        "frozen_spec.json",
        "test_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (_stage_output_path(test_dir, name)).write_text("ok\n", encoding="utf-8")
    _write_stage_completion_certificate(test_dir / "stage_completion_certificate.yaml", stage_status="RETRY")
    write_fake_stage_provenance(lineage_root, "test_evidence")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 8
    assert "🧭 Current orchestrator: qros-research-session" in result.stdout
    assert "📍 Current stage: test_evidence_review" in result.stdout
    assert "🔨 Current active skill: qros-stage-failure-handler" in result.stdout
    assert "💡 Why this skill: Review verdict RETRY blocks normal progression, so failure handling is now the active workflow." in result.stdout
    assert "⛔ Blocking reason: Normal progression is blocked by review verdict RETRY." in result.stdout
    assert "🧪 Review verdict: RETRY" in result.stdout
    assert "🧯 Requires failure handling: True" in result.stdout
    assert "🧨 Failure stage: test_evidence_review" in result.stdout
    assert "qros-stage-failure-handler" in result.stdout
    assert "backtest_ready_confirmation_pending" not in result.stdout


def test_run_research_session_reports_error_when_backtest_ready_lacks_real_engine_outputs(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    test_dir = lineage_root / "05_test_evidence"
    backtest_dir = lineage_root / "06_backtest"
    test_dir.mkdir(parents=True)
    backtest_dir.mkdir(parents=True)
    for name in [
        "report_by_h.parquet",
        "symbol_summary.parquet",
        "admissibility_report.parquet",
        "test_gate_table.csv",
        "crowding_review.md",
        "selected_symbols_test.csv",
        "selected_symbols_test.parquet",
        "frozen_spec.json",
        "test_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(test_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(test_dir, "selected_symbols_test.csv")).write_text(
        "\n".join(
            [
                "symbol,param_id,best_h",
                "ETHUSDT,baseline_v1,30m",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (_stage_output_path(test_dir, "frozen_spec.json")).write_text(
        '{"selected_symbols":["ETHUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    _write_yaml(_stage_draft_path(backtest_dir, "backtest_ready_draft.yaml"), _backtest_ready_draft(confirmed=True))
    _write_display_decision(test_dir, stage="test_evidence")
    _write_next_stage_confirmation(test_dir, stage="test_evidence")
    write_fake_stage_provenance(lineage_root, "test_evidence")
    ensure_stage_program(lineage_root, "backtest_ready")

    skip_result = run(
        [
            sys.executable,
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

    assert skip_result.returncode == 2

    confirm_result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-backtest-ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert confirm_result.returncode == 6
    assert "Current stage: backtest_ready_author" in confirm_result.stdout
    assert "Blocking reason code: OUTPUTS_INVALID" in confirm_result.stdout


def test_run_research_session_builds_backtest_ready_only_after_explicit_confirmation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    test_dir = lineage_root / "05_test_evidence"
    backtest_dir = lineage_root / "06_backtest"
    test_dir.mkdir(parents=True)
    backtest_dir.mkdir(parents=True)
    for name in [
        "report_by_h.parquet",
        "symbol_summary.parquet",
        "admissibility_report.parquet",
        "test_gate_table.csv",
        "crowding_review.md",
        "selected_symbols_test.csv",
        "selected_symbols_test.parquet",
        "frozen_spec.json",
        "test_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(test_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(test_dir, "selected_symbols_test.csv")).write_text(
        "\n".join(
            [
                "symbol,param_id,best_h",
                "ETHUSDT,baseline_v1,30m",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (_stage_output_path(test_dir, "frozen_spec.json")).write_text(
        '{"selected_symbols":["ETHUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    _write_yaml(_stage_draft_path(backtest_dir, "backtest_ready_draft.yaml"), _backtest_ready_draft(confirmed=True))
    _prepare_real_backtest_engine_outputs(backtest_dir)
    _write_display_decision(test_dir, stage="test_evidence")
    _write_next_stage_confirmation(test_dir, stage="test_evidence")
    write_fake_stage_provenance(lineage_root, "test_evidence")
    ensure_stage_program(lineage_root, "backtest_ready")

    skip_result = run(
        [
            sys.executable,
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

    assert skip_result.returncode == 2

    confirm_result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-backtest-ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert confirm_result.returncode == 7

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 7
    assert "📍 Current stage: backtest_ready_review_confirmation_pending" in result.stdout
    assert (_stage_output_path(lineage_root / "06_backtest", "engine_compare.csv")).exists()


def test_run_research_session_reports_holdout_validation_next_group_after_backtest_review_complete(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    backtest_dir.mkdir(parents=True)
    for name in [
        "strategy_combo_ledger.csv",
        "capacity_review.md",
        "backtest_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(backtest_dir, name)).write_text("ok\n", encoding="utf-8")
    _prepare_real_backtest_engine_outputs(backtest_dir)
    write_fake_stage_provenance(lineage_root, "backtest_ready")

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 2
    assert "📍 Current stage: backtest_ready_next_stage_confirmation_pending" in result.stdout
    assert "CONFIRM_NEXT_STAGE" in result.stdout


def test_run_research_session_builds_holdout_validation_only_after_explicit_confirmation(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    mandate_dir = lineage_root / "01_mandate"
    backtest_dir = lineage_root / "06_backtest"
    holdout_dir = lineage_root / "07_holdout"
    mandate_dir.mkdir(parents=True)
    backtest_dir.mkdir(parents=True)
    holdout_dir.mkdir(parents=True)
    (_stage_output_path(mandate_dir, "time_split.json")).write_text(
        '{"train":"2024-01-01/2024-06-30","test":"2024-07-01/2024-09-30","holdout":"2024-10-01/2024-12-31"}\n',
        encoding="utf-8",
    )
    for name in [
        "strategy_combo_ledger.csv",
        "capacity_review.md",
        "backtest_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (_stage_output_path(backtest_dir, name)).write_text("ok\n", encoding="utf-8")
    _prepare_real_backtest_engine_outputs(backtest_dir)
    (_stage_output_path(backtest_dir, "backtest_frozen_config.json")).write_text(
        '{"selected_symbols":["ETHUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    (_stage_output_path(backtest_dir, "selected_strategy_combo.json")).write_text(
        '{"combo_id":"baseline_combo_v1","selected_symbols":["ETHUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    _write_yaml(
        _stage_draft_path(holdout_dir, "holdout_validation_draft.yaml"),
        _holdout_validation_draft(confirmed=True),
    )
    _write_display_decision(backtest_dir, stage="backtest_ready")
    _write_next_stage_confirmation(backtest_dir, stage="backtest_ready")
    write_fake_stage_provenance(lineage_root, "backtest_ready")
    ensure_stage_program(lineage_root, "holdout_validation")

    skip_result = run(
        [
            sys.executable,
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

    assert skip_result.returncode == 2

    confirm_result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--confirm-holdout-validation",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert confirm_result.returncode == 7

    result = run(
        [
            sys.executable,
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

    assert result.returncode == 7
    assert "📍 Current stage: holdout_validation_review_confirmation_pending" in result.stdout
    assert (_stage_output_path(lineage_root / "07_holdout", "holdout_run_manifest.json")).exists()
