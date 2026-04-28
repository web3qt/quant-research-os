from pathlib import Path

import yaml

from runtime.tools.research_session import SESSION_STAGE_PROGRAM_SPECS, STAGE_ACTIVE_SKILLS
from runtime.tools.review_skillgen import context_inference, render
from runtime.tools.review_skillgen.upstream_binding_validator import validate_upstream_bindings


ROOT = Path(__file__).resolve().parents[2]


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _workflow() -> dict:
    return yaml.safe_load(
        (ROOT / "contracts" / "stages" / "workflow_stage_gates.yaml").read_text(encoding="utf-8")
    )


def test_review_skillgen_infers_tss_stage_names() -> None:
    assert hasattr(context_inference, "canonical_stage_from_path_hint")
    canonical_stage = context_inference.canonical_stage_from_path_hint

    assert canonical_stage("02_tss_data_ready") == "tss_data_ready"
    assert canonical_stage("03_tss_signal_ready") == "tss_signal_ready"
    assert canonical_stage("04_tss_train_freeze") == "tss_train_freeze"
    assert canonical_stage("05_tss_test_evidence") == "tss_test_evidence"
    assert canonical_stage("06_tss_backtest_ready") == "tss_backtest_ready"
    assert canonical_stage("07_tss_holdout_validation") == "tss_holdout_validation"


def test_tss_workflow_stage_gates_lock_chain_and_program_contracts() -> None:
    workflow = _workflow()
    stages = workflow["stages"]
    program_keys = workflow["lineage_program_contract"]["stage_program_keys"]

    assert stages["mandate"]["downstream_permissions"]["may_advance_to"] == [
        "tss_data_ready",
        "csf_data_ready",
    ]
    assert stages["tss_data_ready"]["allowed_previous_stages"] == ["mandate"]
    assert stages["tss_data_ready"]["downstream_permissions"]["may_advance_to"] == ["tss_signal_ready"]
    assert stages["tss_signal_ready"]["allowed_previous_stages"] == ["tss_data_ready"]
    assert stages["tss_train_freeze"]["allowed_previous_stages"] == ["tss_signal_ready"]
    assert stages["tss_test_evidence"]["allowed_previous_stages"] == ["tss_train_freeze"]
    assert stages["tss_backtest_ready"]["allowed_previous_stages"] == ["tss_test_evidence"]
    assert stages["tss_holdout_validation"]["allowed_previous_stages"] == ["tss_backtest_ready"]

    assert program_keys["tss_data_ready"]["program_dir"] == (
        "outputs/<lineage_id>/program/time_series_signal/tss_data_ready/"
    )
    assert program_keys["tss_data_ready"]["provenance_target"] == (
        "outputs/<lineage_id>/02_tss_data_ready/program_execution_manifest.json"
    )


def test_tss_session_stage_specs_and_active_skills_are_canonical() -> None:
    expected = {
        "tss_data_ready": ("02_tss_data_ready", "qros-tss-data-ready-author", "qros-tss-data-ready-review"),
        "tss_signal_ready": ("03_tss_signal_ready", "qros-tss-signal-ready-author", "qros-tss-signal-ready-review"),
        "tss_train_freeze": ("04_tss_train_freeze", "qros-tss-train-freeze-author", "qros-tss-train-freeze-review"),
        "tss_test_evidence": ("05_tss_test_evidence", "qros-tss-test-evidence-author", "qros-tss-test-evidence-review"),
        "tss_backtest_ready": ("06_tss_backtest_ready", "qros-tss-backtest-ready-author", "qros-tss-backtest-ready-review"),
        "tss_holdout_validation": (
            "07_tss_holdout_validation",
            "qros-tss-holdout-validation-author",
            "qros-tss-holdout-validation-review",
        ),
    }

    for stage, (stage_dir, author_skill, review_skill) in expected.items():
        assert SESSION_STAGE_PROGRAM_SPECS[stage].stage_dir_name == stage_dir
        assert STAGE_ACTIVE_SKILLS[f"{stage}_author"] == author_skill
        assert STAGE_ACTIVE_SKILLS[f"{stage}_review_confirmation_pending"] == review_skill
        assert STAGE_ACTIVE_SKILLS[f"{stage}_review"] == review_skill


def test_review_skill_render_documents_tss_deterministic_preflight() -> None:
    block = render._render_deterministic_preflight("tss_signal_ready")

    assert "contracts/artifacts/tss_signal_ready_artifacts.yaml" in block
    assert "TSS-SIGNAL-SEMANTIC-001" in block


def test_upstream_binding_validator_checks_tss_signal_route_inheritance(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = lineage_root / "03_tss_signal_ready" / "author" / "formal"
    _write_yaml(
        lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml",
        {"research_route": "time_series_signal", "signal_family": "breakout"},
    )
    _write_yaml(
        formal_dir / "route_inheritance_contract.yaml",
        {"research_route": "cross_sectional_factor", "signal_family": "breakout"},
    )

    findings = validate_upstream_bindings(
        stage="tss_signal_ready",
        lineage_root=lineage_root,
        author_formal_dir=formal_dir,
        structural_binding_checks=[],
    )

    assert any("TSS-SIGNAL-BIND-001" in item for item in findings)
