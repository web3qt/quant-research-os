#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stage_display_runtime import StageDisplayError, write_stage_display_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the generic qros-stage-display workflow for a supported frozen stage.",
    )
    parser.add_argument("--stage-id", required=True, help="Registered stage id. v1 supports only csf_data_ready.")
    parser.add_argument("--lineage-root", type=Path, default=None)
    parser.add_argument("--outputs-root", type=Path, default=None)
    parser.add_argument("--lineage-id", default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory; defaults to <lineage_root>/reports/stage_display.",
    )
    parser.add_argument(
        "--renderer-command",
        default=None,
        help="Optional command override for the required subagent render step. Useful for tests and controlled wrappers.",
    )
    parser.add_argument("--json", action="store_true", help="Print a machine-readable artifact summary.")
    return parser.parse_args()


def _resolve_lineage_root(args: argparse.Namespace) -> Path:
    if args.lineage_root is not None:
        return args.lineage_root.resolve()
    if args.outputs_root is None or args.lineage_id is None:
        raise SystemExit("Either --lineage-root or both --outputs-root and --lineage-id are required.")
    return (args.outputs_root / args.lineage_id).resolve()


def main() -> int:
    args = _parse_args()
    lineage_root = _resolve_lineage_root(args)
    try:
        result = write_stage_display_report(
            lineage_root=lineage_root,
            stage_id=args.stage_id,
            output_dir=args.output_dir.resolve() if args.output_dir is not None else None,
            renderer_command=args.renderer_command,
        )
    except StageDisplayError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
