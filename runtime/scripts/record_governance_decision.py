#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_governance_runtime import capture_governance_decision, record_governance_decision


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture or record a governance decision for an existing candidate.")
    parser.add_argument("--governance-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--decision", required=True, help="approve/approved, reject/rejected, defer/deferred")
    parser.add_argument("--decider", default="user")
    parser.add_argument("--decider-mode", default="interactive")
    parser.add_argument("--agent-id", default="codex")
    parser.add_argument("--note", default=None)
    parser.add_argument("--planned-repo-change", default=None)
    parser.add_argument(
        "--action",
        choices=("capture", "record"),
        default="record",
        help="capture writes governance/pending_decisions; record writes governance/decisions and updates the candidate.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    governance_root = args.governance_root.resolve()

    if args.action == "capture":
        path = capture_governance_decision(
            governance_root=governance_root,
            candidate_id=args.candidate_id,
            decision_outcome=args.decision,
            captured_by_agent=args.agent_id,
            decider_identity=args.decider,
            decider_mode=args.decider_mode,
            decision_note=args.note,
            planned_repo_change=args.planned_repo_change,
        )
        print(
            json.dumps(
                {
                    "action": "capture",
                    "candidate_id": args.candidate_id,
                    "pending_decision_path": str(path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    result = record_governance_decision(
        governance_root=governance_root,
        candidate_id=args.candidate_id,
        decision_outcome=args.decision,
        decider_identity=args.decider,
        decider_mode=args.decider_mode,
        decision_note=args.note,
        planned_repo_change=args.planned_repo_change,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
