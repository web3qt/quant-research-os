#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.research_session import run_research_session
from tools.research_session_reflection import build_data_ready_reflection_payload, reflection_payload_to_dict
from tools.stage_summary_html import render_data_ready_summary_html, write_subagent_bundle


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a data_ready HTML summary from deterministic reflection payload."
    )
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", required=True)
    parser.add_argument(
        "--renderer",
        choices=("deterministic", "subagent-bundle", "both"),
        default="both",
        help="Choose deterministic HTML, subagent handoff bundle, or both.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory; defaults to <lineage_root>/reports.",
    )
    parser.add_argument("--json", action="store_true", help="Print a machine-readable summary of written artifacts.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    status = run_research_session(
        outputs_root=args.outputs_root.resolve(),
        lineage_id=args.lineage_id,
        raw_idea=None,
    )
    lineage_root = status.lineage_root
    payload = build_data_ready_reflection_payload(
        lineage_root=lineage_root,
        current_stage=status.current_stage,
        current_route=status.current_route,
    )
    if payload is None:
        raise SystemExit(
            "data_ready HTML export is only available for time_series_signal lineages at signal_ready_confirmation_pending."
        )

    payload_dict = reflection_payload_to_dict(payload)
    output_dir = args.output_dir.resolve() if args.output_dir is not None else lineage_root / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    payload_path = output_dir / "data_ready_summary.payload.json"
    payload_path.write_text(json.dumps(payload_dict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result: dict[str, object] = {
        "lineage_root": str(lineage_root),
        "current_stage": status.current_stage,
        "current_route": status.current_route,
        "renderer": args.renderer,
        "payload_path": str(payload_path),
        "codex_time_dependency_only": True,
    }

    if args.renderer in {"deterministic", "both"}:
        html_path = output_dir / "data_ready_summary.deterministic.html"
        html_path.write_text(render_data_ready_summary_html(payload_dict) + "\n", encoding="utf-8")
        result["deterministic_html_path"] = str(html_path)

    if args.renderer in {"subagent-bundle", "both"}:
        subagent_dir = output_dir / "data_ready_summary.subagent_bundle"
        target_html_path = output_dir / "data_ready_summary.subagent.html"
        bundle = write_subagent_bundle(
            bundle_dir=subagent_dir,
            payload=payload_dict,
            output_html_path=target_html_path,
        )
        result["subagent_bundle_dir"] = str(bundle["bundle_dir"])
        result["subagent_bundle_payload_path"] = str(bundle["payload"])
        result["subagent_prompt_path"] = str(bundle["prompt"])
        result["subagent_output_path_file"] = str(bundle["output_path"])
        result["subagent_output_html_path"] = str(target_html_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
