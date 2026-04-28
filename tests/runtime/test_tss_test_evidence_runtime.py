from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.tss_test_evidence_runtime import (
    build_tss_test_evidence_from_train_freeze,
    scaffold_tss_test_evidence,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_tss_train_freeze_stage(lineage_root: Path) -> None:
    formal_dir = lineage_root / "04_tss_train_freeze" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "tss_train_freeze.yaml").write_text("stage: tss_train_freeze\n", encoding="utf-8")
    (formal_dir / "train_threshold_ledger.csv").write_text(
        "variant_id,threshold,status\nbaseline_v1,0.0,kept\n",
        encoding="utf-8",
    )
    (formal_dir / "train_variant_ledger.csv").write_text(
        "variant_id,status\nbaseline_v1,kept\n",
        encoding="utf-8",
    )
    (formal_dir / "train_variant_rejects.csv").write_text("variant_id,reject_reason\n", encoding="utf-8")


def _tss_test_evidence_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "test_window_source": "time_split.json::test",
                    "train_reuse_note": "Reuse train-kept variants.",
                    "subperiod_rule": "Report equal subperiods.",
                },
                "missing_items": [],
            },
            "variant_contract": {
                "confirmed": confirmed,
                "draft": {
                    "selected_variant_ids": ["baseline_v1"],
                    "selection_rule": "Admit only train-kept variants.",
                    "multiple_testing_note": "No extra test search.",
                },
                "missing_items": [],
            },
            "evidence_contract": {
                "confirmed": confirmed,
                "draft": {
                    "primary_evidence_contract": "forward_return_uplift",
                    "base_rate_reference": "unconditional_forward_return",
                    "minimum_event_count_rule": "At least one event in fixture.",
                },
                "missing_items": [],
            },
            "audit_contract": {
                "confirmed": confirmed,
                "draft": {
                    "event_count_rule": "Do not accept results from too few events.",
                    "direction_flip_rule": "Escalate sign flips.",
                    "coverage_note": "Coverage failures block review.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["event_forward_return.parquet", "tss_test_gate_table.csv"],
                    "consumer_stage": "tss_backtest_ready",
                    "frozen_spec_note": "Backtest can only use selected test variants.",
                },
                "missing_items": [],
            },
        }
    }


def test_scaffold_tss_test_evidence_creates_draft_under_tss_stage_dir(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"

    stage_dir = scaffold_tss_test_evidence(lineage_root)

    assert stage_dir == lineage_root / "05_tss_test_evidence"
    draft_path = stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml"
    assert draft_path.exists()
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
    assert set(payload["groups"]) == {
        "window_contract",
        "variant_contract",
        "evidence_contract",
        "audit_contract",
        "delivery_contract",
    }


def test_build_tss_test_evidence_writes_planned_formal_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_train_freeze_stage(lineage_root)
    stage_dir = lineage_root / "05_tss_test_evidence"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml",
        _tss_test_evidence_draft(confirmed=True),
    )

    built_dir = build_tss_test_evidence_from_train_freeze(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "event_forward_return.parquet").exists()
    assert (formal_dir / "signal_performance_summary.json").exists()
    assert (formal_dir / "tss_test_gate_table.csv").exists()
    assert (formal_dir / "tss_selected_variants_test.csv").exists()
    assert pq.read_table(formal_dir / "event_forward_return.parquet").num_rows > 0
