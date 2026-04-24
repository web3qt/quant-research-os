from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from runtime.tools.csf_holdout_runtime import build_csf_holdout_validation_from_backtest, scaffold_csf_holdout_validation
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.runtime.test_csf_holdout_runtime import (
    _csf_holdout_validation_draft,
    _prepare_csf_backtest_stage,
    _write_yaml,
)


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _prepare_valid_csf_holdout_validation_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_backtest_stage(lineage_root)
    ensure_stage_program(lineage_root, "csf_holdout_validation")
    write_fake_stage_provenance(lineage_root, "csf_holdout_validation")
    stage_dir = scaffold_csf_holdout_validation(lineage_root)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_holdout_validation_draft.yaml",
        _csf_holdout_validation_draft(confirmed=True),
    )
    build_csf_holdout_validation_from_backtest(lineage_root)
    return stage_dir


def _run_csf_holdout_validation_preflight(stage_dir: Path) -> dict:
    return run_review_preflight(
        explicit_context={
            "stage": "csf_holdout_validation",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": stage_dir.parent.name,
        }
    )


def test_review_preflight_passes_runtime_built_csf_holdout_validation_outputs(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_holdout_validation_stage(tmp_path)

    payload = _run_csf_holdout_validation_preflight(stage_dir)

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_blocks_csf_holdout_validation_missing_contract_artifact(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_holdout_validation_stage(tmp_path)
    (stage_dir / "author" / "formal" / "holdout_portfolio_compare.parquet").unlink()

    payload = _run_csf_holdout_validation_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item == "ARTIFACT-CONTRACT-001: holdout_portfolio_compare.parquet: missing required artifact"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_holdout_validation_missing_direction_match_column(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_holdout_validation_stage(tmp_path)
    _write_parquet_rows(
        stage_dir / "author" / "formal" / "holdout_test_compare.parquet",
        [{"variant_id": "baseline_v1", "backtest_mean_net_return": 0.012, "holdout_mean_net_return": 0.01}],
    )

    payload = _run_csf_holdout_validation_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item == "ARTIFACT-CONTRACT-001: holdout_test_compare.parquet: missing required parquet column direction_match"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_holdout_validation_direction_flip(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_holdout_validation_stage(tmp_path)
    _write_parquet_rows(
        stage_dir / "author" / "formal" / "holdout_test_compare.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "backtest_mean_net_return": 0.012,
                "holdout_mean_net_return": 0.01,
                "direction_match": False,
            }
        ],
    )

    payload = _run_csf_holdout_validation_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-HOLDOUT-SEMANTIC-001" in item for item in payload["content_findings"])
