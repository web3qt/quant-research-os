from __future__ import annotations

import ast
import tokenize
from pathlib import Path
from typing import Protocol

from runtime.tools.stage_program_scaffold import STAGE_PROGRAM_SPECS


_DANGEROUS_STAGE_BUILDERS_BY_MODULE: dict[str, set[str]] = {}
_DANGEROUS_STAGE_BUILDERS_BY_BASE_NAME: dict[str, str] = {}
for spec in STAGE_PROGRAM_SPECS.values():
    module = str(spec["module"])
    function = str(spec["function"])
    _DANGEROUS_STAGE_BUILDERS_BY_MODULE.setdefault(module, set()).add(function)
    _DANGEROUS_STAGE_BUILDERS_BY_BASE_NAME[module.rsplit(".", 1)[-1]] = module


class StageProgramIdentity(Protocol):
    stage_id: str
    program_dir: Path
    entrypoint_path: Path


def validate_stage_program_identity(validated: StageProgramIdentity) -> str | None:
    if validated.stage_id == "mandate":
        return None

    python_files = sorted(validated.program_dir.rglob("*.py"))
    for path in python_files:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            if path == validated.entrypoint_path:
                return f"{validated.program_dir}: run_stage.py is not valid Python: {exc.msg}"
            return f"{validated.program_dir}: helper {path.name} is not valid Python: {exc.msg}"

        if _file_uses_forbidden_stage_builder(tree):
            return f"{validated.program_dir}: post-mandate stage program cannot be a thin wrapper around framework builders"

        if path == validated.entrypoint_path and not _source_has_chinese_comment(source):
            return f"{validated.program_dir}: run_stage.py must contain Chinese comments for key generation logic"
        if path != validated.entrypoint_path and _python_file_has_callable_definitions(source):
            if not _source_has_chinese_comment(source):
                return f"{validated.program_dir}: helper {path.name} must contain Chinese comments for key logic"

    return None


def _source_has_chinese_comment(source: str) -> bool:
    try:
        for token in tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__):
            if token.type == tokenize.COMMENT and any("\u4e00" <= char <= "\u9fff" for char in token.string):
                return True
    except tokenize.TokenError:
        return False
    return False


def _file_uses_forbidden_stage_builder(tree: ast.AST) -> bool:
    imported_builder_names, module_aliases = _resolve_forbidden_builder_imports(tree)
    imported_builder_names, module_aliases = _resolve_local_aliases(
        tree,
        imported_builder_names,
        module_aliases,
    )
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in imported_builder_names:
            return True
        if isinstance(func, ast.Attribute):
            resolved = _resolve_dotted_call_target(func, module_aliases)
            if resolved is not None:
                module_name, attribute_name = resolved
                if attribute_name in _DANGEROUS_STAGE_BUILDERS_BY_MODULE.get(module_name, set()):
                    return True
    return False


def _resolve_local_aliases(
    tree: ast.AST,
    imported_builder_names: set[str],
    module_aliases: dict[str, str],
) -> tuple[set[str], dict[str, str]]:
    resolved_builder_names = set(imported_builder_names)
    resolved_module_aliases = dict(module_aliases)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                    continue
                target_name = node.targets[0].id
                value = node.value
                if isinstance(value, ast.Name) and value.id in resolved_builder_names:
                    if target_name not in resolved_builder_names:
                        resolved_builder_names.add(target_name)
                        changed = True
                    continue
                if isinstance(value, ast.Name):
                    module_name = resolved_module_aliases.get(value.id)
                    if module_name is not None and resolved_module_aliases.get(target_name) != module_name:
                        resolved_module_aliases[target_name] = module_name
                        changed = True
                continue
            if isinstance(node, ast.AnnAssign):
                if not isinstance(node.target, ast.Name):
                    continue
                if node.value is None:
                    continue
                target_name = node.target.id
                value = node.value
                if isinstance(value, ast.Name) and value.id in resolved_builder_names:
                    if target_name not in resolved_builder_names:
                        resolved_builder_names.add(target_name)
                        changed = True
                    continue
                if isinstance(value, ast.Name):
                    module_name = resolved_module_aliases.get(value.id)
                    if module_name is not None and resolved_module_aliases.get(target_name) != module_name:
                        resolved_module_aliases[target_name] = module_name
                        changed = True
    return resolved_builder_names, resolved_module_aliases


def _resolve_forbidden_builder_imports(tree: ast.AST) -> tuple[set[str], dict[str, str]]:
    imported_builder_names: set[str] = set()
    module_aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module in _DANGEROUS_STAGE_BUILDERS_BY_MODULE:
                dangerous_names = _DANGEROUS_STAGE_BUILDERS_BY_MODULE[node.module]
                for alias in node.names:
                    if alias.name == "*":
                        imported_builder_names.update(dangerous_names)
                    elif alias.name in dangerous_names:
                        imported_builder_names.add(alias.asname or alias.name)
                continue
            if node.module == "runtime.tools":
                for alias in node.names:
                    module_name = _DANGEROUS_STAGE_BUILDERS_BY_BASE_NAME.get(alias.name)
                    if module_name is not None:
                        module_aliases[alias.asname or alias.name] = module_name
                continue
            if node.module == "runtime":
                for alias in node.names:
                    if alias.name == "tools":
                        module_aliases[alias.asname or alias.name] = "runtime.tools"
                continue
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in _DANGEROUS_STAGE_BUILDERS_BY_MODULE:
                    module_aliases[alias.asname or alias.name.split(".")[-1]] = alias.name
                elif alias.name == "runtime.tools":
                    module_aliases[alias.asname or alias.name.split(".")[-1]] = alias.name
                elif alias.name == "runtime":
                    module_aliases[alias.asname or alias.name.split(".")[-1]] = alias.name
    return imported_builder_names, module_aliases


def _resolve_dotted_call_target(node: ast.Attribute, module_aliases: dict[str, str]) -> tuple[str, str] | None:
    parts: list[str] = []
    current: ast.AST = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    base_name = current.id
    base_module = module_aliases.get(base_name)
    if base_module is None:
        return None
    parts.append(base_module)
    parts.reverse()
    if len(parts) < 2:
        return None
    return ".".join(parts[:-1]), parts[-1]


def _python_file_has_callable_definitions(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    return any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for node in ast.walk(tree))
