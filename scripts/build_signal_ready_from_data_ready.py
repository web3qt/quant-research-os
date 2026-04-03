#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml


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


def _require_confirmed_freeze_groups(lineage_root: Path) -> None:
    draft_path = lineage_root / "03_signal_ready" / "signal_ready_freeze_draft.yaml"
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    unconfirmed = sorted(name for name, group in groups.items() if not group.get("confirmed"))
    if unconfirmed:
        raise StageProgramRuntimeError(
            "FREEZE_APPROVAL_MISSING",
            "signal_ready_freeze_draft.yaml has unconfirmed groups: " + ", ".join(unconfirmed),
        )


def main() -> int:
    args = _parse_args()
    try:
        _require_confirmed_freeze_groups(args.lineage_root.resolve())
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
