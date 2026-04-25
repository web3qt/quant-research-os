from pathlib import Path
import textwrap

import hashlib
import json
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from runtime.tools.csf_test_evidence_runtime import build_csf_test_evidence_from_train_freeze
from runtime.tools.stage_program_scaffold import STAGE_PROGRAM_SPECS
from tests.helpers.stage_fixtures import prepare_csf_data_ready
from tests.helpers.lineage_program_support import ensure_stage_program
from tests.runtime.test_csf_test_evidence_runtime import (
    _csf_test_evidence_draft,
    _prepare_csf_train_stage,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_parquet(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_thin_wrapper_stage_program(lineage_root: Path, stage_key: str) -> Path:
    spec = STAGE_PROGRAM_SPECS[stage_key]
    program_dir = lineage_root / spec["program_dir"]
    program_dir.mkdir(parents=True, exist_ok=True)
    (program_dir / "README.md").write_text("# thin wrapper\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            from __future__ import annotations

            # 这里故意只做框架转发，验证 preflight 会在 reviewer launch 前拦截。
            from {spec["module"]} import {spec["function"]}


            def main() -> int:
                return {spec["function"]}(None) is not None


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ),
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": spec["stage_id"],
            "route": spec["route"],
            "lineage_id": lineage_root.name,
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [
                {"kind": "artifact", "path": path, "required": True}
                for path in spec["inputs"]
            ],
            "outputs": [
                {"kind": "machine", "path": path, "required": True}
                for path in spec["outputs"]
            ],
            "depends_on_programs": ["mandate"] if stage_key != "mandate" else [],
            "shared_libs": [],
            "authored_by": {
                "agent_id": "test-agent",
                "agent_role": "executor",
                "session_id": "test-session",
            },
        },
    )
    return program_dir


def _prepare_csf_test_evidence_outputs(stage_dir: Path) -> None:
    lineage_root = stage_dir.parent
    _prepare_csf_train_stage(lineage_root)
    stage_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_test_evidence_draft.yaml",
        _csf_test_evidence_draft(confirmed=True),
    )
    build_csf_test_evidence_from_train_freeze(lineage_root)


def _prepare_csf_signal_ready_outputs(stage_dir: Path, *, fake_panel: bool = False) -> None:
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    panel_rows = (
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "factor_value": 1.0, "placeholder_note": "占位"},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "factor_value": -1.0, "placeholder_note": "real"},
        ]
        if fake_panel
        else [
            {"date": "2024-01-01", "asset": "SOLUSDT", "factor_value": 1.0},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "factor_value": -1.0},
        ]
    )
    _write_parquet(author_formal_dir / "factor_panel.parquet", panel_rows)
    _write_parquet(
        author_formal_dir / "factor_coverage_report.parquet",
        [
            {"date": "2024-01-01", "coverage_ratio": 1.0, "asset_count": 2},
        ],
    )
    _write_parquet(
        author_formal_dir / "factor_group_context.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "group_context": "majors"},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "group_context": "memes"},
        ],
    )
    _write_text(
        author_formal_dir / "factor_manifest.yaml",
        "\n".join(
            [
                "stage: csf_signal_ready",
                f"lineage_id: {stage_dir.parent.name}",
                "factor_id: csf_signal_ready_fixture",
                "factor_version: v1",
                "factor_direction: high_better",
                "factor_structure: single_factor",
                "panel_primary_key: [date, asset]",
                "raw_factor_fields: [return_1d, dollar_volume, beta_proxy]",
                "derived_factor_fields: [lead_follow_score]",
                "final_score_field: factor_value",
                "as_of_semantics: Factor values are frozen at the cross-section close.",
                "coverage_min_ratio: 1.0",
                "coverage_contract: Require complete fixture coverage.",
                "missing_value_policy: Preserve nulls and report eligibility separately.",
                "input_field_map:",
                "  - raw_field: return_1d",
                "    source_artifact: shared_feature_base/returns_panel.parquet",
                "    source_column: return_1d",
                "  - raw_field: dollar_volume",
                "    source_artifact: shared_feature_base/liquidity_panel.parquet",
                "    source_column: dollar_volume",
                "  - raw_field: beta_proxy",
                "    source_artifact: shared_feature_base/beta_inputs.parquet",
                "    source_column: beta_proxy",
            ]
        )
        + "\n",
    )
    _write_text(
        author_formal_dir / "component_factor_manifest.yaml",
        "\n".join(
            [
                "stage: csf_signal_ready",
                f"lineage_id: {stage_dir.parent.name}",
                "factor_structure: single_factor",
                "component_factor_ids: []",
                "score_combination_formula: single_factor_passthrough",
                "combination_policy: deterministic_formula",
            ]
        )
        + "\n",
    )
    route_path = stage_dir.parent / "01_mandate" / "author" / "formal" / "research_route.yaml"
    route_payload = yaml.safe_load(route_path.read_text(encoding="utf-8")) or {}
    route_text = route_path.read_text(encoding="utf-8")
    _write_text(
        author_formal_dir / "route_inheritance_contract.yaml",
        "\n".join(
            [
                "source_route_artifact: ../../01_mandate/author/formal/research_route.yaml",
                f"source_route_digest_sha256: {hashlib.sha256(route_text.encode('utf-8')).hexdigest()}",
                f"research_route: {route_payload['research_route']}",
                f"factor_role: {route_payload['factor_role']}",
                f"factor_structure: {route_payload['factor_structure']}",
                f"portfolio_expression: {route_payload['portfolio_expression']}",
                f"neutralization_policy: {route_payload['neutralization_policy']}",
                "target_strategy_reference: ''",
                f"group_taxonomy_reference: {route_payload['group_taxonomy_reference']}",
                "inheritance_mode: exact_copy",
                "target_strategy_reference_requirement_status: not_required",
                "group_taxonomy_reference_requirement_status: required_satisfied",
            ]
        )
        + "\n",
    )
    _write_text(
        author_formal_dir / "factor_field_dictionary.md",
        "# 因子字段字典\n\n- factor_value: factor score.\n",
    )
    _write_text(
        author_formal_dir / "factor_contract.md",
        "# 因子合同\n\nThis stage reuses frozen signal evidence.\n",
    )
    _write_json(
        author_formal_dir / "run_manifest.json",
        {
            "stage": "csf_signal_ready",
            "lineage_id": stage_dir.parent.name,
            "source_stage": "csf_data_ready",
            "research_route": "cross_sectional_factor",
            "factor_role": route_payload["factor_role"],
            "factor_structure": route_payload["factor_structure"],
            "portfolio_expression": route_payload["portfolio_expression"],
            "neutralization_policy": route_payload["neutralization_policy"],
            "program_dir": "program/cross_sectional_factor/signal_ready",
            "program_entrypoint": "run_stage.py",
            "program_execution_manifest": "program_execution_manifest.json",
            "input_roots": [
                "../02_csf_data_ready/author/formal/panel_manifest.json",
                "../../01_mandate/author/formal/research_route.yaml",
            ],
            "stage_outputs": ["factor_panel.parquet", "factor_manifest.yaml"],
            "replay_command": "python3 program/cross_sectional_factor/signal_ready/run_stage.py",
        },
    )
    _write_text(
        author_formal_dir / "artifact_catalog.md",
        "# 产物清单\n\n- factor_panel.parquet\n- factor_coverage_report.parquet\n",
    )
    _write_text(
        author_formal_dir / "field_dictionary.md",
        "# 字段字典\n\n- factor_value: factor score.\n",
    )
    _write_text(
        author_formal_dir / "csf_signal_ready_gate_decision.md",
        "# CSF Signal Ready Gate Decision\n\nverdict: PASS\n",
    )


def _prepare_data_ready_outputs(stage_dir: Path, *, bad_nested_file: bool = False) -> None:
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    aligned_bars_dir = author_formal_dir / "aligned_bars"
    aligned_bars_dir.mkdir(parents=True, exist_ok=True)
    (aligned_bars_dir / "2026").mkdir(parents=True, exist_ok=True)
    _write_text(aligned_bars_dir / "2026" / "0001.csv", "timestamp,price\n2026-04-01T00:00:00Z,100.0\n")
    _write_text(aligned_bars_dir / "2026" / "0002.csv", "timestamp,price\n2026-04-01T01:00:00Z,101.0\n")
    nested_dir = aligned_bars_dir / "late" / "deeper"
    nested_dir.mkdir(parents=True, exist_ok=True)
    _write_text(
        nested_dir / ("0003_bad.csv" if bad_nested_file else "0003_good.csv"),
        "timestamp,price\n2026-04-01T02:00:00Z,102.0\n" if not bad_nested_file else "timestamp,price\n占位,102.0\n",
    )
    rolling_stats_dir = author_formal_dir / "rolling_stats"
    rolling_stats_dir.mkdir(parents=True, exist_ok=True)
    _write_text(rolling_stats_dir / "stats.csv", "window,mean\n24,100.5\n")
    _write_parquet(
        author_formal_dir / "qc_report.parquet",
        [
            {"symbol": "BTCUSDT", "issue_count": 0},
            {"symbol": "ETHUSDT", "issue_count": 0},
        ],
    )
    _write_json(author_formal_dir / "dataset_manifest.json", {"dataset_version": "v1", "universe_version": "u1"})
    _write_text(author_formal_dir / "validation_report.md", "# Validation Report\n\nAll checks passed.\n")
    _write_text(author_formal_dir / "data_contract.md", "# Data Contract\n\nAligned bars are frozen.\n")
    _write_text(author_formal_dir / "dedupe_rule.md", "# Dedupe Rule\n\nUse close_time only.\n")
    _write_text(author_formal_dir / "universe_summary.md", "# Universe Summary\n\nBTC and ETH coverage verified.\n")
    _write_text(author_formal_dir / "universe_exclusions.csv", "symbol,reason\nXRPUSDT,illiquid\n")
    _write_text(author_formal_dir / "universe_exclusions.md", "# Universe Exclusions\n\nXRPUSDT excluded for illiquidity.\n")
    _write_text(author_formal_dir / "data_ready_gate_decision.md", "# Data Ready Gate Decision\n\nverdict: PASS\n")
    _write_json(author_formal_dir / "run_manifest.json", {"command": "qros-stage-run", "status": "recorded"})
    _write_text(author_formal_dir / "artifact_catalog.md", "# Artifact Catalog\n\n- aligned_bars/\n- rolling_stats/\n")
    _write_text(author_formal_dir / "field_dictionary.md", "# Field Dictionary\n\n- timestamp: bar timestamp.\n- price: close price.\n")
    _write_text(author_formal_dir / "rebuild_data_ready.py", "print('rebuild data ready')\n")


def test_review_preflight_fails_when_machine_artifact_is_placeholder_text(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc_alt_k" / "05_csf_test_evidence"
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    ensure_stage_program(stage_dir.parent, "csf_test_evidence")
    _prepare_csf_test_evidence_outputs(stage_dir)
    _write_text(
        author_formal_dir / "csf_selected_variants_test.csv",
        "variant_id,status,note\nbaseline_v1,selected,placeholder\n",
    )
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_test_evidence_freeze_draft.yaml",
        {
            "groups": {
                "contract": {"confirmed": True, "draft": {"artifact_mode": "machine"}, "missing_items": []},
            }
        },
    )

    payload = run_review_preflight(
        explicit_context={
            "stage": "csf_test_evidence",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(author_formal_dir),
            "lineage_id": "btc_alt_k",
        }
    )

    assert payload["status"] == "FAIL"
    assert not any("Missing required" in finding for finding in payload["content_findings"])
    assert payload["content_findings"] == [
        "ARTIFACT-REALISM-001: placeholder machine artifact rejected for csf_selected_variants_test.csv"
    ]


def test_review_preflight_rejects_thin_wrapper_stage_program_before_launcher(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc_alt_k" / "05_csf_test_evidence"
    _write_thin_wrapper_stage_program(stage_dir.parent, "csf_test_evidence")
    _prepare_csf_test_evidence_outputs(stage_dir)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_test_evidence_freeze_draft.yaml",
        {
            "groups": {
                "contract": {"confirmed": True, "draft": {"artifact_mode": "machine"}, "missing_items": []},
            }
        },
    )

    payload = run_review_preflight(
        explicit_context={
            "stage": "csf_test_evidence",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": "btc_alt_k",
        }
    )

    assert payload["status"] == "FAIL"
    assert payload["content_findings"] == [
        next(
            finding
            for finding in payload["content_findings"]
            if finding.startswith("STAGE_PROGRAM_INVALID:")
            and "post-mandate stage program cannot be a thin wrapper around framework builders" in finding
        )
    ]
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_rejects_fake_but_readable_parquet_content(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc_alt_k" / "03_csf_signal_ready"
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    prepare_csf_data_ready(stage_dir.parent)
    ensure_stage_program(stage_dir.parent, "csf_signal_ready")
    _write_yaml(
        stage_dir.parent / "01_mandate" / "author" / "formal" / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )
    _prepare_csf_signal_ready_outputs(stage_dir, fake_panel=True)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml",
        {
            "groups": {
                "contract": {"confirmed": True, "draft": {"artifact_mode": "machine"}, "missing_items": []},
            }
        },
    )

    payload = run_review_preflight(
        explicit_context={
            "stage": "csf_signal_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(author_formal_dir),
            "lineage_id": "btc_alt_k",
        }
    )

    assert payload["status"] == "FAIL"
    assert "ARTIFACT-REALISM-001: placeholder machine artifact rejected for factor_panel.parquet" in payload["content_findings"]
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_allows_benign_machine_readable_content(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc_alt_k" / "03_csf_signal_ready"
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    prepare_csf_data_ready(stage_dir.parent)
    ensure_stage_program(stage_dir.parent, "csf_signal_ready")
    _write_yaml(
        stage_dir.parent / "01_mandate" / "author" / "formal" / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )
    _prepare_csf_signal_ready_outputs(stage_dir, fake_panel=False)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml",
        {
            "groups": {
                "contract": {"confirmed": True, "draft": {"artifact_mode": "machine"}, "missing_items": []},
            }
        },
    )

    payload = run_review_preflight(
        explicit_context={
            "stage": "csf_signal_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(author_formal_dir),
            "lineage_id": "btc_alt_k",
        }
    )

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_ignores_placeholder_text_outside_machine_artifacts_scope(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc_alt_k" / "02_data_ready"
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    ensure_stage_program(stage_dir.parent, "data_ready")
    _prepare_data_ready_outputs(stage_dir, bad_nested_file=False)
    _write_text(author_formal_dir / "validation_report.md", "占位 validation note\n")
    _write_yaml(
        stage_dir / "author" / "draft" / "data_ready_freeze_draft.yaml",
        {
            "groups": {
                "contract": {"confirmed": True, "draft": {"artifact_mode": "machine"}, "missing_items": []},
            }
        },
    )

    payload = run_review_preflight(
        explicit_context={
            "stage": "data_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(author_formal_dir),
            "lineage_id": "btc_alt_k",
        }
    )

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_scans_directory_machine_artifacts_descendants(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc_alt_k" / "02_data_ready"
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    ensure_stage_program(stage_dir.parent, "data_ready")
    _prepare_data_ready_outputs(stage_dir, bad_nested_file=True)
    _write_yaml(
        stage_dir / "author" / "draft" / "data_ready_freeze_draft.yaml",
        {
            "groups": {
                "contract": {"confirmed": True, "draft": {"artifact_mode": "machine"}, "missing_items": []},
            }
        },
    )

    payload = run_review_preflight(
        explicit_context={
            "stage": "data_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(author_formal_dir),
            "lineage_id": "btc_alt_k",
        }
    )

    assert payload["status"] == "FAIL"
    assert any("aligned_bars/late/deeper/0003_bad.csv" in finding for finding in payload["content_findings"])
    assert any("placeholder machine artifact rejected" in finding for finding in payload["content_findings"])
    assert payload["upstream_binding_findings"] == []
