from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.stage_content_gate import check_structural_gates


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must load to a mapping")
    return payload


def _load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must load to a mapping")
    return payload


def _read_parquet_column_values(path: Path, column: str) -> set[str]:
    import pyarrow.parquet as pq

    table = pq.read_table(path, columns=[column])
    return {str(value).strip() for value in table.column(column).to_pylist() if str(value).strip()}


def _check_csf_data_ready_route_binding(lineage_root: Path, author_formal_dir: Path) -> list[str]:
    route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
    if not route_path.exists():
        return ["CSF-DATA-BIND-001: mandate research_route.yaml is missing for csf_data_ready route binding"]
    route_payload = _load_yaml_mapping(route_path)
    if route_payload.get("research_route") != "cross_sectional_factor":
        return [
            "CSF-DATA-BIND-001: csf_data_ready requires mandate research_route.yaml to stay on cross_sectional_factor"
        ]

    findings: list[str] = []
    findings.extend(_check_csf_data_ready_manifest_binding(author_formal_dir))
    findings.extend(_check_csf_data_ready_taxonomy_binding(route_payload, author_formal_dir))
    return findings


def _check_csf_data_ready_manifest_binding(author_formal_dir: Path) -> list[str]:
    findings: list[str] = []
    panel_manifest_path = author_formal_dir / "panel_manifest.json"
    run_manifest_path = author_formal_dir / "run_manifest.json"

    if panel_manifest_path.exists():
        try:
            panel_manifest = _load_json_mapping(panel_manifest_path)
        except Exception as exc:
            findings.append(f"CSF-DATA-BIND-004: panel_manifest.json binding evaluation failed: {exc}")
        else:
            if panel_manifest.get("stage") != "csf_data_ready":
                findings.append("CSF-DATA-BIND-004: panel_manifest.json stage must be csf_data_ready")

    if run_manifest_path.exists():
        try:
            run_manifest = _load_json_mapping(run_manifest_path)
        except Exception as exc:
            findings.append(f"CSF-DATA-BIND-005: run_manifest.json binding evaluation failed: {exc}")
        else:
            if run_manifest.get("source_stage") != "mandate":
                findings.append("CSF-DATA-BIND-005: run_manifest.json source_stage must be mandate")
            if run_manifest.get("consumer_stage") != "csf_signal_ready":
                findings.append("CSF-DATA-BIND-006: run_manifest.json consumer_stage must be csf_signal_ready")

    return findings


def _check_csf_data_ready_taxonomy_binding(route_payload: dict[str, Any], author_formal_dir: Path) -> list[str]:
    neutralization_policy = str(route_payload.get("neutralization_policy", "")).strip()
    if neutralization_policy != "group_neutral":
        return []

    findings: list[str] = []
    expected_reference = str(route_payload.get("group_taxonomy_reference", "")).strip()
    if not expected_reference:
        findings.append(
            "CSF-DATA-BIND-002: mandate group_taxonomy_reference must be non-empty when neutralization_policy is group_neutral"
        )

    taxonomy_path = author_formal_dir / "asset_taxonomy_snapshot.parquet"
    if not taxonomy_path.exists():
        findings.append("CSF-DATA-BIND-002: group_neutral csf_data_ready requires asset_taxonomy_snapshot.parquet")
        return findings

    if not expected_reference:
        return findings

    try:
        observed_references = _read_parquet_column_values(taxonomy_path, "group_taxonomy_reference")
    except Exception as exc:
        findings.append(f"CSF-DATA-BIND-003: asset_taxonomy_snapshot.parquet binding evaluation failed: {exc}")
        return findings

    if observed_references != {expected_reference}:
        findings.append(
            "CSF-DATA-BIND-003: asset_taxonomy_snapshot.group_taxonomy_reference must match mandate "
            f"group_taxonomy_reference; observed={sorted(observed_references)!r} expected={expected_reference!r}"
        )
    return findings


def _check_csf_signal_ready_route_binding(lineage_root: Path, author_formal_dir: Path) -> list[str]:
    route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
    contract_path = author_formal_dir / "route_inheritance_contract.yaml"
    if not route_path.exists():
        return ["CSF-SIGNAL-BIND-001: mandate research_route.yaml is missing for route inheritance validation"]
    if not contract_path.exists():
        return ["CSF-SIGNAL-BIND-001: route_inheritance_contract.yaml is missing"]

    try:
        route_payload = _load_yaml_mapping(route_path)
        contract_payload = _load_yaml_mapping(contract_path)
    except Exception as exc:
        return [f"CSF-SIGNAL-BIND-001: route inheritance contract evaluation failed: {exc}"]
    findings: list[str] = []

    for field in (
        "research_route",
        "factor_role",
        "factor_structure",
        "portfolio_expression",
        "neutralization_policy",
        "target_strategy_reference",
        "group_taxonomy_reference",
    ):
        route_value = route_payload.get(field)
        contract_value = contract_payload.get(field)
        if route_value != contract_value:
            findings.append(
                f"CSF-SIGNAL-BIND-001: route_inheritance_contract.yaml field {field} does not match mandate research_route.yaml; observed={contract_value!r} expected={route_value!r}"
            )

    return findings


def _check_csf_train_freeze_signal_binding(lineage_root: Path, author_formal_dir: Path) -> list[str]:
    signal_contract_path = lineage_root / "03_csf_signal_ready" / "author" / "formal" / "factor_contract.md"
    freeze_path = author_formal_dir / "csf_train_freeze.yaml"
    if not freeze_path.exists():
        return ["CSF-TRAIN-BIND-001: csf_train_freeze.yaml is missing"]

    try:
        freeze_payload = _load_yaml_mapping(freeze_path)
    except Exception as exc:
        return [f"CSF-TRAIN-BIND-001: csf_train_freeze upstream binding evaluation failed: {exc}"]
    governance = freeze_payload.get("search_governance_contract", {})
    if not isinstance(governance, dict):
        return ["CSF-TRAIN-BIND-001: search_governance_contract must be a mapping"]

    findings: list[str] = []
    frozen_reference = governance.get("frozen_signal_contract_reference")
    expected_reference = "03_csf_signal_ready/author/formal/factor_contract.md"
    if not isinstance(frozen_reference, str) or not frozen_reference.strip():
        findings.append("CSF-TRAIN-BIND-001: frozen_signal_contract_reference must be explicit")
    elif frozen_reference.strip() != expected_reference:
        findings.append(
            f"CSF-TRAIN-BIND-001: frozen_signal_contract_reference must bind to {expected_reference}; observed={frozen_reference!r}"
        )

    if not signal_contract_path.exists():
        findings.append("CSF-TRAIN-BIND-002: referenced signal contract is missing under 03_csf_signal_ready/author/formal")

    train_governable_axes = governance.get("train_governable_axes", [])
    non_governable_axes = governance.get("non_governable_axes_after_signal", [])
    if isinstance(train_governable_axes, list) and isinstance(non_governable_axes, list):
        overlap = sorted(set(map(str, train_governable_axes)) & set(map(str, non_governable_axes)))
        if overlap:
            findings.append(
                f"CSF-TRAIN-BIND-003: train_governable_axes overlap non_governable_axes_after_signal; observed={overlap!r}"
            )

    return findings


def validate_upstream_bindings(
    *,
    stage: str,
    lineage_root: Path,
    author_formal_dir: Path,
    structural_binding_checks: list[dict[str, Any]],
) -> list[str]:
    findings = check_structural_gates(author_formal_dir, structural_binding_checks)

    if stage == "csf_data_ready":
        findings.extend(_check_csf_data_ready_route_binding(lineage_root, author_formal_dir))
    if (author_formal_dir / "route_inheritance_contract.yaml").exists() or structural_binding_checks:
        findings.extend(_check_csf_signal_ready_route_binding(lineage_root, author_formal_dir))
    if (author_formal_dir / "csf_train_freeze.yaml").exists():
        findings.extend(_check_csf_train_freeze_signal_binding(lineage_root, author_formal_dir))

    return findings
