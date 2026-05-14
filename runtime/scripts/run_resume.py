#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.progress_runtime import progress_status_payload  # noqa: E402
from runtime.tools.research_session import run_research_session  # noqa: E402
from runtime.tools.review_resume_protocol import build_direct_handoff_capsule  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the current QROS handoff state.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", required=True)
    parser.add_argument("--continue", dest="continue_mode", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _render_text(payload: dict[str, object]) -> str:
    lines = [
        "QROS Resume",
        f"Lineage: {payload['lineage_id']}",
        f"Current stage: {payload['current_stage']}",
        f"Stage status: {payload['stage_status']}",
        f"Gate status: {payload['gate_status']}",
        f"Blocking reason code: {payload['blocking_reason_code']}",
    ]
    if payload.get("blocking_reason"):
        lines.append(f"Blocking reason: {payload['blocking_reason']}")
    lines.extend(
        [
            f"Next action: {payload['next_action']}",
            f"Handoff hint: {payload['handoff_hint']}",
        ]
    )
    if payload.get("recommended_skill"):
        lines.append(f"Recommended next skill: {payload['recommended_skill']}")
    return "\n".join(lines)


def _payload_from_session(status) -> dict[str, object]:
    payload = asdict(status)
    payload["lineage_root"] = str(status.lineage_root)
    payload.update(build_direct_handoff_capsule(status))
    payload["selection_mode"] = "explicit"
    return payload


def main() -> int:
    args = _parse_args()
    if args.continue_mode:
        status = run_research_session(
            outputs_root=args.outputs_root.resolve(),
            lineage_id=args.lineage_id,
            continue_mode=True,
        )
        payload = _payload_from_session(status)
    else:
        payload = progress_status_payload(outputs_root=args.outputs_root.resolve(), lineage_id=args.lineage_id)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
