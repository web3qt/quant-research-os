from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.paper_backtest_implementation_spec_runtime import (
    validate_paper_backtest_implementation_spec,
)
from runtime.tools.paper_backtest_spec_runtime import validate_paper_backtest_spec
from runtime.tools.paper_data_spec_runtime import validate_paper_data_spec
from runtime.tools.paper_signal_spec_runtime import validate_paper_signal_spec
from runtime.tools.paper_test_evidence_spec_runtime import validate_paper_test_evidence_spec
from runtime.tools.paper_train_freeze_spec_runtime import validate_paper_train_freeze_spec


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_PATH = ROOT / "contracts" / "paper_to_spec" / "paper_auto_implementation_handoff_contract.yaml"
IMPLEMENTATION_ACTIONS = {
    "validate_researcher_data",
    "run_agent_data_acquisition",
    "generate_active_repo_backtest_scaffold",
}
UPSTREAM_VALIDATORS = {
    "paper_data_spec": validate_paper_data_spec,
    "paper_signal_spec": validate_paper_signal_spec,
    "paper_train_freeze_spec": validate_paper_train_freeze_spec,
    "paper_test_evidence_spec": validate_paper_test_evidence_spec,
    "paper_backtest_spec": validate_paper_backtest_spec,
    "paper_backtest_implementation_spec": validate_paper_backtest_implementation_spec,
}


@dataclass(frozen=True)
class PaperAutoImplementationHandoffValidationResult:
    spec_path: Path
    contract_path: Path
    findings: list[tuple[str, str]]

    @property
    def valid(self) -> bool:
        return not self.findings

    @property
    def reason_codes(self) -> list[str]:
        observed: list[str] = []
        for code, _ in self.findings:
            if code not in observed:
                observed.append(code)
        return observed


def validate_paper_auto_implementation_handoff(
    spec_path: Path,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> PaperAutoImplementationHandoffValidationResult:
    spec_path = spec_path.resolve()
    contract_path = contract_path.resolve()
    findings: list[tuple[str, str]] = []

    contract = _load_yaml_map(contract_path, "PAPER_AUTO_IMPLEMENTATION_HANDOFF_CONTRACT_INVALID", findings)
    payload = _load_yaml_map(spec_path, "PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_YAML", findings)
    if not isinstance(contract, dict) or not isinstance(payload, dict):
        return PaperAutoImplementationHandoffValidationResult(spec_path, contract_path, findings)

    findings.extend(_validate_top_level(payload, contract))
    findings.extend(_validate_source(payload.get("source"), contract))
    findings.extend(_validate_paper_spec_chain(payload.get("paper_spec_chain"), contract, spec_path))
    findings.extend(_validate_implementation_decision(payload.get("implementation_decision"), contract))
    findings.extend(_validate_data_readiness_brief(payload.get("data_readiness_brief"), contract))
    findings.extend(_validate_researcher_data_response(payload.get("researcher_data_response"), contract))
    findings.extend(_validate_agent_acquisition_plan(payload.get("agent_acquisition_plan"), contract))
    findings.extend(_validate_acquisition_provenance(payload.get("acquisition_provenance"), contract))
    findings.extend(_validate_active_repo_boundary(payload.get("active_repo_boundary"), contract))
    findings.extend(_validate_forbidden_output_paths(payload))
    findings.extend(_validate_ambiguities(payload.get("ambiguities"), contract))
    findings.extend(_validate_allowed_next_action(payload, contract))
    findings.extend(_validate_implementation_handoff(payload.get("implementation_handoff"), contract))

    return PaperAutoImplementationHandoffValidationResult(spec_path, contract_path, findings)


def _load_yaml_map(path: Path, code: str, findings: list[tuple[str, str]]) -> dict[str, Any] | None:
    if not path.exists():
        findings.append((code, f"missing yaml file: {path}"))
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        findings.append((code, f"{path}: invalid yaml: {exc}"))
        return None
    if not isinstance(payload, dict):
        findings.append((code, f"{path}: yaml root must be a mapping"))
        return None
    return payload


def _validate_top_level(payload: dict[str, Any], contract: dict[str, Any]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for field in contract.get("required_top_level_fields", []):
        if field not in payload:
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_MISSING_FIELD", f"missing top-level field: {field}"))

    expected_version = contract.get("spec_version")
    if payload.get("spec_version") != expected_version:
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_VERSION", f"spec_version must be {expected_version!r}"))
    return findings


def _validate_source(source: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(source, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "source must be a mapping")]
    findings = _require_fields("source", source, contract.get("required_source_fields", []))
    findings.extend(_validate_enum("source.source_kind", source.get("source_kind"), contract.get("allowed_source_kinds", [])))
    return findings


def _validate_paper_spec_chain(chain: Any, contract: dict[str, Any], handoff_path: Path) -> list[tuple[str, str]]:
    if not isinstance(chain, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "paper_spec_chain must be a mapping")]

    findings: list[tuple[str, str]] = []
    for field in contract.get("required_paper_spec_chain_fields", []):
        reference = chain.get(field)
        path = f"paper_spec_chain.{field}"
        if not isinstance(reference, dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"{path} must be a mapping"))
            continue
        findings.extend(_require_fields(path, reference, contract.get("required_spec_reference_fields", [])))
        findings.extend(
            _validate_enum(
                f"{path}.validation_status",
                reference.get("validation_status"),
                contract.get("allowed_spec_validation_statuses", []),
            )
        )
        if reference.get("validation_status") != "valid":
            findings.append(
                (
                    "PAPER_AUTO_IMPLEMENTATION_HANDOFF_SPEC_CHAIN_NOT_VALID",
                    f"{path}.validation_status must be valid before implementation prompt",
                )
            )
        reference_path = reference.get("path")
        if not isinstance(reference_path, str) or not reference_path.strip():
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.path must be a non-empty string"))
            continue
        resolved_path = _resolve_reference_path(reference_path, handoff_path)
        if not resolved_path.exists():
            findings.append(
                (
                    "PAPER_AUTO_IMPLEMENTATION_HANDOFF_UPSTREAM_SPEC_MISSING",
                    f"{path}.path does not exist: {reference_path}",
                )
            )
            continue
        validator = UPSTREAM_VALIDATORS.get(field)
        if validator is not None:
            result = validator(resolved_path)
            if not result.valid:
                findings.append(
                    (
                        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_UPSTREAM_SPEC_INVALID",
                        f"{path}.path failed upstream validator with reason codes {result.reason_codes}",
                    )
                )
        if not isinstance(reference.get("digest"), str) or not reference.get("digest", "").strip():
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.digest must be a non-empty string"))
    return findings


def _validate_implementation_decision(decision: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(decision, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "implementation_decision must be a mapping")]
    findings = _require_fields(
        "implementation_decision",
        decision,
        contract.get("required_implementation_decision_fields", []),
    )
    findings.extend(
        _validate_enum(
            "implementation_decision.decision",
            decision.get("decision"),
            contract.get("allowed_implementation_decisions", []),
        )
    )
    if decision.get("decision") == "accepted" and not decision.get("evidence"):
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_CONSENT_EVIDENCE_REQUIRED",
                "implementation_decision.evidence is required when decision is accepted",
            )
        )
    return findings


def _validate_data_readiness_brief(brief: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(brief, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "data_readiness_brief must be a mapping")]

    findings = _require_fields(
        "data_readiness_brief",
        brief,
        contract.get("required_data_readiness_brief_fields", []),
    )
    for list_field in ["required_datasets", "optional_datasets", "blocking_gaps"]:
        if list_field in brief and not isinstance(brief.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"data_readiness_brief.{list_field} must be a list"))
    for field_name in ["required_datasets", "optional_datasets"]:
        datasets = brief.get(field_name, [])
        if not isinstance(datasets, list):
            continue
        for index, dataset in enumerate(datasets):
            findings.extend(_validate_data_item(f"data_readiness_brief.{field_name}[{index}]", dataset, contract))
    return findings


def _validate_data_item(path: str, item: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(item, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"{path} must be a mapping")]
    findings = _require_fields(path, item, contract.get("required_data_item_fields", []))
    for list_field in ["fields", "provenance_requirements"]:
        if list_field in item and not isinstance(item.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.{list_field} must be a list"))
    for map_field in ["market_scope", "symbol_universe", "time_range", "source_constraints"]:
        if map_field in item and not isinstance(item.get(map_field), dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.{map_field} must be a mapping"))
    if "required" in item and not isinstance(item.get("required"), bool):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.required must be a boolean"))
    if "blocking" in item and not isinstance(item.get("blocking"), bool):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.blocking must be a boolean"))
    return findings


def _validate_researcher_data_response(response: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(response, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "researcher_data_response must be a mapping")]
    findings = _require_fields(
        "researcher_data_response",
        response,
        contract.get("required_researcher_data_response_fields", []),
    )
    findings.extend(
        _validate_enum(
            "researcher_data_response.status",
            response.get("status"),
            contract.get("allowed_researcher_data_statuses", []),
        )
    )
    for map_field in ["provided_paths", "access_instructions"]:
        if map_field in response and not isinstance(response.get(map_field), dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"researcher_data_response.{map_field} must be a mapping"))
    for list_field in ["missing_datasets", "evidence"]:
        if list_field in response and not isinstance(response.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"researcher_data_response.{list_field} must be a list"))
    return findings


def _validate_agent_acquisition_plan(plan: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(plan, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "agent_acquisition_plan must be a mapping")]
    findings = _require_fields(
        "agent_acquisition_plan",
        plan,
        contract.get("required_agent_acquisition_plan_fields", []),
    )
    findings.extend(
        _validate_enum(
            "agent_acquisition_plan.status",
            plan.get("status"),
            contract.get("allowed_acquisition_plan_statuses", []),
        )
    )
    sources = plan.get("sources", [])
    if not isinstance(sources, list):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", "agent_acquisition_plan.sources must be a list"))
    else:
        for index, source in enumerate(sources):
            findings.extend(_validate_acquisition_source(f"agent_acquisition_plan.sources[{index}]", source, contract))
    findings.extend(_validate_acquisition_approval(plan.get("approval"), contract))
    if "limitations" in plan and not isinstance(plan.get("limitations"), list):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", "agent_acquisition_plan.limitations must be a list"))
    return findings


def _validate_acquisition_source(path: str, source: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(source, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"{path} must be a mapping")]
    findings = _require_fields(path, source, contract.get("required_acquisition_source_fields", []))
    for list_field in ["symbols", "fields", "expected_artifacts"]:
        if list_field in source and not isinstance(source.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.{list_field} must be a list"))
    if "time_range" in source and not isinstance(source.get("time_range"), dict):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.time_range must be a mapping"))
    if "approval_required" in source and source.get("approval_required") is not True:
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_APPROVAL_REQUIRED", f"{path}.approval_required must be true"))
    return findings


def _validate_acquisition_approval(approval: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(approval, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "agent_acquisition_plan.approval must be a mapping")]
    findings = _require_fields(
        "agent_acquisition_plan.approval",
        approval,
        contract.get("required_acquisition_approval_fields", []),
    )
    if "approved" in approval and not isinstance(approval.get("approved"), bool):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", "agent_acquisition_plan.approval.approved must be a boolean"))
    if approval.get("approved") is True and not approval.get("evidence"):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_ACQUISITION_APPROVAL_EVIDENCE_REQUIRED", "agent_acquisition_plan.approval.evidence is required when approved is true"))
    return findings


def _validate_acquisition_provenance(provenance: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(provenance, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "acquisition_provenance must be a mapping")]
    findings = _require_fields(
        "acquisition_provenance",
        provenance,
        contract.get("required_acquisition_provenance_fields", []),
    )
    findings.extend(
        _validate_enum(
            "acquisition_provenance.run_status",
            provenance.get("run_status"),
            contract.get("allowed_acquisition_run_statuses", []),
        )
    )
    source_records = provenance.get("source_records", [])
    if not isinstance(source_records, list):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", "acquisition_provenance.source_records must be a list"))
    else:
        for index, record in enumerate(source_records):
            findings.extend(_validate_acquisition_source_record(f"acquisition_provenance.source_records[{index}]", record, contract))
    for map_field in ["coverage"]:
        if map_field in provenance and not isinstance(provenance.get(map_field), dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"acquisition_provenance.{map_field} must be a mapping"))
    return findings


def _validate_acquisition_source_record(path: str, record: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(record, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"{path} must be a mapping")]
    findings = _require_fields(path, record, contract.get("required_acquisition_source_record_fields", []))
    for list_field in ["symbols", "fields", "expected_artifacts"]:
        if list_field in record and not isinstance(record.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.{list_field} must be a list"))
    for map_field in ["time_range", "coverage"]:
        if map_field in record and not isinstance(record.get(map_field), dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.{map_field} must be a mapping"))
    return findings


def _validate_active_repo_boundary(boundary: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(boundary, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "active_repo_boundary must be a mapping")]
    findings = _require_fields(
        "active_repo_boundary",
        boundary,
        contract.get("required_active_repo_boundary_fields", []),
    )
    findings.extend(
        _validate_enum(
            "active_repo_boundary.repo_role",
            boundary.get("repo_role"),
            contract.get("allowed_active_repo_roles", []),
        )
    )
    target_root = str(boundary.get("target_root", ""))
    forbidden_root = str(boundary.get("forbidden_root", ""))
    if target_root and forbidden_root and Path(target_root).resolve() == Path(forbidden_root).resolve():
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
                "active_repo_boundary.target_root must not equal forbidden_root",
            )
        )
    return findings


def _validate_ambiguities(ambiguities: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(ambiguities, list):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "ambiguities must be a list")]
    findings: list[tuple[str, str]] = []
    for index, ambiguity in enumerate(ambiguities):
        path = f"ambiguities[{index}]"
        if not isinstance(ambiguity, dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"{path} must be a mapping"))
            continue
        findings.extend(_require_fields(path, ambiguity, contract.get("required_ambiguity_fields", [])))
        if "blocking" in ambiguity and not isinstance(ambiguity.get("blocking"), bool):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.blocking must be a boolean"))
    return findings


def _validate_allowed_next_action(payload: dict[str, Any], contract: dict[str, Any]) -> list[tuple[str, str]]:
    action = payload.get("allowed_next_action")
    findings = _validate_enum("allowed_next_action", action, contract.get("allowed_next_actions", []))
    if action not in IMPLEMENTATION_ACTIONS:
        return findings

    if payload.get("implementation_decision", {}).get("decision") != "accepted":
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_IMPLEMENTATION_NOT_ACCEPTED",
                "implementation actions require implementation_decision.decision accepted",
            )
        )
    if _has_blocking_gap(payload):
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_DATA_READINESS_BLOCKED",
                "implementation actions are blocked while data_readiness_brief.blocking_gaps is non-empty",
            )
        )
    if _has_blocking_ambiguity(payload):
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_BLOCKING_AMBIGUITY",
                "implementation actions are blocked while ambiguities contains blocking=true",
            )
        )
    if action == "run_agent_data_acquisition":
        findings.extend(_validate_agent_acquisition_allowed(payload))
    if action == "generate_active_repo_backtest_scaffold":
        findings.extend(_validate_scaffold_allowed(payload))
    return findings


def _validate_agent_acquisition_allowed(payload: dict[str, Any]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    response_status = payload.get("researcher_data_response", {}).get("status")
    plan = payload.get("agent_acquisition_plan", {})
    approval = plan.get("approval", {})
    if response_status != "cannot_provide":
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_RESEARCHER_DATA_NOT_DECLINED",
                "run_agent_data_acquisition requires researcher_data_response.status cannot_provide",
            )
        )
    if plan.get("status") != "approved" or approval.get("approved") is not True:
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_ACQUISITION_NOT_APPROVED",
                "run_agent_data_acquisition requires approved agent_acquisition_plan",
            )
        )
    if not plan.get("sources"):
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_ACQUISITION_PLAN_EMPTY",
                "run_agent_data_acquisition requires at least one acquisition source",
            )
        )
    return findings


def _validate_scaffold_allowed(payload: dict[str, Any]) -> list[tuple[str, str]]:
    response_status = payload.get("researcher_data_response", {}).get("status")
    provided_paths = payload.get("researcher_data_response", {}).get("provided_paths")
    missing_datasets = payload.get("researcher_data_response", {}).get("missing_datasets")
    acquisition_status = payload.get("acquisition_provenance", {}).get("run_status")
    researcher_data_ready = (
        response_status == "provided"
        and isinstance(provided_paths, dict)
        and bool(provided_paths)
        and isinstance(missing_datasets, list)
        and not missing_datasets
    )
    if researcher_data_ready or acquisition_status == "succeeded":
        return []
    return [
        (
            "PAPER_AUTO_IMPLEMENTATION_HANDOFF_DATA_NOT_READY",
            "generate_active_repo_backtest_scaffold requires researcher-provided data or successful agent acquisition",
        )
    ]


def _validate_implementation_handoff(handoff: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(handoff, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "implementation_handoff must be a mapping")]
    findings = _require_fields(
        "implementation_handoff",
        handoff,
        contract.get("required_implementation_handoff_fields", []),
    )
    for list_field in ["implementation_inputs", "implementation_outputs", "validation_checks"]:
        if list_field in handoff and not isinstance(handoff.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"implementation_handoff.{list_field} must be a list"))
    findings.extend(
        _validate_enum(
            "implementation_handoff.next_stage_recommendation",
            handoff.get("next_stage_recommendation"),
            contract.get("allowed_next_stage_recommendations", []),
        )
    )
    return findings


def _validate_forbidden_output_paths(payload: dict[str, Any]) -> list[tuple[str, str]]:
    boundary = payload.get("active_repo_boundary", {})
    if not isinstance(boundary, dict):
        return []
    forbidden_root = boundary.get("forbidden_root")
    if not isinstance(forbidden_root, str) or not forbidden_root:
        return []

    findings: list[tuple[str, str]] = []
    target_root = boundary.get("target_root")
    if isinstance(target_root, str) and _path_is_under_or_equal(target_root, forbidden_root):
        findings.append(
            (
                "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
                "active_repo_boundary.target_root must not be under forbidden_root",
            )
        )

    plan = payload.get("agent_acquisition_plan", {})
    if isinstance(plan, dict) and isinstance(plan.get("sources"), list):
        for index, source in enumerate(plan["sources"]):
            if not isinstance(source, dict):
                continue
            storage_target = source.get("storage_target")
            if isinstance(storage_target, str) and _path_is_under_or_equal(storage_target, forbidden_root):
                findings.append(
                    (
                        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
                        f"agent_acquisition_plan.sources[{index}].storage_target must not be under forbidden_root",
                    )
                )

    handoff = payload.get("implementation_handoff", {})
    if isinstance(handoff, dict) and isinstance(handoff.get("implementation_outputs"), list):
        for index, output_path in enumerate(handoff["implementation_outputs"]):
            if isinstance(output_path, str) and _path_is_under_or_equal(output_path, forbidden_root):
                findings.append(
                    (
                        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
                        f"implementation_handoff.implementation_outputs[{index}] must not be under forbidden_root",
                    )
                )
    return findings


def _has_blocking_gap(payload: dict[str, Any]) -> bool:
    gaps = payload.get("data_readiness_brief", {}).get("blocking_gaps", [])
    return isinstance(gaps, list) and bool(gaps)


def _has_blocking_ambiguity(payload: dict[str, Any]) -> bool:
    ambiguities = payload.get("ambiguities", [])
    if not isinstance(ambiguities, list):
        return False
    return any(isinstance(item, dict) and item.get("blocking") is True for item in ambiguities)


def _resolve_reference_path(reference_path: str, handoff_path: Path) -> Path:
    path = Path(reference_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    candidates = [ROOT / path, handoff_path.parent / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _path_is_under_or_equal(path_value: str, root_value: str) -> bool:
    path = Path(path_value).expanduser()
    root = Path(root_value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    if not root.is_absolute():
        root = ROOT / root
    try:
        resolved_path = path.resolve()
        resolved_root = root.resolve()
    except OSError:
        return False
    return resolved_path == resolved_root or resolved_root in resolved_path.parents


def _require_fields(path: str, payload: dict[str, Any], fields: list[str]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for field in fields:
        if field not in payload:
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_MISSING_FIELD", f"{path}.{field}: missing required field"))
    return findings


def _validate_enum(path: str, value: Any, allowed_values: list[str]) -> list[tuple[str, str]]:
    if value in allowed_values:
        return []
    return [
        (
            "PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_ENUM",
            f"{path} must be one of {allowed_values}",
        )
    ]
