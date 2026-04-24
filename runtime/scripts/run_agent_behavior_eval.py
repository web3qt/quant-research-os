#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.agent_behavior_eval import (  # noqa: E402
    evaluate_behavior_case,
    load_eval_cases,
    parse_transcript_jsonl,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manual QROS agent behavior eval cases.")
    parser.add_argument("--cases", type=Path, default=ROOT / "contracts" / "agent_eval" / "qros_agent_behavior_eval_cases.yaml")
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--agent-command-template")
    parser.add_argument("--transcript-path", type=Path)
    parser.add_argument("--runtime-status-path", type=Path)
    parser.add_argument("--lineage-root", type=Path)
    return parser.parse_args()


def _print_cases(cases: dict[str, dict]) -> None:
    print("Available agent behavior eval cases:")
    for case_id in sorted(cases):
        print(f"- {case_id}")


def main() -> int:
    args = _parse_args()
    cases = load_eval_cases(args.cases)
    if args.case_id not in cases:
        _print_cases(cases)
        print(f"unknown eval case: {args.case_id}", file=sys.stderr)
        return 2

    case = cases[args.case_id]
    if args.transcript_path is None and not args.agent_command_template:
        _print_cases(cases)
        print("agent command template is required for live eval", file=sys.stderr)
        return 2

    run_dir = args.work_root / args.case_id
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.txt"
    transcript_path = run_dir / "transcript.jsonl"
    result_path = run_dir / "result.yaml"
    prompt_path.write_text(case["prompt"], encoding="utf-8")

    if args.transcript_path is not None:
        shutil.copy2(args.transcript_path, transcript_path)
    else:
        _run_agent_command(args.agent_command_template, prompt_path=prompt_path, transcript_path=transcript_path, run_dir=run_dir)

    runtime_status = _load_runtime_status(args.runtime_status_path)
    lineage_root = args.lineage_root or (run_dir / "research_repo" / "outputs" / case["lineage_id"])
    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(transcript_path),
        lineage_root=lineage_root,
        runtime_status=runtime_status,
    )
    result_path.write_text(yaml.safe_dump(result.to_dict(), sort_keys=False, allow_unicode=True), encoding="utf-8")

    if not result.passed:
        for error in result.errors:
            print(error, file=sys.stderr)
        return 1
    print(f"agent behavior eval passed: {case['id']}")
    return 0


def _load_runtime_status(path: Path | None) -> dict | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _run_agent_command(command_template: str, *, prompt_path: Path, transcript_path: Path, run_dir: Path) -> None:
    command = command_template.format(
        prompt_path=str(prompt_path),
        transcript_path=str(transcript_path),
        work_dir=str(run_dir),
        prompt=prompt_path.read_text(encoding="utf-8"),
    )
    completed = subprocess.run(command, shell=True, cwd=run_dir, capture_output=True, text=True, check=False)
    if not transcript_path.exists():
        transcript_path.write_text(completed.stdout, encoding="utf-8")
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
