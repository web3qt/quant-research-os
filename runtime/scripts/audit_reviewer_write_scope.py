#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_skillgen.context_inference import build_stage_context, infer_review_context
from runtime.tools.review_skillgen.reviewer_write_scope_audit import run_reviewer_write_scope_audit


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit reviewer write scope before deterministic review closure.")
    parser.add_argument("--stage-dir", type=Path, default=None)
    parser.add_argument("--lineage-root", type=Path, default=None)
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
    payload = run_reviewer_write_scope_audit(stage_dir)
    print(f"Audit: {stage_dir / 'review' / 'result' / 'reviewer_write_scope_audit.yaml'}")
    print(f"Audit status: {payload['audit_status']}")
    if payload["audit_status"] != "PASS":
        print(f"Protected files changed: {payload['protected_files_changed']}")
        print(f"Protected files added: {payload['protected_files_added']}")
        print(f"Protected files removed: {payload['protected_files_removed']}")
        print(f"Unexpected result files: {payload['unexpected_result_files']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
