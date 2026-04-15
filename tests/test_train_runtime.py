from pathlib import Path

import yaml

from runtime.tools.train_runtime import build_train_freeze_from_signal_ready, scaffold_train_freeze


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _train_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "train_window_source": "time_split.json::train",
                    "train_window_note": "Freeze train split from mandate only.",
                    "leakage_guardrail": "Never inspect test or backtest while freezing train.",
                },
                "missing_items": [],
            },
            "threshold_contract": {
                "confirmed": confirmed,
                "draft": {
                    "threshold_targets": ["signal_value", "residual_z"],
                    "threshold_rule": "Estimate quantile thresholds on train only.",
                    "regime_cut_rule": "Freeze volatility buckets on train window only.",
                    "frozen_outputs_note": "Downstream test must reuse these thresholds without re-estimation.",
                },
                "missing_items": [],
            },
            "quality_filters": {
                "confirmed": confirmed,
                "draft": {
                    "quality_metrics": ["coverage_rate", "low_sample_rate"],
                    "filter_rule": "Reject symbol-param pairs below minimum train coverage.",
                    "symbol_param_admission_rule": "Only train-admissible pairs may enter test.",
                    "audit_note": "Keep audit-only observations out of formal gate.",
                },
                "missing_items": [],
            },
            "param_governance": {
                "confirmed": confirmed,
                "draft": {
                    "candidate_param_ids": ["baseline_v1"],
                    "kept_param_ids": ["baseline_v1"],
                    "rejected_param_ids": [],
                    "selection_rule": "Keep baseline-only candidate set for first wave.",
                    "reject_log_note": "No rejected params in baseline-only freeze.",
                    "coarse_to_fine_note": "No additional search expansion allowed in train.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": [
                        "train_thresholds.json",
                        "train_quality.parquet",
                        "train_param_ledger.csv",
                        "train_rejects.csv",
                    ],
                    "consumer_stage": "test_evidence",
                    "reuse_constraints": "Test must consume frozen train outputs only.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_signal_ready_stage(lineage_root: Path) -> None:
    signal_ready_dir = lineage_root / "03_signal_ready"
    formal_dir = signal_ready_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "signal_coverage.csv",
        "signal_coverage.md",
        "signal_coverage_summary.md",
        "signal_contract.md",
        "signal_fields_contract.md",
        "signal_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    (formal_dir / "params").mkdir()
    (formal_dir / "param_manifest.csv").write_text(
        "\n".join(
            [
                "param_id,scope,baseline_signal,parameter_values",
                'baseline_v1,baseline,btc_alt_residual_response,"event_window: 15m"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_scaffold_train_freeze_creates_grouped_draft_with_param_ids(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_signal_ready_stage(lineage_root)

    train_dir = scaffold_train_freeze(lineage_root)

    draft = yaml.safe_load((train_dir / "author" / "draft" / "train_freeze_draft.yaml").read_text(encoding="utf-8"))
    assert train_dir == lineage_root / "04_train_freeze"
    assert set(draft["groups"]) == {
        "window_contract",
        "threshold_contract",
        "quality_filters",
        "param_governance",
        "delivery_contract",
    }
    assert draft["groups"]["param_governance"]["draft"]["candidate_param_ids"] == ["baseline_v1"]


def test_build_train_freeze_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    _prepare_signal_ready_stage(lineage_root)
    train_dir = lineage_root / "04_train_freeze"
    train_dir.mkdir(parents=True)
    _write_yaml(train_dir / "author" / "draft" / "train_freeze_draft.yaml", _train_freeze_draft(confirmed=True))

    built_dir = build_train_freeze_from_signal_ready(lineage_root)

    assert built_dir == train_dir
    formal_dir = train_dir / "author" / "formal"
    assert (formal_dir / "train_thresholds.json").exists()
    assert (formal_dir / "train_quality.parquet").exists()
    assert (formal_dir / "train_param_ledger.csv").exists()
    assert (formal_dir / "train_rejects.csv").exists()
    assert (formal_dir / "train_gate_decision.md").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()
