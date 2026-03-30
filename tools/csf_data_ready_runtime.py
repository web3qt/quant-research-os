from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


CSF_DATA_READY_FREEZE_DRAFT_FILE = "csf_data_ready_freeze_draft.yaml"
CSF_DATA_READY_FREEZE_GROUP_ORDER = [
    "panel_contract",
    "taxonomy_contract",
    "eligibility_contract",
    "shared_feature_base",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_csf_data_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "panel_contract": {
                "confirmed": False,
                "draft": {
                    "panel_primary_key": ["date", "asset"],
                    "cross_section_time_key": "",
                    "asset_key": "",
                    "universe_membership_rule": "",
                },
                "missing_items": [],
            },
            "taxonomy_contract": {
                "confirmed": False,
                "draft": {
                    "group_taxonomy_reference": "",
                    "group_mapping_rule": "",
                    "taxonomy_note": "",
                },
                "missing_items": [],
            },
            "eligibility_contract": {
                "confirmed": False,
                "draft": {
                    "eligibility_base_rule": "",
                    "coverage_floor_rule": "",
                    "mask_audit_note": "",
                },
                "missing_items": [],
            },
            "shared_feature_base": {
                "confirmed": False,
                "draft": {
                    "shared_feature_outputs": [],
                    "shared_feature_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "",
                    "frozen_inputs_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_csf_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True, exist_ok=True)
    draft_path = stage_dir / CSF_DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_csf_data_ready_freeze_draft())
    return stage_dir


def build_csf_data_ready_from_mandate(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    mandate_dir = lineage_root / "01_mandate"
    stage_dir = scaffold_csf_data_ready(lineage_root)

    missing = [
        name
        for name in [
            "mandate.md",
            "research_scope.md",
            "research_route.yaml",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (mandate_dir / name).exists()
    ]
    if missing:
        raise ValueError(f"mandate artifacts missing before csf_data_ready build: {', '.join(missing)}")

    route_payload = yaml.safe_load((mandate_dir / "research_route.yaml").read_text(encoding="utf-8")) or {}
    if str(route_payload.get("research_route", "")).strip() != "cross_sectional_factor":
        raise ValueError("research_route must be cross_sectional_factor before csf_data_ready build")

    groups = _require_confirmed_freeze_groups(stage_dir)
    panel_contract = groups["panel_contract"]["draft"]
    taxonomy_contract = groups["taxonomy_contract"]["draft"]
    eligibility_contract = groups["eligibility_contract"]["draft"]
    shared_feature_base = groups["shared_feature_base"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    panel_primary_key = _string_list(panel_contract.get("panel_primary_key", []))
    cross_section_time_key = _required_draft_value(panel_contract, "cross_section_time_key")
    asset_key = _required_draft_value(panel_contract, "asset_key")
    universe_membership_rule = _required_draft_value(panel_contract, "universe_membership_rule")
    group_taxonomy_reference = str(
        taxonomy_contract.get("group_taxonomy_reference") or route_payload.get("group_taxonomy_reference", "")
    ).strip()
    group_mapping_rule = _required_draft_value(taxonomy_contract, "group_mapping_rule")
    taxonomy_note = _required_draft_value(taxonomy_contract, "taxonomy_note")
    eligibility_base_rule = _required_draft_value(eligibility_contract, "eligibility_base_rule")
    coverage_floor_rule = _required_draft_value(eligibility_contract, "coverage_floor_rule")
    mask_audit_note = _required_draft_value(eligibility_contract, "mask_audit_note")
    shared_feature_outputs = _string_list(shared_feature_base.get("shared_feature_outputs", []))
    shared_feature_note = _required_draft_value(shared_feature_base, "shared_feature_note")
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_inputs_note = _required_draft_value(delivery_contract, "frozen_inputs_note")

    (stage_dir / "panel_manifest.json").write_text(
        json.dumps(
            {
                "stage": "csf_data_ready",
                "lineage_id": lineage_root.name,
                "panel_primary_key": panel_primary_key,
                "cross_section_time_key": cross_section_time_key,
                "asset_key": asset_key,
                "shared_feature_outputs": shared_feature_outputs,
                "machine_artifacts": machine_artifacts,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    for name in [
        "asset_universe_membership.parquet",
        "cross_section_coverage.parquet",
        "eligibility_base_mask.parquet",
    ]:
        (stage_dir / name).write_text("placeholder parquet payload\n", encoding="utf-8")
    (stage_dir / "shared_feature_base").mkdir(exist_ok=True)
    if group_taxonomy_reference:
        (stage_dir / "asset_taxonomy_snapshot.parquet").write_text(
            f"group_taxonomy_reference={group_taxonomy_reference}\n",
            encoding="utf-8",
        )
    (stage_dir / "csf_data_contract.md").write_text(
        "\n".join(
            [
                "# CSF Data Contract",
                "",
                f"- Panel primary key: {panel_primary_key}",
                f"- Cross-section time key: {cross_section_time_key}",
                f"- Asset key: {asset_key}",
                f"- Universe membership rule: {universe_membership_rule}",
                f"- Eligibility base rule: {eligibility_base_rule}",
                f"- Coverage floor rule: {coverage_floor_rule}",
                f"- Shared feature outputs: {', '.join(shared_feature_outputs)}",
                f"- Shared feature note: {shared_feature_note}",
                f"- Group taxonomy reference: {group_taxonomy_reference}",
                f"- Group mapping rule: {group_mapping_rule}",
                f"- Taxonomy note: {taxonomy_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "csf_data_ready_gate_decision.md").write_text(
        "\n".join(
            [
                "# CSF Data Ready Gate Decision",
                "",
                "- Formal gate decision remains pending until review closure is written.",
                f"- Consumer stage: {consumer_stage}",
                f"- Frozen inputs note: {frozen_inputs_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# Artifact Catalog",
                "",
                "- panel_manifest.json",
                "- asset_universe_membership.parquet",
                "- cross_section_coverage.parquet",
                "- eligibility_base_mask.parquet",
                "- shared_feature_base/",
                "- asset_taxonomy_snapshot.parquet",
                "- csf_data_contract.md",
                "- csf_data_ready_gate_decision.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# Field Dictionary",
                "",
                f"- `panel_primary_key`: {panel_primary_key}",
                f"- `cross_section_time_key`: {cross_section_time_key}",
                f"- `asset_key`: {asset_key}",
                f"- `eligibility_base_rule`: {eligibility_base_rule}",
                f"- `coverage_floor_rule`: {coverage_floor_rule}",
                f"- `mask_audit_note`: {mask_audit_note}",
                f"- `shared_feature_outputs`: {shared_feature_outputs}",
                f"- `group_taxonomy_reference`: {group_taxonomy_reference}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    payload = yaml.safe_load((stage_dir / CSF_DATA_READY_FREEZE_DRAFT_FILE).read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [name for name in CSF_DATA_READY_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"csf_data_ready draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_data_ready draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]
