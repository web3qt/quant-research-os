from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tools.idea_runtime import build_mandate_from_intake, scaffold_idea_intake
from tools.review_skillgen.review_engine import run_stage_review


SessionStage = Literal["idea_intake", "mandate_author", "mandate_review", "mandate_review_complete"]
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


@dataclass(frozen=True)
class SessionContext:
    lineage_id: str
    lineage_root: Path
    current_stage: SessionStage
    artifacts_written: list[str]
    gate_status: str
    next_action: str


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

    verdict_text = gate_path.read_text(encoding="utf-8")
    if "GO_TO_MANDATE" not in verdict_text:
        return "idea_intake"

    return "mandate_author"


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


def summarize_session_status(
    *,
    lineage_id: str,
    lineage_root: Path,
    current_stage: SessionStage,
    artifacts_written: list[str],
    gate_status: str,
    next_action: str,
) -> SessionContext:
    return SessionContext(
        lineage_id=lineage_id,
        lineage_root=lineage_root,
        current_stage=current_stage,
        artifacts_written=artifacts_written,
        gate_status=gate_status,
        next_action=next_action,
    )


def run_research_session(
    *,
    outputs_root: Path,
    lineage_id: str | None = None,
    raw_idea: str | None = None,
) -> SessionContext:
    lineage_root = resolve_lineage_root(outputs_root, lineage_id=lineage_id, raw_idea=raw_idea)
    lineage_root.mkdir(parents=True, exist_ok=True)

    artifacts_written: list[str] = []
    current_stage = detect_session_stage(lineage_root)

    if current_stage == "idea_intake":
        artifacts_written.extend(ensure_intake_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "mandate_author":
        artifacts_written.extend(build_mandate_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
    return summarize_session_status(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        current_stage=current_stage,
        artifacts_written=artifacts_written,
        gate_status=gate_status,
        next_action=next_action,
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
            verdict_text = intake_gate.read_text(encoding="utf-8")
            if "GO_TO_MANDATE" in verdict_text:
                return "GO_TO_MANDATE", "Build mandate artifacts"
            if "DROP" in verdict_text:
                return "DROP", "Reframe or terminate the idea"
        return "IN_PROGRESS", "Complete intake artifacts and qualification"

    if current_stage == "mandate_author":
        return "GO_TO_MANDATE", "Freeze mandate artifacts"

    if current_stage == "mandate_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run mandate review"

    return "REVIEW_COMPLETE", "Stop here until data_ready orchestration exists"
