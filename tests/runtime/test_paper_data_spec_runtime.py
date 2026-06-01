from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from runtime.tools.paper_data_spec_runtime import validate_paper_data_spec


ROOT = Path(__file__).resolve().parents[2]
VALID_SPEC = ROOT / "tests" / "fixtures" / "paper_to_spec" / "valid_paper_data_spec.yaml"
SCRIPT = ROOT / "runtime" / "scripts" / "validate_paper_data_spec.py"


def _load_valid_spec() -> dict:
    return yaml.safe_load(VALID_SPEC.read_text(encoding="utf-8"))


def test_valid_paper_data_spec_fixture_passes_contract_validation() -> None:
    result = validate_paper_data_spec(VALID_SPEC)

    assert result.valid
    assert result.findings == []


def test_validator_fails_when_required_top_level_field_missing(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload.pop("reading_coverage")
    spec_path = tmp_path / "paper_data_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_data_spec(spec_path)

    assert not result.valid
    assert ("PAPER_DATA_SPEC_MISSING_FIELD", "missing top-level field: reading_coverage") in result.findings


def test_validator_fails_strict_unknown_core_requirement(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_data_requirements"]["funding"]["status"] = "unknown"
    payload["core_data_requirements"]["funding"]["question_if_unknown"] = "Should funding enter pnl?"
    spec_path = tmp_path / "paper_data_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_data_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_DATA_SPEC_BLOCKING_UNKNOWN",
        "core_data_requirements.funding: strict blocking field is unknown",
    ) in result.findings


def test_validator_fails_invalid_requirement_enum(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["core_data_requirements"]["price_bars"]["source"] = "model_guessed"
    spec_path = tmp_path / "paper_data_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_data_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_DATA_SPEC_INVALID_ENUM",
        "core_data_requirements.price_bars.source must be one of "
        "['paper_stated', 'agent_inferred', 'researcher_required', 'exchange_profile_default']",
    ) in result.findings


def test_validator_fails_low_reading_coverage(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["reading_coverage"]["coverage_level"] = "low"
    spec_path = tmp_path / "paper_data_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_data_spec(spec_path)

    assert not result.valid
    assert (
        "PAPER_DATA_SPEC_READING_COVERAGE_LOW",
        "reading_coverage.coverage_level low is blocking for paper_data_spec",
    ) in result.findings


def test_validate_paper_data_spec_script_reports_success() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(VALID_SPEC)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "paper_data_spec valid" in completed.stdout
    assert completed.stderr == ""


def test_validate_paper_data_spec_script_reports_errors(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["target_market"]["market_type"] = "equity"
    spec_path = tmp_path / "paper_data_spec.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(spec_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "PAPER_DATA_SPEC_INVALID_ENUM" in completed.stderr
    assert completed.stdout == ""
