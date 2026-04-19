#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_skillgen.review_preflight import run_review_preflight


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic review preflight before spawning a reviewer.")
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

    payload = run_review_preflight(
        cwd=Path.cwd(),
        explicit_context=explicit_context,
    )
    print(f"Stage: {payload['stage']}")
    print(f"Lineage: {payload['lineage_id']}")
    print(f"Status: {payload['status']}")
    if payload["content_findings"]:
        print("Content findings:")
        for item in payload["content_findings"]:
            print(f"- {item}")
    if payload["upstream_binding_findings"]:
        print("Upstream binding findings:")
        for item in payload["upstream_binding_findings"]:
            print(f"- {item}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
