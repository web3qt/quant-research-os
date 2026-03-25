from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


DATA_READY_FREEZE_DRAFT_FILE = "data_ready_freeze_draft.yaml"
DATA_READY_FREEZE_GROUP_ORDER = [
    "extraction_contract",
    "quality_semantics",
    "universe_admission",
    "shared_derived_layer",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_data_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "extraction_contract": {
                "confirmed": False,
                "draft": {
                    "data_source": "",
                    "time_boundary": "",
                    "primary_time_key": "",
                    "bar_size": "",
                },
                "missing_items": [],
            },
            "quality_semantics": {
                "confirmed": False,
                "draft": {
                    "missing_policy": "",
                    "stale_policy": "",
                    "bad_price_policy": "",
                    "outlier_policy": "",
                    "dedupe_rule": "",
                },
                "missing_items": [],
            },
            "universe_admission": {
                "confirmed": False,
                "draft": {
                    "benchmark_symbol": "",
                    "coverage_floor": "",
                    "admission_rule": "",
                    "exclusion_reporting": "",
                },
                "missing_items": [],
            },
            "shared_derived_layer": {
                "confirmed": False,
                "draft": {
                    "shared_outputs": [],
                    "layer_boundary_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "",
                    "frozen_inputs_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    data_ready_dir = lineage_root / "02_data_ready"
    data_ready_dir.mkdir(parents=True, exist_ok=True)

    draft_path = data_ready_dir / DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_data_ready_freeze_draft())
    return data_ready_dir


def build_data_ready_from_mandate(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = scaffold_data_ready(lineage_root)

    missing_mandate = [
        name
        for name in [
            "mandate.md",
            "research_scope.md",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (mandate_dir / name).exists()
    ]
    if missing_mandate:
        raise ValueError(f"mandate artifacts missing before data_ready build: {', '.join(missing_mandate)}")

    freeze_groups = _require_confirmed_freeze_groups(data_ready_dir)
    extraction_contract = freeze_groups["extraction_contract"]["draft"]
    quality_semantics = freeze_groups["quality_semantics"]["draft"]
    universe_admission = freeze_groups["universe_admission"]["draft"]
    shared_derived_layer = freeze_groups["shared_derived_layer"]["draft"]
    delivery_contract = freeze_groups["delivery_contract"]["draft"]

    data_source = _required_draft_value(extraction_contract, "data_source")
    time_boundary = _required_draft_value(extraction_contract, "time_boundary")
    primary_time_key = _required_draft_value(extraction_contract, "primary_time_key")
    bar_size = _required_draft_value(extraction_contract, "bar_size")
    missing_policy = _required_draft_value(quality_semantics, "missing_policy")
    stale_policy = _required_draft_value(quality_semantics, "stale_policy")
    bad_price_policy = _required_draft_value(quality_semantics, "bad_price_policy")
    outlier_policy = _required_draft_value(quality_semantics, "outlier_policy")
    dedupe_rule = _required_draft_value(quality_semantics, "dedupe_rule")
    benchmark_symbol = _required_draft_value(universe_admission, "benchmark_symbol")
    coverage_floor = _required_draft_value(universe_admission, "coverage_floor")
    admission_rule = _required_draft_value(universe_admission, "admission_rule")
    exclusion_reporting = _required_draft_value(universe_admission, "exclusion_reporting")
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_inputs_note = _required_draft_value(delivery_contract, "frozen_inputs_note")

    shared_outputs = _string_list(shared_derived_layer.get("shared_outputs", []))
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    layer_boundary_note = _required_draft_value(shared_derived_layer, "layer_boundary_note")

    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (data_ready_dir / name).mkdir(exist_ok=True)

    (data_ready_dir / "qc_report.parquet").write_text(
        "placeholder qc artifact for first-wave data_ready skeleton\n",
        encoding="utf-8",
    )
    (data_ready_dir / "dataset_manifest.json").write_text(
        json.dumps(
            {
                "stage": "data_ready",
                "lineage_id": lineage_root.name,
                "source_stage": "mandate",
                "data_source": data_source,
                "time_boundary": time_boundary,
                "primary_time_key": primary_time_key,
                "bar_size": bar_size,
                "shared_outputs": shared_outputs,
                "machine_artifacts": machine_artifacts,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_dir / "validation_report.md").write_text(
        "\n".join(
            [
                "# Validation Report",
                "",
                "- This first-wave output formalizes the data_ready contract and stage skeleton.",
                f"- Benchmark coverage is anchored on `{benchmark_symbol}`.",
                f"- Coverage floor: {coverage_floor}",
                f"- Admission rule: {admission_rule}",
                "",
                "## Quality Semantics",
                "",
                f"- Missing: {missing_policy}",
                f"- Stale: {stale_policy}",
                f"- Bad price: {bad_price_policy}",
                f"- Outlier: {outlier_policy}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_dir / "data_contract.md").write_text(
        "\n".join(
            [
                "# Data Contract",
                "",
                f"- Data source: {data_source}",
                f"- Time boundary: {time_boundary}",
                f"- Primary time key: {primary_time_key}",
                f"- Bar size: {bar_size}",
                f"- Benchmark symbol: {benchmark_symbol}",
                f"- Shared derived outputs: {', '.join(shared_outputs)}",
                f"- Layer boundary: {layer_boundary_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_dir / "dedupe_rule.md").write_text(
        f"# Dedupe Rule\n\n- {dedupe_rule}\n",
        encoding="utf-8",
    )
    (data_ready_dir / "universe_summary.md").write_text(
        "\n".join(
            [
                "# Universe Summary",
                "",
                f"- Benchmark symbol: {benchmark_symbol}",
                f"- Coverage floor: {coverage_floor}",
                f"- Admission rule: {admission_rule}",
                f"- Exclusion reporting: {exclusion_reporting}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_dir / "universe_exclusions.csv").write_text(
        "symbol,reason\n",
        encoding="utf-8",
    )
    (data_ready_dir / "universe_exclusions.md").write_text(
        "\n".join(
            [
                "# Universe Exclusions",
                "",
                "- No exclusions have been recorded in the first-wave skeleton yet.",
                f"- Reporting rule: {exclusion_reporting}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_dir / "data_ready_gate_decision.md").write_text(
        "\n".join(
            [
                "# Data Ready Gate Decision",
                "",
                "- Formal gate decision remains pending until review findings and review closure are written.",
                f"- Next consumer stage: {consumer_stage}",
                f"- Frozen inputs note: {frozen_inputs_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# Artifact Catalog",
                "",
                "- aligned_bars/",
                "- rolling_stats/",
                "- pair_stats/",
                "- benchmark_residual/",
                "- topic_basket_state/",
                "- qc_report.parquet",
                "- dataset_manifest.json",
                "- validation_report.md",
                "- data_contract.md",
                "- dedupe_rule.md",
                "- universe_summary.md",
                "- universe_exclusions.csv",
                "- universe_exclusions.md",
                "- data_ready_gate_decision.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# Field Dictionary",
                "",
                f"- `data_source`: frozen upstream source, currently `{data_source}`.",
                f"- `primary_time_key`: frozen dense grid key, currently `{primary_time_key}`.",
                f"- `bar_size`: frozen cadence inherited into data_ready, currently `{bar_size}`.",
                f"- `missing_policy`: {missing_policy}",
                f"- `stale_policy`: {stale_policy}",
                f"- `bad_price_policy`: {bad_price_policy}",
                f"- `outlier_policy`: {outlier_policy}",
                f"- `benchmark_symbol`: {benchmark_symbol}",
                f"- `shared_outputs`: {shared_outputs}",
                f"- `frozen_inputs_note`: {frozen_inputs_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return data_ready_dir


def _require_confirmed_freeze_groups(data_ready_dir: Path) -> dict[str, Any]:
    draft_path = data_ready_dir / DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        raise ValueError(f"{DATA_READY_FREEZE_DRAFT_FILE} is required before data_ready build")

    draft_payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = draft_payload.get("groups", {})
    missing_groups = [
        name for name in DATA_READY_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))
    ]
    if missing_groups:
        raise ValueError(
            f"{DATA_READY_FREEZE_DRAFT_FILE} has unconfirmed groups: {', '.join(missing_groups)}"
        )
    return groups


def _required_draft_value(group_payload: dict[str, Any], key: str) -> str:
    value = group_payload.get(key, "")
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"confirmed data_ready inputs missing: {key}")
    return normalized


def _string_list(raw_value: Any) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    return [str(item) for item in raw_value if str(item).strip()]
