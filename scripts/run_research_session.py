#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.research_session import run_research_session


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the QROS orchestrated research session.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", default=None)
    parser.add_argument("--raw-idea", default=None)
    parser.add_argument(
        "--confirm-mandate",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build mandate outputs.",
    )
    parser.add_argument(
        "--confirm-data-ready",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build data_ready outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.lineage_id is None and args.raw_idea is None:
        raise SystemExit("Either --lineage-id or --raw-idea must be provided")
    if args.confirm_mandate and args.confirm_data_ready:
        raise SystemExit("Use at most one confirmation flag at a time")

    status = run_research_session(
        outputs_root=args.outputs_root.resolve(),
        lineage_id=args.lineage_id,
        raw_idea=args.raw_idea,
        mandate_decision="CONFIRM_MANDATE" if args.confirm_mandate else None,
        data_ready_decision="CONFIRM_DATA_READY" if args.confirm_data_ready else None,
    )

    print(f"Lineage: {status.lineage_id}")
    print(f"Current stage: {status.current_stage}")
    print(f"Gate status: {status.gate_status}")
    print(f"Next action: {status.next_action}")
    if status.why_now:
        print("Why now:")
        for item in status.why_now:
            print(f"- {item}")
    if status.open_risks:
        print("Open risks:")
        for item in status.open_risks:
            print(f"- {item}")
    if status.artifacts_written:
        print("Artifacts written:")
        for item in status.artifacts_written:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
