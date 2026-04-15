#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_gate_summary(
    *,
    compare_result: dict[str, Any],
    report_path: str | None = None,
    freshness_ok: bool = True,
) -> dict[str, Any]:
    failure_reasons: list[str] = list(compare_result.get("input_errors", []))
    if not compare_result.get("matches", False):
        if not compare_result.get("input_errors"):
            failure_reasons.append("semantic_drift_detected")
    if not freshness_ok:
        failure_reasons.append("nightly_report_stale")

    return {
        "gate": "anti_drift_nightly",
        "status": "PASS" if not failure_reasons else "FAIL",
        "baseline_root": compare_result["baseline_root"],
        "current_root": compare_result["current_root"],
        "matches": compare_result["matches"],
        "freshness_ok": freshness_ok,
        "input_errors": compare_result.get("input_errors", []),
        "missing_files": compare_result.get("missing_files", []),
        "added_files": compare_result.get("added_files", []),
        "changed_files": sorted(compare_result.get("changed_files", {}).keys()),
        "failure_reasons": failure_reasons,
        "report_path": report_path,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a machine-readable anti-drift gate summary.")
    parser.add_argument("--compare-json", type=Path, required=True)
    parser.add_argument("--report-path", default=None)
    parser.add_argument(
        "--freshness-ok",
        choices=["true", "false"],
        default="true",
        help="Whether the nightly report is still within freshness SLA.",
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    compare_result = json.loads(args.compare_json.read_text(encoding="utf-8"))
    summary = build_gate_summary(
        compare_result=compare_result,
        report_path=args.report_path,
        freshness_ok=args.freshness_ok == "true",
    )
    payload = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
