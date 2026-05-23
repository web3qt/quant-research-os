from __future__ import annotations

import json
from pathlib import Path

import yaml

from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.review.test_start_review_session import _prepare_mandate_stage


def _formal_dir(stage_dir: Path) -> Path:
    return stage_dir / "author" / "formal"


def _load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_review_preflight_passes_valid_mandate_contract_outputs(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    payload = run_review_preflight(explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_blocks_mandate_when_artifact_contract_fails(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    time_split_path = _formal_dir(stage_dir) / "time_split.json"
    time_split = json.loads(time_split_path.read_text(encoding="utf-8"))
    time_split.pop("holding_horizons")
    time_split_path.write_text(json.dumps(time_split, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload = run_review_preflight(explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})

    assert payload["status"] == "FAIL"
    assert any("ARTIFACT-CONTRACT-001" in item for item in payload["content_findings"])
    assert any("time_split.json: missing required field holding_horizons" in item for item in payload["content_findings"])


def test_review_preflight_blocks_mandate_when_route_dependency_is_invalid(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    route_path = _formal_dir(stage_dir) / "research_route.yaml"
    route = _load_yaml(route_path)
    route.update(
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "regime_filter",
            "factor_structure": "single_factor",
            "portfolio_expression": "target_strategy_filter",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "",
            "group_taxonomy_reference": "",
            "excluded_routes": ["time_series_signal"],
            "route_rationale": ["Cross-sectional route requires explicit upstream bindings."],
        }
    )
    _write_yaml(route_path, route)

    payload = run_review_preflight(explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})

    assert payload["status"] == "FAIL"
    assert any("MANDATE-SEMANTIC-001" in item for item in payload["content_findings"])
    assert any("target_strategy_reference is required" in item for item in payload["content_findings"])
    assert any("group_taxonomy_reference is required" in item for item in payload["content_findings"])
