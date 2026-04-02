import json
from pathlib import Path

import yaml

from tools.anti_drift import canonical_snapshot_from_session_context, diff_snapshot
from tools.research_session import run_research_session


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "anti_drift"


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_minimal_stage_outputs(stage_dir: Path, *, stage: str) -> None:
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


def _write_stage_completion_certificate(
    path: Path,
    *,
    stage_status: str = "PASS",
    final_verdict: str | None = None,
) -> None:
    _write_yaml(
        path,
        {
            "stage_status": stage_status,
            "final_verdict": final_verdict or stage_status,
        },
    )


def _prepare_csf_mandate_review_complete(lineage_root: Path) -> None:
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_yaml(
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
    _write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    _write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")


def _prepare_mainline_mandate_review_complete(lineage_root: Path) -> None:
    stage_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_yaml(
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
    _write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    _write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")


def _load_golden(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_run_research_session_snapshot_matches_mandate_review_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "01_mandate"
    _write_minimal_stage_outputs(stage_dir, stage="mandate")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="mandate-review-replay",
        evidence_refs=("tests/test_anti_drift_replay.py::mandate_review",),
    )

    assert diff_snapshot(_load_golden("mandate_review_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_failure_handler_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "05_test_evidence"
    _write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    _write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="RETRY")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-retry-replay",
        evidence_refs=("tests/test_anti_drift_replay.py::test_evidence_retry",),
    )

    assert diff_snapshot(_load_golden("test_evidence_retry_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_case"
    lineage_root = outputs_root / lineage_id
    _prepare_csf_mandate_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-data-ready-confirmation",
        evidence_refs=("tests/test_anti_drift_replay.py::csf_data_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("csf_data_ready_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_idea_intake_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    status = run_research_session(
        outputs_root=outputs_root,
        raw_idea="BTC leads high-liquidity alts after shock events",
    )
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="idea-intake-confirmation",
        evidence_refs=("tests/test_anti_drift_replay.py::idea_intake_confirmation",),
    )

    assert diff_snapshot(_load_golden("idea_intake_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_mainline_data_ready_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "mainline_case"
    lineage_root = outputs_root / lineage_id
    _prepare_mainline_mandate_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-confirmation",
        evidence_refs=("tests/test_anti_drift_replay.py::data_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("data_ready_confirmation_snapshot.json"), snapshot) == {}
