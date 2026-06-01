from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from runtime.tools.paper_train_freeze_spec_runtime import validate_paper_train_freeze_spec


ROOT = Path(__file__).resolve().parents[2]
VALID_SPEC = ROOT / "tests" / "fixtures" / "paper_to_spec" / "valid_paper_train_freeze_spec.yaml"
SCRIPT = ROOT / "runtime" / "scripts" / "validate_paper_train_freeze_spec.py"


def _load_valid_spec() -> dict:
    return yaml.safe_load(VALID_SPEC.read_text(encoding="utf-8"))


def test_valid_paper_train_freeze_spec_fixture_passes_contract_validation() -> None:
    result = validate_paper_train_freeze_spec(VALID_SPEC)

    assert result.valid
    assert result.findings == []


def test_validator_fails_when_required_top_level_field_missing(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload.pop("signal_spec_reference")
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_train_freeze_spec(spec_path)

    assert not result.valid
    assert ("PAPER_TRAIN_FREEZE_SPEC_MISSING_FIELD", "missing top-level field: signal_spec_reference") in result.findings


def test_validator_fails_when_signal_spec_reference_not_valid(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["signal_spec_reference"]["validation_status"] = "blocked"
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_train_freeze_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TRAIN_FREEZE_SPEC_SIGNAL_SPEC_NOT_VALID",
        "signal_spec_reference.validation_status must be valid before train-freeze spec",
    ) in result.findings


def test_validator_fails_when_inherited_policy_mismatches_train_test_mode(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["signal_spec_reference"]["inherited_train_test_policy"] = "required_parameter_fit"
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_train_freeze_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TRAIN_FREEZE_SPEC_POLICY_MISMATCH",
        "signal_spec_reference.inherited_train_test_policy must match core_train_freeze_requirements.train_test_mode.value.mode",
    ) in result.findings


def test_validator_fails_strict_unknown_core_requirement(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_train_freeze_requirements"]["split_policy"]["status"] = "unknown"
    payload["core_train_freeze_requirements"]["split_policy"]["question_if_unknown"] = "How should train/test be split?"
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_train_freeze_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TRAIN_FREEZE_SPEC_BLOCKING_UNKNOWN",
        "core_train_freeze_requirements.split_policy: strict blocking field is unknown",
    ) in result.findings


def test_validator_fails_unknown_train_test_mode(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_train_freeze_requirements"]["train_test_mode"]["value"]["mode"] = "unknown"
    payload["signal_spec_reference"]["inherited_train_test_policy"] = "unknown"
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_train_freeze_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TRAIN_FREEZE_SPEC_TRAIN_TEST_MODE_UNKNOWN",
        "core_train_freeze_requirements.train_test_mode.value.mode must not be unknown",
    ) in result.findings


def test_validator_fails_invalid_requirement_enum(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_train_freeze_requirements"]["parameter_freeze"]["source"] = "model_guessed"
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_train_freeze_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TRAIN_FREEZE_SPEC_INVALID_ENUM",
        "core_train_freeze_requirements.parameter_freeze.source must be one of "
        "['signal_spec_inherited', 'paper_stated', 'agent_inferred', 'researcher_required']",
    ) in result.findings


def test_validator_fails_paper_stated_without_evidence(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_train_freeze_requirements"]["parameter_freeze"]["source"] = "paper_stated"
    payload["core_train_freeze_requirements"]["parameter_freeze"]["evidence"] = []
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_train_freeze_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TRAIN_FREEZE_SPEC_EVIDENCE_REQUIRED",
        "core_train_freeze_requirements.parameter_freeze: paper_stated requires evidence",
    ) in result.findings


def test_validator_fails_invalid_next_stage_recommendation(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_handoff"]["next_stage_recommendation"] = "paper_backtest_spec"
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_train_freeze_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_TRAIN_FREEZE_SPEC_INVALID_ENUM",
        "implementation_handoff.next_stage_recommendation must be one of "
        "['paper_test_evidence_spec', 'ask_researcher']",
    ) in result.findings


def test_validate_paper_train_freeze_spec_script_reports_success() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(VALID_SPEC)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "paper_train_freeze_spec valid" in completed.stdout
    assert completed.stderr == ""


def test_validate_paper_train_freeze_spec_script_reports_errors(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_train_freeze_requirements"]["train_test_mode"]["value"]["mode"] = "walk_forward_magic"
    spec_path = tmp_path / "paper_train_freeze_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(spec_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "PAPER_TRAIN_FREEZE_SPEC_INVALID_ENUM" in completed.stderr
    assert completed.stdout == ""
