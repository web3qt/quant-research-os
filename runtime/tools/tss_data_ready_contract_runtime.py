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
    violations = _check_forward_label_ordering(
        stage_formal_dir / "asset_time_index.parquet", errors
    )
    if violations > 0:
        errors.append(
            f"asset_time_index.parquet: forward_label_timestamp must be after timestamp "
            f"({violations} row(s) violated)"
        )
    return ArtifactValidationResult(errors=errors)


def _check_forward_label_ordering(
    path: Path, errors: list[str]
) -> int:
    """Use vectorized PyArrow compute to count ordering violations."""
    try:
        import pyarrow.parquet as pq
        import pyarrow.compute as pc

        table = pq.read_table(path, columns=["timestamp", "forward_label_timestamp"])
        if table.num_rows == 0:
            return 0
        ts = table.column("timestamp")
        flt = table.column("forward_label_timestamp")
        # Both should be timestamps; if either column is missing/null, skip.
        if ts.null_count == table.num_rows or flt.null_count == table.num_rows:
            return 0
        violations = pc.less_equal(flt, ts)
        return int(pc.sum(violations.cast("int32")).as_py())
    except Exception as exc:
        errors.append(f"{path.name}: parquet read failed: {exc}")
        return 0
