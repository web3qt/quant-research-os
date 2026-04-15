#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.lineage_program_runtime import StageProgramRuntimeError, StageProgramSpec, invoke_stage_if_admitted


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build 02_data_ready artifacts from a mandate with confirmed data_ready freeze groups."
    )
    parser.add_argument("--lineage-root", type=Path, required=True)
    return parser.parse_args()


def _require_confirmed_freeze_groups(lineage_root: Path) -> None:
    draft_path = lineage_root / "02_data_ready" / "author" / "draft" / "data_ready_freeze_draft.yaml"
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    unconfirmed = sorted(name for name, group in groups.items() if not group.get("confirmed"))
    if unconfirmed:
        raise StageProgramRuntimeError(
            "FREEZE_APPROVAL_MISSING",
            "data_ready_freeze_draft.yaml has unconfirmed groups: " + ", ".join(unconfirmed),
        )


def main() -> int:
    args = _parse_args()
    try:
        _require_confirmed_freeze_groups(args.lineage_root.resolve())
        result = invoke_stage_if_admitted(
            args.lineage_root.resolve(),
            StageProgramSpec(
                stage_id="data_ready",
                route="time_series_signal",
                stage_dir_name="02_data_ready",
                required_outputs=(
                    "aligned_bars",
                    "rolling_stats",
                    "pair_stats",
                    "benchmark_residual",
                    "topic_basket_state",
                    "qc_report.parquet",
                    "dataset_manifest.json",
                    "validation_report.md",
                    "data_contract.md",
                    "dedupe_rule.md",
                    "universe_summary.md",
                    "universe_exclusions.csv",
                    "universe_exclusions.md",
                    "data_ready_gate_decision.md",
                    "run_manifest.json",
                    "rebuild_data_ready.py",
                    "artifact_catalog.md",
                    "field_dictionary.md",
                ),
            ),
        )
    except StageProgramRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Built data_ready artifacts in {result.stage_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
