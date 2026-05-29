# Data Implementation Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a hard `data_implementation_contract` gate for `csf_data_ready` and `tss_data_ready` stage programs so active data-ready builds use Polars/parquet/lazy/vectorized implementation patterns and fail before review when slow pandas or row-wise main paths appear.

**Architecture:** Add a machine-readable contract under `contracts/stages/`, then implement a focused runtime validator that reads the lineage-local stage program declaration and scans Python AST patterns in `run_stage.py` plus helpers. Wire the validator into `qros-validate-stage` and review-entry preflight for only `csf_data_ready` and `tss_data_ready`; update active author skills and tests so the rule is discoverable and regression-checked.

**Tech Stack:** Python stdlib `ast`, `dataclasses`, `pathlib`, PyYAML, pytest, existing QROS `stage_program_scaffold`, `review_preflight`, and `validate_stage_artifacts` runtime paths.

---

## File Structure

- Create `contracts/stages/data_implementation_contract.yaml`
  - Machine-readable truth for applicable stages, required declaration shape, forbidden patterns, allowed exception scopes, and reason codes.
- Create `runtime/tools/data_implementation_contract_runtime.py`
  - Single-purpose validator for data-ready implementation discipline. It should not validate artifact shape or research semantics.
- Create `tests/contracts/test_data_implementation_contract.py`
  - Contract shape tests.
- Create `tests/runtime/test_data_implementation_contract_runtime.py`
  - Unit tests for declaration checks and AST pattern detection.
- Modify `runtime/scripts/validate_stage_artifacts.py`
  - Run the data implementation validator after artifact validation for applicable stages.
- Modify `runtime/tools/review_skillgen/review_preflight.py`
  - Add implementation findings to `content_findings` before review can pass.
- Modify `tests/runtime/test_validate_stage_artifacts_script.py`
  - Cover qros validate-stage failure when a data-ready program violates the contract.
- Modify `tests/review/test_review_preflight_csf_data_ready_contract.py`
  - Add CSF review-entry blocking coverage.
- Modify `tests/review/test_review_preflight_tss_data_ready_contract.py`
  - Add TSS review-entry blocking coverage.
- Modify `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
  - Document the hard gate and default implementation discipline.
- Modify `skills/tss_data_ready/qros-tss-data-ready-author/SKILL.md`
  - Same for TSS.
- Modify `tests/skills/test_csf_data_ready_contract_first_guidance.py`
  - Lock the CSF skill language.
- Modify `tests/skills/test_tss_data_ready_contract_first_guidance.py` and `tests/helpers/tss_stage_parity.py`
  - Lock TSS skill language.
- Optional doc update if implementation uncovers a user-facing gap:
  - `docs/guides/qros-research-session-usage.md`

## Task 1: Add The Contract Truth Layer

**Files:**
- Create: `contracts/stages/data_implementation_contract.yaml`
- Create: `tests/contracts/test_data_implementation_contract.py`

- [ ] **Step 1: Write the failing contract tests**

Create `tests/contracts/test_data_implementation_contract.py`:

```python
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
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
python -m pytest tests/contracts/test_data_implementation_contract.py -q
```

Expected:

```text
FAILED ... contracts/stages/data_implementation_contract.yaml
```

- [ ] **Step 3: Add the contract file**

Create `contracts/stages/data_implementation_contract.yaml`:

```yaml
schema_id: data-implementation-contract-v1
schema_version: v1
contract_role: data_ready_stage_program_implementation_gate
applicable_stages:
  - csf_data_ready
  - tss_data_ready
legacy_stages_excluded:
  - data_ready

required_declaration:
  engine: polars
  input_strategy: parquet_lazy_scan
  compute_strategy: expression_vectorized
  output_strategy: parquet_columnar
  disallowed_main_path:
    - pandas
    - row_wise_loop
    - per_symbol_full_scan_loop
    - repeated_full_scan_without_shared_intermediate

forbidden_patterns:
  imports:
    - pandas
  calls:
    - to_pandas
    - iterrows
    - itertuples
  apply_axis:
    - 1
  loop_targets:
    - asset
    - assets
    - symbol
    - symbols
  full_scan_calls:
    - scan_parquet
    - read_parquet
    - scan_csv
    - read_csv

allowed_exceptions:
  - metadata_report_conversion
  - manifest_writing
  - field_dictionary_writing
  - artifact_catalog_writing
  - test_fixture
  - docs_archive_migration

reason_codes:
  - code: DATA_IMPL_DECLARATION_MISSING
    meaning: 适用 stage 的 stage_program.yaml 缺少 data_implementation_contract 声明。
  - code: DATA_IMPL_ENGINE_NOT_POLARS
    meaning: 适用 stage 未声明 Polars 作为主数据引擎。
  - code: DATA_IMPL_ENGINE_FORBIDDEN_PANDAS
    meaning: 适用 stage program 主路径导入 pandas。
  - code: DATA_IMPL_TO_PANDAS_FORBIDDEN
    meaning: 适用 stage program 主路径调用 to_pandas。
  - code: DATA_IMPL_ROW_LOOP_FORBIDDEN
    meaning: 适用 stage program 主路径使用逐行迭代。
  - code: DATA_IMPL_APPLY_AXIS1_FORBIDDEN
    meaning: 适用 stage program 主路径使用 DataFrame.apply(axis=1)。
  - code: DATA_IMPL_PER_ASSET_FULL_SCAN_FORBIDDEN
    meaning: 适用 stage program 对 asset 或 symbol 循环执行全量 scan/read。
  - code: DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN
    meaning: 适用 stage program 对同一输入重复全量 scan/read，且未声明共享中间层。
  - code: DATA_IMPL_CONTRACT_STAGE_NOT_APPLICABLE
    meaning: 请求校验的 stage 不属于 active data-ready 路线。
```

- [ ] **Step 4: Run the tests and verify GREEN**

Run:

```bash
python -m pytest tests/contracts/test_data_implementation_contract.py -q
```

Expected:

```text
4 passed
```

- [ ] **Step 5: Commit**

```bash
git add contracts/stages/data_implementation_contract.yaml tests/contracts/test_data_implementation_contract.py
git commit -m "feat: add data implementation contract"
```

## Task 2: Implement The Runtime Validator

**Files:**
- Create: `runtime/tools/data_implementation_contract_runtime.py`
- Create: `tests/runtime/test_data_implementation_contract_runtime.py`

- [ ] **Step 1: Write validator tests**

Create `tests/runtime/test_data_implementation_contract_runtime.py`:

```python
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


def test_legacy_data_ready_is_not_applicable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "legacy_case"

    result = validate_data_implementation_contract(lineage_root, "data_ready", "time_series_signal")

    assert result.valid is True
    assert result.reason_codes == []
    assert result.status == "not_applicable"
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/runtime/test_data_implementation_contract_runtime.py -q
```

Expected:

```text
FAILED ... ModuleNotFoundError: No module named 'runtime.tools.data_implementation_contract_runtime'
```

- [ ] **Step 3: Implement the validator**

Create `runtime/tools/data_implementation_contract_runtime.py`:

```python
from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.lineage_program_runtime import stage_program_dir


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "contracts" / "stages" / "data_implementation_contract.yaml"
APPLICABLE_STAGE_ROUTES = {
    "csf_data_ready": "cross_sectional_factor",
    "tss_data_ready": "time_series_signal",
}
REQUIRED_DECLARATION = {
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
FULL_SCAN_CALLS = {"scan_parquet", "read_parquet", "scan_csv", "read_csv"}
ROW_LOOP_CALLS = {"iterrows", "itertuples"}
LOOP_TARGET_NAMES = {"asset", "assets", "symbol", "symbols"}


@dataclass(frozen=True)
class DataImplementationValidationResult:
    stage_id: str
    program_dir: Path | None
    status: str
    errors: list[str]
    reason_codes: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_data_implementation_contract(
    lineage_root: Path,
    stage_id: str,
    route: str,
) -> DataImplementationValidationResult:
    expected_route = APPLICABLE_STAGE_ROUTES.get(stage_id)
    if expected_route is None:
        return DataImplementationValidationResult(
            stage_id=stage_id,
            program_dir=None,
            status="not_applicable",
            errors=[],
            reason_codes=[],
        )
    if route != expected_route:
        return _result(
            stage_id,
            None,
            [("DATA_IMPL_CONTRACT_STAGE_NOT_APPLICABLE", f"{stage_id}: expected route {expected_route}, found {route}")],
        )

    program_dir = stage_program_dir(lineage_root, stage_id, route)
    manifest_path = program_dir / "stage_program.yaml"
    if not manifest_path.exists():
        return _result(
            stage_id,
            program_dir,
            [("DATA_IMPL_DECLARATION_MISSING", f"{stage_id}: stage_program.yaml is missing")],
        )

    manifest = _load_yaml_map(manifest_path)
    findings: list[tuple[str, str]] = []
    findings.extend(_validate_declaration(stage_id, manifest.get("data_implementation_contract")))
    findings.extend(_scan_program_python_files(program_dir))
    return _result(stage_id, program_dir, findings)


def _result(
    stage_id: str,
    program_dir: Path | None,
    findings: list[tuple[str, str]],
) -> DataImplementationValidationResult:
    return DataImplementationValidationResult(
        stage_id=stage_id,
        program_dir=program_dir,
        status="PASS" if not findings else "FAIL",
        errors=[message for _, message in findings],
        reason_codes=_dedupe([code for code, _ in findings]),
    )


def _dedupe(values: list[str]) -> list[str]:
    observed: list[str] = []
    for value in values:
        if value not in observed:
            observed.append(value)
    return observed


def _load_yaml_map(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _validate_declaration(stage_id: str, declaration: Any) -> list[tuple[str, str]]:
    if not isinstance(declaration, dict):
        return [("DATA_IMPL_DECLARATION_MISSING", f"{stage_id}: missing data_implementation_contract declaration")]

    findings: list[tuple[str, str]] = []
    for key, expected in REQUIRED_DECLARATION.items():
        observed = declaration.get(key)
        if observed == expected:
            continue
        if key == "engine":
            findings.append(("DATA_IMPL_ENGINE_NOT_POLARS", f"{stage_id}: data_implementation_contract.engine must be polars"))
        else:
            findings.append(
                (
                    "DATA_IMPL_DECLARATION_MISSING",
                    f"{stage_id}: data_implementation_contract.{key} must be {expected!r}",
                )
            )
    return findings


def _scan_program_python_files(program_dir: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in sorted(program_dir.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            findings.append(("DATA_IMPL_DECLARATION_MISSING", f"{path}: Python parse failed: {exc.msg}"))
            continue
        scanner = _ProgramScanner(path)
        scanner.visit(tree)
        findings.extend(scanner.findings)
    return findings


class _ProgramScanner(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[tuple[str, str]] = []
        self.scan_literal_paths: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "pandas":
                self.findings.append(("DATA_IMPL_ENGINE_FORBIDDEN_PANDAS", f"{self.path}: pandas import is forbidden"))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "pandas":
            self.findings.append(("DATA_IMPL_ENGINE_FORBIDDEN_PANDAS", f"{self.path}: pandas import is forbidden"))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        call_name = _call_name(node.func)
        if call_name == "to_pandas":
            self.findings.append(("DATA_IMPL_TO_PANDAS_FORBIDDEN", f"{self.path}: to_pandas is forbidden"))
        if call_name in ROW_LOOP_CALLS:
            self.findings.append(("DATA_IMPL_ROW_LOOP_FORBIDDEN", f"{self.path}: {call_name} is forbidden"))
        if call_name == "apply" and _call_has_axis_one(node):
            self.findings.append(("DATA_IMPL_APPLY_AXIS1_FORBIDDEN", f"{self.path}: apply(axis=1) is forbidden"))
        if call_name in FULL_SCAN_CALLS:
            literal_path = _first_literal_arg(node)
            if literal_path is not None:
                self.scan_literal_paths.append(literal_path)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        target_names = _target_names(node.target)
        if target_names & LOOP_TARGET_NAMES and _loop_body_has_full_scan(node):
            self.findings.append(
                (
                    "DATA_IMPL_PER_ASSET_FULL_SCAN_FORBIDDEN",
                    f"{self.path}: per-asset or per-symbol full scan loop is forbidden",
                )
            )
        self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> None:
        self.generic_visit(node)
        repeated = [path for path, count in Counter(self.scan_literal_paths).items() if count > 1]
        for path in repeated:
            self.findings.append(
                (
                    "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN",
                    f"{self.path}: repeated full scan/read of {path!r} is forbidden without shared intermediate",
                )
            )


def _call_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _call_has_axis_one(node: ast.Call) -> bool:
    for keyword in node.keywords:
        if keyword.arg == "axis" and isinstance(keyword.value, ast.Constant) and keyword.value.value == 1:
            return True
    return False


def _first_literal_arg(node: ast.Call) -> str | None:
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _target_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for item in target.elts:
            names.update(_target_names(item))
        return names
    return set()


def _loop_body_has_full_scan(node: ast.For) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and _call_name(child.func) in FULL_SCAN_CALLS:
            return True
    return False
```

- [ ] **Step 4: Run validator tests and verify GREEN**

Run:

```bash
python -m pytest tests/runtime/test_data_implementation_contract_runtime.py -q
```

Expected:

```text
8 passed
```

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/data_implementation_contract_runtime.py tests/runtime/test_data_implementation_contract_runtime.py
git commit -m "feat: validate data-ready implementation contract"
```

## Task 3: Wire The Gate Into Validate-Stage And Review Preflight

**Files:**
- Modify: `runtime/scripts/validate_stage_artifacts.py`
- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Modify: `tests/runtime/test_validate_stage_artifacts_script.py`
- Modify: `tests/review/test_review_preflight_csf_data_ready_contract.py`
- Modify: `tests/review/test_review_preflight_tss_data_ready_contract.py`

- [ ] **Step 1: Add failing validate-stage script coverage**

Append to `tests/runtime/test_validate_stage_artifacts_script.py`:

```python
def test_validate_stage_artifacts_blocks_csf_data_ready_pandas_program(tmp_path: Path) -> None:
    from tests.review.test_review_preflight_csf_data_ready_contract import _prepare_valid_csf_data_ready_stage

    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)
    program_dir = stage_dir.parent / "program" / "cross_sectional_factor" / "data_ready"
    manifest_path = program_dir / "stage_program.yaml"
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    payload["data_implementation_contract"] = {
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
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    (program_dir / "run_stage.py").write_text("import pandas as pd\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "runtime" / "scripts" / "validate_stage_artifacts.py"),
            "--outputs-root",
            str(tmp_path / "outputs"),
            "--lineage-id",
            stage_dir.parent.name,
            "--stage",
            "csf_data_ready",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "DATA_IMPL_ENGINE_FORBIDDEN_PANDAS" in result.stderr
```

If the file uses different helper names for `REPO_ROOT`, `subprocess`, or `sys`, import them at the top:

```python
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
```

- [ ] **Step 2: Add failing review preflight tests**

Append to `tests/review/test_review_preflight_csf_data_ready_contract.py`:

```python
def _add_valid_data_implementation_declaration(program_dir: Path) -> None:
    manifest_path = program_dir / "stage_program.yaml"
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    payload["data_implementation_contract"] = {
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
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_review_preflight_blocks_csf_data_ready_when_data_implementation_contract_fails(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_data_ready_stage(tmp_path)
    program_dir = stage_dir.parent / "program" / "cross_sectional_factor" / "data_ready"
    _add_valid_data_implementation_declaration(program_dir)
    (program_dir / "run_stage.py").write_text("import pandas as pd\n", encoding="utf-8")

    payload = _run_csf_data_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("DATA_IMPL_ENGINE_FORBIDDEN_PANDAS" in item for item in payload["content_findings"])
```

Append to `tests/review/test_review_preflight_tss_data_ready_contract.py`:

```python
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program


def test_review_preflight_blocks_tss_data_ready_when_data_implementation_declaration_missing(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    ensure_stage_program(lineage_root, "tss_data_ready")
    stage_dir = lineage_root / "02_tss_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)

    payload = run_review_preflight(
        explicit_context={
            "stage": "tss_data_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(lineage_root),
            "author_formal_dir": str(formal_dir),
            "lineage_id": lineage_root.name,
        }
    )

    assert payload["status"] == "FAIL"
    assert any("DATA_IMPL_DECLARATION_MISSING" in item for item in payload["content_findings"])
```

- [ ] **Step 3: Run targeted tests and verify RED**

Run:

```bash
python -m pytest tests/runtime/test_validate_stage_artifacts_script.py tests/review/test_review_preflight_csf_data_ready_contract.py tests/review/test_review_preflight_tss_data_ready_contract.py -q
```

Expected:

```text
FAILED ... DATA_IMPL...
```

- [ ] **Step 4: Wire the validator into `validate_stage_artifacts.py`**

Modify `runtime/scripts/validate_stage_artifacts.py`:

```python
from runtime.tools.data_implementation_contract_runtime import (  # noqa: E402
    validate_data_implementation_contract,
)
```

Add near the top:

```python
DATA_IMPLEMENTATION_ROUTES = {
    "csf_data_ready": "cross_sectional_factor",
    "tss_data_ready": "time_series_signal",
}
```

In `main()`, after artifact shape validation succeeds and before printing success:

```python
    route = DATA_IMPLEMENTATION_ROUTES.get(args.stage)
    if route is not None:
        lineage_root = args.outputs_root / args.lineage_id
        impl_result = validate_data_implementation_contract(lineage_root, args.stage, route)
        if not impl_result.valid:
            for code, error in zip(impl_result.reason_codes, impl_result.errors, strict=False):
                print(f"{code}: {error}", file=sys.stderr)
            return 1
```

If Python compatibility complains about `strict=False`, replace the loop with:

```python
            for error in impl_result.errors:
                print(error, file=sys.stderr)
```

- [ ] **Step 5: Wire the validator into `review_preflight.py`**

Modify imports in `runtime/tools/review_skillgen/review_preflight.py`:

```python
from runtime.tools.data_implementation_contract_runtime import validate_data_implementation_contract
```

Add helper near `_validate_stage_program_for_review`:

```python
def _check_data_implementation_contract(stage: str, lineage_root: Path) -> list[str]:
    routes = {
        "csf_data_ready": "cross_sectional_factor",
        "tss_data_ready": "time_series_signal",
    }
    route = routes.get(stage)
    if route is None:
        return []
    result = validate_data_implementation_contract(lineage_root, stage, route)
    return [
        f"{code}: {error}"
        for code, error in zip(result.reason_codes, result.errors, strict=False)
    ]
```

In `run_review_preflight()`, immediately after `_validate_stage_program_for_review`:

```python
    content_findings.extend(_check_data_implementation_contract(stage, lineage_root))
```

- [ ] **Step 6: Run targeted tests and verify GREEN**

Run:

```bash
python -m pytest tests/runtime/test_validate_stage_artifacts_script.py tests/review/test_review_preflight_csf_data_ready_contract.py tests/review/test_review_preflight_tss_data_ready_contract.py -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 7: Commit**

```bash
git add runtime/scripts/validate_stage_artifacts.py runtime/tools/review_skillgen/review_preflight.py tests/runtime/test_validate_stage_artifacts_script.py tests/review/test_review_preflight_csf_data_ready_contract.py tests/review/test_review_preflight_tss_data_ready_contract.py
git commit -m "feat: gate data-ready implementation before review"
```

## Task 4: Update Active Author Skill Guidance

**Files:**
- Modify: `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
- Modify: `skills/tss_data_ready/qros-tss-data-ready-author/SKILL.md`
- Modify: `tests/skills/test_csf_data_ready_contract_first_guidance.py`
- Modify: `tests/skills/test_tss_data_ready_contract_first_guidance.py`
- Modify: `tests/helpers/tss_stage_parity.py`

- [ ] **Step 1: Add failing skill tests**

Modify `tests/skills/test_csf_data_ready_contract_first_guidance.py`:

```python
def test_csf_data_ready_author_skill_requires_data_implementation_contract_gate() -> None:
    content = skill_text("qros-csf-data-ready-author")

    assert "data_implementation_contract" in content
    assert "Polars" in content
    assert "pl.scan_parquet" in content
    assert "pandas" in content
    assert "逐行循环" in content
    assert "逐 symbol" in content
    assert "不得询问用户技术实现细节" in content
```

Modify `tests/helpers/tss_stage_parity.py` inside `assert_tss_skill_guidance_is_contract_first` for `stage == "tss_data_ready"`:

```python
    if stage == "tss_data_ready":
        assert "data_implementation_contract" in author
        assert "Polars" in author
        assert "pl.scan_parquet" in author
        assert "pandas" in author
        assert "逐行循环" in author
        assert "逐 symbol" in author
        assert "不得询问用户技术实现细节" in author
```

No direct change is needed in `tests/skills/test_tss_data_ready_contract_first_guidance.py`; it already calls the shared parity helper.

- [ ] **Step 2: Run skill tests and verify RED**

Run:

```bash
python -m pytest tests/skills/test_csf_data_ready_contract_first_guidance.py tests/skills/test_tss_data_ready_contract_first_guidance.py -q
```

Expected:

```text
FAILED ... data_implementation_contract
```

- [ ] **Step 3: Update CSF author skill**

In `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`, add under `## Mandatory Discipline`:

```markdown
- 必须通过 `data_implementation_contract` 硬门禁后才允许 build/review；该门禁只约束实现纪律，不替代 artifact contract、semantic validation 或 upstream binding validation。
- 本阶段 stage program 的主数据引擎必须使用 Polars；大表 parquet 输入默认使用 `pl.scan_parquet` 或等价 lazy scan，聚合、排序、去重、join、窗口和过滤必须优先使用 Polars expression / lazy pipeline。
- 不得询问用户技术实现细节来决定是否使用 Polars、parquet-first、lazy scan 或表达式化计算；这些是 QROS 默认实现纪律。
- stage program 主路径不得使用 pandas、`.to_pandas()`、`.iterrows()`、`.itertuples()`、`DataFrame.apply(..., axis=1)`、逐行循环、逐 symbol 全量 scan/read/write，或重复全量 scan 同一大输入来分别生成多个 formal outputs。
- Python loop 只能用于 manifest、artifact catalog、field dictionary、输出文件枚举和小型 metadata/report 控制流，不能承担面板主路径计算。
```

In `## Working Rules`, insert before `运行 qros-validate-stage`:

```markdown
14. 确认 lineage-local stage program 的 `stage_program.yaml` 已声明 `data_implementation_contract`，并运行实现门禁；门禁不通过时停在 author lane 修复程序，不得进入 review
```

Renumber following items if the surrounding list is numbered manually.

- [ ] **Step 4: Update TSS author skill**

In `skills/tss_data_ready/qros-tss-data-ready-author/SKILL.md`, add under `## Mandatory Discipline`:

```markdown
- 必须通过 `data_implementation_contract` 硬门禁后才允许 build/review；该门禁只约束实现纪律，不替代 artifact contract 或 TSS semantic validation。
- 本阶段 stage program 的主数据引擎必须使用 Polars；大表 parquet 输入默认使用 `pl.scan_parquet` 或等价 lazy scan，时间轴构建、质量标记、split adequacy 和 as-of 特征基础层必须优先使用 Polars expression / lazy pipeline。
- 不得询问用户技术实现细节来决定是否使用 Polars、parquet-first、lazy scan 或表达式化计算；这些是 QROS 默认实现纪律。
- stage program 主路径不得使用 pandas、`.to_pandas()`、`.iterrows()`、`.itertuples()`、`DataFrame.apply(..., axis=1)`、逐行循环、逐 symbol 全量 scan/read/write，或重复全量 scan 同一大输入来分别生成多个 formal outputs。
- Python loop 只能用于 manifest、artifact catalog、field dictionary、输出文件枚举和小型 metadata/report 控制流，不能承担时间轴主路径计算。
```

In `## Working Rules`, insert before `运行 qros-validate-stage`:

```markdown
7. 确认 lineage-local stage program 的 `stage_program.yaml` 已声明 `data_implementation_contract`，并运行实现门禁；门禁不通过时停在 author lane 修复程序，不得进入 review
```

Renumber following items.

- [ ] **Step 5: Run skill tests and verify GREEN**

Run:

```bash
python -m pytest tests/skills/test_csf_data_ready_contract_first_guidance.py tests/skills/test_tss_data_ready_contract_first_guidance.py -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 6: Commit**

```bash
git add skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md skills/tss_data_ready/qros-tss-data-ready-author/SKILL.md tests/skills/test_csf_data_ready_contract_first_guidance.py tests/skills/test_tss_data_ready_contract_first_guidance.py tests/helpers/tss_stage_parity.py
git commit -m "docs: require data implementation gate in author skills"
```

## Task 5: Final Verification And Regression Sweep

**Files:**
- No required source changes.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest \
  tests/contracts/test_data_implementation_contract.py \
  tests/runtime/test_data_implementation_contract_runtime.py \
  tests/runtime/test_validate_stage_artifacts_script.py \
  tests/review/test_review_preflight_csf_data_ready_contract.py \
  tests/review/test_review_preflight_tss_data_ready_contract.py \
  tests/skills/test_csf_data_ready_contract_first_guidance.py \
  tests/skills/test_tss_data_ready_contract_first_guidance.py \
  -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 2: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected:

```text
smoke tier passes
```

- [ ] **Step 3: Run full-smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected:

```text
full-smoke tier passes
```

- [ ] **Step 4: Inspect final diff**

Run:

```bash
git status --short
git diff --stat
```

Expected:

```text
Only data implementation contract, validator, wiring, tests, and skill guidance files are modified.
```

- [ ] **Step 5: Commit final verification note if any tracked docs changed**

If no additional files changed during verification, do not create a commit. If implementation required a user-facing docs update such as `docs/guides/qros-research-session-usage.md`, commit it:

```bash
git add docs/guides/qros-research-session-usage.md
git commit -m "docs: describe data implementation gate"
```

## Self-Review

- Spec coverage: The plan covers the contract truth layer, stage program declaration, runtime validator, hard fail rules, allowed exceptions, validate-stage integration, review preflight integration, author skill guidance, focused tests, smoke, and full-smoke.
- Scope: The plan explicitly targets only `csf_data_ready` and `tss_data_ready`; legacy `data_ready` is excluded and has a not-applicable test.
- Type consistency: The runtime API is consistently named `validate_data_implementation_contract(lineage_root, stage_id, route)` and returns `DataImplementationValidationResult` with `valid`, `errors`, `reason_codes`, and `status`.
- Placeholder scan: No task depends on undefined placeholder work; every code-changing step includes concrete code or exact insertion text.

