from pathlib import Path

from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.session.test_research_session_runtime import _write_minimal_stage_outputs


def _prepare_signal_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "preflight_case"
    stage_dir = lineage_root / "03_csf_signal_ready"
    _write_minimal_stage_outputs(stage_dir, stage="csf_signal_ready")
    ensure_stage_program(lineage_root, "csf_signal_ready")
    write_fake_stage_provenance(lineage_root, "csf_signal_ready")
    mandate_dir = lineage_root / "01_mandate" / "author" / "formal"
    mandate_dir.mkdir(parents=True, exist_ok=True)
    (mandate_dir / "research_route.yaml").write_text(
        "\n".join(
            [
                "research_route: cross_sectional_factor",
                "factor_role: standalone_alpha",
                "factor_structure: single_factor",
                "portfolio_expression: long_short_market_neutral",
                "neutralization_policy: group_neutral",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return stage_dir


def test_run_review_preflight_reports_upstream_binding_failure_for_signal_ready(tmp_path: Path) -> None:
    stage_dir = _prepare_signal_stage(tmp_path)
    formal_dir = stage_dir / "author" / "formal"
    (formal_dir / "route_inheritance_contract.yaml").write_text(
        "\n".join(
            [
                "research_route: cross_sectional_factor",
                "factor_role: regime_filter",
                "factor_structure: single_factor",
                "portfolio_expression: long_short_market_neutral",
                "neutralization_policy: group_neutral",
                "inheritance_mode: exact_copy",
                "target_strategy_reference_requirement_status: required_satisfied",
                "group_taxonomy_reference_requirement_status: required_satisfied",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    payload = run_review_preflight(cwd=stage_dir)

    assert payload["status"] == "FAIL"
    assert any("CSF-SIGNAL-BIND-001" in item for item in payload["upstream_binding_findings"])
