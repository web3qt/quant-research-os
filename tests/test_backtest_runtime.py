from pathlib import Path

import pytest
import yaml

from tools.backtest_runtime import build_backtest_ready_from_test_evidence, scaffold_backtest_ready


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_fake_parquet(path: Path) -> None:
    path.write_bytes(b"PAR1test-payloadPAR1")


def _prepare_real_backtest_engine_outputs(backtest_dir: Path) -> None:
    formal_dir = backtest_dir / "author" / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)
    (formal_dir / "engine_compare.csv").write_text(
        "\n".join(
            [
                "engine,gross_return,net_return,max_drawdown,semantic_gap",
                "vectorbt,0.12,0.09,-0.08,false",
                "backtrader,0.119,0.089,-0.081,false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for engine_name in ("vectorbt", "backtrader"):
        engine_dir = formal_dir / engine_name
        engine_dir.mkdir(exist_ok=True)
        for name in (
            "trades.parquet",
            "symbol_metrics.parquet",
            "portfolio_timeseries.parquet",
            "portfolio_summary.parquet",
        ):
            _write_fake_parquet(engine_dir / name)


def _backtest_ready_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "execution_policy": {
                "confirmed": confirmed,
                "draft": {
                    "selected_symbols": ["ETHUSDT", "SOLUSDT"],
                    "best_h": "30m",
                    "entry_rule": "Enter on frozen test whitelist continuation signal.",
                    "exit_rule": "Exit at frozen best_h or hard risk stop.",
                    "cost_model_note": "Use formal fee and slippage schedule only.",
                },
                "missing_items": [],
            },
            "portfolio_policy": {
                "confirmed": confirmed,
                "draft": {
                    "position_sizing_rule": "Equal-notional baseline sizing.",
                    "capital_base": "100000 USD",
                    "max_concurrent_positions": "5",
                    "combo_scope_note": "Baseline combo only in first-wave governance stage.",
                },
                "missing_items": [],
            },
            "risk_overlay": {
                "confirmed": confirmed,
                "draft": {
                    "risk_controls": ["kill_switch", "max_turnover_cap"],
                    "stop_or_kill_switch_rule": "Disable new entries under exchange or data anomalies.",
                    "abnormal_performance_sanity_check": "Required if net results look abnormally strong.",
                    "reservation_note": "Capacity assumptions may still need later hardening.",
                },
                "missing_items": [],
            },
            "engine_contract": {
                "confirmed": confirmed,
                "draft": {
                    "required_engines": ["vectorbt", "backtrader"],
                    "semantic_compare_rule": "Both engines must agree on semantic_gap = false.",
                    "repro_rule": "Same frozen config must reproduce stable aggregate results.",
                    "engine_scope_note": "Both engines consume the same frozen whitelist and best_h.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "engine_compare.csv",
                        "vectorbt/",
                        "backtrader/",
                        "strategy_combo_ledger.csv",
                    ],
                    "consumer_stage": "holdout_validation",
                    "frozen_config_note": "Holdout must consume frozen backtest config only.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_test_evidence_stage(lineage_root: Path) -> None:
    test_dir = lineage_root / "05_test_evidence"
    formal_dir = test_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "frozen_spec.json").write_text(
        '{"selected_symbols":["ETHUSDT","SOLUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    (formal_dir / "selected_symbols_test.csv").write_text(
        "\n".join(
            [
                "symbol,param_id,best_h",
                "ETHUSDT,baseline_v1,30m",
                "SOLUSDT,baseline_v1,30m",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_scaffold_backtest_ready_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_test_evidence_stage(lineage_root)

    backtest_dir = scaffold_backtest_ready(lineage_root)

    draft = yaml.safe_load((backtest_dir / "author" / "draft" / "backtest_ready_draft.yaml").read_text(encoding="utf-8"))
    assert backtest_dir == lineage_root / "06_backtest"
    assert set(draft["groups"]) == {
        "execution_policy",
        "portfolio_policy",
        "risk_overlay",
        "engine_contract",
        "delivery_contract",
    }
    assert draft["groups"]["execution_policy"]["draft"]["selected_symbols"] == ["ETHUSDT", "SOLUSDT"]


def test_build_backtest_ready_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_test_evidence_stage(lineage_root)
    backtest_dir = lineage_root / "06_backtest"
    backtest_dir.mkdir(parents=True)
    _write_yaml(backtest_dir / "author" / "draft" / "backtest_ready_draft.yaml", _backtest_ready_draft(confirmed=True))
    _prepare_real_backtest_engine_outputs(backtest_dir)

    built_dir = build_backtest_ready_from_test_evidence(lineage_root)

    assert built_dir == backtest_dir
    formal_dir = backtest_dir / "author" / "formal"
    assert (formal_dir / "engine_compare.csv").exists()
    assert (formal_dir / "vectorbt").exists()
    assert (formal_dir / "backtrader").exists()
    assert (formal_dir / "strategy_combo_ledger.csv").exists()
    assert (formal_dir / "capacity_review.md").exists()
    assert (formal_dir / "backtest_gate_decision.md").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()
    assert (formal_dir / "backtest_frozen_config.json").exists()


def test_build_backtest_ready_rejects_placeholder_engine_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_test_evidence_stage(lineage_root)
    backtest_dir = lineage_root / "06_backtest"
    backtest_dir.mkdir(parents=True)
    _write_yaml(backtest_dir / "author" / "draft" / "backtest_ready_draft.yaml", _backtest_ready_draft(confirmed=True))

    for engine_name in ("vectorbt", "backtrader"):
        engine_dir = backtest_dir / "author" / "formal" / engine_name
        engine_dir.mkdir(parents=True)
        (engine_dir / "trades.parquet").write_text(
            f"placeholder trades artifact for {engine_name}\n",
            encoding="utf-8",
        )
        (engine_dir / "symbol_metrics.parquet").write_text(
            f"placeholder symbol metrics artifact for {engine_name}\n",
            encoding="utf-8",
        )
        (engine_dir / "portfolio_timeseries.parquet").write_text(
            f"placeholder portfolio timeseries artifact for {engine_name}\n",
            encoding="utf-8",
        )
        (engine_dir / "portfolio_summary.parquet").write_text(
            f"placeholder portfolio summary artifact for {engine_name}\n",
            encoding="utf-8",
        )
    (backtest_dir / "author" / "formal" / "engine_compare.csv").write_text(
        "engine_a,engine_b,semantic_gap,note\nvectorbt,backtrader,false,placeholder\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="real dual-engine backtest outputs"):
        build_backtest_ready_from_test_evidence(lineage_root)
