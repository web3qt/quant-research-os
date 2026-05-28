from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.csf_backtest_runtime import build_csf_backtest_ready_from_test_evidence
from tests.runtime.test_csf_backtest_runtime import (
    _csf_backtest_ready_draft,
    _prepare_csf_test_stage,
    _write_yaml,
)


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _build_valid_formal_dir(lineage_root: Path) -> Path:
    _prepare_csf_test_stage(lineage_root)
    stage_dir = lineage_root / "06_csf_backtest_ready"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_backtest_ready_draft.yaml", _csf_backtest_ready_draft(confirmed=True))
    build_csf_backtest_ready_from_test_evidence(lineage_root)
    return stage_dir / "author" / "formal"


def test_csf_backtest_ready_semantics_accepts_runtime_built_outputs(tmp_path: Path) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert result.valid is True
    assert result.errors == []


def test_csf_backtest_ready_semantics_rejects_weight_variant_outside_test_selected_set(
    tmp_path: Path,
) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    pq.write_table(
        pa.table(
            {
                "date": ["2024-10-01"],
                "asset": ["SOLUSDT"],
                "variant_id": ["leaked_variant"],
                "weight": [0.5],
                "side": ["long"],
            }
        ),
        formal_dir / "portfolio_weight_panel.parquet",
    )

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert (
        "portfolio_weight_panel.parquet: variant_id rows must stay within test-selected variants; outside=['leaked_variant']"
        in result.errors
    )


def test_csf_backtest_ready_semantics_rejects_non_positive_mean_net_return(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    (formal_dir / "csf_backtest_gate_table.csv").write_text(
        "variant_id,portfolio_expression,mean_net_return,after_cost_rule,name_level_rule\n"
        "baseline_v1,long_short_market_neutral,0.0,net-of-cost,concentration checked\n",
        encoding="utf-8",
    )

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert "csf_backtest_gate_table.csv: mean_net_return must be > 0 for every selected variant" in result.errors


def test_csf_backtest_ready_semantics_rejects_portfolio_expression_drift(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = yaml.safe_load((formal_dir / "portfolio_contract.yaml").read_text(encoding="utf-8"))
    payload["portfolio_expression"] = "target_strategy_overlay"
    _write_yaml(formal_dir / "portfolio_contract.yaml", payload)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert (
        "portfolio_contract.yaml: portfolio_expression must match mandate research_route.yaml; expected='long_short_market_neutral'; observed='target_strategy_overlay'"
        in result.errors
    )


def test_csf_backtest_ready_semantics_rejects_run_manifest_missing_test_binding(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = json.loads((formal_dir / "run_manifest.json").read_text(encoding="utf-8"))
    payload["input_roots"] = ["author/draft/csf_backtest_ready_draft.yaml"]
    (formal_dir / "run_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert (
        "run_manifest.json: input_roots must bind to ../05_csf_test_evidence/author/formal/csf_selected_variants_test.csv"
        in result.errors
    )


def test_csf_backtest_ready_semantics_rejects_run_manifest_missing_return_accounting_output(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = json.loads((formal_dir / "run_manifest.json").read_text(encoding="utf-8"))
    payload["stage_outputs"] = [
        output for output in payload["stage_outputs"] if output != "return_accounting_provenance.yaml"
    ]
    (formal_dir / "run_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert (
        "run_manifest.json: stage_outputs missing required outputs ['return_accounting_provenance.yaml']"
        in result.errors
    )


def test_csf_backtest_ready_semantics_rejects_missing_return_accounting_provenance(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    (formal_dir / "return_accounting_provenance.yaml").unlink()

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert "return_accounting_provenance.yaml: missing required return accounting provenance" in result.errors


def test_csf_backtest_ready_semantics_rejects_missing_path_risk_artifacts(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    (formal_dir / "portfolio_return_series.parquet").unlink()

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert any("portfolio_return_series.parquet" in error for error in result.errors)


def test_csf_backtest_ready_semantics_rejects_risk_metric_drift(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    rows = pq.read_table(formal_dir / "risk_adjusted_metrics.parquet").to_pylist()
    rows[0]["annualized_return_365d"] = 999.0
    _write_parquet_rows(formal_dir / "risk_adjusted_metrics.parquet", rows)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert any(
        "risk_adjusted_metrics.parquet: annualized_return_365d mismatch" in error
        for error in result.errors
    )


def test_csf_backtest_ready_semantics_rejects_signal_panel_return_source(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))
    payload["return_source"]["source_type"] = "signal_panel"
    _write_yaml(formal_dir / "return_accounting_provenance.yaml", payload)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert (
        "return_accounting_provenance.yaml: return_source.source_type signal_panel is forbidden for formal backtest PnL"
        in result.errors
    )


def test_csf_backtest_ready_semantics_rejects_mom_ret_as_formal_return_field(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))
    payload["return_source"]["return_field"] = "mom_ret"
    payload["accounting"]["gross_return_formula"] = "sum(weight * mom_ret)"
    _write_yaml(formal_dir / "return_accounting_provenance.yaml", payload)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert (
        "return_accounting_provenance.yaml: formal return field/formula must not use proxy token mom_ret"
        in result.errors
    )


def test_csf_backtest_ready_semantics_rejects_signal_ready_only_return_paths(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))
    payload["return_source"]["input_paths"] = [
        "../03_csf_signal_ready/author/formal/factor_panel.parquet",
    ]
    _write_yaml(formal_dir / "return_accounting_provenance.yaml", payload)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert (
        "return_accounting_provenance.yaml: formal return input_paths must include an independent market/execution source, not only signal/train factor outputs"
        in result.errors
    )


def test_csf_backtest_ready_semantics_rejects_stage_program_weight_times_mom_ret(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    program_path = lineage_root / "program" / "cross_sectional_factor" / "backtest_ready" / "run_stage.py"
    program_path.parent.mkdir(parents=True)
    program_path.write_text(
        "gross_ret = (merged['weight'] * merged['mom_ret']).sum()\n",
        encoding="utf-8",
    )

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert (
        "run_stage.py: formal backtest program appears to compute PnL from weight * mom_ret proxy returns"
        in result.errors
    )
