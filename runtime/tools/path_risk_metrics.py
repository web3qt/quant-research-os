from __future__ import annotations

import math
from statistics import mean, stdev
from typing import Any


ABS_TOLERANCE = 1e-9
REL_TOLERANCE = 1e-6


def compute_risk_metrics(
    variant_id: str,
    net_returns: list[float],
    net_pnls: list[float],
    max_drawdown: float,
) -> dict[str, Any]:
    annual_365 = mean(net_returns) * 365
    annual_252 = mean(net_returns) * 252
    vol_365 = stdev(net_returns) * math.sqrt(365) if len(net_returns) >= 2 else None
    vol_252 = stdev(net_returns) * math.sqrt(252) if len(net_returns) >= 2 else None
    return {
        "variant_id": variant_id,
        "annualized_return_365d": annual_365,
        "annualized_return_252d": annual_252,
        "volatility_365d": vol_365,
        "volatility_252d": vol_252,
        "sharpe_365d": annual_365 / vol_365 if vol_365 else None,
        "sharpe_252d": annual_252 / vol_252 if vol_252 else None,
        "sortino_365d": _sortino(net_returns, 365),
        "sortino_252d": _sortino(net_returns, 252),
        "calmar_365d": annual_365 / abs(max_drawdown) if max_drawdown else None,
        "calmar_252d": annual_252 / abs(max_drawdown) if max_drawdown else None,
        "profit_factor": profit_factor(net_pnls),
        "max_drawdown": max_drawdown,
        "observation_count": len(net_returns),
    }


def profit_factor(net_pnls: list[float]) -> float | None:
    gross_profit = sum(value for value in net_pnls if value > 0)
    gross_loss = abs(sum(value for value in net_pnls if value < 0))
    if gross_loss == 0:
        return math.inf if gross_profit > 0 else None
    return gross_profit / gross_loss


def values_close(observed: float | None, expected: float | None) -> bool:
    if observed is None or expected is None:
        return observed is None and expected is None
    if math.isinf(observed) or math.isinf(expected):
        return math.isinf(observed) and math.isinf(expected) and observed == expected
    return math.isclose(observed, expected, rel_tol=REL_TOLERANCE, abs_tol=ABS_TOLERANCE)


def _sortino(net_returns: list[float], days: int) -> float | None:
    downside = [min(value, 0.0) for value in net_returns]
    if len(downside) < 2:
        return None
    downside_vol = stdev(downside) * math.sqrt(days)
    return None if downside_vol == 0 else mean(net_returns) * days / downside_vol
