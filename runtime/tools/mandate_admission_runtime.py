from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.idea_runtime import _blank_mandate_freeze_draft
from runtime.tools.research_preflight import ResearchPreflightStatus, compute_research_preflight


QUALIFICATION_DIMENSIONS = (
    "observability",
    "mechanism_plausibility",
    "tradeability",
    "data_feasibility",
    "scoping_clarity",
    "distinctiveness",
)
SUPPORTED_RESEARCH_ROUTES = {
    "time_series_signal",
    "cross_sectional_factor",
}


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


def admission_preflight_error(payload: dict[str, Any]) -> str | None:
    route_error = _assess_route_viability(payload)
    if route_error is not None:
        return route_error

    scope = payload.get("scope")
    if not isinstance(scope, dict):
        return None

    preflight = assess_time_coverage_preflight(
        data_source=scope.get("data_source", ""),
        time_boundary=scope.get("time_boundary", ""),
    )
    if preflight is None or preflight.passable:
        return None
    return (
        f"time coverage preflight failed: {preflight.blocker_code}: "
        f"{preflight.blocker_reason}"
    )


def assess_time_coverage_preflight(
    *,
    data_source: object,
    time_boundary: object,
) -> ResearchPreflightStatus | None:
    boundary = _parse_time_boundary(time_boundary)
    if boundary is None:
        return None

    inventory_facts = discover_data_inventory_facts(data_source)
    if not inventory_facts:
        return None

    return compute_research_preflight(
        stage="mandate",
        user_confirmed={
            "research_route": "",
            "bar_size": "",
            "train_start": boundary[0],
            "holdout_end": boundary[1],
        },
        runtime_facts=inventory_facts,
    )


def discover_data_inventory_facts(data_source: object) -> dict[str, str]:
    data_source_path = _as_existing_path(data_source)
    if data_source_path is None:
        return {}

    candidate_paths = [data_source_path] if data_source_path.is_file() else [
        data_source_path / "data_inventory.json",
        data_source_path / "data_inventory.yaml",
        data_source_path / "data_inventory.yml",
        data_source_path / "dataset_manifest.json",
        data_source_path / "dataset_manifest.yaml",
        data_source_path / "dataset_manifest.yml",
    ]
    for candidate_path in candidate_paths:
        if not candidate_path.exists() or not candidate_path.is_file():
            continue
        payload = yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
        facts = _extract_inventory_facts(payload)
        if facts:
            return facts
    return {}


def _assess_route_viability(payload: dict[str, Any]) -> str | None:
    observation = str(payload.get("observation", "")).strip()
    primary_hypothesis = str(payload.get("primary_hypothesis", "")).strip()
    research_questions = payload.get("research_questions", [])
    route_assessment = payload.get("route_assessment")
    scope = payload.get("scope")
    target_task = scope.get("target_task", "") if isinstance(scope, dict) else ""

    if not isinstance(route_assessment, dict):
        return None

    recommended_route = str(route_assessment.get("recommended_route", "")).strip()
    if recommended_route not in SUPPORTED_RESEARCH_ROUTES:
        return None

    expected_route = _infer_expected_route(
        observation=observation,
        primary_hypothesis=primary_hypothesis,
        research_questions=research_questions,
        target_task=target_task,
    )
    if expected_route is None or recommended_route == expected_route:
        return None
    return (
        "route_assessment.recommended_route "
        f"{recommended_route} conflicts with clearly {expected_route} problem framing"
    )


def _infer_expected_route(
    *,
    observation: object,
    primary_hypothesis: object,
    research_questions: object,
    target_task: object,
) -> str | None:
    framing_parts = [
        str(observation or "").strip(),
        str(primary_hypothesis or "").strip(),
        str(target_task or "").strip(),
    ]
    if isinstance(research_questions, list):
        framing_parts.extend(str(item).strip() for item in research_questions if str(item).strip())
    framing = " ".join(framing_parts).lower()
    cross_sectional_markers = (
        "cross-sectional",
        "cross sectional",
        "cross-asset",
        "cross asset",
        "relative return",
        "relative returns",
        "rank all assets",
        "rank assets",
        "ranking",
        "rank forecast",
    )
    if any(marker in framing for marker in cross_sectional_markers):
        return "cross_sectional_factor"
    return None


def _parse_time_boundary(time_boundary: object) -> tuple[str, str] | None:
    normalized = str(time_boundary or "").strip()
    if not normalized:
        return None
    if "/" in normalized:
        parts = [part.strip() for part in normalized.split("/", maxsplit=1)]
    elif " to " in normalized:
        parts = [part.strip() for part in normalized.split(" to ", maxsplit=1)]
    else:
        return None
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


def _as_existing_path(value: object) -> Path | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None
    candidate = Path(normalized).expanduser()
    if candidate.exists():
        return candidate
    return None


def _extract_inventory_facts(payload: Any) -> dict[str, str]:
    candidates: list[Any] = [payload]
    if isinstance(payload, dict):
        candidates.extend(
            [
                payload.get("coverage"),
                payload.get("time_coverage"),
                payload.get("inventory"),
            ]
        )
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        data_min_ts = str(candidate.get("data_min_ts", "")).strip()
        data_max_ts = str(candidate.get("data_max_ts", "")).strip()
        if data_min_ts and data_max_ts:
            return {
                "data_min_ts": data_min_ts,
                "data_max_ts": data_max_ts,
            }
    return {}


def _get_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
