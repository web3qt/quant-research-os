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


def _freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "research_intent": {"confirmed": confirmed, "draft": {"research_question": "q"}},
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
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _freeze_draft(confirmed=True))

    assert detect_session_stage(lineage_root) == "mandate_author"


def test_run_research_session_reports_next_freeze_group_when_draft_incomplete(tmp_path: Path) -> None:
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

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_confirmation_pending"
    assert status.next_action == "Complete mandate freeze group: research_intent"


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


def test_detect_session_stage_returns_data_ready_pending_when_mandate_closure_artifacts_exist(
    tmp_path: Path,
) -> None:
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

    assert detect_session_stage(lineage_root) == "signal_ready_review_complete"


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
