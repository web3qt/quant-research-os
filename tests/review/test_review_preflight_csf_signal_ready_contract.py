from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.csf_signal_ready_runtime import build_csf_signal_ready_from_data_ready, scaffold_csf_signal_ready
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.runtime.test_csf_signal_ready_semantic_validation import _valid_draft
from tests.runtime.test_csf_signal_ready_runtime import _prepare_csf_data_ready_stage, _write_yaml


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _prepare_valid_csf_signal_ready_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_data_ready_stage(lineage_root)
    ensure_stage_program(lineage_root, "csf_signal_ready")
    write_fake_stage_provenance(lineage_root, "csf_signal_ready")
    stage_dir = scaffold_csf_signal_ready(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml", _valid_draft())
    build_csf_signal_ready_from_data_ready(lineage_root)
    return stage_dir


def _run_csf_signal_ready_preflight(stage_dir: Path) -> dict:
    return run_review_preflight(
        explicit_context={
            "stage": "csf_signal_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": stage_dir.parent.name,
        }
    )


def test_review_preflight_blocks_csf_signal_ready_missing_contract_artifact(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_signal_ready_stage(tmp_path)
    (stage_dir / "author" / "formal" / "component_factor_manifest.yaml").unlink()

    payload = _run_csf_signal_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item == "ARTIFACT-CONTRACT-001: component_factor_manifest.yaml: missing required artifact"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_signal_ready_missing_final_score_column(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_signal_ready_stage(tmp_path)
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet_rows(
        formal_dir / "factor_panel.parquet",
        [{"date": "2024-01-01", "asset": "SOLUSDT", "other_score": 1.0}],
    )

    payload = _run_csf_signal_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-SIGNAL-SEMANTIC-001: factor_panel.parquet: missing final_score_field" in item for item in payload["content_findings"])


def test_review_preflight_blocks_csf_signal_ready_route_digest_drift(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_signal_ready_stage(tmp_path)
    route_path = stage_dir.parent / "01_mandate" / "author" / "formal" / "research_route.yaml"
    route_payload = _load_yaml(route_path)
    route_payload["route_rationale"] = ["same fields but changed route contract digest"]
    _write_yaml(route_path, route_payload)

    payload = _run_csf_signal_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-SIGNAL-BIND-002" in item for item in payload["upstream_binding_findings"])


def test_review_preflight_blocks_csf_signal_ready_factor_panel_outside_eligible_universe(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_signal_ready_stage(tmp_path)
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet_rows(
        formal_dir / "factor_panel.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "factor_value": 1.0},
            {"date": "2024-01-01", "asset": "NOT_ELIGIBLE", "factor_value": 0.5},
        ],
    )

    payload = _run_csf_signal_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-SIGNAL-BIND-007" in item for item in payload["upstream_binding_findings"])


def test_review_preflight_blocks_csf_signal_ready_group_context_taxonomy_drift(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_signal_ready_stage(tmp_path)
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet_rows(
        formal_dir / "factor_group_context.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "group_context": "wrong_bucket"},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "group_context": "memes"},
        ],
    )

    payload = _run_csf_signal_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-SIGNAL-BIND-004" in item for item in payload["upstream_binding_findings"])


def test_review_preflight_passes_runtime_built_csf_signal_ready_outputs(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_signal_ready_stage(tmp_path)

    payload = _run_csf_signal_ready_preflight(stage_dir)

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []
