from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.csf_test_evidence_runtime import build_csf_test_evidence_from_train_freeze
from tests.runtime.test_csf_test_evidence_runtime import (
    _csf_test_evidence_draft,
    _prepare_csf_train_stage,
    _write_yaml,
)


def _build_valid_formal_dir(lineage_root: Path) -> Path:
    _prepare_csf_train_stage(lineage_root)
    _prepare_csf_rank_ic_inputs(lineage_root)
    stage_dir = lineage_root / "05_csf_test_evidence"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_test_evidence_draft.yaml", _csf_test_evidence_draft(confirmed=True))
    build_csf_test_evidence_from_train_freeze(lineage_root)
    return stage_dir / "author" / "formal"


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _prepare_csf_rank_ic_inputs(lineage_root: Path) -> None:
    signal_formal_dir = lineage_root / "03_csf_signal_ready" / "author" / "formal"
    data_formal_dir = lineage_root / "02_csf_data_ready" / "author" / "formal"
    signal_formal_dir.mkdir(parents=True, exist_ok=True)
    data_formal_dir.mkdir(parents=True, exist_ok=True)
    _write_parquet_rows(
        signal_formal_dir / "factor_panel.parquet",
        [
            {"date": "2024-07-01", "asset": "AAAUSDT", "score": 1.0},
            {"date": "2024-07-01", "asset": "BBBUSDT", "score": 2.0},
            {"date": "2024-07-01", "asset": "CCCUSDT", "score": 3.0},
        ],
    )
    _write_yaml(
        signal_formal_dir / "factor_manifest.yaml",
        {
            "stage": "csf_signal_ready",
            "lineage_id": lineage_root.name,
            "final_score_field": "score",
        },
    )
    _write_parquet_rows(
        data_formal_dir / "forward_return_panel.parquet",
        [
            {"date": "2024-07-01", "asset": "AAAUSDT", "forward_return": 0.01},
            {"date": "2024-07-01", "asset": "BBBUSDT", "forward_return": 0.02},
            {"date": "2024-07-01", "asset": "CCCUSDT", "forward_return": 0.03},
        ],
    )


def test_csf_test_evidence_semantics_accepts_runtime_built_outputs(tmp_path: Path) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert result.valid is True
    assert result.errors == []


def test_csf_test_evidence_semantics_rejects_selected_variant_outside_train_kept_set(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    (formal_dir / "csf_selected_variants_test.csv").write_text(
        "variant_id,status\nleaked_variant,selected\n",
        encoding="utf-8",
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "csf_selected_variants_test.csv: selected variants must be a subset of train kept variants; outside=['leaked_variant']"
        in result.errors
    )


def test_csf_test_evidence_semantics_rejects_rank_ic_summary_variant_drift(tmp_path: Path) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = json.loads((formal_dir / "rank_ic_summary.json").read_text(encoding="utf-8"))
    payload["selected_variant_ids"] = ["leaked_variant"]
    (formal_dir / "rank_ic_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "rank_ic_summary.json: selected_variant_ids must match csf_selected_variants_test.csv; missing=['baseline_v1']; extra=['leaked_variant']"
        in result.errors
    )


def test_csf_test_evidence_semantics_rejects_non_positive_standalone_rank_ic(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = json.loads((formal_dir / "rank_ic_summary.json").read_text(encoding="utf-8"))
    payload["mean_rank_ic"] = 0.0
    (formal_dir / "rank_ic_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert "rank_ic_summary.json: standalone_alpha mean_rank_ic must be > 0 before review" in result.errors


def test_csf_test_evidence_semantics_rejects_run_manifest_missing_train_binding(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = json.loads((formal_dir / "run_manifest.json").read_text(encoding="utf-8"))
    payload["input_roots"] = ["author/draft/csf_test_evidence_draft.yaml"]
    (formal_dir / "run_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "run_manifest.json: input_roots must bind to ../04_csf_train_freeze/author/formal/csf_train_freeze.yaml"
        in result.errors
    )


def test_csf_test_evidence_semantics_rejects_rank_ic_not_recomputed_from_frozen_inputs(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    _write_parquet_rows(
        formal_dir / "rank_ic_timeseries.parquet",
        [{"date": "2024-07-01", "variant_id": "baseline_v1", "rank_ic": 0.11}],
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "rank_ic_timeseries.parquet: rank_ic for date=2024-07-01 variant_id=baseline_v1 "
        "must be computed from factor_panel.parquet and forward_return_panel.parquet; expected 1, found 0.11"
        in result.errors
    )


def test_csf_test_evidence_semantics_rejects_missing_rank_ic_input_binding(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    run_manifest_path = formal_dir / "run_manifest.json"
    payload = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    payload.pop("rank_ic_input_binding", None)
    run_manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert "run_manifest.json: rank_ic_input_binding must bind factor_panel and forward_return_panel before review" in result.errors
