#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_skillgen.adversarial_review_contract import issue_spawned_reviewer_receipt
from runtime.tools.review_skillgen.context_inference import build_stage_context, infer_review_context


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue the spawned reviewer receipt before adversarial review.")
    parser.add_argument("--stage-dir", type=Path, default=None)
    parser.add_argument("--lineage-root", type=Path, default=None)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--reviewer-session-id", required=True)
    parser.add_argument("--launcher-session-id", default="local-launcher-session")
    parser.add_argument("--launcher-thread-id", default=os.environ.get("CODEX_THREAD_ID", "local-launcher-thread"))
    parser.add_argument("--spawned-agent-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.stage_dir is not None or args.lineage_root is not None:
        if args.stage_dir is None or args.lineage_root is None:
            raise SystemExit("--stage-dir and --lineage-root must be provided together")
        context = build_stage_context(args.stage_dir.resolve())
    else:
        context = infer_review_context(Path.cwd())

    stage_dir = Path(context["stage_dir"]).resolve()
    payload = issue_spawned_reviewer_receipt(
        stage_dir,
        reviewer_identity=args.reviewer_id,
        reviewer_session_id=args.reviewer_session_id,
        launcher_session_id=args.launcher_session_id,
        launcher_thread_id=args.launcher_thread_id,
        spawned_agent_id=args.spawned_agent_id,
    )
    print(f"Issued: {stage_dir / 'review' / 'request' / 'spawned_reviewer_receipt.yaml'}")
    print(f"Review cycle: {payload['review_cycle_id']}")
    print(f"Requested reviewer: {payload['requested_reviewer_identity']}")
    print(f"Spawned agent id: {payload['spawned_agent_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
