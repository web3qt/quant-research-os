from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from runtime.tools.csf_test_evidence_runtime import (
    build_csf_test_evidence_from_train_freeze,
    scaffold_csf_test_evidence,
)
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.runtime.test_csf_test_evidence_runtime import (
    _csf_test_evidence_draft,
    _prepare_csf_train_stage,
    _write_yaml,
)


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _prepare_valid_csf_test_evidence_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_train_stage(lineage_root)
    ensure_stage_program(lineage_root, "csf_test_evidence")
    write_fake_stage_provenance(lineage_root, "csf_test_evidence")
    stage_dir = scaffold_csf_test_evidence(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_test_evidence_draft.yaml", _csf_test_evidence_draft(confirmed=True))
    build_csf_test_evidence_from_train_freeze(lineage_root)
    return stage_dir


def _run_csf_test_evidence_preflight(stage_dir: Path) -> dict:
    return run_review_preflight(
        explicit_context={
            "stage": "csf_test_evidence",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": stage_dir.parent.name,
        }
    )


def test_review_preflight_passes_runtime_built_csf_test_evidence_outputs(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_test_evidence_stage(tmp_path)

    payload = _run_csf_test_evidence_preflight(stage_dir)

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_blocks_csf_test_evidence_missing_contract_artifact(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_test_evidence_stage(tmp_path)
    (stage_dir / "author" / "formal" / "bucket_returns.parquet").unlink()

    payload = _run_csf_test_evidence_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item == "ARTIFACT-CONTRACT-001: bucket_returns.parquet: missing required artifact"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_test_evidence_missing_rank_ic_column(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_test_evidence_stage(tmp_path)
    _write_parquet_rows(
        stage_dir / "author" / "formal" / "rank_ic_timeseries.parquet",
        [{"date": "2024-07-01", "variant_id": "baseline_v1", "other_metric": 0.1}],
    )

    payload = _run_csf_test_evidence_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item == "ARTIFACT-CONTRACT-001: rank_ic_timeseries.parquet: missing required parquet column rank_ic"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_test_evidence_variant_drift(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_test_evidence_stage(tmp_path)
    (stage_dir / "author" / "formal" / "csf_selected_variants_test.csv").write_text(
        "variant_id,status\nleaked_variant,selected\n",
        encoding="utf-8",
    )

    payload = _run_csf_test_evidence_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-TEST-SEMANTIC-001" in item for item in payload["content_findings"])
