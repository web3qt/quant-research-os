from pathlib import Path

import pyarrow.parquet as pq
import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from runtime.tools.tss_signal_ready_runtime import (
    build_tss_signal_ready_from_data_ready,
    scaffold_tss_signal_ready,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_tss_data_ready_stage(lineage_root: Path) -> None:
    formal_dir = lineage_root / "02_tss_data_ready" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "time_index_manifest.json",
        "asset_time_index.parquet",
        "quality_flags.parquet",
        "split_sample_adequacy_report.yaml",
        "run_manifest.json",
        "rebuild_tss_data_ready.py",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")


def _tss_signal_ready_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "signal_identity": {
                "confirmed": confirmed,
                "draft": {
                    "signal_id": "breakout_v1",
                    "signal_version": "v1",
                    "signal_direction": "high_better",
                    "target_asset": "BTCUSDT",
                },
                "missing_items": [],
            },
            "input_contract": {
                "confirmed": confirmed,
                "draft": {
                    "input_field_map": [
                        {
                            "field": "rolling_return_20",
                            "source_artifact": "feature_base/returns.parquet",
                            "source_column": "rolling_return_20",
                        }
                    ],
                    "input_roots": ["../02_tss_data_ready/author/formal/feature_base"],
                    "forbidden_input_roots": ["forward_label_base"],
                },
                "missing_items": [],
            },
            "signal_expression": {
                "confirmed": confirmed,
                "draft": {
                    "signal_field": "signal_value",
                    "expression": "rolling_return_20 > 0",
                    "asof_rule": "Signal value is computed at bar close.",
                },
                "missing_items": [],
            },
            "event_contract": {
                "confirmed": confirmed,
                "draft": {
                    "event_id_fields": ["asset", "timestamp", "param_id", "horizon"],
                    "horizons": ["1d"],
                    "event_trigger_rule": "signal_value > 0",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["signal_manifest.yaml", "signal_panel.parquet"],
                    "consumer_stage": "tss_train_freeze",
                    "frozen_inputs_note": "Train may tune thresholds but cannot change signal inputs.",
                },
                "missing_items": [],
            },
        }
    }


def test_scaffold_tss_signal_ready_creates_draft_under_tss_stage_dir(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"

    stage_dir = scaffold_tss_signal_ready(lineage_root)

    assert stage_dir == lineage_root / "03_tss_signal_ready"
    draft_path = stage_dir / "author" / "draft" / "tss_signal_ready_freeze_draft.yaml"
    assert draft_path.exists()
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
    assert set(payload["groups"]) == {
        "signal_identity",
        "input_contract",
        "signal_expression",
        "event_contract",
        "delivery_contract",
    }


def test_build_tss_signal_ready_writes_planned_formal_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_data_ready_stage(lineage_root)
    stage_dir = lineage_root / "03_tss_signal_ready"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_signal_ready_freeze_draft.yaml",
        _tss_signal_ready_draft(confirmed=True),
    )

    built_dir = build_tss_signal_ready_from_data_ready(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "signal_manifest.yaml").exists()
    assert (formal_dir / "param_manifest.csv").exists()
    assert (formal_dir / "signal_panel.parquet").exists()
    assert (formal_dir / "signal_event_panel.parquet").exists()
    assert (formal_dir / "route_inheritance_contract.yaml").exists()
    signal_manifest = yaml.safe_load((formal_dir / "signal_manifest.yaml").read_text(encoding="utf-8"))
    assert signal_manifest["stage"] == "tss_signal_ready"
    assert signal_manifest["research_route"] == "time_series_signal"
    assert "forward_label_base" not in str(signal_manifest["input_field_map"])
    assert pq.read_table(formal_dir / "signal_panel.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "signal_event_panel.parquet").num_rows > 0
