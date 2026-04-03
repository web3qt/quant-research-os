from pathlib import Path

import pytest
import yaml

from tests.lineage_program_support import ensure_stage_program
from tools.lineage_program_runtime import StageProgramRuntimeError, inspect_stage_program, stage_outputs_complete, validate_stage_program


def test_missing_stage_program_reports_missing_contract(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "missing_case"
    inspection = inspect_stage_program(lineage_root, "data_ready", "time_series_signal")

    assert inspection.program_contract_status == "missing"
    assert inspection.error_code == "STAGE_PROGRAM_MISSING"
    assert inspection.required_program_dir == "program/time_series/data_ready"


def test_invalid_stage_program_rejects_shared_lib_escape(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "invalid_case"
    program_dir = ensure_stage_program(lineage_root, "data_ready")
    manifest_path = program_dir / "stage_program.yaml"
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    payload["shared_libs"] = ["program/time_series/shared.py"]
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    with pytest.raises(StageProgramRuntimeError) as excinfo:
        validate_stage_program(lineage_root, "data_ready", "time_series_signal")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"
    assert "program/common/" in str(excinfo.value)


def test_stage_outputs_complete_requires_provenance(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "case_x" / "02_data_ready"
    stage_dir.mkdir(parents=True)
    for name in ["aligned_bars", "qc_report.parquet", "dataset_manifest.json"]:
        target = stage_dir / name
        if "." in name:
            target.write_text("ok\n", encoding="utf-8")
        else:
            target.mkdir()

    assert stage_outputs_complete(stage_dir, ("aligned_bars", "qc_report.parquet", "dataset_manifest.json")) is False
