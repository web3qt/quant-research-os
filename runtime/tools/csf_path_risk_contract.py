from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from runtime.tools.path_risk_metrics import compute_risk_metrics, values_close

PATH_RISK_ARTIFACTS: set[str] = {
    "portfolio_return_series.parquet",
    "equity_curve.parquet",
    "portfolio_pnl_ledger.parquet",
    "asset_pnl_ledger.parquet",
    "risk_adjusted_metrics.parquet",
}

_REQUIRED = {
    "portfolio_return_series.parquet": (
        "date",
        "variant_id",
        "gross_return",
        "net_return",
        "turnover",
        "cost",
        "asset_count",
        "max_name_weight",
    ),
    "equity_curve.parquet": ("date", "variant_id", "gross_equity", "net_equity", "drawdown"),
    "portfolio_pnl_ledger.parquet": (
        "date",
        "variant_id",
        "gross_pnl",
        "cost",
        "net_pnl",
        "capital_base",
        "profit_loss_sign",
    ),
    "asset_pnl_ledger.parquet": (
        "date",
        "variant_id",
        "asset",
        "weight",
        "side",
        "asset_return",
        "gross_pnl_contribution",
        "cost_contribution",
        "net_pnl_contribution",
    ),
    "risk_adjusted_metrics.parquet": (
        "variant_id",
        "annualized_return_365d",
        "annualized_return_252d",
        "volatility_365d",
        "volatility_252d",
        "sharpe_365d",
        "sharpe_252d",
        "sortino_365d",
        "sortino_252d",
        "calmar_365d",
        "calmar_252d",
        "profit_factor",
        "max_drawdown",
        "observation_count",
    ),
}
_NON_NUMERIC = {"date", "variant_id", "asset", "side", "profit_loss_sign"}
_NUMERIC = {name: tuple(col for col in cols if col not in _NON_NUMERIC) for name, cols in _REQUIRED.items()}
_NULLABLE_METRICS = {
    "volatility_365d",
    "volatility_252d",
    "sharpe_365d",
    "sharpe_252d",
    "sortino_365d",
    "sortino_252d",
    "calmar_365d",
    "calmar_252d",
    "profit_factor",
}


def validate_path_risk_artifacts(formal_dir: Path, *, selected_variant_ids: list[str], portfolio_expression: str) -> list[str]:
    errors: list[str] = []
    rows = {artifact: _read_rows(formal_dir / artifact, errors) for artifact in sorted(PATH_RISK_ARTIFACTS)}
    if errors:
        return errors
    selected = set(selected_variant_ids)
    for artifact, artifact_rows in rows.items():
        key = ("variant_id",) if artifact == "risk_adjusted_metrics.parquet" else ("date", "variant_id")
        if artifact == "asset_pnl_ledger.parquet":
            key = ("date", "variant_id", "asset")
        errors.extend(_validate_rows(artifact, artifact_rows, selected, key))
    if errors:
        return errors

    returns = rows["portfolio_return_series.parquet"]
    equity = rows["equity_curve.parquet"]
    portfolio = rows["portfolio_pnl_ledger.parquet"]
    assets = rows["asset_pnl_ledger.parquet"]
    metrics = rows["risk_adjusted_metrics.parquet"]
    for variant_id in sorted(selected):
        variant_returns = _rows_for_variant(returns, variant_id)
        variant_metrics = _rows_for_variant(metrics, variant_id)
        if not variant_returns:
            errors.append(f"portfolio_return_series.parquet: missing selected variant {variant_id}")
            continue
        if len(variant_metrics) != 1:
            errors.append(f"risk_adjusted_metrics.parquet: expected one row for variant_id {variant_id}")
            continue
        variant_portfolio = _rows_for_variant(portfolio, variant_id)
        errors.extend(_validate_equity(variant_id, variant_returns, _rows_for_variant(equity, variant_id)))
        errors.extend(_validate_portfolio_ledger(variant_id, variant_returns, variant_portfolio))
        errors.extend(_validate_asset_ledger(variant_id, variant_portfolio, _rows_for_variant(assets, variant_id), portfolio_expression))
        errors.extend(_validate_metrics(variant_id, variant_returns, variant_portfolio, variant_metrics[0]))
    return errors


def _validate_rows(artifact: str, rows: list[dict[str, Any]], selected: set[str], key_columns: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        missing = [col for col in _REQUIRED[artifact] if col not in row]
        if missing:
            errors.append(f"{artifact}: missing required columns {missing}")
            continue
        variant_id = str(row["variant_id"])
        if variant_id not in selected:
            errors.append(f"{artifact}: variant_id {variant_id} is not selected")
        if "date" in row and _date_key(row["date"]) is None:
            errors.append(f"{artifact}: date is not parseable: {row['date']!r}")
        key = tuple(_date_key(row[col]) if col == "date" else row[col] for col in key_columns)
        if key in seen:
            errors.append(f"{artifact}: duplicate key {key}")
        seen.add(key)
        for col in _NUMERIC[artifact]:
            if col in _NULLABLE_METRICS and row[col] is None:
                continue
            if not _is_numeric(row[col], allow_inf=col in _NULLABLE_METRICS):
                errors.append(f"{artifact}: {col} must be finite numeric")
    return errors


def _validate_equity(variant_id: str, returns: list[dict[str, Any]], equity: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    equity_by_date = {_date_key(row["date"]): row for row in equity}
    return_dates = {_date_key(row["date"]) for row in returns}
    extra_dates = sorted(set(equity_by_date) - return_dates)
    if extra_dates:
        errors.append(f"equity_curve.parquet: unexpected dates for variant_id {variant_id}: {extra_dates!r}")
    gross_equity = net_equity = peak = 1.0
    for row in _sort_by_date(returns):
        day = _date_key(row["date"])
        observed = equity_by_date.get(day)
        if observed is None:
            errors.append(f"equity_curve.parquet: missing row for variant_id {variant_id} date {day}")
            continue
        gross_equity *= 1 + _float(row["gross_return"])
        net_equity *= 1 + _float(row["net_return"])
        peak = max(peak, net_equity)
        for col, expected in (("gross_equity", gross_equity), ("net_equity", net_equity), ("drawdown", net_equity / peak - 1.0)):
            if not values_close(_optional_float(observed[col]), expected):
                errors.append(f"equity_curve.parquet: {col} mismatch for variant_id {variant_id} date {day}")
    return errors


def _validate_portfolio_ledger(variant_id: str, returns: list[dict[str, Any]], portfolio: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    portfolio_by_date = {_date_key(row["date"]): row for row in portfolio}
    return_dates = {_date_key(row["date"]) for row in returns}
    extra_dates = sorted(set(portfolio_by_date) - return_dates)
    if extra_dates:
        errors.append(f"portfolio_pnl_ledger.parquet: unexpected dates for variant_id {variant_id}: {extra_dates!r}")
    for row in _sort_by_date(returns):
        day = _date_key(row["date"])
        observed = portfolio_by_date.get(day)
        if observed is None:
            errors.append(f"portfolio_pnl_ledger.parquet: missing row for variant_id {variant_id} date {day}")
            continue
        capital_base = _float(observed["capital_base"])
        checks = (("gross_pnl", _float(row["gross_return"]) * capital_base), ("net_pnl", _float(row["net_return"]) * capital_base), ("cost", _float(row["cost"]) * capital_base))
        for col, expected in checks:
            if not values_close(_optional_float(observed[col]), expected):
                errors.append(f"portfolio_pnl_ledger.parquet: {col} mismatch for variant_id {variant_id} date {day}")
        if observed["profit_loss_sign"] != _profit_loss_sign(_float(observed["net_pnl"])):
            errors.append(f"portfolio_pnl_ledger.parquet: profit_loss_sign mismatch for variant_id {variant_id} date {day}")
    return errors


def _validate_asset_ledger(variant_id: str, portfolio: list[dict[str, Any]], assets: list[dict[str, Any]], portfolio_expression: str) -> list[str]:
    errors: list[str] = []
    assets_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in assets:
        assets_by_date[_date_key(row["date"])].append(row)
    portfolio_dates = {_date_key(row["date"]) for row in portfolio}
    extra_dates = sorted(set(assets_by_date) - portfolio_dates)
    if extra_dates:
        errors.append(f"asset_pnl_ledger.parquet: unexpected dates for variant_id {variant_id}: {extra_dates!r}")
    for row in _sort_by_date(portfolio):
        day = _date_key(row["date"])
        day_assets = assets_by_date.get(day, [])
        if not day_assets:
            errors.append(f"asset_pnl_ledger.parquet: missing rows for variant_id {variant_id} date {day}")
            continue
        for asset_col, portfolio_col in (("gross_pnl_contribution", "gross_pnl"), ("cost_contribution", "cost"), ("net_pnl_contribution", "net_pnl")):
            if not values_close(sum(_float(asset[asset_col]) for asset in day_assets), _float(row[portfolio_col])):
                errors.append(f"asset_pnl_ledger.parquet: {asset_col} aggregate mismatch for variant_id {variant_id} date {day}")
        errors.extend(_validate_exposure(day, variant_id, day_assets, portfolio_expression))
    return errors


def _validate_exposure(day: str, variant_id: str, rows: list[dict[str, Any]], portfolio_expression: str) -> list[str]:
    sides = {str(row["side"]) for row in rows}
    long_weight = sum(_float(row["weight"]) for row in rows if row["side"] == "long")
    short_weight = sum(abs(_float(row["weight"])) for row in rows if row["side"] == "short")
    prefix = f"asset_pnl_ledger.parquet: exposure mismatch for variant_id {variant_id} date {day}"
    if portfolio_expression == "long_only_rank" and (sides != {"long"} or not values_close(long_weight, 1.0)):
        return [f"{prefix}: long_only_rank requires all long side and total weight 1.0"]
    if portfolio_expression == "short_only_rank" and (sides != {"short"} or not values_close(short_weight, 1.0)):
        return [f"{prefix}: short_only_rank requires all short side and absolute total weight 1.0"]
    if portfolio_expression == "long_short_market_neutral":
        if "long" not in sides or "short" not in sides:
            return [f"{prefix}: long_short_market_neutral requires both long and short sides"]
        if not values_close(long_weight, short_weight) or not values_close(long_weight, 1.0):
            return [f"{prefix}: long_short_market_neutral requires balanced 1.0/1.0 gross side exposure"]
    return []


def _validate_metrics(variant_id: str, returns: list[dict[str, Any]], portfolio: list[dict[str, Any]], metrics: dict[str, Any]) -> list[str]:
    net_returns = [_float(row["net_return"]) for row in _sort_by_date(returns)]
    net_pnls = [_float(row["net_pnl"]) for row in _sort_by_date(portfolio)]
    expected = compute_risk_metrics(variant_id, net_returns, net_pnls, _recompute_max_drawdown(net_returns))
    errors: list[str] = []
    for col, expected_value in expected.items():
        if col == "variant_id":
            if metrics[col] != expected_value:
                errors.append(f"risk_adjusted_metrics.parquet: variant_id mismatch for variant_id {variant_id}")
        elif col == "observation_count":
            observed_count = _optional_float(metrics[col])
            expected_count = _optional_float(expected_value)
            if (
                observed_count is None
                or expected_count is None
                or not observed_count.is_integer()
                or int(observed_count) != int(expected_count)
            ):
                errors.append(f"risk_adjusted_metrics.parquet: {col} mismatch for variant_id {variant_id}")
        elif not values_close(_optional_float(metrics[col]), _optional_float(expected_value)):
            errors.append(f"risk_adjusted_metrics.parquet: {col} mismatch for variant_id {variant_id}")
    return errors


def _read_rows(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq

        rows = pq.read_table(path).to_pylist()
    except Exception as exc:
        errors.append(f"{path.name}: parquet read failed: {exc}")
        return []
    if not rows:
        errors.append(f"{path.name}: must contain at least one row")
    return rows


def _date_key(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            return None
    return None


def _recompute_max_drawdown(net_returns: list[float]) -> float:
    equity = peak = 1.0
    max_drawdown = 0.0
    for net_return in net_returns:
        equity *= 1 + net_return
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1.0)
    return max_drawdown


def _rows_for_variant(rows: Iterable[dict[str, Any]], variant_id: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["variant_id"] == variant_id]


def _sort_by_date(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: _date_key(row["date"]))


def _profit_loss_sign(net_pnl: float) -> str:
    return "profit" if net_pnl > 0 else "loss" if net_pnl < 0 else "flat"


def _is_numeric(value: Any, *, allow_inf: bool) -> bool:
    if isinstance(value, bool):
        return False
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) or (allow_inf and math.isinf(numeric))


def _float(value: Any) -> float:
    return float(value)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
