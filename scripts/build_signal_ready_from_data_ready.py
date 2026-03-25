#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.signal_ready_runtime import build_signal_ready_from_data_ready


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build 03_signal_ready artifacts from data_ready with confirmed signal_ready freeze groups."
    )
    parser.add_argument("--lineage-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    signal_ready_dir = build_signal_ready_from_data_ready(args.lineage_root.resolve())
    print(f"Built signal_ready artifacts in {signal_ready_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
