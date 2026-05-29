from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/stages/data_implementation_contract.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_data_implementation_contract_exists_and_targets_active_data_ready_stages() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["schema_id"] == "data-implementation-contract-v1"
    assert contract["schema_version"] == "v1"
    assert contract["contract_role"] == "data_ready_stage_program_implementation_gate"
    assert contract["applicable_stages"] == ["csf_data_ready", "tss_data_ready"]
    assert contract["legacy_stages_excluded"] == ["data_ready"]


def test_data_implementation_contract_requires_polars_and_columnar_io() -> None:
    contract = _load_contract()
    required = contract["required_declaration"]

    assert required["engine"] == "polars"
    assert required["input_strategy"] == "parquet_lazy_scan"
    assert required["compute_strategy"] == "expression_vectorized"
    assert required["output_strategy"] == "parquet_columnar"
    assert required["disallowed_main_path"] == [
        "pandas",
        "row_wise_loop",
        "per_symbol_full_scan_loop",
        "repeated_full_scan_without_shared_intermediate",
    ]


def test_data_implementation_contract_declares_forbidden_patterns_and_reason_codes() -> None:
    contract = _load_contract()
    patterns = contract["forbidden_patterns"]
    reason_codes = {item["code"] for item in contract["reason_codes"]}

    assert patterns["imports"] == ["pandas"]
    assert patterns["calls"] == ["to_pandas", "iterrows", "itertuples"]
    assert patterns["apply_axis"] == [1]
    assert patterns["loop_targets"] == ["asset", "assets", "symbol", "symbols"]
    assert patterns["full_scan_calls"] == ["scan_parquet", "read_parquet", "scan_csv", "read_csv"]

    assert {
        "DATA_IMPL_DECLARATION_MISSING",
        "DATA_IMPL_ENGINE_NOT_POLARS",
        "DATA_IMPL_ENGINE_FORBIDDEN_PANDAS",
        "DATA_IMPL_TO_PANDAS_FORBIDDEN",
        "DATA_IMPL_ROW_LOOP_FORBIDDEN",
        "DATA_IMPL_APPLY_AXIS1_FORBIDDEN",
        "DATA_IMPL_PER_ASSET_FULL_SCAN_FORBIDDEN",
        "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN",
        "DATA_IMPL_CONTRACT_STAGE_NOT_APPLICABLE",
    }.issubset(reason_codes)


def test_data_implementation_contract_allows_small_control_flow_exceptions() -> None:
    contract = _load_contract()
    exceptions = contract["allowed_exceptions"]

    assert "metadata_report_conversion" in exceptions
    assert "manifest_writing" in exceptions
    assert "field_dictionary_writing" in exceptions
    assert "artifact_catalog_writing" in exceptions
    assert "test_fixture" in exceptions
    assert "docs_archive_migration" in exceptions
