from __future__ import annotations

import json
from pathlib import Path
from subprocess import run
import sys
import tomllib

import yaml

from tests.helpers.lineage_program_support import ensure_stage_program
from tests.helpers.repo_paths import REPO_ROOT
from tests.session.test_idea_runtime_scripts import _mandate_freeze_draft, _route_assessment, _write_yaml


def _build_valid_mandate(tmp_path: Path) -> Path:
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
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n", encoding="utf-8")
    (intake_dir / "qualification_scorecard.yaml").write_text("idea_id: btc_alt_transmission_v1\n", encoding="utf-8")
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, "runtime/scripts/build_mandate_from_intake.py", "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return lineage_root / "01_mandate" / "author" / "formal"


def test_generated_mandate_file_tree_matches_artifact_contract(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract

    formal_dir = _build_valid_mandate(tmp_path)
    contract = load_artifact_contract("mandate")

    assert sorted(path.name for path in formal_dir.iterdir()) == sorted(
        [*contract["artifacts"], "program_execution_manifest.json"]
    )


def test_generated_mandate_machine_shapes_match_contract(tmp_path: Path) -> None:
    formal_dir = _build_valid_mandate(tmp_path)

    route = yaml.safe_load((formal_dir / "research_route.yaml").read_text(encoding="utf-8"))
    assert list(route) == [
        "research_route",
        "factor_role",
        "factor_structure",
        "portfolio_expression",
        "neutralization_policy",
        "target_strategy_reference",
        "group_taxonomy_reference",
        "excluded_routes",
        "route_rationale",
        "route_change_policy",
        "route_contract_version",
    ]

    time_split = json.loads((formal_dir / "time_split.json").read_text(encoding="utf-8"))
    assert list(time_split) == ["train", "test", "backtest", "holdout", "bar_size", "holding_horizons", "policy_note"]

    run_config = tomllib.loads((formal_dir / "run_config.toml").read_text(encoding="utf-8"))
    assert list(run_config) == [
        "stage",
        "lineage_id",
        "market",
        "universe",
        "target_task",
        "data_source",
        "bar_size",
        "non_rust_exceptions",
    ]
    assert run_config["non_rust_exceptions"] == []


def test_generated_mandate_passes_artifact_shape_validator(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    formal_dir = _build_valid_mandate(tmp_path)

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("mandate"))

    assert result.valid is True
    assert result.errors == []
