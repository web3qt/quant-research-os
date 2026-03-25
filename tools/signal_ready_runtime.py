from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml


SIGNAL_READY_FREEZE_DRAFT_FILE = "signal_ready_freeze_draft.yaml"
SIGNAL_READY_FREEZE_GROUP_ORDER = [
    "signal_expression",
    "param_identity",
    "time_semantics",
    "signal_schema",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_signal_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "signal_expression": {
                "confirmed": False,
                "draft": {
                    "baseline_signal": "",
                    "upstream_inputs": [],
                    "state_fields": [],
                    "filter_fields": [],
                },
                "missing_items": [],
            },
            "param_identity": {
                "confirmed": False,
                "draft": {
                    "param_id": "",
                    "parameter_values": {},
                    "identity_note": "",
                },
                "missing_items": [],
            },
            "time_semantics": {
                "confirmed": False,
                "draft": {
                    "signal_timestamp": "",
                    "label_alignment": "",
                    "no_lookahead_guardrail": "",
                },
                "missing_items": [],
            },
            "signal_schema": {
                "confirmed": False,
                "draft": {
                    "timeseries_schema": [],
                    "quality_fields": [],
                    "schema_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "doc_artifacts": [],
                    "consumer_stage": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_signal_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    signal_ready_dir = lineage_root / "03_signal_ready"
    signal_ready_dir.mkdir(parents=True, exist_ok=True)

    draft_path = signal_ready_dir / SIGNAL_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_signal_ready_freeze_draft())
    return signal_ready_dir


def build_signal_ready_from_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    data_ready_dir = lineage_root / "02_data_ready"
    signal_ready_dir = scaffold_signal_ready(lineage_root)

    missing_data_ready = [
        name
        for name in [
            "aligned_bars",
            "rolling_stats",
            "pair_stats",
            "benchmark_residual",
            "topic_basket_state",
            "qc_report.parquet",
            "dataset_manifest.json",
            "data_contract.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (data_ready_dir / name).exists()
    ]
    if missing_data_ready:
        raise ValueError(
            f"data_ready artifacts missing before signal_ready build: {', '.join(missing_data_ready)}"
        )

    freeze_groups = _require_confirmed_freeze_groups(signal_ready_dir)
    signal_expression = freeze_groups["signal_expression"]["draft"]
    param_identity = freeze_groups["param_identity"]["draft"]
    time_semantics = freeze_groups["time_semantics"]["draft"]
    signal_schema = freeze_groups["signal_schema"]["draft"]
    delivery_contract = freeze_groups["delivery_contract"]["draft"]

    baseline_signal = _required_draft_value(signal_expression, "baseline_signal")
    param_id = _required_draft_value(param_identity, "param_id")
    identity_note = _required_draft_value(param_identity, "identity_note")
    signal_timestamp = _required_draft_value(time_semantics, "signal_timestamp")
    label_alignment = _required_draft_value(time_semantics, "label_alignment")
    no_lookahead_guardrail = _required_draft_value(time_semantics, "no_lookahead_guardrail")
    schema_note = _required_draft_value(signal_schema, "schema_note")
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")

    upstream_inputs = _string_list(signal_expression.get("upstream_inputs", []))
    state_fields = _string_list(signal_expression.get("state_fields", []))
    filter_fields = _string_list(signal_expression.get("filter_fields", []))
    timeseries_schema = _string_list(signal_schema.get("timeseries_schema", []))
    quality_fields = _string_list(signal_schema.get("quality_fields", []))
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    doc_artifacts = _string_list(delivery_contract.get("doc_artifacts", []))
    parameter_values = param_identity.get("parameter_values", {})

    params_dir = signal_ready_dir / "params"
    params_dir.mkdir(exist_ok=True)
    (params_dir / f"{param_id}.parquet").write_text(
        "placeholder signal timeseries artifact for baseline-only signal_ready skeleton\n",
        encoding="utf-8",
    )

    with (signal_ready_dir / "param_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["param_id", "scope", "baseline_signal", "parameter_values"])
        writer.writerow([param_id, "baseline", baseline_signal, yaml.safe_dump(parameter_values, sort_keys=True).strip()])

    with (signal_ready_dir / "signal_coverage.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["param_id", "coverage_rate", "low_sample_rate", "pair_missing_rate"])
        writer.writerow([param_id, "1.0", "0.0", "0.0"])

    (signal_ready_dir / "signal_coverage.md").write_text(
        "\n".join(
            [
                "# Signal Coverage",
                "",
                f"- Baseline param_id: {param_id}",
                "- Coverage is placeholder-perfect in the first-wave skeleton.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (signal_ready_dir / "signal_coverage_summary.md").write_text(
        "\n".join(
            [
                "# Signal Coverage Summary",
                "",
                f"- Baseline signal: {baseline_signal}",
                f"- Consumer stage: {consumer_stage}",
                f"- Quality fields: {', '.join(quality_fields)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (signal_ready_dir / "signal_contract.md").write_text(
        "\n".join(
            [
                "# Signal Contract",
                "",
                f"- Baseline signal: {baseline_signal}",
                f"- Param ID: {param_id}",
                f"- Upstream inputs: {', '.join(upstream_inputs)}",
                f"- State fields: {', '.join(state_fields)}",
                f"- Filter fields: {', '.join(filter_fields)}",
                f"- Identity note: {identity_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (signal_ready_dir / "signal_fields_contract.md").write_text(
        "\n".join(
            [
                "# Signal Fields Contract",
                "",
                f"- Timeseries schema: {', '.join(timeseries_schema)}",
                f"- Signal timestamp: {signal_timestamp}",
                f"- Label alignment: {label_alignment}",
                f"- No-lookahead guardrail: {no_lookahead_guardrail}",
                f"- Schema note: {schema_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (signal_ready_dir / "signal_gate_decision.md").write_text(
        "\n".join(
            [
                "# Signal Ready Gate Decision",
                "",
                "- Formal gate decision remains pending until review findings and review closure are written.",
                f"- Baseline-only scope is frozen for param_id `{param_id}`.",
                f"- Next consumer stage: {consumer_stage}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (signal_ready_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# Artifact Catalog",
                "",
                "- param_manifest.csv",
                "- params/",
                "- signal_coverage.csv",
                "- signal_coverage.md",
                "- signal_coverage_summary.md",
                "- signal_contract.md",
                "- signal_fields_contract.md",
                "- signal_gate_decision.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (signal_ready_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# Field Dictionary",
                "",
                f"- `baseline_signal`: frozen baseline signal expression, currently `{baseline_signal}`.",
                f"- `param_id`: frozen baseline identifier, currently `{param_id}`.",
                f"- `signal_timestamp`: signal time key, currently `{signal_timestamp}`.",
                f"- `label_alignment`: {label_alignment}",
                f"- `no_lookahead_guardrail`: {no_lookahead_guardrail}",
                f"- `timeseries_schema`: {timeseries_schema}",
                f"- `quality_fields`: {quality_fields}",
                f"- `machine_artifacts`: {machine_artifacts}",
                f"- `doc_artifacts`: {doc_artifacts}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return signal_ready_dir


def _require_confirmed_freeze_groups(signal_ready_dir: Path) -> dict[str, Any]:
    draft_path = signal_ready_dir / SIGNAL_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        raise ValueError(f"{SIGNAL_READY_FREEZE_DRAFT_FILE} is required before signal_ready build")

    draft_payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = draft_payload.get("groups", {})
    missing_groups = [
        name for name in SIGNAL_READY_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))
    ]
    if missing_groups:
        raise ValueError(
            f"{SIGNAL_READY_FREEZE_DRAFT_FILE} has unconfirmed groups: {', '.join(missing_groups)}"
        )
    return groups


def _required_draft_value(group_payload: dict[str, Any], key: str) -> str:
    value = group_payload.get(key, "")
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"confirmed signal_ready inputs missing: {key}")
    return normalized


def _string_list(raw_value: Any) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    return [str(item) for item in raw_value if str(item).strip()]
