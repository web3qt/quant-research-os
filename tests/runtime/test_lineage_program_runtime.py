from pathlib import Path

import yaml

from tests.helpers.lineage_program_support import ensure_stage_program
from tests.session.test_idea_runtime_scripts import _mandate_freeze_draft, _route_assessment
from runtime.tools.lineage_program_runtime import (
    StageProgramRuntimeError,
    StageProgramSpec,
    inspect_stage_program,
    invoke_stage_if_admitted,
    load_provenance_manifest,
    stage_program_dir,
    stage_program_relative_dir,
)
from runtime.tools.stage_program_scaffold import STAGE_PROGRAM_SPECS


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_prebuild_gate_program(
    lineage_root: Path,
    *,
    dry_run_columns: list[str],
) -> None:
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "signal_ready"
    program_dir.mkdir(parents=True)
    (program_dir / "README.md").write_text("# Signal Ready Program\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        f"""#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lineage-root", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stage_dir = args.lineage_root / "03_csf_signal_ready" / "author" / "formal"
    stage_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        # 预检只写 schema report，避免触发全量构建。
        (stage_dir / "prebuild_schema_report.json").write_text(json.dumps({{
            "artifacts": {{
                "factor_panel.parquet": {{
                    "columns": {dry_run_columns!r},
                    "primary_key": ["date", "asset"],
                    "coverage_fields": ["factor_coverage_ratio"]
                }},
                "factor_manifest.yaml": {{
                    "fields": ["factor_id", "factor_direction", "final_score_field"]
                }}
            }}
        }}), encoding="utf-8")
        return 0

    # 全量构建只有 dry-run 通过后才应执行。
    for name in (
        "factor_panel.parquet",
        "factor_manifest.yaml",
        "component_factor_manifest.yaml",
        "factor_coverage_report.parquet",
        "factor_group_context.parquet",
        "route_inheritance_contract.yaml",
        "factor_contract.md",
        "factor_field_dictionary.md",
        "csf_signal_ready_gate_decision.md",
        "run_manifest.json",
        "artifact_catalog.md",
        "field_dictionary.md",
    ):
        (stage_dir / name).write_text("ok\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""",
        encoding="utf-8",
    )
    (program_dir / "stage_program.yaml").write_text(
        yaml.safe_dump(
            {
                "stage_id": "signal_ready",
                "route": "cross_sectional_factor",
                "lineage_id": lineage_root.name,
                "entrypoint": "run_stage.py",
                "entry_type": "python",
                "inputs": [],
                "outputs": [
                    {"kind": "machine", "path": "03_csf_signal_ready/author/formal/factor_panel.parquet", "required": True}
                ],
                "depends_on_programs": ["mandate"],
                "shared_libs": [],
                "authored_by": {
                    "agent_id": "test-agent",
                    "agent_role": "executor",
                    "session_id": "test-session",
                },
                "prebuild_schema_gate": {
                    "entrypoint_args": ["--dry-run"],
                    "report_path": "prebuild_schema_report.json",
                    "artifacts": {
                        "factor_panel.parquet": {
                            "required_columns": ["date", "asset", "score"],
                            "primary_key": ["date", "asset"],
                            "coverage_fields": ["factor_coverage_ratio"],
                        },
                        "factor_manifest.yaml": {
                            "required_fields": ["factor_id", "factor_direction", "final_score_field"],
                        },
                    },
                },
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _data_ready_freeze_draft() -> dict:
    return {
        "groups": {
            "extraction_contract": {
                "confirmed": True,
                "draft": {
                    "data_source": "Binance UM futures klines",
                    "time_boundary": "2024-01-01 to 2024-12-31",
                    "primary_time_key": "close_time",
                    "bar_size": "5m",
                },
                "missing_items": [],
            },
            "quality_semantics": {
                "confirmed": True,
                "draft": {
                    "missing_policy": "preserve nulls explicitly",
                    "stale_policy": "mark stale bars",
                    "bad_price_policy": "flag only",
                    "outlier_policy": "flag only",
                    "dedupe_rule": "dedupe by symbol and close_time",
                },
                "missing_items": [],
            },
            "universe_admission": {
                "confirmed": True,
                "draft": {
                    "benchmark_symbol": "BTCUSDT",
                    "coverage_floor": "99.0%",
                    "admission_rule": "exclude symbols below coverage floor",
                    "exclusion_reporting": "write csv and md reports",
                },
                "missing_items": [],
            },
            "shared_derived_layer": {
                "confirmed": True,
                "draft": {
                    "shared_outputs": ["rolling_stats", "pair_stats", "benchmark_residual", "topic_basket_state"],
                    "layer_boundary_note": "shared only, not signal layer",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": True,
                "draft": {
                    "machine_artifacts": ["aligned_bars/", "qc_report.parquet", "dataset_manifest.json"],
                    "consumer_stage": "signal_ready",
                    "frozen_inputs_note": "signal stage must consume frozen outputs",
                },
                "missing_items": [],
            },
        }
    }


def test_stage_program_resolution_uses_route_aware_paths(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "case_a"

    assert stage_program_relative_dir("mandate", "route_neutral") == Path("program/mandate")
    assert stage_program_relative_dir("data_ready", "time_series_signal") == Path("program/time_series/data_ready")
    assert stage_program_relative_dir("tss_data_ready", "time_series_signal") == Path(
        "program/time_series_signal/tss_data_ready"
    )
    assert stage_program_relative_dir("tss_signal_ready", "time_series_signal") == Path(
        "program/time_series_signal/tss_signal_ready"
    )
    assert stage_program_relative_dir("signal_ready", "cross_sectional_factor") == Path(
        "program/cross_sectional_factor/signal_ready"
    )
    assert stage_program_dir(lineage_root, "data_ready", "time_series_signal") == lineage_root / "program/time_series/data_ready"
    assert stage_program_dir(lineage_root, "tss_data_ready", "time_series_signal") == (
        lineage_root / "program/time_series_signal/tss_data_ready"
    )


def test_tss_stage_program_scaffold_specs_use_tss_stage_keys() -> None:
    assert STAGE_PROGRAM_SPECS["tss_data_ready"]["stage_id"] == "tss_data_ready"
    assert STAGE_PROGRAM_SPECS["tss_data_ready"]["program_dir"] == Path(
        "program/time_series_signal/tss_data_ready"
    )
    assert STAGE_PROGRAM_SPECS["tss_data_ready"]["module"] == "runtime.tools.tss_data_ready_runtime"
    assert STAGE_PROGRAM_SPECS["tss_data_ready"]["stage_dir"] == Path("02_tss_data_ready")
    assert STAGE_PROGRAM_SPECS["tss_signal_ready"]["stage_id"] == "tss_signal_ready"
    assert STAGE_PROGRAM_SPECS["tss_signal_ready"]["program_dir"] == Path(
        "program/time_series_signal/tss_signal_ready"
    )


def test_invoke_stage_if_admitted_records_provenance_for_time_series_stage(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_case"
    mandate_dir = lineage_root / "01_mandate"
    mandate_formal_dir = mandate_dir / "author" / "formal"
    mandate_formal_dir.mkdir(parents=True)
    for name, content in {
        "mandate.md": "# Mandate\n",
        "research_scope.md": "# Research Scope\n",
        "research_route.yaml": "research_route: time_series_signal\n",
        "time_split.json": "{}\n",
        "parameter_grid.yaml": "parameters: []\n",
        "run_config.toml": 'stage = "mandate"\n',
        "artifact_catalog.md": "# Artifact Catalog\n",
        "field_dictionary.md": "# Field Dictionary\n",
    }.items():
        (mandate_formal_dir / name).write_text(content, encoding="utf-8")
    _write_yaml(lineage_root / "02_data_ready" / "author" / "draft" / "data_ready_freeze_draft.yaml", _data_ready_freeze_draft())
    ensure_stage_program(lineage_root, "data_ready")

    inspection = inspect_stage_program(lineage_root, "data_ready", "time_series_signal")
    assert inspection.program_contract_status == "valid"
    assert inspection.required_program_dir == "program/time_series/data_ready"
    assert inspection.required_program_entrypoint == "run_stage.py"

    result = invoke_stage_if_admitted(
        lineage_root,
        StageProgramSpec(
            stage_id="data_ready",
            route="time_series_signal",
            stage_dir_name="02_data_ready",
            required_outputs=(
                "aligned_bars",
                "rolling_stats",
                "pair_stats",
                "benchmark_residual",
                "topic_basket_state",
                "qc_report.parquet",
                "dataset_manifest.json",
                "validation_report.md",
                "data_contract.md",
                "dedupe_rule.md",
                "universe_summary.md",
                "universe_exclusions.csv",
                "universe_exclusions.md",
                "data_ready_gate_decision.md",
                "run_manifest.json",
                "rebuild_data_ready.py",
                "artifact_catalog.md",
                "field_dictionary.md",
            ),
        ),
    )

    provenance = load_provenance_manifest(result.stage_dir)
    assert provenance is not None
    assert provenance["stage_id"] == "data_ready"
    assert provenance["route"] == "time_series_signal"
    assert provenance["program_dir"] == "program/time_series/data_ready"
    assert provenance["stage_program_manifest_path"] == "program/time_series/data_ready/stage_program.yaml"
    assert provenance["entrypoint"] == "run_stage.py"
    assert provenance["authored_by_agent_id"] == "test-agent"
    assert provenance["authored_by_agent_role"] == "executor"
    assert provenance["authoring_session_id"] == "test-session"
    assert provenance["status"] == "success"
    assert (result.stage_dir / "author" / "formal" / "dataset_manifest.json").exists()
    assert (result.stage_dir / "author" / "formal" / "program_execution_manifest.json").exists()


def test_invoke_stage_if_admitted_blocks_full_build_when_prebuild_schema_gate_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_prebuild_gate_program(lineage_root, dry_run_columns=["date", "asset"])

    try:
        invoke_stage_if_admitted(
            lineage_root,
            StageProgramSpec(
                stage_id="signal_ready",
                route="cross_sectional_factor",
                stage_dir_name="03_csf_signal_ready",
                required_outputs=(
                    "factor_panel.parquet",
                    "factor_manifest.yaml",
                    "component_factor_manifest.yaml",
                    "factor_coverage_report.parquet",
                    "factor_group_context.parquet",
                    "route_inheritance_contract.yaml",
                    "factor_contract.md",
                    "factor_field_dictionary.md",
                    "csf_signal_ready_gate_decision.md",
                    "run_manifest.json",
                    "artifact_catalog.md",
                    "field_dictionary.md",
                ),
            ),
        )
    except StageProgramRuntimeError as exc:
        assert exc.reason_code == "STAGE_PROGRAM_PREBUILD_FAILED"
        assert "score" in exc.message
    else:
        raise AssertionError("expected prebuild failure")

    formal_dir = lineage_root / "03_csf_signal_ready" / "author" / "formal"
    assert (formal_dir / "prebuild_schema_report.json").exists()
    assert not (formal_dir / "factor_panel.parquet").exists()
    assert not (formal_dir / "program_execution_manifest.json").exists()


def test_invoke_stage_if_admitted_runs_full_build_after_prebuild_schema_gate_passes(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_prebuild_gate_program(
        lineage_root,
        dry_run_columns=["date", "asset", "score", "factor_coverage_ratio"],
    )

    result = invoke_stage_if_admitted(
        lineage_root,
        StageProgramSpec(
            stage_id="signal_ready",
            route="cross_sectional_factor",
            stage_dir_name="03_csf_signal_ready",
            required_outputs=(
                "factor_panel.parquet",
                "factor_manifest.yaml",
                "component_factor_manifest.yaml",
                "factor_coverage_report.parquet",
                "factor_group_context.parquet",
                "route_inheritance_contract.yaml",
                "factor_contract.md",
                "factor_field_dictionary.md",
                "csf_signal_ready_gate_decision.md",
                "run_manifest.json",
                "artifact_catalog.md",
                "field_dictionary.md",
            ),
        ),
    )

    formal_dir = result.stage_dir / "author" / "formal"
    assert (formal_dir / "prebuild_schema_report.json").exists()
    assert (formal_dir / "factor_panel.parquet").exists()
    assert (formal_dir / "program_execution_manifest.json").exists()


def test_invoke_stage_if_admitted_supports_route_neutral_mandate_programs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "case_mandate"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True, exist_ok=True)

    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "case_mandate",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "route_assessment": _route_assessment(),
            "approved_scope": {
                "market": "Binance perpetual",
                "data_source": "Binance UM futures klines",
                "universe": "top liquidity alts",
                "bar_size": "5m",
                "horizons": ["15m", "30m", "60m"],
                "target_task": "event-driven relative return study",
                "excluded_scope": ["low liquidity tails"],
            },
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {
            "market": "Binance perpetual",
            "data_source": "Binance UM futures klines",
            "instrument_type": "perpetual",
            "universe": "top liquidity alts",
            "bar_size": "5m",
            "holding_horizons": ["15m", "30m", "60m"],
            "target_task": "event-driven relative return study",
            "excluded_scope": ["low liquidity tails"],
            "budget_days": 10,
            "max_iterations": 3,
        },
    )
    (intake_dir / "research_question_set.md").write_text(
        "# Research Questions\n\n- Does BTC shock lead ALT follow-through?\n",
        encoding="utf-8",
    )
    (intake_dir / "qualification_scorecard.yaml").write_text("idea_id: case_mandate\n", encoding="utf-8")
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "mandate")

    inspection = inspect_stage_program(lineage_root, "mandate", "route_neutral")
    assert inspection.program_contract_status == "valid"
    assert inspection.required_program_dir == "program/mandate"
    assert inspection.required_program_entrypoint == "run_stage.py"

    result = invoke_stage_if_admitted(
        lineage_root,
        StageProgramSpec(
            stage_id="mandate",
            route="route_neutral",
            stage_dir_name="01_mandate",
            required_outputs=(
                "mandate.md",
                "research_scope.md",
                "research_route.yaml",
                "time_split.json",
                "parameter_grid.yaml",
                "run_config.toml",
                "artifact_catalog.md",
                "field_dictionary.md",
            ),
        ),
    )

    provenance = load_provenance_manifest(result.stage_dir)
    assert provenance is not None
    assert provenance["stage_id"] == "mandate"
    assert provenance["route"] == "route_neutral"
    assert provenance["program_dir"] == "program/mandate"
    assert provenance["stage_program_manifest_path"] == "program/mandate/stage_program.yaml"
    assert provenance["status"] == "success"
    assert (lineage_root / "01_mandate" / "author" / "formal" / "mandate.md").exists()
