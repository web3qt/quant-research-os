import json
from pathlib import Path

import pytest
import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from tests.helpers.lineage_program_support import write_fake_stage_provenance
from runtime.tools.review_skillgen.adversarial_review_contract import (
    ensure_adversarial_review_request,
    issue_reviewer_receipt,
    load_adversarial_review_request,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import run_reviewer_write_scope_audit
from runtime.tools.mandate_admission_runtime import (
    admission_ready_for_freeze,
    scaffold_mandate_admission,
)
from runtime.tools.research_session import (
    _latest_review_failure_status,
    detect_session_stage,
    run_research_session,
    resolve_lineage_selection,
    resolve_lineage_root,
    slugify_idea,
    summarize_session_status,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _read_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_review_eligibility(lineage_root: Path, payload: dict) -> None:
    path = lineage_root / "review_eligibility.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_test_parquet_rows(path: Path, rows: list[dict]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_data_inventory(data_root: Path, *, data_min_ts: str, data_max_ts: str) -> Path:
    data_root.mkdir(parents=True, exist_ok=True)
    (data_root / "data_inventory.json").write_text(
        yaml.safe_dump(
            {
                "data_min_ts": data_min_ts,
                "data_max_ts": data_max_ts,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return data_root


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
        "candidate_routes": ["time_series_signal", "cross_sectional_factor"],
        "recommended_route": "time_series_signal",
        "why_recommended": ["Single-asset direction is the main expression."],
        "why_not_other_routes": {"cross_sectional_factor": ["Cross-asset sorting is secondary."]},
        "route_risks": ["Universe breadth may be limited."],
        "route_decision_pending": True,
    }


def _write_mandate_admission(
    lineage_root: Path,
    *,
    accepted: bool = True,
    include_route: bool = True,
    freeze_confirmed: bool | None = None,
    transition_confirmed: bool = False,
) -> Path:
    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    route_assessment = _route_assessment()
    route_assessment["route_decision_pending"] = False
    payload = {
        "lineage_id": lineage_root.name,
        "raw_idea": "BTC leads ALTs",
        "observation": "BTC shocks precede ALT reactions.",
        "primary_hypothesis": "BTC leads price discovery.",
        "counter_hypothesis": "Moves are shared beta.",
        "research_questions": ["Do ALTs follow BTC after shocks?"],
        "scope": {
            "market": "binance perp",
            "instrument_type": "perpetual",
            "universe": "high liquidity alts",
            "data_source": "binance um futures klines",
            "bar_size": "5m",
            "holding_horizons": ["15m", "30m"],
            "target_task": "event-driven relative return study",
            "excluded_scope": ["low liquidity tails"],
            "budget_days": 5,
            "max_iterations": 3,
        },
        "qualification": {
            "summary": "Researchable.",
            "dimensions": {
                name: {"score": 3, "evidence": ["present"], "uncertainty": [], "kill_reason": []}
                for name in [
                    "observability",
                    "mechanism_plausibility",
                    "tradeability",
                    "data_feasibility",
                    "scoping_clarity",
                    "distinctiveness",
                ]
            },
        },
        "route_assessment": route_assessment
        if include_route
        else {
            "candidate_routes": [],
            "recommended_route": "",
            "why_recommended": [],
            "why_not_other_routes": {},
            "route_risks": [],
            "route_decision_pending": True,
        },
        "admission_decision": {
            "verdict": "ACCEPT_FOR_MANDATE" if accepted else "NEEDS_REFRAME",
            "why": ["Scope is concrete."],
            "kill_criteria": ["No edge after costs."],
            "required_reframe_actions": [] if accepted else ["narrow universe"],
        },
    }
    _write_yaml(draft_dir / "mandate_admission.yaml", payload)
    if freeze_confirmed is not None:
        _write_yaml(draft_dir / "mandate_freeze_draft.yaml", _freeze_draft(confirmed=freeze_confirmed))
    if transition_confirmed:
        _write_yaml(
            draft_dir / "mandate_transition_approval.yaml",
            {
                "lineage_id": lineage_root.name,
                "decision": "CONFIRM_MANDATE",
                "approved_by": "tester",
                "approved_at": "2026-05-21T10:00:00Z",
                "source_stage": "mandate_freeze_confirmation_pending",
            },
        )
    return draft_dir


def test_scaffold_mandate_admission_creates_compressed_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "breakout_quality"

    artifacts = scaffold_mandate_admission(lineage_root, raw_idea="突破质量分数")

    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    assert "01_mandate/author/draft/mandate_admission.yaml" in artifacts
    assert "01_mandate/author/draft/mandate_freeze_draft.yaml" in artifacts
    payload = _read_yaml(draft_dir / "mandate_admission.yaml")
    assert payload["lineage_id"] == "breakout_quality"
    assert payload["raw_idea"] == "突破质量分数"
    assert payload["admission_decision"]["verdict"] == "NEEDS_REFRAME"


def test_admission_ready_for_freeze_requires_accept_verdict_and_route() -> None:
    payload = {
        "lineage_id": "breakout_quality",
        "raw_idea": "breakout quality",
        "observation": "Clean breakouts may continue.",
        "primary_hypothesis": "Volume-confirmed breakouts have relative strength.",
        "counter_hypothesis": "The effect is shared beta.",
        "research_questions": ["Does quality rank forecast forward returns?"],
        "scope": {
            "market": "crypto perpetual futures",
            "instrument_type": "perpetual",
            "universe": "top 30 Binance USD-M",
            "data_source": "/data/binance",
            "bar_size": "5m",
            "holding_horizons": ["30m", "2h"],
            "target_task": "cross-sectional ranking",
            "excluded_scope": ["spot"],
            "budget_days": 5,
            "max_iterations": 3,
        },
        "qualification": {
            "summary": "Researchable.",
            "dimensions": {
                name: {"score": 3, "evidence": ["present"], "uncertainty": [], "kill_reason": []}
                for name in [
                    "observability",
                    "mechanism_plausibility",
                    "tradeability",
                    "data_feasibility",
                    "scoping_clarity",
                    "distinctiveness",
                ]
            },
        },
        "route_assessment": {
            "candidate_routes": ["cross_sectional_factor", "time_series_signal"],
            "recommended_route": "cross_sectional_factor",
            "why_recommended": ["Ranking is the thesis."],
            "why_not_other_routes": {"time_series_signal": ["Single-asset direction is secondary."]},
            "route_risks": ["Short leg fragility."],
            "route_decision_pending": False,
        },
        "admission_decision": {
            "verdict": "ACCEPT_FOR_MANDATE",
            "why": ["Scope is concrete."],
            "kill_criteria": ["No monotonic buckets after costs."],
            "required_reframe_actions": [],
        },
    }

    assert admission_ready_for_freeze(payload) is None

    payload["route_assessment"]["route_decision_pending"] = True
    assert (
        admission_ready_for_freeze(payload)
        == "route_assessment.route_decision_pending must be false"
    )
    payload["route_assessment"]["route_decision_pending"] = False

    payload["qualification"]["dimensions"]["observability"]["score"] = True
    assert (
        admission_ready_for_freeze(payload)
        == "qualification.dimensions.observability.score must be positive"
    )
    payload["qualification"]["dimensions"]["observability"]["score"] = 3

    payload["route_assessment"]["recommended_route"] = ""
    assert admission_ready_for_freeze(payload) == "route_assessment.recommended_route is required"


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


def _write_failure_post_retry_decision(
    stage_dir: Path,
    *,
    failure_id: str = "backtest_exec_fail_20260423T045312Z",
    failed_stage: str = "csf_backtest_ready",
    normal_progression_allowed: bool = False,
) -> Path:
    failure_package_dir = stage_dir / "failure_packages" / failure_id
    _write_yaml(
        failure_package_dir / "post_retry_decision.yaml",
        {
            "lineage_id": stage_dir.parent.name,
            "failed_stage": failed_stage,
            "failure_class": "EXEC_FAIL",
            "controlled_retry_count": 1,
            "retry_result": "hard_gate_still_failed",
            "recommended_next_decision": "NO_GO_OR_CHILD_LINEAGE_REQUIRED",
            "normal_progression_allowed": normal_progression_allowed,
            "reason": (
                "Stage-local accounting correction improved the result but did not clear "
                "mean_net_return > 0."
            ),
        },
    )
    return failure_package_dir


def _write_failure_disposition(
    failure_package_dir: Path,
    *,
    decision: str,
) -> None:
    _write_yaml(
        failure_package_dir / "failure_disposition.yaml",
        {
            "lineage_id": failure_package_dir.parents[2].name,
            "failed_stage": failure_package_dir.parents[1].name.removeprefix("06_"),
            "decision": decision,
            "normal_progression_allowed": False,
            "decided_at": "2026-04-23T05:10:00Z",
            "reason": "Formal disposition recorded after controlled retry stayed below the hard gate.",
        },
    )


def _write_adversarial_review_request(
    stage_dir: Path,
    *,
    stage: str,
    program_dir: str,
    author_identity: str = "test-agent",
    author_session_id: str = "test-session",
) -> None:
    ensure_adversarial_review_request(
        stage_dir,
        lineage_id=stage_dir.parent.name,
        stage=stage,
        author_identity=author_identity,
        author_session_id=author_session_id,
        required_program_dir=program_dir,
        required_program_entrypoint="run_stage.py",
        required_artifact_paths=[],
        required_provenance_paths=["program_execution_manifest.json"],
    )


def _review_request_payload(stage_dir: Path) -> dict:
    return load_adversarial_review_request(stage_dir / "review" / "request" / "adversarial_review_request.yaml")


def _write_reviewer_receipt(
    stage_dir: Path,
    *,
    reviewer_identity: str = "reviewer-agent",
    reviewer_session_id: str = "review-session",
    reviewer_agent_id: str = "reviewer-child-agent",
) -> None:
    issue_reviewer_receipt(
        stage_dir,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id="launcher-session",
        launcher_thread_id="leader-thread",
        reviewer_agent_id=reviewer_agent_id,
    )


def _write_adversarial_review_result(
    stage_dir: Path,
    *,
    stage: str,
    program_dir: str,
    outcome: str,
) -> None:
    request_payload = _review_request_payload(stage_dir)
    final_verdict_by_outcome = {
        "CLOSURE_READY_PASS": "PASS",
        "CLOSURE_READY_CONDITIONAL_PASS": "CONDITIONAL PASS",
        "CLOSURE_READY_PASS_FOR_RETRY": "PASS FOR RETRY",
        "CLOSURE_READY_RETRY": "RETRY",
        "CLOSURE_READY_NO_GO": "NO-GO",
        "CLOSURE_READY_CHILD_LINEAGE": "CHILD LINEAGE",
    }
    _write_yaml(
        stage_dir / "review" / "result" / "adversarial_review_result.yaml",
        {
            "review_cycle_id": request_payload["review_cycle_id"],
            "reviewer_identity": "reviewer-agent",
            "reviewer_role": "reviewer",
            "reviewer_session_id": "review-session",
            "reviewer_mode": "adversarial",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewer_execution_mode": "spawned_agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
            "review_loop_outcome": outcome,
            **(
                {"final_verdict": final_verdict_by_outcome[outcome]}
                if outcome in final_verdict_by_outcome
                else {}
            ),
            "reviewed_program_dir": program_dir,
            "reviewed_program_entrypoint": "run_stage.py",
            "reviewed_project_root": request_payload["project_root"],
            "reviewed_lineage_root": request_payload["lineage_root"],
            "reviewed_stage_dir": request_payload["stage_dir"],
            "hard_gate_findings_acknowledged": True,
            "reviewed_artifact_paths": [],
            "reviewed_provenance_paths": ["program_execution_manifest.json"],
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "hard_gate_downgrade_detected": False,
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )
    final_review_verdict = final_verdict_by_outcome.get(outcome, outcome)
    _write_yaml(
        stage_dir / "review" / "final_review.yaml",
        {
            "lineage_id": stage_dir.parent.name,
            "stage_id": stage,
            "reviewer_identity": "reviewer-agent",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewed_artifact_paths": ["artifact_catalog.md"],
            "reviewed_program_path": f"{program_dir}/run_stage.py",
            "reviewed_artifact_digest": "sha256:test-artifact-digest",
            "reviewed_program_digest": "sha256:test-program-digest",
            "verdict": final_review_verdict,
            "review_summary": "test review fixture",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "rollback_stage": None,
            "downstream_permissions": [],
            "recommended_next_action": "test review fixture",
        },
    )
    run_reviewer_write_scope_audit(stage_dir)


def _write_minimal_stage_outputs(stage_dir: Path, *, stage: str) -> None:
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)

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
            "run_manifest.json",
            "rebuild_data_ready.py",
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
        "csf_data_ready": [
            "panel_manifest.json",
            "asset_universe_membership.parquet",
            "cross_section_coverage.parquet",
            "split_sample_adequacy_report.yaml",
            "eligibility_base_mask.parquet",
            "asset_taxonomy_snapshot.parquet",
            "csf_data_contract.md",
            "csf_data_ready_gate_decision.md",
            "run_manifest.json",
            "rebuild_csf_data_ready.py",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_signal_ready": [
            "factor_panel.parquet",
            "factor_manifest.yaml",
            "component_factor_manifest.yaml",
            "factor_coverage_report.parquet",
            "factor_group_context.parquet",
            "route_inheritance_contract.yaml",
            "factor_contract.md",
            "factor_field_dictionary.md",
            "csf_signal_ready_gate_decision.md",
            "run_manifest.json",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_train_freeze": [
            "csf_train_freeze.yaml",
            "train_factor_quality.parquet",
            "train_variant_ledger.csv",
            "train_variant_rejects.csv",
            "train_bucket_diagnostics.parquet",
            "train_neutralization_diagnostics.parquet",
            "csf_train_contract.md",
            "csf_train_freeze_gate_decision.md",
            "run_manifest.json",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_test_evidence": [
            "rank_ic_timeseries.parquet",
            "rank_ic_summary.json",
            "bucket_returns.parquet",
            "monotonicity_report.json",
            "breadth_coverage_report.parquet",
            "subperiod_stability_report.json",
            "filter_condition_panel.parquet",
            "target_strategy_condition_compare.parquet",
            "gated_vs_ungated_summary.json",
            "csf_test_gate_table.csv",
            "csf_selected_variants_test.csv",
            "csf_test_contract.md",
            "csf_test_gate_decision.md",
            "run_manifest.json",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_backtest_ready": [
            "portfolio_contract.yaml",
            "portfolio_weight_panel.parquet",
            "rebalance_ledger.csv",
            "turnover_capacity_report.parquet",
            "cost_assumption_report.md",
            "portfolio_summary.parquet",
            "name_level_metrics.parquet",
            "drawdown_report.json",
            "target_strategy_compare.parquet",
            "csf_backtest_gate_table.csv",
            "csf_backtest_contract.md",
            "csf_backtest_gate_decision.md",
            "run_manifest.json",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "csf_holdout_validation": [
            "csf_holdout_run_manifest.json",
            "holdout_factor_diagnostics.parquet",
            "holdout_test_compare.parquet",
            "holdout_portfolio_compare.parquet",
            "rolling_holdout_stability.json",
            "regime_shift_audit.json",
            "csf_holdout_gate_decision.md",
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
        "csf_data_ready": ["shared_feature_base"],
        "csf_signal_ready": [],
        "csf_train_freeze": [],
        "csf_test_evidence": [],
        "csf_backtest_ready": [],
        "csf_holdout_validation": [],
    }

    parquet_fixtures: dict[str, list[dict]] = {
        "asset_universe_membership.parquet": [
            {"date": "2024-01-01", "asset": "BTCUSDT", "in_universe": True},
            {"date": "2024-01-01", "asset": "ETHUSDT", "in_universe": True},
        ],
        "cross_section_coverage.parquet": [
            {"date": "2024-01-01", "coverage_ratio": 1.0, "asset_count": 2},
        ],
        "eligibility_base_mask.parquet": [
            {"date": "2024-01-01", "asset": "BTCUSDT", "eligible": True},
            {"date": "2024-01-01", "asset": "ETHUSDT", "eligible": True},
        ],
        "asset_taxonomy_snapshot.parquet": [
            {"asset": "BTCUSDT", "group_taxonomy_reference": "sector_bucket_v1", "group_bucket": "core"},
            {"asset": "ETHUSDT", "group_taxonomy_reference": "sector_bucket_v1", "group_bucket": "core"},
        ],
        "factor_panel.parquet": [
            {"date": "2024-01-01", "asset": "BTCUSDT", "factor_value": 1.0},
            {"date": "2024-01-01", "asset": "ETHUSDT", "factor_value": -1.0},
        ],
        "factor_coverage_report.parquet": [
            {"date": "2024-01-01", "coverage_ratio": 1.0, "asset_count": 2},
        ],
        "factor_group_context.parquet": [
            {"date": "2024-01-01", "asset": "BTCUSDT", "group_context": "core"},
            {"date": "2024-01-01", "asset": "ETHUSDT", "group_context": "core"},
        ],
        "train_factor_quality.parquet": [
            {"variant_id": "baseline_v1", "quality_score": 1.0},
        ],
        "train_bucket_diagnostics.parquet": [
            {"bucket_id": "q1", "min_names": 10, "ranking_scope": "full_universe"},
        ],
        "train_neutralization_diagnostics.parquet": [
            {
                "neutralization_policy": "group_neutral",
                "group_taxonomy_reference": "sector_bucket_v1",
                "beta_estimation_window": "60d",
            },
        ],
        "portfolio_weight_panel.parquet": [
            {"date": "2024-10-01", "asset": "SOLUSDT", "variant_id": "baseline_v1", "weight": 0.5, "side": "long"},
        ],
        "turnover_capacity_report.parquet": [
            {"date": "2024-10-01", "variant_id": "baseline_v1", "turnover": 0.12, "capacity_utilization": 0.25},
        ],
        "portfolio_summary.parquet": [
            {"variant_id": "baseline_v1", "mean_gross_return": 0.018, "mean_net_return": 0.012, "max_drawdown": -0.08},
        ],
        "name_level_metrics.parquet": [
            {"asset": "SOLUSDT", "variant_id": "baseline_v1", "contribution": 0.012, "max_weight": 0.5},
        ],
        "target_strategy_compare.parquet": [
            {
                "variant_id": "baseline_v1",
                "target_strategy_reference": "",
                "portfolio_mean_net_return": 0.012,
                "target_mean_net_return": 0.006,
            },
        ],
    }
    text_fixtures: dict[str, str] = {}
    if stage == "mandate":
        text_fixtures = {
            "mandate.md": "\n".join(
                [
                    "# Mandate",
                    "## 目标",
                    "## 研究意图",
                    "## 路线理由",
                    "## 成功标准",
                    "## 失败标准",
                    "## 已冻结执行输入",
                    "## 执行合同",
                    "## Gate 依据",
                ]
            )
            + "\n",
            "research_scope.md": "# Research Scope\n",
            "research_route.yaml": yaml.safe_dump(
                {
                    "research_route": "time_series_signal",
                    "factor_role": "",
                    "factor_structure": "",
                    "portfolio_expression": "",
                    "neutralization_policy": "",
                    "target_strategy_reference": "",
                    "group_taxonomy_reference": "",
                    "excluded_routes": ["cross_sectional_factor"],
                    "route_rationale": ["Single-asset direction is the primary expression."],
                    "route_change_policy": {
                        "before_downstream_freeze": "rollback_to_mandate",
                        "after_downstream_freeze": "child_lineage",
                    },
                    "route_contract_version": "v1",
                },
                sort_keys=False,
                allow_unicode=True,
            ),
            "time_split.json": json.dumps(
                {
                    "train": "2024-01-01/2024-03-31",
                    "test": "2024-04-01/2024-06-30",
                    "backtest": "2024-07-01/2024-09-30",
                    "holdout": "2024-10-01/2024-12-31",
                    "bar_size": "5m",
                    "holding_horizons": ["15m"],
                    "policy_note": "locked",
                    "execution_timing_policy": (
                        "Features use only completed bars and execution happens on the next bar."
                    ),
                    "feature_warmup_policy": "Use lookback warm-up to compute the effective sample start.",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            "parameter_grid.yaml": yaml.safe_dump(
                {
                    "parameters": [
                        {
                            "param_id": "shock_threshold_bp",
                            "values": [30, 50],
                        }
                    ],
                    "note": "locked parameter family",
                    "search_budget": {
                        "max_grid_combinations": 16,
                        "staged_freeze_required": True,
                        "budget_policy": "Freeze core signal before overlays.",
                    },
                    "rebalance_horizon_policy": "Rebalance cadence is execution timing, not a label horizon.",
                },
                sort_keys=False,
                allow_unicode=True,
            ),
            "run_config.toml": "\n".join(
                [
                    'stage = "mandate"',
                    f'lineage_id = "{stage_dir.parent.name}"',
                    'market = "binance perp"',
                    'universe = "high liquidity alts"',
                    'target_task = "event-driven relative return study"',
                    'data_source = "binance um futures klines"',
                    'bar_size = "5m"',
                    "non_rust_exceptions = []",
                    'downstream_required_artifacts = ["raw_to_canonical_field_map", "benchmark_suite_contract"]',
                ]
            )
            + "\n",
            "artifact_catalog.md": "# 产物清单\n",
            "field_dictionary.md": "# 字段字典\n",
        }
    if stage == "csf_data_ready":
        text_fixtures = {
            "split_sample_adequacy_report.yaml": yaml.safe_dump(
                {
                    "stage": "csf_data_ready",
                    "lineage_id": stage_dir.parent.name,
                    "sample_unit": "cross_section_snapshot",
                    "source_artifact": "cross_section_coverage.parquet",
                    "split_source_artifact": "../../01_mandate/author/formal/time_split.json",
                    "split_sample_counts": {"train": 1, "test": 1, "backtest": 1, "holdout": 1},
                    "minimum_required": {"train": 1, "test": 1, "backtest": 1, "holdout": 1},
                    "adequacy": {"train": "pass", "test": "pass", "backtest": "pass", "holdout": "pass"},
                    "final_verdict": "PASS",
                },
                sort_keys=False,
                allow_unicode=True,
            ),
        }

    for name in file_outputs[stage]:
        if name in parquet_fixtures:
            _write_test_parquet_rows(author_formal_dir / name, parquet_fixtures[name])
            continue
        if name in text_fixtures:
            (author_formal_dir / name).write_text(text_fixtures[name], encoding="utf-8")
            continue
        (author_formal_dir / name).write_text("ok\n", encoding="utf-8")
    for name in dir_outputs[stage]:
        (author_formal_dir / name).mkdir()
    if stage == "backtest_ready":
        (author_formal_dir / "engine_compare.csv").write_text(
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
            engine_dir = author_formal_dir / engine_name
            for name in (
                "trades.parquet",
                "symbol_metrics.parquet",
                "portfolio_timeseries.parquet",
                "portfolio_summary.parquet",
            ):
                (engine_dir / name).write_bytes(b"PAR1test-payloadPAR1")
    write_fake_stage_provenance(stage_dir.parent, stage)


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
                    "consumer_stage": "terminal",
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


def test_resolve_lineage_selection_blocks_same_slug_raw_idea_when_lineage_exists(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    lineage_root.mkdir(parents=True)
    (lineage_root / "01_mandate").mkdir()

    selection = resolve_lineage_selection(outputs_root, lineage_id=None, raw_idea="BTC leads ALTs")

    assert selection.lineage_root == lineage_root
    assert selection.lineage_id == "btc_leads_alts"
    assert selection.mode == "resume_blocked_existing_slug"
    assert selection.resume_blocked is True


def test_resolve_lineage_selection_marks_explicit_lineage_resume(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    lineage_root.mkdir(parents=True)
    (lineage_root / "01_mandate").mkdir()

    selection = resolve_lineage_selection(outputs_root, lineage_id="btc_leads_alts", raw_idea=None)

    assert selection.lineage_root == lineage_root
    assert selection.mode == "explicit_resume"
    assert selection.resume_blocked is False


def test_resolve_lineage_root_raises_for_existing_same_slug_raw_idea(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    lineage_root.mkdir(parents=True)
    (lineage_root / "01_mandate").mkdir()

    with pytest.raises(ValueError, match="use explicit lineage_id to resume it"):
        resolve_lineage_root(outputs_root, lineage_id=None, raw_idea="BTC leads ALTs")


def test_detect_session_stage_returns_mandate_admission_when_lineage_missing(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"

    assert detect_session_stage(lineage_root) == "mandate_admission"


def test_detect_session_stage_returns_mandate_freeze_confirmation_when_admission_accepted(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "breakout_quality"
    scaffold_mandate_admission(lineage_root, raw_idea="breakout quality")
    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    payload = _read_yaml(draft_dir / "mandate_admission.yaml")
    payload.update(
        {
            "observation": "Clean breakouts may continue.",
            "primary_hypothesis": "Volume-confirmed breakouts have relative strength.",
            "counter_hypothesis": "The effect is shared beta.",
            "research_questions": ["Does quality rank forecast forward returns?"],
        }
    )
    payload["scope"].update(
        {
            "market": "crypto perpetual futures",
            "instrument_type": "perpetual",
            "universe": "top 30 Binance USD-M",
            "data_source": "/data/binance",
            "bar_size": "5m",
            "holding_horizons": ["30m"],
            "target_task": "cross-sectional ranking",
            "excluded_scope": ["spot"],
            "budget_days": 5,
            "max_iterations": 3,
        }
    )
    payload["qualification"]["summary"] = "Researchable."
    for dimension in payload["qualification"]["dimensions"].values():
        dimension["score"] = 3
        dimension["evidence"] = ["present"]
    payload["route_assessment"] = {
        "candidate_routes": ["cross_sectional_factor", "time_series_signal"],
        "recommended_route": "cross_sectional_factor",
        "why_recommended": ["Ranking is the thesis."],
        "why_not_other_routes": {"time_series_signal": ["Single-asset direction is secondary."]},
        "route_risks": ["Short leg fragility."],
        "route_decision_pending": False,
    }
    payload["admission_decision"] = {
        "verdict": "ACCEPT_FOR_MANDATE",
        "why": ["Scope is concrete."],
        "kill_criteria": ["No monotonic buckets after costs."],
        "required_reframe_actions": [],
    }
    _write_yaml(draft_dir / "mandate_admission.yaml", payload)
    _write_yaml(draft_dir / "mandate_freeze_draft.yaml", _freeze_draft(confirmed=False))

    assert detect_session_stage(lineage_root) == "mandate_freeze_confirmation_pending"


def test_detect_session_stage_returns_idea_intake_when_gate_not_admitted(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _write_mandate_admission(lineage_root, accepted=False)

    assert detect_session_stage(lineage_root) == "mandate_admission"


def test_detect_session_stage_returns_pending_confirmation_when_admitted_but_not_approved(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _write_mandate_admission(lineage_root, freeze_confirmed=False)

    assert detect_session_stage(lineage_root) == "mandate_freeze_confirmation_pending"


def test_detect_session_stage_returns_mandate_author_when_admitted_and_explicitly_approved(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _write_mandate_admission(lineage_root, freeze_confirmed=True, transition_confirmed=True)

    assert detect_session_stage(lineage_root) == "mandate_author"


def test_run_research_session_reports_next_freeze_group_when_draft_incomplete(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    _write_mandate_admission(lineage_root, freeze_confirmed=False)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_freeze_confirmation_pending"
    assert status.current_route == "time_series_signal"
    assert status.next_action == (
        "Review all mandate freeze groups in qros-research-session, then reply 确认全部 "
        "to mark the displayed groups confirmed."
    )
    assert [group["name"] for group in status.freeze_groups or []] == [
        "research_intent",
        "scope_contract",
        "data_contract",
        "execution_contract",
    ]
    assert {group["confirmed"] for group in status.freeze_groups or []} == {False}


def test_run_research_session_can_confirm_all_freeze_groups_without_stage_transition(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    draft_dir = _write_mandate_admission(lineage_root, freeze_confirmed=False)

    status = run_research_session(
        outputs_root=outputs_root,
        lineage_id="btc_leads_alts",
        confirm_all_freeze_groups=True,
    )

    assert status.current_stage == "mandate_freeze_confirmation_pending"
    assert status.next_action == (
        "Reply CONFIRM_MANDATE <lineage_id> in qros-research-session after reviewing the displayed contract."
    )
    assert "01_mandate/author/draft/mandate_freeze_draft.yaml" in status.artifacts_written
    draft = _read_yaml(draft_dir / "mandate_freeze_draft.yaml")
    assert {name: group["confirmed"] for name, group in draft["groups"].items()} == {
        "research_intent": True,
        "scope_contract": True,
        "data_contract": True,
        "execution_contract": True,
    }


def test_run_research_session_keeps_intake_open_when_route_assessment_is_missing(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    _write_mandate_admission(lineage_root, include_route=False)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_admission"
    assert status.current_route is None
    assert status.gate_status == "MANDATE_ADMISSION_IN_PROGRESS"
    assert "recommended_route" in status.next_action or "route_assessment" in status.next_action


def test_run_research_session_stops_at_intake_confirmation_pending_for_new_lineage(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"

    status = run_research_session(outputs_root=outputs_root, raw_idea="BTC leads ALTs")

    assert status.current_stage == "mandate_admission"
    assert status.gate_status == "MANDATE_ADMISSION_IN_PROGRESS"
    assert "observation is required" in status.next_action
    assert status.lineage_mode == "fresh_start"
    assert "fresh lineage slug" in (status.lineage_selection_reason or "")


def test_run_research_session_blocks_implicit_resume_for_existing_same_slug_raw_idea(
    tmp_path: Path,
) -> None:
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

    status = run_research_session(outputs_root=outputs_root, raw_idea="BTC leads ALTs")

    assert status.lineage_id == "btc_leads_alts"
    assert status.current_stage == "mandate_admission"
    assert status.lineage_mode == "resume_blocked_existing_slug"
    assert status.blocking_reason_code == "LINEAGE_RESUME_BLOCKED"
    assert "blocked implicit resume" in status.why_this_skill
    assert "Resume blocked for existing lineage btc_leads_alts" in status.next_action
    assert "Continue qros-research-session with explicit lineage btc_leads_alts" in status.resume_hint


def test_run_research_session_explicit_lineage_id_resume_is_still_allowed(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    _write_mandate_admission(lineage_root, accepted=False)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.lineage_id == "btc_leads_alts"
    assert status.lineage_mode == "explicit_resume"
    assert status.current_stage == "mandate_admission"


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
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")

    assert detect_session_stage(lineage_root) == "mandate_review_confirmation_pending"


def test_run_research_session_blocks_review_entry_when_mandate_preflight_fails(tmp_path: Path) -> None:
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
    (_stage_output_path(mandate_dir, "research_route.yaml")).write_text(
        yaml.safe_dump(
            {
                "research_route": "time_series_signal",
                "excluded_routes": ["cross_sectional_factor"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (_stage_output_path(mandate_dir, "time_split.json")).write_text(
        json.dumps(
            {
                "train": "",
                "test": "",
                "backtest": "",
                "holdout": "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (_stage_output_path(mandate_dir, "parameter_grid.yaml")).write_text(
        yaml.safe_dump({"parameters": []}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    write_fake_stage_provenance(lineage_root, "mandate")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_review_confirmation_pending"
    assert status.stage_status == "awaiting_author_fix"
    assert status.blocking_reason_code == "OUTPUTS_INVALID"
    assert "time_split.json" in (status.blocking_reason or "")
    assert "qros-mandate-author" in (status.next_action or "")


def test_run_research_session_does_not_record_review_confirmation_when_preflight_fails(tmp_path: Path) -> None:
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
    (_stage_output_path(mandate_dir, "research_route.yaml")).write_text(
        yaml.safe_dump(
            {
                "research_route": "time_series_signal",
                "excluded_routes": ["cross_sectional_factor"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (_stage_output_path(mandate_dir, "time_split.json")).write_text(
        json.dumps(
            {
                "train": "",
                "test": "",
                "backtest": "",
                "holdout": "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (_stage_output_path(mandate_dir, "parameter_grid.yaml")).write_text(
        yaml.safe_dump({"parameters": []}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    write_fake_stage_provenance(lineage_root, "mandate")

    status = run_research_session(
        outputs_root=outputs_root,
        lineage_id="btc_leads_alts",
        review_decision="CONFIRM_REVIEW",
    )

    assert status.current_stage == "mandate_review_confirmation_pending"
    assert status.stage_status == "awaiting_author_fix"
    assert not (mandate_dir / "author" / "draft" / "review_transition_approval.yaml").exists()


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
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")

    assert detect_session_stage(lineage_root) == "mandate_next_stage_confirmation_pending"


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
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")

    assert detect_session_stage(lineage_root) == "mandate_next_stage_confirmation_pending"


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
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_next_stage_confirmation_pending"
    assert "CONFIRM_NEXT_STAGE" in status.next_action


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
        (_stage_output_path(mandate_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")
    _write_display_decision(mandate_dir, stage="mandate")
    _write_yaml(_stage_draft_path(data_ready_dir, "data_ready_freeze_draft.yaml"), _data_ready_freeze_draft(confirmed=True))
    _write_yaml(
        _stage_draft_path(data_ready_dir, "data_ready_transition_approval.yaml"),
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_DATA_READY",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "mandate_review_complete",
        },
    )
    _write_next_stage_confirmation(mandate_dir, stage="mandate")

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
        "run_manifest.json",
        "rebuild_data_ready.py",
        "artifact_catalog.md",
        "field_dictionary.md",
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

    assert detect_session_stage(lineage_root) == "data_ready_review_confirmation_pending"


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

    assert detect_session_stage(lineage_root) == "data_ready_next_stage_confirmation_pending"


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

    assert detect_session_stage(lineage_root) == "data_ready_next_stage_confirmation_pending"


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

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "data_ready_next_stage_confirmation_pending"
    assert "CONFIRM_NEXT_STAGE" in status.next_action


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
    _write_display_decision(data_ready_dir, stage="data_ready")
    _write_yaml(_stage_draft_path(signal_ready_dir, "signal_ready_freeze_draft.yaml"), _signal_ready_freeze_draft(confirmed=True))
    _write_yaml(
        _stage_draft_path(signal_ready_dir, "signal_ready_transition_approval.yaml"),
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_SIGNAL_READY",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "data_ready_review_complete",
        },
    )
    _write_next_stage_confirmation(data_ready_dir, stage="data_ready")

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
        (_stage_output_path(signal_ready_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(signal_ready_dir, "params")).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "signal_ready")

    assert detect_session_stage(lineage_root) == "signal_ready_review_confirmation_pending"


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
        (_stage_output_path(signal_ready_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(signal_ready_dir, "params")).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "signal_ready")

    assert detect_session_stage(lineage_root) == "signal_ready_next_stage_confirmation_pending"


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
        (_stage_output_path(signal_ready_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(signal_ready_dir, "params")).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "signal_ready")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "signal_ready_next_stage_confirmation_pending"
    assert "CONFIRM_NEXT_STAGE" in status.next_action


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
        (_stage_output_path(signal_ready_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(signal_ready_dir, "params")).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "signal_ready")
    _write_display_decision(signal_ready_dir, stage="signal_ready")
    _write_yaml(_stage_draft_path(train_dir, "train_freeze_draft.yaml"), _train_freeze_draft(confirmed=True))
    _write_yaml(
        _stage_draft_path(train_dir, "train_transition_approval.yaml"),
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_TRAIN_FREEZE",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "signal_ready_review_complete",
        },
    )
    _write_next_stage_confirmation(signal_ready_dir, stage="signal_ready")

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
        (_stage_output_path(train_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "train_freeze")

    assert detect_session_stage(lineage_root) == "train_freeze_review_confirmation_pending"


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
        (_stage_output_path(train_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "train_freeze")

    assert detect_session_stage(lineage_root) == "train_freeze_next_stage_confirmation_pending"


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
        (_stage_output_path(train_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "train_freeze")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "train_freeze_next_stage_confirmation_pending"
    assert "CONFIRM_NEXT_STAGE" in status.next_action


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
        (_stage_output_path(train_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "train_freeze")
    _write_display_decision(train_dir, stage="train_freeze")
    _write_yaml(_stage_draft_path(test_dir, "test_evidence_draft.yaml"), _test_evidence_draft(confirmed=True))
    _write_yaml(
        _stage_draft_path(test_dir, "test_evidence_transition_approval.yaml"),
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_TEST_EVIDENCE",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "train_freeze_review_complete",
        },
    )
    _write_next_stage_confirmation(train_dir, stage="train_freeze")

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
        (_stage_output_path(test_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "test_evidence")

    assert detect_session_stage(lineage_root) == "test_evidence_review_confirmation_pending"


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
        (_stage_output_path(test_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "test_evidence")
    write_fake_stage_provenance(lineage_root, "test_evidence")

    assert detect_session_stage(lineage_root) == "test_evidence_next_stage_confirmation_pending"


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
        (_stage_output_path(test_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "test_evidence")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "test_evidence_next_stage_confirmation_pending"
    assert "CONFIRM_NEXT_STAGE" in status.next_action


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
        (_stage_output_path(test_dir, name)).write_text("ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "test_evidence")
    _write_display_decision(test_dir, stage="test_evidence")
    _write_yaml(_stage_draft_path(backtest_dir, "backtest_ready_draft.yaml"), _backtest_ready_draft(confirmed=True))
    _write_yaml(
        _stage_draft_path(backtest_dir, "backtest_ready_transition_approval.yaml"),
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_BACKTEST_READY",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "test_evidence_review_complete",
        },
    )
    _write_next_stage_confirmation(test_dir, stage="test_evidence")

    assert detect_session_stage(lineage_root) == "backtest_ready_author"


def test_detect_session_stage_returns_backtest_ready_review_when_outputs_exist(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    _write_minimal_stage_outputs(backtest_dir, stage="backtest_ready")

    assert detect_session_stage(lineage_root) == "backtest_ready_review_confirmation_pending"


def test_detect_session_stage_keeps_backtest_ready_author_when_engine_outputs_are_placeholder(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    test_dir = lineage_root / "05_test_evidence"
    backtest_dir = lineage_root / "06_backtest"
    _write_minimal_stage_outputs(test_dir, stage="test_evidence")
    _write_stage_completion_certificate(test_dir / "stage_completion_certificate.yaml")
    _write_display_decision(test_dir, stage="test_evidence")
    backtest_dir.mkdir(parents=True)
    _write_yaml(_stage_draft_path(backtest_dir, "backtest_ready_draft.yaml"), _backtest_ready_draft(confirmed=True))
    _write_yaml(
        _stage_draft_path(backtest_dir, "backtest_ready_transition_approval.yaml"),
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
        (_stage_output_path(backtest_dir, name)).write_text("ok\n", encoding="utf-8")
    for engine_name in ("vectorbt", "backtrader"):
        engine_dir = _stage_output_path(backtest_dir, engine_name)
        engine_dir.mkdir(parents=True, exist_ok=True)
        (engine_dir / "trades.parquet").write_text(
            f"placeholder trades artifact for {engine_name}\n",
            encoding="utf-8",
        )
        (engine_dir / "portfolio_summary.parquet").write_text(
            f"placeholder portfolio summary artifact for {engine_name}\n",
            encoding="utf-8",
        )

    _write_next_stage_confirmation(test_dir, stage="test_evidence")

    assert detect_session_stage(lineage_root) == "backtest_ready_author"


def test_detect_session_stage_returns_backtest_ready_review_complete_when_closure_exists(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    _write_minimal_stage_outputs(backtest_dir, stage="backtest_ready")
    _write_stage_completion_certificate(backtest_dir / "stage_completion_certificate.yaml")

    assert detect_session_stage(lineage_root) == "backtest_ready_next_stage_confirmation_pending"


def test_run_research_session_reports_next_holdout_validation_group(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    _write_minimal_stage_outputs(backtest_dir, stage="backtest_ready")
    _write_stage_completion_certificate(backtest_dir / "stage_completion_certificate.yaml")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "backtest_ready_next_stage_confirmation_pending"
    assert "CONFIRM_NEXT_STAGE" in status.next_action


def test_detect_session_stage_returns_holdout_validation_author_when_explicitly_confirmed(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    backtest_dir = lineage_root / "06_backtest"
    holdout_dir = lineage_root / "07_holdout"
    _write_minimal_stage_outputs(backtest_dir, stage="backtest_ready")
    holdout_dir.mkdir(parents=True)
    _write_stage_completion_certificate(backtest_dir / "stage_completion_certificate.yaml")
    _write_display_decision(backtest_dir, stage="backtest_ready")
    _write_yaml(
        _stage_draft_path(holdout_dir, "holdout_validation_draft.yaml"),
        _holdout_validation_draft(confirmed=True),
    )
    _write_yaml(
        _stage_draft_path(holdout_dir, "holdout_validation_transition_approval.yaml"),
        {
            "lineage_id": "btc_leads_alts",
            "decision": "CONFIRM_HOLDOUT_VALIDATION",
            "approved_by": "tester",
            "approved_at": "2026-03-25T10:00:00Z",
            "source_stage": "backtest_ready_review_complete",
        },
    )
    _write_next_stage_confirmation(backtest_dir, stage="backtest_ready")

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
        (_stage_output_path(holdout_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(holdout_dir, "window_results")).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "holdout_validation")

    assert detect_session_stage(lineage_root) == "holdout_validation_review_confirmation_pending"


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
        (_stage_output_path(holdout_dir, name)).write_text("ok\n", encoding="utf-8")
    (_stage_output_path(holdout_dir, "window_results")).mkdir(parents=True, exist_ok=True)
    write_fake_stage_provenance(lineage_root, "holdout_validation")

    assert detect_session_stage(lineage_root) == "holdout_validation_next_stage_confirmation_pending"


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
        ("mandate", lineage_root / "01_mandate", "mandate_next_stage_confirmation_pending"),
        ("data_ready", lineage_root / "02_data_ready", "data_ready_next_stage_confirmation_pending"),
        ("signal_ready", lineage_root / "03_signal_ready", "signal_ready_next_stage_confirmation_pending"),
        ("train_freeze", lineage_root / "04_train_freeze", "train_freeze_next_stage_confirmation_pending"),
        ("test_evidence", lineage_root / "05_test_evidence", "test_evidence_next_stage_confirmation_pending"),
        ("backtest_ready", lineage_root / "06_backtest", "backtest_ready_next_stage_confirmation_pending"),
        ("holdout_validation", lineage_root / "07_holdout", "holdout_validation_next_stage_confirmation_pending"),
    ]

    for stage, stage_dir, expected_stage in cases:
        _write_minimal_stage_outputs(stage_dir, stage=stage)
        _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")

        assert detect_session_stage(lineage_root) == expected_stage, stage


def test_run_research_session_enters_next_stage_confirmation_after_completed_display(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    mandate_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(mandate_dir, stage="mandate")
    _write_stage_completion_certificate(mandate_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_fake_stage_provenance(lineage_root, "mandate")
    _write_display_decision(mandate_dir, stage="mandate")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_next_stage_confirmation_pending"
    assert status.gate_status == "NEXT_STAGE_CONFIRMATION_PENDING"
    assert "CONFIRM_NEXT_STAGE" in status.next_action


def test_detect_session_stage_routes_mainline_and_csf_through_display_confirmation_before_advancing(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    mainline_root = outputs_root / "mainline_case"
    csf_root = outputs_root / "csf_case"

    mainline_cases = [
        ("data_ready", mainline_root / "02_data_ready", "data_ready_next_stage_confirmation_pending"),
        ("signal_ready", mainline_root / "03_signal_ready", "signal_ready_next_stage_confirmation_pending"),
        ("train_freeze", mainline_root / "04_train_freeze", "train_freeze_next_stage_confirmation_pending"),
    ]
    for stage, stage_dir, expected in mainline_cases:
        _write_minimal_stage_outputs(stage_dir, stage=stage)
        _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
        write_fake_stage_provenance(mainline_root, stage)
        assert detect_session_stage(mainline_root) == expected

    mandate_dir = csf_root / "01_mandate"
    _write_minimal_stage_outputs(mandate_dir, stage="mandate")
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
    write_fake_stage_provenance(csf_root, "mandate")
    assert detect_session_stage(csf_root) == "mandate_next_stage_confirmation_pending"

    csf_cases = [
        ("csf_data_ready", csf_root / "02_csf_data_ready", "csf_data_ready_next_stage_confirmation_pending"),
        ("csf_signal_ready", csf_root / "03_csf_signal_ready", "csf_signal_ready_next_stage_confirmation_pending"),
        ("csf_train_freeze", csf_root / "04_csf_train_freeze", "csf_train_freeze_next_stage_confirmation_pending"),
        ("csf_test_evidence", csf_root / "05_csf_test_evidence", "csf_test_evidence_next_stage_confirmation_pending"),
        ("csf_backtest_ready", csf_root / "06_csf_backtest_ready", "csf_backtest_ready_next_stage_confirmation_pending"),
        ("csf_holdout_validation", csf_root / "07_csf_holdout_validation", "csf_holdout_validation_next_stage_confirmation_pending"),
    ]
    for stage, stage_dir, expected in csf_cases:
        _write_minimal_stage_outputs(stage_dir, stage=stage)
        _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
        write_fake_stage_provenance(csf_root, stage.removeprefix("csf_"))
        assert detect_session_stage(csf_root) == expected


def test_run_research_session_routes_final_holdout_into_terminal_next_stage_confirmation_after_display(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    holdout_dir = lineage_root / "07_holdout"
    _write_minimal_stage_outputs(holdout_dir, stage="holdout_validation")
    _write_stage_completion_certificate(holdout_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    write_fake_stage_provenance(lineage_root, "holdout_validation")
    _write_display_decision(holdout_dir, stage="holdout_validation")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "holdout_validation_next_stage_confirmation_pending"
    assert "terminal completion confirmation" in (status.blocking_reason or "")


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


def test_run_research_session_requires_failure_handling_on_non_advancing_csf_review_verdicts(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    cases = [
        (
            "csf_data_retry",
            "RETRY",
            "csf_data_ready",
            "02_csf_data_ready",
            "csf_data_ready_review",
        ),
        (
            "csf_signal_child_lineage",
            "CHILD LINEAGE",
            "csf_signal_ready",
            "03_csf_signal_ready",
            "csf_signal_ready_review",
        ),
        (
            "csf_train_pass_for_retry",
            "PASS FOR RETRY",
            "csf_train_freeze",
            "04_csf_train_freeze",
            "csf_train_freeze_review",
        ),
        (
            "csf_test_retry",
            "RETRY",
            "csf_test_evidence",
            "05_csf_test_evidence",
            "csf_test_evidence_review",
        ),
        (
            "csf_backtest_no_go",
            "NO-GO",
            "csf_backtest_ready",
            "06_csf_backtest_ready",
            "csf_backtest_ready_review",
        ),
        (
            "csf_holdout_no_go",
            "NO-GO",
            "csf_holdout_validation",
            "07_csf_holdout_validation",
            "csf_holdout_validation_review",
        ),
    ]

    for lineage_id, verdict, stage, stage_dir_name, expected_stage in cases:
        lineage_root = outputs_root / lineage_id
        mandate_dir = lineage_root / "01_mandate"
        mandate_dir.mkdir(parents=True, exist_ok=True)
        _write_yaml(
            _stage_output_path(mandate_dir, "research_route.yaml"),
            {
                "research_route": "cross_sectional_factor",
                "factor_role": "standalone_alpha",
                "factor_structure": "single_factor",
                "portfolio_expression": "long_short_market_neutral",
                "neutralization_policy": "group_neutral",
            },
        )
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


def test_latest_review_failure_status_covers_tss_route_specific_stages(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    cases = [
        ("tss_data_ready", "02_tss_data_ready", "tss_data_ready_review"),
        ("tss_signal_ready", "03_tss_signal_ready", "tss_signal_ready_review"),
        ("tss_train_freeze", "04_tss_train_freeze", "tss_train_freeze_review"),
        ("tss_test_evidence", "05_tss_test_evidence", "tss_test_evidence_review"),
        ("tss_backtest_ready", "06_tss_backtest_ready", "tss_backtest_ready_review"),
        ("tss_holdout_validation", "07_tss_holdout_validation", "tss_holdout_validation_review"),
    ]

    for stage, stage_dir_name, expected_stage in cases:
        lineage_root = outputs_root / f"{stage}_failure_case"
        mandate_dir = lineage_root / "01_mandate"
        _write_yaml(
            _stage_output_path(mandate_dir, "research_route.yaml"),
            {"research_route": "time_series_signal"},
        )
        stage_dir = lineage_root / stage_dir_name
        _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")

        verdict, requires_failure_handling, failure_stage, reason = _latest_review_failure_status(lineage_root)

        assert verdict == "NO-GO"
        assert requires_failure_handling is True
        assert failure_stage == expected_stage
        assert reason == f"{expected_stage} requires failure handling because review verdict is NO-GO."


def test_run_research_session_requires_failure_disposition_after_blocking_failure_package(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_k"
    mandate_dir = lineage_root / "01_mandate"
    _write_yaml(
        _stage_output_path(mandate_dir, "research_route.yaml"),
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "short_only_rank",
            "neutralization_policy": "none",
        },
    )
    backtest_dir = lineage_root / "06_csf_backtest_ready"
    _write_minimal_stage_outputs(backtest_dir, stage="csf_backtest_ready")
    _write_failure_post_retry_decision(backtest_dir)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_alt_k")

    assert status.current_stage == "csf_backtest_ready_review_confirmation_pending"
    assert status.stage_status == "failure_disposition_required"
    assert status.blocking_reason_code == "FAILURE_DISPOSITION_REQUIRED"
    assert status.gate_status == "FAILURE_DISPOSITION_REQUIRED"
    assert status.current_skill == "qros-stage-failure-handler"
    assert status.requires_failure_handling is True
    assert status.failure_stage == "csf_backtest_ready"
    assert "failure_disposition.yaml" in status.next_action
    assert "NO_GO" in status.next_action
    assert "CHILD_LINEAGE" in status.next_action


def test_run_research_session_does_not_write_review_confirmation_when_failure_disposition_required(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_k"
    mandate_dir = lineage_root / "01_mandate"
    _write_yaml(
        _stage_output_path(mandate_dir, "research_route.yaml"),
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "short_only_rank",
            "neutralization_policy": "none",
        },
    )
    backtest_dir = lineage_root / "06_csf_backtest_ready"
    _write_minimal_stage_outputs(backtest_dir, stage="csf_backtest_ready")
    _write_failure_post_retry_decision(backtest_dir)

    status = run_research_session(
        outputs_root=outputs_root,
        lineage_id="btc_alt_k",
        review_decision="CONFIRM_REVIEW",
    )

    assert status.blocking_reason_code == "FAILURE_DISPOSITION_REQUIRED"
    assert not (backtest_dir / "author" / "draft" / "review_transition_approval.yaml").exists()


def test_detect_session_stage_review_eligible_csf_test_evidence_failure_handler_blocks_review_confirmation_pending(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_review_blocked"
    mandate_dir = lineage_root / "01_mandate"
    _write_yaml(
        _stage_output_path(mandate_dir, "research_route.yaml"),
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
        },
    )
    stage_dir = lineage_root / "05_csf_test_evidence"
    _write_minimal_stage_outputs(stage_dir, stage="csf_test_evidence")
    _write_review_eligibility(
        lineage_root,
        {
            "failure_package": {
                "stage": "csf_test_evidence",
                "reason_code": "CSF_TEST_EVIDENCE_FAILURE_HANDLER_REQUIRED",
                "reason": "Canonical review eligibility blocked review entry for csf_test_evidence.",
                "failure_reason_summary": "Canonical review eligibility requires failure handling for csf_test_evidence.",
            }
        },
    )

    assert detect_session_stage(lineage_root) == "csf_test_evidence_review"

    status = run_research_session(outputs_root=outputs_root, lineage_id="csf_review_blocked")

    assert status.current_stage == "csf_test_evidence_review"
    assert status.stage_status == "blocked_requires_failure_handling"
    assert status.blocking_reason_code == "FAILURE_HANDLER_REQUIRED"
    assert status.current_skill == "qros-stage-failure-handler"
    assert status.gate_status == "FAILURE_HANDLING_REQUIRED"
    assert status.requires_failure_handling is True
    assert status.review_verdict is None
    assert status.failure_stage == "csf_test_evidence"
    assert status.failure_reason_summary == "Canonical review eligibility requires failure handling for csf_test_evidence."


def test_run_research_session_review_eligible_csf_test_evidence_failure_handler_does_not_write_review_confirmation(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_review_blocked"
    mandate_dir = lineage_root / "01_mandate"
    _write_yaml(
        _stage_output_path(mandate_dir, "research_route.yaml"),
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
        },
    )
    stage_dir = lineage_root / "05_csf_test_evidence"
    _write_minimal_stage_outputs(stage_dir, stage="csf_test_evidence")
    _write_review_eligibility(
        lineage_root,
        {
            "failure_package": {
                "stage": "csf_test_evidence",
                "reason_code": "CSF_TEST_EVIDENCE_FAILURE_HANDLER_REQUIRED",
                "reason": "Canonical review eligibility blocked review entry for csf_test_evidence.",
                "failure_reason_summary": "Canonical review eligibility requires failure handling for csf_test_evidence.",
            }
        },
    )

    status = run_research_session(
        outputs_root=outputs_root,
        lineage_id="csf_review_blocked",
        review_decision="CONFIRM_REVIEW",
    )

    assert status.current_stage == "csf_test_evidence_review"
    assert status.current_skill == "qros-stage-failure-handler"
    assert status.review_verdict is None
    assert not (stage_dir / "author" / "draft" / "review_transition_approval.yaml").exists()


def test_run_research_session_keeps_disposed_failure_from_reentering_review(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_k"
    mandate_dir = lineage_root / "01_mandate"
    _write_yaml(
        _stage_output_path(mandate_dir, "research_route.yaml"),
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "short_only_rank",
            "neutralization_policy": "none",
        },
    )
    backtest_dir = lineage_root / "06_csf_backtest_ready"
    _write_minimal_stage_outputs(backtest_dir, stage="csf_backtest_ready")
    failure_package_dir = _write_failure_post_retry_decision(backtest_dir)
    _write_failure_disposition(failure_package_dir, decision="NO_GO")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_alt_k")

    assert status.current_stage == "csf_backtest_ready_review_confirmation_pending"
    assert status.stage_status == "failure_disposition_recorded"
    assert status.blocking_reason_code == "FAILURE_DISPOSITION_RECORDED"
    assert status.gate_status == "FAILURE_DISPOSITION_RECORDED"
    assert status.current_skill == "qros-lineage-change-control"
    assert status.requires_failure_handling is True
    assert status.failure_stage == "csf_backtest_ready"
    assert "NO_GO" in (status.failure_reason_summary or "")
    assert "must not re-enter review" in status.next_action


def test_run_research_session_ignores_removed_review_governance_lane(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "governance_case"
    lineage_root = outputs_root / lineage_id
    mandate_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(mandate_dir, stage="mandate")
    _write_adversarial_review_request(
        mandate_dir,
        stage="mandate",
        program_dir="program/mandate",
    )
    _write_reviewer_receipt(mandate_dir)
    _write_adversarial_review_result(
        mandate_dir,
        stage="mandate",
        program_dir="program/mandate",
        outcome="CLOSURE_READY_PASS",
    )
    _write_stage_completion_certificate(mandate_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    _write_next_stage_confirmation(mandate_dir, stage="mandate")

    governance_root = tmp_path / "governance"
    candidate_path = governance_root / "candidates" / "review-pending-governance.yaml"
    _write_yaml(
        candidate_path,
        {
            "candidate_id": "review-pending-governance",
            "candidate_class": "template_constraint",
            "policy_activation_state": "inactive",
            "status": "awaiting_governance_decision",
            "distinct_review_cycles": 3,
            "distinct_contexts": ["governance_case::mandate"],
            "evidence_records": [],
            "decision_ref": None,
            "updated_at": "2026-04-15T12:00:00Z",
        },
    )
    _write_yaml(
        governance_root / "pending_decisions" / "review-pending-governance.yaml",
        {
            "candidate_id": "review-pending-governance",
            "decision_outcome": "approved",
            "decision_note": "User approved this for follow-up repo work.",
        },
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)

    assert status.current_stage == "tss_data_ready_confirmation_pending"
    assert status.stage_status == "awaiting_freeze_approval"
    assert status.blocking_reason_code == "FREEZE_APPROVAL_MISSING"
    assert "governance" not in (status.blocking_reason or "").lower()


def test_run_research_session_marks_pass_reviews_as_not_requiring_failure_handling(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "05_test_evidence"

    _write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "test_evidence_next_stage_confirmation_pending"
    assert status.review_verdict == "PASS"
    assert status.requires_failure_handling is False
    assert status.failure_stage is None
    assert status.failure_reason_summary is None


def test_run_research_session_clears_intake_open_risks_after_routing_into_csf_data_ready(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_case"
    mandate_dir = lineage_root / "01_mandate"
    intake_dir = lineage_root / "00_idea_intake"
    mandate_dir.mkdir(parents=True)
    intake_dir.mkdir(parents=True)

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
    _write_stage_completion_certificate(mandate_dir / "stage_completion_certificate.yaml")
    write_fake_stage_provenance(lineage_root, "mandate")

    status = run_research_session(outputs_root=outputs_root, lineage_id="csf_case")

    assert status.current_stage == "mandate_next_stage_confirmation_pending"
    assert status.open_risks == []


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
    assert status.gate_status == "ADVERSARIAL_REVIEW_PENDING"
    assert "qros-mandate-review" in status.next_action
    assert "review/final_review.yaml" in status.next_action


def test_run_research_session_does_not_route_mandate_review_eligibility_block_into_failure_handler(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_review_eligibility(
        lineage_root,
        {
            "failure_package": {
                "stage": "mandate",
                "reason_code": "MANDATE_REVIEW_BLOCKED",
                "reason": "Canonical review eligibility blocked mandate review entry.",
                "failure_reason_summary": "Canonical review eligibility blocked mandate review entry.",
            }
        },
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert detect_session_stage(lineage_root) == "mandate_review_confirmation_pending"
    assert status.current_stage == "mandate_review_confirmation_pending"
    assert status.stage_status == "awaiting_author_fix"
    assert status.current_skill == "qros-mandate-author"
    assert status.gate_status == "OUTPUTS_INVALID"
    assert status.blocking_reason_code == "OUTPUTS_INVALID"
    assert status.requires_failure_handling is False
    assert status.failure_stage is None
    assert status.failure_reason_summary is None


def test_run_research_session_stays_in_author_fix_when_data_viability_contract_fails(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "coverage_blocked_case"
    _write_mandate_admission(lineage_root, accepted=True, include_route=True)
    inventory_root = _write_data_inventory(
        tmp_path / "inventory",
        data_min_ts="2024-03-01",
        data_max_ts="2024-12-31",
    )
    freeze_draft = _freeze_draft(confirmed=False)
    freeze_draft["groups"]["scope_contract"]["draft"]["time_boundary"] = "2023-01-01/2026-03-01"
    freeze_draft["groups"]["data_contract"]["draft"]["data_source"] = str(inventory_root)
    _write_yaml(
        lineage_root / "01_mandate" / "author" / "draft" / "mandate_freeze_draft.yaml",
        freeze_draft,
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="coverage_blocked_case")

    assert status.current_stage == "mandate_freeze_confirmation_pending"
    assert status.stage_status == "awaiting_author_fix"
    assert status.blocking_reason_code == "TIME_COVERAGE_OUT_OF_RANGE"
    assert status.gate_status == "OUTPUTS_INVALID"
    assert status.current_skill == "qros-research-session"
    assert "Adjust train/test/backtest/holdout" in status.next_action
    assert "review-ready" not in status.next_action.lower()


def test_run_research_session_does_not_route_mandate_confirm_review_into_failure_handler_when_review_eligibility_truth_blocks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    monkeypatch.setattr(
        "runtime.tools.research_session._review_entry_preflight_payload",
        lambda **kwargs: {
            "stage": "mandate",
            "lineage_id": lineage_root.name,
            "status": "PASS",
            "content_findings": [],
            "upstream_binding_findings": [],
        },
    )
    _write_review_eligibility(
        lineage_root,
        {
            "failure_package": {
                "stage": "mandate",
                "reason_code": "MANDATE_REVIEW_BLOCKED",
                "reason": "Canonical review eligibility blocked mandate review entry.",
                "failure_reason_summary": "Canonical review eligibility blocked mandate review entry.",
            }
        },
    )

    status = run_research_session(
        outputs_root=outputs_root,
        lineage_id="btc_leads_alts",
        review_decision="CONFIRM_REVIEW",
    )

    assert status.current_stage == "mandate_review_confirmation_pending"
    assert status.current_skill == "qros-mandate-author"
    assert status.requires_failure_handling is False
    assert status.failure_stage is None
    assert status.failure_reason_summary is None
    assert not (stage_dir / "author" / "draft" / "review_transition_approval.yaml").exists()


def test_detect_session_stage_keeps_blocked_mandate_review_pending_even_with_confirm_review_approval(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_review_eligibility(
        lineage_root,
        {
            "failure_package": {
                "stage": "mandate",
                "reason_code": "MANDATE_REVIEW_BLOCKED",
                "reason": "Canonical review eligibility blocked mandate review entry.",
                "failure_reason_summary": "Canonical review eligibility blocked mandate review entry.",
            }
        },
    )
    _write_yaml(
        stage_dir / "author" / "draft" / "review_transition_approval.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "decision": "CONFIRM_REVIEW",
            "approved_by": "tester",
            "approved_at": "2026-05-22T10:00:00Z",
            "source_stage": "mandate_review_confirmation_pending",
        },
    )

    assert detect_session_stage(lineage_root) == "mandate_review_confirmation_pending"

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_review_confirmation_pending"
    assert status.current_skill == "qros-mandate-author"
    assert status.requires_failure_handling is False
    assert status.failure_stage is None
    assert status.failure_reason_summary is None


def test_run_research_session_exposes_author_fix_substate_for_fix_required_review(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage="mandate",
        program_dir="program/mandate",
        outcome="FIX_REQUIRED",
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_review"
    assert status.stage_status == "awaiting_author_fix"
    assert status.blocking_reason_code == "AUTHOR_FIX_REQUIRED"
    assert status.current_skill == "qros-mandate-author"
    assert status.gate_status == "AUTHOR_FIX_REQUIRED"
    assert "author-fix skill" in status.why_this_skill
    assert "review/final_review.yaml" in status.next_action
    assert "fresh reviewer cycle" in status.next_action


def test_run_research_session_exposes_review_closure_substate_after_closure_ready_result(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    _write_adversarial_review_result(
        stage_dir,
        stage="mandate",
        program_dir="program/mandate",
        outcome="CLOSURE_READY_PASS",
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_stage == "mandate_review"
    assert status.stage_status == "awaiting_review_closure"
    assert status.blocking_reason_code == "REVIEW_CLOSURE_PENDING"
    assert status.gate_status == "REVIEW_CLOSURE_PENDING"
    assert status.current_skill == "qros-mandate-review"


def test_run_research_session_reports_reviewer_unbound_for_bare_final_review(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_yaml(
        stage_dir / "review" / "final_review.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "verdict": "PASS",
        },
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.stage_status == "reviewer_unbound"
    assert status.blocking_reason_code == "REVIEWER_UNBOUND"
    assert status.review_state == "review_in_progress"


def test_run_research_session_reports_review_format_invalid_for_malformed_final_review(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    (stage_dir / "review" / "final_review.yaml").write_text(
        "lineage_id: [unterminated\n",
        encoding="utf-8",
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.stage_status == "review_format_invalid"
    assert status.blocking_reason_code == "REVIEW_FORMAT_INVALID"


def test_run_research_session_reports_author_outputs_stale_after_prepare(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    (stage_dir / "author" / "formal" / "mandate.md").write_text("mutated after prepare\n", encoding="utf-8")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.stage_status == "author_outputs_stale"
    assert status.blocking_reason_code == "AUTHOR_OUTPUTS_STALE"


def test_run_research_session_accepts_mapping_findings_in_raw_final_review(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    _write_yaml(
        stage_dir / "review" / "final_review.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "reviewer_identity": "reviewer-agent",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewed_artifact_paths": ["artifact_catalog.md"],
            "reviewed_program_path": "program/mandate/run_stage.py",
            "reviewed_artifact_digest": "sha256:test-artifact-digest",
            "reviewed_program_digest": "sha256:test-program-digest",
            "verdict": "PASS",
            "review_summary": "test review fixture",
            "blocking_findings": [],
            "reservation_findings": [{"id": "I1", "text": "object finding"}],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "rollback_stage": None,
            "downstream_permissions": [],
            "recommended_next_action": "test review fixture",
        },
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.stage_status == "review_scope_mismatch"
    assert status.blocking_reason_code == "REVIEW_SCOPE_MISMATCH"


def test_summarize_session_status_contains_required_fields(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"

    status = summarize_session_status(
        lineage_id="btc_leads_alts",
        lineage_root=lineage_root,
        lineage_mode="fresh_start",
        lineage_selection_reason="raw_idea resolved to fresh lineage slug btc_leads_alts.",
        current_stage="idea_intake",
        current_route=None,
        artifacts_written=["00_idea_intake/idea_brief.md"],
        gate_status="NEEDS_REFRAME",
        next_action="Fill qualification inputs",
    )

    assert status.lineage_id == "btc_leads_alts"
    assert status.lineage_root == lineage_root
    assert status.lineage_mode == "fresh_start"
    assert status.lineage_selection_reason is not None
    assert status.current_orchestrator == "qros-research-session"
    assert status.current_stage == "idea_intake"
    assert status.artifacts_written == ["00_idea_intake/idea_brief.md"]
    assert status.gate_status == "NEEDS_REFRAME"
    assert status.next_action == "Fill qualification inputs"
    assert status.current_skill == "qros-idea-intake-author"
    assert "idea_intake" in status.why_this_skill
    assert status.blocking_reason == "Idea intake inputs or admission evidence are still incomplete."
    assert "Continue with qros-idea-intake-author for lineage btc_leads_alts" in status.resume_hint
    assert status.review_verdict is None
    assert status.requires_failure_handling is False
    assert status.failure_stage is None
    assert status.failure_reason_summary is None


def test_summarize_session_status_review_complete_clears_blocking_reason(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"

    status = summarize_session_status(
        lineage_id="btc_leads_alts",
        lineage_root=lineage_root,
        lineage_mode="explicit_resume",
        lineage_selection_reason="Explicit lineage_id btc_leads_alts was provided, so qros-session is targeting that lineage directly.",
        current_stage="holdout_validation_review_complete",
        current_route="time_series_signal",
        artifacts_written=[],
        gate_status="REVIEW_COMPLETE",
        next_action="Archive lineage and stop.",
    )

    assert status.current_skill == "qros-research-session"
    assert status.blocking_reason is None
    assert "terminal review-complete state" in status.why_this_skill


def test_run_research_session_exposes_visibility_fields_for_failure_handling(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "05_test_evidence"

    _write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="RETRY")

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_leads_alts")

    assert status.current_orchestrator == "qros-research-session"
    assert status.current_stage == "test_evidence_review"
    assert status.current_skill == "qros-stage-failure-handler"
    assert status.why_this_skill == (
        "Review verdict RETRY blocks normal progression, so failure handling is now the active workflow."
    )
    assert status.blocking_reason == "Normal progression is blocked by review verdict RETRY."
    assert "qros-stage-failure-handler" in status.resume_hint
