#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_files(root: Path) -> dict[str, Path]:
    if root.is_file():
        return {root.name: root}
    return {
        str(path.relative_to(root)): path
        for path in sorted(root.rglob("*.json"))
        if path.is_file()
        and path.name != "baseline_manifest.json"
    }


def compare_json_roots(baseline_root: Path, current_root: Path) -> dict[str, Any]:
    input_errors: list[str] = []
    if not baseline_root.exists():
        input_errors.append("baseline_root_missing")
    if not current_root.exists():
        input_errors.append("current_root_missing")

    baseline_files = _json_files(baseline_root) if baseline_root.exists() else {}
    current_files = _json_files(current_root) if current_root.exists() else {}

    if baseline_root.exists() and not baseline_files:
        input_errors.append("baseline_root_empty")
    if current_root.exists() and not current_files:
        input_errors.append("current_root_empty")

    missing_files = sorted(set(baseline_files) - set(current_files))
    added_files = sorted(set(current_files) - set(baseline_files))
    changed_files: dict[str, dict[str, Any]] = {}

    for rel_path in sorted(set(baseline_files) & set(current_files)):
        baseline_payload = _load_json(baseline_files[rel_path])
        current_payload = _load_json(current_files[rel_path])
        if baseline_payload != current_payload:
            changed_files[rel_path] = {
                "baseline": baseline_payload,
                "current": current_payload,
            }

    return {
        "baseline_root": str(baseline_root),
        "current_root": str(current_root),
        "matches": not (input_errors or missing_files or added_files or changed_files),
        "input_errors": input_errors,
        "missing_files": missing_files,
        "added_files": added_files,
        "changed_files": changed_files,
    }


def promote_json_roots(
    current_root: Path,
    baseline_root: Path,
    *,
    label: str,
    source_note: str | None = None,
) -> dict[str, Any]:
    current_files = _json_files(current_root)
    baseline_root.mkdir(parents=True, exist_ok=True)

    promoted_files: list[str] = []
    for rel_path, src in current_files.items():
        dest = baseline_root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        promoted_files.append(rel_path)

    manifest = {
        "label": label,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "source_note": source_note,
        "current_root": str(current_root),
        "baseline_root": str(baseline_root),
        "files": promoted_files,
    }
    (baseline_root / "baseline_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage anti-drift JSON baselines.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="Compare current JSON payloads against a baseline root.")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--current", type=Path, required=True)

    promote = subparsers.add_parser("promote", help="Promote current JSON payloads into a baseline root.")
    promote.add_argument("--current", type=Path, required=True)
    promote.add_argument("--baseline", type=Path, required=True)
    promote.add_argument("--label", required=True)
    promote.add_argument("--source-note", default=None)

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "compare":
        payload = compare_json_roots(args.baseline, args.current)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["matches"] else 1

    manifest = promote_json_roots(
        args.current,
        args.baseline,
        label=args.label,
        source_note=args.source_note,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
