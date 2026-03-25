#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.idea_runtime import build_mandate_from_intake


def main() -> int:
    parser = argparse.ArgumentParser(description="Build 01_mandate artifacts from qualified intake outputs.")
    parser.add_argument("--lineage-root", type=Path, required=True)
    args = parser.parse_args()

    try:
        mandate_dir = build_mandate_from_intake(args.lineage_root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Built mandate artifacts at {mandate_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
