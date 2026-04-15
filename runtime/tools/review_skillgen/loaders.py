from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _review_closure_verdicts(status_vocabulary: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        verdict
        for verdict, meta in status_vocabulary.items()
        if isinstance(meta, dict) and meta.get("scope") != "idea_intake"
    )


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
    status_vocabulary = data.get("status_vocabulary")
    if not isinstance(status_vocabulary, dict):
        raise ValueError("gate schema missing status_vocabulary")
    data["review_closure_vocabulary"] = _review_closure_verdicts(status_vocabulary)
    data["review_passing_verdicts"] = tuple(
        verdict
        for verdict, meta in status_vocabulary.items()
        if isinstance(meta, dict) and meta.get("scope") == "research_stage" and bool(meta.get("can_advance"))
    )
    data["review_retry_verdicts"] = tuple(
        verdict
        for verdict, meta in status_vocabulary.items()
        if isinstance(meta, dict) and meta.get("scope") == "research_stage" and not bool(meta.get("can_advance"))
    )
    return data


def load_checklist_schema(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    if "stages" not in data:
        raise ValueError("checklist schema missing stages")
    return data
