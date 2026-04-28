from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from runtime.scripts.run_signal_diagnostics import _render_text
from runtime.tools.signal_diagnostics import SignalDiagnosticsError, diagnostics_payload, latest_lineage_id


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)


def _formal_dir(outputs_root: Path, lineage_id: str, stage_dir: str) -> Path:
    return outputs_root / lineage_id / stage_dir / "author" / "formal"


def _observed_metric(payload: dict[str, Any], metric_id: str) -> dict[str, Any]:
    for dimension in payload["dimensions"]:
        for metric in dimension["observed_metrics"]:
            if metric["metric_id"] == metric_id:
                return metric
    raise AssertionError(f"missing observed metric: {metric_id}")


def _missing_metric_ids(payload: dict[str, Any]) -> set[str]:
    missing: set[str] = set()
    for dimension in payload["dimensions"]:
        missing.update(metric["metric_id"] for metric in dimension["missing_metrics"])
    return missing


def test_missing_outputs_root_raises_without_creating_directory(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    with pytest.raises(SignalDiagnosticsError, match="No QROS outputs directory"):
        latest_lineage_id(outputs_root)

    assert not outputs_root.exists()


def test_latest_lineage_id_selects_recently_modified_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    old_lineage = outputs_root / "old_lineage"
    new_lineage = outputs_root / "new_lineage"
    old_lineage.mkdir(parents=True)
    new_lineage.mkdir(parents=True)
    (old_lineage / "marker.txt").write_text("old", encoding="utf-8")
    (new_lineage / "marker.txt").write_text("new", encoding="utf-8")

    assert latest_lineage_id(outputs_root) == "new_lineage"


def test_explicit_lineage_id_and_tss_stage_are_honored(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "chosen", "05_tss_test_evidence")
    _write_json(
        formal_dir / "signal_performance_summary.json",
        {
            "stage": "tss_test_evidence",
            "research_route": "time_series_signal",
            "mean_forward_return": 0.012,
            "hit_rate": 0.56,
            "event_count": 80,
        },
    )

    payload = diagnostics_payload(outputs_root=outputs_root, lineage_id="chosen", stage="tss_test_evidence")

    assert payload["lineage_id"] == "chosen"
    assert payload["selection_mode"] == "explicit"
    assert payload["stage"] == "tss_test_evidence"
    assert payload["route"] == "time_series_signal"
    assert payload["is_review_verdict"] is False
    assert payload["formal_verdict_boundary"] == "diagnostics_only_not_review"


def test_tss_test_evidence_reads_summary_and_explains_metrics_in_chinese(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "lineage", "05_tss_test_evidence")
    _write_json(
        formal_dir / "signal_performance_summary.json",
        {
            "stage": "tss_test_evidence",
            "research_route": "time_series_signal",
            "mean_forward_return": 0.018,
            "hit_rate": 0.56,
            "base_rate": 0.51,
            "base_rate_uplift": 0.05,
            "event_count": 120,
            "signal_frequency": 0.08,
        },
    )

    payload = diagnostics_payload(outputs_root=outputs_root, lineage_id="lineage", stage="tss_test_evidence")

    assert payload["health"] == "WATCH"
    assert payload["summary"]
    assert _observed_metric(payload, "mean_forward_return")["value"] == pytest.approx(0.018)
    assert _observed_metric(payload, "hit_rate")["value"] == pytest.approx(0.56)
    assert _observed_metric(payload, "base_rate_uplift")["value"] == pytest.approx(0.05)
    assert _observed_metric(payload, "signal_frequency")["value"] == pytest.approx(0.08)
    assert "命中率" in _observed_metric(payload, "hit_rate")["interpretation"]
    assert "forward return" in _observed_metric(payload, "mean_forward_return")["interpretation"]
    assert "高信号做多" in _observed_metric(payload, "mean_forward_return")["strategy_link"]
    assert "mfe_mae" in _missing_metric_ids(payload)


def test_tss_negative_rank_ic_interpretation_links_to_strategy_direction(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "lineage", "05_tss_test_evidence")
    _write_json(
        formal_dir / "signal_performance_summary.json",
        {
            "stage": "tss_test_evidence",
            "research_route": "time_series_signal",
            "mean_rank_ic": -0.027,
            "mean_forward_return": -0.011,
            "hit_rate": 0.44,
            "event_count": 90,
        },
    )

    payload = diagnostics_payload(outputs_root=outputs_root, lineage_id="lineage", stage="tss_test_evidence")
    rank_ic = _observed_metric(payload, "mean_rank_ic")

    assert rank_ic["severity"] == "watch"
    assert "信号方向可能反了" in rank_ic["interpretation"]
    assert "当前窗口预测关系为负" in rank_ic["interpretation"]
    assert "高信号做多" in rank_ic["strategy_link"]
    assert "系统性站错方向" in rank_ic["strategy_link"]


def test_tss_holdout_validation_reads_compare_metrics(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "lineage", "07_tss_holdout_validation")
    _write_parquet(
        formal_dir / "holdout_event_compare.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "test_mean_forward_return": 0.012,
                "holdout_mean_forward_return": 0.007,
                "direction_match": True,
                "holdout_hit_rate": 0.54,
            }
        ],
    )
    _write_parquet(
        formal_dir / "holdout_backtest_compare.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "backtest_mean_net_return": 0.01,
                "holdout_mean_net_return": 0.006,
                "net_return_delta": -0.004,
                "backtest_max_drawdown": -0.08,
                "holdout_max_drawdown": -0.11,
            }
        ],
    )

    payload = diagnostics_payload(outputs_root=outputs_root, lineage_id="lineage", stage="tss_holdout_validation")

    assert _observed_metric(payload, "direction_match")["value"] is True
    assert _observed_metric(payload, "holdout_mean_forward_return")["value"] == pytest.approx(0.007)
    assert _observed_metric(payload, "holdout_hit_rate")["value"] == pytest.approx(0.54)
    assert _observed_metric(payload, "net_return_delta")["value"] == pytest.approx(-0.004)
    assert _observed_metric(payload, "drawdown_delta")["value"] == pytest.approx(-0.03)


def test_text_renderer_is_not_a_review_verdict_and_prioritizes_interpretation(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "lineage", "05_tss_test_evidence")
    _write_json(
        formal_dir / "signal_performance_summary.json",
        {
            "stage": "tss_test_evidence",
            "research_route": "time_series_signal",
            "mean_rank_ic": -0.027,
            "mean_forward_return": -0.011,
            "hit_rate": 0.44,
            "event_count": 90,
        },
    )

    text = _render_text(diagnostics_payload(outputs_root=outputs_root, lineage_id="lineage", stage="tss_test_evidence"))

    assert "先说结论" in text
    assert "怎么理解这些数" in text
    assert "跟当前策略的关系" in text
    assert "信号方向可能反了" in text
    assert "这不是 review verdict，也不是 gate verdict" in text
    assert "正式 PASS" not in text
    assert "正式 FAIL" not in text
