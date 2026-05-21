from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.idea_runtime import _blank_mandate_freeze_draft


QUALIFICATION_DIMENSIONS = (
    "observability",
    "mechanism_plausibility",
    "tradeability",
    "data_feasibility",
    "scoping_clarity",
    "distinctiveness",
)


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def blank_mandate_admission(lineage_id: str, raw_idea: str = "") -> dict[str, Any]:
    return {
        "lineage_id": lineage_id,
        "raw_idea": raw_idea,
        "observation": "",
        "primary_hypothesis": "",
        "counter_hypothesis": "",
        "research_questions": [],
        "scope": {
            "market": "",
            "instrument_type": "",
            "universe": "",
            "data_source": "",
            "bar_size": "",
            "holding_horizons": [],
            "target_task": "",
            "excluded_scope": [],
            "budget_days": 0,
            "max_iterations": 0,
        },
        "qualification": {
            "summary": "",
            "dimensions": {
                name: {"score": 0, "evidence": [], "uncertainty": [], "kill_reason": []}
                for name in QUALIFICATION_DIMENSIONS
            },
        },
        "route_assessment": {
            "candidate_routes": [],
            "recommended_route": "",
            "why_recommended": [],
            "why_not_other_routes": {},
            "route_risks": [],
            "route_decision_pending": True,
        },
        "admission_decision": {
            "verdict": "NEEDS_REFRAME",
            "why": [],
            "kill_criteria": [],
            "required_reframe_actions": [],
        },
    }


def scaffold_mandate_admission(lineage_root: Path, *, raw_idea: str = "") -> list[str]:
    lineage_root = lineage_root.resolve()
    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    admission_path = draft_dir / "mandate_admission.yaml"
    freeze_path = draft_dir / "mandate_freeze_draft.yaml"
    written: list[str] = []

    if not admission_path.exists():
        _dump_yaml(admission_path, blank_mandate_admission(lineage_root.name, raw_idea=raw_idea))
        written.append(str(admission_path.relative_to(lineage_root)))
    if not freeze_path.exists():
        _dump_yaml(freeze_path, _blank_mandate_freeze_draft())
        written.append(str(freeze_path.relative_to(lineage_root)))

    validation = validate_stage_artifacts(draft_dir, load_artifact_contract("mandate_admission"))
    if not validation.valid:
        joined_errors = "; ".join(validation.errors)
        raise ValueError(f"mandate_admission scaffold does not match artifact contract: {joined_errors}")
    return written


def load_mandate_admission(lineage_root: Path) -> dict[str, Any]:
    path = lineage_root / "01_mandate" / "author" / "draft" / "mandate_admission.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def admission_ready_for_freeze(payload: dict[str, Any]) -> str | None:
    required_strings = (
        "raw_idea",
        "observation",
        "primary_hypothesis",
        "counter_hypothesis",
        "scope.market",
        "scope.universe",
        "scope.data_source",
        "scope.bar_size",
        "scope.target_task",
        "route_assessment.recommended_route",
    )
    for path in required_strings:
        value = _get_path(payload, path)
        if not isinstance(value, str) or not value.strip():
            return f"{path} is required"

    candidate_routes = _get_path(payload, "route_assessment.candidate_routes")
    recommended_route = _get_path(payload, "route_assessment.recommended_route")
    if not isinstance(candidate_routes, list) or recommended_route not in candidate_routes:
        return "route_assessment.recommended_route must be in candidate_routes"

    route_decision_pending = _get_path(payload, "route_assessment.route_decision_pending")
    if route_decision_pending is not False:
        return "route_assessment.route_decision_pending must be false"

    kill_criteria = _get_path(payload, "admission_decision.kill_criteria")
    if not isinstance(kill_criteria, list) or not kill_criteria:
        return "admission_decision.kill_criteria is required"

    verdict = _get_path(payload, "admission_decision.verdict")
    if verdict != "ACCEPT_FOR_MANDATE":
        return "admission_decision.verdict must be ACCEPT_FOR_MANDATE"

    dimensions = _get_path(payload, "qualification.dimensions")
    if not isinstance(dimensions, dict):
        return "qualification.dimensions is required"
    for name in QUALIFICATION_DIMENSIONS:
        score = _get_path(payload, f"qualification.dimensions.{name}.score")
        if isinstance(score, bool) or not isinstance(score, int) or score <= 0:
            return f"qualification.dimensions.{name}.score must be positive"
    return None


def _get_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
