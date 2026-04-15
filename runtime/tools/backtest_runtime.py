from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


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
    layout = ensure_stage_author_layout(backtest_dir)

    draft_path = layout["author_draft_dir"] / BACKTEST_READY_DRAFT_FILE
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
    test_formal_dir = ensure_stage_author_layout(test_dir)["author_formal_dir"]
    backtest_layout = ensure_stage_author_layout(backtest_dir)
    backtest_formal_dir = backtest_layout["author_formal_dir"]

    missing_inputs: list[str] = []
    for path in [
        test_formal_dir / "frozen_spec.json",
        test_formal_dir / "selected_symbols_test.csv",
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

    (backtest_formal_dir / "backtest_frozen_config.json").write_text(
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

    with (backtest_formal_dir / "strategy_combo_ledger.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["combo_id", "execution_rule", "portfolio_rule", "risk_overlay", "status"])
        writer.writerow(["baseline_combo_v1", entry_rule, position_sizing_rule, stop_or_kill_switch_rule, "selected"])

    (backtest_formal_dir / "selected_strategy_combo.json").write_text(
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

    (backtest_formal_dir / "capacity_review.md").write_text(
        "\n".join(
            [
                "# Capacity Review",
                "",
                f"- 资本基数: {capital_base}",
                f"- 成本模型说明: {cost_model_note}",
                f"- 容量瓶颈说明: {combo_scope_note}",
                f"- 风险保留项说明: {reservation_note}",
                f"- 异常表现核查: {abnormal_performance_sanity_check}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (backtest_formal_dir / "backtest_gate_decision.md").write_text(
        "\n".join(
            [
                "# Backtest Gate Decision",
                "",
                "- 在 review findings 和 review closure 写出之前，formal gate 决策仍保持 pending。",
                f"- 已选 symbols: {', '.join(selected_symbols)}",
                f"- 已冻结 best_h: {best_h}",
                f"- 必需引擎: {', '.join(required_engines)}",
                f"- 下游消费阶段: {consumer_stage}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (backtest_formal_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# 产物清单",
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

    (backtest_formal_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `selected_symbols`: backtest 消费的冻结 whitelist，当前为 {selected_symbols}。",
                f"- `best_h`: 来自 test_evidence 的冻结持有窗口，当前为 `{best_h}`。",
                f"- `entry_rule`: 执行入场规则，当前为 `{entry_rule}`。",
                f"- `exit_rule`: 执行出场规则，当前为 `{exit_rule}`。",
                f"- `position_sizing_rule`: 组合仓位规则，当前为 `{position_sizing_rule}`。",
                f"- `risk_controls`: 风险覆盖控制，当前为 {risk_controls}。",
                f"- `required_engines`: formal 验证要求的引擎集合，当前为 {required_engines}。",
                f"- `machine_artifacts`: 本阶段正式机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    _require_real_dual_engine_backtest_outputs(backtest_dir)

    return backtest_dir


def backtest_ready_real_outputs_complete(backtest_dir: Path) -> bool:
    formal_dir = ensure_stage_author_layout(backtest_dir)["author_formal_dir"]
    compare_path = formal_dir / "engine_compare.csv"
    if not compare_path.exists() or _engine_compare_is_placeholder(compare_path):
        return False

    for engine_name in ("vectorbt", "backtrader"):
        engine_dir = formal_dir / engine_name
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
    frozen_spec_path = lineage_root / "05_test_evidence" / "author" / "formal" / "frozen_spec.json"
    selected_symbols_path = lineage_root / "05_test_evidence" / "author" / "formal" / "selected_symbols_test.csv"
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
    draft_path = ensure_stage_author_layout(backtest_dir)["author_draft_dir"] / BACKTEST_READY_DRAFT_FILE
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
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
