from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


MANDATE_FREEZE_DRAFT_FILE = "mandate_freeze_draft.yaml"
MANDATE_FREEZE_GROUP_ORDER = [
    "research_intent",
    "scope_contract",
    "data_contract",
    "execution_contract",
]


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
        "idea_brief.md": "# Idea Brief\n\n## Raw Idea\n\n- TODO\n\n## Source\n\n- TODO\n",
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
            "## Observation\n\n- TODO\n\n"
            "## Primary Hypothesis\n\n- TODO\n\n"
            "## Counter-Hypothesis\n\n- TODO\n"
        ),
        "research_question_set.md": "# Research Questions\n\n- TODO\n",
        "artifact_catalog.md": (
            "# Artifact Catalog\n\n"
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

    gate_decision = yaml.safe_load((intake_dir / "idea_gate_decision.yaml").read_text(encoding="utf-8"))

    if gate_decision.get("verdict") != "GO_TO_MANDATE":
        raise ValueError("idea_gate_decision verdict must be GO_TO_MANDATE before mandate build")

    mandate_dir.mkdir(parents=True, exist_ok=True)
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
    excluded_scope = _string_list(scope_contract.get("excluded_scope", []))
    timestamp_semantics = _required_draft_value(data_contract, "timestamp_semantics")
    no_lookahead_guardrail = _required_draft_value(data_contract, "no_lookahead_guardrail")

    (mandate_dir / "mandate.md").write_text(
        "\n".join(
            [
                "# Mandate",
                "",
                f"Idea ID: {gate_decision.get('idea_id', lineage_root.name)}",
                "",
                "## Objective",
                "",
                "- Convert qualified intake into a formal mandate.",
                "",
                "## Research Intent",
                "",
                f"- Research question: {research_question}",
                f"- Primary hypothesis: {primary_hypothesis}",
                f"- Counter-hypothesis: {counter_hypothesis}",
                f"- Excluded topics: {', '.join(excluded_topics)}",
                "",
                "## Success Criteria",
                "",
                *[f"- {item}" for item in success_criteria],
                "",
                "## Failure Criteria",
                "",
                *[f"- {item}" for item in failure_criteria],
                "",
                "## Frozen Execution Inputs",
                "",
                f"- Data source: {data_source}",
                f"- Bar size: {bar_size}",
                f"- Holding horizons: {', '.join(holding_horizons)}",
                f"- Timestamp semantics: {timestamp_semantics}",
                f"- No-lookahead guardrail: {no_lookahead_guardrail}",
                "",
                "## Execution Contract",
                "",
                f"- Time split policy: {time_split_note}",
                f"- Parameter boundary policy: {parameter_boundary_note}",
                f"- Artifact contract: {artifact_contract_note}",
                f"- Crowding/capacity note: {crowding_capacity_note}",
                "",
                "## Gate Basis",
                "",
                "- idea_gate_decision.yaml verdict = GO_TO_MANDATE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (mandate_dir / "research_scope.md").write_text(
        "\n".join(
            [
                "# Research Scope",
                "",
                f"- Market: {market}",
                f"- Data source: {data_source}",
                f"- Universe: {universe}",
                f"- Bar size: {bar_size}",
                f"- Target task: {target_task}",
                f"- Excluded scope: {', '.join(excluded_scope)}",
                f"- Budget days: {scope_contract.get('budget_days', 0)}",
                f"- Max iterations: {scope_contract.get('max_iterations', 0)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (mandate_dir / "time_split.json").write_text(
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
        mandate_dir / "parameter_grid.yaml",
        {
            "parameters": [],
            "note": "Fill formal parameter candidates after mandate qualification.",
        },
    )
    (mandate_dir / "run_config.toml").write_text(
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
    (mandate_dir / "artifact_catalog.md").write_text(
        "# Artifact Catalog\n\n- mandate.md\n- research_scope.md\n- time_split.json\n- parameter_grid.yaml\n- run_config.toml\n",
        encoding="utf-8",
    )
    (mandate_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# Field Dictionary",
                "",
                f"- `data_source`: frozen upstream source for this mandate, currently `{data_source}`.",
                f"- `bar_size`: frozen research cadence for this mandate, currently `{bar_size}`.",
                f"- `holding_horizons`: frozen evaluation horizons, currently `{holding_horizons}`.",
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
