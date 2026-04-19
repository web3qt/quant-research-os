from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from subprocess import run
import sys

import yaml

from tests.helpers.lineage_program_support import ensure_stage_program
from tests.helpers.repo_paths import REPO_ROOT


def _copy_repo_fixture(tmp_path: Path) -> Path:
    fixture_root = tmp_path / "fixture-repo"
    shutil.copytree(
        REPO_ROOT,
        fixture_root,
        ignore=shutil.ignore_patterns(".git", ".worktrees", ".pytest_cache", "__pycache__", "*.pyc"),
    )
    return fixture_root


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _route_assessment() -> dict:
    return {
        "candidate_routes": ["cross_sectional_factor", "time_series_signal"],
        "recommended_route": "cross_sectional_factor",
        "why_recommended": ["Cross-asset sorting is the primary expression."],
        "why_not_other_routes": {"time_series_signal": ["Single-asset direction is secondary."]},
        "route_risks": ["Universe breadth may be limited."],
        "route_decision_pending": True,
    }


def _mandate_freeze_draft(*, confirmed: bool) -> dict:
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
                "draft": {
                    "market": "binance perp",
                    "universe": "high liquidity alts",
                    "target_task": "study",
                },
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


def _run_qros_session(project_root: Path, env: dict[str, str], *args: str):
    return run(
        [str(project_root / ".qros" / "bin" / "qros-session"), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )


def test_qros_session_temp_repo_smoke_reaches_mandate_review_gate(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    project_root = tmp_path / "research-project"
    project_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"

    setup_result = run(
        [str(fixture_root / "setup"), "--host", "codex", "--mode", "repo-local"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )
    assert setup_result.returncode == 0, setup_result.stderr

    first_result = _run_qros_session(
        project_root,
        env,
        "--raw-idea",
        "BTC leads high-liquidity alts after shock events",
    )
    assert first_result.returncode == 0, first_result.stderr
    assert "Current stage: idea_intake_confirmation_pending" in first_result.stdout

    outputs_root = project_root / "outputs"
    lineage_dirs = sorted(path for path in outputs_root.iterdir() if path.is_dir())
    assert len(lineage_dirs) == 1
    lineage_root = lineage_dirs[0]
    lineage_id = lineage_root.name
    intake_dir = lineage_root / "00_idea_intake"

    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": lineage_id,
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
        {
            "market": "binance perp",
            "data_source": "binance um futures klines",
            "bar_size": "5m",
        },
    )

    intake_confirm_result = _run_qros_session(project_root, env, "--lineage-id", lineage_id, "--confirm-intake")
    assert intake_confirm_result.returncode == 0, intake_confirm_result.stderr
    assert "Current stage: mandate_confirmation_pending" in intake_confirm_result.stdout

    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n\n- BTC leads ALTs\n", encoding="utf-8")
    ensure_stage_program(lineage_root, "mandate")

    mandate_result = _run_qros_session(project_root, env, "--lineage-id", lineage_id, "--confirm-mandate")
    assert mandate_result.returncode == 0, mandate_result.stderr

    review_pending_result = _run_qros_session(project_root, env, "--lineage-id", lineage_id)
    assert review_pending_result.returncode == 0, review_pending_result.stderr
    assert "Current stage: mandate_review_confirmation_pending" in review_pending_result.stdout
    assert "Run with --confirm-review or reply CONFIRM_REVIEW" in review_pending_result.stdout

    confirm_review_result = _run_qros_session(project_root, env, "--lineage-id", lineage_id, "--confirm-review")
    assert confirm_review_result.returncode == 0, confirm_review_result.stderr

    review_result = _run_qros_session(project_root, env, "--lineage-id", lineage_id, "--json")
    assert review_result.returncode == 0, review_result.stderr
    payload = json.loads(review_result.stdout)
    assert payload["current_stage"] == "mandate_review"
    assert payload["current_skill"] == "qros-mandate-review"
    assert payload["gate_status"] == "ADVERSARIAL_REVIEW_PENDING"
    assert (
        payload["next_action"]
        == "Launch a spawned reviewer child, issue spawned_reviewer_receipt.yaml, then wait for adversarial_review_result.yaml."
    )
    assert (lineage_root / "01_mandate" / "review" / "request" / "adversarial_review_request.yaml").exists()
