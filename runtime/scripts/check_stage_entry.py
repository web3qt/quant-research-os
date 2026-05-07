#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.stage_entry_guard import StageEntryGuardError, check_stage_entry  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether a stage-specific QROS skill may run now.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", default=None)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--lane", choices=("author", "review"), required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = check_stage_entry(
            outputs_root=args.outputs_root.resolve(),
            lineage_id=args.lineage_id,
            stage=args.stage,
            lane=args.lane,
        )
    except StageEntryGuardError as exc:
        if args.json:
            print(json.dumps(exc.result.to_dict(), ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(exc.result.message, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
