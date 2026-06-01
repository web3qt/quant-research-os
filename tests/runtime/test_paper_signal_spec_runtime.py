from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from runtime.tools.paper_signal_spec_runtime import validate_paper_signal_spec


ROOT = Path(__file__).resolve().parents[2]
VALID_SPEC = ROOT / "tests" / "fixtures" / "paper_to_spec" / "valid_paper_signal_spec.yaml"
SCRIPT = ROOT / "runtime" / "scripts" / "validate_paper_signal_spec.py"


def _load_valid_spec() -> dict:
    return yaml.safe_load(VALID_SPEC.read_text(encoding="utf-8"))


def test_valid_paper_signal_spec_fixture_passes_contract_validation() -> None:
    result = validate_paper_signal_spec(VALID_SPEC)

    assert result.valid
    assert result.findings == []


def test_validator_fails_when_required_top_level_field_missing(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload.pop("data_spec_reference")
    spec_path = tmp_path / "paper_signal_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_signal_spec(spec_path)

    assert not result.valid
    assert ("PAPER_SIGNAL_SPEC_MISSING_FIELD", "missing top-level field: data_spec_reference") in result.findings


def test_validator_fails_when_data_spec_reference_not_valid(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["data_spec_reference"]["validation_status"] = "blocked"
    spec_path = tmp_path / "paper_signal_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_signal_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_SIGNAL_SPEC_DATA_SPEC_NOT_VALID",
        "data_spec_reference.validation_status must be valid before signal spec",
    ) in result.findings


def test_validator_fails_strict_unknown_core_requirement(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_signal_requirements"]["signal_definition"]["status"] = "unknown"
    payload["core_signal_requirements"]["signal_definition"]["question_if_unknown"] = "What is the exact signal formula?"
    spec_path = tmp_path / "paper_signal_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_signal_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_SIGNAL_SPEC_BLOCKING_UNKNOWN",
        "core_signal_requirements.signal_definition: strict blocking field is unknown",
    ) in result.findings


def test_validator_fails_unknown_train_test_policy_mode(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_signal_requirements"]["train_test_policy"]["value"]["mode"] = "unknown"
    spec_path = tmp_path / "paper_signal_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_signal_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_SIGNAL_SPEC_TRAIN_TEST_POLICY_UNKNOWN",
        "core_signal_requirements.train_test_policy.value.mode must not be unknown",
    ) in result.findings


def test_validator_fails_invalid_requirement_enum(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_signal_requirements"]["feature_inputs"]["source"] = "model_guessed"
    spec_path = tmp_path / "paper_signal_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_signal_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_SIGNAL_SPEC_INVALID_ENUM",
        "core_signal_requirements.feature_inputs.source must be one of "
        "['paper_stated', 'data_spec_inherited', 'agent_inferred', 'researcher_required']",
    ) in result.findings


def test_validator_fails_paper_stated_without_evidence(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_signal_requirements"]["feature_inputs"]["evidence"] = []
    spec_path = tmp_path / "paper_signal_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_signal_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_SIGNAL_SPEC_EVIDENCE_REQUIRED",
        "core_signal_requirements.feature_inputs: paper_stated requires evidence",
    ) in result.findings


def test_validator_fails_invalid_next_stage_recommendation(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_handoff"]["next_stage_recommendation"] = "paper_backtest_spec"
    spec_path = tmp_path / "paper_signal_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_signal_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_SIGNAL_SPEC_INVALID_ENUM",
        "implementation_handoff.next_stage_recommendation must be one of "
        "['paper_train_freeze_spec', 'paper_test_evidence_spec', 'ask_researcher']",
    ) in result.findings


def test_validate_paper_signal_spec_script_reports_success() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(VALID_SPEC)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "paper_signal_spec valid" in completed.stdout
    assert completed.stderr == ""


def test_validate_paper_signal_spec_script_reports_errors(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_signal_requirements"]["signal_family"]["value"]["family"] = "stat_arb"
    spec_path = tmp_path / "paper_signal_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(spec_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "PAPER_SIGNAL_SPEC_INVALID_ENUM" in completed.stderr
    assert completed.stdout == ""
