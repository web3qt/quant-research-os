from pathlib import Path

import pytest
import yaml

from runtime.tools.review_skillgen.protected_state_guard import ProtectedStateError
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.review.test_start_review_session import _prepare_mandate_stage
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.session.test_research_session_runtime import _freeze_draft, _write_data_inventory
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


def test_run_review_preflight_rejects_stale_review_runtime_state(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    state_path = stage_dir / "review" / "state" / "review_runtime_state.yaml"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        yaml.safe_dump(
            {
                "review_state": "review_closed_pass",
                "active_review_cycle_id": "manual-cycle",
                "review_bound_author_digest": "0" * 64,
                "last_review_verdict": "PASS",
                "closure_written_at": "2026-05-11T00:00:00Z",
                "updated_at": "2026-05-11T00:00:00Z",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ProtectedStateError, match="REVIEW_STATE_PROJECTION_DRIFT"):
        run_review_preflight(explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})


def test_run_review_preflight_rejects_existing_research_preflight_blocker(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    (stage_dir / "author" / "formal" / "run_config.toml").write_text("version = 1\n", encoding="utf-8")
    inventory_root = _write_data_inventory(
        tmp_path / "inventory",
        data_min_ts="2024-03-01",
        data_max_ts="2024-12-31",
    )
    freeze_draft = _freeze_draft(confirmed=True)
    freeze_draft["groups"]["scope_contract"]["draft"]["time_boundary"] = "2023-01-01/2026-03-01"
    freeze_draft["groups"]["data_contract"]["draft"]["data_source"] = str(inventory_root)
    draft_path = stage_dir / "author" / "draft" / "mandate_freeze_draft.yaml"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(yaml.safe_dump(freeze_draft, sort_keys=False), encoding="utf-8")

    payload = run_review_preflight(explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})

    assert payload["status"] == "FAIL"
    assert payload["content_findings"] == payload["research_preflight_findings"]
    assert payload["upstream_binding_findings"] == []
    assert payload["research_preflight_findings"] == [
        (
            "TIME_COVERAGE_OUT_OF_RANGE: Frozen review windows exceed real data coverage. "
            "Adjust train/test/backtest/holdout to fit actual data coverage before mandate freeze."
        )
    ]


def test_run_review_preflight_does_not_apply_mandate_blocker_rule_to_post_mandate_stage(
    tmp_path: Path,
) -> None:
    stage_dir = _prepare_signal_stage(tmp_path)
    inventory_root = _write_data_inventory(
        tmp_path / "inventory",
        data_min_ts="2024-03-01",
        data_max_ts="2024-12-31",
    )
    freeze_draft = _freeze_draft(confirmed=True)
    freeze_draft["groups"]["scope_contract"]["draft"]["time_boundary"] = "2023-01-01/2026-03-01"
    freeze_draft["groups"]["data_contract"]["draft"]["data_source"] = str(inventory_root)
    draft_path = stage_dir / "author" / "draft" / "mandate_freeze_draft.yaml"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(yaml.safe_dump(freeze_draft, sort_keys=False), encoding="utf-8")

    payload = run_review_preflight(cwd=stage_dir)

    assert payload["research_preflight_findings"] == []
    assert payload["status"] == "FAIL"
    assert any("CSF-SIGNAL-BIND-001" in item for item in payload["upstream_binding_findings"])


def test_run_review_preflight_stale_protected_state_wins_over_research_preflight_blocker(
    tmp_path: Path,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    (stage_dir / "author" / "formal" / "run_config.toml").write_text("version = 1\n", encoding="utf-8")
    inventory_root = _write_data_inventory(
        tmp_path / "inventory",
        data_min_ts="2024-03-01",
        data_max_ts="2024-12-31",
    )
    freeze_draft = _freeze_draft(confirmed=True)
    freeze_draft["groups"]["scope_contract"]["draft"]["time_boundary"] = "2023-01-01/2026-03-01"
    freeze_draft["groups"]["data_contract"]["draft"]["data_source"] = str(inventory_root)
    draft_path = stage_dir / "author" / "draft" / "mandate_freeze_draft.yaml"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(yaml.safe_dump(freeze_draft, sort_keys=False), encoding="utf-8")
    state_path = stage_dir / "review" / "state" / "review_runtime_state.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        yaml.safe_dump(
            {
                "review_state": "review_closed_pass",
                "active_review_cycle_id": "manual-cycle",
                "review_bound_author_digest": "0" * 64,
                "last_review_verdict": "PASS",
                "closure_written_at": "2026-05-11T00:00:00Z",
                "updated_at": "2026-05-11T00:00:00Z",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ProtectedStateError, match="REVIEW_STATE_PROJECTION_DRIFT"):
        run_review_preflight(explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})
