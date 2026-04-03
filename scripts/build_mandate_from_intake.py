#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.lineage_program_runtime import StageProgramRuntimeError, StageProgramSpec, invoke_stage_if_admitted


def main() -> int:
    parser = argparse.ArgumentParser(description="Build 01_mandate artifacts from qualified intake outputs.")
    parser.add_argument("--lineage-root", type=Path, required=True)
    args = parser.parse_args()

    try:
        result = invoke_stage_if_admitted(
            args.lineage_root.resolve(),
            StageProgramSpec(
                stage_id="mandate",
                route="route_neutral",
                stage_dir_name="01_mandate",
                required_outputs=(
                    "mandate.md",
                    "research_scope.md",
                    "research_route.yaml",
                    "time_split.json",
                    "parameter_grid.yaml",
                    "run_config.toml",
                    "artifact_catalog.md",
                    "field_dictionary.md",
                ),
            ),
        )
    except StageProgramRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Built mandate artifacts at {result.stage_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
