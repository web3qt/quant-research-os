#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.signal_diagnostics import SignalDiagnosticsError, diagnostics_payload  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show read-only QROS TSS signal diagnostics.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", default=None)
    parser.add_argument("--stage", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _render_text(payload: dict[str, object]) -> str:
    lines = [
        "QROS TSS 信号诊断",
        f"Lineage: {payload['lineage_id']} ({payload['selection_mode']})",
        f"Stage: {payload['stage']}",
        f"Route: {payload['route']}",
        f"Health: {payload['health']}",
        f"Confidence: {payload['confidence']}",
        "边界: 这是 diagnostics，这不是 review verdict，也不是 gate verdict。",
        "",
        "先说结论",
        f"- {payload['summary']}",
    ]
    summary = _first_metric_explanations(payload)
    if summary:
        lines.extend(f"- {item}" for item in summary[:3])
    else:
        lines.append("- 当前没有读到足够的 observed diagnostics，只能先看缺失证据。")

    dimensions = payload.get("dimensions")
    if isinstance(dimensions, list):
        lines.extend(["", "怎么理解这些数"])
        for dimension in dimensions:
            if not isinstance(dimension, dict):
                continue
            lines.extend(["", f"{dimension['name']} [{dimension['health']}]"])
            observed = dimension.get("observed_metrics")
            if isinstance(observed, list) and observed:
                for metric in observed:
                    if isinstance(metric, dict):
                        lines.append(
                            f"- {metric.get('metric_id')}: {metric.get('value')} "
                            f"(severity={metric.get('severity')}, source={metric.get('source')})"
                        )
                        interpretation = metric.get("interpretation")
                        if interpretation:
                            lines.append(f"  解释: {interpretation}")
                        strategy_link = metric.get("strategy_link")
                        if strategy_link:
                            lines.append(f"  跟当前策略的关系: {strategy_link}")
            missing = dimension.get("missing_metrics")
            if isinstance(missing, list) and missing:
                lines.append("缺失 / 未计算:")
                for metric in missing:
                    if isinstance(metric, dict):
                        lines.append(f"- {metric.get('metric_id')}: {metric.get('reason')}")

    next_diagnostics = payload.get("next_diagnostics")
    if isinstance(next_diagnostics, list) and next_diagnostics:
        lines.extend(["", "下一步建议补充的 diagnostics:"])
        lines.extend(f"- {item}" for item in next_diagnostics)
    return "\n".join(lines)


def _first_metric_explanations(payload: dict[str, object]) -> list[str]:
    explanations: list[str] = []
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, list):
        return explanations
    for dimension in dimensions:
        if not isinstance(dimension, dict):
            continue
        observed = dimension.get("observed_metrics")
        if not isinstance(observed, list):
            continue
        for metric in observed:
            if not isinstance(metric, dict):
                continue
            if metric.get("severity") == "watch" and metric.get("interpretation"):
                explanations.append(str(metric["interpretation"]))
    if explanations:
        return explanations
    for dimension in dimensions:
        if not isinstance(dimension, dict):
            continue
        observed = dimension.get("observed_metrics")
        if not isinstance(observed, list):
            continue
        for metric in observed:
            if isinstance(metric, dict) and metric.get("interpretation"):
                explanations.append(str(metric["interpretation"]))
    return explanations


def main() -> int:
    args = _parse_args()
    try:
        payload = diagnostics_payload(
            outputs_root=args.outputs_root.resolve(),
            lineage_id=args.lineage_id,
            stage=args.stage,
        )
    except SignalDiagnosticsError as exc:
        print(f"qros-signal-diagnostics: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
