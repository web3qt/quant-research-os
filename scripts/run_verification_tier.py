#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.verification_tiers import SUPPORTED_VERIFICATION_TIERS, pytest_command, repo_relative_existing_paths, tier_definition


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a named QROS verification tier.")
    parser.add_argument("--tier", choices=SUPPORTED_VERIFICATION_TIERS, required=True)
    parser.add_argument("--list", action="store_true", help="List supported tiers and their test files.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved pytest command without running it.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    parser.add_argument("--python", default=sys.executable, help="Python executable used for pytest invocation.")
    return parser.parse_args()


def _list_payload() -> dict[str, object]:
    return {
        "tiers": [
            {
                "name": tier,
                "description": tier_definition(tier).description,
                "tests": list(tier_definition(tier).test_paths),
            }
            for tier in SUPPORTED_VERIFICATION_TIERS
        ]
    }


def main() -> int:
    args = _parse_args()

    if args.list:
        payload = _list_payload()
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for tier_payload in payload["tiers"]:
                print(f"[{tier_payload['name']}] {tier_payload['description']}")
                for path in tier_payload["tests"]:
                    print(f"- {path}")
        return 0

    test_paths = repo_relative_existing_paths(ROOT, tier=args.tier)
    command = pytest_command(tier=args.tier, python_bin=args.python)
    payload = {
        "tier": args.tier,
        "description": tier_definition(args.tier).description,
        "cwd": str(ROOT),
        "tests": list(test_paths),
        "command": command,
    }

    if args.dry_run:
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(" ".join(command))
        return 0

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    result = subprocess.run(command, cwd=ROOT, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
