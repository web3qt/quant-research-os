#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.paper_to_spec import PaperToSpecError, materialize_strategy_spec_bundle  # noqa: E402


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PaperToSpecError(message)


def _parse_args() -> argparse.Namespace:
    parser = _ArgumentParser(description="Materialize a QROS paper-to-spec bundle.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--spec-file", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-kind", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _load_spec_payload(spec_file: Path) -> dict[str, object]:
    try:
        raw_payload = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PaperToSpecError(f"failed to parse spec file {spec_file}: {exc}") from exc
    except OSError as exc:
        raise PaperToSpecError(f"failed to read spec file {spec_file}: {exc}") from exc

    if not isinstance(raw_payload, dict):
        raise PaperToSpecError(f"spec file {spec_file} must be a YAML mapping")
    return raw_payload


def _render_text(result: dict[str, str]) -> str:
    lines = [
        "QROS Paper-to-Spec",
        f"Slug: {result['slug']}",
        f"Bundle: {result['bundle_root']}",
        f"Strategy spec: {result['strategy_spec_path']}",
        f"Strategy markdown: {result['strategy_markdown_path']}",
        f"Source manifest: {result['source_manifest_path']}",
    ]
    return "\n".join(lines)


def main() -> int:
    try:
        args = _parse_args()
        spec_payload = _load_spec_payload(args.spec_file)
        result = materialize_strategy_spec_bundle(
            outputs_root=args.outputs_root.resolve(),
            source_locator=args.source,
            source_kind=args.source_kind,
            source_title=args.title,
            spec_payload=spec_payload,
            requested_slug=args.slug,
        )
    except PaperToSpecError as exc:
        print(f"qros-paper-to-spec: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
