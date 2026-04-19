#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.stage_evaluator import evaluate_stage, write_stage_evaluator_artifacts  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a QROS stage and optionally write evaluator artifacts.")
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--lineage-root", type=Path, default=None)
    parser.add_argument("--write", action="store_true", help="Write stage_evaluator.json and stage_evaluator_results.jsonl")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.write:
        payload = write_stage_evaluator_artifacts(
            args.stage_dir.resolve(),
            lineage_root=args.lineage_root.resolve() if args.lineage_root is not None else None,
        )
    else:
        payload = evaluate_stage(
            args.stage_dir.resolve(),
            lineage_root=args.lineage_root.resolve() if args.lineage_root is not None else None,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
