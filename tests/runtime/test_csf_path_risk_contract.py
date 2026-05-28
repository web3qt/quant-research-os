from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from runtime.tools.csf_path_risk_contract import (
    compute_risk_metrics,
    validate_path_risk_artifacts,
)


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_valid_path_risk_artifacts(
    formal_dir: Path,
    *,
    variant_id: str = "baseline_v1",
) -> None:
    formal_dir.mkdir(parents=True, exist_ok=True)
    returns = [
        {
            "date": "2024-10-01",
            "variant_id": variant_id,
            "gross_return": 0.012,
            "net_return": 0.010,
            "turnover": 0.20,
            "cost": 0.002,
            "asset_count": 2,
            "max_name_weight": 0.5,
        },
        {
            "date": "2024-10-02",
            "variant_id": variant_id,
            "gross_return": -0.004,
            "net_return": -0.005,
            "turnover": 0.10,
            "cost": 0.001,
            "asset_count": 2,
            "max_name_weight": 0.5,
        },
        {
            "date": "2024-10-03",
            "variant_id": variant_id,
            "gross_return": 0.008,
            "net_return": 0.007,
            "turnover": 0.10,
            "cost": 0.001,
            "asset_count": 2,
            "max_name_weight": 0.5,
        },
    ]
    _write_parquet_rows(formal_dir / "portfolio_return_series.parquet", returns)
    _write_parquet_rows(
        formal_dir / "equity_curve.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "gross_equity": 1.012,
                "net_equity": 1.010,
                "drawdown": 0.0,
            },
            {
                "date": "2024-10-02",
                "variant_id": variant_id,
                "gross_equity": 1.007952,
                "net_equity": 1.00495,
                "drawdown": -0.005,
            },
            {
                "date": "2024-10-03",
                "variant_id": variant_id,
                "gross_equity": 1.016015616,
                "net_equity": 1.01198465,
                "drawdown": 0.0,
            },
        ],
    )
    _write_parquet_rows(
        formal_dir / "portfolio_pnl_ledger.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "gross_pnl": 0.012,
                "cost": 0.002,
                "net_pnl": 0.010,
                "capital_base": 1.0,
                "profit_loss_sign": "profit",
            },
            {
                "date": "2024-10-02",
                "variant_id": variant_id,
                "gross_pnl": -0.004,
                "cost": 0.001,
                "net_pnl": -0.005,
                "capital_base": 1.0,
                "profit_loss_sign": "loss",
            },
            {
                "date": "2024-10-03",
                "variant_id": variant_id,
                "gross_pnl": 0.008,
                "cost": 0.001,
                "net_pnl": 0.007,
                "capital_base": 1.0,
                "profit_loss_sign": "profit",
            },
        ],
    )
    _write_parquet_rows(
        formal_dir / "asset_pnl_ledger.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "asset": "SOLUSDT",
                "weight": 0.5,
                "side": "long",
                "asset_return": 0.012,
                "gross_pnl_contribution": 0.006,
                "cost_contribution": 0.001,
                "net_pnl_contribution": 0.005,
            },
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "asset": "DOGEUSDT",
                "weight": 0.5,
                "side": "long",
                "asset_return": 0.012,
                "gross_pnl_contribution": 0.006,
                "cost_contribution": 0.001,
                "net_pnl_contribution": 0.005,
            },
            {
                "date": "2024-10-02",
                "variant_id": variant_id,
                "asset": "SOLUSDT",
                "weight": 0.5,
                "side": "long",
                "asset_return": -0.004,
                "gross_pnl_contribution": -0.002,
                "cost_contribution": 0.0005,
                "net_pnl_contribution": -0.0025,
            },
            {
                "date": "2024-10-02",
                "variant_id": variant_id,
                "asset": "DOGEUSDT",
                "weight": 0.5,
                "side": "long",
                "asset_return": -0.004,
                "gross_pnl_contribution": -0.002,
                "cost_contribution": 0.0005,
                "net_pnl_contribution": -0.0025,
            },
            {
                "date": "2024-10-03",
                "variant_id": variant_id,
                "asset": "SOLUSDT",
                "weight": 0.5,
                "side": "long",
                "asset_return": 0.008,
                "gross_pnl_contribution": 0.004,
                "cost_contribution": 0.0005,
                "net_pnl_contribution": 0.0035,
            },
            {
                "date": "2024-10-03",
                "variant_id": variant_id,
                "asset": "DOGEUSDT",
                "weight": 0.5,
                "side": "long",
                "asset_return": 0.008,
                "gross_pnl_contribution": 0.004,
                "cost_contribution": 0.0005,
                "net_pnl_contribution": 0.0035,
            },
        ],
    )
    _write_parquet_rows(
        formal_dir / "risk_adjusted_metrics.parquet",
        [
            compute_risk_metrics(
                variant_id=variant_id,
                net_returns=[0.010, -0.005, 0.007],
                net_pnls=[0.010, -0.005, 0.007],
                max_drawdown=-0.005,
            )
        ],
    )


def test_validate_path_risk_artifacts_accepts_consistent_artifacts(tmp_path: Path) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert errors == []


def test_validate_path_risk_artifacts_rejects_equity_drift(tmp_path: Path) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)
    _write_parquet_rows(
        formal_dir / "equity_curve.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": "baseline_v1",
                "gross_equity": 1.012,
                "net_equity": 1.50,
                "drawdown": 0.0,
            }
        ],
    )

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any("equity_curve.parquet: net_equity mismatch" in error for error in errors)


def test_validate_path_risk_artifacts_rejects_asset_ledger_mismatch(
    tmp_path: Path,
) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)
    _write_parquet_rows(
        formal_dir / "asset_pnl_ledger.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": "baseline_v1",
                "asset": "SOLUSDT",
                "weight": 1.0,
                "side": "long",
                "asset_return": 0.01,
                "gross_pnl_contribution": 0.01,
                "cost_contribution": 0.0,
                "net_pnl_contribution": 0.02,
            }
        ],
    )

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any(
        "asset_pnl_ledger.parquet: net_pnl_contribution aggregate mismatch" in error
        for error in errors
    )


def test_validate_path_risk_artifacts_allows_bad_but_reproducible_risk_metrics(
    tmp_path: Path,
) -> None:
    formal_dir = tmp_path / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)
    variant_id = "baseline_v1"
    _write_parquet_rows(
        formal_dir / "portfolio_return_series.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "gross_return": -0.009,
                "net_return": -0.010,
                "turnover": 0.10,
                "cost": 0.001,
                "asset_count": 1,
                "max_name_weight": 1.0,
            },
            {
                "date": "2024-10-02",
                "variant_id": variant_id,
                "gross_return": -0.019,
                "net_return": -0.020,
                "turnover": 0.10,
                "cost": 0.001,
                "asset_count": 1,
                "max_name_weight": 1.0,
            },
            {
                "date": "2024-10-03",
                "variant_id": variant_id,
                "gross_return": -0.014,
                "net_return": -0.015,
                "turnover": 0.10,
                "cost": 0.001,
                "asset_count": 1,
                "max_name_weight": 1.0,
            },
        ],
    )
    _write_parquet_rows(
        formal_dir / "equity_curve.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "gross_equity": 0.991,
                "net_equity": 0.99,
                "drawdown": -0.010,
            },
            {
                "date": "2024-10-02",
                "variant_id": variant_id,
                "gross_equity": 0.972171,
                "net_equity": 0.9702,
                "drawdown": -0.0298,
            },
            {
                "date": "2024-10-03",
                "variant_id": variant_id,
                "gross_equity": 0.958560606,
                "net_equity": 0.955647,
                "drawdown": -0.044353,
            },
        ],
    )
    _write_parquet_rows(
        formal_dir / "portfolio_pnl_ledger.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "gross_pnl": -0.009,
                "cost": 0.001,
                "net_pnl": -0.010,
                "capital_base": 1.0,
                "profit_loss_sign": "loss",
            },
            {
                "date": "2024-10-02",
                "variant_id": variant_id,
                "gross_pnl": -0.019,
                "cost": 0.001,
                "net_pnl": -0.020,
                "capital_base": 1.0,
                "profit_loss_sign": "loss",
            },
            {
                "date": "2024-10-03",
                "variant_id": variant_id,
                "gross_pnl": -0.014,
                "cost": 0.001,
                "net_pnl": -0.015,
                "capital_base": 1.0,
                "profit_loss_sign": "loss",
            },
        ],
    )
    _write_parquet_rows(
        formal_dir / "asset_pnl_ledger.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "asset": "SOLUSDT",
                "weight": 1.0,
                "side": "long",
                "asset_return": -0.009,
                "gross_pnl_contribution": -0.009,
                "cost_contribution": 0.001,
                "net_pnl_contribution": -0.010,
            },
            {
                "date": "2024-10-02",
                "variant_id": variant_id,
                "asset": "SOLUSDT",
                "weight": 1.0,
                "side": "long",
                "asset_return": -0.019,
                "gross_pnl_contribution": -0.019,
                "cost_contribution": 0.001,
                "net_pnl_contribution": -0.020,
            },
            {
                "date": "2024-10-03",
                "variant_id": variant_id,
                "asset": "SOLUSDT",
                "weight": 1.0,
                "side": "long",
                "asset_return": -0.014,
                "gross_pnl_contribution": -0.014,
                "cost_contribution": 0.001,
                "net_pnl_contribution": -0.015,
            },
        ],
    )
    _write_parquet_rows(
        formal_dir / "risk_adjusted_metrics.parquet",
        [
            compute_risk_metrics(
                variant_id=variant_id,
                net_returns=[-0.010, -0.020, -0.015],
                net_pnls=[-0.010, -0.020, -0.015],
                max_drawdown=-0.044353,
            )
        ],
    )

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=[variant_id],
        portfolio_expression="long_only_rank",
    )

    assert errors == []


def test_validate_path_risk_artifacts_rejects_duplicate_return_key(
    tmp_path: Path,
) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)
    duplicate_rows = [
        {
            "date": "2024-10-01",
            "variant_id": "baseline_v1",
            "gross_return": 0.012,
            "net_return": 0.010,
            "turnover": 0.20,
            "cost": 0.002,
            "asset_count": 2,
            "max_name_weight": 0.5,
        },
        {
            "date": "2024-10-01",
            "variant_id": "baseline_v1",
            "gross_return": 0.012,
            "net_return": 0.010,
            "turnover": 0.20,
            "cost": 0.002,
            "asset_count": 2,
            "max_name_weight": 0.5,
        },
    ]
    _write_parquet_rows(formal_dir / "portfolio_return_series.parquet", duplicate_rows)

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any("portfolio_return_series.parquet: duplicate key" in error for error in errors)


def test_validate_path_risk_artifacts_rejects_variant_drift(tmp_path: Path) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir, variant_id="leaked_variant")

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any(
        "portfolio_return_series.parquet: variant_id leaked_variant is not selected" in error
        for error in errors
    )


def test_validate_path_risk_artifacts_rejects_extra_equity_date(tmp_path: Path) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)
    _write_parquet_rows(
        formal_dir / "equity_curve.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": "baseline_v1",
                "gross_equity": 1.012,
                "net_equity": 1.010,
                "drawdown": 0.0,
            },
            {
                "date": "2024-10-02",
                "variant_id": "baseline_v1",
                "gross_equity": 1.007952,
                "net_equity": 1.00495,
                "drawdown": -0.005,
            },
            {
                "date": "2024-10-03",
                "variant_id": "baseline_v1",
                "gross_equity": 1.016015616,
                "net_equity": 1.01198465,
                "drawdown": 0.0,
            },
            {
                "date": "2024-10-04",
                "variant_id": "baseline_v1",
                "gross_equity": 1.016015616,
                "net_equity": 1.01198465,
                "drawdown": 0.0,
            },
        ],
    )

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any("equity_curve.parquet: unexpected dates" in error for error in errors)


def test_validate_path_risk_artifacts_rejects_extra_asset_ledger_date(
    tmp_path: Path,
) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)
    table = pq.read_table(formal_dir / "asset_pnl_ledger.parquet").to_pylist()
    table.append(
        {
            "date": "2024-10-04",
            "variant_id": "baseline_v1",
            "asset": "SOLUSDT",
            "weight": 1.0,
            "side": "long",
            "asset_return": 0.0,
            "gross_pnl_contribution": 0.0,
            "cost_contribution": 0.0,
            "net_pnl_contribution": 0.0,
        }
    )
    _write_parquet_rows(formal_dir / "asset_pnl_ledger.parquet", table)

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any("asset_pnl_ledger.parquet: unexpected dates" in error for error in errors)


def test_validate_path_risk_artifacts_requires_exact_observation_count(
    tmp_path: Path,
) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)
    metrics = pq.read_table(formal_dir / "risk_adjusted_metrics.parquet").to_pylist()
    metrics[0]["observation_count"] = 4
    _write_parquet_rows(formal_dir / "risk_adjusted_metrics.parquet", metrics)

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any("risk_adjusted_metrics.parquet: observation_count mismatch" in error for error in errors)


def test_validate_path_risk_artifacts_rejects_fractional_observation_count(
    tmp_path: Path,
) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)
    metrics = pq.read_table(formal_dir / "risk_adjusted_metrics.parquet").to_pylist()
    metrics[0]["observation_count"] = 3.9
    _write_parquet_rows(formal_dir / "risk_adjusted_metrics.parquet", metrics)

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any("risk_adjusted_metrics.parquet: observation_count mismatch" in error for error in errors)
