# CSF Path-Level Risk Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make CSF backtest and holdout formal contracts require path-level return, equity, PnL ledger, asset attribution, and risk metric artifacts with deterministic consistency checks.

**Architecture:** Add required artifact shapes to both CSF contracts, generate fixture-quality outputs from the existing CSF runtime builders, and add a shared `runtime/tools/csf_path_risk_contract.py` validator used by both stage semantic validators. Keep performance gates unchanged: existing net-return and holdout direction gates remain, while Sharpe/Calmar/profit factor are checked for presence and reproducibility only.

**Tech Stack:** Python 3.13, pytest, pyarrow parquet, YAML/JSON contract files, QROS runtime validators.

---

## File Structure

- Modify `contracts/artifacts/csf_backtest_ready_artifacts.yaml`: add five required formal parquet artifacts and include them in run manifest output expectations.
- Modify `contracts/artifacts/csf_holdout_validation_artifacts.yaml`: add the same five required formal parquet artifacts and include them in holdout manifest output expectations.
- Modify `contracts/diagnostics/factor_metric_library.yaml`: make Sharpe/Sortino/Calmar/profit factor read from `risk_adjusted_metrics.parquet`; add holdout path-risk metric sources.
- Modify `contracts/diagnostics/csf_stage_diagnostic_profiles.yaml`: promote CSF backtest path-risk metrics to required and add holdout path-risk diagnostics.
- Create `runtime/tools/csf_path_risk_contract.py`: shared deterministic checks for return series, equity curve, portfolio ledger, asset ledger, and risk metrics.
- Modify `runtime/tools/csf_backtest_ready_contract_runtime.py`: call the shared validator and require new stage outputs.
- Modify `runtime/tools/csf_holdout_validation_contract_runtime.py`: call the shared validator and require new stage outputs.
- Modify `runtime/tools/csf_backtest_runtime.py`: fixture builder writes consistent path-risk artifacts.
- Modify `runtime/tools/csf_holdout_runtime.py`: fixture builder writes holdout artifacts with the same shape.
- Modify `runtime/tools/factor_diagnostics.py`: read risk metrics from `risk_adjusted_metrics.parquet` instead of gap-detecting Sharpe/Sortino/Calmar/profit factor.
- Modify tests under `tests/contracts/`, `tests/runtime/`, and `tests/docs/` listed below.
- Modify docs and skills listed in the spec so user-facing behavior matches the new hard contract.

## Shared Test Helpers

Create local helper snippets inside runtime tests rather than a broad new test utility unless duplication grows beyond these files.

Use this deterministic path-risk fixture for a single `variant_id`:

```python
PATH_RISK_RETURN_ROWS = [
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
        "date": "2024-10-02",
        "variant_id": "baseline_v1",
        "gross_return": -0.004,
        "net_return": -0.005,
        "turnover": 0.10,
        "cost": 0.001,
        "asset_count": 2,
        "max_name_weight": 0.5,
    },
    {
        "date": "2024-10-03",
        "variant_id": "baseline_v1",
        "gross_return": 0.008,
        "net_return": 0.007,
        "turnover": 0.10,
        "cost": 0.001,
        "asset_count": 2,
        "max_name_weight": 0.5,
    },
]
```

Expected normalized portfolio rows use `capital_base = 1.0` and `net_pnl = net_return`.

---

### Task 1: Contract Shape Tests

**Files:**
- Modify: `tests/contracts/test_csf_backtest_ready_artifact_contract.py`
- Modify: `tests/contracts/test_csf_holdout_validation_artifact_contract.py`
- Modify: `contracts/artifacts/csf_backtest_ready_artifacts.yaml`
- Modify: `contracts/artifacts/csf_holdout_validation_artifacts.yaml`

- [ ] **Step 1: Add failing backtest artifact shape assertions**

Append assertions in `test_csf_backtest_ready_contract_locks_machine_artifact_shapes`:

```python
    assert _artifact(contract, "portfolio_return_series.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "gross_return",
        "net_return",
        "turnover",
        "cost",
        "asset_count",
        "max_name_weight",
    ]
    assert _artifact(contract, "equity_curve.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "gross_equity",
        "net_equity",
        "drawdown",
    ]
    assert _artifact(contract, "portfolio_pnl_ledger.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "gross_pnl",
        "cost",
        "net_pnl",
        "capital_base",
        "profit_loss_sign",
    ]
    assert _artifact(contract, "asset_pnl_ledger.parquet")["required_columns"] == [
        "date",
        "variant_id",
        "asset",
        "weight",
        "side",
        "asset_return",
        "gross_pnl_contribution",
        "cost_contribution",
        "net_pnl_contribution",
    ]
    assert _artifact(contract, "risk_adjusted_metrics.parquet")["required_columns"] == [
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
    ]
```

- [ ] **Step 2: Add failing holdout artifact shape assertions**

Add the same five artifact assertions to `test_csf_holdout_validation_contract_locks_machine_artifact_shapes`.

- [ ] **Step 3: Run contract tests and verify failure**

Run:

```bash
python -m pytest tests/contracts/test_csf_backtest_ready_artifact_contract.py::test_csf_backtest_ready_contract_locks_machine_artifact_shapes tests/contracts/test_csf_holdout_validation_artifact_contract.py::test_csf_holdout_validation_contract_locks_machine_artifact_shapes -q
```

Expected: both tests fail with missing artifact lookup errors.

- [ ] **Step 4: Add backtest contract artifacts**

In `contracts/artifacts/csf_backtest_ready_artifacts.yaml`, add these entries under `artifacts:` after `portfolio_summary.parquet`:

```yaml
  portfolio_return_series.parquet:
    type: parquet
    required_columns:
      - date
      - variant_id
      - gross_return
      - net_return
      - turnover
      - cost
      - asset_count
      - max_name_weight
    non_empty: true

  equity_curve.parquet:
    type: parquet
    required_columns:
      - date
      - variant_id
      - gross_equity
      - net_equity
      - drawdown
    non_empty: true

  portfolio_pnl_ledger.parquet:
    type: parquet
    required_columns:
      - date
      - variant_id
      - gross_pnl
      - cost
      - net_pnl
      - capital_base
      - profit_loss_sign
    non_empty: true

  asset_pnl_ledger.parquet:
    type: parquet
    required_columns:
      - date
      - variant_id
      - asset
      - weight
      - side
      - asset_return
      - gross_pnl_contribution
      - cost_contribution
      - net_pnl_contribution
    non_empty: true

  risk_adjusted_metrics.parquet:
    type: parquet
    required_columns:
      - variant_id
      - annualized_return_365d
      - annualized_return_252d
      - volatility_365d
      - volatility_252d
      - sharpe_365d
      - sharpe_252d
      - sortino_365d
      - sortino_252d
      - calmar_365d
      - calmar_252d
      - profit_factor
      - max_drawdown
      - observation_count
    non_empty: true
```

- [ ] **Step 5: Add holdout contract artifacts**

Add the same five entries to `contracts/artifacts/csf_holdout_validation_artifacts.yaml` after `holdout_portfolio_compare.parquet`.

- [ ] **Step 6: Run contract tests and verify pass**

Run:

```bash
python -m pytest tests/contracts/test_csf_backtest_ready_artifact_contract.py::test_csf_backtest_ready_contract_locks_machine_artifact_shapes tests/contracts/test_csf_holdout_validation_artifact_contract.py::test_csf_holdout_validation_contract_locks_machine_artifact_shapes -q
```

Expected: tests pass.

- [ ] **Step 7: Commit**

```bash
git add contracts/artifacts/csf_backtest_ready_artifacts.yaml contracts/artifacts/csf_holdout_validation_artifacts.yaml tests/contracts/test_csf_backtest_ready_artifact_contract.py tests/contracts/test_csf_holdout_validation_artifact_contract.py
git commit -m "feat: require csf path-risk artifact shapes"
```

---

### Task 2: Shared Path-Risk Validator Unit Tests

**Files:**
- Create: `runtime/tools/csf_path_risk_contract.py`
- Create: `tests/runtime/test_csf_path_risk_contract.py`

- [ ] **Step 1: Write failing happy-path and failure tests**

Create `tests/runtime/test_csf_path_risk_contract.py`:

```python
from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from runtime.tools.csf_path_risk_contract import compute_risk_metrics, validate_path_risk_artifacts


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_valid_path_risk_artifacts(formal_dir: Path, *, variant_id: str = "baseline_v1") -> None:
    formal_dir.mkdir(parents=True, exist_ok=True)
    returns = [
        {"date": "2024-10-01", "variant_id": variant_id, "gross_return": 0.012, "net_return": 0.010, "turnover": 0.20, "cost": 0.002, "asset_count": 2, "max_name_weight": 0.5},
        {"date": "2024-10-02", "variant_id": variant_id, "gross_return": -0.004, "net_return": -0.005, "turnover": 0.10, "cost": 0.001, "asset_count": 2, "max_name_weight": 0.5},
        {"date": "2024-10-03", "variant_id": variant_id, "gross_return": 0.008, "net_return": 0.007, "turnover": 0.10, "cost": 0.001, "asset_count": 2, "max_name_weight": 0.5},
    ]
    _write_parquet_rows(formal_dir / "portfolio_return_series.parquet", returns)
    _write_parquet_rows(
        formal_dir / "equity_curve.parquet",
        [
            {"date": "2024-10-01", "variant_id": variant_id, "gross_equity": 1.012, "net_equity": 1.010, "drawdown": 0.0},
            {"date": "2024-10-02", "variant_id": variant_id, "gross_equity": 1.007952, "net_equity": 1.00495, "drawdown": -0.005},
            {"date": "2024-10-03", "variant_id": variant_id, "gross_equity": 1.016015616, "net_equity": 1.01198465, "drawdown": 0.0},
        ],
    )
    _write_parquet_rows(
        formal_dir / "portfolio_pnl_ledger.parquet",
        [
            {"date": "2024-10-01", "variant_id": variant_id, "gross_pnl": 0.012, "cost": 0.002, "net_pnl": 0.010, "capital_base": 1.0, "profit_loss_sign": "profit"},
            {"date": "2024-10-02", "variant_id": variant_id, "gross_pnl": -0.004, "cost": 0.001, "net_pnl": -0.005, "capital_base": 1.0, "profit_loss_sign": "loss"},
            {"date": "2024-10-03", "variant_id": variant_id, "gross_pnl": 0.008, "cost": 0.001, "net_pnl": 0.007, "capital_base": 1.0, "profit_loss_sign": "profit"},
        ],
    )
    _write_parquet_rows(
        formal_dir / "asset_pnl_ledger.parquet",
        [
            {"date": "2024-10-01", "variant_id": variant_id, "asset": "SOLUSDT", "weight": 0.5, "side": "long", "asset_return": 0.012, "gross_pnl_contribution": 0.006, "cost_contribution": 0.001, "net_pnl_contribution": 0.005},
            {"date": "2024-10-01", "variant_id": variant_id, "asset": "DOGEUSDT", "weight": 0.5, "side": "long", "asset_return": 0.012, "gross_pnl_contribution": 0.006, "cost_contribution": 0.001, "net_pnl_contribution": 0.005},
            {"date": "2024-10-02", "variant_id": variant_id, "asset": "SOLUSDT", "weight": 0.5, "side": "long", "asset_return": -0.004, "gross_pnl_contribution": -0.002, "cost_contribution": 0.0005, "net_pnl_contribution": -0.0025},
            {"date": "2024-10-02", "variant_id": variant_id, "asset": "DOGEUSDT", "weight": 0.5, "side": "long", "asset_return": -0.004, "gross_pnl_contribution": -0.002, "cost_contribution": 0.0005, "net_pnl_contribution": -0.0025},
            {"date": "2024-10-03", "variant_id": variant_id, "asset": "SOLUSDT", "weight": 0.5, "side": "long", "asset_return": 0.008, "gross_pnl_contribution": 0.004, "cost_contribution": 0.0005, "net_pnl_contribution": 0.0035},
            {"date": "2024-10-03", "variant_id": variant_id, "asset": "DOGEUSDT", "weight": 0.5, "side": "long", "asset_return": 0.008, "gross_pnl_contribution": 0.004, "cost_contribution": 0.0005, "net_pnl_contribution": 0.0035},
        ],
    )
    _write_parquet_rows(
        formal_dir / "risk_adjusted_metrics.parquet",
        [
            {
                "variant_id": variant_id,
                "annualized_return_365d": 1.46,
                "annualized_return_252d": 1.008,
                "volatility_365d": 0.1469693845669907,
                "volatility_252d": 0.12210651088302175,
                "sharpe_365d": 9.933360652841385,
                "sharpe_252d": 8.255087035380547,
                "sortino_365d": 0.0,
                "sortino_252d": 0.0,
                "calmar_365d": 292.0,
                "calmar_252d": 201.6,
                "profit_factor": 3.4,
                "max_drawdown": -0.005,
                "observation_count": 3,
            }
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
        [{"date": "2024-10-01", "variant_id": "baseline_v1", "gross_equity": 1.012, "net_equity": 1.50, "drawdown": 0.0}],
    )

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any("equity_curve.parquet: net_equity mismatch" in error for error in errors)


def test_validate_path_risk_artifacts_rejects_asset_ledger_mismatch(tmp_path: Path) -> None:
    formal_dir = tmp_path / "formal"
    _write_valid_path_risk_artifacts(formal_dir)
    _write_parquet_rows(
        formal_dir / "asset_pnl_ledger.parquet",
        [{"date": "2024-10-01", "variant_id": "baseline_v1", "asset": "SOLUSDT", "weight": 1.0, "side": "long", "asset_return": 0.01, "gross_pnl_contribution": 0.01, "cost_contribution": 0.0, "net_pnl_contribution": 0.02}],
    )

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=["baseline_v1"],
        portfolio_expression="long_only_rank",
    )

    assert any("asset_pnl_ledger.parquet: net_pnl_contribution aggregate mismatch" in error for error in errors)


def test_validate_path_risk_artifacts_allows_bad_but_reproducible_risk_metrics(tmp_path: Path) -> None:
    formal_dir = tmp_path / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)
    variant_id = "baseline_v1"
    _write_parquet_rows(
        formal_dir / "portfolio_return_series.parquet",
        [
            {"date": "2024-10-01", "variant_id": variant_id, "gross_return": -0.009, "net_return": -0.010, "turnover": 0.10, "cost": 0.001, "asset_count": 1, "max_name_weight": 1.0},
            {"date": "2024-10-02", "variant_id": variant_id, "gross_return": -0.019, "net_return": -0.020, "turnover": 0.10, "cost": 0.001, "asset_count": 1, "max_name_weight": 1.0},
            {"date": "2024-10-03", "variant_id": variant_id, "gross_return": -0.014, "net_return": -0.015, "turnover": 0.10, "cost": 0.001, "asset_count": 1, "max_name_weight": 1.0},
        ],
    )
    _write_parquet_rows(
        formal_dir / "equity_curve.parquet",
        [
            {"date": "2024-10-01", "variant_id": variant_id, "gross_equity": 0.991, "net_equity": 0.99, "drawdown": -0.010},
            {"date": "2024-10-02", "variant_id": variant_id, "gross_equity": 0.972171, "net_equity": 0.9702, "drawdown": -0.0298},
            {"date": "2024-10-03", "variant_id": variant_id, "gross_equity": 0.958560606, "net_equity": 0.955647, "drawdown": -0.044353},
        ],
    )
    _write_parquet_rows(
        formal_dir / "portfolio_pnl_ledger.parquet",
        [
            {"date": "2024-10-01", "variant_id": variant_id, "gross_pnl": -0.009, "cost": 0.001, "net_pnl": -0.010, "capital_base": 1.0, "profit_loss_sign": "loss"},
            {"date": "2024-10-02", "variant_id": variant_id, "gross_pnl": -0.019, "cost": 0.001, "net_pnl": -0.020, "capital_base": 1.0, "profit_loss_sign": "loss"},
            {"date": "2024-10-03", "variant_id": variant_id, "gross_pnl": -0.014, "cost": 0.001, "net_pnl": -0.015, "capital_base": 1.0, "profit_loss_sign": "loss"},
        ],
    )
    _write_parquet_rows(
        formal_dir / "asset_pnl_ledger.parquet",
        [
            {"date": "2024-10-01", "variant_id": variant_id, "asset": "SOLUSDT", "weight": 1.0, "side": "long", "asset_return": -0.009, "gross_pnl_contribution": -0.009, "cost_contribution": 0.001, "net_pnl_contribution": -0.010},
            {"date": "2024-10-02", "variant_id": variant_id, "asset": "SOLUSDT", "weight": 1.0, "side": "long", "asset_return": -0.019, "gross_pnl_contribution": -0.019, "cost_contribution": 0.001, "net_pnl_contribution": -0.020},
            {"date": "2024-10-03", "variant_id": variant_id, "asset": "SOLUSDT", "weight": 1.0, "side": "long", "asset_return": -0.014, "gross_pnl_contribution": -0.014, "cost_contribution": 0.001, "net_pnl_contribution": -0.015},
        ],
    )
    _write_parquet_rows(
        formal_dir / "risk_adjusted_metrics.parquet",
        [compute_risk_metrics(variant_id=variant_id, net_returns=[-0.010, -0.020, -0.015], net_pnls=[-0.010, -0.020, -0.015], max_drawdown=-0.044353)],
    )

    errors = validate_path_risk_artifacts(
        formal_dir,
        selected_variant_ids=[variant_id],
        portfolio_expression="long_only_rank",
    )

    assert errors == []
```

- [ ] **Step 2: Run tests and verify import failure**

Run:

```bash
python -m pytest tests/runtime/test_csf_path_risk_contract.py -q
```

Expected: fail because `runtime.tools.csf_path_risk_contract` does not exist.

- [ ] **Step 3: Implement shared validator module**

Create `runtime/tools/csf_path_risk_contract.py` with these public interfaces:

```python
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from typing import Any


ABS_TOLERANCE = 1e-9
REL_TOLERANCE = 1e-6
PATH_RISK_ARTIFACTS = {
    "portfolio_return_series.parquet",
    "equity_curve.parquet",
    "portfolio_pnl_ledger.parquet",
    "asset_pnl_ledger.parquet",
    "risk_adjusted_metrics.parquet",
}


def compute_risk_metrics(
    *,
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
        "profit_factor": _profit_factor(net_pnls),
        "max_drawdown": max_drawdown,
        "observation_count": len(net_returns),
    }


def validate_path_risk_artifacts(
    formal_dir: Path,
    *,
    selected_variant_ids: list[str],
    portfolio_expression: str,
) -> list[str]:
    errors: list[str] = []
    returns = _read_rows(formal_dir / "portfolio_return_series.parquet", errors)
    equity = _read_rows(formal_dir / "equity_curve.parquet", errors)
    portfolio_ledger = _read_rows(formal_dir / "portfolio_pnl_ledger.parquet", errors)
    asset_ledger = _read_rows(formal_dir / "asset_pnl_ledger.parquet", errors)
    metrics = _read_rows(formal_dir / "risk_adjusted_metrics.parquet", errors)
    if errors:
        return errors

    selected = set(selected_variant_ids)
    for artifact_name, rows, key_columns in [
        ("portfolio_return_series.parquet", returns, ("date", "variant_id")),
        ("equity_curve.parquet", equity, ("date", "variant_id")),
        ("portfolio_pnl_ledger.parquet", portfolio_ledger, ("date", "variant_id")),
        ("asset_pnl_ledger.parquet", asset_ledger, ("date", "variant_id", "asset")),
        ("risk_adjusted_metrics.parquet", metrics, ("variant_id",)),
    ]:
        errors.extend(_validate_rows(artifact_name, rows, selected, key_columns))
    if errors:
        return errors

    for variant_id in sorted(selected):
        variant_returns = _rows_for_variant(returns, variant_id)
        variant_equity = _rows_for_variant(equity, variant_id)
        variant_portfolio = _rows_for_variant(portfolio_ledger, variant_id)
        variant_assets = _rows_for_variant(asset_ledger, variant_id)
        variant_metrics = _rows_for_variant(metrics, variant_id)
        if not variant_returns:
            errors.append(f"portfolio_return_series.parquet: missing selected variant {variant_id}")
            continue
        if len(variant_metrics) != 1:
            errors.append(f"risk_adjusted_metrics.parquet: expected one row for variant_id {variant_id}")
            continue
        errors.extend(_validate_equity(variant_id, variant_returns, variant_equity))
        errors.extend(_validate_portfolio_ledger(variant_id, variant_returns, variant_portfolio))
        errors.extend(_validate_asset_ledger(variant_id, variant_portfolio, variant_assets, portfolio_expression))
        errors.extend(_validate_metrics(variant_id, variant_returns, variant_portfolio, variant_metrics[0]))
    return errors


def _read_rows(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq

        return pq.read_table(path).to_pylist()
    except Exception as exc:
        errors.append(f"{path.name}: parquet read failed: {exc}")
        return []
```

Add these metric helpers in the same module:

```python
def _sortino(net_returns: list[float], annualization_days: int) -> float | None:
    downside = [min(value, 0.0) for value in net_returns]
    if len(downside) < 2:
        return None
    downside_vol = stdev(downside) * math.sqrt(annualization_days)
    if downside_vol == 0:
        return None
    return mean(net_returns) * annualization_days / downside_vol


def _profit_factor(net_pnls: list[float]) -> float | None:
    gross_profit = sum(value for value in net_pnls if value > 0)
    gross_loss = abs(sum(value for value in net_pnls if value < 0))
    if gross_loss == 0 and gross_profit > 0:
        return math.inf
    if gross_loss == 0:
        return None
    return gross_profit / gross_loss


def _is_close(observed: float | None, expected: float | None) -> bool:
    if observed is None or expected is None:
        return observed is None and expected is None
    if math.isinf(observed) or math.isinf(expected):
        return math.isinf(observed) and math.isinf(expected) and observed == expected
    return math.isclose(observed, expected, rel_tol=REL_TOLERANCE, abs_tol=ABS_TOLERANCE)
```

Add validation helpers with these responsibilities:

- `_validate_rows`: check non-empty rows, selected variant membership, duplicate keys, parseable `date`, and finite numeric fields.
- `_validate_equity`: sort by date, recompute gross/net equity from returns with initial equity `1.0`, recompute drawdown from running peak, and emit messages containing `equity_curve.parquet: net_equity mismatch`, `gross_equity mismatch`, or `drawdown mismatch`.
- `_validate_portfolio_ledger`: match each `date × variant_id` to return rows, verify gross/net PnL equals return times `capital_base`, verify `cost`, and verify `profit_loss_sign`.
- `_validate_asset_ledger`: aggregate contribution rows by `date × variant_id`, compare gross/cost/net sums to portfolio ledger, and enforce `long_only_rank` sides are `long` with total weight `1.0`.
- `_validate_metrics`: recompute `compute_risk_metrics(...)` and compare every risk metric column in `risk_adjusted_metrics.parquet`.

Keep this module under 250 lines; split metric math into `runtime/tools/path_risk_metrics.py` only if the completed implementation exceeds that size.

- [ ] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/runtime/test_csf_path_risk_contract.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/csf_path_risk_contract.py tests/runtime/test_csf_path_risk_contract.py
git commit -m "feat: validate csf path-risk consistency"
```

---

### Task 3: Runtime Builders Produce New Formal Artifacts

**Files:**
- Modify: `runtime/tools/csf_backtest_runtime.py`
- Modify: `runtime/tools/csf_holdout_runtime.py`
- Modify: `tests/runtime/test_csf_backtest_runtime.py`
- Modify: `tests/runtime/test_csf_holdout_runtime.py`

- [ ] **Step 1: Add failing backtest builder assertions**

In `test_build_csf_backtest_ready_writes_required_outputs`, add:

```python
    assert (formal_dir / "portfolio_return_series.parquet").exists()
    assert (formal_dir / "equity_curve.parquet").exists()
    assert (formal_dir / "portfolio_pnl_ledger.parquet").exists()
    assert (formal_dir / "asset_pnl_ledger.parquet").exists()
    assert (formal_dir / "risk_adjusted_metrics.parquet").exists()
    assert pq.read_table(formal_dir / "portfolio_return_series.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "equity_curve.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "portfolio_pnl_ledger.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "asset_pnl_ledger.parquet").num_rows > 0
    assert pq.read_table(formal_dir / "risk_adjusted_metrics.parquet").num_rows > 0
```

- [ ] **Step 2: Add failing holdout builder assertions**

In `tests/runtime/test_csf_holdout_runtime.py`, add equivalent existence and non-empty assertions to the holdout build test.

- [ ] **Step 3: Run builder tests and verify failure**

Run:

```bash
python -m pytest tests/runtime/test_csf_backtest_runtime.py::test_build_csf_backtest_ready_writes_required_outputs tests/runtime/test_csf_holdout_runtime.py::test_build_csf_holdout_validation_writes_required_outputs -q
```

Expected: fail because files are not written.

- [ ] **Step 4: Add fixture path-risk writer helper to backtest runtime**

In `runtime/tools/csf_backtest_runtime.py`, add a private helper near `_write_parquet_rows`:

```python
def _write_fixture_path_risk_artifacts(stage_formal_dir: Path, selected_variant_ids: list[str]) -> None:
    for variant_id in selected_variant_ids:
        _write_parquet_rows(
            stage_formal_dir / "portfolio_return_series.parquet",
            [
                {"date": "2024-10-01", "variant_id": variant_id, "gross_return": 0.012, "net_return": 0.010, "turnover": 0.20, "cost": 0.002, "asset_count": 2, "max_name_weight": 0.5},
                {"date": "2024-10-02", "variant_id": variant_id, "gross_return": -0.004, "net_return": -0.005, "turnover": 0.10, "cost": 0.001, "asset_count": 2, "max_name_weight": 0.5},
                {"date": "2024-10-03", "variant_id": variant_id, "gross_return": 0.008, "net_return": 0.007, "turnover": 0.10, "cost": 0.001, "asset_count": 2, "max_name_weight": 0.5},
            ],
        )
        _write_parquet_rows(
            stage_formal_dir / "equity_curve.parquet",
            [
                {"date": "2024-10-01", "variant_id": variant_id, "gross_equity": 1.012, "net_equity": 1.010, "drawdown": 0.0},
                {"date": "2024-10-02", "variant_id": variant_id, "gross_equity": 1.007952, "net_equity": 1.00495, "drawdown": -0.005},
                {"date": "2024-10-03", "variant_id": variant_id, "gross_equity": 1.016015616, "net_equity": 1.01198465, "drawdown": 0.0},
            ],
        )
        _write_parquet_rows(
            stage_formal_dir / "portfolio_pnl_ledger.parquet",
            [
                {"date": "2024-10-01", "variant_id": variant_id, "gross_pnl": 0.012, "cost": 0.002, "net_pnl": 0.010, "capital_base": 1.0, "profit_loss_sign": "profit"},
                {"date": "2024-10-02", "variant_id": variant_id, "gross_pnl": -0.004, "cost": 0.001, "net_pnl": -0.005, "capital_base": 1.0, "profit_loss_sign": "loss"},
                {"date": "2024-10-03", "variant_id": variant_id, "gross_pnl": 0.008, "cost": 0.001, "net_pnl": 0.007, "capital_base": 1.0, "profit_loss_sign": "profit"},
            ],
        )
```

Continue the helper by building five row lists before writing parquet files. For each `variant_id`, append the Task 2 `asset_pnl_ledger.parquet` rows and append `compute_risk_metrics(variant_id=variant_id, net_returns=[0.010, -0.005, 0.007], net_pnls=[0.010, -0.005, 0.007], max_drawdown=-0.005)` to the risk metrics rows. Write each parquet file once after all variants have been processed.

- [ ] **Step 5: Call helper in backtest build**

Call `_write_fixture_path_risk_artifacts(stage_formal_dir, selected_variant_ids)` before writing markdown reports. Add the five new artifact names to `run_manifest.json.stage_outputs` and `portfolio_contract.yaml.delivery_contract.machine_artifacts`.

- [ ] **Step 6: Add equivalent helper to holdout runtime**

For first pass, duplicate only the row constants in `runtime/tools/csf_holdout_runtime.py` if importing from backtest runtime would create an awkward dependency. Write holdout artifacts with the same shape and values. Add the five new names to `csf_holdout_run_manifest.json.stage_outputs` and delivery machine artifacts.

- [ ] **Step 7: Run builder tests**

Run:

```bash
python -m pytest tests/runtime/test_csf_backtest_runtime.py::test_build_csf_backtest_ready_writes_required_outputs tests/runtime/test_csf_holdout_runtime.py::test_build_csf_holdout_validation_writes_required_outputs -q
```

Expected: pass.

- [ ] **Step 8: Commit**

```bash
git add runtime/tools/csf_backtest_runtime.py runtime/tools/csf_holdout_runtime.py tests/runtime/test_csf_backtest_runtime.py tests/runtime/test_csf_holdout_runtime.py
git commit -m "feat: emit csf path-risk fixture artifacts"
```

---

### Task 4: Stage Semantic Validators Enforce Path-Risk Contract

**Files:**
- Modify: `runtime/tools/csf_backtest_ready_contract_runtime.py`
- Modify: `runtime/tools/csf_holdout_validation_contract_runtime.py`
- Modify: `tests/runtime/test_csf_backtest_ready_semantic_validation.py`
- Modify: `tests/runtime/test_csf_holdout_validation_semantic_validation.py`

- [ ] **Step 1: Add failing semantic tests for missing path-risk output**

Add to backtest semantic tests:

```python
def test_csf_backtest_ready_semantics_rejects_missing_path_risk_artifacts(tmp_path: Path) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    (formal_dir / "portfolio_return_series.parquet").unlink()

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert any("portfolio_return_series.parquet" in error for error in result.errors)
```

Add the equivalent holdout test in `tests/runtime/test_csf_holdout_validation_semantic_validation.py`.

- [ ] **Step 2: Add failing semantic tests for metric inconsistency**

Add backtest test:

```python
def test_csf_backtest_ready_semantics_rejects_risk_metric_drift(tmp_path: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    pq.write_table(
        pa.table(
            {
                "variant_id": ["baseline_v1"],
                "annualized_return_365d": [999.0],
                "annualized_return_252d": [999.0],
                "volatility_365d": [1.0],
                "volatility_252d": [1.0],
                "sharpe_365d": [999.0],
                "sharpe_252d": [999.0],
                "sortino_365d": [999.0],
                "sortino_252d": [999.0],
                "calmar_365d": [999.0],
                "calmar_252d": [999.0],
                "profit_factor": [999.0],
                "max_drawdown": [-0.005],
                "observation_count": [3],
            }
        ),
        formal_dir / "risk_adjusted_metrics.parquet",
    )

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert any("risk_adjusted_metrics.parquet: annualized_return_365d mismatch" in error for error in result.errors)
```

Add an equivalent holdout test.

- [ ] **Step 3: Run semantic tests and verify failure**

Run:

```bash
python -m pytest tests/runtime/test_csf_backtest_ready_semantic_validation.py tests/runtime/test_csf_holdout_validation_semantic_validation.py -q
```

Expected: new tests fail until validators call the shared path-risk validator.

- [ ] **Step 4: Wire backtest semantic validator**

In `runtime/tools/csf_backtest_ready_contract_runtime.py`, import:

```python
from runtime.tools.csf_path_risk_contract import PATH_RISK_ARTIFACTS, validate_path_risk_artifacts
```

Update `REQUIRED_STAGE_OUTPUTS` to include `PATH_RISK_ARTIFACTS`.

After existing parquet variant checks, add:

```python
    errors.extend(
        validate_path_risk_artifacts(
            stage_formal_dir,
            selected_variant_ids=selected_variant_ids,
            portfolio_expression=str(portfolio_contract.get("portfolio_expression", "")).strip(),
        )
    )
```

- [ ] **Step 5: Wire holdout semantic validator**

In `runtime/tools/csf_holdout_validation_contract_runtime.py`, import the same helper. Update `REQUIRED_STAGE_OUTPUTS` and add:

```python
    errors.extend(
        validate_path_risk_artifacts(
            stage_formal_dir,
            selected_variant_ids=selected_variant_ids,
            portfolio_expression=str(run_manifest.get("portfolio_expression", "")).strip(),
        )
    )
```

- [ ] **Step 6: Run semantic tests**

Run:

```bash
python -m pytest tests/runtime/test_csf_backtest_ready_semantic_validation.py tests/runtime/test_csf_holdout_validation_semantic_validation.py -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add runtime/tools/csf_backtest_ready_contract_runtime.py runtime/tools/csf_holdout_validation_contract_runtime.py tests/runtime/test_csf_backtest_ready_semantic_validation.py tests/runtime/test_csf_holdout_validation_semantic_validation.py
git commit -m "feat: enforce csf path-risk semantic checks"
```

---

### Task 5: Diagnostics Read Formal Risk Metrics

**Files:**
- Modify: `contracts/diagnostics/factor_metric_library.yaml`
- Modify: `contracts/diagnostics/csf_stage_diagnostic_profiles.yaml`
- Modify: `runtime/tools/factor_diagnostics.py`
- Modify: `tests/runtime/test_factor_diagnostics.py`
- Modify: `docs/guides/qros-factor-diagnostics.md`

- [ ] **Step 1: Add failing diagnostics test**

In `tests/runtime/test_factor_diagnostics.py`, extend the CSF backtest fixture to write `risk_adjusted_metrics.parquet` and assert observed metrics:

```python
    _write_parquet(
        formal_dir / "risk_adjusted_metrics.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "annualized_return_365d": 1.46,
                "annualized_return_252d": 1.008,
                "volatility_365d": 0.1469693845669907,
                "volatility_252d": 0.12210651088302175,
                "sharpe_365d": 9.933360652841385,
                "sharpe_252d": 8.255087035380547,
                "sortino_365d": 0.0,
                "sortino_252d": 0.0,
                "calmar_365d": 292.0,
                "calmar_252d": 201.6,
                "profit_factor": 3.4,
                "max_drawdown": -0.005,
                "observation_count": 3,
            }
        ],
    )
    assert _observed_metric(payload, "sharpe")["value"] == pytest.approx(9.933360652841385)
    assert _observed_metric(payload, "sortino")["value"] == pytest.approx(0.0)
    assert _observed_metric(payload, "calmar")["value"] == pytest.approx(292.0)
    assert _observed_metric(payload, "profit_factor")["value"] == pytest.approx(3.4)
```

- [ ] **Step 2: Run diagnostics test and verify failure**

Run:

```bash
python -m pytest tests/runtime/test_factor_diagnostics.py -q
```

Expected: Sharpe/Sortino/Calmar/profit factor still appear as missing gaps.

- [ ] **Step 3: Update metric library and profile contracts**

In `contracts/diagnostics/factor_metric_library.yaml`, change CSF metric sources:

```yaml
  sharpe:
    required_inputs:
      - risk_adjusted_metrics.parquet.sharpe_365d
    v1_observation_mode: read_existing
```

Apply the same pattern:

- `sortino` -> `risk_adjusted_metrics.parquet.sortino_365d`
- `calmar` -> `risk_adjusted_metrics.parquet.calmar_365d`
- `profit_factor` -> `risk_adjusted_metrics.parquet.profit_factor`

In `contracts/diagnostics/csf_stage_diagnostic_profiles.yaml`, move `sharpe`, `sortino`, `calmar`, and `profit_factor` into required metrics for `csf_backtest_ready`. Add holdout risk metrics if the profile supports stage-local metric IDs; otherwise document that holdout reads the same metric file through diagnostics runtime.

- [ ] **Step 4: Update factor diagnostics observers**

In `runtime/tools/factor_diagnostics.py`, replace:

```python
        "sharpe": _gap("sharpe", "portfolio_return_series.parquet"),
        "sortino": _gap("sortino", "portfolio_return_series.parquet"),
        "calmar": _gap("calmar", "portfolio_return_series.parquet"),
        "profit_factor": _gap("profit_factor", "trade_pnl_ledger.parquet"),
```

with:

```python
        "sharpe": _risk_metric("sharpe", "sharpe_365d"),
        "sortino": _risk_metric("sortino", "sortino_365d"),
        "calmar": _risk_metric("calmar", "calmar_365d"),
        "profit_factor": _risk_metric("profit_factor", "profit_factor"),
```

Add helper near `_mean_from_holdout_factor`:

```python
def _risk_metric(metric_id: str, column: str) -> Any:
    def observe(formal_dir: Path) -> ObservedMetric | MissingMetric:
        return _mean_from_parquet(
            formal_dir / "risk_adjusted_metrics.parquet",
            metric_id,
            column,
            f"risk_adjusted_metrics.parquet.{column}",
        )

    return observe
```

- [ ] **Step 5: Update diagnostics guide**

In `docs/guides/qros-factor-diagnostics.md`, change CSF backtest row from “Sharpe / Profit Factor 缺口” to “Sharpe / Sortino / Calmar / Profit Factor formal risk metrics”.

- [ ] **Step 6: Run focused diagnostics tests**

Run:

```bash
python -m pytest tests/runtime/test_factor_diagnostics.py -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add contracts/diagnostics/factor_metric_library.yaml contracts/diagnostics/csf_stage_diagnostic_profiles.yaml runtime/tools/factor_diagnostics.py tests/runtime/test_factor_diagnostics.py docs/guides/qros-factor-diagnostics.md
git commit -m "feat: read csf formal risk metrics"
```

---

### Task 6: Docs, Skills, and Regression Tests

**Files:**
- Modify: `docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md`
- Modify: `docs/sop/main-flow/07_csf_holdout_validation_sop_cn.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-factor-diagnostics.md`
- Modify: `skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md`
- Modify: `skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md`
- Modify: `skills/csf_holdout_validation/qros-csf-holdout-validation-author/SKILL.md`
- Modify: `skills/csf_holdout_validation/qros-csf-holdout-validation-review/SKILL.md`
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: docs regression tests under `tests/docs/`

- [ ] **Step 1: Add failing docs regression assertions**

In `tests/docs/test_csf_backtest_ready_contract_first_docs.py`, add assertions that `06_csf_backtest_ready_sop_cn.md` contains:

```python
    assert "portfolio_return_series.parquet" in content
    assert "equity_curve.parquet" in content
    assert "portfolio_pnl_ledger.parquet" in content
    assert "asset_pnl_ledger.parquet" in content
    assert "risk_adjusted_metrics.parquet" in content
    assert "365" in content
    assert "252" in content
    assert "不新增 PASS 阈值" in content
```

In `tests/docs/test_csf_holdout_validation_contract_first_docs.py`, add the same assertions for holdout SOP.

- [ ] **Step 2: Run docs tests and verify failure**

Run:

```bash
python -m pytest tests/docs/test_csf_backtest_ready_contract_first_docs.py tests/docs/test_csf_holdout_validation_contract_first_docs.py -q
```

Expected: fail until docs are updated.

- [ ] **Step 3: Update backtest SOP required outputs and gate language**

In `docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md`, add the five artifacts to “必备输出” and add:

```markdown
路径级风险诊断也是 hard contract。`portfolio_return_series.parquet`、`equity_curve.parquet`、`portfolio_pnl_ledger.parquet`、`asset_pnl_ledger.parquet` 与 `risk_adjusted_metrics.parquet` 必须存在、非空，并能互相复算。

365 天是 crypto 永续主口径；252 天是传统交易日参考口径。Sharpe、Sortino、Calmar、profit factor 必须可由 formal return / PnL 序列复算，但它们不新增 PASS 阈值。Backtest 的机器 hard gate 仍然是正式成本后收益为正，以及路径级产物真实一致。
```

- [ ] **Step 4: Update holdout SOP required outputs and gate language**

In `docs/sop/main-flow/07_csf_holdout_validation_sop_cn.md`, add the same five artifacts and:

```markdown
Holdout 必须与 backtest 同构输出路径级风险诊断。不能只提供 compare summary，也不能在 holdout 因新增诊断重新选 variant、调 bucket cut、改 neutralization 或改 weight mapping。

365 天是 crypto 永续主口径；252 天是传统交易日参考口径。Sharpe、Sortino、Calmar、profit factor 只要求真实、可复算、口径一致，不新增 PASS 阈值。Holdout 现有 hard gate 仍然是 `direction_match = true` 且 `holdout_mean_net_return > 0`。
```

- [ ] **Step 5: Update skills**

In each listed CSF author/review skill, add one concise rule under artifact contract or review scope:

```markdown
- `portfolio_return_series.parquet`、`equity_curve.parquet`、`portfolio_pnl_ledger.parquet`、`asset_pnl_ledger.parquet`、`risk_adjusted_metrics.parquet` 是 formal hard contract；缺失或无法复算时不得进入 review / 不得放行。
```

For review skills, add:

```markdown
- Sharpe、Sortino、Calmar、profit factor 不新增 PASS 阈值；review 关注它们是否由 formal return / PnL 序列复算一致，以及差表现是否在 gate decision 中被解释。
```

- [ ] **Step 6: Update usage guide**

In `docs/guides/qros-research-session-usage.md`, extend the CSF backtest/holdout gate paragraph:

```markdown
`csf_backtest_ready` 与 `csf_holdout_validation` 还会要求路径级风险诊断产物完整并可复算，包括 return series、equity curve、portfolio PnL ledger、asset PnL ledger 与 risk-adjusted metrics。Sharpe / Calmar / profit factor 不新增机器 PASS 阈值，但缺失或与原始序列不一致会阻断 stage validation。
```

- [ ] **Step 7: Run docs tests**

Run:

```bash
python -m pytest tests/docs/test_csf_backtest_ready_contract_first_docs.py tests/docs/test_csf_holdout_validation_contract_first_docs.py -q
```

Expected: pass.

- [ ] **Step 8: Commit**

```bash
git add docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md docs/sop/main-flow/07_csf_holdout_validation_sop_cn.md docs/guides/qros-research-session-usage.md docs/guides/qros-factor-diagnostics.md skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md skills/csf_holdout_validation/qros-csf-holdout-validation-author/SKILL.md skills/csf_holdout_validation/qros-csf-holdout-validation-review/SKILL.md skills/core/qros-research-session/SKILL.md tests/docs/test_csf_backtest_ready_contract_first_docs.py tests/docs/test_csf_holdout_validation_contract_first_docs.py
git commit -m "docs: document csf path-risk hard contract"
```

---

### Task 7: Integrated Validation

**Files:**
- No code edits expected.

- [ ] **Step 1: Run focused contract and runtime tests**

Run:

```bash
python -m pytest \
  tests/contracts/test_csf_backtest_ready_artifact_contract.py \
  tests/contracts/test_csf_holdout_validation_artifact_contract.py \
  tests/runtime/test_csf_path_risk_contract.py \
  tests/runtime/test_csf_backtest_runtime.py \
  tests/runtime/test_csf_holdout_runtime.py \
  tests/runtime/test_csf_backtest_ready_semantic_validation.py \
  tests/runtime/test_csf_holdout_validation_semantic_validation.py \
  tests/runtime/test_factor_diagnostics.py \
  tests/docs/test_csf_backtest_ready_contract_first_docs.py \
  tests/docs/test_csf_holdout_validation_contract_first_docs.py
```

Expected: all selected tests pass.

- [ ] **Step 2: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: smoke tier passes.

- [ ] **Step 3: Run full-smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: full-smoke tier passes.

- [ ] **Step 4: Inspect git status**

Run:

```bash
git status --short
```

Expected: no uncommitted changes after task commits.

- [ ] **Step 5: Final summary**

Report:

- Contract artifacts added for backtest and holdout.
- Shared path-risk consistency validator added.
- Runtime builders produce new fixture artifacts.
- Diagnostics read formal risk metrics.
- Docs and skills updated.
- Focused tests, smoke, and full-smoke results.
