#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_session_runtime import start_review_session  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start an explicit human-driven review session for the current stage.")
    parser.add_argument("--stage-dir", type=Path, default=None)
    parser.add_argument("--lineage-root", type=Path, default=None)
    parser.add_argument("--reviewer-id", default=os.environ.get("QROS_REVIEWER_ID", "codex-reviewer"))
    parser.add_argument("--reviewer-session-id", default=os.environ.get("QROS_REVIEWER_SESSION_ID") or os.environ.get("CODEX_THREAD_ID") or "local-review-session")
    parser.add_argument("--launcher-session-id", default=os.environ.get("CODEX_THREAD_ID", "local-review-session"))
    parser.add_argument("--launcher-thread-id", default=os.environ.get("CODEX_THREAD_ID", "local-review-thread"))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    explicit_context = None
    if args.stage_dir is not None or args.lineage_root is not None:
        if args.stage_dir is None or args.lineage_root is None:
            raise SystemExit("--stage-dir and --lineage-root must be provided together")
        explicit_context = {
            "stage_dir": args.stage_dir.resolve(),
            "lineage_root": args.lineage_root.resolve(),
        }

    payload = start_review_session(
        cwd=Path.cwd(),
        explicit_context=explicit_context,
        reviewer_identity=args.reviewer_id,
        reviewer_session_id=args.reviewer_session_id,
        launcher_session_id=args.launcher_session_id,
        launcher_thread_id=args.launcher_thread_id,
    )
    print(f"Lineage: {payload['lineage_id']}")
    print(f"Stage: {payload['stage']}")
    print(f"Review cycle: {payload['review_cycle_id']}")
    print(f"Request: {payload['request_path']}")
    print(f"Receipt: {payload['receipt_path']}")
    if payload["archived_paths"]:
        print("Archived:")
        for item in payload["archived_paths"]:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
