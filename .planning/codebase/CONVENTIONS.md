# Coding Conventions

**Analysis Date:** 2026-05-06

## Naming Patterns

**Files:**
- snake_case throughout: `review_engine.py`, `stage_evaluator.py`, `adversarial_review_contract.py`
- Module files use single-word or compound-snake names: `anti_drift.py`, `closure_writer.py`
- Test files use `test_` prefix matching the module under test: `test_review_engine.py`, `test_stage_evaluator.py`
- Scripts in `runtime/scripts/` follow the same snake_case pattern: `gen_stage_review_skills.py`, `run_research_session.py`
- Contract YAML files use snake_case: `workflow_stage_gates.yaml`, `review_checklist_master.yaml`
- Binary scripts in `runtime/bin/` use kebab-case: `qros-update`, `qros-spawn-reviewer`

**Functions:**
- snake_case with descriptive multi-word names: `run_stage_review()`, `canonical_snapshot_from_session_context()`
- Private/internal functions prefixed with single underscore: `_require_stage_config()`, `_read_yaml_if_present()`
- Public API functions have no prefix: `evaluate_stage()`, `build_review_scope()`
- Builder/factory functions use `build_` or `scaffold_` prefix: `build_csf_signal_ready_from_data_ready()`, `scaffold_csf_data_ready()`
- Loader functions use `load_` prefix: `load_gate_schema()`, `load_adversarial_review_request()`
- Validator functions use `validate_` prefix: `validate_receipt_against_request()`, `validate_result_contract()`
- Issuer/writer functions use `ensure_` or `write_` prefix: `ensure_adversarial_review_request()`, `write_closure_artifacts()`

**Variables:**
- snake_case: `stage_dir`, `lineage_root`, `review_result`
- Private module-level variables prefixed with single underscore: `_SESSION_STAGE_TO_GATE_STAGE`, `_NEXT_STAGE_SNAPSHOT`
- Constants use UPPER_SNAKE_CASE: `ROOT`, `SNAPSHOT_VERSION`, `ALLOWED_REVIEW_LOOP_OUTCOMES`
- Frozen tuples for constant collections: `IDEA_INTAKE_REQUIRED_OUTPUTS`, `MANDATE_REQUIRED_OUTPUTS`
- Type aliases use PascalCase: `GateSchema`, `ChecklistSchema`, `InstallMode`, `ResolvedInstallMode`

**Types:**
- dataclasses with `frozen=True` for immutable value objects: `StageEvaluatorSpec`, `CanonicalDecisionSnapshot`, `ReviewerRuntimeIdentity`
- `Literal` types for constrained strings: `InstallMode = Literal["repo-local", "user-global", "auto"]`
- Return type annotations on all public functions
- Use `from __future__ import annotations` in 101 of 100 runtime files and 90 test files for forward-reference type hints
- `dict[str, Any]` is the dominant complex type; `Path` is used consistently for filesystem paths
- `str | None` union pattern for optional strings (Python 3.11+ syntax)

## Code Style

**Formatting:**
- No explicit formatter configuration detected (no `.prettierrc`, no `black`, no `ruff.toml`, no `biome.json`)
- Code follows consistent PEP 8 style as written
- 4-space indentation
- Double quotes for strings
- Trailing commas in multi-line collections and function arguments
- Blank lines between top-level functions (PEP 8 standard)
- 79-100 character line lengths observed

**Linting:**
- No linter configuration detected (no `.flake8`, no `.ruff.toml`, no `pyproject.toml` lint section)
- No type checker configuration (no `mypy.ini`, no `[tool.mypy]` in pyproject.toml)
- No pre-commit hooks configuration (no `.pre-commit-config.yaml`)

**Key observations:**
- The codebase relies on disciplined manual style consistency rather than automated enforcement
- `from __future__ import annotations` is used universally, enabling modern type syntax without runtime cost

## Import Organization

**Order:**
1. `from __future__ import annotations` (always first)
2. Standard library imports: `import json`, `from pathlib import Path`, `from dataclasses import dataclass`
3. Third-party imports: `import yaml`, `import pyarrow.parquet as pq`
4. Local imports: `from runtime.tools.review_skillgen.adversarial_review_contract import ...`

**Within local imports:**
- Absolute imports only (no relative imports observed)
- `from runtime.tools.<module> import <specific_names>` is the standard pattern
- Multiple names from the same module on a single import line when logically related
- Multi-line import blocks when importing many names from the same module

**Path Aliases:**
- No path aliases configured (no `[tool.pytest.ini_options]` pythonpath beyond `"."`)
- Imports reference the package root `runtime.tools.*` directly

**Example from `runtime/tools/review_engine.py`:**
```python
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
import os
from typing import Any

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    FIX_REQUIRED_OUTCOME,
    ReviewerRuntimeIdentity,
    load_adversarial_review_request,
    ...
)
```

## Error Handling

**Patterns:**
- Custom exception classes extend `RuntimeError` or `ValueError`: `ReviewRuntimeConfigurationError(RuntimeError)`, `InstallError(RuntimeError)`, `StageProgramRuntimeError(ValueError)`, `ArtifactContractError(ValueError)`
- Each major module defines its own domain-specific exception: 10 custom exception classes across the runtime
- Validation functions raise `ValueError` with descriptive messages including the path and expected condition
- Error messages include actionable fix suggestions, e.g., `"fix: add a StageEvaluatorSpec to STAGE_EVALUATOR_SPECS"`
- Bilingual error messages: configuration errors include both English descriptions and Chinese docstrings (e.g., `"QROS review runtime configuration error:"` in messages, Chinese in class docstrings)
- `try/except` blocks are narrow and purpose-specific (e.g., YAML loading, file parsing)
- No bare `except:` or overly broad exception catching
- Missing-file scenarios return empty defaults rather than raising: `_read_yaml_if_present()` returns `{}` if file missing

**Raise pattern example:**
```python
raise ReviewRuntimeConfigurationError(
    "\n".join([
        "QROS review runtime configuration error:",
        f"missing {missing_label}: {stage}",
        f"fix: add `{stage}:` under `stages:` in `{relative_path}`",
    ])
)
```

## Logging

**Framework:** No logging framework used. The codebase does not import `logging` or any logging library.

**Output mechanism:**
- Library code (`runtime/tools/`) returns values and raises exceptions -- no stdout output
- CLI scripts (`runtime/scripts/`) use `print()` for user-facing output
- `print(..., file=sys.stderr)` for error output in CLI scripts
- No structured logging, no log levels, no log files

**Convention:** Keep library code silent; let the CLI layer handle all user-facing output. This is a deliberate design choice -- the runtime is a library consumed by agent scripts.

## Comments

**When to Comment:**
- Module-level docstrings are rare; the code is largely self-documenting through descriptive names
- Inline comments are sparse, used only for non-obvious logic
- Chinese comments appear in a few places alongside English: `"Stage content gate 只处理当前阶段自身内容"`
- TODO comments appear only in template/scaffold code (e.g., `idea_runtime.py` generates template files with `"TODO"` placeholders for users to fill in)
- No FIXME, HACK, or XXX comments found in library code

**Docstrings:**
- Classes use one-line docstrings: `"""QROS review runtime configuration error, with actionable fix info."""`
- Functions rarely have docstrings; the function name and type annotations serve as documentation
- Test helper modules have module-level docstrings: `"""Shared stage fixture builders for CSF pipeline tests."""`
- Dataclass fields rely on field names for documentation rather than docstrings

## Function Design

**Size:** Functions tend to be focused. The largest functions are orchestration functions like `run_stage_review()` (~280 lines) and `evaluate_stage()` that coordinate multiple steps. Helper functions are typically 10-30 lines.

**Parameters:**
- Keyword-only arguments for public APIs using `*` separator: `def run_stage_review(*, cwd=None, ...)`
- Path parameters accept `str | Path` and resolve internally: `stage_dir: str | Path`
- Complex configuration passed as dicts loaded from YAML contracts
- No default mutable arguments

**Return Values:**
- Functions return `dict[str, Any]` for structured data payloads
- Builder functions return `Path` pointing to the created directory
- Validation functions return `None` on success, raise on failure
- Check functions return `list[str]` of findings (empty = pass)

## Module Design

**Exports:**
- No explicit `__all__` declarations
- Modules export public functions and classes by naming convention (no underscore prefix)
- The `runtime/tools/review_skillgen/__init__.py` exists but is empty

**Barrel Files:**
- No barrel/index files used; consumers import directly from specific modules
- `runtime/tools/review_skillgen/` is the only package (has `__init__.py`); all other modules are single files

**Module organization by domain:**
- `runtime/tools/review_skillgen/` -- review protocol subsystem (18 files)
- `runtime/tools/*_runtime.py` -- per-stage runtime logic
- `runtime/tools/*_contract_runtime.py` -- per-stage contract validation
- `runtime/scripts/` -- CLI entry points that call into `runtime/tools/`

## Data Patterns

**Dataclasses:**
- All dataclasses use `frozen=True` for immutability
- Value objects: `StageEvaluatorSpec`, `CanonicalDecisionSnapshot`, `ReviewerRuntimeIdentity`
- Configuration objects: `InstallTarget`, `RuntimeAsset`
- Diagnostic objects: `FactorDiagnosticProfile`, `SignalDiagnosticProfile`

**Dictionaries as data:**
- YAML contract schemas are loaded as `dict[str, Any]`
- Gate configurations, checklist schemas, and artifact contracts flow through the system as dicts
- Payload construction uses dict literals, not dataclasses
- This is a deliberate choice: contracts are defined externally in YAML and consumed as dicts

**Constants:**
- Stage output requirements defined as frozen tuples: `DATA_READY_REQUIRED_OUTPUTS = (...)`
- Lookup tables as frozen dicts: `STAGE_EVALUATOR_SPECS: dict[str, StageEvaluatorSpec]`
- Allowed value sets as frozen sets: `ALLOWED_REVIEW_LOOP_OUTCOMES = {...}`

## Configuration File Patterns

**YAML contracts (authoritative):**
- `contracts/stages/workflow_stage_gates.yaml` -- stage gate definitions, required outputs, structural/metric checks
- `contracts/review/review_checklist_master.yaml` -- review checklist per stage
- `contracts/artifacts/*_artifacts.yaml` -- per-stage artifact contracts

**pyproject.toml:**
- Minimal configuration: project name, version, Python requirement, dependencies
- pytest config section: `testpaths = ["tests"]`, `pythonpath = ["."]`

**No environment files checked into VCS:** `.env` files are in `.gitignore`

## Git Workflow Conventions

**Branch strategy:**
- `main` branch is the release branch
- `dev` branch is active development
- Feature branches used for changes (implied by PR workflow)

**CI:**
- Single GitHub Actions workflow: `.github/workflows/anti-drift.yml`
- Runs on: pull requests, pushes to main, nightly cron (3 AM UTC), manual dispatch
- Python 3.13 in CI
- Installs dependencies via pip (not uv, despite lockfile)

**Commit messages:**
- Conventional commit style: `spec:`, `chore:`, `fix:` prefixes observed in recent history
- Example: `spec: host-neutral review protocol design for Phase 3`, `chore: release 0.4.4`

## File Encoding

- All file I/O uses explicit `encoding="utf-8"`
- YAML output uses `allow_unicode=True` for Chinese content support

## Code Organization Within Files

**Standard file layout (library modules):**
1. `from __future__ import annotations`
2. Standard library imports
3. Third-party imports
4. Local imports
5. Module-level constants (ROOT, paths, allowed sets)
6. Custom exception classes
7. Private helper functions (`_` prefix)
8. Public API functions

**Standard file layout (CLI scripts):**
1. Same import structure
2. `argparse` setup
3. Main function with business logic
4. `if __name__ == "__main__":` entry point

---

*Convention analysis: 2026-05-06*
