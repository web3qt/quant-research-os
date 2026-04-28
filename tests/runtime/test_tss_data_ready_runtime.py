import json
from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.tss_data_ready_runtime import (
    build_tss_data_ready_from_mandate,
    scaffold_tss_data_ready,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_tss_mandate_stage(lineage_root: Path) -> None:
    formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    (formal_dir / "time_split.json").write_text(
        json.dumps(
            {
                "train": "2024-01-01/2024-01-01",
                "test": "2024-01-02/2024-01-02",
                "backtest": "2024-01-03/2024-01-03",
                "holdout": "2024-01-04/2024-01-04",
                "bar_size": "1d",
                "holding_horizons": ["1d"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_yaml(
        formal_dir / "research_route.yaml",
        {"research_route": "time_series_signal", "target_asset": "BTCUSDT"},
    )


def _tss_data_ready_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "time_index_contract": {
                "confirmed": confirmed,
                "draft": {
                    "asset_key": "asset",
                    "timestamp_key": "timestamp",
                    "bar_size": "1d",
                    "timestamp_semantics": "Bars are timestamped at close and usable after close.",
                },
                "missing_items": [],
            },
            "quality_semantics": {
                "confirmed": confirmed,
                "draft": {
                    "missing_policy": "drop missing bars",
                    "stale_policy": "flag stale bars",
                    "bad_price_policy": "flag non-positive prices",
                    "outlier_policy": "winsorize diagnostic only",
                    "low_liquidity_policy": "flag low volume bars",
                },
                "missing_items": [],
            },
            "label_contract": {
                "confirmed": confirmed,
                "draft": {
                    "horizons": ["1d"],
                    "forward_return_fields": ["return_1d_forward"],
                    "label_availability_rule": "Labels are available only after the horizon closes.",
                    "no_lookahead_guardrail": "forward_label_base is never an input to signal construction.",
                },
                "missing_items": [],
            },
            "feature_base": {
                "confirmed": confirmed,
                "draft": {
                    "feature_outputs": ["returns", "volatility"],
                    "forbidden_label_inputs": ["forward_label_base"],
                    "feature_asof_rule": "Features use information available at timestamp close only.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "time_index_manifest.json",
                        "asset_time_index.parquet",
                        "quality_flags.parquet",
                    ],
                    "consumer_stage": "tss_signal_ready",
                    "frozen_inputs_note": "Signal stage consumes feature_base, not forward_label_base.",
                },
                "missing_items": [],
            },
        }
    }


def test_scaffold_tss_data_ready_creates_draft_under_tss_stage_dir(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"

    stage_dir = scaffold_tss_data_ready(lineage_root)

    assert stage_dir == lineage_root / "02_tss_data_ready"
    draft_path = stage_dir / "author" / "draft" / "tss_data_ready_freeze_draft.yaml"
    assert draft_path.exists()
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
    assert set(payload["groups"]) == {
        "time_index_contract",
        "quality_semantics",
        "label_contract",
        "feature_base",
        "delivery_contract",
    }


def test_build_tss_data_ready_writes_planned_formal_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_mandate_stage(lineage_root)
    stage_dir = lineage_root / "02_tss_data_ready"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_data_ready_freeze_draft.yaml",
        _tss_data_ready_draft(confirmed=True),
    )

    built_dir = build_tss_data_ready_from_mandate(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "time_index_manifest.json").exists()
    assert (formal_dir / "asset_time_index.parquet").exists()
    assert (formal_dir / "quality_flags.parquet").exists()
    assert (formal_dir / "split_sample_adequacy_report.yaml").exists()
    assert (formal_dir / "run_manifest.json").exists()
    assert (formal_dir / "rebuild_tss_data_ready.py").exists()
    assert pq.read_table(formal_dir / "asset_time_index.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "quality_flags.parquet").num_rows > 0
    manifest = json.loads((formal_dir / "time_index_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "tss_data_ready"
    assert manifest["research_route"] == "time_series_signal"
