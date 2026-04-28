from __future__ import annotations

import csv
from pathlib import Path

from runtime.tools.artifact_contract_runtime import ArtifactValidationResult


def validate_tss_test_evidence_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
    stage_formal_dir = stage_formal_dir.resolve()
    lineage_root = lineage_root.resolve() if lineage_root is not None else _infer_lineage_root(stage_formal_dir)
    errors: list[str] = []
    selected_rows = _read_csv_rows(stage_formal_dir / "tss_selected_variants_test.csv", errors)
    selected_ids = _csv_variant_ids(selected_rows, status_filter="selected")
    train_kept_ids = _read_train_kept_variant_ids(lineage_root, errors)
    if not selected_ids:
        errors.append("tss_selected_variants_test.csv: expected at least one selected variant")
        return ArtifactValidationResult(errors=errors)
    outside = sorted(set(selected_ids) - set(train_kept_ids))
    if outside:
        errors.append(
            "tss_selected_variants_test.csv: selected variants must be a subset of train kept variants; "
            f"outside={outside!r}"
        )
    return ArtifactValidationResult(errors=errors)


def _infer_lineage_root(stage_formal_dir: Path) -> Path | None:
    parts = stage_formal_dir.parts
    if "05_tss_test_evidence" not in parts:
        return None
    stage_index = parts.index("05_tss_test_evidence")
    return Path(*parts[:stage_index])


def _read_train_kept_variant_ids(lineage_root: Path | None, errors: list[str]) -> list[str]:
    if lineage_root is None:
        return []
    ledger_path = lineage_root / "04_tss_train_freeze" / "author" / "formal" / "train_variant_ledger.csv"
    rows = _read_csv_rows(ledger_path, errors)
    return _csv_variant_ids(rows, status_filter="kept")


def _read_csv_rows(path: Path, errors: list[str]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception as exc:
        errors.append(f"{path.name}: csv read failed: {exc}")
        return []


def _csv_variant_ids(rows: list[dict[str, str]], *, status_filter: str | None = None) -> list[str]:
    variant_ids: list[str] = []
    for row in rows:
        if status_filter is not None and str(row.get("status", "")).strip() != status_filter:
            continue
        variant_id = str(row.get("variant_id", "")).strip()
        if variant_id:
            variant_ids.append(variant_id)
    return variant_ids
