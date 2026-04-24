from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_CONTRACTS = {
    "idea_intake": ROOT / "contracts" / "artifacts" / "idea_intake_artifacts.yaml",
    "mandate": ROOT / "contracts" / "artifacts" / "mandate_artifacts.yaml",
}


@dataclass(frozen=True)
class ArtifactValidationResult:
    errors: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


class ArtifactContractError(ValueError):
    pass


def load_artifact_contract(stage: str) -> dict[str, Any]:
    path = ARTIFACT_CONTRACTS.get(stage)
    if path is None:
        raise ArtifactContractError(f"unsupported artifact contract stage: {stage}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_stage_artifacts(stage_dir: Path, contract: dict[str, Any]) -> ArtifactValidationResult:
    errors: list[str] = []
    stage_dir = stage_dir.resolve()

    for artifact_name, artifact_contract in contract.get("artifacts", {}).items():
        artifact_path = stage_dir / artifact_name
        if not artifact_path.exists():
            errors.append(f"{artifact_name}: missing required artifact")
            continue

        artifact_type = artifact_contract.get("type")
        if artifact_type == "markdown":
            errors.extend(_validate_markdown_artifact(artifact_name, artifact_path, artifact_contract))
            continue
        if artifact_type == "yaml":
            errors.extend(_validate_yaml_artifact(artifact_name, artifact_path, artifact_contract, contract))
            continue
        if artifact_type == "json":
            errors.extend(_validate_mapping_artifact(artifact_name, artifact_path, artifact_contract, contract, parser="json"))
            continue
        if artifact_type == "toml":
            errors.extend(_validate_mapping_artifact(artifact_name, artifact_path, artifact_contract, contract, parser="toml"))
            continue
        errors.append(f"{artifact_name}: unsupported artifact type {artifact_type!r}")

    return ArtifactValidationResult(errors=errors)


def _validate_markdown_artifact(artifact_name: str, artifact_path: Path, artifact_contract: dict[str, Any]) -> list[str]:
    content = artifact_path.read_text(encoding="utf-8")
    sections = _markdown_sections(content)
    errors: list[str] = []
    for section in artifact_contract.get("required_sections", []):
        if section not in sections:
            errors.append(f"{artifact_name}: missing markdown section {section}")
    return errors


def _markdown_sections(content: str) -> set[str]:
    sections: set[str] = set()
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        title = stripped.lstrip("#").strip()
        if title:
            sections.add(title)
    return sections


def _validate_yaml_artifact(
    artifact_name: str,
    artifact_path: Path,
    artifact_contract: dict[str, Any],
    stage_contract: dict[str, Any],
) -> list[str]:
    return _validate_mapping_artifact(artifact_name, artifact_path, artifact_contract, stage_contract, parser="yaml")


def _validate_mapping_artifact(
    artifact_name: str,
    artifact_path: Path,
    artifact_contract: dict[str, Any],
    stage_contract: dict[str, Any],
    *,
    parser: str,
) -> list[str]:
    errors: list[str] = []
    try:
        payload = _load_mapping_payload(artifact_path, parser=parser)
    except Exception as exc:
        return [f"{artifact_name}: {parser} parse failed: {exc}"]

    if not isinstance(payload, dict):
        return [f"{artifact_name}: expected {parser} map, found {type(payload).__name__}"]

    if _unknown_top_level_fields_forbidden(artifact_contract, stage_contract):
        allowed = _allowed_top_level_fields(artifact_contract)
        for key in payload:
            if key not in allowed:
                errors.append(f"{artifact_name}: unknown top-level field {key}")

    for field in artifact_contract.get("fields", []):
        field_path = str(field["path"])
        exists, value = _resolve_field(payload, field_path)
        if not exists:
            errors.append(f"{artifact_name}: missing required field {field_path}")
            continue
        errors.extend(_validate_field_value(artifact_name, field_path, value, field))

    errors.extend(_validate_declared_groups(artifact_name, payload, artifact_contract))
    return errors


def _load_mapping_payload(path: Path, *, parser: str) -> Any:
    if parser == "yaml":
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    if parser == "json":
        return json.loads(path.read_text(encoding="utf-8"))
    if parser == "toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise ArtifactContractError(f"unsupported mapping parser: {parser}")


def _unknown_top_level_fields_forbidden(artifact_contract: dict[str, Any], stage_contract: dict[str, Any]) -> bool:
    artifact_policy = artifact_contract.get("unknown_top_level_fields")
    if artifact_policy is not None:
        return artifact_policy == "forbid"
    machine_policy = stage_contract.get("unknown_machine_top_level_fields")
    if machine_policy is not None:
        return machine_policy == "forbid"
    return stage_contract.get("unknown_yaml_top_level_fields") == "forbid"


def _allowed_top_level_fields(artifact_contract: dict[str, Any]) -> set[str]:
    return {str(field["path"]).split(".", 1)[0] for field in artifact_contract.get("fields", [])}


def _resolve_field(payload: dict[str, Any], field_path: str) -> tuple[bool, Any]:
    value: Any = payload
    for part in field_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def _validate_field_value(artifact_name: str, field_path: str, value: Any, field: dict[str, Any]) -> list[str]:
    expected_type = str(field["type"])
    errors: list[str] = []
    if expected_type == "enum":
        values = list(field.get("values", []))
        if value not in values:
            errors.append(f"{artifact_name}: {field_path} expected one of {values}, found {value!r}")
        return errors

    if not _matches_type(value, expected_type):
        errors.append(
            f"{artifact_name}: {field_path} expected {expected_type}, found {type(value).__name__}"
        )
        return errors

    allowed_values = field.get("allowed_values_if_nonempty")
    if allowed_values:
        errors.extend(_validate_allowed_values(artifact_name, field_path, value, list(allowed_values)))
    return errors


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "map":
        return isinstance(value, dict)
    if expected_type == "list[string]":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if expected_type == "list[map]":
        return isinstance(value, list) and all(isinstance(item, dict) for item in value)
    return False


def _validate_allowed_values(artifact_name: str, field_path: str, value: Any, allowed_values: list[str]) -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if value and value not in allowed_values:
            errors.append(f"{artifact_name}: {field_path} unsupported value {value!r}")
        return errors
    if isinstance(value, list):
        for item in value:
            if item and item not in allowed_values:
                errors.append(f"{artifact_name}: {field_path} unsupported value {item!r}")
    return errors


def _validate_declared_groups(artifact_name: str, payload: dict[str, Any], artifact_contract: dict[str, Any]) -> list[str]:
    groups = artifact_contract.get("groups")
    if not groups:
        return []
    observed = payload.get("groups")
    if not isinstance(observed, dict):
        return [f"{artifact_name}: groups expected map, found {type(observed).__name__}"]
    missing = [group for group in groups if group not in observed]
    return [f"{artifact_name}: missing group {group}" for group in missing]
