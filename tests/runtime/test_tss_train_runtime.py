from pathlib import Path

import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from runtime.tools.tss_train_runtime import (
    build_tss_train_freeze_from_signal_ready,
    scaffold_tss_train_freeze,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_tss_signal_ready_stage(lineage_root: Path) -> None:
    formal_dir = lineage_root / "03_tss_signal_ready" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "signal_manifest.yaml",
        "param_manifest.csv",
        "signal_panel.parquet",
        "signal_event_panel.parquet",
        "route_inheritance_contract.yaml",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")


def _tss_train_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "calibration_contract": {
                "confirmed": confirmed,
                "draft": {
                    "train_window_source": "time_split.json::train",
                    "calibration_metric": "mean_forward_return",
                    "calibration_note": "Calibrate thresholds only on train.",
                },
                "missing_items": [],
            },
            "threshold_contract": {
                "confirmed": confirmed,
                "draft": {
                    "threshold_field": "signal_value",
                    "candidate_thresholds": [0.0],
                    "threshold_selection_rule": "baseline threshold",
                },
                "missing_items": [],
            },
            "search_governance_contract": {
                "confirmed": confirmed,
                "draft": {
                    "candidate_variant_ids": ["baseline_v1"],
                    "kept_variant_ids": ["baseline_v1"],
                    "rejected_variant_ids": [],
                    "non_governable_axes_after_signal": ["input_field_map", "signal_expression"],
                },
                "missing_items": [],
            },
            "reuse_contract": {
                "confirmed": confirmed,
                "draft": {
                    "frozen_signal_contract_reference": "03_tss_signal_ready/author/formal/signal_manifest.yaml",
                    "no_signal_redefinition_rule": "Train cannot consume forward_label_base or change signal inputs.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["tss_train_freeze.yaml", "train_variant_ledger.csv"],
                    "consumer_stage": "tss_test_evidence",
                    "reuse_constraints": "Test must reuse train-kept variants.",
                },
                "missing_items": [],
            },
        }
    }


def test_scaffold_tss_train_freeze_creates_draft_under_tss_stage_dir(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"

    stage_dir = scaffold_tss_train_freeze(lineage_root)

    assert stage_dir == lineage_root / "04_tss_train_freeze"
    draft_path = stage_dir / "author" / "draft" / "tss_train_freeze_draft.yaml"
    assert draft_path.exists()
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
    assert set(payload["groups"]) == {
        "calibration_contract",
        "threshold_contract",
        "search_governance_contract",
        "reuse_contract",
        "delivery_contract",
    }


def test_build_tss_train_freeze_writes_planned_formal_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_signal_ready_stage(lineage_root)
    stage_dir = lineage_root / "04_tss_train_freeze"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_train_freeze_draft.yaml",
        _tss_train_freeze_draft(confirmed=True),
    )

    built_dir = build_tss_train_freeze_from_signal_ready(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "tss_train_freeze.yaml").exists()
    assert (formal_dir / "train_threshold_ledger.csv").exists()
    assert (formal_dir / "train_variant_ledger.csv").exists()
    assert (formal_dir / "train_variant_rejects.csv").exists()
    payload = yaml.safe_load((formal_dir / "tss_train_freeze.yaml").read_text(encoding="utf-8"))
    assert payload["stage"] == "tss_train_freeze"
    assert payload["research_route"] == "time_series_signal"
    assert payload["search_governance_contract"]["kept_variant_ids"] == ["baseline_v1"]
