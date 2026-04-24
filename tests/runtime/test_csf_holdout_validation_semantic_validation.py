from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from runtime.tools.csf_holdout_validation_contract_runtime import validate_csf_holdout_validation_semantics
from runtime.tools.csf_holdout_runtime import build_csf_holdout_validation_from_backtest, scaffold_csf_holdout_validation
from tests.runtime.test_csf_holdout_runtime import (
    _csf_holdout_validation_draft,
    _prepare_csf_backtest_stage,
    _write_yaml,
)


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _prepare_valid_csf_holdout_validation(lineage_root: Path) -> Path:
    _prepare_csf_backtest_stage(lineage_root)
    stage_dir = scaffold_csf_holdout_validation(lineage_root)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_holdout_validation_draft.yaml",
        _csf_holdout_validation_draft(confirmed=True),
    )
    build_csf_holdout_validation_from_backtest(lineage_root)
    return stage_dir


def test_csf_holdout_validation_semantic_validator_accepts_runtime_built_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)

    result = validate_csf_holdout_validation_semantics(stage_dir / "author" / "formal", lineage_root)

    assert result.valid is True
    assert result.errors == []


def test_csf_holdout_validation_semantic_validator_rejects_direction_flip(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet_rows(
        formal_dir / "holdout_test_compare.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "backtest_mean_net_return": 0.012,
                "holdout_mean_net_return": 0.01,
                "direction_match": False,
            }
        ],
    )

    result = validate_csf_holdout_validation_semantics(formal_dir, lineage_root)

    assert "holdout_test_compare.parquet: direction_match must be true for every selected variant" in result.errors


def test_csf_holdout_validation_semantic_validator_rejects_non_positive_holdout_return(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet_rows(
        formal_dir / "holdout_test_compare.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "backtest_mean_net_return": 0.012,
                "holdout_mean_net_return": 0.0,
                "direction_match": True,
            }
        ],
    )

    result = validate_csf_holdout_validation_semantics(formal_dir, lineage_root)

    assert "holdout_test_compare.parquet: holdout_mean_net_return must be > 0 for every selected variant" in result.errors


def test_csf_holdout_validation_semantic_validator_rejects_variant_drift(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet_rows(
        formal_dir / "holdout_portfolio_compare.parquet",
        [
            {
                "variant_id": "leaked_variant",
                "backtest_max_drawdown": -0.08,
                "holdout_max_drawdown": -0.07,
                "holdout_mean_net_return": 0.01,
                "net_return_delta": -0.002,
            }
        ],
    )

    result = validate_csf_holdout_validation_semantics(formal_dir, lineage_root)

    assert (
        "holdout_portfolio_compare.parquet: variant_id rows must stay within backtest-selected variants; "
        "outside=['leaked_variant']"
    ) in result.errors


def test_csf_holdout_validation_semantic_validator_rejects_run_manifest_without_backtest_binding(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = json.loads((formal_dir / "csf_holdout_run_manifest.json").read_text(encoding="utf-8"))
    payload["input_roots"] = []
    (formal_dir / "csf_holdout_run_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_holdout_validation_semantics(formal_dir, lineage_root)

    assert (
        "csf_holdout_run_manifest.json: input_roots must bind to "
        "../06_csf_backtest_ready/author/formal/portfolio_contract.yaml"
    ) in result.errors


def test_csf_holdout_validation_semantic_validator_rejects_portfolio_expression_drift(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = json.loads((formal_dir / "csf_holdout_run_manifest.json").read_text(encoding="utf-8"))
    payload["portfolio_expression"] = "changed_expression"
    (formal_dir / "csf_holdout_run_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_holdout_validation_semantics(formal_dir, lineage_root)

    assert (
        "csf_holdout_run_manifest.json: portfolio_expression must match upstream backtest run_manifest; "
        "expected='long_short_market_neutral'; observed='changed_expression'"
    ) in result.errors
