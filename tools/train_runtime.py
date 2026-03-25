from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml


TRAIN_FREEZE_DRAFT_FILE = "train_freeze_draft.yaml"
TRAIN_FREEZE_GROUP_ORDER = [
    "window_contract",
    "threshold_contract",
    "quality_filters",
    "param_governance",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_train_freeze_draft(*, candidate_param_ids: list[str] | None = None) -> dict[str, Any]:
    param_ids = candidate_param_ids or []
    return {
        "groups": {
            "window_contract": {
                "confirmed": False,
                "draft": {
                    "train_window_source": "time_split.json::train",
                    "train_window_note": "",
                    "leakage_guardrail": "",
                },
                "missing_items": [],
            },
            "threshold_contract": {
                "confirmed": False,
                "draft": {
                    "threshold_targets": [],
                    "threshold_rule": "",
                    "regime_cut_rule": "",
                    "frozen_outputs_note": "",
                },
                "missing_items": [],
            },
            "quality_filters": {
                "confirmed": False,
                "draft": {
                    "quality_metrics": [],
                    "filter_rule": "",
                    "symbol_param_admission_rule": "",
                    "audit_note": "",
                },
                "missing_items": [],
            },
            "param_governance": {
                "confirmed": False,
                "draft": {
                    "candidate_param_ids": param_ids,
                    "kept_param_ids": param_ids,
                    "rejected_param_ids": [],
                    "selection_rule": "",
                    "reject_log_note": "",
                    "coarse_to_fine_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [
                        "train_thresholds.json",
                        "train_quality.parquet",
                        "train_param_ledger.csv",
                        "train_rejects.csv",
                    ],
                    "consumer_stage": "test_evidence",
                    "reuse_constraints": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_train_freeze(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    train_dir = lineage_root / "04_train_freeze"
    train_dir.mkdir(parents=True, exist_ok=True)

    draft_path = train_dir / TRAIN_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_train_freeze_draft(candidate_param_ids=_load_param_ids(lineage_root)))
    return train_dir


def build_train_freeze_from_signal_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    signal_ready_dir = lineage_root / "03_signal_ready"
    train_dir = scaffold_train_freeze(lineage_root)

    missing_signal_ready = [
        name
        for name in [
            "param_manifest.csv",
            "params",
            "signal_coverage.csv",
            "signal_coverage.md",
            "signal_coverage_summary.md",
            "signal_contract.md",
            "signal_fields_contract.md",
            "signal_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (signal_ready_dir / name).exists()
    ]
    if missing_signal_ready:
        raise ValueError(
            "signal_ready artifacts missing before train_freeze build: "
            + ", ".join(missing_signal_ready)
        )

    freeze_groups = _require_confirmed_freeze_groups(train_dir)
    window_contract = freeze_groups["window_contract"]["draft"]
    threshold_contract = freeze_groups["threshold_contract"]["draft"]
    quality_filters = freeze_groups["quality_filters"]["draft"]
    param_governance = freeze_groups["param_governance"]["draft"]
    delivery_contract = freeze_groups["delivery_contract"]["draft"]

    train_window_source = _required_draft_value(window_contract, "train_window_source")
    train_window_note = _required_draft_value(window_contract, "train_window_note")
    leakage_guardrail = _required_draft_value(window_contract, "leakage_guardrail")
    threshold_rule = _required_draft_value(threshold_contract, "threshold_rule")
    regime_cut_rule = _required_draft_value(threshold_contract, "regime_cut_rule")
    frozen_outputs_note = _required_draft_value(threshold_contract, "frozen_outputs_note")
    filter_rule = _required_draft_value(quality_filters, "filter_rule")
    symbol_param_admission_rule = _required_draft_value(quality_filters, "symbol_param_admission_rule")
    audit_note = _required_draft_value(quality_filters, "audit_note")
    selection_rule = _required_draft_value(param_governance, "selection_rule")
    reject_log_note = _required_draft_value(param_governance, "reject_log_note")
    coarse_to_fine_note = _required_draft_value(param_governance, "coarse_to_fine_note")
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    reuse_constraints = _required_draft_value(delivery_contract, "reuse_constraints")

    threshold_targets = _string_list(threshold_contract.get("threshold_targets", []))
    quality_metrics = _string_list(quality_filters.get("quality_metrics", []))
    candidate_param_ids = _string_list(param_governance.get("candidate_param_ids", []))
    kept_param_ids = _string_list(param_governance.get("kept_param_ids", []))
    rejected_param_ids = _string_list(param_governance.get("rejected_param_ids", []))
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))

    if not candidate_param_ids:
        candidate_param_ids = _load_param_ids(lineage_root)
    if not kept_param_ids:
        kept_param_ids = list(candidate_param_ids)
    unknown_kept = sorted(set(kept_param_ids) - set(candidate_param_ids))
    if unknown_kept:
        raise ValueError(f"kept_param_ids must be drawn from candidate_param_ids: {', '.join(unknown_kept)}")
    unknown_rejected = sorted(set(rejected_param_ids) - set(candidate_param_ids))
    if unknown_rejected:
        raise ValueError(
            f"rejected_param_ids must be drawn from candidate_param_ids: {', '.join(unknown_rejected)}"
        )

    (train_dir / "train_thresholds.json").write_text(
        json.dumps(
            {
                "stage": "train_calibration",
                "lineage_id": lineage_root.name,
                "source_stage": "signal_ready",
                "train_window_source": train_window_source,
                "train_window_note": train_window_note,
                "leakage_guardrail": leakage_guardrail,
                "threshold_targets": threshold_targets,
                "threshold_rule": threshold_rule,
                "regime_cut_rule": regime_cut_rule,
                "quality_metrics": quality_metrics,
                "filter_rule": filter_rule,
                "symbol_param_admission_rule": symbol_param_admission_rule,
                "kept_param_ids": kept_param_ids,
                "rejected_param_ids": rejected_param_ids,
                "frozen_outputs_note": frozen_outputs_note,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    (train_dir / "train_quality.parquet").write_text(
        "\n".join(
            [
                "placeholder train-quality artifact for governance-first train_freeze stage",
                f"quality_metrics={','.join(quality_metrics)}",
                f"filter_rule={filter_rule}",
                f"symbol_param_admission_rule={symbol_param_admission_rule}",
                f"audit_note={audit_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with (train_dir / "train_param_ledger.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["param_id", "status", "selection_rule", "train_window_source", "notes"])
        for param_id in candidate_param_ids:
            status = "kept" if param_id in kept_param_ids else "rejected"
            note = coarse_to_fine_note if status == "kept" else reject_log_note
            writer.writerow([param_id, status, selection_rule, train_window_source, note])

    with (train_dir / "train_rejects.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["param_id", "reject_reason"])
        for param_id in rejected_param_ids:
            writer.writerow([param_id, reject_log_note])

    (train_dir / "train_gate_decision.md").write_text(
        "\n".join(
            [
                "# Train Gate Decision",
                "",
                "- Formal gate decision remains pending until review findings and review closure are written.",
                f"- Train window source: {train_window_source}",
                f"- Threshold rule: {threshold_rule}",
                f"- Regime cut rule: {regime_cut_rule}",
                f"- Selection rule: {selection_rule}",
                f"- Next consumer stage: {consumer_stage}",
                f"- Reuse constraints: {reuse_constraints}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (train_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# Artifact Catalog",
                "",
                "- train_thresholds.json",
                "- train_quality.parquet",
                "- train_param_ledger.csv",
                "- train_rejects.csv",
                "- train_gate_decision.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (train_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# Field Dictionary",
                "",
                f"- `train_window_source`: upstream train split reference, currently `{train_window_source}`.",
                f"- `threshold_targets`: fields or contracts governed by train freeze, currently {threshold_targets}.",
                f"- `threshold_rule`: frozen threshold estimation rule, currently `{threshold_rule}`.",
                f"- `regime_cut_rule`: frozen regime cut rule, currently `{regime_cut_rule}`.",
                f"- `quality_metrics`: quality metrics reviewed in train freeze, currently {quality_metrics}.",
                f"- `filter_rule`: frozen train quality filter logic, currently `{filter_rule}`.",
                f"- `candidate_param_ids`: upstream parameter ids considered in train, currently {candidate_param_ids}.",
                f"- `kept_param_ids`: parameter ids allowed to proceed, currently {kept_param_ids}.",
                f"- `rejected_param_ids`: parameter ids rejected during train freeze, currently {rejected_param_ids}.",
                f"- `machine_artifacts`: formal machine outputs from this stage, currently {machine_artifacts}.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return train_dir


def _load_param_ids(lineage_root: Path) -> list[str]:
    manifest_path = lineage_root / "03_signal_ready" / "param_manifest.csv"
    if not manifest_path.exists():
        return []

    rows = manifest_path.read_text(encoding="utf-8").splitlines()
    if len(rows) <= 1:
        return []

    param_ids: list[str] = []
    for row in rows[1:]:
        parts = row.split(",", 1)
        if not parts or not parts[0]:
            continue
        param_ids.append(parts[0])
    return param_ids


def _require_confirmed_freeze_groups(train_dir: Path) -> dict[str, Any]:
    payload = yaml.safe_load((train_dir / TRAIN_FREEZE_DRAFT_FILE).read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})

    missing = [name for name in TRAIN_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"train_freeze draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"train_freeze draft missing required value: {key}")
    return value


def _string_list(values: list[Any]) -> list[str]:
    return [str(item).strip() for item in values if str(item).strip()]
