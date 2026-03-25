#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.data_ready_runtime import build_data_ready_from_mandate


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build 02_data_ready artifacts from a mandate with confirmed data_ready freeze groups."
    )
    parser.add_argument("--lineage-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    data_ready_dir = build_data_ready_from_mandate(args.lineage_root.resolve())
    print(f"Built data_ready artifacts in {data_ready_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
