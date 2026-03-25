from pathlib import Path
from subprocess import run
import sys

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

    assert confirm_result.returncode == 0

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

    assert confirm_result.returncode == 0

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

    assert result.returncode == 0
    assert "Current stage: data_ready_review" in result.stdout
    assert (lineage_root / "02_data_ready" / "data_contract.md").exists()


def test_run_research_session_reports_signal_ready_next_group_after_data_ready_review_complete(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_research_session.py"
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    data_ready_dir = lineage_root / "02_data_ready"
    data_ready_dir.mkdir(parents=True)
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
        "stage_completion_certificate.yaml",
    ]:
        (data_ready_dir / name).write_text("ok\n", encoding="utf-8")
    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (data_ready_dir / name).mkdir()

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

    assert result.returncode == 0
    assert "Current stage: signal_ready_confirmation_pending" in result.stdout
    assert "Next action: Complete signal_ready freeze group: signal_expression" in result.stdout


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
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (data_ready_dir / name).write_text("ok\n", encoding="utf-8")
    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (data_ready_dir / name).mkdir()
    _write_yaml(signal_ready_dir / "signal_ready_freeze_draft.yaml", _signal_ready_freeze_draft(confirmed=True))

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

    assert confirm_result.returncode == 0

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

    assert result.returncode == 0
    assert "Current stage: signal_ready_review" in result.stdout
    assert (lineage_root / "03_signal_ready" / "signal_contract.md").exists()


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
        (signal_ready_dir / name).write_text("ok\n", encoding="utf-8")
    (signal_ready_dir / "params").mkdir()

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

    assert result.returncode == 0
    assert "Current stage: train_freeze_confirmation_pending" in result.stdout
    assert "Next action: Complete train_freeze group: window_contract" in result.stdout


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
        (signal_ready_dir / name).write_text("ok\n", encoding="utf-8")
    (signal_ready_dir / "params").mkdir()
    (signal_ready_dir / "param_manifest.csv").write_text(
        "\n".join(
            [
                "param_id,scope,baseline_signal,parameter_values",
                'baseline_v1,baseline,btc_alt_residual_response,"event_window: 15m"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_yaml(train_dir / "train_freeze_draft.yaml", _train_freeze_draft(confirmed=True))

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

    assert confirm_result.returncode == 0

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

    assert result.returncode == 0
    assert "Current stage: train_freeze_review" in result.stdout
    assert (lineage_root / "04_train_freeze" / "train_thresholds.json").exists()


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
        (train_dir / name).write_text("ok\n", encoding="utf-8")

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

    assert result.returncode == 0
    assert "Current stage: test_evidence_confirmation_pending" in result.stdout
    assert "Next action: Complete test_evidence group: window_contract" in result.stdout


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
    (mandate_dir / "time_split.json").write_text(
        '{"train":"","test":"","holding_horizons":["15m","30m"]}\n',
        encoding="utf-8",
    )
    (data_ready_dir / "aligned_bars").mkdir()
    (signal_ready_dir / "params").mkdir()
    (signal_ready_dir / "param_manifest.csv").write_text(
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
        (train_dir / name).write_text("ok\n", encoding="utf-8")
    (train_dir / "train_param_ledger.csv").write_text(
        "\n".join(
            [
                "param_id,status,selection_rule,train_window_source,notes",
                "baseline_v1,kept,baseline-only,time_split.json::train,ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_yaml(test_dir / "test_evidence_draft.yaml", _test_evidence_draft(confirmed=True))

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

    assert confirm_result.returncode == 0

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

    assert result.returncode == 0
    assert "Current stage: test_evidence_review" in result.stdout
    assert (lineage_root / "05_test_evidence" / "frozen_spec.json").exists()


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
        (test_dir / name).write_text("ok\n", encoding="utf-8")

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

    assert result.returncode == 0
    assert "Current stage: backtest_ready_confirmation_pending" in result.stdout
    assert "Next action: Complete backtest_ready group: execution_policy" in result.stdout


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
        (test_dir / name).write_text("ok\n", encoding="utf-8")
    (test_dir / "selected_symbols_test.csv").write_text(
        "\n".join(
            [
                "symbol,param_id,best_h",
                "ETHUSDT,baseline_v1,30m",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (test_dir / "frozen_spec.json").write_text(
        '{"selected_symbols":["ETHUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    _write_yaml(backtest_dir / "backtest_ready_draft.yaml", _backtest_ready_draft(confirmed=True))

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

    assert confirm_result.returncode == 0

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

    assert result.returncode == 0
    assert "Current stage: backtest_ready_review" in result.stdout
    assert (lineage_root / "06_backtest" / "engine_compare.csv").exists()


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
        "engine_compare.csv",
        "strategy_combo_ledger.csv",
        "capacity_review.md",
        "backtest_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (backtest_dir / name).write_text("ok\n", encoding="utf-8")
    (backtest_dir / "vectorbt").mkdir()
    (backtest_dir / "backtrader").mkdir()

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

    assert result.returncode == 0
    assert "Current stage: holdout_validation_confirmation_pending" in result.stdout
    assert "Next action: Complete holdout_validation group: window_contract" in result.stdout


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
    (mandate_dir / "time_split.json").write_text(
        '{"train":"2024-01-01/2024-06-30","test":"2024-07-01/2024-09-30","holdout":"2024-10-01/2024-12-31"}\n',
        encoding="utf-8",
    )
    for name in [
        "engine_compare.csv",
        "strategy_combo_ledger.csv",
        "capacity_review.md",
        "backtest_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (backtest_dir / name).write_text("ok\n", encoding="utf-8")
    (backtest_dir / "vectorbt").mkdir()
    (backtest_dir / "backtrader").mkdir()
    (backtest_dir / "backtest_frozen_config.json").write_text(
        '{"selected_symbols":["ETHUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    (backtest_dir / "selected_strategy_combo.json").write_text(
        '{"combo_id":"baseline_combo_v1","selected_symbols":["ETHUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    _write_yaml(
        holdout_dir / "holdout_validation_draft.yaml",
        _holdout_validation_draft(confirmed=True),
    )

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

    assert confirm_result.returncode == 0

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

    assert result.returncode == 0
    assert "Current stage: holdout_validation_review" in result.stdout
    assert (lineage_root / "07_holdout" / "holdout_run_manifest.json").exists()
