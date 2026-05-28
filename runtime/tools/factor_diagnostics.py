from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
METRIC_LIBRARY_PATH = ROOT / "contracts" / "diagnostics" / "factor_metric_library.yaml"
STAGE_PROFILES_PATH = ROOT / "contracts" / "diagnostics" / "csf_stage_diagnostic_profiles.yaml"

STAGE_DIRS: dict[str, str] = {
    "csf_data_ready": "02_csf_data_ready",
    "csf_signal_ready": "03_csf_signal_ready",
    "csf_train_freeze": "04_csf_train_freeze",
    "csf_test_evidence": "05_csf_test_evidence",
    "csf_backtest_ready": "06_csf_backtest_ready",
    "csf_holdout_validation": "07_csf_holdout_validation",
}


class FactorDiagnosticsError(RuntimeError):
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
            "value": self.value,
            "status": self.status,
            "source": self.source,
            "severity": self.severity,
            "interpretation": self.interpretation,
            "strategy_link": self.strategy_link,
        }


@dataclass(frozen=True)
class MissingMetric:
    metric_id: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {"metric_id": self.metric_id, "reason": self.reason}


def latest_lineage_id(outputs_root: Path) -> str:
    if not outputs_root.exists():
        raise FactorDiagnosticsError(f"No QROS outputs directory found: {outputs_root}")
    lineage_dirs = [path for path in outputs_root.iterdir() if path.is_dir()]
    if not lineage_dirs:
        raise FactorDiagnosticsError(f"No QROS lineage directories found under: {outputs_root}")
    latest = max(lineage_dirs, key=lambda path: (_latest_mtime(path), path.name))
    return latest.name


def diagnostics_payload(
    *,
    outputs_root: Path,
    lineage_id: str | None = None,
    stage: str | None = None,
) -> dict[str, object]:
    profiles = _load_yaml(STAGE_PROFILES_PATH)["profiles"]
    metrics = _load_yaml(METRIC_LIBRARY_PATH)["metrics"]

    selection_mode = "explicit" if lineage_id else "latest"
    selected_lineage_id = lineage_id or latest_lineage_id(outputs_root)
    lineage_root = outputs_root / selected_lineage_id
    if not lineage_root.exists() or not lineage_root.is_dir():
        raise FactorDiagnosticsError(f"QROS lineage not found: {lineage_root}")

    selected_stage = stage or _infer_stage(lineage_root)
    if selected_stage not in profiles or selected_stage not in STAGE_DIRS:
        raise FactorDiagnosticsError(f"Unsupported diagnostics stage: {selected_stage}")

    stage_formal_dir = lineage_root / STAGE_DIRS[selected_stage] / "author" / "formal"
    if not stage_formal_dir.exists():
        raise FactorDiagnosticsError(
            f"No CSF formal artifacts found for lineage {selected_lineage_id} stage {selected_stage}: "
            f"{stage_formal_dir}"
        )

    dimensions: list[dict[str, object]] = []
    observed_count = 0
    missing_count = 0
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
                observed_count += 1
                observed_metrics.append(result.as_dict())
            else:
                missing_count += 1
                missing_metrics.append(result.as_dict())
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
        "schema_id": "qros-factor-diagnostics-report-v1",
        "lineage_id": selected_lineage_id,
        "lineage_root": str(lineage_root),
        "selection_mode": selection_mode,
        "stage": selected_stage,
        "stage_formal_dir": str(stage_formal_dir),
        "route": "cross_sectional_factor",
        "health": _overall_health(observed_count, missing_count),
        "confidence": _confidence(observed_count, missing_count),
        "formal_verdict_boundary": "diagnostics_only_not_review",
        "metric_library_schema": "factor-metric-library-v1",
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
    raise FactorDiagnosticsError(
        f"No CSF formal artifacts found for lineage {lineage_root.name}. "
        "Run qros-progress to confirm current stage, or pass --stage explicitly."
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FactorDiagnosticsError(f"{path}: yaml read failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise FactorDiagnosticsError(f"{path}: expected yaml map")
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

    if metric_id == "rank_ic":
        if numeric is None:
            return _plain_interpretation(metric_id)
        if numeric < 0:
            return {
                "severity": "watch",
                "interpretation": (
                    f"mean Rank IC 为负（{numeric:.4f}），表示当前样本中因子排序与未来收益排序反向；"
                    "通俗讲，高分标的后面反而更容易排在收益靠后的一侧。"
                ),
                "strategy_link": (
                    "如果当前策略是做多高因子组，这个结果和策略方向存在冲突；"
                    "需要优先检查 factor_direction 是否写反，再结合 Top-Bottom Spread、净收益和 holdout 方向确认。"
                ),
            }
        if numeric > 0:
            return {
                "severity": "info",
                "interpretation": (
                    f"mean Rank IC 为正（{numeric:.4f}），表示因子排序与未来收益排序大体同向；"
                    "高分标的后续收益排名更靠前的概率更高。"
                ),
                "strategy_link": "如果策略做多高因子组，这个信号方向与策略假设基本一致，但仍要看分层、成本后收益和 holdout 是否延续。",
            }
        return {
            "severity": "watch",
            "interpretation": "mean Rank IC 接近 0，表示当前窗口里排序预测关系很弱，因子可能接近噪声。",
            "strategy_link": "不要只凭这个因子做方向判断，应检查分层收益、样本 breadth 和是否只在少数日期有效。",
        }

    if metric_id == "rank_ic_win_rate" and numeric is not None:
        severity = "watch" if numeric < 0.5 else "info"
        return {
            "severity": severity,
            "interpretation": f"Rank IC 胜率为 {_pct(numeric)}，表示有多少日期因子排序方向是对的。",
            "strategy_link": "如果胜率低于 50%，说明方向正确的日期偏少，需要确认收益是否只来自少数极端日期。",
        }

    if metric_id == "icir" and numeric is not None:
        severity = "watch" if numeric <= 0 else "info"
        return {
            "severity": severity,
            "interpretation": f"ICIR 为 {numeric:.4f}，衡量 Rank IC 均值相对波动的稳定性；越高说明预测力越稳定。",
            "strategy_link": "ICIR 偏低或为负时，即使某些日期 IC 好看，也可能难以稳定转化为可交易收益。",
        }

    if metric_id == "mean_gross_return" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"组合扣成本前平均收益为 {_pct(numeric)}，反映信号在不考虑交易摩擦时的原始收益能力。",
            "strategy_link": "如果 gross 为正但 net 明显变弱，问题通常不在信号方向本身，而在换手、滑点或容量约束。",
        }

    if metric_id == "mean_net_return" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"组合扣成本后平均收益为 {_pct(numeric)}，这是更接近真实可交易表现的收益口径。",
            "strategy_link": "如果扣成本后收益转负，说明当前策略即使有预测信号，也可能被手续费、滑点或调仓频率吃掉。",
        }

    if metric_id == "gross_net_erosion" and numeric is not None:
        return {
            "severity": "watch" if numeric > 0 else "info",
            "interpretation": f"gross 到 net 的成本侵蚀约为 {_pct(numeric)}，表示交易成本吃掉了多少平均收益。",
            "strategy_link": "成本侵蚀越大，越需要降低换手、延长持有期、收紧交易过滤，或重新评估该因子的可交易性。",
        }

    if metric_id == "max_drawdown" and numeric is not None:
        return {
            "severity": "watch" if abs(numeric) > 0.1 else "info",
            "interpretation": f"最大回撤约为 {_pct(abs(numeric))}，表示这条组合曲线历史上最深的账面回撤幅度。",
            "strategy_link": "回撤越深，对仓位、止损、风险预算和是否需要组合层风控的要求越高。",
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
                "interpretation": "holdout 方向不匹配，表示样本外方向与训练/测试阶段的冻结预期相反。",
                "strategy_link": "这通常是高优先级风险信号，需要检查因子方向、市场状态变化和是否存在过拟合。",
            }
        return {
            "severity": "info",
            "interpretation": "holdout 方向匹配，表示样本外方向与冻结预期一致。",
            "strategy_link": "方向一致只是必要条件，还要继续看收益退化、回撤变化和 rolling stability。",
        }

    if metric_id == "holdout_mean_net_return" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"holdout 扣成本后平均收益为 {_pct(numeric)}，表示样本外更接近真实交易的收益表现。",
            "strategy_link": "如果 holdout net return 明显低于 backtest，需要警惕样本内过拟合或市场状态变化。",
        }

    if metric_id == "net_return_delta" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"holdout 相对 backtest 的净收益变化为 {_pct(numeric)}。",
            "strategy_link": "负数表示样本外收益退化；需要结合 Rank IC、成本侵蚀和 regime shift 判断退化来源。",
        }

    if metric_id == "drawdown_delta" and numeric is not None:
        return {
            "severity": "watch" if numeric < 0 else "info",
            "interpretation": f"holdout 相对 backtest 的回撤变化为 {_pct(numeric)}。",
            "strategy_link": "负数通常表示样本外回撤加深，需要检查是否有市场状态切换或组合风险暴露扩大。",
        }

    if metric_id in {"coverage_ratio", "factor_score_non_null_ratio"} and numeric is not None:
        return {
            "severity": "watch" if numeric < 0.8 else "info",
            "interpretation": f"{metric_id} 为 {_pct(numeric)}，反映样本或因子值的有效覆盖程度。",
            "strategy_link": "覆盖不足会让 IC、分层和回测结果更容易被少数标的或少数日期主导。",
        }

    if metric_id in {"asset_count", "breadth", "bucket_min_names"} and numeric is not None:
        return {
            "severity": "watch" if numeric < 30 else "info",
            "interpretation": f"{metric_id} 为 {numeric:.0f}，反映横截面样本厚度或分层样本数量。",
            "strategy_link": "横截面太薄时，分组收益和 Rank IC 的稳定性会下降，容易出现偶然有效。",
        }

    return _plain_interpretation(metric_id)


def _plain_interpretation(metric_id: str) -> dict[str, str]:
    return {
        "severity": "info",
        "interpretation": f"{metric_id} 已观测到，可作为当前阶段质量诊断证据之一。",
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


def _sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


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


def _min_from_parquet(path: Path, metric_id: str, column: str, source: str) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(path)
    values = _numeric_values(rows, column)
    if not values:
        return _missing(metric_id, f"{path.name} lacks numeric {column}")
    return _observed(metric_id, min(values), source)


def _exists_metric(formal_dir: Path, metric_id: str, rel_path: str) -> ObservedMetric | MissingMetric:
    path = formal_dir / rel_path
    if path.exists():
        return _observed(metric_id, "present", rel_path)
    return _missing(metric_id, f"missing {rel_path}")


def _data_coverage(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _min_from_parquet(
        formal_dir / "cross_section_coverage.parquet",
        "coverage_ratio",
        "coverage_ratio",
        "cross_section_coverage.parquet.coverage_ratio",
    )


def _data_asset_count(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _min_from_parquet(
        formal_dir / "cross_section_coverage.parquet",
        "asset_count",
        "asset_count",
        "cross_section_coverage.parquet.asset_count",
    )


def _split_sample_adequacy(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_yaml(
        formal_dir / "split_sample_adequacy_report.yaml",
        "split_sample_adequacy",
        "final_verdict",
        "split_sample_adequacy_report.yaml.final_verdict",
    )


def _signal_coverage(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _min_from_parquet(
        formal_dir / "factor_coverage_report.parquet",
        "coverage_ratio",
        "coverage_ratio",
        "factor_coverage_report.parquet.coverage_ratio",
    )


def _factor_score_non_null_ratio(formal_dir: Path) -> ObservedMetric | MissingMetric:
    manifest = _read_yaml_optional(formal_dir / "factor_manifest.yaml")
    if manifest is None:
        return _missing("factor_score_non_null_ratio", "missing factor_manifest.yaml")
    score_field = str(manifest.get("final_score_field", "")).strip()
    if not score_field:
        return _missing("factor_score_non_null_ratio", "factor_manifest.yaml lacks final_score_field")
    rows = _read_parquet_rows(formal_dir / "factor_panel.parquet")
    if not rows:
        return _missing("factor_score_non_null_ratio", "missing or empty factor_panel.parquet")
    non_null = sum(1 for row in rows if row.get(score_field) is not None)
    return _observed("factor_score_non_null_ratio", non_null / len(rows), f"factor_panel.parquet.{score_field}")


def _factor_direction(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_yaml(
        formal_dir / "factor_manifest.yaml",
        "factor_direction",
        "factor_direction",
        "factor_manifest.yaml.factor_direction",
    )


def _input_field_binding(formal_dir: Path) -> ObservedMetric | MissingMetric:
    manifest = _read_yaml_optional(formal_dir / "factor_manifest.yaml")
    if manifest is None:
        return _missing("input_field_binding", "missing factor_manifest.yaml")
    mappings = manifest.get("input_field_map")
    if isinstance(mappings, list) and mappings:
        return _observed("input_field_binding", "present", "factor_manifest.yaml.input_field_map")
    return _missing("input_field_binding", "input_field_map missing or empty")


def _route_inheritance(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _exists_metric(formal_dir, "route_inheritance", "route_inheritance_contract.yaml")


def _train_quality_score(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "train_factor_quality.parquet",
        "train_quality_score",
        "quality_score",
        "train_factor_quality.parquet.quality_score",
    )


def _bucket_min_names(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _min_from_parquet(
        formal_dir / "train_bucket_diagnostics.parquet",
        "bucket_min_names",
        "min_names",
        "train_bucket_diagnostics.parquet.min_names",
    )


def _variant_ledger_coverage(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_csv_rows(formal_dir / "train_variant_ledger.csv")
    if rows and all(str(row.get("variant_id", "")).strip() for row in rows):
        return _observed("variant_ledger_coverage", len(rows), "train_variant_ledger.csv")
    return _missing("variant_ledger_coverage", "missing train_variant_ledger.csv rows")


def _reject_reason_completeness(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_csv_rows(formal_dir / "train_variant_rejects.csv")
    if rows and all(str(row.get("reject_reason", "")).strip() for row in rows):
        return _observed("reject_reason_completeness", "complete", "train_variant_rejects.csv.reject_reason")
    return _missing("reject_reason_completeness", "missing reject_reason rows")


def _rank_ic(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_json(
        formal_dir / "rank_ic_summary.json",
        "rank_ic",
        "mean_rank_ic",
        "rank_ic_summary.json.mean_rank_ic",
    )


def _rank_ic_win_rate(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(formal_dir / "rank_ic_timeseries.parquet")
    values = _numeric_values(rows, "rank_ic")
    if not values:
        return _missing("rank_ic_win_rate", "rank_ic_timeseries.parquet lacks rank_ic values")
    return _observed(
        "rank_ic_win_rate",
        sum(1 for value in values if value > 0) / len(values),
        "rank_ic_timeseries.parquet.rank_ic",
    )


def _icir(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(formal_dir / "rank_ic_timeseries.parquet")
    values = _numeric_values(rows, "rank_ic")
    mean = _mean(values)
    std = _sample_std(values)
    if mean is None or std in {None, 0}:
        return _missing("icir", "rank_ic_timeseries.parquet lacks enough non-constant rank_ic values")
    return _observed("icir", mean / std, "rank_ic_timeseries.parquet.rank_ic")


def _monotonicity(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_json(
        formal_dir / "monotonicity_report.json",
        "monotonicity",
        "status",
        "monotonicity_report.json.status",
    )


def _breadth(formal_dir: Path) -> ObservedMetric | MissingMetric:
    if (formal_dir / "breadth_coverage_report.parquet").exists():
        return _min_from_parquet(
            formal_dir / "breadth_coverage_report.parquet",
            "breadth",
            "asset_count",
            "breadth_coverage_report.parquet.asset_count",
        )
    return _mean_from_parquet(
        formal_dir / "holdout_factor_diagnostics.parquet",
        "breadth",
        "breadth",
        "holdout_factor_diagnostics.parquet.breadth",
    )


def _subperiod_stability(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_json(
        formal_dir / "subperiod_stability_report.json",
        "subperiod_stability",
        "status",
        "subperiod_stability_report.json.status",
    )


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
    rows = _read_parquet_rows(formal_dir / "holdout_test_compare.parquet")
    if not rows:
        return _missing("direction_match", "missing holdout_test_compare.parquet")
    return _observed(
        "direction_match",
        all(row.get("direction_match") is True for row in rows),
        "holdout_test_compare.parquet.direction_match",
    )


def _holdout_mean_net_return(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "holdout_test_compare.parquet",
        "holdout_mean_net_return",
        "holdout_mean_net_return",
        "holdout_test_compare.parquet.holdout_mean_net_return",
    )


def _net_return_delta(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "holdout_portfolio_compare.parquet",
        "net_return_delta",
        "net_return_delta",
        "holdout_portfolio_compare.parquet.net_return_delta",
    )


def _drawdown_delta(formal_dir: Path) -> ObservedMetric | MissingMetric:
    rows = _read_parquet_rows(formal_dir / "holdout_portfolio_compare.parquet")
    backtest = _mean(_numeric_values(rows, "backtest_max_drawdown"))
    holdout = _mean(_numeric_values(rows, "holdout_max_drawdown"))
    if backtest is None or holdout is None:
        return _missing("drawdown_delta", "holdout_portfolio_compare.parquet lacks drawdown columns")
    return _observed("drawdown_delta", holdout - backtest, "holdout_portfolio_compare.parquet.drawdown_delta")


def _bucket_stability_score(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _mean_from_parquet(
        formal_dir / "holdout_factor_diagnostics.parquet",
        "bucket_stability_score",
        "bucket_stability_score",
        "holdout_factor_diagnostics.parquet.bucket_stability_score",
    )


def _rolling_stability(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_json(
        formal_dir / "rolling_holdout_stability.json",
        "rolling_stability",
        "stability_status",
        "rolling_holdout_stability.json.stability_status",
    )


def _regime_shift_audit(formal_dir: Path) -> ObservedMetric | MissingMetric:
    return _value_from_json(
        formal_dir / "regime_shift_audit.json",
        "regime_shift_audit",
        "audit_status",
        "regime_shift_audit.json.audit_status",
    )


def _gap(metric_id: str, rel_path: str) -> Any:
    def observe(formal_dir: Path) -> MissingMetric | ObservedMetric:
        if (formal_dir / rel_path).exists():
            return _observed(metric_id, "input_available", rel_path)
        return _missing(metric_id, f"missing {rel_path}")

    return observe


def _mean_from_holdout_factor(metric_id: str) -> Any:
    def observe(formal_dir: Path) -> ObservedMetric | MissingMetric:
        return _mean_from_parquet(
            formal_dir / "holdout_factor_diagnostics.parquet",
            metric_id,
            metric_id,
            f"holdout_factor_diagnostics.parquet.{metric_id}",
        )

    return observe


def _risk_metric(metric_id: str, column: str) -> Any:
    def observe(formal_dir: Path) -> ObservedMetric | MissingMetric:
        return _mean_from_parquet(
            formal_dir / "risk_adjusted_metrics.parquet",
            metric_id,
            column,
            f"risk_adjusted_metrics.parquet.{column}",
        )

    return observe


_METRIC_OBSERVERS: dict[str, dict[str, Any]] = {
    "csf_data_ready": {
        "coverage_ratio": _data_coverage,
        "asset_count": _data_asset_count,
        "split_sample_adequacy": _split_sample_adequacy,
        "universe_membership": _gap("universe_membership", "asset_universe_membership.parquet"),
        "eligibility_mask": _gap("eligibility_mask", "eligibility_base_mask.parquet"),
        "liquidity_panel": _gap("liquidity_panel", "shared_feature_base/liquidity_panel.parquet"),
        "beta_inputs": _gap("beta_inputs", "shared_feature_base/beta_inputs.parquet"),
    },
    "csf_signal_ready": {
        "coverage_ratio": _signal_coverage,
        "factor_score_non_null_ratio": _factor_score_non_null_ratio,
        "factor_direction": _factor_direction,
        "input_field_binding": _input_field_binding,
        "route_inheritance": _route_inheritance,
    },
    "csf_train_freeze": {
        "variant_ledger_coverage": _variant_ledger_coverage,
        "reject_reason_completeness": _reject_reason_completeness,
        "train_quality_score": _train_quality_score,
        "bucket_min_names": _bucket_min_names,
        "neutralization_diagnostics": _gap("neutralization_diagnostics", "train_neutralization_diagnostics.parquet"),
    },
    "csf_test_evidence": {
        "rank_ic": _rank_ic,
        "rank_ic_win_rate": _rank_ic_win_rate,
        "icir": _icir,
        "ic": _gap("ic", "ic_timeseries.parquet"),
        "ic_skew": _gap("ic_skew", "rank_ic_timeseries.parquet"),
        "ic_autocorrelation": _gap("ic_autocorrelation", "rank_ic_timeseries.parquet"),
        "top_bottom_spread": _gap("top_bottom_spread", "bucket_returns.parquet"),
        "monotonicity": _monotonicity,
        "bucket_win_rate": _gap("bucket_win_rate", "bucket_returns.parquet"),
        "breadth": _breadth,
        "subperiod_stability": _subperiod_stability,
    },
    "csf_backtest_ready": {
        "mean_gross_return": _mean_gross_return,
        "mean_net_return": _mean_net_return,
        "gross_net_erosion": _gross_net_erosion,
        "name_level_concentration": _gap("name_level_concentration", "name_level_metrics.parquet"),
        "alpha": _gap("alpha", "portfolio_return_series.parquet"),
        "beta": _gap("beta", "portfolio_return_series.parquet"),
        "max_drawdown": _max_drawdown,
        "sharpe": _risk_metric("sharpe", "sharpe_365d"),
        "sortino": _risk_metric("sortino", "sortino_365d"),
        "calmar": _risk_metric("calmar", "calmar_365d"),
        "turnover": _turnover,
        "capacity_utilization": _capacity_utilization,
        "profit_factor": _risk_metric("profit_factor", "profit_factor"),
    },
    "csf_holdout_validation": {
        "direction_match": _direction_match,
        "holdout_mean_net_return": _holdout_mean_net_return,
        "net_return_delta": _net_return_delta,
        "drawdown_delta": _drawdown_delta,
        "coverage_ratio": _mean_from_holdout_factor("coverage_ratio"),
        "breadth": _breadth,
        "bucket_stability_score": _bucket_stability_score,
        "sharpe": _risk_metric("sharpe", "sharpe_365d"),
        "sortino": _risk_metric("sortino", "sortino_365d"),
        "calmar": _risk_metric("calmar", "calmar_365d"),
        "profit_factor": _risk_metric("profit_factor", "profit_factor"),
        "rolling_stability": _rolling_stability,
        "regime_shift_audit": _regime_shift_audit,
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
        notes.append("Some expected diagnostics are missing or not computed in V1.")
    if observed_metrics and missing_metrics:
        notes.append("Observed metrics should be interpreted with incomplete diagnostics coverage.")
    return notes


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
                actions.append(f"Add or standardize diagnostic metric: {metric_id}")
    return sorted(set(actions))
