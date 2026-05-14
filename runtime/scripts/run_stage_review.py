#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_skillgen.review_engine import ReviewRuntimeConfigurationError, run_stage_review
from runtime.tools.review_resume_protocol import build_review_handoff_notice
from runtime.tools.stage_evaluator import StageEvaluatorConfigurationError


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the first-wave stage review engine.")
    parser.add_argument("--stage-dir", type=Path, default=None)
    parser.add_argument("--lineage-root", type=Path, default=None)
    parser.add_argument("--reviewer-id", default=None)
    parser.add_argument("--reviewer-role", default=None)
    parser.add_argument("--reviewer-session-id", default=None)
    parser.add_argument("--reviewer-mode", default=None)
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

    try:
        payload = run_stage_review(
            cwd=Path.cwd(),
            explicit_context=explicit_context,
            reviewer_identity=args.reviewer_id,
            reviewer_role=args.reviewer_role,
            reviewer_session_id=args.reviewer_session_id,
            reviewer_mode=args.reviewer_mode,
        )
    except (ReviewRuntimeConfigurationError, StageEvaluatorConfigurationError) as exc:
        raise SystemExit(str(exc)) from None
    print(f"Review loop outcome: {payload['review_loop_outcome']}")
    print(f"Final verdict: {payload['final_verdict']}")
    print(f"Stage: {payload['stage']}")
    print(f"Lineage: {payload['lineage_id']}")
    handoff_notice = build_review_handoff_notice(
        final_verdict=payload["final_verdict"],
        stage=payload["stage"],
    )
    if handoff_notice["recommended_skill"]:
        print(f"Recommended next skill: {handoff_notice['recommended_skill']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
