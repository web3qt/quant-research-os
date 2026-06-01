from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_PATH = ROOT / "contracts" / "paper_to_spec" / "paper_data_spec_contract.yaml"


@dataclass(frozen=True)
class PaperDataSpecValidationResult:
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


def validate_paper_data_spec(
    spec_path: Path,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> PaperDataSpecValidationResult:
    spec_path = spec_path.resolve()
    contract_path = contract_path.resolve()
    findings: list[tuple[str, str]] = []

    contract = _load_yaml_map(contract_path, "PAPER_DATA_SPEC_CONTRACT_INVALID", findings)
    payload = _load_yaml_map(spec_path, "PAPER_DATA_SPEC_INVALID_YAML", findings)
    if not isinstance(contract, dict) or not isinstance(payload, dict):
        return PaperDataSpecValidationResult(spec_path, contract_path, findings)

    findings.extend(_validate_top_level(payload, contract))
    findings.extend(_validate_source(payload.get("source"), contract))
    findings.extend(_validate_reading_coverage(payload.get("reading_coverage"), contract))
    findings.extend(_validate_target_market(payload.get("target_market"), contract))
    findings.extend(_validate_core_requirements(payload.get("core_data_requirements"), contract))
    findings.extend(_validate_optional_blocks(payload.get("triggered_optional_blocks"), contract))
    findings.extend(_validate_ambiguities(payload.get("ambiguities"), contract))
    findings.extend(_validate_implementation_handoff(payload.get("implementation_handoff"), contract))

    return PaperDataSpecValidationResult(spec_path, contract_path, findings)


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
            findings.append(("PAPER_DATA_SPEC_MISSING_FIELD", f"missing top-level field: {field}"))

    expected_version = contract.get("spec_version")
    if payload.get("spec_version") != expected_version:
        findings.append(
            (
                "PAPER_DATA_SPEC_INVALID_VERSION",
                f"spec_version must be {expected_version!r}",
            )
        )
    return findings


def _validate_source(source: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(source, dict):
        return [("PAPER_DATA_SPEC_INVALID_SECTION", "source must be a mapping")]

    findings = _require_fields("source", source, contract.get("required_source_fields", []))
    findings.extend(
        _validate_enum(
            "source.source_kind",
            source.get("source_kind"),
            contract.get("allowed_source_kinds", []),
        )
    )
    return findings


def _validate_reading_coverage(reading_coverage: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(reading_coverage, dict):
        return [("PAPER_DATA_SPEC_INVALID_SECTION", "reading_coverage must be a mapping")]

    findings = _require_fields(
        "reading_coverage",
        reading_coverage,
        contract.get("required_reading_coverage_fields", []),
    )
    findings.extend(
        _validate_enum(
            "reading_coverage.coverage_level",
            reading_coverage.get("coverage_level"),
            contract.get("allowed_coverage_levels", []),
        )
    )
    if reading_coverage.get("coverage_level") == "low":
        findings.append(
            (
                "PAPER_DATA_SPEC_READING_COVERAGE_LOW",
                "reading_coverage.coverage_level low is blocking for paper_data_spec",
            )
        )
    for list_field in [
        "extracted_pages",
        "covered_sections",
        "low_confidence_regions",
        "unread_or_unextracted_pages",
        "data_relevant_evidence",
    ]:
        if list_field in reading_coverage and not isinstance(reading_coverage.get(list_field), list):
            findings.append(
                (
                    "PAPER_DATA_SPEC_INVALID_TYPE",
                    f"reading_coverage.{list_field} must be a list",
                )
            )
    return findings


def _validate_target_market(target_market: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(target_market, dict):
        return [("PAPER_DATA_SPEC_INVALID_SECTION", "target_market must be a mapping")]

    findings = _require_fields(
        "target_market",
        target_market,
        contract.get("required_target_market_fields", []),
    )
    findings.extend(
        _validate_enum(
            "target_market.market_type",
            target_market.get("market_type"),
            contract.get("allowed_market_types", []),
        )
    )
    findings.extend(
        _validate_enum(
            "target_market.exchange_profile",
            target_market.get("exchange_profile"),
            contract.get("allowed_exchange_profiles", []),
        )
    )
    return findings


def _validate_core_requirements(core_requirements: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(core_requirements, dict):
        return [("PAPER_DATA_SPEC_INVALID_SECTION", "core_data_requirements must be a mapping")]

    findings: list[tuple[str, str]] = []
    strict_fields = contract.get("strict_blocking_fields", [])
    for field in contract.get("core_required_fields", []):
        if field not in core_requirements:
            findings.append(
                (
                    "PAPER_DATA_SPEC_MISSING_FIELD",
                    f"core_data_requirements.{field}: missing required core data field",
                )
            )
            continue
        findings.extend(_validate_requirement_entry(f"core_data_requirements.{field}", core_requirements[field], contract))
        if field in strict_fields:
            findings.extend(_validate_strict_requirement(field, core_requirements[field]))
    return findings


def _validate_optional_blocks(optional_blocks: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if optional_blocks is None:
        return [("PAPER_DATA_SPEC_INVALID_SECTION", "triggered_optional_blocks must be a list")]
    if not isinstance(optional_blocks, list):
        return [("PAPER_DATA_SPEC_INVALID_SECTION", "triggered_optional_blocks must be a list")]

    findings: list[tuple[str, str]] = []
    allowed_blocks = contract.get("optional_blocks", [])
    for index, block in enumerate(optional_blocks):
        path = f"triggered_optional_blocks[{index}]"
        if not isinstance(block, dict):
            findings.append(("PAPER_DATA_SPEC_INVALID_SECTION", f"{path} must be a mapping"))
            continue
        findings.extend(_require_fields(path, block, contract.get("required_optional_block_fields", [])))
        findings.extend(_validate_enum(f"{path}.block_name", block.get("block_name"), allowed_blocks))
        requirements = block.get("requirements")
        if not isinstance(requirements, dict):
            findings.append(("PAPER_DATA_SPEC_INVALID_SECTION", f"{path}.requirements must be a mapping"))
            continue
        for requirement_name, requirement in requirements.items():
            findings.extend(
                _validate_requirement_entry(
                    f"{path}.requirements.{requirement_name}",
                    requirement,
                    contract,
                )
            )
    return findings


def _validate_ambiguities(ambiguities: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(ambiguities, list):
        return [("PAPER_DATA_SPEC_INVALID_SECTION", "ambiguities must be a list")]
    findings: list[tuple[str, str]] = []
    for index, ambiguity in enumerate(ambiguities):
        path = f"ambiguities[{index}]"
        if not isinstance(ambiguity, dict):
            findings.append(("PAPER_DATA_SPEC_INVALID_SECTION", f"{path} must be a mapping"))
            continue
        findings.extend(_require_fields(path, ambiguity, contract.get("required_ambiguity_fields", [])))
        if "blocking" in ambiguity and not isinstance(ambiguity.get("blocking"), bool):
            findings.append(("PAPER_DATA_SPEC_INVALID_TYPE", f"{path}.blocking must be a boolean"))
    return findings


def _validate_implementation_handoff(implementation_handoff: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(implementation_handoff, dict):
        return [("PAPER_DATA_SPEC_INVALID_SECTION", "implementation_handoff must be a mapping")]
    findings = _require_fields(
        "implementation_handoff",
        implementation_handoff,
        contract.get("required_implementation_handoff_fields", []),
    )
    for list_field in ["raw_inputs", "derived_inputs", "validation_checks"]:
        if list_field in implementation_handoff and not isinstance(implementation_handoff.get(list_field), list):
            findings.append(
                (
                    "PAPER_DATA_SPEC_INVALID_TYPE",
                    f"implementation_handoff.{list_field} must be a list",
                )
            )
    return findings


def _validate_requirement_entry(path: str, entry: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(entry, dict):
        return [("PAPER_DATA_SPEC_INVALID_SECTION", f"{path} must be a mapping")]

    findings = _require_fields(path, entry, contract.get("required_requirement_fields", []))
    findings.extend(_validate_enum(f"{path}.status", entry.get("status"), contract.get("allowed_requirement_statuses", [])))
    findings.extend(_validate_enum(f"{path}.source", entry.get("source"), contract.get("allowed_requirement_sources", [])))

    if "evidence" in entry and not isinstance(entry.get("evidence"), list):
        findings.append(("PAPER_DATA_SPEC_INVALID_TYPE", f"{path}.evidence must be a list"))
    if "blocking_if_unknown" in entry and not isinstance(entry.get("blocking_if_unknown"), bool):
        findings.append(("PAPER_DATA_SPEC_INVALID_TYPE", f"{path}.blocking_if_unknown must be a boolean"))
    if entry.get("source") == "paper_stated" and not entry.get("evidence"):
        findings.append(("PAPER_DATA_SPEC_EVIDENCE_REQUIRED", f"{path}: paper_stated requires evidence"))
    return findings


def _validate_strict_requirement(field: str, entry: Any) -> list[tuple[str, str]]:
    if not isinstance(entry, dict):
        return []
    findings: list[tuple[str, str]] = []
    path = f"core_data_requirements.{field}"
    if entry.get("blocking_if_unknown") is not True:
        findings.append(("PAPER_DATA_SPEC_STRICT_FIELD_NOT_BLOCKING", f"{path}: strict field must block when unknown"))
    if entry.get("status") == "unknown":
        findings.append(("PAPER_DATA_SPEC_BLOCKING_UNKNOWN", f"{path}: strict blocking field is unknown"))
    return findings


def _require_fields(path: str, payload: dict[str, Any], fields: list[str]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for field in fields:
        if field not in payload:
            findings.append(("PAPER_DATA_SPEC_MISSING_FIELD", f"{path}.{field}: missing required field"))
    return findings


def _validate_enum(path: str, value: Any, allowed_values: list[str]) -> list[tuple[str, str]]:
    if value in allowed_values:
        return []
    return [
        (
            "PAPER_DATA_SPEC_INVALID_ENUM",
            f"{path} must be one of {allowed_values}",
        )
    ]
