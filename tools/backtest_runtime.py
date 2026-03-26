from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml


BACKTEST_READY_DRAFT_FILE = "backtest_ready_draft.yaml"
BACKTEST_READY_GROUP_ORDER = [
    "execution_policy",
    "portfolio_policy",
    "risk_overlay",
    "engine_contract",
    "delivery_contract",
]
BACKTEST_ENGINE_REQUIRED_FILES = (
    "trades.parquet",
    "symbol_metrics.parquet",
    "portfolio_timeseries.parquet",
    "portfolio_summary.parquet",
)


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_backtest_ready_draft(
    *,
    selected_symbols: list[str] | None = None,
    best_h: str = "",
) -> dict[str, Any]:
    symbols = selected_symbols or []
    return {
        "groups": {
            "execution_policy": {
                "confirmed": False,
                "draft": {
                    "selected_symbols": symbols,
                    "best_h": best_h,
                    "entry_rule": "",
                    "exit_rule": "",
                    "cost_model_note": "",
                },
                "missing_items": [],
            },
            "portfolio_policy": {
                "confirmed": False,
                "draft": {
                    "position_sizing_rule": "",
                    "capital_base": "",
                    "max_concurrent_positions": "",
                    "combo_scope_note": "",
                },
                "missing_items": [],
            },
            "risk_overlay": {
                "confirmed": False,
                "draft": {
                    "risk_controls": [],
                    "stop_or_kill_switch_rule": "",
                    "abnormal_performance_sanity_check": "",
                    "reservation_note": "",
                },
                "missing_items": [],
            },
            "engine_contract": {
                "confirmed": False,
                "draft": {
                    "required_engines": ["vectorbt", "backtrader"],
                    "semantic_compare_rule": "",
                    "repro_rule": "",
                    "engine_scope_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [
                        "engine_compare.csv",
                        "vectorbt/",
                        "backtrader/",
                        "strategy_combo_ledger.csv",
                    ],
                    "consumer_stage": "holdout_validation",
                    "frozen_config_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_backtest_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    backtest_dir = lineage_root / "06_backtest"
    backtest_dir.mkdir(parents=True, exist_ok=True)

    draft_path = backtest_dir / BACKTEST_READY_DRAFT_FILE
    if not draft_path.exists():
        symbols, best_h = _load_test_selection(lineage_root)
        _dump_yaml(
            draft_path,
            _blank_backtest_ready_draft(selected_symbols=symbols, best_h=best_h),
        )
    return backtest_dir


def build_backtest_ready_from_test_evidence(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    test_dir = lineage_root / "05_test_evidence"
    backtest_dir = scaffold_backtest_ready(lineage_root)

    missing_inputs: list[str] = []
    for path in [
        test_dir / "frozen_spec.json",
        test_dir / "selected_symbols_test.csv",
    ]:
        if not path.exists():
            missing_inputs.append(str(path.relative_to(lineage_root)))
    if missing_inputs:
        raise ValueError(
            "test_evidence artifacts missing before backtest_ready build: " + ", ".join(missing_inputs)
        )

    freeze_groups = _require_confirmed_freeze_groups(backtest_dir)
    execution_policy = freeze_groups["execution_policy"]["draft"]
    portfolio_policy = freeze_groups["portfolio_policy"]["draft"]
    risk_overlay = freeze_groups["risk_overlay"]["draft"]
    engine_contract = freeze_groups["engine_contract"]["draft"]
    delivery_contract = freeze_groups["delivery_contract"]["draft"]

    selected_symbols = _string_list(execution_policy.get("selected_symbols", []))
    best_h = _required_draft_value(execution_policy, "best_h")
    entry_rule = _required_draft_value(execution_policy, "entry_rule")
    exit_rule = _required_draft_value(execution_policy, "exit_rule")
    cost_model_note = _required_draft_value(execution_policy, "cost_model_note")

    position_sizing_rule = _required_draft_value(portfolio_policy, "position_sizing_rule")
    capital_base = _required_draft_value(portfolio_policy, "capital_base")
    max_concurrent_positions = _required_draft_value(portfolio_policy, "max_concurrent_positions")
    combo_scope_note = _required_draft_value(portfolio_policy, "combo_scope_note")

    risk_controls = _string_list(risk_overlay.get("risk_controls", []))
    stop_or_kill_switch_rule = _required_draft_value(risk_overlay, "stop_or_kill_switch_rule")
    abnormal_performance_sanity_check = _required_draft_value(
        risk_overlay, "abnormal_performance_sanity_check"
    )
    reservation_note = _required_draft_value(risk_overlay, "reservation_note")

    required_engines = _string_list(engine_contract.get("required_engines", []))
    semantic_compare_rule = _required_draft_value(engine_contract, "semantic_compare_rule")
    repro_rule = _required_draft_value(engine_contract, "repro_rule")
    engine_scope_note = _required_draft_value(engine_contract, "engine_scope_note")

    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_config_note = _required_draft_value(delivery_contract, "frozen_config_note")

    upstream_symbols, upstream_best_h = _load_test_selection(lineage_root)
    if not selected_symbols:
        selected_symbols = list(upstream_symbols)
    unknown_symbols = sorted(set(selected_symbols) - set(upstream_symbols))
    if unknown_symbols:
        raise ValueError(
            "selected_symbols must be drawn from test_evidence whitelist: " + ", ".join(unknown_symbols)
        )
    if upstream_best_h and best_h != upstream_best_h:
        raise ValueError("best_h must match the frozen test_evidence best_h")

    (backtest_dir / "backtest_frozen_config.json").write_text(
        json.dumps(
            {
                "stage": "backtest_ready",
                "lineage_id": lineage_root.name,
                "source_stage": "test_evidence",
                "selected_symbols": selected_symbols,
                "best_h": best_h,
                "entry_rule": entry_rule,
                "exit_rule": exit_rule,
                "cost_model_note": cost_model_note,
                "position_sizing_rule": position_sizing_rule,
                "capital_base": capital_base,
                "max_concurrent_positions": max_concurrent_positions,
                "risk_controls": risk_controls,
                "stop_or_kill_switch_rule": stop_or_kill_switch_rule,
                "required_engines": required_engines,
                "semantic_compare_rule": semantic_compare_rule,
                "consumer_stage": consumer_stage,
                "frozen_config_note": frozen_config_note,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    with (backtest_dir / "strategy_combo_ledger.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["combo_id", "execution_rule", "portfolio_rule", "risk_overlay", "status"])
        writer.writerow(["baseline_combo_v1", entry_rule, position_sizing_rule, stop_or_kill_switch_rule, "selected"])

    (backtest_dir / "selected_strategy_combo.json").write_text(
        json.dumps(
            {
                "combo_id": "baseline_combo_v1",
                "selected_symbols": selected_symbols,
                "best_h": best_h,
                "entry_rule": entry_rule,
                "exit_rule": exit_rule,
                "position_sizing_rule": position_sizing_rule,
                "risk_controls": risk_controls,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    (backtest_dir / "capacity_review.md").write_text(
        "\n".join(
            [
                "# Capacity Review",
                "",
                f"- Capital base: {capital_base}",
                f"- Cost model note: {cost_model_note}",
                f"- Capacity bottleneck note: {combo_scope_note}",
                f"- Risk reservation note: {reservation_note}",
                f"- Abnormal performance sanity check: {abnormal_performance_sanity_check}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (backtest_dir / "backtest_gate_decision.md").write_text(
        "\n".join(
            [
                "# Backtest Gate Decision",
                "",
                "- Formal gate decision remains pending until review findings and review closure are written.",
                f"- Selected symbols: {', '.join(selected_symbols)}",
                f"- Frozen best_h: {best_h}",
                f"- Engines required: {', '.join(required_engines)}",
                f"- Next consumer stage: {consumer_stage}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (backtest_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# Artifact Catalog",
                "",
                "- backtest_frozen_config.json",
                "- engine_compare.csv",
                "- strategy_combo_ledger.csv",
                "- selected_strategy_combo.json",
                "- vectorbt/",
                "- backtrader/",
                "- capacity_review.md",
                "- backtest_gate_decision.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (backtest_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# Field Dictionary",
                "",
                f"- `selected_symbols`: frozen whitelist consumed by backtest, currently {selected_symbols}.",
                f"- `best_h`: frozen horizon from test_evidence, currently `{best_h}`.",
                f"- `entry_rule`: execution entry rule, currently `{entry_rule}`.",
                f"- `exit_rule`: execution exit rule, currently `{exit_rule}`.",
                f"- `position_sizing_rule`: portfolio sizing rule, currently `{position_sizing_rule}`.",
                f"- `risk_controls`: risk overlay controls, currently {risk_controls}.",
                f"- `required_engines`: formal engines required for verification, currently {required_engines}.",
                f"- `machine_artifacts`: formal machine outputs from this stage, currently {machine_artifacts}.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    _require_real_dual_engine_backtest_outputs(backtest_dir)

    return backtest_dir


def backtest_ready_real_outputs_complete(backtest_dir: Path) -> bool:
    compare_path = backtest_dir / "engine_compare.csv"
    if not compare_path.exists() or _engine_compare_is_placeholder(compare_path):
        return False

    for engine_name in ("vectorbt", "backtrader"):
        engine_dir = backtest_dir / engine_name
        if not _engine_dir_has_real_outputs(engine_dir):
            return False
    return True


def _require_real_dual_engine_backtest_outputs(backtest_dir: Path) -> None:
    if backtest_ready_real_outputs_complete(backtest_dir):
        return
    raise ValueError(
        "real dual-engine backtest outputs are missing or placeholder; "
        "prepare vectorbt/backtrader results plus a real engine_compare.csv in the active research repo before freezing backtest_ready"
    )


def _engine_dir_has_real_outputs(engine_dir: Path) -> bool:
    if not engine_dir.exists() or not engine_dir.is_dir():
        return False
    for name in BACKTEST_ENGINE_REQUIRED_FILES:
        artifact_path = engine_dir / name
        if not artifact_path.exists() or not _is_real_parquet_artifact(artifact_path):
            return False
    return True


def _is_real_parquet_artifact(path: Path) -> bool:
    try:
        payload = path.read_bytes()
    except OSError:
        return False
    if len(payload) < 8:
        return False
    if payload[:4] != b"PAR1" or payload[-4:] != b"PAR1":
        return False
    return True


def _engine_compare_is_placeholder(path: Path) -> bool:
    try:
        rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    except (OSError, UnicodeDecodeError):
        return True
    if len(rows) < 2:
        return True
    header = rows[0]
    data_rows = rows[1:]
    if header == ["engine_a", "engine_b", "semantic_gap", "note"] and len(data_rows) == 1:
        row = data_rows[0]
        if len(row) >= 4 and row[0] == "vectorbt" and row[1] == "backtrader" and row[2] == "false":
            return True
    return False


def _load_test_selection(lineage_root: Path) -> tuple[list[str], str]:
    frozen_spec_path = lineage_root / "05_test_evidence" / "frozen_spec.json"
    selected_symbols_path = lineage_root / "05_test_evidence" / "selected_symbols_test.csv"
    best_h = ""
    selected_symbols: list[str] = []

    if frozen_spec_path.exists():
        try:
            payload = json.loads(frozen_spec_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        best_h = str(payload.get("best_h", "")).strip()
        selected_symbols = _string_list(payload.get("selected_symbols", []))

    if not selected_symbols and selected_symbols_path.exists():
        rows = selected_symbols_path.read_text(encoding="utf-8").splitlines()
        for row in rows[1:]:
            parts = row.split(",")
            if parts and parts[0].strip():
                selected_symbols.append(parts[0].strip())
        selected_symbols = sorted(set(selected_symbols))

    return selected_symbols, best_h


def _require_confirmed_freeze_groups(backtest_dir: Path) -> dict[str, Any]:
    payload = yaml.safe_load((backtest_dir / BACKTEST_READY_DRAFT_FILE).read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [name for name in BACKTEST_READY_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"backtest_ready draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"backtest_ready draft missing required value: {key}")
    return value


def _string_list(values: list[Any]) -> list[str]:
    return [str(item).strip() for item in values if str(item).strip()]
