#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.review_governance_runtime import sync_review_governance_from_stage


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update review governance candidates from a stage governance signal")
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--lineage-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = sync_review_governance_from_stage(stage_dir=args.stage_dir.resolve(), lineage_root=args.lineage_root.resolve())
    print(f"Ledger appended: {result['ledger_appended']}")
    print(f"Candidates updated: {len(result['candidates_updated'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
