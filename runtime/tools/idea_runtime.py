from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.context_inference import build_stage_context


MANDATE_FREEZE_DRAFT_FILE = "mandate_freeze_draft.yaml"
MANDATE_FREEZE_GROUP_ORDER = [
    "research_intent",
    "scope_contract",
    "data_contract",
    "execution_contract",
]
SUPPORTED_RESEARCH_ROUTES = {
    "time_series_signal",
    "cross_sectional_factor",
}
SUPPORTED_FACTOR_ROLES = {"standalone_alpha", "regime_filter", "combo_filter"}
SUPPORTED_FACTOR_STRUCTURES = {"single_factor", "multi_factor_score"}
SUPPORTED_PORTFOLIO_EXPRESSIONS = {
    "long_short_market_neutral",
    "long_only_rank",
    "short_only_rank",
    "benchmark_relative_long_only",
    "group_relative_long_short",
    "target_strategy_filter",
    "target_strategy_overlay",
}
SUPPORTED_NEUTRALIZATION_POLICIES = {"none", "market_beta_neutral", "group_neutral"}


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_mandate_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "research_intent": {
                "confirmed": False,
                "draft": {
                    "research_question": "",
                    "primary_hypothesis": "",
                    "counter_hypothesis": "",
                    "research_route": "",
                    "factor_role": "",
                    "factor_structure": "",
                    "portfolio_expression": "",
                    "neutralization_policy": "",
                    "target_strategy_reference": "",
                    "group_taxonomy_reference": "",
                    "excluded_routes": [],
                    "route_rationale": [],
                    "success_criteria": [],
                    "failure_criteria": [],
                    "excluded_topics": [],
                },
            },
            "scope_contract": {
                "confirmed": False,
                "draft": {
                    "market": "",
                    "universe": "",
                    "target_task": "",
                    "excluded_scope": [],
                    "budget_days": 0,
                    "max_iterations": 0,
                },
            },
            "data_contract": {
                "confirmed": False,
                "draft": {
                    "data_source": "",
                    "bar_size": "",
                    "holding_horizons": [],
                    "timestamp_semantics": "",
                    "no_lookahead_guardrail": "",
                },
            },
            "execution_contract": {
                "confirmed": False,
                "draft": {
                    "time_split_note": "",
                    "parameter_boundary_note": "",
                    "artifact_contract_note": "",
                    "crowding_capacity_note": "",
                },
            },
        }
    }


def scaffold_idea_intake(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True, exist_ok=True)

    templates: dict[str, str] = {
        "idea_brief.md": "# Idea Brief\n\n## 原始想法\n\n- TODO\n\n## 来源\n\n- TODO\n",
        "intake_interview.md": (
            "# Intake Interview\n\n"
            "在填写 qualification 和 gate 之前，必须先和用户确认：\n\n"
            "- observation 到底是什么\n"
            "- primary hypothesis 是什么\n"
            "- counter-hypothesis 是什么\n"
            "- market / universe / target_task 是什么\n"
            "- data_source / bar_size 是什么\n"
            "- kill criteria / reframe 条件是什么\n"
        ),
        "observation_hypothesis_map.md": (
            "# Observation Hypothesis Map\n\n"
            "## 观察\n\n- TODO\n\n"
            "## 主假设\n\n- TODO\n\n"
            "## 对立假设\n\n- TODO\n"
        ),
        "research_question_set.md": "# Research Questions\n\n- TODO\n",
        "artifact_catalog.md": (
            "# 产物清单\n\n"
            "- idea_brief.md\n"
            "- intake_interview.md\n"
            "- observation_hypothesis_map.md\n"
        ),
    }
    for name, content in templates.items():
        (intake_dir / name).write_text(content, encoding="utf-8")

    _dump_yaml(
        intake_dir / "scope_canvas.yaml",
        {
            "market": "",
            "data_source": "",
            "instrument_type": "",
            "universe": "",
            "bar_size": "",
            "holding_horizons": [],
            "target_task": "",
            "excluded_scope": [],
            "budget_days": 0,
            "max_iterations": 0,
        },
    )
    _dump_yaml(
        intake_dir / "qualification_scorecard.yaml",
        {
            "idea_id": lineage_root.name,
            "reviewer_identity": "codex",
            "summary": "",
            "dimensions": {
                key: {"score": 0, "evidence": [], "uncertainty": [], "kill_reason": []}
                for key in [
                    "observability",
                    "mechanism_plausibility",
                    "tradeability",
                    "data_feasibility",
                    "scoping_clarity",
                    "distinctiveness",
                ]
            },
        },
    )
    _dump_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": lineage_root.name,
            "verdict": "NEEDS_REFRAME",
            "why": [],
            "route_assessment": {
                "candidate_routes": [],
                "recommended_route": "",
                "why_recommended": [],
                "why_not_other_routes": {},
                "route_risks": [],
                "route_decision_pending": True,
            },
            "approved_scope": {},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _dump_yaml(intake_dir / MANDATE_FREEZE_DRAFT_FILE, _blank_mandate_freeze_draft())
    return intake_dir


def build_mandate_from_intake(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    intake_dir = lineage_root / "00_idea_intake"
    mandate_dir = lineage_root / "01_mandate"
    mandate_context = build_stage_context(mandate_dir)
    mandate_formal_dir = mandate_context["author_formal_dir"]

    gate_decision = yaml.safe_load((intake_dir / "idea_gate_decision.yaml").read_text(encoding="utf-8"))

    if gate_decision.get("verdict") != "GO_TO_MANDATE":
        raise ValueError("idea_gate_decision verdict must be GO_TO_MANDATE before mandate build")
    route_assessment = _require_route_assessment(gate_decision)

    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    freeze_groups = _require_confirmed_freeze_groups(intake_dir)
    research_intent = freeze_groups["research_intent"]["draft"]
    scope_contract = freeze_groups["scope_contract"]["draft"]
    data_contract = freeze_groups["data_contract"]["draft"]
    execution_contract = freeze_groups["execution_contract"]["draft"]

    data_values = _require_draft_values(data_contract, "data_source", "bar_size")
    data_source = data_values["data_source"]
    bar_size = data_values["bar_size"]
    research_question = _required_draft_value(research_intent, "research_question")
    primary_hypothesis = _required_draft_value(research_intent, "primary_hypothesis")
    counter_hypothesis = _required_draft_value(research_intent, "counter_hypothesis")
    research_route = _require_supported_route(
        _required_draft_value(research_intent, "research_route"),
        field_name="confirmed mandate inputs research_route",
    )
    factor_role = _optional_supported_value(
        research_intent.get("factor_role", ""),
        supported=SUPPORTED_FACTOR_ROLES,
        field_name="confirmed mandate inputs factor_role",
    )
    factor_structure = _optional_supported_value(
        research_intent.get("factor_structure", ""),
        supported=SUPPORTED_FACTOR_STRUCTURES,
        field_name="confirmed mandate inputs factor_structure",
    )
    portfolio_expression = _optional_supported_value(
        research_intent.get("portfolio_expression", ""),
        supported=SUPPORTED_PORTFOLIO_EXPRESSIONS,
        field_name="confirmed mandate inputs portfolio_expression",
    )
    neutralization_policy = _optional_supported_value(
        research_intent.get("neutralization_policy", ""),
        supported=SUPPORTED_NEUTRALIZATION_POLICIES,
        field_name="confirmed mandate inputs neutralization_policy",
    )
    target_strategy_reference = _optional_string(research_intent.get("target_strategy_reference", ""))
    group_taxonomy_reference = _optional_string(research_intent.get("group_taxonomy_reference", ""))
    market = _required_draft_value(scope_contract, "market")
    universe = _required_draft_value(scope_contract, "universe")
    target_task = _required_draft_value(scope_contract, "target_task")
    time_split_note = _required_draft_value(execution_contract, "time_split_note")
    parameter_boundary_note = _required_draft_value(execution_contract, "parameter_boundary_note")
    artifact_contract_note = _required_draft_value(execution_contract, "artifact_contract_note")
    crowding_capacity_note = _required_draft_value(execution_contract, "crowding_capacity_note")
    holding_horizons = _string_list(data_contract.get("holding_horizons", []))
    success_criteria = _string_list(research_intent.get("success_criteria", []))
    failure_criteria = _string_list(research_intent.get("failure_criteria", []))
    excluded_topics = _string_list(research_intent.get("excluded_topics", []))
    excluded_routes = _require_supported_route_list(
        _string_list(research_intent.get("excluded_routes", [])),
        field_name="confirmed mandate inputs excluded_routes",
    )
    route_rationale = _string_list(research_intent.get("route_rationale", []))
    excluded_scope = _string_list(scope_contract.get("excluded_scope", []))
    timestamp_semantics = _required_draft_value(data_contract, "timestamp_semantics")
    no_lookahead_guardrail = _required_draft_value(data_contract, "no_lookahead_guardrail")
    if not excluded_routes:
        raise ValueError("confirmed mandate inputs missing: excluded_routes")
    if not route_rationale:
        raise ValueError("confirmed mandate inputs missing: route_rationale")
    if research_route not in route_assessment["candidate_routes"]:
        raise ValueError("confirmed mandate inputs research_route must be one of intake candidate_routes")
    rejected_routes = {route for route in route_assessment["candidate_routes"] if route != research_route}
    if set(excluded_routes) != rejected_routes:
        raise ValueError("confirmed mandate inputs excluded_routes must match rejected intake candidate_routes")
    if research_route in excluded_routes:
        raise ValueError("confirmed mandate inputs excluded_routes cannot include research_route")
    if research_route == "cross_sectional_factor":
        missing_csf_identity = [
            field_name
            for field_name, field_value in (
                ("factor_role", factor_role),
                ("factor_structure", factor_structure),
                ("portfolio_expression", portfolio_expression),
                ("neutralization_policy", neutralization_policy),
            )
            if not field_value
        ]
        if missing_csf_identity:
            raise ValueError(
                "confirmed mandate inputs missing CSF identity fields: " + ", ".join(missing_csf_identity)
            )
        _validate_csf_portfolio_expression_role_pair(
            factor_role=factor_role,
            portfolio_expression=portfolio_expression,
        )
        if factor_role in {"regime_filter", "combo_filter"} and not target_strategy_reference:
            raise ValueError(
                "confirmed mandate inputs missing: target_strategy_reference for filter/combo cross_sectional_factor route"
            )
        if neutralization_policy == "group_neutral" and not group_taxonomy_reference:
            raise ValueError(
                "confirmed mandate inputs missing: group_taxonomy_reference for group_neutral cross_sectional_factor route"
            )

    (mandate_formal_dir / "mandate.md").write_text(
        "\n".join(
            [
                "# Mandate",
                "",
                f"Idea ID: {gate_decision.get('idea_id', lineage_root.name)}",
                "",
                "## 目标",
                "",
                "- 将已通过 qualification 的 intake 冻结为正式 mandate。",
                "",
                "## 研究意图",
                "",
                f"- 研究问题: {research_question}",
                f"- 主假设: {primary_hypothesis}",
                f"- 对立假设: {counter_hypothesis}",
                f"- 研究路线: {research_route}",
                f"- 因子角色: {factor_role or 'n/a'}",
                f"- 因子结构: {factor_structure or 'n/a'}",
                f"- 组合表达: {portfolio_expression or 'n/a'}",
                f"- 中性化策略: {neutralization_policy or 'n/a'}",
                f"- 目标策略引用: {target_strategy_reference or 'n/a'}",
                f"- 分组体系引用: {group_taxonomy_reference or 'n/a'}",
                f"- 排除路线: {', '.join(excluded_routes)}",
                f"- 排除主题: {', '.join(excluded_topics)}",
                "",
                "## 路线理由",
                "",
                *[f"- {item}" for item in route_rationale],
                "",
                "## 成功标准",
                "",
                *[f"- {item}" for item in success_criteria],
                "",
                "## 失败标准",
                "",
                *[f"- {item}" for item in failure_criteria],
                "",
                "## 已冻结执行输入",
                "",
                f"- 数据来源: {data_source}",
                f"- Bar 粒度: {bar_size}",
                f"- 持有窗口: {', '.join(holding_horizons)}",
                f"- 时间戳语义: {timestamp_semantics}",
                f"- 无前视护栏: {no_lookahead_guardrail}",
                "",
                "## 执行合同",
                "",
                f"- 时间切分策略: {time_split_note}",
                f"- 参数边界策略: {parameter_boundary_note}",
                f"- 产物合同: {artifact_contract_note}",
                f"- 拥挤度 / 容量说明: {crowding_capacity_note}",
                "",
                "## Gate 依据",
                "",
                "- idea_gate_decision.yaml verdict = GO_TO_MANDATE",
                f"- Intake 推荐路线: {route_assessment['recommended_route']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (mandate_formal_dir / "research_scope.md").write_text(
        "\n".join(
            [
                "# Research Scope",
                "",
                f"- 市场: {market}",
                f"- 数据来源: {data_source}",
                f"- Universe: {universe}",
                f"- Bar 粒度: {bar_size}",
                f"- 研究任务: {target_task}",
                f"- 排除范围: {', '.join(excluded_scope)}",
                f"- 预算天数: {scope_contract.get('budget_days', 0)}",
                f"- 最大迭代次数: {scope_contract.get('max_iterations', 0)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _dump_yaml(
        mandate_formal_dir / "research_route.yaml",
        {
            "research_route": research_route,
            "factor_role": factor_role,
            "factor_structure": factor_structure,
            "portfolio_expression": portfolio_expression,
            "neutralization_policy": neutralization_policy,
            "target_strategy_reference": target_strategy_reference,
            "group_taxonomy_reference": group_taxonomy_reference,
            "excluded_routes": excluded_routes,
            "route_rationale": route_rationale,
            "route_change_policy": {
                "before_downstream_freeze": "rollback_to_mandate",
                "after_downstream_freeze": "child_lineage",
            },
            "route_contract_version": "v1",
        },
    )

    (mandate_formal_dir / "time_split.json").write_text(
        json.dumps(
            {
                "train": "",
                "test": "",
                "backtest": "",
                "holdout": "",
                "bar_size": bar_size,
                "holding_horizons": holding_horizons,
                "policy_note": time_split_note,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    _dump_yaml(
        mandate_formal_dir / "parameter_grid.yaml",
        {
            "parameters": [],
            "note": "在 mandate qualification 完成后补正式参数候选。",
        },
    )
    (mandate_formal_dir / "run_config.toml").write_text(
        "\n".join(
            [
                'stage = "mandate"',
                f'lineage_id = "{lineage_root.name}"',
                f'market = "{market}"',
                f'universe = "{universe}"',
                f'target_task = "{target_task}"',
                f'data_source = "{data_source}"',
                f'bar_size = "{bar_size}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (mandate_formal_dir / "artifact_catalog.md").write_text(
        "# 产物清单\n\n- mandate.md\n- research_scope.md\n- research_route.yaml\n- time_split.json\n- parameter_grid.yaml\n- run_config.toml\n",
        encoding="utf-8",
    )
    (mandate_formal_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `research_route`: 本 mandate 冻结的研究路线，当前为 `{research_route}`。",
                f"- `factor_role`: CSF 因子角色，当前为 `{factor_role or 'n/a'}`。",
                f"- `factor_structure`: CSF 因子结构，当前为 `{factor_structure or 'n/a'}`。",
                f"- `portfolio_expression`: CSF 组合表达，当前为 `{portfolio_expression or 'n/a'}`。",
                f"- `neutralization_policy`: CSF 中性化策略，当前为 `{neutralization_policy or 'n/a'}`。",
                f"- `target_strategy_reference`: CSF 目标策略引用，当前为 `{target_strategy_reference or 'n/a'}`。",
                f"- `group_taxonomy_reference`: CSF 分组体系引用，当前为 `{group_taxonomy_reference or 'n/a'}`。",
                f"- `excluded_routes`: mandate 冻结时排除的备选路线，当前为 `{excluded_routes}`。",
                f"- `data_source`: 本 mandate 冻结的上游数据来源，当前为 `{data_source}`。",
                f"- `bar_size`: 本 mandate 冻结的研究粒度，当前为 `{bar_size}`。",
                f"- `holding_horizons`: 本 mandate 冻结的持有窗口，当前为 `{holding_horizons}`。",
                f"- `artifact_contract`: {artifact_contract_note}",
                f"- `no_lookahead_guardrail`: {no_lookahead_guardrail}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return mandate_dir


def _require_confirmed_freeze_groups(intake_dir: Path) -> dict[str, Any]:
    draft_path = intake_dir / MANDATE_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        raise ValueError(f"{MANDATE_FREEZE_DRAFT_FILE} is required before mandate build")

    draft_payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = draft_payload.get("groups", {})
    missing_groups = [
        name for name in MANDATE_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))
    ]
    if missing_groups:
        raise ValueError(
            f"{MANDATE_FREEZE_DRAFT_FILE} has unconfirmed groups: {', '.join(missing_groups)}"
        )
    return groups


def _required_draft_value(group_payload: dict[str, Any], key: str) -> str:
    value = group_payload.get(key, "")
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"confirmed mandate inputs missing: {key}")
    return normalized


def _require_draft_values(group_payload: dict[str, Any], *keys: str) -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []
    for key in keys:
        value = str(group_payload.get(key, "")).strip()
        if not value:
            missing.append(key)
            continue
        values[key] = value
    if missing:
        raise ValueError(f"confirmed mandate inputs missing: {', '.join(missing)}")
    return values


def _string_list(raw_value: Any) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    return [str(item) for item in raw_value if str(item).strip()]


def _require_route_assessment(gate_decision: dict[str, Any]) -> dict[str, Any]:
    route_assessment = gate_decision.get("route_assessment")
    if not isinstance(route_assessment, dict):
        raise ValueError("idea_gate_decision missing route_assessment for GO_TO_MANDATE")

    recommended_route = _require_supported_route(
        str(route_assessment.get("recommended_route", "")).strip(),
        field_name="idea_gate_decision route_assessment recommended_route",
    )
    candidate_routes = _require_supported_route_list(
        _string_list(route_assessment.get("candidate_routes", [])),
        field_name="idea_gate_decision route_assessment candidate_routes",
    )
    why_recommended = _string_list(route_assessment.get("why_recommended", []))
    why_not_other_routes = route_assessment.get("why_not_other_routes", {})

    if not candidate_routes:
        raise ValueError("idea_gate_decision route_assessment missing candidate_routes")
    if len(candidate_routes) < 2:
        raise ValueError("idea_gate_decision route_assessment candidate_routes must include at least two routes")
    if recommended_route not in candidate_routes:
        raise ValueError("idea_gate_decision route_assessment recommended_route must be in candidate_routes")
    if not why_recommended:
        raise ValueError("idea_gate_decision route_assessment missing why_recommended")
    if not isinstance(why_not_other_routes, dict):
        raise ValueError("idea_gate_decision route_assessment missing why_not_other_routes")
    rejected_routes = {route for route in candidate_routes if route != recommended_route}
    documented_rejections = {str(route).strip() for route in why_not_other_routes if str(route).strip()}
    if rejected_routes - documented_rejections:
        raise ValueError("idea_gate_decision route_assessment missing why_not_other_routes entries")
    return route_assessment


def _require_supported_route(route_value: str, *, field_name: str) -> str:
    route_name = str(route_value).strip()
    if not route_name:
        raise ValueError(f"{field_name} missing")
    if route_name not in SUPPORTED_RESEARCH_ROUTES:
        raise ValueError(f"{field_name} unsupported route: {route_name}")
    return route_name


def _require_supported_route_list(route_values: list[str], *, field_name: str) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_route in route_values:
        route_name = _require_supported_route(raw_route, field_name=field_name)
        if route_name in seen:
            raise ValueError(f"{field_name} contains duplicate route: {route_name}")
        normalized.append(route_name)
        seen.add(route_name)
    return normalized


def _optional_supported_value(value: object, *, supported: set[str], field_name: str) -> str:
    normalized = _optional_string(value)
    if not normalized:
        return ""
    if normalized not in supported:
        raise ValueError(f"{field_name} must be one of: {', '.join(sorted(supported))}")
    return normalized


def _optional_string(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _validate_csf_portfolio_expression_role_pair(
    *,
    factor_role: str,
    portfolio_expression: str,
) -> None:
    allowed_by_role = {
        "standalone_alpha": {
            "long_short_market_neutral",
            "long_only_rank",
            "short_only_rank",
            "benchmark_relative_long_only",
            "group_relative_long_short",
        },
        "regime_filter": {"target_strategy_filter"},
        "combo_filter": {"target_strategy_filter", "target_strategy_overlay"},
    }
    allowed = allowed_by_role.get(factor_role, set())
    if portfolio_expression not in allowed:
        raise ValueError(
            "confirmed mandate inputs portfolio_expression "
            f"{portfolio_expression!r} is not allowed for factor_role {factor_role!r}; "
            f"allowed values: {', '.join(sorted(allowed))}"
        )
