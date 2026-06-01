from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from runtime.tools.paper_test_evidence_spec_runtime import validate_paper_test_evidence_spec


ROOT = Path(__file__).resolve().parents[2]
VALID_SPEC = ROOT / "tests" / "fixtures" / "paper_to_spec" / "valid_paper_test_evidence_spec.yaml"
SCRIPT = ROOT / "runtime" / "scripts" / "validate_paper_test_evidence_spec.py"


def _load_valid_spec() -> dict:
    return yaml.safe_load(VALID_SPEC.read_text(encoding="utf-8"))


def test_valid_paper_test_evidence_spec_fixture_passes_contract_validation() -> None:
    result = validate_paper_test_evidence_spec(VALID_SPEC)

    assert result.valid
    assert result.findings == []


def test_validator_fails_when_required_top_level_field_missing(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload.pop("train_freeze_spec_reference")
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_test_evidence_spec(spec_path)

    assert not result.valid
    assert ("PAPER_TEST_EVIDENCE_SPEC_MISSING_FIELD", "missing top-level field: train_freeze_spec_reference") in result.findings


def test_validator_fails_when_train_freeze_spec_reference_not_valid(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["train_freeze_spec_reference"]["validation_status"] = "blocked"
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_test_evidence_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TEST_EVIDENCE_SPEC_TRAIN_FREEZE_SPEC_NOT_VALID",
        "train_freeze_spec_reference.validation_status must be valid before test-evidence spec",
    ) in result.findings


def test_validator_fails_strict_unknown_core_requirement(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_test_evidence_requirements"]["no_retune_attestation"]["status"] = "unknown"
    payload["core_test_evidence_requirements"]["no_retune_attestation"]["question_if_unknown"] = "Can test results change parameters?"
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_test_evidence_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TEST_EVIDENCE_SPEC_BLOCKING_UNKNOWN",
        "core_test_evidence_requirements.no_retune_attestation: strict blocking field is unknown",
    ) in result.findings


def test_validator_fails_invalid_requirement_enum(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_test_evidence_requirements"]["signal_diagnostics"]["source"] = "model_guessed"
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_test_evidence_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TEST_EVIDENCE_SPEC_INVALID_ENUM",
        "core_test_evidence_requirements.signal_diagnostics.source must be one of "
        "['train_freeze_spec_inherited', 'paper_stated', 'agent_inferred', 'researcher_required']",
    ) in result.findings


def test_validator_fails_paper_stated_without_evidence(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_test_evidence_requirements"]["performance_diagnostics"]["source"] = "paper_stated"
    payload["core_test_evidence_requirements"]["performance_diagnostics"]["evidence"] = []
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_test_evidence_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TEST_EVIDENCE_SPEC_EVIDENCE_REQUIRED",
        "core_test_evidence_requirements.performance_diagnostics: paper_stated requires evidence",
    ) in result.findings


def test_validator_fails_invalid_next_stage_recommendation(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_handoff"]["next_stage_recommendation"] = "paper_holdout_spec"
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_test_evidence_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TEST_EVIDENCE_SPEC_INVALID_ENUM",
        "implementation_handoff.next_stage_recommendation must be one of "
        "['paper_backtest_spec', 'ask_researcher']",
    ) in result.findings


def test_validator_fails_when_no_retune_attestation_allows_parameter_change(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_test_evidence_requirements"]["no_retune_attestation"]["value"]["allows_parameter_change"] = True
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_test_evidence_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TEST_EVIDENCE_SPEC_RETUNE_ALLOWED",
        "core_test_evidence_requirements.no_retune_attestation.value.allows_parameter_change must be false",
    ) in result.findings


def test_validator_fails_when_test_result_usage_policy_allows_retune(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_test_evidence_requirements"]["test_result_usage_policy"]["value"]["allowed_actions"].append("retune_parameters")
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_test_evidence_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TEST_EVIDENCE_SPEC_RETUNE_ALLOWED",
        "core_test_evidence_requirements.test_result_usage_policy must not allow retune or parameter changes",
    ) in result.findings


def test_validate_paper_test_evidence_spec_script_reports_success() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(VALID_SPEC)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "paper_test_evidence_spec valid" in completed.stdout
    assert completed.stderr == ""


def test_validate_paper_test_evidence_spec_script_reports_errors(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_handoff"]["next_stage_recommendation"] = "paper_holdout_spec"
    spec_path = tmp_path / "paper_test_evidence_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(spec_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "PAPER_TEST_EVIDENCE_SPEC_INVALID_ENUM" in completed.stderr
    assert completed.stdout == ""
