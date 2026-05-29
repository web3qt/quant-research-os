from __future__ import annotations

from pathlib import Path

import yaml

from runtime.tools.data_implementation_contract_runtime import (
    validate_data_implementation_contract,
)


def _write_program(lineage_root: Path, stage: str, source: str, declaration: dict | None) -> Path:
    if stage == "csf_data_ready":
        program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
        route = "cross_sectional_factor"
    elif stage == "tss_data_ready":
        program_dir = lineage_root / "program" / "time_series_signal" / "tss_data_ready"
        route = "time_series_signal"
    else:
        raise AssertionError(stage)

    program_dir.mkdir(parents=True)
    (program_dir / "README.md").write_text("# Data Ready Program\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(source, encoding="utf-8")
    manifest = {
        "stage_id": stage,
        "route": route,
        "lineage_id": lineage_root.name,
        "entrypoint": "run_stage.py",
        "entry_type": "python",
        "inputs": [],
        "outputs": [],
        "depends_on_programs": ["mandate"],
        "shared_libs": [],
        "authored_by": {
            "agent_id": "test-agent",
            "agent_role": "executor",
            "session_id": "test-session",
        },
    }
    if declaration is not None:
        manifest["data_implementation_contract"] = declaration
    (program_dir / "stage_program.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return program_dir


def _valid_declaration() -> dict:
    return {
        "engine": "polars",
        "input_strategy": "parquet_lazy_scan",
        "compute_strategy": "expression_vectorized",
        "output_strategy": "parquet_columnar",
        "disallowed_main_path": [
            "pandas",
            "row_wise_loop",
            "per_symbol_full_scan_loop",
            "repeated_full_scan_without_shared_intermediate",
        ],
    }


def test_polars_lazy_vectorized_program_passes(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
from __future__ import annotations

import polars as pl


def main() -> None:
    # 使用 lazy parquet scan 生成横截面覆盖表。
    frame = (
        pl.scan_parquet("raw/panel/*.parquet")
        .filter(pl.col("is_tradable"))
        .group_by("date")
        .agg(
            pl.col("asset").n_unique().alias("asset_count"),
            pl.len().alias("row_count"),
        )
    )
    frame.sink_parquet("02_csf_data_ready/author/formal/cross_section_coverage.parquet")
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert result.valid is True
    assert result.errors == []


def test_missing_declaration_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(lineage_root, "csf_data_ready", "import polars as pl\n", None)

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert result.valid is False
    assert result.reason_codes == ["DATA_IMPL_DECLARATION_MISSING"]


def test_missing_stage_program_yaml_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True)
    (program_dir / "run_stage.py").write_text("import polars as pl\n", encoding="utf-8")

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert result.valid is False
    assert result.reason_codes == ["DATA_IMPL_DECLARATION_MISSING"]


def test_wrong_engine_declaration_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    declaration = _valid_declaration()
    declaration["engine"] = "pandas"
    _write_program(lineage_root, "csf_data_ready", "import polars as pl\n", declaration)

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_ENGINE_NOT_POLARS" in result.reason_codes


def test_wrong_strategy_or_disallowed_main_path_declaration_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    declaration = _valid_declaration()
    declaration["input_strategy"] = "parquet_eager_read"
    declaration["disallowed_main_path"] = ["pandas"]
    _write_program(lineage_root, "tss_data_ready", "import polars as pl\n", declaration)

    result = validate_data_implementation_contract(lineage_root, "tss_data_ready", "time_series_signal")

    assert "DATA_IMPL_DECLARATION_MISSING" in result.reason_codes


def test_pandas_import_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(lineage_root, "csf_data_ready", "import pandas as pd\n", _valid_declaration())

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_ENGINE_FORBIDDEN_PANDAS" in result.reason_codes


def test_to_pandas_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _write_program(
        lineage_root,
        "tss_data_ready",
        '''
import polars as pl


def main() -> None:
    # 小心：这里把全量 lazy result 转 pandas，必须被挡住。
    pl.scan_parquet("raw/*.parquet").collect().to_pandas()
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "tss_data_ready", "time_series_signal")

    assert "DATA_IMPL_TO_PANDAS_FORBIDDEN" in result.reason_codes


def test_row_iteration_and_apply_axis_one_fail(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _write_program(
        lineage_root,
        "tss_data_ready",
        '''
def main(df):
    for row in df.iterrows():
        print(row)
    for row in df.itertuples():
        print(row)
    df.apply(lambda row: row["x"] + 1, axis=1)
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "tss_data_ready", "time_series_signal")

    assert "DATA_IMPL_ROW_LOOP_FORBIDDEN" in result.reason_codes
    assert "DATA_IMPL_APPLY_AXIS1_FORBIDDEN" in result.reason_codes


def test_per_symbol_full_scan_loop_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
import polars as pl


def main(symbols):
    for symbol in symbols:
        # 逐 symbol 全量 scan 会在大 universe 下退化。
        pl.scan_parquet(f"raw/{symbol}.parquet").collect().write_parquet(f"out/{symbol}.parquet")
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_PER_ASSET_FULL_SCAN_FORBIDDEN" in result.reason_codes


def test_polars_full_scan_alias_in_symbol_loop_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
import polars as pl

scan = pl.scan_parquet


def main(symbols):
    for symbol in symbols:
        scan("raw/panel.parquet").filter(pl.col("asset") == symbol).collect()
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_PER_ASSET_FULL_SCAN_FORBIDDEN" in result.reason_codes


def test_repeated_literal_full_scan_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
import polars as pl


def main():
    pl.scan_parquet("raw/panel.parquet").select("asset").collect()
    pl.scan_parquet("raw/panel.parquet").select("date").collect()
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN" in result.reason_codes


def test_imported_polars_scan_alias_repeated_literal_full_scan_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
from polars import scan_parquet

reader = scan_parquet


def main():
    reader("raw/panel.parquet").select("asset").collect()
    reader("raw/panel.parquet").select("date").collect()
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN" in result.reason_codes


def test_local_scan_parquet_helper_does_not_trigger_repeated_full_scan(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
def scan_parquet(path):
    return path


def main():
    scan_parquet("raw/panel.parquet")
    scan_parquet("raw/panel.parquet")
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN" not in result.reason_codes


def test_local_function_shadows_imported_polars_scan(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
from polars import scan_parquet


def scan_parquet(path):
    return path


def main():
    scan_parquet("raw/panel.parquet")
    scan_parquet("raw/panel.parquet")
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN" not in result.reason_codes


def test_local_function_shadows_polars_scan_alias(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
import polars as pl

scan = pl.scan_parquet


def scan(path):
    return path


def main():
    scan("raw/panel.parquet")
    scan("raw/panel.parquet")
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN" not in result.reason_codes


def test_non_polars_reassignment_shadows_polars_scan_alias(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _write_program(
        lineage_root,
        "csf_data_ready",
        '''
import polars as pl


def local_helper(path):
    return path


scan = pl.scan_parquet
scan = local_helper


def main():
    scan("raw/panel.parquet")
    scan("raw/panel.parquet")
''',
        _valid_declaration(),
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN" not in result.reason_codes


def test_repeated_literal_full_scan_across_program_files_fails(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    program_dir = _write_program(
        lineage_root,
        "csf_data_ready",
        '''
import polars as pl


def main():
    pl.scan_parquet("raw/panel.parquet").select("asset").collect()
''',
        _valid_declaration(),
    )
    (program_dir / "helper.py").write_text(
        '''
import polars as pl


def helper():
    pl.scan_parquet("raw/panel.parquet").select("date").collect()
''',
        encoding="utf-8",
    )

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN" in result.reason_codes


def test_legacy_data_ready_is_not_applicable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "legacy_case"

    result = validate_data_implementation_contract(lineage_root, "data_ready", "time_series_signal")

    assert result.valid is True
    assert result.reason_codes == []
    assert result.status == "not_applicable"


def test_applicable_stage_with_non_matching_route_is_not_applicable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "route_case"

    result = validate_data_implementation_contract(lineage_root, "csf_data_ready", "time_series_signal")

    assert result.valid is True
    assert result.reason_codes == []
    assert result.errors == []
    assert result.status == "not_applicable"
