#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.anti_drift_scenarios import export_default_snapshots


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the blessed anti-drift snapshot scenarios.")
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    written = export_default_snapshots(args.output_dir)
    print(json.dumps({"output_dir": str(args.output_dir), "files": [str(path.name) for path in written]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
