from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from runtime.tools.csf_data_ready_contract_runtime import validate_csf_data_ready_semantics
from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate
from tests.runtime.test_csf_data_ready_runtime import (
    _csf_data_ready_draft,
    _prepare_mandate_stage,
    _write_yaml,
)


def _build_valid_formal_dir(lineage_root: Path) -> Path:
    _prepare_mandate_stage(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _csf_data_ready_draft(confirmed=True))
    build_csf_data_ready_from_mandate(lineage_root)
    return stage_dir / "author" / "formal"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_empty_parquet(path: Path, schema: dict[str, pa.DataType]) -> None:
    pq.write_table(pa.table({key: pa.array([], type=value) for key, value in schema.items()}), path)


def test_semantic_validator_accepts_generated_csf_data_ready(tmp_path: Path) -> None:
    formal_dir = _build_valid_formal_dir(tmp_path / "outputs" / "csf_case")

    result = validate_csf_data_ready_semantics(formal_dir)

    assert result.valid is True
    assert result.errors == []


def test_semantic_validator_rejects_noncanonical_panel_primary_key(tmp_path: Path) -> None:
    formal_dir = _build_valid_formal_dir(tmp_path / "outputs" / "csf_case")
    manifest_path = formal_dir / "panel_manifest.json"
    manifest = _load_json(manifest_path)
    manifest["panel_primary_key"] = ["asset", "date"]
    _write_json(manifest_path, manifest)

    result = validate_csf_data_ready_semantics(formal_dir)

    assert result.valid is False
    assert "panel_manifest.json: panel_primary_key must equal ['date', 'asset']" in result.errors


def test_semantic_validator_rejects_empty_membership(tmp_path: Path) -> None:
    formal_dir = _build_valid_formal_dir(tmp_path / "outputs" / "csf_case")
    _write_empty_parquet(
        formal_dir / "asset_universe_membership.parquet",
        {
            "date": pa.string(),
            "asset": pa.string(),
            "in_universe": pa.bool_(),
        },
    )

    result = validate_csf_data_ready_semantics(formal_dir)

    assert result.valid is False
    assert "asset_universe_membership.parquet: expected non-empty rows" in result.errors


def test_semantic_validator_rejects_duplicate_eligibility_key(tmp_path: Path) -> None:
    formal_dir = _build_valid_formal_dir(tmp_path / "outputs" / "csf_case")
    _write_parquet_rows(
        formal_dir / "eligibility_base_mask.parquet",
        [
            {"date": "2024-01-01", "asset": "BTCUSDT", "eligible": True},
            {"date": "2024-01-01", "asset": "BTCUSDT", "eligible": False},
        ],
    )

    result = validate_csf_data_ready_semantics(formal_dir)

    assert result.valid is False
    assert "eligibility_base_mask.parquet: duplicate key ('2024-01-01', 'BTCUSDT') for ['date', 'asset']" in result.errors


def test_semantic_validator_rejects_coverage_floor_breach(tmp_path: Path) -> None:
    formal_dir = _build_valid_formal_dir(tmp_path / "outputs" / "csf_case")
    _write_parquet_rows(
        formal_dir / "cross_section_coverage.parquet",
        [{"date": "2024-01-01", "coverage_ratio": 0.60, "asset_count": 2}],
    )

    result = validate_csf_data_ready_semantics(formal_dir)

    assert result.valid is False
    assert "cross_section_coverage.parquet: min coverage_ratio 0.6 below coverage_floor_min_ratio 0.95" in result.errors


def test_semantic_validator_rejects_empty_shared_feature_base(tmp_path: Path) -> None:
    formal_dir = _build_valid_formal_dir(tmp_path / "outputs" / "csf_case")
    _write_empty_parquet(
        formal_dir / "shared_feature_base" / "returns_panel.parquet",
        {
            "date": pa.string(),
            "asset": pa.string(),
            "return_1d": pa.float64(),
        },
    )

    result = validate_csf_data_ready_semantics(formal_dir)

    assert result.valid is False
    assert "shared_feature_base/returns_panel.parquet: expected non-empty rows" in result.errors
