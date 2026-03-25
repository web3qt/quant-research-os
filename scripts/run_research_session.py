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
    parser.add_argument(
        "--confirm-signal-ready",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build signal_ready outputs.",
    )
    parser.add_argument(
        "--confirm-train-freeze",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build train_freeze outputs.",
    )
    parser.add_argument(
        "--confirm-test-evidence",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build test_evidence outputs.",
    )
    parser.add_argument(
        "--confirm-backtest-ready",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build backtest_ready outputs.",
    )
    parser.add_argument(
        "--confirm-holdout-validation",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build holdout_validation outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.lineage_id is None and args.raw_idea is None:
        raise SystemExit("Either --lineage-id or --raw-idea must be provided")
    confirm_flags = [
        args.confirm_mandate,
        args.confirm_data_ready,
        args.confirm_signal_ready,
        args.confirm_train_freeze,
        args.confirm_test_evidence,
        args.confirm_backtest_ready,
        args.confirm_holdout_validation,
    ]
    if sum(1 for flag in confirm_flags if flag) > 1:
        raise SystemExit("Use at most one confirmation flag at a time")

    status = run_research_session(
        outputs_root=args.outputs_root.resolve(),
        lineage_id=args.lineage_id,
        raw_idea=args.raw_idea,
        mandate_decision="CONFIRM_MANDATE" if args.confirm_mandate else None,
        data_ready_decision="CONFIRM_DATA_READY" if args.confirm_data_ready else None,
        signal_ready_decision="CONFIRM_SIGNAL_READY" if args.confirm_signal_ready else None,
        train_freeze_decision="CONFIRM_TRAIN_FREEZE" if args.confirm_train_freeze else None,
        test_evidence_decision="CONFIRM_TEST_EVIDENCE" if args.confirm_test_evidence else None,
        backtest_ready_decision="CONFIRM_BACKTEST_READY" if args.confirm_backtest_ready else None,
        holdout_validation_decision=(
            "CONFIRM_HOLDOUT_VALIDATION" if args.confirm_holdout_validation else None
        ),
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
