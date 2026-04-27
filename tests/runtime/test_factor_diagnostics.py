from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml

from runtime.tools.factor_diagnostics import FactorDiagnosticsError, diagnostics_payload, latest_lineage_id


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_csv(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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

    with pytest.raises(FactorDiagnosticsError, match="No QROS outputs directory"):
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


def test_explicit_lineage_id_is_honored(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "chosen", "05_csf_test_evidence")
    _write_json(
        formal_dir / "rank_ic_summary.json",
        {
            "stage": "csf_test_evidence",
            "factor_role": "standalone_alpha",
            "selected_variant_ids": ["baseline_v1"],
            "primary_evidence_contract": "rank_ic_and_bucket_spread",
            "mean_rank_ic": 0.04,
            "median_rank_ic": 0.03,
            "num_dates": 3,
        },
    )
    _write_parquet(
        formal_dir / "rank_ic_timeseries.parquet",
        [
            {"date": "2024-01-01", "variant_id": "baseline_v1", "rank_ic": 0.03},
            {"date": "2024-01-02", "variant_id": "baseline_v1", "rank_ic": -0.01},
            {"date": "2024-01-03", "variant_id": "baseline_v1", "rank_ic": 0.06},
        ],
    )

    payload = diagnostics_payload(outputs_root=outputs_root, lineage_id="chosen", stage="csf_test_evidence")

    assert payload["lineage_id"] == "chosen"
    assert payload["selection_mode"] == "explicit"
    assert payload["stage"] == "csf_test_evidence"


def test_unsupported_stage_is_rejected(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    (outputs_root / "lineage").mkdir(parents=True)

    with pytest.raises(FactorDiagnosticsError, match="Unsupported diagnostics stage"):
        diagnostics_payload(outputs_root=outputs_root, lineage_id="lineage", stage="mandate")


def test_csf_test_evidence_reads_rank_ic_and_reports_missing_spread(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "lineage", "05_csf_test_evidence")
    _write_json(
        formal_dir / "rank_ic_summary.json",
        {
            "stage": "csf_test_evidence",
            "factor_role": "standalone_alpha",
            "selected_variant_ids": ["baseline_v1"],
            "primary_evidence_contract": "rank_ic_and_bucket_spread",
            "mean_rank_ic": 0.034,
            "median_rank_ic": 0.02,
            "num_dates": 3,
        },
    )
    _write_parquet(
        formal_dir / "rank_ic_timeseries.parquet",
        [
            {"date": "2024-01-01", "variant_id": "baseline_v1", "rank_ic": 0.03},
            {"date": "2024-01-02", "variant_id": "baseline_v1", "rank_ic": -0.01},
            {"date": "2024-01-03", "variant_id": "baseline_v1", "rank_ic": 0.06},
        ],
    )
    _write_json(
        formal_dir / "monotonicity_report.json",
        {"stage": "csf_test_evidence", "selected_variant_ids": ["baseline_v1"], "status": "review"},
    )
    _write_parquet(
        formal_dir / "breadth_coverage_report.parquet",
        [{"date": "2024-01-01", "variant_id": "baseline_v1", "coverage_ratio": 0.9, "asset_count": 80}],
    )
    _write_json(
        formal_dir / "subperiod_stability_report.json",
        {"stage": "csf_test_evidence", "selected_variant_ids": ["baseline_v1"], "status": "pass"},
    )

    payload = diagnostics_payload(outputs_root=outputs_root, lineage_id="lineage", stage="csf_test_evidence")

    assert payload["health"] == "WATCH"
    assert _observed_metric(payload, "rank_ic")["value"] == pytest.approx(0.034)
    assert _observed_metric(payload, "rank_ic_win_rate")["value"] == pytest.approx(2 / 3)
    assert _observed_metric(payload, "icir")["status"] == "observed"
    assert "top_bottom_spread" in _missing_metric_ids(payload)


def test_csf_backtest_ready_reads_existing_portfolio_metrics(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "lineage", "06_csf_backtest_ready")
    _write_parquet(
        formal_dir / "portfolio_summary.parquet",
        [{"variant_id": "baseline_v1", "mean_gross_return": 0.018, "mean_net_return": 0.012, "max_drawdown": -0.08}],
    )
    _write_parquet(
        formal_dir / "turnover_capacity_report.parquet",
        [{"date": "2024-01-01", "variant_id": "baseline_v1", "turnover": 0.14, "capacity_utilization": 0.25}],
    )

    payload = diagnostics_payload(outputs_root=outputs_root, lineage_id="lineage", stage="csf_backtest_ready")

    assert _observed_metric(payload, "mean_gross_return")["value"] == pytest.approx(0.018)
    assert _observed_metric(payload, "mean_net_return")["value"] == pytest.approx(0.012)
    assert _observed_metric(payload, "gross_net_erosion")["value"] == pytest.approx(0.006)
    assert _observed_metric(payload, "max_drawdown")["value"] == pytest.approx(-0.08)
    assert _observed_metric(payload, "turnover")["value"] == pytest.approx(0.14)
    assert _observed_metric(payload, "capacity_utilization")["value"] == pytest.approx(0.25)
    assert {"sharpe", "profit_factor"} <= _missing_metric_ids(payload)


def test_csf_holdout_validation_reads_compare_metrics(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = _formal_dir(outputs_root, "lineage", "07_csf_holdout_validation")
    _write_parquet(
        formal_dir / "holdout_test_compare.parquet",
        [{"variant_id": "baseline_v1", "backtest_mean_net_return": 0.012, "holdout_mean_net_return": 0.01, "direction_match": True}],
    )
    _write_parquet(
        formal_dir / "holdout_portfolio_compare.parquet",
        [{"variant_id": "baseline_v1", "backtest_max_drawdown": -0.08, "holdout_max_drawdown": -0.10, "holdout_mean_net_return": 0.01, "net_return_delta": -0.002}],
    )
    _write_parquet(
        formal_dir / "holdout_factor_diagnostics.parquet",
        [{"date": "2024-01-01", "variant_id": "baseline_v1", "coverage_ratio": 0.91, "breadth": 65, "direction_match": True, "bucket_stability_score": 0.7}],
    )
    _write_json(
        formal_dir / "rolling_holdout_stability.json",
        {"stage": "csf_holdout_validation", "selected_variant_ids": ["baseline_v1"], "direction_match": True, "stability_status": "pass", "rolling_window_count": 4},
    )
    _write_json(
        formal_dir / "regime_shift_audit.json",
        {"stage": "csf_holdout_validation", "selected_variant_ids": ["baseline_v1"], "regime_shift_detected": False, "audit_status": "pass", "explanation": "No material shift."},
    )

    payload = diagnostics_payload(outputs_root=outputs_root, lineage_id="lineage", stage="csf_holdout_validation")

    assert _observed_metric(payload, "direction_match")["value"] is True
    assert _observed_metric(payload, "holdout_mean_net_return")["value"] == pytest.approx(0.01)
    assert _observed_metric(payload, "net_return_delta")["value"] == pytest.approx(-0.002)
    assert _observed_metric(payload, "drawdown_delta")["value"] == pytest.approx(-0.02)
    assert _observed_metric(payload, "bucket_stability_score")["value"] == pytest.approx(0.7)
    assert _observed_metric(payload, "rolling_stability")["value"] == "pass"
    assert _observed_metric(payload, "regime_shift_audit")["value"] == "pass"
