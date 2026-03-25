from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml

from tools.idea_runtime import (
    MANDATE_FREEZE_DRAFT_FILE,
    MANDATE_FREEZE_GROUP_ORDER,
    build_mandate_from_intake,
    scaffold_idea_intake,
)
from tools.review_skillgen.review_engine import run_stage_review


SessionStage = Literal[
    "idea_intake",
    "mandate_confirmation_pending",
    "mandate_author",
    "mandate_review",
    "mandate_review_complete",
]
MandateTransitionDecision = Literal["CONFIRM_MANDATE", "HOLD", "REFRAME"]
MANDATE_REQUIRED_OUTPUTS = [
    "mandate.md",
    "research_scope.md",
    "time_split.json",
    "parameter_grid.yaml",
    "run_config.toml",
    "artifact_catalog.md",
    "field_dictionary.md",
]
MANDATE_CLOSURE_OUTPUTS = [
    "latest_review_pack.yaml",
    "stage_gate_review.yaml",
    "stage_completion_certificate.yaml",
]
MANDATE_TRANSITION_APPROVAL_FILE = "mandate_transition_approval.yaml"


@dataclass(frozen=True)
class SessionContext:
    lineage_id: str
    lineage_root: Path
    current_stage: SessionStage
    artifacts_written: list[str]
    gate_status: str
    next_action: str
    why_now: list[str]
    open_risks: list[str]


def slugify_idea(raw_idea: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", raw_idea.strip().lower())
    normalized = normalized.strip("_")
    if not normalized:
        raise ValueError("raw_idea must contain at least one alphanumeric character")
    return normalized


def resolve_lineage_root(outputs_root: Path, lineage_id: str | None, raw_idea: str | None) -> Path:
    if lineage_id:
        return outputs_root / lineage_id
    if raw_idea:
        return outputs_root / slugify_idea(raw_idea)
    raise ValueError("Either lineage_id or raw_idea must be provided")


def detect_session_stage(lineage_root: Path) -> SessionStage:
    intake_dir = lineage_root / "00_idea_intake"
    mandate_dir = lineage_root / "01_mandate"

    if _mandate_outputs_complete(mandate_dir):
        if _mandate_closure_complete(mandate_dir):
            return "mandate_review_complete"
        return "mandate_review"

    if not intake_dir.exists():
        return "idea_intake"

    gate_path = intake_dir / "idea_gate_decision.yaml"
    if not gate_path.exists():
        return "idea_intake"

    gate_decision = _read_yaml(gate_path)
    if gate_decision.get("verdict") != "GO_TO_MANDATE":
        return "idea_intake"

    approval_decision = read_mandate_transition_decision(lineage_root)
    if approval_decision == "CONFIRM_MANDATE" and next_mandate_freeze_group(lineage_root) is None:
        return "mandate_author"
    if approval_decision == "REFRAME":
        return "idea_intake"

    return "mandate_confirmation_pending"


def ensure_intake_scaffold(lineage_root: Path) -> list[str]:
    intake_dir = lineage_root / "00_idea_intake"
    if intake_dir.exists():
        return []

    scaffold_idea_intake(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in intake_dir.iterdir())


def build_mandate_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "mandate_author":
        return []

    mandate_dir = build_mandate_from_intake(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in mandate_dir.iterdir())


def run_mandate_review_if_ready(lineage_root: Path) -> dict[str, object] | None:
    if detect_session_stage(lineage_root) != "mandate_review":
        return None

    mandate_dir = lineage_root / "01_mandate"
    if not (mandate_dir / "review_findings.yaml").exists():
        return None

    return run_stage_review(
        explicit_context={
            "lineage_id": lineage_root.name,
            "lineage_root": lineage_root,
            "stage": "mandate",
            "stage_dir": mandate_dir,
        }
    )


def write_mandate_transition_decision(
    lineage_root: Path,
    *,
    decision: MandateTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    gate_decision = _read_yaml(approval_path.parent / "idea_gate_decision.yaml")
    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_gate_verdict": gate_decision.get("verdict", ""),
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def read_mandate_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_MANDATE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def session_transition_summary(lineage_root: Path) -> tuple[list[str], list[str]]:
    gate_path = lineage_root / "00_idea_intake" / "idea_gate_decision.yaml"
    if not gate_path.exists():
        return [], []

    gate_decision = _read_yaml(gate_path)
    why_now = [str(item) for item in gate_decision.get("why", []) if item]
    open_risks = [str(item) for item in gate_decision.get("required_reframe_actions", []) if item]
    if not open_risks and gate_decision.get("rollback_target"):
        open_risks = [f"rollback_target remains {gate_decision['rollback_target']}"]
    return why_now, open_risks


def next_mandate_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "00_idea_intake" / MANDATE_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return MANDATE_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in MANDATE_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def summarize_session_status(
    *,
    lineage_id: str,
    lineage_root: Path,
    current_stage: SessionStage,
    artifacts_written: list[str],
    gate_status: str,
    next_action: str,
    why_now: list[str] | None = None,
    open_risks: list[str] | None = None,
) -> SessionContext:
    return SessionContext(
        lineage_id=lineage_id,
        lineage_root=lineage_root,
        current_stage=current_stage,
        artifacts_written=artifacts_written,
        gate_status=gate_status,
        next_action=next_action,
        why_now=why_now or [],
        open_risks=open_risks or [],
    )


def run_research_session(
    *,
    outputs_root: Path,
    lineage_id: str | None = None,
    raw_idea: str | None = None,
    mandate_decision: MandateTransitionDecision | None = None,
) -> SessionContext:
    lineage_root = resolve_lineage_root(outputs_root, lineage_id=lineage_id, raw_idea=raw_idea)
    lineage_root.mkdir(parents=True, exist_ok=True)

    artifacts_written: list[str] = []
    if mandate_decision is not None:
        artifacts_written.append(
            write_mandate_transition_decision(lineage_root, decision=mandate_decision)
        )

    current_stage = detect_session_stage(lineage_root)

    if current_stage == "idea_intake":
        artifacts_written.extend(ensure_intake_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "mandate_author":
        artifacts_written.extend(build_mandate_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
    why_now, open_risks = session_transition_summary(lineage_root)
    return summarize_session_status(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        current_stage=current_stage,
        artifacts_written=artifacts_written,
        gate_status=gate_status,
        next_action=next_action,
        why_now=why_now,
        open_risks=open_risks,
    )


def _mandate_outputs_complete(mandate_dir: Path) -> bool:
    return all((mandate_dir / name).exists() for name in MANDATE_REQUIRED_OUTPUTS)


def _mandate_closure_complete(mandate_dir: Path) -> bool:
    if (mandate_dir / "stage_completion_certificate.yaml").exists():
        return True
    return all((mandate_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str]:
    intake_gate = lineage_root / "00_idea_intake" / "idea_gate_decision.yaml"
    if current_stage == "idea_intake":
        if intake_gate.exists():
            verdict = _read_yaml(intake_gate).get("verdict", "")
            if verdict == "GO_TO_MANDATE":
                return "GO_TO_MANDATE_PENDING_CONFIRMATION", "Await explicit CONFIRM_MANDATE"
            if verdict == "DROP":
                return "DROP", "Reframe or terminate the idea"
        return "IN_PROGRESS", "Complete intake artifacts and qualification"

    if current_stage == "mandate_confirmation_pending":
        next_group = next_mandate_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_MANDATE_PENDING_CONFIRMATION", f"Complete mandate freeze group: {next_group}"
        decision = read_mandate_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_MANDATE_ON_HOLD", "Wait for explicit CONFIRM_MANDATE"
        return "GO_TO_MANDATE_PENDING_CONFIRMATION", "Run with --confirm-mandate or reply CONFIRM_MANDATE <lineage_id>"

    if current_stage == "mandate_author":
        return "GO_TO_MANDATE_CONFIRMED", "Freeze mandate artifacts"

    if current_stage == "mandate_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run mandate review"

    return "REVIEW_COMPLETE", "Stop here until data_ready orchestration exists"


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _approval_path(lineage_root: Path) -> Path:
    return lineage_root / "00_idea_intake" / MANDATE_TRANSITION_APPROVAL_FILE
