import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_test_evidence_runtime import (
    build_csf_test_evidence_from_train_freeze,
    scaffold_csf_test_evidence,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _csf_test_evidence_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "test_window_source": "time_split.json::test",
                    "train_reuse_note": "Test reuses train preprocessing and bucket rules only.",
                    "subperiod_rule": "Report stability over equal subperiods.",
                },
                "missing_items": [],
            },
            "variant_contract": {
                "confirmed": confirmed,
                "draft": {
                    "selected_variant_ids": ["baseline_v1"],
                    "selection_rule": "Admit only train-kept variants.",
                    "multiple_testing_note": "No extra test-stage search is allowed.",
                },
                "missing_items": [],
            },
            "evidence_contract": {
                "confirmed": confirmed,
                "draft": {
                    "primary_evidence_contract": "rank_ic_and_bucket_spread",
                    "factor_role": "standalone_alpha",
                    "role_specific_note": "Standalone alpha must prove ranking stability in test.",
                },
                "missing_items": [],
            },
            "audit_contract": {
                "confirmed": confirmed,
                "draft": {
                    "breadth_rule": "Require enough active names per date before accepting test output.",
                    "flip_rule": "Escalate when factor direction flips in test.",
                    "coverage_note": "Coverage failures remain blocking, not audit-only.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["csf_test_gate_table.csv", "csf_selected_variants_test.csv"],
                    "consumer_stage": "csf_backtest_ready",
                    "frozen_spec_note": "Backtest may only consume test-admitted variants.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_csf_train_stage(lineage_root: Path) -> None:
    stage_dir = lineage_root / "04_csf_train_freeze"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "csf_train_freeze.yaml",
        "train_factor_quality.parquet",
        "train_variant_ledger.csv",
        "train_variant_rejects.csv",
        "train_bucket_diagnostics.parquet",
        "train_neutralization_diagnostics.parquet",
        "csf_train_contract.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    (formal_dir / "train_variant_ledger.csv").write_text(
        "variant_id,status,selection_rule\nbaseline_v1,kept,baseline-only\n",
        encoding="utf-8",
    )
    mandate_dir = lineage_root / "01_mandate"
    mandate_formal_dir = mandate_dir / "author" / "formal"
    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(mandate_formal_dir / "research_route.yaml", {"research_route": "cross_sectional_factor", "factor_role": "standalone_alpha"})


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _prepare_csf_rank_ic_inputs(lineage_root: Path) -> None:
    signal_formal_dir = lineage_root / "03_csf_signal_ready" / "author" / "formal"
    data_formal_dir = lineage_root / "02_csf_data_ready" / "author" / "formal"
    _write_parquet_rows(
        signal_formal_dir / "factor_panel.parquet",
        [
            {"date": "2024-07-01", "asset": "AAAUSDT", "score": 1.0},
            {"date": "2024-07-01", "asset": "BBBUSDT", "score": 2.0},
            {"date": "2024-07-01", "asset": "CCCUSDT", "score": 3.0},
        ],
    )
    _write_yaml(
        signal_formal_dir / "factor_manifest.yaml",
        {
            "stage": "csf_signal_ready",
            "lineage_id": lineage_root.name,
            "final_score_field": "score",
        },
    )
    _write_parquet_rows(
        data_formal_dir / "forward_return_panel.parquet",
        [
            {"date": "2024-07-01", "asset": "AAAUSDT", "forward_return": 0.01},
            {"date": "2024-07-01", "asset": "BBBUSDT", "forward_return": 0.02},
            {"date": "2024-07-01", "asset": "CCCUSDT", "forward_return": 0.03},
        ],
    )


def test_scaffold_csf_test_evidence_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_train_stage(lineage_root)

    stage_dir = scaffold_csf_test_evidence(lineage_root)

    draft = yaml.safe_load((stage_dir / "author" / "draft" / "csf_test_evidence_draft.yaml").read_text(encoding="utf-8"))
    assert stage_dir == lineage_root / "05_csf_test_evidence"
    assert set(draft["groups"]) == {
        "window_contract",
        "variant_contract",
        "evidence_contract",
        "audit_contract",
        "delivery_contract",
    }


def test_build_csf_test_evidence_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_train_stage(lineage_root)
    _prepare_csf_rank_ic_inputs(lineage_root)
    stage_dir = lineage_root / "05_csf_test_evidence"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_test_evidence_draft.yaml", _csf_test_evidence_draft(confirmed=True))

    built_dir = build_csf_test_evidence_from_train_freeze(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "rank_ic_timeseries.parquet").exists()
    assert (formal_dir / "rank_ic_summary.json").exists()
    assert (formal_dir / "bucket_returns.parquet").exists()
    assert (formal_dir / "monotonicity_report.json").exists()
    assert (formal_dir / "breadth_coverage_report.parquet").exists()
    assert (formal_dir / "subperiod_stability_report.json").exists()
    assert (formal_dir / "filter_condition_panel.parquet").exists()
    assert (formal_dir / "target_strategy_condition_compare.parquet").exists()
    assert (formal_dir / "gated_vs_ungated_summary.json").exists()
    assert (formal_dir / "csf_test_gate_table.csv").exists()
    assert (formal_dir / "csf_selected_variants_test.csv").exists()
    assert (formal_dir / "csf_test_contract.md").exists()
    assert (formal_dir / "csf_test_gate_decision.md").exists()
    assert (formal_dir / "run_manifest.json").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()

    rank_ic_summary = json.loads((formal_dir / "rank_ic_summary.json").read_text(encoding="utf-8"))
    assert rank_ic_summary["mean_rank_ic"] == 1.0
    assert rank_ic_summary["num_dates"] == 1
    assert pq.read_table(formal_dir / "rank_ic_timeseries.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "bucket_returns.parquet").num_rows > 0

    run_manifest = json.loads((formal_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["stage"] == "csf_test_evidence"
    assert "csf_test_gate_decision.md" in run_manifest["stage_outputs"]
    assert "run_manifest.json" in run_manifest["stage_outputs"]
    assert run_manifest["rank_ic_input_binding"]["execution_mode"] == "real_input"

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("csf_test_evidence"))
    assert result.valid is True
    assert result.errors == []
