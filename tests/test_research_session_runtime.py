from pathlib import Path

import yaml

from tools.research_session import (
    detect_session_stage,
    run_research_session,
    resolve_lineage_root,
    slugify_idea,
    summarize_session_status,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _route_assessment() -> dict:
    return {
        "candidate_routes": ["time_series_signal", "cross_sectional_factor"],
        "recommended_route": "time_series_signal",
        "why_recommended": ["Single-asset direction is the main expression."],
        "why_not_other_routes": {"cross_sectional_factor": ["Cross-asset sorting is secondary."]},
        "route_risks": ["Universe breadth may be limited."],
        "route_decision_pending": True,
    }


def _write_stage_completion_certificate(
    path: Path,
    *,
    stage_status: str = "PASS",
    final_verdict: str | None = None,
) -> None:
    _write_yaml(
        path,
        {
            "stage_status": stage_status,
            "final_verdict": final_verdict or stage_status,
        },
    )


def _write_minimal_stage_outputs(stage_dir: Path, *, stage: str) -> None:
    stage_dir.mkdir(parents=True, exist_ok=True)

    file_outputs: dict[str, list[str]] = {
        "mandate": [
            "mandate.md",
            "research_scope.md",
            "research_route.yaml",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "data_ready": [
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
        ],
        "signal_ready": [
            "param_manifest.csv",
            "signal_coverage.csv",
            "signal_coverage.md",
            "signal_coverage_summary.md",
            "signal_contract.md",
            "signal_fields_contract.md",
            "signal_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "train_freeze": [
            "train_thresholds.json",
            "train_quality.parquet",
            "train_param_ledger.csv",
            "train_rejects.csv",
            "train_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "test_evidence": [
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
        ],
        "backtest_ready": [
            "engine_compare.csv",
            "strategy_combo_ledger.csv",
            "capacity_review.md",
            "backtest_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "holdout_validation": [
            "holdout_run_manifest.json",
            "holdout_backtest_compare.csv",
            "holdout_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
    }
    dir_outputs: dict[str, list[str]] = {
        "mandate": [],
        "data_ready": [
            "aligned_bars",
            "rolling_stats",
            "pair_stats",
            "benchmark_residual",
            "topic_basket_state",
        ],
        "signal_ready": ["params"],
        "train_freeze": [],
        "test_evidence": [],
        "backtest_ready": ["vectorbt", "backtrader"],
        "holdout_validation": ["window_results"],
    }

    for name in file_outputs[stage]:
        (stage_dir / name).write_text("ok\n", encoding="utf-8")
    for name in dir_outputs[stage]:
        (stage_dir / name).mkdir()
    if stage == "backtest_ready":
        (stage_dir / "engine_compare.csv").write_text(
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
            engine_dir = stage_dir / engine_name
            for name in (
                "trades.parquet",
                "symbol_metrics.parquet",
                "portfolio_timeseries.parquet",
                "portfolio_summary.parquet",
            ):
                (engine_dir / name).write_bytes(b"PAR1test-payloadPAR1")


def _freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "research_intent": {
                "confirmed": confirmed,
                "draft": {
                    "research_question": "q",
                    "research_route": "time_series_signal",
                    "excluded_routes": ["cross_sectional_factor"],
                    "route_rationale": ["Single-asset direction is the primary expression."],
                },
            },
            "scope_contract": {"confirmed": confirmed, "draft": {"market": "binance perp"}},
            "data_contract": {
                "confirmed": confirmed,
                "draft": {"data_source": "binance um futures klines", "bar_size": "5m"},
            },
            "execution_contract": {"confirmed": confirmed, "draft": {"time_split_note": "frozen"}},
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
                    "bad_price_policy": "flag and retain bad prices",
                    "outlier_policy": "flag only, no silent repair",
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
                    "layer_boundary_note": "shared research base only, not thesis-specific signals",
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
                    "frozen_inputs_note": "signal_ready must consume frozen layer outputs only",
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
                    "schema_note": "baseline signal schema frozen for downstream consumers",
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
                    "train_window_note": "Freeze train split only.",
                    "leakage_guardrail": "Do not inspect test or backtest.",
                },
                "missing_items": [],
            },
            "threshold_contract": {
                "confirmed": confirmed,
                "draft": {
                    "threshold_targets": ["signal_value"],
                    "threshold_rule": "Estimate signal thresholds on train only.",
                    "regime_cut_rule": "Freeze regime cuts on train only.",
                    "frozen_outputs_note": "Test must reuse thresholds without re-estimation.",
                },
                "missing_items": [],
            },
            "quality_filters": {
                "confirmed": confirmed,
                "draft": {
                    "quality_metrics": ["coverage_rate"],
                    "filter_rule": "Reject low-coverage pairs on train.",
                    "symbol_param_admission_rule": "Only admissible train pairs may proceed.",
                    "audit_note": "Audit-only observations stay out of formal gate.",
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
                    "coarse_to_fine_note": "No extra search expansion in first wave.",
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
                    "reuse_constraints": "Test must consume frozen train outputs only.",
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
                    "test_window_note": "Freeze test split only.",
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

    assert detect_session_stage(lineage_root) == "idea_intake_confirmation_pending"


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
            "route_assessment": _route_assessment(),
            "approved_scope": {"market": "binance perp"},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )

    assert detect_session_stage(lineage_root) == "idea_intake_confirmation_pending"


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
            "route_assessment": _route_assessment(),
            "approved_scope": {"market": "binance perp"},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
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
        intake_dir / "mandate_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_MANDATE",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_gate_verdict": "GO_TO_MANDATE",
        },
    )
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _freeze_draft(confirmed=True))

    assert detect_session_stage(lineage_root) == "mandate_author"


def test_run_research_session_reports_next_freeze_group_when_draft_incomplete(tmp_path: Path) -> None:
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
            "approved_scope": {"market": "binance perp"},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(intake_dir / "scope_canvas.yaml", {"market": "binance perp"})

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_confirmation_pending"
    assert status.current_route == "time_series_signal"
    assert status.next_action == "Complete mandate freeze group: research_intent"


def test_run_research_session_keeps_intake_open_when_route_assessment_is_missing(tmp_path: Path) -> None:
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
            "approved_scope": {"market": "binance perp"},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(intake_dir / "scope_canvas.yaml", {"market": "binance perp"})

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "idea_intake"
    assert status.current_route is None
    assert status.gate_status == "IN_PROGRESS"
    assert "route_assessment" in status.next_action


def test_run_research_session_stops_at_intake_confirmation_pending_for_new_lineage(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"

    status = run_research_session(outputs_root=outputs_root, raw_idea="BTC leads ALTs")

    assert status.current_stage == "idea_intake_confirmation_pending"
    assert status.gate_status == "IDEA_INTAKE_PENDING_CONFIRMATION"
    assert "--confirm-intake" in status.next_action


def test_detect_session_stage_returns_mandate_review_when_mandate_artifacts_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "mandate_review"


def test_detect_session_stage_returns_data_ready_pending_when_mandate_closure_artifacts_exist(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "data_ready_confirmation_pending"


def test_detect_session_stage_enters_data_ready_confirmation_after_mandate_review_complete(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "data_ready_confirmation_pending"


def test_run_research_session_reports_next_data_ready_freeze_group(tmp_path: Path) -> None:
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
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "data_ready_confirmation_pending"
    assert status.next_action == "Complete data_ready freeze group: extraction_contract"


def test_detect_session_stage_returns_data_ready_author_when_explicitly_confirmed(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
        (mandate_dir / name).write_text("ok\n", encoding="utf-8")
    _write_yaml(data_ready_dir / "data_ready_freeze_draft.yaml", _data_ready_freeze_draft(confirmed=True))
    _write_yaml(
        data_ready_dir / "data_ready_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_DATA_READY",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "mandate_review_complete",
        },
    )

    assert detect_session_stage(lineage_root) == "data_ready_author"


def test_detect_session_stage_returns_data_ready_review_when_outputs_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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

    assert detect_session_stage(lineage_root) == "data_ready_review"


def test_detect_session_stage_returns_signal_ready_pending_when_data_ready_closure_exists(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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

    assert detect_session_stage(lineage_root) == "signal_ready_confirmation_pending"


def test_detect_session_stage_enters_signal_ready_confirmation_after_data_ready_review_complete(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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

    assert detect_session_stage(lineage_root) == "signal_ready_confirmation_pending"


def test_run_research_session_reports_next_signal_ready_freeze_group(tmp_path: Path) -> None:
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

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "signal_ready_confirmation_pending"
    assert status.next_action == "Complete signal_ready freeze group: signal_expression"


def test_detect_session_stage_returns_signal_ready_author_when_explicitly_confirmed(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
    _write_yaml(
        signal_ready_dir / "signal_ready_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_SIGNAL_READY",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "data_ready_review_complete",
        },
    )

    assert detect_session_stage(lineage_root) == "signal_ready_author"


def test_detect_session_stage_returns_signal_ready_review_when_outputs_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
    ]:
        (signal_ready_dir / name).write_text("ok\n", encoding="utf-8")
    (signal_ready_dir / "params").mkdir()

    assert detect_session_stage(lineage_root) == "signal_ready_review"


def test_detect_session_stage_returns_signal_ready_review_complete_when_closure_exists(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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

    assert detect_session_stage(lineage_root) == "train_freeze_confirmation_pending"


def test_run_research_session_reports_next_train_freeze_group(tmp_path: Path) -> None:
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

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "train_freeze_confirmation_pending"
    assert status.next_action == "Complete train_freeze group: window_contract"


def test_detect_session_stage_returns_train_freeze_author_when_explicitly_confirmed(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    signal_ready_dir = lineage_root / "03_signal_ready"
    train_dir = lineage_root / "04_train_freeze"
    signal_ready_dir.mkdir(parents=True)
    train_dir.mkdir(parents=True)
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
    _write_yaml(train_dir / "train_freeze_draft.yaml", _train_freeze_draft(confirmed=True))
    _write_yaml(
        train_dir / "train_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_TRAIN_FREEZE",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "signal_ready_review_complete",
        },
    )

    assert detect_session_stage(lineage_root) == "train_freeze_author"


def test_detect_session_stage_returns_train_freeze_review_when_outputs_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
    ]:
        (train_dir / name).write_text("ok\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "train_freeze_review"


def test_detect_session_stage_returns_test_evidence_pending_when_train_freeze_closure_exists(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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

    assert detect_session_stage(lineage_root) == "test_evidence_confirmation_pending"


def test_run_research_session_reports_next_test_evidence_group(tmp_path: Path) -> None:
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

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "test_evidence_confirmation_pending"
    assert status.next_action == "Complete test_evidence group: window_contract"


def test_detect_session_stage_returns_test_evidence_author_when_explicitly_confirmed(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    train_dir = lineage_root / "04_train_freeze"
    test_dir = lineage_root / "05_test_evidence"
    train_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
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
    _write_yaml(test_dir / "test_evidence_draft.yaml", _test_evidence_draft(confirmed=True))
    _write_yaml(
        test_dir / "test_evidence_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_TEST_EVIDENCE",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "train_freeze_review_complete",
        },
    )

    assert detect_session_stage(lineage_root) == "test_evidence_author"


def test_detect_session_stage_returns_test_evidence_review_when_outputs_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
        (test_dir / name).write_text("ok\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "test_evidence_review"


def test_detect_session_stage_returns_backtest_ready_pending_when_test_evidence_closure_exists(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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

    assert detect_session_stage(lineage_root) == "backtest_ready_confirmation_pending"


def test_run_research_session_reports_next_backtest_ready_group(tmp_path: Path) -> None:
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

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "backtest_ready_confirmation_pending"
    assert status.next_action == "Complete backtest_ready group: execution_policy"


def test_detect_session_stage_returns_backtest_ready_author_when_explicitly_confirmed(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
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
    _write_yaml(backtest_dir / "backtest_ready_draft.yaml", _backtest_ready_draft(confirmed=True))
    _write_yaml(
        backtest_dir / "backtest_ready_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_BACKTEST_READY",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "test_evidence_review_complete",
        },
    )

    assert detect_session_stage(lineage_root) == "backtest_ready_author"


def test_detect_session_stage_returns_backtest_ready_review_when_outputs_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    _write_minimal_stage_outputs(backtest_dir, stage="backtest_ready")

    assert detect_session_stage(lineage_root) == "backtest_ready_review"


def test_detect_session_stage_keeps_backtest_ready_author_when_engine_outputs_are_placeholder(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    test_dir = lineage_root / "05_test_evidence"
    backtest_dir = lineage_root / "06_backtest"
    _write_minimal_stage_outputs(test_dir, stage="test_evidence")
    (test_dir / "stage_completion_certificate.yaml").write_text("ok\n", encoding="utf-8")
    backtest_dir.mkdir(parents=True)
    _write_yaml(backtest_dir / "backtest_ready_draft.yaml", _backtest_ready_draft(confirmed=True))
    _write_yaml(
        backtest_dir / "backtest_ready_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_BACKTEST_READY",
            "approved_by": "tester",
            "approved_at": "2026-03-26T10:00:00Z",
            "source_stage": "test_evidence_review_complete",
        },
    )
    for name in [
        "engine_compare.csv",
        "strategy_combo_ledger.csv",
        "capacity_review.md",
        "backtest_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "backtest_frozen_config.json",
    ]:
        (backtest_dir / name).write_text("ok\n", encoding="utf-8")
    for engine_name in ("vectorbt", "backtrader"):
        engine_dir = backtest_dir / engine_name
        engine_dir.mkdir()
        (engine_dir / "trades.parquet").write_text(
            f"placeholder trades artifact for {engine_name}\n",
            encoding="utf-8",
        )
        (engine_dir / "portfolio_summary.parquet").write_text(
            f"placeholder portfolio summary artifact for {engine_name}\n",
            encoding="utf-8",
        )

    assert detect_session_stage(lineage_root) == "backtest_ready_author"


def test_detect_session_stage_returns_backtest_ready_review_complete_when_closure_exists(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    _write_minimal_stage_outputs(backtest_dir, stage="backtest_ready")
    (backtest_dir / "stage_completion_certificate.yaml").write_text("ok\n", encoding="utf-8")

    assert detect_session_stage(lineage_root) == "holdout_validation_confirmation_pending"


def test_run_research_session_reports_next_holdout_validation_group(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    _write_minimal_stage_outputs(backtest_dir, stage="backtest_ready")
    (backtest_dir / "stage_completion_certificate.yaml").write_text("ok\n", encoding="utf-8")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "holdout_validation_confirmation_pending"
    assert status.next_action == "Complete holdout_validation group: window_contract"


def test_detect_session_stage_returns_holdout_validation_author_when_explicitly_confirmed(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    holdout_dir = lineage_root / "07_holdout"
    _write_minimal_stage_outputs(backtest_dir, stage="backtest_ready")
    holdout_dir.mkdir(parents=True)
    (backtest_dir / "stage_completion_certificate.yaml").write_text("ok\n", encoding="utf-8")
    _write_yaml(
        holdout_dir / "holdout_validation_draft.yaml",
        _holdout_validation_draft(confirmed=True),
    )
    _write_yaml(
        holdout_dir / "holdout_validation_transition_approval.yaml",
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_HOLDOUT_VALIDATION",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "backtest_ready_review_complete",
        },
    )

    assert detect_session_stage(lineage_root) == "holdout_validation_author"


def test_detect_session_stage_returns_holdout_validation_review_when_outputs_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    holdout_dir = lineage_root / "07_holdout"
    holdout_dir.mkdir(parents=True)
    for name in [
        "holdout_run_manifest.json",
        "holdout_backtest_compare.csv",
        "holdout_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (holdout_dir / name).write_text("ok\n", encoding="utf-8")
    (holdout_dir / "window_results").mkdir()

    assert detect_session_stage(lineage_root) == "holdout_validation_review"


def test_detect_session_stage_returns_holdout_validation_review_complete_when_closure_exists(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    holdout_dir = lineage_root / "07_holdout"
    holdout_dir.mkdir(parents=True)
    for name in [
        "holdout_run_manifest.json",
        "holdout_backtest_compare.csv",
        "holdout_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (holdout_dir / name).write_text("ok\n", encoding="utf-8")
    (holdout_dir / "window_results").mkdir()

    assert detect_session_stage(lineage_root) == "holdout_validation_review_complete"


def test_detect_session_stage_does_not_advance_on_retry_completion_certificate(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    cases = [
        ("mandate", lineage_root / "01_mandate", "mandate_review"),
        ("data_ready", lineage_root / "02_data_ready", "data_ready_review"),
        ("signal_ready", lineage_root / "03_signal_ready", "signal_ready_review"),
        ("train_freeze", lineage_root / "04_train_freeze", "train_freeze_review"),
        ("test_evidence", lineage_root / "05_test_evidence", "test_evidence_review"),
        ("backtest_ready", lineage_root / "06_backtest", "backtest_ready_review"),
        ("holdout_validation", lineage_root / "07_holdout", "holdout_validation_review"),
    ]

    for stage, stage_dir, expected_stage in cases:
        _write_minimal_stage_outputs(stage_dir, stage=stage)
        _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="RETRY")

        assert detect_session_stage(lineage_root) == expected_stage, stage


def test_detect_session_stage_advances_on_pass_completion_certificate(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    cases = [
        ("mandate", lineage_root / "01_mandate", "data_ready_confirmation_pending"),
        ("data_ready", lineage_root / "02_data_ready", "signal_ready_confirmation_pending"),
        ("signal_ready", lineage_root / "03_signal_ready", "train_freeze_confirmation_pending"),
        ("train_freeze", lineage_root / "04_train_freeze", "test_evidence_confirmation_pending"),
        ("test_evidence", lineage_root / "05_test_evidence", "backtest_ready_confirmation_pending"),
        ("backtest_ready", lineage_root / "06_backtest", "holdout_validation_confirmation_pending"),
        ("holdout_validation", lineage_root / "07_holdout", "holdout_validation_review_complete"),
    ]

    for stage, stage_dir, expected_stage in cases:
        _write_minimal_stage_outputs(stage_dir, stage=stage)
        _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")

        assert detect_session_stage(lineage_root) == expected_stage, stage


def test_run_research_session_requires_failure_handling_on_non_advancing_review_verdicts(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    cases = [
        ("btc_leads_alts_retry", "RETRY", "test_evidence", "05_test_evidence", "test_evidence_review"),
        (
            "btc_leads_alts_pass_for_retry",
            "PASS FOR RETRY",
            "train_freeze",
            "04_train_freeze",
            "train_freeze_review",
        ),
        ("btc_leads_alts_no_go", "NO-GO", "backtest_ready", "06_backtest", "backtest_ready_review"),
        (
            "btc_leads_alts_child_lineage",
            "CHILD LINEAGE",
            "data_ready",
            "02_data_ready",
            "data_ready_review",
        ),
    ]

    for lineage_id, verdict, stage, stage_dir_name, expected_stage in cases:
        lineage_root = outputs_root / lineage_id
        stage_dir = lineage_root / stage_dir_name
        _write_minimal_stage_outputs(stage_dir, stage=stage)
        _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status=verdict)

        status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)

        assert status.current_stage == expected_stage
        assert status.review_verdict == verdict
        assert status.requires_failure_handling is True
        assert status.failure_stage == expected_stage
        assert "failure" in status.next_action.lower()
        assert status.failure_reason_summary == f"{expected_stage} requires failure handling because review verdict is {verdict}."


def test_run_research_session_marks_pass_reviews_as_not_requiring_failure_handling(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "05_test_evidence"

    _write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "backtest_ready_confirmation_pending"
    assert status.review_verdict == "PASS"
    assert status.requires_failure_handling is False
    assert status.failure_stage is None
    assert status.failure_reason_summary is None


def test_run_research_session_does_not_route_mandate_review_into_failure_handler(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="RETRY")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_review"
    assert status.review_verdict == "RETRY"
    assert status.requires_failure_handling is False
    assert status.failure_stage is None
    assert status.failure_reason_summary is None
    assert status.gate_status == "REVIEW_PENDING"
    assert status.next_action == "Write review_findings.yaml and run mandate review"


def test_summarize_session_status_contains_required_fields(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"

    status = summarize_session_status(
        lineage_id="btc_leads_alts",
        lineage_root=lineage_root,
        current_stage="idea_intake",
        current_route=None,
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
    assert status.review_verdict is None
    assert status.requires_failure_handling is False
    assert status.failure_stage is None
    assert status.failure_reason_summary is None
