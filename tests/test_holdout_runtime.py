from pathlib import Path

import yaml

from tools.holdout_runtime import (
    build_holdout_validation_from_backtest,
    scaffold_holdout_validation,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _holdout_validation_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "holdout_window_source": "time_split.json::holdout",
                    "window_plan": ["single_window", "merged_window"],
                    "window_note": "Freeze final untouched validation windows only.",
                    "no_redefinition_guardrail": "Holdout cannot redefine the research question.",
                },
                "missing_items": [],
            },
            "reuse_contract": {
                "confirmed": confirmed,
                "draft": {
                    "frozen_config_source": "06_backtest/backtest_frozen_config.json",
                    "selected_combo_source": "06_backtest/selected_strategy_combo.json",
                    "selected_symbols": ["ETHUSDT", "SOLUSDT"],
                    "best_h": "30m",
                    "no_reestimate_rule": "Do not re-estimate any research parameter in holdout.",
                    "no_whitelist_change_rule": "Do not change symbol whitelist in holdout.",
                },
                "missing_items": [],
            },
            "drift_audit": {
                "confirmed": confirmed,
                "draft": {
                    "required_views": ["single_window", "merged_window"],
                    "direction_flip_rule": "Escalate if holdout direction flips without execution explanation.",
                    "sparse_activity_rule": "Explain low-trade windows without changing frozen policy.",
                    "explanatory_note": "Sparse windows may be normal under strict frozen filters.",
                },
                "missing_items": [],
            },
            "failure_governance": {
                "confirmed": confirmed,
                "draft": {
                    "retryable_conditions": ["execution defect", "data delivery defect"],
                    "no_go_conditions": ["unexplained direction flip", "structure collapse"],
                    "child_lineage_trigger": "Open child lineage when a new mechanism is needed to explain failure.",
                    "rollback_boundary": "Only holdout rerun/reporting is allowed in-place.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "holdout_run_manifest.json",
                        "holdout_backtest_compare.csv",
                        "window_results/",
                    ],
                    "consumer_stage": "promotion_decision",
                    "field_doc_rule": "Every machine artifact needs companion field documentation.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_backtest_stage(lineage_root: Path) -> None:
    mandate_dir = lineage_root / "01_mandate"
    mandate_dir.mkdir(parents=True)
    (mandate_dir / "time_split.json").write_text(
        '{"train":"2024-01-01/2024-06-30","test":"2024-07-01/2024-09-30","holdout":"2024-10-01/2024-12-31"}\n',
        encoding="utf-8",
    )

    backtest_dir = lineage_root / "06_backtest"
    backtest_dir.mkdir(parents=True)
    (backtest_dir / "backtest_frozen_config.json").write_text(
        '{"selected_symbols":["ETHUSDT","SOLUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )
    (backtest_dir / "selected_strategy_combo.json").write_text(
        '{"combo_id":"baseline_combo_v1","selected_symbols":["ETHUSDT","SOLUSDT"],"best_h":"30m"}\n',
        encoding="utf-8",
    )


def test_scaffold_holdout_validation_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_backtest_stage(lineage_root)

    holdout_dir = scaffold_holdout_validation(lineage_root)

    draft = yaml.safe_load(
        (holdout_dir / "holdout_validation_draft.yaml").read_text(encoding="utf-8")
    )
    assert holdout_dir == lineage_root / "07_holdout"
    assert set(draft["groups"]) == {
        "window_contract",
        "reuse_contract",
        "drift_audit",
        "failure_governance",
        "delivery_contract",
    }
    assert draft["groups"]["reuse_contract"]["draft"]["selected_symbols"] == ["ETHUSDT", "SOLUSDT"]


def test_build_holdout_validation_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_backtest_stage(lineage_root)
    holdout_dir = lineage_root / "07_holdout"
    holdout_dir.mkdir(parents=True)
    _write_yaml(
        holdout_dir / "holdout_validation_draft.yaml",
        _holdout_validation_draft(confirmed=True),
    )

    built_dir = build_holdout_validation_from_backtest(lineage_root)

    assert built_dir == holdout_dir
    assert (holdout_dir / "holdout_run_manifest.json").exists()
    assert (holdout_dir / "holdout_backtest_compare.csv").exists()
    assert (holdout_dir / "window_results").exists()
    assert (holdout_dir / "holdout_gate_decision.md").exists()
    assert (holdout_dir / "artifact_catalog.md").exists()
    assert (holdout_dir / "field_dictionary.md").exists()
