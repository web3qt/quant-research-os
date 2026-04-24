from __future__ import annotations

from pathlib import Path
from subprocess import run
import sys

import yaml

from runtime.tools.idea_runtime import scaffold_idea_intake
from tests.helpers.repo_paths import REPO_ROOT
from tests.runtime.test_csf_data_ready_runtime import (
    _csf_data_ready_draft,
    _prepare_mandate_stage,
    _write_yaml as _write_csf_yaml,
)
from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate
from tests.runtime.test_artifact_contract_runtime import (
    _write_minimal_valid_csf_backtest_ready_formal,
    _write_minimal_valid_csf_signal_ready_formal,
    _write_minimal_valid_csf_test_evidence_formal,
    _write_minimal_valid_csf_train_freeze_formal,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_validate_stage_artifacts_script_accepts_valid_idea_intake(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_transmission_v1"
    scaffold_idea_intake(lineage_root)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "idea_intake",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "idea_intake artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_reports_invalid_shape(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    payload = yaml.safe_load((intake_dir / "scope_canvas.yaml").read_text(encoding="utf-8"))
    payload["holding_horizons"] = "15m"
    _write_yaml(intake_dir / "scope_canvas.yaml", payload)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "idea_intake",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "scope_canvas.yaml: holding_horizons expected list[string], found str" in result.stderr


def test_validate_stage_artifacts_script_accepts_valid_mandate(tmp_path: Path) -> None:
    from tests.helpers.lineage_program_support import ensure_stage_program
    from tests.session.test_idea_runtime_scripts import _mandate_freeze_draft, _route_assessment

    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "route_assessment": _route_assessment(),
            "approved_scope": {},
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
            "holding_horizons": ["15m"],
            "target_task": "event-driven relative return study",
            "excluded_scope": [],
            "budget_days": 10,
            "max_iterations": 3,
        },
    )
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n", encoding="utf-8")
    (intake_dir / "qualification_scorecard.yaml").write_text("idea_id: btc_alt_transmission_v1\n", encoding="utf-8")
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "mandate")

    build = run(
        [sys.executable, "runtime/scripts/build_mandate_from_intake.py", "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert build.returncode == 0, build.stderr

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "mandate",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "mandate artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_reports_invalid_mandate_shape(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "btc_alt_transmission_v1" / "01_mandate" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "mandate.md").write_text("# Mandate\n", encoding="utf-8")

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "mandate",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "research_scope.md: missing required artifact" in result.stderr


def test_validate_stage_artifacts_script_accepts_valid_csf_data_ready(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_case"
    _prepare_mandate_stage(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True)
    _write_csf_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _csf_data_ready_draft(confirmed=True))
    build_csf_data_ready_from_mandate(lineage_root)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_data_ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "csf_data_ready artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_reports_invalid_csf_data_ready_shape(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_case"
    _prepare_mandate_stage(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True)
    _write_csf_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _csf_data_ready_draft(confirmed=True))
    build_csf_data_ready_from_mandate(lineage_root)
    (stage_dir / "author" / "formal" / "shared_feature_base" / "returns_panel.parquet").unlink()

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_data_ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "shared_feature_base/returns_panel.parquet: missing required artifact" in result.stderr


def test_validate_stage_artifacts_script_accepts_valid_csf_signal_ready(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "csf_case" / "03_csf_signal_ready" / "author" / "formal"
    _write_minimal_valid_csf_signal_ready_formal(formal_dir)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_signal_ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "csf_signal_ready artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_rejects_invalid_csf_signal_ready(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "csf_case" / "03_csf_signal_ready" / "author" / "formal"
    _write_minimal_valid_csf_signal_ready_formal(formal_dir)
    (formal_dir / "factor_group_context.parquet").unlink()

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_signal_ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "factor_group_context.parquet: missing required artifact" in result.stderr


def test_validate_stage_artifacts_script_accepts_valid_csf_train_freeze(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "csf_case" / "04_csf_train_freeze" / "author" / "formal"
    _write_minimal_valid_csf_train_freeze_formal(formal_dir)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_train_freeze",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "csf_train_freeze artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_rejects_invalid_csf_train_freeze(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "csf_case" / "04_csf_train_freeze" / "author" / "formal"
    _write_minimal_valid_csf_train_freeze_formal(formal_dir)
    (formal_dir / "train_variant_ledger.csv").write_text(
        "variant_id,status\nbaseline_v1,kept\n",
        encoding="utf-8",
    )

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_train_freeze",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "train_variant_ledger.csv: missing required csv column selection_rule" in result.stderr


def test_validate_stage_artifacts_script_accepts_valid_csf_test_evidence(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "csf_case" / "05_csf_test_evidence" / "author" / "formal"
    _write_minimal_valid_csf_test_evidence_formal(formal_dir)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_test_evidence",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "csf_test_evidence artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_rejects_invalid_csf_test_evidence(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "csf_case" / "05_csf_test_evidence" / "author" / "formal"
    _write_minimal_valid_csf_test_evidence_formal(formal_dir)
    (formal_dir / "csf_test_gate_table.csv").write_text(
        "variant_id,verdict\nbaseline_v1,selected\n",
        encoding="utf-8",
    )

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_test_evidence",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "csf_test_gate_table.csv: missing required csv column primary_evidence_contract" in result.stderr


def test_validate_stage_artifacts_script_accepts_valid_csf_backtest_ready(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "csf_case" / "06_csf_backtest_ready" / "author" / "formal"
    _write_minimal_valid_csf_backtest_ready_formal(formal_dir)

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_backtest_ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "csf_backtest_ready artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_rejects_invalid_csf_backtest_ready(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "csf_case" / "06_csf_backtest_ready" / "author" / "formal"
    _write_minimal_valid_csf_backtest_ready_formal(formal_dir)
    (formal_dir / "csf_backtest_gate_decision.md").unlink()

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "csf_case",
            "--stage",
            "csf_backtest_ready",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "csf_backtest_gate_decision.md: missing required artifact" in result.stderr
