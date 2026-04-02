from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

import yaml

from tools.anti_drift import CanonicalDecisionSnapshot, canonical_snapshot_from_session_context
from tools.research_session import run_research_session


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def write_minimal_stage_outputs(stage_dir: Path, *, stage: str) -> None:
    file_outputs: dict[str, list[str]] = {
        "mandate": [
            "mandate.md",
            "research_scope.md",
            "research_route.yaml",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
        "data_ready": [
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
        ],
        "test_evidence": [
            "report_by_h.parquet",
            "symbol_summary.parquet",
            "admissibility_report.parquet",
            "test_gate_table.csv",
            "crowding_review.md",
            "selected_symbols_test.csv",
            "selected_symbols_test.parquet",
            "frozen_spec.json",
            "test_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ],
    }

    stage_dir.mkdir(parents=True, exist_ok=True)
    for name in file_outputs[stage]:
        (stage_dir / name).write_text("placeholder\n", encoding="utf-8")


def write_stage_completion_certificate(
    path: Path,
    *,
    stage_status: str = "PASS",
    final_verdict: str | None = None,
) -> None:
    write_yaml(
        path,
        {
            "stage_status": stage_status,
            "final_verdict": final_verdict or stage_status,
        },
    )


def prepare_csf_mandate_review_complete(lineage_root: Path) -> None:
    stage_dir = lineage_root / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_yaml(
        stage_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "regime_filter",
            "factor_structure": "multi_factor_score",
            "portfolio_expression": "long_only_rank",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "trend_combo_v1",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")


def prepare_mainline_mandate_review_complete(lineage_root: Path) -> None:
    stage_dir = lineage_root / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    write_yaml(
        stage_dir / "research_route.yaml",
        {
            "research_route": "time_series_signal",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "directional_long_short",
            "neutralization_policy": "none",
            "target_strategy_reference": "",
            "group_taxonomy_reference": "",
        },
    )
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")


def prepare_mainline_data_ready_review_complete(lineage_root: Path) -> None:
    prepare_mainline_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="data_ready")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")


def snapshot_idea_intake_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    status = run_research_session(
        outputs_root=outputs_root,
        raw_idea="BTC leads high-liquidity alts after shock events",
    )
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="idea-intake-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::idea_intake_confirmation",),
    )


def snapshot_mandate_review(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="mandate-review-replay",
        evidence_refs=("tools/anti_drift_scenarios.py::mandate_review",),
    )


def snapshot_test_evidence_retry(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "05_test_evidence"
    write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="RETRY")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-retry-replay",
        evidence_refs=("tools/anti_drift_scenarios.py::test_evidence_retry",),
    )


def snapshot_csf_data_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_case"
    prepare_csf_mandate_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-data-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::csf_data_ready_confirmation",),
    )


def snapshot_data_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "mainline_case"
    prepare_mainline_mandate_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::data_ready_confirmation",),
    )


def snapshot_signal_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "signal_ready_case"
    prepare_mainline_data_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="signal-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::signal_ready_confirmation",),
    )


SCENARIOS: dict[str, Callable[[Path], CanonicalDecisionSnapshot]] = {
    "idea_intake_confirmation_snapshot.json": snapshot_idea_intake_confirmation,
    "mandate_review_snapshot.json": snapshot_mandate_review,
    "test_evidence_retry_snapshot.json": snapshot_test_evidence_retry,
    "csf_data_ready_confirmation_snapshot.json": snapshot_csf_data_ready_confirmation,
    "data_ready_confirmation_snapshot.json": snapshot_data_ready_confirmation,
    "signal_ready_confirmation_snapshot.json": snapshot_signal_ready_confirmation,
}


def export_default_snapshots(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with TemporaryDirectory() as tmp:
        outputs_root = Path(tmp) / "outputs"
        for file_name, builder in SCENARIOS.items():
            snapshot = builder(outputs_root)
            target = output_dir / file_name
            target.write_text(
                json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            written.append(target)
    return written
