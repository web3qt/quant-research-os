#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff, reset_review_cycle  # noqa: E402
from runtime.tools.review_skillgen.review_preflight import run_review_preflight  # noqa: E402
from runtime.tools.review_skillgen.review_engine import ReviewRuntimeConfigurationError  # noqa: E402
from runtime.tools.stage_evaluator import StageEvaluatorConfigurationError  # noqa: E402


def _resolve_host_from_manifest(cwd: Path) -> str:
    manifest_path = cwd / ".qros" / "install-manifest.json"
    if manifest_path.exists():
        try:
            import json
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            host = manifest.get("host")
            if host in ("codex", "claude-code"):
                return host
        except Exception:
            pass
    return "codex"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare QROS review cycles.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="Prepare request, receipt, handoff prompt, and closer command.")
    prepare.add_argument("--stage-dir", type=Path, default=None)
    prepare.add_argument("--lineage-root", type=Path, default=None)
    prepare.add_argument("--host", choices=["codex", "claude-code"], default=None)
    prepare.add_argument("--reviewer-id", default=os.environ.get("QROS_REVIEWER_ID", "codex-reviewer"))
    prepare.add_argument(
        "--reviewer-session-id",
        default=os.environ.get("QROS_REVIEWER_SESSION_ID", "spawned-reviewer"),
    )
    prepare.add_argument("--launcher-session-id", default=os.environ.get("QROS_LAUNCHER_SESSION_ID", "local-launcher-session"))
    prepare.add_argument("--launcher-thread-id", default=os.environ.get("QROS_LAUNCHER_THREAD_ID", "local-launcher-thread"))
    prepare.add_argument("--reviewer-agent-id", required=True)
    prepare.add_argument("--json", action="store_true")

    validate = subparsers.add_parser("validate", help="Validate protected review state without writing changes.")
    validate.add_argument("--stage-dir", type=Path, required=True)
    validate.add_argument("--lineage-root", type=Path, required=True)
    validate.add_argument("--json", action="store_true")

    reset = subparsers.add_parser("reset", help="Archive stale active review cycle.")
    reset.add_argument("--stage-dir", type=Path, required=True)
    reset.add_argument("--lineage-root", type=Path, required=True)
    reset.add_argument("--archive-stale-cycle", action="store_true", required=True)
    reset.add_argument("--json", action="store_true")
    return parser.parse_args()


def _explicit_context(args: argparse.Namespace) -> dict[str, Path] | None:
    if args.stage_dir is None and args.lineage_root is None:
        return None
    if args.stage_dir is None or args.lineage_root is None:
        raise SystemExit("--stage-dir and --lineage-root must be provided together")
    return {
        "stage_dir": args.stage_dir.resolve(),
        "lineage_root": args.lineage_root.resolve(),
    }


def _json_safe(payload: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, Path):
            safe[key] = str(value)
        else:
            safe[key] = value
    return safe


def main() -> int:
    args = _parse_args()
    cwd = Path.cwd()
    if args.command == "validate":
        payload = run_review_preflight(
            cwd=cwd,
            explicit_context={
                "stage_dir": args.stage_dir.resolve(),
                "lineage_root": args.lineage_root.resolve(),
            },
        )
        if args.json:
            print(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2))
        else:
            print(f"Stage: {payload['stage']}")
            print(f"Lineage: {payload['lineage_id']}")
            print(f"Status: {payload['status']}")
        return 0 if payload["status"] == "PASS" else 1

    if args.command == "reset":
        payload = reset_review_cycle(stage_dir=args.stage_dir, reason="stale")
        if args.json:
            print(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2))
        else:
            print(f"Stage dir: {payload['stage_dir']}")
            print(f"Review cycle: {payload.get('review_cycle_id', 'none')}")
            print("Archived paths:")
            for item in payload["archived_paths"]:
                print(f"- {item}")
            print(f"Next action: {payload['next_action']}")
        return 0

    if args.command != "prepare":
        raise SystemExit(f"unsupported command: {args.command}")
    host = args.host or _resolve_host_from_manifest(cwd)
    try:
        payload = prepare_review_cycle_for_handoff(
            cwd=cwd,
            explicit_context=_explicit_context(args),
            reviewer_identity=args.reviewer_id,
            reviewer_session_id=args.reviewer_session_id,
            launcher_session_id=args.launcher_session_id,
            launcher_thread_id=args.launcher_thread_id,
            reviewer_agent_id=args.reviewer_agent_id,
            host=host,
        )
    except (ReviewRuntimeConfigurationError, StageEvaluatorConfigurationError) as exc:
        raise SystemExit(str(exc)) from None
    if args.json:
        print(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2))
        return 0

    print(f"Host: {host}")
    print(f"Lineage: {payload['lineage_id']}")
    print(f"Stage: {payload['stage']}")
    print(f"Review cycle: {payload['review_cycle_id']}")
    print(f"Request: {payload['request_path']}")
    print(f"Receipt: {payload['receipt_path']}")
    print()
    print("Reviewer handoff prompt:")
    print(payload["reviewer_handoff_prompt"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
