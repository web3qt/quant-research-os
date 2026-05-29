from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.lineage_program_runtime import stage_program_dir


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
    if expected_route is None or route != expected_route:
        return DataImplementationValidationResult(
            stage_id=stage_id,
            program_dir=None,
            status="not_applicable",
            errors=[],
            reason_codes=[],
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
        status="valid" if not findings else "invalid",
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
            findings.append(
                (
                    "DATA_IMPL_ENGINE_NOT_POLARS",
                    f"{stage_id}: data_implementation_contract.engine must be polars",
                )
            )
            continue
        findings.append(
            (
                "DATA_IMPL_DECLARATION_MISSING",
                f"{stage_id}: data_implementation_contract.{key} must be {expected!r}",
            )
        )
    return findings


def _scan_program_python_files(program_dir: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    scan_literal_paths: list[tuple[Path, str]] = []
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
        scan_literal_paths.extend((path, literal_path) for literal_path in scanner.scan_literal_paths)

    # stage program 是一个整体；重复 literal scan 即使分散在 helper 里也要拦截。
    literal_counts = Counter(literal_path for _, literal_path in scan_literal_paths)
    repeated_paths = {literal_path for literal_path, count in literal_counts.items() if count > 1}
    for path, literal_path in scan_literal_paths:
        if literal_path not in repeated_paths:
            continue
        findings.append(
            (
                "DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN",
                f"{path}: repeated full scan/read of {literal_path!r} is forbidden without shared intermediate",
            )
        )
    return findings


class _ProgramScanner(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[tuple[str, str]] = []
        self.scan_literal_paths: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "pandas" or alias.name.startswith("pandas."):
                self.findings.append(("DATA_IMPL_ENGINE_FORBIDDEN_PANDAS", f"{self.path}: pandas import is forbidden"))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "pandas" or (node.module is not None and node.module.startswith("pandas.")):
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
