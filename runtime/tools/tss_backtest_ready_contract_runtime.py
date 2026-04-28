from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


def validate_tss_backtest_ready_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    del lineage_root
    stage_formal_dir = stage_formal_dir.resolve()
    errors: list[str] = []
    payload = _load_yaml_mapping(stage_formal_dir / "strategy_contract.yaml", errors)
    if payload is None:
        return ArtifactValidationResult(errors=errors)
    if not str(payload.get("net_after_cost_rule", "")).strip():
        errors.append("strategy_contract.yaml: net_after_cost_rule must be present and non-empty")
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
