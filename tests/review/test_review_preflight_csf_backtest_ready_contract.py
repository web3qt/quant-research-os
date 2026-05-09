from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.csf_backtest_runtime import (
    build_csf_backtest_ready_from_test_evidence,
    scaffold_csf_backtest_ready,
)
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.runtime.test_csf_backtest_runtime import (
    _csf_backtest_ready_draft,
    _prepare_csf_test_stage,
    _write_yaml,
)


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _prepare_valid_csf_backtest_ready_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_test_stage(lineage_root)
    ensure_stage_program(lineage_root, "csf_backtest_ready")
    write_fake_stage_provenance(lineage_root, "csf_backtest_ready")
    stage_dir = scaffold_csf_backtest_ready(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_backtest_ready_draft.yaml", _csf_backtest_ready_draft(confirmed=True))
    build_csf_backtest_ready_from_test_evidence(lineage_root)
    return stage_dir


def _run_csf_backtest_ready_preflight(stage_dir: Path) -> dict:
    return run_review_preflight(
        explicit_context={
            "stage": "csf_backtest_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": stage_dir.parent.name,
        }
    )


def test_review_preflight_passes_runtime_built_csf_backtest_ready_outputs(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_backtest_ready_stage(tmp_path)

    payload = _run_csf_backtest_ready_preflight(stage_dir)

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_blocks_csf_backtest_ready_missing_contract_artifact(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_backtest_ready_stage(tmp_path)
    (stage_dir / "author" / "formal" / "portfolio_weight_panel.parquet").unlink()

    payload = _run_csf_backtest_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item == "ARTIFACT-CONTRACT-001: portfolio_weight_panel.parquet: missing required artifact"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_backtest_ready_missing_weight_column(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_backtest_ready_stage(tmp_path)
    _write_parquet_rows(
        stage_dir / "author" / "formal" / "portfolio_weight_panel.parquet",
        [{"date": "2024-10-01", "asset": "SOLUSDT", "variant_id": "baseline_v1", "side": "long"}],
    )

    payload = _run_csf_backtest_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item == "ARTIFACT-CONTRACT-001: portfolio_weight_panel.parquet: missing required parquet column weight"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_backtest_ready_variant_drift(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_backtest_ready_stage(tmp_path)
    _write_parquet_rows(
        stage_dir / "author" / "formal" / "portfolio_weight_panel.parquet",
        [
            {
                "date": "2024-10-01",
                "asset": "SOLUSDT",
                "variant_id": "leaked_variant",
                "weight": 0.5,
                "side": "long",
            }
        ],
    )

    payload = _run_csf_backtest_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-BACKTEST-SEMANTIC-001" in item for item in payload["content_findings"])


def test_review_preflight_blocks_csf_backtest_ready_missing_return_provenance(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_backtest_ready_stage(tmp_path)
    (stage_dir / "author" / "formal" / "return_accounting_provenance.yaml").unlink()

    payload = _run_csf_backtest_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("return_accounting_provenance.yaml" in item for item in payload["content_findings"])


def test_review_preflight_blocks_csf_backtest_ready_mom_ret_return_provenance(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_backtest_ready_stage(tmp_path)
    provenance_path = stage_dir / "author" / "formal" / "return_accounting_provenance.yaml"
    payload = yaml.safe_load(provenance_path.read_text(encoding="utf-8"))
    payload["return_source"]["return_field"] = "mom_ret"
    payload["accounting"]["gross_return_formula"] = "sum(weight * mom_ret)"
    provenance_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    result = _run_csf_backtest_ready_preflight(stage_dir)

    assert result["status"] == "FAIL"
    assert any("CSF-BACKTEST-SEMANTIC-001" in item and "mom_ret" in item for item in result["content_findings"])
