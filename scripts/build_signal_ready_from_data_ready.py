#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.lineage_program_runtime import StageProgramRuntimeError, StageProgramSpec, invoke_stage_if_admitted


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build 03_signal_ready artifacts from data_ready with confirmed signal_ready freeze groups."
    )
    parser.add_argument("--lineage-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = invoke_stage_if_admitted(
            args.lineage_root.resolve(),
            StageProgramSpec(
                stage_id="signal_ready",
                route="time_series_signal",
                stage_dir_name="03_signal_ready",
                required_outputs=(
                    "param_manifest.csv",
                    "params",
                    "signal_coverage.csv",
                    "signal_coverage.md",
                    "signal_coverage_summary.md",
                    "signal_contract.md",
                    "signal_fields_contract.md",
                    "signal_gate_decision.md",
                    "artifact_catalog.md",
                    "field_dictionary.md",
                ),
            ),
        )
    except StageProgramRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Built signal_ready artifacts in {result.stage_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
