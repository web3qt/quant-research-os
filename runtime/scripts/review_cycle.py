#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare QROS review cycles.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="Prepare request, receipt, handoff prompt, and closer command.")
    prepare.add_argument("--stage-dir", type=Path, default=None)
    prepare.add_argument("--lineage-root", type=Path, default=None)
    prepare.add_argument("--reviewer-id", default=os.environ.get("QROS_REVIEWER_ID", "codex-reviewer"))
    prepare.add_argument(
        "--reviewer-session-id",
        default=os.environ.get("QROS_REVIEWER_SESSION_ID") or os.environ.get("CODEX_THREAD_ID") or "spawned-reviewer",
    )
    prepare.add_argument("--launcher-session-id", default=os.environ.get("CODEX_THREAD_ID", "local-launcher-session"))
    prepare.add_argument("--launcher-thread-id", default=os.environ.get("CODEX_THREAD_ID", "local-launcher-thread"))
    prepare.add_argument("--spawned-agent-id", required=True)
    prepare.add_argument("--json", action="store_true")
    return parser.parse_args()


def _explicit_context(args: argparse.Namespace) -> dict[str, Path] | None:
    if args.stage_dir is None and args.lineage_root is None:
        return None
    if args.stage_dir is None or args.lineage_root is None:
        raise SystemExit("--stage-dir and --lineage-root must be provided together")
    return {
        "stage_dir": args.stage_dir.resolve(),
        "lineage_root": args.lineage_root.resolve(),
    }


def _json_safe(payload: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, Path):
            safe[key] = str(value)
        else:
            safe[key] = value
    return safe


def main() -> int:
    args = _parse_args()
    if args.command != "prepare":
        raise SystemExit(f"unsupported command: {args.command}")
    payload = prepare_review_cycle_for_handoff(
        cwd=Path.cwd(),
        explicit_context=_explicit_context(args),
        reviewer_identity=args.reviewer_id,
        reviewer_session_id=args.reviewer_session_id,
        launcher_session_id=args.launcher_session_id,
        launcher_thread_id=args.launcher_thread_id,
        spawned_agent_id=args.spawned_agent_id,
    )
    if args.json:
        print(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2))
        return 0

    print(f"Lineage: {payload['lineage_id']}")
    print(f"Stage: {payload['stage']}")
    print(f"Review cycle: {payload['review_cycle_id']}")
    print(f"Request: {payload['request_path']}")
    print(f"Receipt: {payload['receipt_path']}")
    print()
    print("Reviewer handoff prompt:")
    print(payload["reviewer_handoff_prompt"])
    print()
    print("Closer command:")
    print(payload["closer_command"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
