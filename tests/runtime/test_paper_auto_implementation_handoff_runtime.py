from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from runtime.tools.paper_auto_implementation_handoff_runtime import (
    validate_paper_auto_implementation_handoff,
)


ROOT = Path(__file__).resolve().parents[2]
VALID_SPEC = ROOT / "tests" / "fixtures" / "paper_to_spec" / "valid_paper_auto_implementation_handoff.yaml"
SCRIPT = ROOT / "runtime" / "scripts" / "validate_paper_auto_implementation_handoff.py"


def _load_valid_spec() -> dict:
    return yaml.safe_load(VALID_SPEC.read_text(encoding="utf-8"))


def _write_spec(tmp_path: Path, payload: dict) -> Path:
    spec_path = tmp_path / "paper_auto_implementation_handoff.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return spec_path


def test_valid_paper_auto_implementation_handoff_fixture_passes_contract_validation() -> None:
    result = validate_paper_auto_implementation_handoff(VALID_SPEC)

    assert result.valid
    assert result.findings == []


def test_validator_fails_when_required_top_level_field_missing(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload.pop("paper_spec_chain")
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_MISSING_FIELD",
        "missing top-level field: paper_spec_chain",
    ) in result.findings


def test_validator_blocks_implementation_when_spec_chain_not_valid(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["paper_spec_chain"]["paper_signal_spec"]["validation_status"] = "blocked"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_SPEC_CHAIN_NOT_VALID",
        "paper_spec_chain.paper_signal_spec.validation_status must be valid before implementation prompt",
    ) in result.findings


def test_validator_blocks_missing_upstream_spec_even_if_status_claims_valid(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["paper_spec_chain"]["paper_data_spec"]["path"] = "tests/fixtures/paper_to_spec/missing_data_spec.yaml"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_UPSTREAM_SPEC_MISSING",
        "paper_spec_chain.paper_data_spec.path does not exist: tests/fixtures/paper_to_spec/missing_data_spec.yaml",
    ) in result.findings


def test_validator_blocks_implementation_actions_without_acceptance(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_decision"]["decision"] = "pending"
    payload["allowed_next_action"] = "validate_researcher_data"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_IMPLEMENTATION_NOT_ACCEPTED",
        "implementation actions require implementation_decision.decision accepted",
    ) in result.findings


def test_validator_blocks_implementation_actions_when_data_readiness_has_gaps(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["data_readiness_brief"]["blocking_gaps"] = ["funding_rates missing"]
    payload["allowed_next_action"] = "validate_researcher_data"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_DATA_READINESS_BLOCKED",
        "implementation actions are blocked while data_readiness_brief.blocking_gaps is non-empty",
    ) in result.findings


def test_validator_blocks_implementation_actions_when_ambiguity_blocks(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["ambiguities"] = [
        {
            "field": "data_readiness_brief.required_datasets[0].time_range",
            "question": "What start date is required?",
            "blocking": True,
        }
    ]
    payload["allowed_next_action"] = "validate_researcher_data"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_BLOCKING_AMBIGUITY",
        "implementation actions are blocked while ambiguities contains blocking=true",
    ) in result.findings


def test_validator_allows_agent_acquisition_only_after_cannot_provide_and_approval(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["researcher_data_response"]["status"] = "cannot_provide"
    payload["researcher_data_response"]["provided_paths"] = {}
    payload["researcher_data_response"]["missing_datasets"] = ["price_bars", "funding_rates"]
    payload["agent_acquisition_plan"] = {
        "status": "approved",
        "sources": [
            {
                "dataset": "price_bars",
                "source": "exchange_public_api",
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "time_range": {"start": "2023-01-01T00:00:00Z", "end": "2025-12-31T23:00:00Z"},
                "fields": ["timestamp", "symbol", "open", "high", "low", "close", "volume"],
                "command": "active-repo fetch-bars --venue binance",
                "storage_target": "/active-repo/data/price_bars.parquet",
                "expected_artifacts": ["/active-repo/data/price_bars.parquet"],
                "approval_required": True,
            }
        ],
        "approval": {
            "approved": True,
            "approved_by": "researcher",
            "approved_at": "2026-06-02T00:00:00Z",
            "evidence": ["researcher approved acquisition plan"],
        },
        "limitations": [],
    }
    payload["allowed_next_action"] = "run_agent_data_acquisition"

    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert result.valid


def test_validator_blocks_agent_acquisition_when_researcher_data_not_declined(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["agent_acquisition_plan"]["status"] = "approved"
    payload["agent_acquisition_plan"]["approval"]["approved"] = True
    payload["agent_acquisition_plan"]["approval"]["evidence"] = ["approved"]
    payload["allowed_next_action"] = "run_agent_data_acquisition"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_RESEARCHER_DATA_NOT_DECLINED",
        "run_agent_data_acquisition requires researcher_data_response.status cannot_provide",
    ) in result.findings


def test_validator_blocks_agent_acquisition_without_approved_plan(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["researcher_data_response"]["status"] = "cannot_provide"
    payload["allowed_next_action"] = "run_agent_data_acquisition"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_ACQUISITION_NOT_APPROVED",
        "run_agent_data_acquisition requires approved agent_acquisition_plan",
    ) in result.findings


def test_validator_blocks_agent_acquisition_with_empty_sources(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["researcher_data_response"]["status"] = "cannot_provide"
    payload["researcher_data_response"]["provided_paths"] = {}
    payload["researcher_data_response"]["missing_datasets"] = ["price_bars"]
    payload["agent_acquisition_plan"]["status"] = "approved"
    payload["agent_acquisition_plan"]["approval"]["approved"] = True
    payload["agent_acquisition_plan"]["approval"]["evidence"] = ["approved"]
    payload["agent_acquisition_plan"]["sources"] = []
    payload["allowed_next_action"] = "run_agent_data_acquisition"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_ACQUISITION_PLAN_EMPTY",
        "run_agent_data_acquisition requires at least one acquisition source",
    ) in result.findings


def test_validator_blocks_scaffold_when_data_not_ready(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["researcher_data_response"]["status"] = "cannot_provide"
    payload["allowed_next_action"] = "generate_active_repo_backtest_scaffold"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_DATA_NOT_READY",
        "generate_active_repo_backtest_scaffold requires researcher-provided data or successful agent acquisition",
    ) in result.findings


def test_validator_blocks_scaffold_when_provided_paths_are_empty(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["researcher_data_response"]["provided_paths"] = {}
    payload["researcher_data_response"]["missing_datasets"] = ["price_bars"]
    payload["allowed_next_action"] = "generate_active_repo_backtest_scaffold"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_DATA_NOT_READY",
        "generate_active_repo_backtest_scaffold requires researcher-provided data or successful agent acquisition",
    ) in result.findings


def test_validator_blocks_qros_framework_repo_target(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["active_repo_boundary"]["target_root"] = payload["active_repo_boundary"]["forbidden_root"]
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
        "active_repo_boundary.target_root must not equal forbidden_root",
    ) in result.findings


def test_validator_blocks_qros_framework_repo_child_target(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["active_repo_boundary"]["target_root"] = (
        f"{payload['active_repo_boundary']['forbidden_root']}/outputs/paper_to_spec/example"
    )
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
        "active_repo_boundary.target_root must not be under forbidden_root",
    ) in result.findings


def test_validator_blocks_qros_framework_repo_storage_target(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["researcher_data_response"]["status"] = "cannot_provide"
    payload["researcher_data_response"]["provided_paths"] = {}
    payload["researcher_data_response"]["missing_datasets"] = ["price_bars"]
    payload["agent_acquisition_plan"] = {
        "status": "approved",
        "sources": [
            {
                "dataset": "price_bars",
                "source": "exchange_public_api",
                "symbols": ["BTCUSDT"],
                "time_range": {"start": "2023-01-01T00:00:00Z", "end": "2025-12-31T23:00:00Z"},
                "fields": ["timestamp", "symbol", "close"],
                "command": "fetch",
                "storage_target": f"{payload['active_repo_boundary']['forbidden_root']}/outputs/price_bars.parquet",
                "expected_artifacts": ["price_bars.parquet"],
                "approval_required": True,
            }
        ],
        "approval": {
            "approved": True,
            "approved_by": "researcher",
            "approved_at": "2026-06-02T00:00:00Z",
            "evidence": ["approved"],
        },
        "limitations": [],
    }
    payload["allowed_next_action"] = "run_agent_data_acquisition"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
        "agent_acquisition_plan.sources[0].storage_target must not be under forbidden_root",
    ) in result.findings


def test_validator_blocks_qros_framework_repo_implementation_output(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_handoff"]["implementation_outputs"] = [
        f"{payload['active_repo_boundary']['forbidden_root']}/outputs/paper_to_spec/example/program"
    ]
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
        "implementation_handoff.implementation_outputs[0] must not be under forbidden_root",
    ) in result.findings


def test_validator_fails_invalid_next_stage_recommendation(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_handoff"]["next_stage_recommendation"] = "mark_review_closed"
    result = validate_paper_auto_implementation_handoff(_write_spec(tmp_path, payload))

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_ENUM",
        "implementation_handoff.next_stage_recommendation must be one of "
        "['stop_after_specs', 'ask_researcher', 'validate_researcher_data', "
        "'run_agent_data_acquisition', 'generate_active_repo_backtest_scaffold']",
    ) in result.findings


def test_validate_paper_auto_implementation_handoff_script_reports_success() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(VALID_SPEC)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "paper_auto_implementation_handoff valid" in completed.stdout
    assert completed.stderr == ""


def test_validate_paper_auto_implementation_handoff_script_reports_errors(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["allowed_next_action"] = "run_agent_data_acquisition"
    spec_path = _write_spec(tmp_path, payload)

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(spec_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "PAPER_AUTO_IMPLEMENTATION_HANDOFF_RESEARCHER_DATA_NOT_DECLINED" in completed.stderr
    assert completed.stdout == ""
