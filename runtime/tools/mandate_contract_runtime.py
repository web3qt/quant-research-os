from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


def validate_mandate_semantics(stage_formal_dir: Path) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    errors: list[str] = []

    research_route = _load_yaml_mapping(stage_formal_dir / "research_route.yaml", errors)
    time_split = _load_json_mapping(stage_formal_dir / "time_split.json", errors)
    run_config = _load_toml_mapping(stage_formal_dir / "run_config.toml", errors)

    if research_route is not None:
        errors.extend(_validate_research_route(research_route))
    if time_split is not None and run_config is not None:
        errors.extend(_validate_time_split_binding(time_split, run_config))

    return ArtifactValidationResult(errors=errors)


def _load_yaml_mapping(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"{path.name}: yaml read failed: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: expected yaml map, found {type(payload).__name__}")
        return None
    return payload


def _load_json_mapping(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: json read failed: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: expected json map, found {type(payload).__name__}")
        return None
    return payload


def _load_toml_mapping(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: toml read failed: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: expected toml map, found {type(payload).__name__}")
        return None
    return payload


def _validate_research_route(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    research_route = _string_value(payload.get("research_route"))
    excluded_routes = _string_list(payload.get("excluded_routes"))
    route_rationale = _string_list(payload.get("route_rationale"))

    if not excluded_routes:
        errors.append("research_route.yaml: excluded_routes must be a non-empty list")
    if research_route and research_route in excluded_routes:
        errors.append("research_route.yaml: excluded_routes cannot include research_route")
    if not route_rationale:
        errors.append("research_route.yaml: route_rationale must be a non-empty list")

    policy = payload.get("route_change_policy")
    if not isinstance(policy, dict):
        errors.append("research_route.yaml: route_change_policy must be a map")
    else:
        if _string_value(policy.get("before_downstream_freeze")) != "rollback_to_mandate":
            errors.append(
                "research_route.yaml: route_change_policy.before_downstream_freeze must equal rollback_to_mandate"
            )
        if _string_value(policy.get("after_downstream_freeze")) != "child_lineage":
            errors.append(
                "research_route.yaml: route_change_policy.after_downstream_freeze must equal child_lineage"
            )

    if research_route == "cross_sectional_factor":
        errors.extend(_validate_csf_route_dependencies(payload))
    return errors


def _validate_csf_route_dependencies(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("factor_role", "factor_structure", "portfolio_expression", "neutralization_policy"):
        if not _string_value(payload.get(field)):
            errors.append(f"research_route.yaml: {field} must be non-empty for cross_sectional_factor")

    factor_role = _string_value(payload.get("factor_role"))
    portfolio_expression = _string_value(payload.get("portfolio_expression"))
    target_strategy_reference = _string_value(payload.get("target_strategy_reference"))
    neutralization_policy = _string_value(payload.get("neutralization_policy"))
    group_taxonomy_reference = _string_value(payload.get("group_taxonomy_reference"))

    if factor_role in {"regime_filter", "combo_filter"} and not target_strategy_reference:
        errors.append("research_route.yaml: target_strategy_reference is required for filter/combo factor_role")
    if portfolio_expression in {"target_strategy_filter", "target_strategy_overlay"} and not target_strategy_reference:
        errors.append("research_route.yaml: target_strategy_reference is required for target_strategy portfolio_expression")
    if neutralization_policy == "group_neutral" and not group_taxonomy_reference:
        errors.append("research_route.yaml: group_taxonomy_reference is required for group_neutral")
    return errors


def _validate_time_split_binding(time_split: dict[str, Any], run_config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    holding_horizons = _string_list(time_split.get("holding_horizons"))
    if not holding_horizons:
        errors.append("time_split.json: holding_horizons must be a non-empty list")

    time_split_bar_size = _string_value(time_split.get("bar_size"))
    run_config_bar_size = _string_value(run_config.get("bar_size"))
    if time_split_bar_size and run_config_bar_size and time_split_bar_size != run_config_bar_size:
        errors.append("time_split.json: bar_size must match run_config.toml bar_size")
    return errors


def _string_value(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
