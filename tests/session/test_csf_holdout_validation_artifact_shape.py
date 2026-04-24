from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_holdout_runtime import build_csf_holdout_validation_from_backtest, scaffold_csf_holdout_validation
from tests.runtime.test_csf_holdout_runtime import (
    _csf_holdout_validation_draft,
    _prepare_csf_backtest_stage,
    _write_yaml,
)


def _prepare_valid_csf_holdout_validation(lineage_root: Path) -> Path:
    _prepare_csf_backtest_stage(lineage_root)
    stage_dir = scaffold_csf_holdout_validation(lineage_root)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_holdout_validation_draft.yaml",
        _csf_holdout_validation_draft(confirmed=True),
    )
    build_csf_holdout_validation_from_backtest(lineage_root)
    return stage_dir


def test_csf_holdout_validation_scaffold_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_backtest_stage(lineage_root)

    stage_dir = scaffold_csf_holdout_validation(lineage_root)

    draft = yaml.safe_load(
        (stage_dir / "author" / "draft" / "csf_holdout_validation_draft.yaml").read_text(encoding="utf-8")
    )
    assert set(draft["groups"]) == {
        "window_contract",
        "reuse_contract",
        "stability_contract",
        "failure_governance",
        "delivery_contract",
    }
    assert set(draft["groups"]["reuse_contract"]["draft"]) == {
        "backtest_contract_source",
        "test_contract_source",
        "variant_reuse_rule",
        "no_reestimate_rule",
    }


def test_csf_holdout_validation_build_shape_matches_contract(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("csf_holdout_validation"))

    assert result.valid is True
    assert result.errors == []


def test_csf_holdout_validation_run_manifest_key_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    import json

    payload = json.loads((formal_dir / "csf_holdout_run_manifest.json").read_text(encoding="utf-8"))

    assert set(payload) == {
        "stage",
        "lineage_id",
        "source_stage",
        "holdout_window_source",
        "time_split",
        "reuse_rule",
        "drift_scope",
        "backtest_contract_source",
        "test_contract_source",
        "variant_reuse_rule",
        "no_reestimate_rule",
        "direction_flip_rule",
        "coverage_rule",
        "regime_shift_rule",
        "retryable_conditions",
        "child_lineage_trigger",
        "rollback_boundary",
        "input_roots",
        "stage_outputs",
        "program_dir",
        "program_entrypoint",
        "program_execution_manifest",
        "replay_command",
        "selected_variant_ids",
        "portfolio_expression",
        "delivery_contract",
    }
    assert payload["delivery_contract"]["consumer_stage"] == "terminal"


def test_csf_holdout_validation_compare_columns_are_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_holdout_validation(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    test_compare = pq.read_table(formal_dir / "holdout_test_compare.parquet")
    portfolio_compare = pq.read_table(formal_dir / "holdout_portfolio_compare.parquet")

    assert set(test_compare.column_names) == {
        "variant_id",
        "backtest_mean_net_return",
        "holdout_mean_net_return",
        "direction_match",
    }
    assert set(portfolio_compare.column_names) == {
        "variant_id",
        "backtest_max_drawdown",
        "holdout_max_drawdown",
        "holdout_mean_net_return",
        "net_return_delta",
    }
