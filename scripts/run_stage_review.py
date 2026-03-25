#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.review_skillgen.review_engine import run_stage_review


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the first-wave stage review engine.")
    parser.add_argument("--stage-dir", type=Path, default=None)
    parser.add_argument("--lineage-root", type=Path, default=None)
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

    payload = run_stage_review(cwd=Path.cwd(), explicit_context=explicit_context)
    print(f"Final verdict: {payload['final_verdict']}")
    print(f"Stage: {payload['stage']}")
    print(f"Lineage: {payload['lineage_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
