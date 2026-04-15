#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.idea_runtime import scaffold_idea_intake


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold 00_idea_intake artifacts for a lineage.")
    parser.add_argument("--lineage-root", type=Path, required=True)
    args = parser.parse_args()

    intake_dir = scaffold_idea_intake(args.lineage_root)
    print(f"Scaffolded idea intake at {intake_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
