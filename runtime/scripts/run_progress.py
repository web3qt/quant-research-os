#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.progress_runtime import ProgressError, progress_status_payload  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show read-only QROS research progress.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _render_text(payload: dict[str, object]) -> str:
    lines = [
        "QROS Progress",
        f"Lineage: {payload['lineage_id']} ({payload['selection_mode']})",
        f"Current stage: {payload['current_stage']}",
        f"Current active skill: {payload['current_skill']}",
        f"Stage status: {payload['stage_status']}",
        f"Gate status: {payload['gate_status']}",
        f"Blocking reason code: {payload['blocking_reason_code']}",
    ]
    if payload.get("blocking_reason"):
        lines.append(f"Blocking reason: {payload['blocking_reason']}")
    lines.extend(
        [
            f"Next action: {payload['next_action']}",
            f"Resume hint: {payload['resume_hint']}",
        ]
    )
    if payload.get("clear_required"):
        lines.extend(
            [
                "Clear required: True",
                f"Clear instruction: {payload['clear_instruction']}",
            ]
        )
        if payload.get("recommended_skill"):
            lines.append(f"Recommended next skill: {payload['recommended_skill']}")
    open_risks = payload.get("open_risks")
    if isinstance(open_risks, list) and open_risks:
        lines.append("Open risks:")
        lines.extend(f"- {item}" for item in open_risks)
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    try:
        payload = progress_status_payload(
            outputs_root=args.outputs_root.resolve(),
            lineage_id=args.lineage_id,
        )
    except ProgressError as exc:
        print(f"qros-progress: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
