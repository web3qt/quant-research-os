from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


def validate_tss_data_ready_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    del lineage_root
    stage_formal_dir = stage_formal_dir.resolve()
    errors: list[str] = []
    rows = _read_parquet_rows(stage_formal_dir / "asset_time_index.parquet", errors)
    for row_index, row in enumerate(rows, start=1):
        timestamp = _parse_datetime(row.get("timestamp"))
        forward_label_timestamp = _parse_datetime(row.get("forward_label_timestamp"))
        if timestamp is None or forward_label_timestamp is None:
            continue
        if forward_label_timestamp <= timestamp:
            errors.append(
                "asset_time_index.parquet: forward_label_timestamp must be after timestamp "
                f"for row {row_index}"
            )
    return ArtifactValidationResult(errors=errors)


def _read_parquet_rows(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq

        return pq.read_table(path).to_pylist()
    except Exception as exc:
        errors.append(f"{path.name}: parquet read failed: {exc}")
        return []


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
