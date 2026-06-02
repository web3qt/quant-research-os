from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from runtime.tools.paper_backtest_implementation_spec_runtime import (
    validate_paper_backtest_implementation_spec,
)


ROOT = Path(__file__).resolve().parents[2]
VALID_SPEC = ROOT / "tests" / "fixtures" / "paper_to_spec" / "valid_paper_backtest_implementation_spec.yaml"
SCRIPT = ROOT / "runtime" / "scripts" / "validate_paper_backtest_implementation_spec.py"


def _load_valid_spec() -> dict:
    return yaml.safe_load(VALID_SPEC.read_text(encoding="utf-8"))


def test_valid_paper_backtest_implementation_spec_fixture_passes_contract_validation() -> None:
    result = validate_paper_backtest_implementation_spec(VALID_SPEC)

    assert result.valid
    assert result.findings == []


def test_validator_fails_when_required_top_level_field_missing(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload.pop("backtest_spec_reference")
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_backtest_implementation_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_BACKTEST_IMPLEMENTATION_SPEC_MISSING_FIELD",
        "missing top-level field: backtest_spec_reference",
    ) in result.findings


def test_validator_fails_when_backtest_spec_reference_not_valid(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["backtest_spec_reference"]["validation_status"] = "blocked"
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_backtest_implementation_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_BACKTEST_IMPLEMENTATION_SPEC_BACKTEST_SPEC_NOT_VALID",
        "backtest_spec_reference.validation_status must be valid before backtest implementation spec",
    ) in result.findings


def test_validator_fails_strict_unknown_core_requirement(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_implementation_requirements"]["backtest_entrypoint"]["status"] = "unknown"
    payload["core_implementation_requirements"]["backtest_entrypoint"]["question_if_unknown"] = "Which command runs?"
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_backtest_implementation_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_BACKTEST_IMPLEMENTATION_SPEC_BLOCKING_UNKNOWN",
        "core_implementation_requirements.backtest_entrypoint: strict blocking field is unknown",
    ) in result.findings


def test_validator_fails_invalid_requirement_enum(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_implementation_requirements"]["target_stage_program"]["source"] = "model_guessed"
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_backtest_implementation_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_BACKTEST_IMPLEMENTATION_SPEC_INVALID_ENUM",
        "core_implementation_requirements.target_stage_program.source must be one of "
        "['backtest_spec_inherited', 'paper_stated', 'agent_inferred', 'researcher_required', "
        "'repo_policy_required']",
    ) in result.findings


def test_validator_fails_paper_stated_without_evidence(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_implementation_requirements"]["backtest_entrypoint"]["source"] = "paper_stated"
    payload["core_implementation_requirements"]["backtest_entrypoint"]["evidence"] = []
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_backtest_implementation_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_BACKTEST_IMPLEMENTATION_SPEC_EVIDENCE_REQUIRED",
        "core_implementation_requirements.backtest_entrypoint: paper_stated requires evidence",
    ) in result.findings


def test_validator_fails_invalid_next_stage_recommendation(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_handoff"]["next_stage_recommendation"] = "implement_backtest_directly"
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_backtest_implementation_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_BACKTEST_IMPLEMENTATION_SPEC_INVALID_ENUM",
        "implementation_handoff.next_stage_recommendation must be one of "
        "['generate_active_repo_backtest_scaffold', 'ask_researcher']",
    ) in result.findings


def test_validator_fails_when_boundary_targets_qros_framework_repo(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_implementation_requirements"]["active_research_repo_boundary"]["value"]["repo_role"] = "qros_framework_repo"
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_backtest_implementation_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_BACKTEST_IMPLEMENTATION_SPEC_FRAMEWORK_REPO_TARGET",
        "core_implementation_requirements.active_research_repo_boundary must target active research repo, not QROS framework repo",
    ) in result.findings


def test_validator_fails_when_no_retune_controls_allow_retune(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_implementation_requirements"]["no_retune_controls"]["value"]["allowed_actions"].append(
        "retune_parameters"
    )
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_backtest_implementation_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_BACKTEST_IMPLEMENTATION_SPEC_RETUNE_ALLOWED",
        "core_implementation_requirements.no_retune_controls must not allow retune, recalibrate, alter signal, or optimize parameters",
    ) in result.findings


def test_validate_paper_backtest_implementation_spec_script_reports_success() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(VALID_SPEC)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "paper_backtest_implementation_spec valid" in completed.stdout
    assert completed.stderr == ""


def test_validate_paper_backtest_implementation_spec_script_reports_errors(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_handoff"]["next_stage_recommendation"] = "implement_backtest_directly"
    spec_path = tmp_path / "paper_backtest_implementation_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(spec_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "PAPER_BACKTEST_IMPLEMENTATION_SPEC_INVALID_ENUM" in completed.stderr
    assert completed.stdout == ""
