from pathlib import Path

import yaml

from runtime.tools.test_evidence_runtime import build_test_evidence_from_train_freeze, scaffold_test_evidence


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _test_evidence_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "test_window_source": "time_split.json::test",
                    "test_window_note": "Freeze test split from mandate only.",
                    "train_reuse_note": "Reuse train thresholds and kept params only.",
                },
                "missing_items": [],
            },
            "formal_gate_contract": {
                "confirmed": confirmed,
                "draft": {
                    "selected_param_ids": ["baseline_v1"],
                    "candidate_best_h": ["15m", "30m"],
                    "best_h": "30m",
                    "formal_gate_note": "Formal gate uses frozen train thresholds only.",
                    "threshold_reuse_note": "No train threshold re-estimation in test.",
                },
                "missing_items": [],
            },
            "admissibility_contract": {
                "confirmed": confirmed,
                "draft": {
                    "selected_symbols": ["ETHUSDT", "SOLUSDT"],
                    "admissibility_rule": "Only symbols passing formal test gate are admitted.",
                    "rejection_rule": "Reject symbols failing structure continuation checks.",
                    "summary_note": "Whitelist is frozen for downstream backtest consumers.",
                },
                "missing_items": [],
            },
            "audit_contract": {
                "confirmed": confirmed,
                "draft": {
                    "audit_items": ["HAC t value", "crowding overlap"],
                    "formal_vs_audit_boundary": "Crowding stays audit-only unless upstream contract changes.",
                    "crowding_scope": "Compare against known crowded beta-style benchmarks.",
                    "condition_analysis_note": "Condition buckets remain explanatory only.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "report_by_h.parquet",
                        "symbol_summary.parquet",
                        "admissibility_report.parquet",
                        "test_gate_table.csv",
                        "selected_symbols_test.csv",
                        "selected_symbols_test.parquet",
                        "frozen_spec.json",
                    ],
                    "consumer_stage": "backtest_ready",
                    "frozen_spec_note": "Backtest must consume frozen whitelist and best_h only.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_upstream_stages(lineage_root: Path) -> None:
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = lineage_root / "02_data_ready"
    signal_ready_dir = lineage_root / "03_signal_ready"
    train_dir = lineage_root / "04_train_freeze"

    (mandate_dir / "author" / "formal").mkdir(parents=True)
    (data_ready_dir / "author" / "formal").mkdir(parents=True)
    (signal_ready_dir / "author" / "formal").mkdir(parents=True)
    (train_dir / "author" / "formal").mkdir(parents=True)

    (mandate_dir / "author" / "formal" / "time_split.json").write_text(
        '{"train": "", "test": "", "holding_horizons": ["15m", "30m"]}\n',
        encoding="utf-8",
    )
    (data_ready_dir / "author" / "formal" / "aligned_bars").mkdir()
    (signal_ready_dir / "author" / "formal" / "params").mkdir()
    (signal_ready_dir / "author" / "formal" / "param_manifest.csv").write_text(
        "\n".join(
            [
                "param_id,scope,baseline_signal,parameter_values",
                'baseline_v1,baseline,btc_alt_residual_response,"event_window: 15m"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (train_dir / "author" / "formal" / "train_thresholds.json").write_text('{"kept_param_ids":["baseline_v1"]}\n', encoding="utf-8")
    (train_dir / "author" / "formal" / "train_param_ledger.csv").write_text(
        "\n".join(
            [
                "param_id,status,selection_rule,train_window_source,notes",
                "baseline_v1,kept,baseline-only,time_split.json::train,ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_scaffold_test_evidence_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_upstream_stages(lineage_root)

    test_dir = scaffold_test_evidence(lineage_root)

    draft = yaml.safe_load((test_dir / "author" / "draft" / "test_evidence_draft.yaml").read_text(encoding="utf-8"))
    assert test_dir == lineage_root / "05_test_evidence"
    assert set(draft["groups"]) == {
        "window_contract",
        "formal_gate_contract",
        "admissibility_contract",
        "audit_contract",
        "delivery_contract",
    }
    assert draft["groups"]["formal_gate_contract"]["draft"]["selected_param_ids"] == ["baseline_v1"]


def test_build_test_evidence_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_upstream_stages(lineage_root)
    test_dir = lineage_root / "05_test_evidence"
    test_dir.mkdir(parents=True)
    _write_yaml(test_dir / "author" / "draft" / "test_evidence_draft.yaml", _test_evidence_draft(confirmed=True))

    built_dir = build_test_evidence_from_train_freeze(lineage_root)

    assert built_dir == test_dir
    formal_dir = test_dir / "author" / "formal"
    assert (formal_dir / "report_by_h.parquet").exists()
    assert (formal_dir / "symbol_summary.parquet").exists()
    assert (formal_dir / "admissibility_report.parquet").exists()
    assert (formal_dir / "test_gate_table.csv").exists()
    assert (formal_dir / "crowding_review.md").exists()
    assert (formal_dir / "selected_symbols_test.csv").exists()
    assert (formal_dir / "selected_symbols_test.parquet").exists()
    assert (formal_dir / "frozen_spec.json").exists()
    assert (formal_dir / "test_gate_decision.md").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()
