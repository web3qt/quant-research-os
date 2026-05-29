#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.paper_to_spec_baseline import (  # noqa: E402
    BaselineScaffoldError,
    scaffold_baseline_from_spec,
)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise BaselineScaffoldError(message)


def _parse_args() -> argparse.Namespace:
    parser = _ArgumentParser(
        description="Scaffold a deterministic paper-to-spec baseline bundle."
    )
    parser.add_argument("--target-repo", type=Path, required=True)
    parser.add_argument("--spec-path", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _render_text(result: dict[str, str]) -> str:
    return "\n".join(
        [
            "QROS Paper-to-Spec Baseline",
            f"Layout: {result['layout_mode']}",
            f"Bundle root: {result['bundle_root']}",
            f"Run entrypoint: {result['run_entrypoint']}",
            f"Smoke test: {result['smoke_test_path']}",
        ]
    )


def main() -> int:
    try:
        args = _parse_args()
        result = scaffold_baseline_from_spec(
            target_repo=args.target_repo.resolve(),
            spec_path=args.spec_path.resolve(),
            prefer_repo_native=True,
        )
    except BaselineScaffoldError as exc:
        print(f"qros-paper-to-spec-baseline: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
