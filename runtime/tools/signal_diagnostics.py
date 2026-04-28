from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
METRIC_LIBRARY_PATH = ROOT / "contracts" / "diagnostics" / "tss_metric_library.yaml"
STAGE_PROFILES_PATH = ROOT / "contracts" / "diagnostics" / "tss_stage_diagnostic_profiles.yaml"

STAGE_DIRS: dict[str, str] = {
    "tss_data_ready": "02_tss_data_ready",
    "tss_signal_ready": "03_tss_signal_ready",
    "tss_train_freeze": "04_tss_train_freeze",
    "tss_test_evidence": "05_tss_test_evidence",
    "tss_backtest_ready": "06_tss_backtest_ready",
    "tss_holdout_validation": "07_tss_holdout_validation",
}


class SignalDiagnosticsError(RuntimeError):
    pass


@dataclass(frozen=True)
class ObservedMetric:
    metric_id: str
    value: object
    status: str
    source: str
    severity: str
    interpretation: str
    strategy_link: str

    def as_dict(self) -> dict[str, object]:
        return {
            "metric_id": self.metric_id,
            "name": self.metric_id,
            "value": self.value,
            "status": self.status,
            "source": self.source,
            "severity": self.severity,
            "interpretation": self.interpretation,
            "explanation": self.interpretation,
            "strategy_link": self.strategy_link,
        }


@dataclass(frozen=True)
class MissingMetric:
    metric_id: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {"metric_id": self.metric_id, "name": self.metric_id, "reason": self.reason}


def latest_lineage_id(outputs_root: Path) -> str:
    if not outputs_root.exists():
        raise SignalDiagnosticsError(f"No QROS outputs directory found: {outputs_root}")
    lineage_dirs = [path for path in outputs_root.iterdir() if path.is_dir()]
    if not lineage_dirs:
        raise SignalDiagnosticsError(f"No QROS lineage directories found under: {outputs_root}")
    latest = max(lineage_dirs, key=lambda path: (_latest_mtime(path), path.name))
    return latest.name


def diagnostics_payload(
    *,
    outputs_root: Path,
    lineage_id: str | None = None,
    stage: str | None = None,
) -> dict[str, object]:
    profiles = _load_yaml(STAGE_PROFILES_PATH)["profiles"]
    _load_yaml(METRIC_LIBRARY_PATH)["metrics"]

    selection_mode = "explicit" if lineage_id else "latest"
    selected_lineage_id = lineage_id or latest_lineage_id(outputs_root)
    lineage_root = outputs_root / selected_lineage_id
    if not lineage_root.exists() or not lineage_root.is_dir():
        raise SignalDiagnosticsError(f"QROS lineage not found: {lineage_root}")

    selected_stage = stage or _infer_stage(lineage_root)
    if selected_stage not in profiles or selected_stage not in STAGE_DIRS:
        raise SignalDiagnosticsError(f"Unsupported diagnostics stage: {selected_stage}")

    stage_formal_dir = lineage_root / STAGE_DIRS[selected_stage] / "author" / "formal"
    if not stage_formal_dir.exists():
        raise SignalDiagnosticsError(
            f"No TSS formal artifacts found for lineage {selected_lineage_id} stage {selected_stage}: "
            f"{stage_formal_dir}"
        )

    dimensions: list[dict[str, object]] = []
    observed_flat: list[dict[str, object]] = []
    missing_flat: list[dict[str, object]] = []
    evidence_gaps: list[str] = []
    for dimension_name, dimension in profiles[selected_stage]["health_dimensions"].items():
        metric_ids = [
            *dimension.get("required_metrics", []),
            *dimension.get("recommended_metrics", []),
        ]
        observed_metrics: list[dict[str, object]] = []
        missing_metrics: list[dict[str, object]] = []
        for metric_id in metric_ids:
            result = _observe_metric(selected_stage, metric_id, stage_formal_dir)
            if isinstance(result, ObservedMetric):
                metric = result.as_dict()
                observed_metrics.append(metric)
                observed_flat.append(metric)
            else:
                metric = result.as_dict()
                missing_metrics.append(metric)
                missing_flat.append(metric)
                evidence_gaps.append(result.reason)
        dimensions.append(
            {
                "name": dimension_name,
                "health": _dimension_health(observed_metrics, missing_metrics),
                "observed_metrics": observed_metrics,
                "missing_metrics": missing_metrics,
                "risk_notes": _risk_notes(observed_metrics, missing_metrics),
            }
        )

    return {
        "schema_id": "qros-signal-diagnostics-report-v1",
        "lineage_id": selected_lineage_id,
        "lineage_root": str(lineage_root),
        "selection_mode": selection_mode,
        "stage": selected_stage,
        "stage_formal_dir": str(stage_formal_dir),
        "route": "time_series_signal",
        "health": _overall_health(len(observed_flat), len(missing_flat)),
        "confidence": _confidence(len(observed_flat), len(missing_flat)),
        "formal_verdict_boundary": "diagnostics_only_not_review",
        "is_review_verdict": False,
        "metric_library_schema": "tss-metric-library-v1",
        "summary": _summary(selected_stage, observed_flat, missing_flat),
        "observed_metrics": observed_flat,
        "missing_metrics": missing_flat,
        "dimensions": dimensions,
        "evidence_gaps": sorted(set(evidence_gaps)),
        "next_diagnostics": _next_diagnostics(dimensions),
    }


def _latest_mtime(path: Path) -> float:
    latest = path.stat().st_mtime
    for child in path.rglob("*"):
        latest = max(latest, child.stat().st_mtime)
    return latest


def _infer_stage(lineage_root: Path) -> str:
    for stage, stage_dir in reversed(STAGE_DIRS.items()):
        if (lineage_root / stage_dir / "author" / "formal").exists():
            return stage
    raise SignalDiagnosticsError(
        f"No TSS formal artifacts found for lineage {lineage_root.name}. "
        "Run qros-progress to confirm current stage, or pass --stage explicitly."
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SignalDiagnosticsError(f"{path}: yaml read failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise SignalDiagnosticsError(f"{path}: expected yaml map")
    return payload


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _read_yaml_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def _read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        import pyarrow.parquet as pq

        return pq.read_table(path).to_pylist()
    except Exception:
        return []


def _observe_metric(stage: str, metric_id: str, formal_dir: Path) -> ObservedMetric | MissingMetric:
    observer = _METRIC_OBSERVERS.get(stage, {}).get(metric_id)
    if observer is None:
        return MissingMetric(metric_id, f"{metric_id}: no V1 observer for {stage}")
    return observer(formal_dir)


def _missing(metric_id: str, reason: str) -> MissingMetric:
    return MissingMetric(metric_id, f"{metric_id}: {reason}")


def _observed(metric_id: str, value: object, source: str) -> ObservedMetric:
    interpretation = _interpret_metric(metric_id, value)
    return ObservedMetric(
        metric_id=metric_id,
        value=value,
        status="observed",
        source=source,
        severity=interpretation["severity"],
        interpretation=interpretation["interpretation"],
        strategy_link=interpretation["strategy_link"],
    )


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _pct(value: float) -> str:
    return f"{value:.2%}"


def _interpret_metric(metric_id: str, value: object) -> dict[str, str]:
    numeric = _as_float(value)

    if metric_id == "mean_rank_ic":
        if numeric is None:
            return _plain_interpretation(metric_id)
        if numeric < 0:
            return {
                "severity": "watch",
                "interpretation": (
                    f"mean_rank_ic < 0（{numeric:.4f}），对 TSS 表示信号方向可能反了 / "
                    "当前窗口预测关系为负；高信号后续收益排序反而偏弱。"
                ),
                "strategy_link": (
                    "如果策略按高信号做多，则可能系统性站错方向；需要优先检查信号方向、标签方向、"
                    "持有窗口和是否应该反向使用该信号。"
                ),
            }
        if numeric > 0:
            return {
                "severity": "info",
                "interpretation": (
                    f"mean_rank_ic 为正（{numeric:.4f}），表示当前窗口中信号排序与未来收益排序大体同向。"
                ),
                "strategy_link": "如果策略按高信号做多，方向和冻结假设基本一致，但仍要结合 forward return、成本和 holdout。",
            }
        return {
            "severity": "watch",
            "interpretation": "mean_rank_ic 接近 0，表示当前窗口里信号排序预测关系很弱，可能接近噪声。",
            "strategy_link": "不要只凭这个信号做方向判断，应检查事件数量、forward return、base rate uplift 和 holdout 延续性。",
        }

    if metric_id == "mean_forward_return" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": (
                f"平均 forward return 为 {_pct(numeric)}，表示信号触发后目标持有窗口的平均后续收益。"
            ),
            "strategy_link": (
                "如果策略按高信号做多，forward return 为正才更接近策略假设；为负时要怀疑方向、持有期或交易过滤。"
            ),
        }

    if metric_id == "hit_rate" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0.5 else "info",
            "interpretation": (
                f"命中率为 {_pct(numeric)}，表示信号触发后方向判断正确的事件比例；"
                "高于 50% 只是略优于随机方向，还要结合 base rate 和成本后表现。"
            ),
            "strategy_link": "如果信号频率很低或事件数量很少，命中率本身不足以说明策略可交易。",
        }

    if metric_id == "base_rate_uplift" and numeric is not None:
        return {
            "severity": "watch" if numeric <= 0 else "info",
            "interpretation": f"base rate uplift 为 {_pct(numeric)}，表示信号命中率相对无信号基准的提升。",
            "strategy_link": "uplift 为正说明信号可能提供增量方向信息；为负则说明触发信号后反而弱于基准。",
        }

    if metric_id == "signal_frequency" and numeric is not None:
        severity = "watch" if numeric < 0.01 or numeric > 0.5 else "info"
        return {
            "severity": severity,
            "interpretation": f"信号触发频率为 {_pct(numeric)}，反映信号在样本中的稀疏程度。",
            "strategy_link": "过低会导致样本和成交机会不足；过高可能接近长期持仓，需要和换手、成本、容量一起看。",
        }

    if metric_id in {"event_count", "signal_event_count", "parameter_count"} and numeric is not None:
        return {
            "severity": "watch" if numeric < 30 else "info",
            "interpretation": f"{metric_id} 为 {numeric:.0f}，反映当前诊断样本或搜索面的数量厚度。",
            "strategy_link": "数量太少时，均值收益、命中率和 Rank IC 更容易被少数事件主导。",
        }

    if metric_id == "mfe_mae" and numeric is not None:
        return {
            "severity": "watch" if numeric <= 1 else "info",
            "interpretation": f"MFE / MAE 为 {numeric:.4f}，衡量有利波动相对不利波动是否占优。",
            "strategy_link": "如果该值偏低，即使最终 forward return 为正，入场后的路径风险也可能较差。",
        }

    if metric_id == "mean_gross_return" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"组合扣成本前平均收益为 {_pct(numeric)}，反映 TSS 信号的原始收益能力。",
            "strategy_link": "如果 gross 为正但 net 变弱，主要风险通常来自换手、滑点、手续费或容量。",
        }

    if metric_id in {"mean_net_return", "holdout_mean_net_return"} and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"扣成本后平均收益为 {_pct(numeric)}，这是更接近真实可交易表现的收益口径。",
            "strategy_link": "如果扣成本后收益转负，说明信号收益可能被交易成本或执行约束吃掉。",
        }

    if metric_id == "gross_net_erosion" and numeric is not None:
        return {
            "severity": "watch" if numeric > 0 else "info",
            "interpretation": f"gross 到 net 的成本侵蚀约为 {_pct(numeric)}。",
            "strategy_link": "成本侵蚀越大，越需要降低换手、延长持有期、收紧交易过滤或重新评估可交易性。",
        }

    if metric_id == "max_drawdown" and numeric is not None:
        return {
            "severity": "watch" if abs(numeric) > 0.1 else "info",
            "interpretation": f"最大回撤约为 {_pct(abs(numeric))}，表示 TSS 组合曲线历史最深账面回撤。",
            "strategy_link": "回撤越深，对仓位、止损、风险预算和组合层风控的要求越高。",
        }

    if metric_id == "turnover" and numeric is not None:
        return {
            "severity": "watch" if numeric > 0.5 else "info",
            "interpretation": f"平均换手率约为 {_pct(numeric)}，表示策略调仓和交易强度。",
            "strategy_link": "高换手会放大手续费、滑点和冲击成本；需要和 net return、gross/net erosion 一起看。",
        }

    if metric_id == "capacity_utilization" and numeric is not None:
        return {
            "severity": "watch" if numeric > 0.8 else "info",
            "interpretation": f"容量使用率约为 {_pct(numeric)}，表示当前交易规模相对可承载容量的压力。",
            "strategy_link": "容量使用率越高，越容易出现成交冲击；如果同时 net return 较弱，策略规模可能需要下调。",
        }

    if metric_id == "direction_match":
        if value is False:
            return {
                "severity": "watch",
                "interpretation": "holdout 方向不匹配，表示样本外信号方向与 test / backtest 阶段冻结预期相反。",
                "strategy_link": "这通常是高优先级风险信号，需要检查信号方向、市场状态变化和是否存在过拟合。",
            }
        return {
            "severity": "info",
            "interpretation": "holdout 方向匹配，表示样本外方向与冻结预期一致。",
            "strategy_link": "方向一致只是必要条件，还要继续看收益退化、回撤变化和事件稳定性。",
        }

    if metric_id == "holdout_mean_forward_return" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"holdout 平均 forward return 为 {_pct(numeric)}，表示样本外信号触发后的后续收益。",
            "strategy_link": "如果 holdout forward return 明显弱于 test，需要警惕样本内过拟合或市场状态变化。",
        }

    if metric_id == "holdout_hit_rate" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0.5 else "info",
            "interpretation": f"holdout 命中率为 {_pct(numeric)}，表示样本外方向判断正确的事件比例。",
            "strategy_link": "样本外命中率低于 test 时，需要检查信号是否只在训练/测试窗口有效。",
        }

    if metric_id == "net_return_delta" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"holdout 相对 backtest 的净收益变化为 {_pct(numeric)}。",
            "strategy_link": "负数表示样本外收益退化；需要结合 forward return、成本侵蚀和市场状态判断来源。",
        }

    if metric_id == "drawdown_delta" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"holdout 相对 backtest 的回撤变化为 {_pct(numeric)}。",
            "strategy_link": "负数通常表示样本外回撤加深，需要检查是否有市场状态切换或组合风险暴露扩大。",
        }

    if metric_id in {"time_index_coverage", "signal_non_null_ratio", "quality_flag_rate"} and numeric is not None:
        return {
            "severity": "watch" if numeric < 0.8 else "info",
            "interpretation": f"{metric_id} 为 {_pct(numeric)}，反映时间索引、信号字段或质量标记的有效覆盖程度。",
            "strategy_link": "覆盖不足会让 TSS evidence 更容易被少数资产、少数时间段或缺失处理方式主导。",
        }

    if metric_id == "asset_count" and numeric is not None:
        return {
            "severity": "watch" if numeric < 5 else "info",
            "interpretation": f"asset_count 为 {numeric:.0f}，反映 TSS 样本中资产数量。",
            "strategy_link": "资产数量过少时，信号表现可能高度依赖单一标的状态，holdout 稳定性更重要。",
        }

    return _plain_interpretation(metric_id)


def _plain_interpretation(metric_id: str) -> dict[str, str]:
    return {
        "severity": "info",
        "interpretation": f"{metric_id} 已观测到，可作为当前 TSS 阶段质量诊断证据之一。",
        "strategy_link": "需要和同阶段其他 diagnostics 一起看；单个指标不构成 review verdict 或 gate verdict。",
    }


def _numeric_values(rows: list[dict[str, Any]], column: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(column)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        values.append(float(value))
    return values


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _value_from_json(path: Path, metric_id: str, key: str, source: str) -> ObservedMetric | MissingMetric:
    payload = _read_json(path)
    if payload is None:
        return _missing(metric_id, f"missing or unreadable {path.name}")
    if key not in payload:
        return _missing(metric_id, f"{path.name} lacks {key}")
    return _observed(metric_id, payload[key], source)


def _value_from_yaml(path: Path, metric_id: str, key: str, source: str) -> ObservedMetric | MissingMetric:
    payload = _read_yaml_optional(path)
    if payload is None:
        return _missing(metric_id, f"missing or unreadable {path.name}")
    if key not in payload:
        return _missing(metric_id, f"{path.name} lacks {key}")
    return _observed(metric_id, payload[key], source)


def _mean_from_parquet(path: Path, metric_id: str, column: str, source: str) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(path)
    values = _numeric_values(rows, column)
    value = _mean(values)
    if value is None:
        return _missing(metric_id, f"{path.name} lacks numeric {column}")
    return _observed(metric_id, value, source)


def _exists_metric(formal_dir: Path, metric_id: str, rel_path: str) -> ObservedMetric | MissingMetric:
    path = formal_dir / rel_path
    if path.exists():
        return _observed(metric_id, "present", rel_path)
    return _missing(metric_id, f"missing {rel_path}")


def _count_csv_rows(formal_dir: Path, metric_id: str, rel_path: str) -> ObservedMetric | MissingMetric:
    rows = _read_csv_rows(formal_dir / rel_path)
    if rows:
        return _observed(metric_id, len(rows), rel_path)
    return _missing(metric_id, f"missing {rel_path} rows")


def _count_parquet_rows(formal_dir: Path, metric_id: str, rel_path: str) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(formal_dir / rel_path)
    if rows:
        return _observed(metric_id, len(rows), rel_path)
    return _missing(metric_id, f"missing or empty {rel_path}")


def _time_index_coverage(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_json(
        formal_dir / "time_index_manifest.json",
        "time_index_coverage",
        "coverage_ratio",
        "time_index_manifest.json.coverage_ratio",
    )


def _asset_count(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(formal_dir / "asset_time_index.parquet")
    assets = {str(row.get("asset_id")) for row in rows if row.get("asset_id") is not None}
    if assets:
        return _observed("asset_count", len(assets), "asset_time_index.parquet.asset_id")
    return _missing("asset_count", "asset_time_index.parquet lacks asset_id values")


def _split_sample_adequacy(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_yaml(
        formal_dir / "split_sample_adequacy_report.yaml",
        "split_sample_adequacy",
        "final_verdict",
        "split_sample_adequacy_report.yaml.final_verdict",
    )


def _quality_flag_rate(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "quality_flags.parquet",
        "quality_flag_rate",
        "flag_rate",
        "quality_flags.parquet.flag_rate",
    )


def _signal_non_null_ratio(formal_dir: Path) -> ObservedMetric | MissingMetric:
    manifest = _read_yaml_optional(formal_dir / "signal_manifest.yaml")
    if manifest is None:
        return _missing("signal_non_null_ratio", "missing signal_manifest.yaml")
    signal_field = str(manifest.get("final_signal_field", "")).strip()
    if not signal_field:
        return _missing("signal_non_null_ratio", "signal_manifest.yaml lacks final_signal_field")
    rows = _read_parquet_rows(formal_dir / "signal_panel.parquet")
    if not rows:
        return _missing("signal_non_null_ratio", "missing or empty signal_panel.parquet")
    non_null = sum(1 for row in rows if row.get(signal_field) is not None)
    return _observed("signal_non_null_ratio", non_null / len(rows), f"signal_panel.parquet.{signal_field}")


def _route_inheritance(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _exists_metric(formal_dir, "route_inheritance", "route_inheritance_contract.yaml")


def _reject_reason_completeness(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_csv_rows(formal_dir / "train_variant_rejects.csv")
    if rows and all(str(row.get("reject_reason", "")).strip() for row in rows):
        return _observed("reject_reason_completeness", "complete", "train_variant_rejects.csv.reject_reason")
    return _missing("reject_reason_completeness", "missing reject_reason rows")


def _train_quality_score(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_yaml(
        formal_dir / "tss_train_freeze.yaml",
        "train_quality_score",
        "train_quality_score",
        "tss_train_freeze.yaml.train_quality_score",
    )


def _summary_value(metric_id: str, key: str) -> Any:
    def observe(formal_dir: Path) -> ObservedMetric | MissingMetric:
        return _value_from_json(
            formal_dir / "signal_performance_summary.json",
            metric_id,
            key,
            f"signal_performance_summary.json.{key}",
        )

    return observe


def _mfe_mae(formal_dir: Path) -> ObservedMetric | MissingMetric:
    payload = _read_json(formal_dir / "signal_performance_summary.json")
    if payload and "mfe_mae" in payload:
        return _observed("mfe_mae", payload["mfe_mae"], "signal_performance_summary.json.mfe_mae")
    rows = _read_parquet_rows(formal_dir / "event_forward_return.parquet")
    mfe = _mean(_numeric_values(rows, "mfe"))
    mae_values = [abs(value) for value in _numeric_values(rows, "mae")]
    mae = _mean(mae_values)
    if mfe is None or mae in {None, 0}:
        return _missing("mfe_mae", "signal_performance_summary.json lacks mfe_mae and event_forward_return.parquet lacks mfe/mae")
    return _observed("mfe_mae", mfe / mae, "event_forward_return.parquet.mfe_mae")


def _mean_gross_return(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "portfolio_summary.parquet",
        "mean_gross_return",
        "mean_gross_return",
        "portfolio_summary.parquet.mean_gross_return",
    )


def _mean_net_return(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "portfolio_summary.parquet",
        "mean_net_return",
        "mean_net_return",
        "portfolio_summary.parquet.mean_net_return",
    )


def _gross_net_erosion(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(formal_dir / "portfolio_summary.parquet")
    gross = _mean(_numeric_values(rows, "mean_gross_return"))
    net = _mean(_numeric_values(rows, "mean_net_return"))
    if gross is None or net is None:
        return _missing("gross_net_erosion", "portfolio_summary.parquet lacks gross or net return")
    return _observed("gross_net_erosion", gross - net, "portfolio_summary.parquet.gross_minus_net")


def _max_drawdown(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "portfolio_summary.parquet",
        "max_drawdown",
        "max_drawdown",
        "portfolio_summary.parquet.max_drawdown",
    )


def _turnover(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "turnover_capacity_report.parquet",
        "turnover",
        "turnover",
        "turnover_capacity_report.parquet.turnover",
    )


def _capacity_utilization(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "turnover_capacity_report.parquet",
        "capacity_utilization",
        "capacity_utilization",
        "turnover_capacity_report.parquet.capacity_utilization",
    )


def _direction_match(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(formal_dir / "holdout_event_compare.parquet")
    if not rows:
        return _missing("direction_match", "missing holdout_event_compare.parquet")
    return _observed(
        "direction_match",
        all(row.get("direction_match") is True for row in rows),
        "holdout_event_compare.parquet.direction_match",
    )


def _holdout_mean_forward_return(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "holdout_event_compare.parquet",
        "holdout_mean_forward_return",
        "holdout_mean_forward_return",
        "holdout_event_compare.parquet.holdout_mean_forward_return",
    )


def _holdout_hit_rate(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "holdout_event_compare.parquet",
        "holdout_hit_rate",
        "holdout_hit_rate",
        "holdout_event_compare.parquet.holdout_hit_rate",
    )


def _holdout_mean_net_return(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "holdout_backtest_compare.parquet",
        "holdout_mean_net_return",
        "holdout_mean_net_return",
        "holdout_backtest_compare.parquet.holdout_mean_net_return",
    )


def _net_return_delta(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "holdout_backtest_compare.parquet",
        "net_return_delta",
        "net_return_delta",
        "holdout_backtest_compare.parquet.net_return_delta",
    )


def _drawdown_delta(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(formal_dir / "holdout_backtest_compare.parquet")
    backtest = _mean(_numeric_values(rows, "backtest_max_drawdown"))
    holdout = _mean(_numeric_values(rows, "holdout_max_drawdown"))
    if backtest is None or holdout is None:
        return _missing("drawdown_delta", "holdout_backtest_compare.parquet lacks drawdown columns")
    return _observed("drawdown_delta", holdout - backtest, "holdout_backtest_compare.parquet.drawdown_delta")


def _gap(metric_id: str, rel_path: str) -> Any:
    def observe(formal_dir: Path) -> MissingMetric | ObservedMetric:
        if (formal_dir / rel_path).exists():
            return _observed(metric_id, "input_available", rel_path)
        return _missing(metric_id, f"missing {rel_path}")

    return observe


_METRIC_OBSERVERS: dict[str, dict[str, Any]] = {
    "tss_data_ready": {
        "time_index_coverage": _time_index_coverage,
        "asset_count": _asset_count,
        "split_sample_adequacy": _split_sample_adequacy,
        "quality_flag_rate": _quality_flag_rate,
    },
    "tss_signal_ready": {
        "signal_non_null_ratio": _signal_non_null_ratio,
        "signal_event_count": lambda formal_dir: _count_parquet_rows(
            formal_dir, "signal_event_count", "signal_event_panel.parquet"
        ),
        "parameter_count": lambda formal_dir: _count_csv_rows(formal_dir, "parameter_count", "param_manifest.csv"),
        "route_inheritance": _route_inheritance,
    },
    "tss_train_freeze": {
        "threshold_ledger_coverage": _gap("threshold_ledger_coverage", "train_threshold_ledger.csv"),
        "variant_ledger_coverage": lambda formal_dir: _count_csv_rows(
            formal_dir, "variant_ledger_coverage", "train_variant_ledger.csv"
        ),
        "reject_reason_completeness": _reject_reason_completeness,
        "train_quality_score": _train_quality_score,
    },
    "tss_test_evidence": {
        "mean_forward_return": _summary_value("mean_forward_return", "mean_forward_return"),
        "hit_rate": _summary_value("hit_rate", "hit_rate"),
        "base_rate_uplift": _summary_value("base_rate_uplift", "base_rate_uplift"),
        "event_count": _summary_value("event_count", "event_count"),
        "signal_frequency": _summary_value("signal_frequency", "signal_frequency"),
        "mean_rank_ic": _summary_value("mean_rank_ic", "mean_rank_ic"),
        "mfe_mae": _mfe_mae,
    },
    "tss_backtest_ready": {
        "mean_gross_return": _mean_gross_return,
        "mean_net_return": _mean_net_return,
        "gross_net_erosion": _gross_net_erosion,
        "max_drawdown": _max_drawdown,
        "turnover": _turnover,
        "capacity_utilization": _capacity_utilization,
    },
    "tss_holdout_validation": {
        "direction_match": _direction_match,
        "holdout_mean_forward_return": _holdout_mean_forward_return,
        "holdout_hit_rate": _holdout_hit_rate,
        "holdout_mean_net_return": _holdout_mean_net_return,
        "net_return_delta": _net_return_delta,
        "drawdown_delta": _drawdown_delta,
    },
}


def _dimension_health(
    observed_metrics: list[dict[str, object]],
    missing_metrics: list[dict[str, object]],
) -> str:
    if not observed_metrics:
        return "INSUFFICIENT_DATA"
    if missing_metrics:
        return "WATCH"
    return "GOOD"


def _overall_health(observed_count: int, missing_count: int) -> str:
    if observed_count == 0:
        return "INSUFFICIENT_DATA"
    if missing_count == 0:
        return "GOOD"
    if observed_count >= missing_count:
        return "WATCH"
    return "WEAK"


def _confidence(observed_count: int, missing_count: int) -> str:
    if observed_count == 0:
        return "LOW"
    if missing_count == 0:
        return "HIGH"
    return "MEDIUM" if observed_count >= missing_count else "LOW"


def _risk_notes(
    observed_metrics: list[dict[str, object]],
    missing_metrics: list[dict[str, object]],
) -> list[str]:
    notes: list[str] = []
    if missing_metrics:
        notes.append("Some expected TSS diagnostics are missing or not computed in V1.")
    if observed_metrics and missing_metrics:
        notes.append("Observed metrics should be interpreted with incomplete diagnostics coverage.")
    return notes


def _summary(stage: str, observed_metrics: list[dict[str, object]], missing_metrics: list[dict[str, object]]) -> str:
    watch_metrics = [metric for metric in observed_metrics if metric.get("severity") == "watch"]
    if watch_metrics:
        metric = watch_metrics[0]
        return f"{stage} 读到 {len(observed_metrics)} 个指标；优先关注 {metric['metric_id']}：{metric['interpretation']}"
    if observed_metrics:
        return f"{stage} 读到 {len(observed_metrics)} 个指标；当前 diagnostics 可解释，但仍不构成 review verdict。"
    if missing_metrics:
        return f"{stage} 未读到可解释指标；需要先补齐 {len(missing_metrics)} 个 diagnostics 证据。"
    return f"{stage} 没有配置可诊断指标。"


def _next_diagnostics(dimensions: list[dict[str, object]]) -> list[str]:
    actions: list[str] = []
    for dimension in dimensions:
        missing = dimension.get("missing_metrics", [])
        if not isinstance(missing, list):
            continue
        for metric in missing:
            if not isinstance(metric, dict):
                continue
            metric_id = metric.get("metric_id")
            if metric_id:
                actions.append(f"Add or standardize TSS diagnostic metric: {metric_id}")
    return sorted(set(actions))
