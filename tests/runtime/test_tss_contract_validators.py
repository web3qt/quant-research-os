import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from runtime.tools.tss_backtest_ready_contract_runtime import validate_tss_backtest_ready_semantics
from runtime.tools.tss_data_ready_contract_runtime import validate_tss_data_ready_semantics
from runtime.tools.tss_holdout_validation_contract_runtime import validate_tss_holdout_validation_semantics
from runtime.tools.tss_signal_ready_contract_runtime import validate_tss_signal_ready_semantics
from runtime.tools.tss_test_evidence_contract_runtime import validate_tss_test_evidence_semantics
from runtime.tools.tss_train_freeze_contract_runtime import validate_tss_train_freeze_semantics


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_parquet(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {key: [row.get(key) for row in rows] for key in rows[0]}
    pq.write_table(pa.table(columns), path)


def test_tss_data_ready_rejects_forward_label_timestamp_not_after_signal_timestamp(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = lineage_root / "02_tss_data_ready" / "author" / "formal"
    _write_parquet(
        formal_dir / "asset_time_index.parquet",
        [
            {
                "asset": "BTCUSDT",
                "timestamp": "2024-01-02T00:00:00Z",
                "forward_label_timestamp": "2024-01-01T00:00:00Z",
            }
        ],
    )

    result = validate_tss_data_ready_semantics(formal_dir, lineage_root)

    assert not result.valid
    assert any("forward_label_timestamp must be after timestamp" in item for item in result.errors)


def test_tss_signal_ready_rejects_forward_label_input_binding(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = lineage_root / "03_tss_signal_ready" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    _write_yaml(
        formal_dir / "signal_manifest.yaml",
        {
            "stage": "tss_signal_ready",
            "lineage_id": "tss_case",
            "research_route": "time_series_signal",
            "signal_id": "breakout",
            "input_field_map": [
                {"field": "return_5m_forward", "source_artifact": "forward_label_base/labels.parquet"},
            ],
            "source": "feature_base/technical.parquet",
        },
    )
    _write_json(
        formal_dir / "run_manifest.json",
        {"input_roots": ["../02_tss_data_ready/author/formal/forward_label_base"]},
    )

    result = validate_tss_signal_ready_semantics(formal_dir, lineage_root)

    assert not result.valid
    assert any("forward_label_base" in item for item in result.errors)
    assert any("未来标签不能用于信号构造" in item for item in result.errors)


def test_tss_signal_ready_accepts_feature_base_inputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = lineage_root / "03_tss_signal_ready" / "author" / "formal"
    _write_yaml(
        formal_dir / "signal_manifest.yaml",
        {
            "stage": "tss_signal_ready",
            "lineage_id": "tss_case",
            "research_route": "time_series_signal",
            "signal_id": "breakout",
            "input_field_map": [
                {"field": "rolling_return_20", "source_artifact": "feature_base/technical.parquet"},
            ],
            "input_roots": ["../02_tss_data_ready/author/formal/feature_base"],
        },
    )

    result = validate_tss_signal_ready_semantics(formal_dir, lineage_root)

    assert result.valid
    assert result.errors == []


def test_tss_train_freeze_rejects_kept_variant_outside_candidate_set(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = lineage_root / "04_tss_train_freeze" / "author" / "formal"
    _write_yaml(
        formal_dir / "tss_train_freeze.yaml",
        {
            "stage": "tss_train_freeze",
            "lineage_id": "tss_case",
            "research_route": "time_series_signal",
            "search_governance_contract": {
                "candidate_variant_ids": ["baseline_v1"],
                "kept_variant_ids": ["leaked_variant"],
                "rejected_variant_ids": [],
            },
        },
    )

    result = validate_tss_train_freeze_semantics(formal_dir, lineage_root)

    assert (
        "tss_train_freeze.yaml: kept_variant_ids must be a subset of candidate_variant_ids; outside=['leaked_variant']"
        in result.errors
    )


def test_tss_test_evidence_rejects_selected_variant_outside_train_kept_set(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    train_formal_dir = lineage_root / "04_tss_train_freeze" / "author" / "formal"
    train_formal_dir.mkdir(parents=True)
    (train_formal_dir / "train_variant_ledger.csv").write_text(
        "variant_id,status\nbaseline_v1,kept\n",
        encoding="utf-8",
    )
    formal_dir = lineage_root / "05_tss_test_evidence" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "tss_selected_variants_test.csv").write_text(
        "variant_id,status\nleaked_variant,selected\n",
        encoding="utf-8",
    )

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "tss_selected_variants_test.csv: selected variants must be a subset of train kept variants; outside=['leaked_variant']"
        in result.errors
    )


def test_tss_backtest_ready_requires_net_after_cost_rule(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = lineage_root / "06_tss_backtest_ready" / "author" / "formal"
    _write_yaml(
        formal_dir / "strategy_contract.yaml",
        {
            "stage": "tss_backtest_ready",
            "lineage_id": "tss_case",
            "research_route": "time_series_signal",
            "strategy_id": "baseline_strategy",
        },
    )

    result = validate_tss_backtest_ready_semantics(formal_dir, lineage_root)

    assert "strategy_contract.yaml: net_after_cost_rule must be present and non-empty" in result.errors


def test_tss_holdout_validation_rejects_tuning_performed(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = lineage_root / "07_tss_holdout_validation" / "author" / "formal"
    _write_json(
        formal_dir / "tss_holdout_run_manifest.json",
        {
            "stage": "tss_holdout_validation",
            "lineage_id": "tss_case",
            "research_route": "time_series_signal",
            "tuning_performed": True,
        },
    )

    result = validate_tss_holdout_validation_semantics(formal_dir, lineage_root)

    assert "tss_holdout_run_manifest.json: must not declare tuning_performed: true" in result.errors
