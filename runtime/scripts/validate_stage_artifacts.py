#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.artifact_contract_runtime import (  # noqa: E402
    ArtifactContractError,
    load_artifact_contract,
    validate_stage_artifacts,
)
from runtime.tools.data_implementation_contract_runtime import validate_data_implementation_contract  # noqa: E402


DATA_IMPLEMENTATION_STAGE_ROUTES = {
    "csf_data_ready": "cross_sectional_factor",
    "tss_data_ready": "time_series_signal",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate QROS stage artifact shape against its contract.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", required=True)
    parser.add_argument("--stage", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        contract = load_artifact_contract(args.stage)
    except ArtifactContractError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    stage_dir = args.outputs_root / args.lineage_id / str(contract["stage_dir"])
    result = validate_stage_artifacts(stage_dir, contract)
    if not result.valid:
        for error in result.errors:
            print(error, file=sys.stderr)
        return 1

    route = DATA_IMPLEMENTATION_STAGE_ROUTES.get(args.stage)
    if route is not None:
        lineage_root = args.outputs_root / args.lineage_id
        implementation_result = validate_data_implementation_contract(lineage_root, args.stage, route)
        if not implementation_result.valid:
            reason_codes = ", ".join(implementation_result.reason_codes) or "DATA_IMPL_CONTRACT_INVALID"
            for error in implementation_result.errors:
                print(f"{reason_codes}: {error}", file=sys.stderr)
            return 1

    print(f"{args.stage} artifact shape valid: {stage_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
