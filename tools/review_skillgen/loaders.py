from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must load to a mapping")
    return data


def load_gate_schema(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    if "stages" not in data:
        raise ValueError("gate schema missing stages")
    return data


def load_checklist_schema(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    if "stages" not in data:
        raise ValueError("checklist schema missing stages")
    return data
