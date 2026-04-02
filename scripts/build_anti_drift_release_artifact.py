#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_release_artifact(
    *,
    nightly_gate_summary: dict[str, Any],
    generator_fresh: bool,
    classification_baseline_matches: bool,
    snapshot_cli_ok: bool,
) -> dict[str, Any]:
    failure_reasons: list[str] = []
    if nightly_gate_summary.get("status") != "PASS":
        failure_reasons.append("nightly_gate_failed")
    if not generator_fresh:
        failure_reasons.append("generated_skills_stale")
    if not classification_baseline_matches:
        failure_reasons.append("classification_baseline_mismatch")
    if not snapshot_cli_ok:
        failure_reasons.append("snapshot_cli_failed")

    return {
        "artifact": "anti_drift_release",
        "status": "PASS" if not failure_reasons else "FAIL",
        "nightly_gate_status": nightly_gate_summary.get("status"),
        "generator_fresh": generator_fresh,
        "classification_baseline_matches": classification_baseline_matches,
        "snapshot_cli_ok": snapshot_cli_ok,
        "failure_reasons": failure_reasons,
    }


def _parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes", "on"}:
        return True
    if lowered in {"false", "0", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected boolean-like value, got: {value}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a machine-readable anti-drift release artifact.")
    parser.add_argument("--nightly-gate-json", type=Path, required=True)
    parser.add_argument("--generator-fresh", type=_parse_bool, required=True)
    parser.add_argument("--classification-baseline-matches", type=_parse_bool, required=True)
    parser.add_argument("--snapshot-cli-ok", type=_parse_bool, required=True)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    nightly_gate_summary = json.loads(args.nightly_gate_json.read_text(encoding="utf-8"))
    artifact = build_release_artifact(
        nightly_gate_summary=nightly_gate_summary,
        generator_fresh=args.generator_fresh,
        classification_baseline_matches=args.classification_baseline_matches,
        snapshot_cli_ok=args.snapshot_cli_ok,
    )
    payload = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if artifact["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
