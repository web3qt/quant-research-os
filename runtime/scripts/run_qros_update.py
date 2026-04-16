#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.update_runtime import DEFAULT_BRANCH, DEFAULT_REPO_URL, UpdateError, run_qros_update


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update QROS to the latest published main and refresh the current repo-local runtime.")
    parser.add_argument("--cwd", type=Path, default=None)
    parser.add_argument("--source-repo", type=Path, default=None)
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    target_cwd = (args.cwd or Path.cwd()).resolve()

    try:
        result = run_qros_update(
            target_cwd=target_cwd,
            home=Path.home(),
            explicit_source_repo=args.source_repo.resolve() if args.source_repo is not None else None,
            repo_root_fallback=ROOT,
            repo_url=args.repo_url,
            branch=args.branch,
        )
    except UpdateError as exc:
        print(f"QROS update failed: {exc}", file=sys.stderr)
        return 1

    print(f"QROS updated to {result.source_git_commit or 'unknown-commit'}")
    print(f"Source repo: {result.source_repo}")
    print(f"Global manifest: {result.global_manifest_path}")
    print(f"Repo-local manifest: {result.local_manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
