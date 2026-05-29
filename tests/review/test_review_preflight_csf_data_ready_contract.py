from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program
from tests.runtime.test_csf_data_ready_runtime import (
    _csf_data_ready_draft,
    _prepare_mandate_stage,
    _write_yaml,
)


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _valid_data_implementation_declaration() -> dict:
    return {
        "engine": "polars",
        "input_strategy": "parquet_lazy_scan",
        "compute_strategy": "expression_vectorized",
        "output_strategy": "parquet_columnar",
        "disallowed_main_path": [
            "pandas",
            "row_wise_loop",
            "per_symbol_full_scan_loop",
            "repeated_full_scan_without_shared_intermediate",
        ],
    }


def _add_data_implementation_declaration(program_dir: Path) -> None:
    manifest_path = program_dir / "stage_program.yaml"
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    payload["data_implementation_contract"] = _valid_data_implementation_declaration()
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_valid_csf_data_ready_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_mandate_stage(lineage_root)
    _add_data_implementation_declaration(ensure_stage_program(lineage_root, "csf_data_ready"))
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _csf_data_ready_draft(confirmed=True))
    build_csf_data_ready_from_mandate(lineage_root)
    return stage_dir


def _run_csf_data_ready_preflight(stage_dir: Path) -> dict:
    return run_review_preflight(
        explicit_context={
            "stage": "csf_data_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": stage_dir.parent.name,
        }
    )


def test_review_preflight_blocks_csf_data_ready_when_artifact_contract_fails(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)
    (stage_dir / "author" / "formal" / "shared_feature_base" / "returns_panel.parquet").unlink()

    payload = _run_csf_data_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item == "ARTIFACT-CONTRACT-001: shared_feature_base/returns_panel.parquet: missing required artifact"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_data_ready_when_program_imports_pandas(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)
    program_dir = stage_dir.parent / "program" / "cross_sectional_factor" / "data_ready"
    (program_dir / "run_stage.py").write_text("import pandas as pd\n", encoding="utf-8")

    payload = _run_csf_data_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("DATA_IMPL_ENGINE_FORBIDDEN_PANDAS" in item for item in payload["content_findings"])


def test_review_preflight_blocks_csf_data_ready_when_route_is_not_csf(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)
    _write_yaml(
        stage_dir.parent / "01_mandate" / "author" / "formal" / "research_route.yaml",
        {
            "research_route": "time_series_signal",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )

    payload = _run_csf_data_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-DATA-BIND-001" in item for item in payload["upstream_binding_findings"])


def test_review_preflight_blocks_csf_data_ready_when_taxonomy_snapshot_missing_for_group_neutral(
    tmp_path: Path,
) -> None:
    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)
    (stage_dir / "author" / "formal" / "asset_taxonomy_snapshot.parquet").unlink()

    payload = _run_csf_data_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-DATA-BIND-002" in item for item in payload["upstream_binding_findings"])


def test_review_preflight_blocks_csf_data_ready_when_taxonomy_reference_drifts(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)
    _write_parquet_rows(
        stage_dir / "author" / "formal" / "asset_taxonomy_snapshot.parquet",
        [
            {
                "asset": "BTCUSDT",
                "date": "2024-01-01",
                "group_taxonomy_reference": "wrong_taxonomy_v1",
                "group_bucket": "core",
            }
        ],
    )

    payload = _run_csf_data_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-DATA-BIND-003" in item for item in payload["upstream_binding_findings"])


def test_review_preflight_blocks_csf_data_ready_when_backtest_split_has_no_samples(
    tmp_path: Path,
) -> None:
    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)
    report_path = stage_dir / "author" / "formal" / "split_sample_adequacy_report.yaml"
    _write_yaml(
        report_path,
        {
            "stage": "csf_data_ready",
            "lineage_id": "csf_case",
            "sample_unit": "cross_section_snapshot",
            "source_artifact": "cross_section_coverage.parquet",
            "split_source_artifact": "../../01_mandate/author/formal/time_split.json",
            "split_sample_counts": {
                "train": 1,
                "test": 1,
                "backtest": 0,
                "holdout": 1,
            },
            "minimum_required": {
                "train": 1,
                "test": 1,
                "backtest": 1,
                "holdout": 1,
            },
            "adequacy": {
                "train": "pass",
                "test": "pass",
                "backtest": "fail",
                "holdout": "pass",
            },
            "final_verdict": "FAIL",
        },
    )

    payload = _run_csf_data_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        "split_sample_adequacy_report.yaml: backtest sample_count 0 below minimum_required 1" in item
        for item in payload["content_findings"]
    )


def test_review_preflight_accepts_valid_csf_data_ready(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)

    payload = _run_csf_data_ready_preflight(stage_dir)

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []
