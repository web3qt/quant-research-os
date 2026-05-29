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
    findings: list[tuple[str, str]]
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
            findings=[],
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
        findings=findings,
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
        self.polars_module_alias_scopes: list[set[str]] = [set()]
        self.polars_scan_name_scopes: list[set[str]] = [set()]
        self.per_asset_loop_scan_stack: list[bool] = []

    @property
    def polars_module_aliases(self) -> set[str]:
        return self.polars_module_alias_scopes[-1]

    @property
    def polars_scan_names(self) -> set[str]:
        return self.polars_scan_name_scopes[-1]

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "pandas" or alias.name.startswith("pandas."):
                self.findings.append(("DATA_IMPL_ENGINE_FORBIDDEN_PANDAS", f"{self.path}: pandas import is forbidden"))
            if alias.name == "polars":
                self.polars_module_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "pandas" or (node.module is not None and node.module.startswith("pandas.")):
            self.findings.append(("DATA_IMPL_ENGINE_FORBIDDEN_PANDAS", f"{self.path}: pandas import is forbidden"))
        if node.module == "polars":
            for alias in node.names:
                if alias.name in FULL_SCAN_CALLS:
                    self.polars_scan_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        resolved = self._resolve_polars_scan_function(node.value)
        module_alias = self._resolve_polars_module_alias(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if resolved is not None:
                    self.polars_scan_names.add(target.id)
                else:
                    self.polars_scan_names.discard(target.id)
                if module_alias is not None:
                    self.polars_module_aliases.add(target.id)
                else:
                    self.polars_module_aliases.discard(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            resolved = self._resolve_polars_scan_function(node.value) if node.value is not None else None
            module_alias = self._resolve_polars_module_alias(node.value) if node.value is not None else None
            if resolved is not None:
                self.polars_scan_names.add(node.target.id)
            else:
                self.polars_scan_names.discard(node.target.id)
            if module_alias is not None:
                self.polars_module_aliases.add(node.target.id)
            else:
                self.polars_module_aliases.discard(node.target.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.polars_scan_names.discard(node.name)
        self.polars_module_aliases.discard(node.name)
        self._visit_nested_scope(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.polars_scan_names.discard(node.name)
        self.polars_module_aliases.discard(node.name)
        self._visit_nested_scope(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.polars_scan_names.discard(node.name)
        self.polars_module_aliases.discard(node.name)
        self._visit_nested_scope(node)

    def _visit_nested_scope(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
        self.polars_module_alias_scopes.append(set(self.polars_module_aliases))
        self.polars_scan_name_scopes.append(set(self.polars_scan_names))
        for decorator in node.decorator_list:
            self.visit(decorator)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults:
                self.visit(default)
            for default in node.args.kw_defaults:
                if default is not None:
                    self.visit(default)
            if node.returns is not None:
                self.visit(node.returns)
            for parameter_name in _argument_names(node.args):
                self.polars_scan_names.discard(parameter_name)
                self.polars_module_aliases.discard(parameter_name)
        else:
            for base in node.bases:
                self.visit(base)
            for keyword in node.keywords:
                self.visit(keyword)
        for stmt in node.body:
            self.visit(stmt)
        self.polars_scan_name_scopes.pop()
        self.polars_module_alias_scopes.pop()

    def visit_Call(self, node: ast.Call) -> None:
        call_name = _call_name(node.func)
        if call_name == "to_pandas":
            self.findings.append(("DATA_IMPL_TO_PANDAS_FORBIDDEN", f"{self.path}: to_pandas is forbidden"))
        if call_name in ROW_LOOP_CALLS:
            self.findings.append(("DATA_IMPL_ROW_LOOP_FORBIDDEN", f"{self.path}: {call_name} is forbidden"))
        if call_name == "apply" and _call_has_axis_one(node):
            self.findings.append(("DATA_IMPL_APPLY_AXIS1_FORBIDDEN", f"{self.path}: apply(axis=1) is forbidden"))
        if self._resolve_polars_scan_function(node.func) is not None:
            for index in range(len(self.per_asset_loop_scan_stack)):
                self.per_asset_loop_scan_stack[index] = True
            literal_path = _first_literal_arg(node)
            if literal_path is not None:
                self.scan_literal_paths.append(literal_path)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        target_names = _target_names(node.target)
        self.visit(node.iter)
        for name in target_names:
            self.polars_scan_names.discard(name)
            self.polars_module_aliases.discard(name)

        is_per_asset_loop = bool(target_names & LOOP_TARGET_NAMES)
        if is_per_asset_loop:
            self.per_asset_loop_scan_stack.append(False)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)
        loop_had_scan = self.per_asset_loop_scan_stack.pop() if is_per_asset_loop else False
        if loop_had_scan:
            self.findings.append(
                (
                    "DATA_IMPL_PER_ASSET_FULL_SCAN_FORBIDDEN",
                    f"{self.path}: per-asset or per-symbol full scan loop is forbidden",
                )
            )

    def visit_Module(self, node: ast.Module) -> None:
        self.generic_visit(node)

    def _resolve_polars_scan_function(self, func: ast.AST) -> str | None:
        if isinstance(func, ast.Name):
            if func.id in self.polars_scan_names:
                return func.id
            return None
        if isinstance(func, ast.Attribute):
            if not isinstance(func.value, ast.Name):
                return None
            if func.value.id not in self.polars_module_aliases:
                return None
            if func.attr in FULL_SCAN_CALLS:
                return func.attr
        return None

    def _resolve_polars_module_alias(self, value: ast.AST | None) -> str | None:
        if isinstance(value, ast.Name) and value.id in self.polars_module_aliases:
            return value.id
        return None


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


def _argument_names(arguments: ast.arguments) -> set[str]:
    names = {arg.arg for arg in arguments.posonlyargs}
    names.update(arg.arg for arg in arguments.args)
    names.update(arg.arg for arg in arguments.kwonlyargs)
    if arguments.vararg is not None:
        names.add(arguments.vararg.arg)
    if arguments.kwarg is not None:
        names.add(arguments.kwarg.arg)
    return names
