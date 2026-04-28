from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


FORWARD_LABEL_ERROR = (
    "forward_label_base is a future-label artifact and 未来标签不能用于信号构造; "
    "TSS signals may only consume as-of feature inputs"
)


def validate_tss_signal_ready_semantics(
    author_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    del lineage_root
    author_formal_dir = author_formal_dir.resolve()
    errors: list[str] = []
    manifest_path = author_formal_dir / "signal_manifest.yaml"
    manifest = _load_yaml_mapping(manifest_path, errors)
    if manifest is None:
        return ArtifactValidationResult(errors=errors)

    if manifest.get("stage") != "tss_signal_ready":
        errors.append("signal_manifest.yaml: stage must be tss_signal_ready")
    if manifest.get("research_route") != "time_series_signal":
        errors.append("signal_manifest.yaml: research_route must be time_series_signal")

    errors.extend(_validate_no_forward_label_binding("signal_manifest.yaml", manifest))
    run_manifest_path = author_formal_dir / "run_manifest.json"
    if run_manifest_path.exists():
        run_manifest = _load_json_mapping(run_manifest_path, errors)
        if run_manifest is not None:
            errors.extend(_validate_no_forward_label_binding("run_manifest.json", run_manifest))

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


def _validate_no_forward_label_binding(artifact_name: str, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, value in _iter_input_binding_values(payload):
        if "forward_label_base" in value:
            errors.append(f"{artifact_name}: {FORWARD_LABEL_ERROR} ({path}={value!r})")
    return errors


def _iter_input_binding_values(payload: Any, path: str = "$") -> list[tuple[str, str]]:
    binding_keys = {
        "input_field_map",
        "input_roots",
        "input_root",
        "source",
        "source_artifact",
        "source_path",
        "source_root",
        "source_roots",
    }
    values: list[tuple[str, str]] = []
    if isinstance(payload, dict):
        for key, item in payload.items():
            child_path = f"{path}.{key}"
            if key in binding_keys:
                values.extend(_string_leaves(item, child_path))
                continue
            values.extend(_iter_input_binding_values(item, child_path))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            values.extend(_iter_input_binding_values(item, f"{path}[{index}]"))
    return values


def _string_leaves(value: Any, path: str) -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        values: list[tuple[str, str]] = []
        for key, item in value.items():
            values.extend(_string_leaves(item, f"{path}.{key}"))
        return values
    if isinstance(value, list):
        values: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            values.extend(_string_leaves(item, f"{path}[{index}]"))
        return values
    return []
