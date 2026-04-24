import json
from pathlib import Path

import pyarrow.parquet as pq

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_holdout_runtime import (
    build_csf_holdout_validation_from_backtest,
    scaffold_csf_holdout_validation,
)
from tests.runtime.test_csf_backtest_runtime import (
    _csf_backtest_ready_draft,
    _prepare_csf_test_stage,
    _write_yaml as _write_backtest_yaml,
)
from runtime.tools.csf_backtest_runtime import build_csf_backtest_ready_from_test_evidence


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _csf_holdout_validation_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "holdout_window_source": "time_split.json::holdout",
                    "reuse_rule": "Holdout reuses the frozen backtest and test contracts only.",
                    "drift_scope": "Compare holdout cross-sections against prior test windows.",
                },
                "missing_items": [],
            },
            "reuse_contract": {
                "confirmed": confirmed,
                "draft": {
                    "backtest_contract_source": "06_csf_backtest_ready/portfolio_contract.yaml",
                    "test_contract_source": "05_csf_test_evidence/csf_test_gate_table.csv",
                    "variant_reuse_rule": "Do not change selected variants in holdout.",
                    "no_reestimate_rule": "No parameter re-estimation in holdout.",
                },
                "missing_items": [],
            },
            "stability_contract": {
                "confirmed": confirmed,
                "draft": {
                    "direction_flip_rule": "Escalate unexplained direction flips.",
                    "coverage_rule": "Coverage collapse is a blocking failure.",
                    "regime_shift_rule": "Audit regime shifts explicitly before concluding.",
                },
                "missing_items": [],
            },
            "failure_governance": {
                "confirmed": confirmed,
                "draft": {
                    "retryable_conditions": ["artifact defect", "repro defect"],
                    "child_lineage_trigger": "Open child lineage if a new mechanism is required.",
                    "rollback_boundary": "Only holdout rerun/reporting changes are allowed in place.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["csf_holdout_run_manifest.json", "holdout_test_compare.parquet"],
                    "consumer_stage": "terminal",
                    "field_doc_rule": "Every machine artifact needs field documentation.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_csf_backtest_stage(lineage_root: Path) -> None:
    _prepare_csf_test_stage(lineage_root)
    mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    payload = json.loads('{"holdout":"2024-10-01/2024-12-31"}')
    (mandate_formal_dir / "time_split.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    stage_dir = lineage_root / "06_csf_backtest_ready"
    stage_dir.mkdir(parents=True, exist_ok=True)
    _write_backtest_yaml(
        stage_dir / "author" / "draft" / "csf_backtest_ready_draft.yaml",
        _csf_backtest_ready_draft(confirmed=True),
    )
    build_csf_backtest_ready_from_test_evidence(lineage_root)


def test_scaffold_csf_holdout_validation_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_backtest_stage(lineage_root)

    stage_dir = scaffold_csf_holdout_validation(lineage_root)

    draft = yaml.safe_load((stage_dir / "author" / "draft" / "csf_holdout_validation_draft.yaml").read_text(encoding="utf-8"))
    assert stage_dir == lineage_root / "07_csf_holdout_validation"
    assert set(draft["groups"]) == {
        "window_contract",
        "reuse_contract",
        "stability_contract",
        "failure_governance",
        "delivery_contract",
    }


def test_build_csf_holdout_validation_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_backtest_stage(lineage_root)
    stage_dir = lineage_root / "07_csf_holdout_validation"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_holdout_validation_draft.yaml", _csf_holdout_validation_draft(confirmed=True))

    built_dir = build_csf_holdout_validation_from_backtest(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "csf_holdout_run_manifest.json").exists()
    assert (formal_dir / "holdout_factor_diagnostics.parquet").exists()
    assert (formal_dir / "holdout_test_compare.parquet").exists()
    assert (formal_dir / "holdout_portfolio_compare.parquet").exists()
    assert (formal_dir / "rolling_holdout_stability.json").exists()
    assert (formal_dir / "regime_shift_audit.json").exists()
    assert (formal_dir / "csf_holdout_gate_decision.md").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()

    assert pq.read_table(formal_dir / "holdout_factor_diagnostics.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "holdout_test_compare.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "holdout_portfolio_compare.parquet").num_rows > 0

    run_manifest = json.loads((formal_dir / "csf_holdout_run_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["stage"] == "csf_holdout_validation"
    assert run_manifest["source_stage"] == "csf_backtest_ready"
    assert "holdout_portfolio_compare.parquet" in run_manifest["stage_outputs"]

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("csf_holdout_validation"))
    assert result.valid is True
    assert result.errors == []
