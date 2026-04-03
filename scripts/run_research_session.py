#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.research_session import run_research_session
from tools.anti_drift import canonical_snapshot_from_session_context

EXIT_CODES = {
    "NONE": 0,
    "FREEZE_APPROVAL_MISSING": 2,
    "STAGE_PROGRAM_MISSING": 3,
    "STAGE_PROGRAM_INVALID": 4,
    "PROGRAM_EXECUTION_FAILED": 5,
    "PROVENANCE_MISSING": 5,
    "OUTPUTS_INVALID": 6,
    "REVIEW_PENDING": 7,
    "ADVERSARIAL_REVIEW_PENDING": 7,
    "AUTHOR_FIX_REQUIRED": 7,
    "REVIEW_CLOSURE_PENDING": 7,
    "FAILURE_HANDLER_REQUIRED": 8,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the QROS orchestrated research session.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", default=None)
    parser.add_argument("--raw-idea", default=None)
    parser.add_argument(
        "--confirm-intake",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may treat intake interview as complete.",
    )
    parser.add_argument(
        "--confirm-mandate",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build mandate outputs.",
    )
    parser.add_argument(
        "--confirm-data-ready",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build data_ready outputs.",
    )
    parser.add_argument(
        "--confirm-signal-ready",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build signal_ready outputs.",
    )
    parser.add_argument(
        "--confirm-train-freeze",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build train_freeze outputs.",
    )
    parser.add_argument(
        "--confirm-test-evidence",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build test_evidence outputs.",
    )
    parser.add_argument(
        "--confirm-backtest-ready",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build backtest_ready outputs.",
    )
    parser.add_argument(
        "--confirm-holdout-validation",
        action="store_true",
        help="Write an explicit approval artifact so the next session run may build holdout_validation outputs.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the session status as machine-readable JSON instead of the formatted text panel.",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Print the canonical anti-drift decision snapshot as JSON.",
    )
    return parser.parse_args()


def _status_payload(status) -> dict[str, object]:
    payload = asdict(status)
    payload["lineage_root"] = str(status.lineage_root)
    return payload


def _snapshot_payload(status, *, fixture_id: str | None) -> dict[str, object]:
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id=fixture_id or status.lineage_id,
        evidence_refs=("scripts/run_research_session.py",),
    )
    return snapshot.to_dict()


def _exit_code(status) -> int:
    return EXIT_CODES.get(status.blocking_reason_code, 0)


def _confirmation_feedback(args: argparse.Namespace, status) -> list[str]:
    lines: list[str] = []
    confirmation_label = None
    if args.confirm_intake:
        confirmation_label = "CONFIRM_IDEA_INTAKE"
    elif args.confirm_mandate:
        confirmation_label = "CONFIRM_MANDATE"
    elif args.confirm_data_ready:
        confirmation_label = "CONFIRM_DATA_READY"
    elif args.confirm_signal_ready:
        confirmation_label = "CONFIRM_SIGNAL_READY"
    elif args.confirm_train_freeze:
        confirmation_label = "CONFIRM_TRAIN_FREEZE"
    elif args.confirm_test_evidence:
        confirmation_label = "CONFIRM_TEST_EVIDENCE"
    elif args.confirm_backtest_ready:
        confirmation_label = "CONFIRM_BACKTEST_READY"
    elif args.confirm_holdout_validation:
        confirmation_label = "CONFIRM_HOLDOUT_VALIDATION"

    if confirmation_label is None:
        return lines

    lines.append(f"Confirmation recorded: {confirmation_label}")
    if args.confirm_intake:
        if status.current_stage == "mandate_confirmation_pending":
            lines.append("Confirmation advanced the workflow.")
        else:
            lines.append(
                "Confirmation did not advance the workflow because intake gate requirements are still incomplete."
            )
    return lines


def main() -> int:
    args = _parse_args()

    if args.lineage_id is None and args.raw_idea is None:
        raise SystemExit("Either --lineage-id or --raw-idea must be provided")
    confirm_flags = [
        args.confirm_intake,
        args.confirm_mandate,
        args.confirm_data_ready,
        args.confirm_signal_ready,
        args.confirm_train_freeze,
        args.confirm_test_evidence,
        args.confirm_backtest_ready,
        args.confirm_holdout_validation,
    ]
    if sum(1 for flag in confirm_flags if flag) > 1:
        raise SystemExit("Use at most one confirmation flag at a time")

    status = run_research_session(
        outputs_root=args.outputs_root.resolve(),
        lineage_id=args.lineage_id,
        raw_idea=args.raw_idea,
        idea_intake_decision="CONFIRM_IDEA_INTAKE" if args.confirm_intake else None,
        mandate_decision="CONFIRM_MANDATE" if args.confirm_mandate else None,
        data_ready_decision="CONFIRM_DATA_READY" if args.confirm_data_ready else None,
        signal_ready_decision="CONFIRM_SIGNAL_READY" if args.confirm_signal_ready else None,
        train_freeze_decision="CONFIRM_TRAIN_FREEZE" if args.confirm_train_freeze else None,
        test_evidence_decision="CONFIRM_TEST_EVIDENCE" if args.confirm_test_evidence else None,
        backtest_ready_decision="CONFIRM_BACKTEST_READY" if args.confirm_backtest_ready else None,
        holdout_validation_decision=(
            "CONFIRM_HOLDOUT_VALIDATION" if args.confirm_holdout_validation else None
        ),
    )

    if args.snapshot:
        print(json.dumps(_snapshot_payload(status, fixture_id=args.lineage_id), ensure_ascii=False, indent=2))
        return _exit_code(status)

    if args.json:
        print(json.dumps(_status_payload(status), ensure_ascii=False, indent=2))
        return _exit_code(status)

    for line in _confirmation_feedback(args, status):
        print(line)
    print(f"Lineage: {status.lineage_id}")
    print(f"Orchestrator: {status.current_orchestrator}")
    print(f"Current stage: {status.current_stage}")
    print(f"Current active skill: {status.current_skill}")
    print(f"Why this skill: {status.why_this_skill}")
    if status.current_route is not None:
        print(f"Research route: {status.current_route}")
    print(f"Stage status: {status.stage_status}")
    print(f"Blocking reason code: {status.blocking_reason_code}")
    if status.required_program_dir is not None:
        print(f"Required program dir: {status.required_program_dir}")
    if status.required_program_entrypoint is not None:
        print(f"Required program entrypoint: {status.required_program_entrypoint}")
    print(f"Program contract status: {status.program_contract_status}")
    print(f"Provenance status: {status.provenance_status}")
    if status.factor_role is not None:
        print(f"Factor role: {status.factor_role}")
    if status.factor_structure is not None:
        print(f"Factor structure: {status.factor_structure}")
    if status.portfolio_expression is not None:
        print(f"Portfolio expression: {status.portfolio_expression}")
    if status.neutralization_policy is not None:
        print(f"Neutralization policy: {status.neutralization_policy}")
    print(f"Gate status: {status.gate_status}")
    print(f"Terminal state: {status.current_stage.endswith('_review_complete')}")
    if status.review_verdict is not None:
        print(f"Review verdict: {status.review_verdict}")
    print(f"Requires failure handling: {status.requires_failure_handling}")
    if status.failure_stage is not None:
        print(f"Failure stage: {status.failure_stage}")
    if status.failure_reason_summary is not None:
        print(f"Failure reason: {status.failure_reason_summary}")
    if status.blocking_reason is not None:
        print(f"Blocking reason: {status.blocking_reason}")
    print(f"Next action: {status.next_action}")
    print(f"Resume hint: {status.resume_hint}")
    if status.why_now:
        print("Why now:")
        for item in status.why_now:
            print(f"- {item}")
    if status.open_risks:
        print("Open risks:")
        for item in status.open_risks:
            print(f"- {item}")
    if status.artifacts_written:
        print("Artifacts written:")
        for item in status.artifacts_written:
            print(f"- {item}")
    return _exit_code(status)


if __name__ == "__main__":
    raise SystemExit(main())
