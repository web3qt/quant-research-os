from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def scaffold_idea_intake(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True, exist_ok=True)

    templates: dict[str, str] = {
        "idea_brief.md": "# Idea Brief\n\n## Raw Idea\n\n- TODO\n\n## Source\n\n- TODO\n",
        "observation_hypothesis_map.md": (
            "# Observation Hypothesis Map\n\n"
            "## Observation\n\n- TODO\n\n"
            "## Primary Hypothesis\n\n- TODO\n\n"
            "## Counter-Hypothesis\n\n- TODO\n"
        ),
        "research_question_set.md": "# Research Questions\n\n- TODO\n",
        "artifact_catalog.md": "# Artifact Catalog\n\n- idea_brief.md\n- observation_hypothesis_map.md\n",
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
    return intake_dir


def build_mandate_from_intake(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    intake_dir = lineage_root / "00_idea_intake"
    mandate_dir = lineage_root / "01_mandate"

    gate_decision = yaml.safe_load((intake_dir / "idea_gate_decision.yaml").read_text(encoding="utf-8"))

    if gate_decision.get("verdict") != "GO_TO_MANDATE":
        raise ValueError("idea_gate_decision verdict must be GO_TO_MANDATE before mandate build")

    scope_canvas = yaml.safe_load((intake_dir / "scope_canvas.yaml").read_text(encoding="utf-8"))
    research_questions = (intake_dir / "research_question_set.md").read_text(encoding="utf-8")

    mandate_dir.mkdir(parents=True, exist_ok=True)

    approved_scope = gate_decision.get("approved_scope", {})
    data_source = _resolve_scope_value("data_source", approved_scope, scope_canvas)
    bar_size = _resolve_scope_value("bar_size", approved_scope, scope_canvas)
    if not data_source or not bar_size:
        missing = []
        if not data_source:
            missing.append("data_source")
        if not bar_size:
            missing.append("bar_size")
        raise ValueError(f"confirmed mandate inputs missing: {', '.join(missing)}")

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
                "## Research Questions",
                "",
                research_questions.strip(),
                "",
                "## Frozen Execution Inputs",
                "",
                f"- Data source: {data_source}",
                f"- Bar size: {bar_size}",
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
                f"- Market: {approved_scope.get('market', scope_canvas.get('market', ''))}",
                f"- Data source: {data_source}",
                f"- Universe: {approved_scope.get('universe', scope_canvas.get('universe', ''))}",
                f"- Bar size: {bar_size}",
                f"- Target task: {approved_scope.get('target_task', scope_canvas.get('target_task', ''))}",
                f"- Excluded scope: {', '.join(approved_scope.get('excluded_scope', scope_canvas.get('excluded_scope', [])))}",
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
                "- TODO: define remaining formal fields consumed by downstream stages.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return mandate_dir


def _resolve_scope_value(key: str, approved_scope: dict[str, Any], scope_canvas: dict[str, Any]) -> str:
    value = approved_scope.get(key, scope_canvas.get(key, ""))
    if value is None:
        return ""
    return str(value).strip()
