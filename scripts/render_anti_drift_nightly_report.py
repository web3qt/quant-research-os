#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.anti_drift_baseline import compare_json_roots


def render_markdown_report(compare_result: dict) -> str:
    lines = [
        "# Anti-Drift Nightly Report",
        "",
        f"- Baseline: `{compare_result['baseline_root']}`",
        f"- Current: `{compare_result['current_root']}`",
        f"- Matches: `{compare_result['matches']}`",
        "",
    ]

    if compare_result["missing_files"]:
        lines.extend(["## Missing files", ""])
        lines.extend(f"- `{path}`" for path in compare_result["missing_files"])
        lines.append("")

    if compare_result["added_files"]:
        lines.extend(["## Added files", ""])
        lines.extend(f"- `{path}`" for path in compare_result["added_files"])
        lines.append("")

    if compare_result["changed_files"]:
        lines.extend(["## Changed files", ""])
        for rel_path, payload in compare_result["changed_files"].items():
            lines.append(f"### `{rel_path}`")
            changed_keys = sorted(set(payload["baseline"]) | set(payload["current"]))
            for key in changed_keys:
                if payload["baseline"].get(key) != payload["current"].get(key):
                    lines.append(f"- `{key}`")
                    lines.append(f"  - baseline: `{payload['baseline'].get(key)}`")
                    lines.append(f"  - current: `{payload['current'].get(key)}`")
            lines.append("")

    if not compare_result["missing_files"] and not compare_result["added_files"] and not compare_result["changed_files"]:
        lines.extend(["## Summary", "", "No semantic drift detected against the blessed baseline.", ""])

    return "\n".join(lines).rstrip() + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a markdown nightly anti-drift report.")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = render_markdown_report(compare_json_roots(args.baseline, args.current))
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
