from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.review_skillgen.review_engine import run_stage_review
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    run_reviewer_write_scope_audit,
    write_reviewer_write_scope_baseline,
)
from tests.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.test_research_session_runtime import _write_minimal_stage_outputs


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_parquet(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys())
    columns = {key: [row[key] for row in rows] for key in keys}
    pq.write_table(pa.table(columns), path)


def _prepare_csf_stage(tmp_path: Path, *, stage_key: str, stage_dir_name: str) -> Path:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / stage_dir_name
    _write_minimal_stage_outputs(stage_dir, stage=stage_key)
    mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(
        mandate_formal_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "portfolio_expression": "short_only_rank",
        },
    )
    ensure_stage_program(lineage_root, stage_key)
    write_fake_stage_provenance(lineage_root, stage_key)
    return stage_dir


def _write_review_request_and_result(stage_dir: Path, *, stage: str) -> None:
    required_artifact_paths: list[str] = []
    required_provenance_paths = ["program_execution_manifest.json"]
    launcher_handoff_context_paths: list[str] = []
    handoff_manifest_path = stage_dir / "review" / "request" / "spawned_reviewer_handoff_manifest.yaml"
    _write_yaml(
        handoff_manifest_path,
        {
            "review_cycle_id": f"{stage}-cycle-1",
            "lineage_id": stage_dir.parent.name,
            "stage": stage,
            "required_program_dir": f"program/cross_sectional_factor/{stage}",
            "required_program_entrypoint": "run_stage.py",
            "required_artifact_paths": required_artifact_paths,
            "required_provenance_paths": required_provenance_paths,
            "permitted_input_roots": ["review/request", "author/formal"],
            "permitted_output_roots": ["review/result"],
            "required_result_write_root": "review/result",
            "launcher_review_ready_status": "complete",
            "launcher_checked_artifact_paths": required_artifact_paths,
            "launcher_checked_provenance_paths": required_provenance_paths,
            "launcher_handoff_context_paths": launcher_handoff_context_paths,
        },
    )
    handoff_manifest_digest = hashlib.sha256(
        handoff_manifest_path.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    request_payload = {
        "review_cycle_id": f"{stage}-cycle-1",
        "lineage_id": stage_dir.parent.name,
        "stage": stage,
        "author_identity": "author-agent",
        "author_session_id": "author-session",
        "required_program_dir": f"program/cross_sectional_factor/{stage}",
        "required_program_entrypoint": "run_stage.py",
        "required_artifact_paths": required_artifact_paths,
        "required_provenance_paths": required_provenance_paths,
        "required_reviewer_mode": "adversarial",
        "handoff_manifest_path": "review/request/spawned_reviewer_handoff_manifest.yaml",
        "handoff_manifest_digest": handoff_manifest_digest,
        "required_result_write_root": "review/result",
        "launcher_review_ready_status": "complete",
        "launcher_checked_artifact_paths": required_artifact_paths,
        "launcher_checked_provenance_paths": required_provenance_paths,
        "launcher_handoff_context_paths": launcher_handoff_context_paths,
    }
    receipt_payload = {
        "review_cycle_id": f"{stage}-cycle-1",
        "launcher_owner": "qros-runtime-launcher",
        "launcher_session_id": "launcher-session",
        "launcher_thread_id": "leader-thread",
        "spawn_mode": "spawned_agent",
        "spawned_agent_id": "reviewer-child-agent",
        "fork_context": False,
        "write_root": "review/result",
        "handoff_manifest_path": "review/request/spawned_reviewer_handoff_manifest.yaml",
        "handoff_manifest_digest": handoff_manifest_digest,
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "review-session",
        "receipt_written_at": "2026-04-17T03:00:00Z",
    }
    result_payload = {
        "review_cycle_id": f"{stage}-cycle-1",
        "reviewer_identity": "reviewer-agent",
        "reviewer_role": "reviewer",
        "reviewer_session_id": "review-session",
        "reviewer_mode": "adversarial",
        "reviewer_agent_id": "reviewer-child-agent",
        "reviewer_execution_mode": "spawned_agent",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_manifest_digest": handoff_manifest_digest,
        "review_loop_outcome": "CLOSURE_READY_PASS",
        "reviewed_program_dir": f"program/cross_sectional_factor/{stage}",
        "reviewed_program_entrypoint": "run_stage.py",
        "reviewed_artifact_paths": required_artifact_paths,
        "reviewed_provenance_paths": required_provenance_paths,
        "blocking_findings": [],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "downstream_permissions": [],
    }
    _write_yaml(stage_dir / "review" / "request" / "adversarial_review_request.yaml", request_payload)
    _write_yaml(stage_dir / "review" / "request" / "spawned_reviewer_receipt.yaml", receipt_payload)
    write_reviewer_write_scope_baseline(
        stage_dir,
        review_cycle_id=receipt_payload["review_cycle_id"],
        launcher_thread_id=receipt_payload["launcher_thread_id"],
        spawned_agent_id=receipt_payload["spawned_agent_id"],
    )
    _write_yaml(stage_dir / "review" / "result" / "adversarial_review_result.yaml", result_payload)
    run_reviewer_write_scope_audit(stage_dir)


def test_run_stage_review_blocks_csf_test_evidence_when_rank_ic_is_non_positive(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_test_evidence",
        stage_dir_name="05_csf_test_evidence",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_json(
        formal_dir / "rank_ic_summary.json",
        {
            "variant_id": "fragility_v1_q5_beta_neutral_h3",
            "mean_rank_ic": -0.7698,
            "median_rank_ic": -0.8117,
            "num_dates": 140,
        },
    )
    (formal_dir / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    (formal_dir / "csf_test_gate_decision.md").write_text("metric gate snapshot\n", encoding="utf-8")
    _write_review_request_and_result(stage_dir, stage="csf_test_evidence")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("mean_rank_ic" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_backtest_ready_when_net_return_is_non_positive(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_backtest_ready",
        stage_dir_name="06_csf_backtest_ready",
    )
    formal_dir = stage_dir / "author" / "formal"
    with (formal_dir / "csf_backtest_gate_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["selected_variant_id", "portfolio_expression", "mean_net_return", "max_drawdown", "after_cost_rule"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "selected_variant_id": "fragility_v1_q5_beta_neutral_h3",
                "portfolio_expression": "short_only_rank",
                "mean_net_return": -0.06565512737954216,
                "max_drawdown": -0.9999459848592996,
                "after_cost_rule": "all primary economics must be reported net of cost, not gross-only",
            }
        )
    _write_json(
        formal_dir / "drawdown_report.json",
        {
            "max_drawdown": -0.9999459848592996,
            "ending_equity": 0.0000528,
            "num_rebalance_dates": 140,
        },
    )
    (formal_dir / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    (formal_dir / "engine_compare.csv").write_text("engine,status\nvectorbt,ok\n", encoding="utf-8")
    (formal_dir / "csf_backtest_gate_decision.md").write_text("metric gate snapshot\n", encoding="utf-8")
    _write_review_request_and_result(stage_dir, stage="csf_backtest_ready")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("mean_net_return" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_holdout_validation_when_direction_flips(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_holdout_validation",
        stage_dir_name="07_csf_holdout_validation",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet(
        formal_dir / "holdout_test_compare.parquet",
        [
            {
                "selected_variant_id": "fragility_v1_q5_beta_neutral_h3",
                "portfolio_expression": "short_only_rank",
                "mean_net_return": 0.0125,
                "max_drawdown": -0.9999459848592996,
                "holdout_mean_net_return": 0.0125,
                "direction_match": False,
            }
        ],
    )
    _write_json(
        formal_dir / "rolling_holdout_stability.json",
        {
            "num_holdout_dates": 140,
            "mean_net_return": 0.0125,
            "max_drawdown": -0.9999459848592996,
            "coverage_names_mean": 1.15,
        },
    )
    (formal_dir / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    _write_review_request_and_result(stage_dir, stage="csf_holdout_validation")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("aligned" in item or "observed=False" in item for item in payload["blocking_findings"])
