#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.paper_test_evidence_spec_runtime import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    validate_paper_test_evidence_spec,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a QROS paper_test_evidence_spec.yaml artifact.")
    parser.add_argument("--spec-path", type=Path, required=True)
    parser.add_argument("--contract-path", type=Path, default=DEFAULT_CONTRACT_PATH)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = validate_paper_test_evidence_spec(args.spec_path, args.contract_path)
    if not result.valid:
        for reason_code, message in result.findings:
            print(f"{reason_code}: {message}", file=sys.stderr)
        return 1

    print(f"paper_test_evidence_spec valid: {result.spec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
