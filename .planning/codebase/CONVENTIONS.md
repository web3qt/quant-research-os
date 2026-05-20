# Coding Conventions

**Analysis Date:** 2026-05-20

## Language & Runtime

**Primary:** Python 3.11+ (enforced via `requires-python = ">=3.11"` in `pyproject.toml`)

**Key characteristics:**
- Uses modern Python syntax: `str | None` union types (not `Optional[str]`), `tuple[str, ...]`
- `from __future__ import annotations` is present in nearly all source files (~103 of ~111 runtime files) and most test files (~111 test files)
- No type stubs or `py.typed` marker detected; typing is inline

## Naming Patterns

**Files:**
- snake_case for all Python modules: `review_engine.py`, `stage_evaluator.py`, `adversarial_review_contract.py`
- Test files prefixed with `test_`: `test_review_engine.py`, `test_csf_data_ready_artifact_contract.py`
- Helper modules in `tests/helpers/`: `stage_fixtures.py`, `gate_assertions.py`, `agent_harness.py`
- Runtime contract files suffixed with `_runtime.py`: `csf_data_ready_runtime.py`, `tss_signal_ready_runtime.py`
- Runtime contract files suffixed with `_contract_runtime.py`: `csf_data_ready_contract_runtime.py`, `tss_data_ready_contract_runtime.py`

**Functions:**
- snake_case universally: `run_stage_review()`, `load_gate_schema()`, `assert_protected_review_state_intact()`
- Private/internal helpers prefixed with underscore: `_require_stage_config()`, `_load_yaml()`, `_write_yaml()`
- Boolean-returning functions use `is_`/`has_` prefixes: `is_complete`, `_is_non_empty_value()`
- Factory/builders use `build_`/`prepare_`/`ensure_` prefixes: `build_review_payload()`, `prepare_mandate()`, `ensure_adversarial_review_request()`
- Loader functions use `load_` prefix: `load_gate_schema()`, `load_adversarial_review_request()`
- Validation functions use `validate_`/`assert_`/`check_`/`_require_` prefixes: `validate_receipt_against_request()`, `assert_all_gates_pass()`, `check_structural_gates()`, `_require_string()`

**Variables:**
- snake_case: `blocking_findings`, `stage_dir`, `review_loop_outcome`
- Constants are UPPER_SNAKE_CASE at module level: `GATES_PATH`, `CHECKLIST_PATH`, `FIX_REQUIRED_OUTCOME`
- Tuple constants for frozen collections: `IDEA_INTAKE_REQUIRED_OUTPUTS = ("idea_brief.md", ...)`

**Types:**
- `PascalCase` for dataclasses and classes: `StageEvaluatorSpec`, `ReviewerRuntimeIdentity`, `ProtectedStateError`, `AgentHarness`
- Custom exceptions inherit from `RuntimeError`: `ReviewRuntimeConfigurationError`, `StageEvaluatorConfigurationError`
- Type aliases use `PascalCase`: `GateSchema = dict[str, Any]`, `ChecklistSchema = dict[str, Any]`
- Frozen dataclasses for immutable value objects: `@dataclass(frozen=True)`

## Code Style

**Formatting:**
- No formatter config detected (no `.prettierrc`, `black.toml`, `ruff.toml`)
- Indentation: 4 spaces (consistent throughout)
- Line length appears to follow ~120 chars soft limit
- Trailing commas in multi-line collections

**Linting:**
- No linter config detected (no `.eslintrc`, `ruff.toml`, `flake8`)
- Code is consistently clean and well-structured despite lack of tooling enforcement

## Import Organization

**Order (source files):**
1. `from __future__ import annotations` (first line in ~93% of files)
2. Standard library: `csv`, `json`, `hashlib`, `os`, `datetime`, `pathlib`, `typing`
3. Third-party: `yaml`, `pyarrow`
4. Internal `runtime.*` imports (absolute paths)

**Order (test files):**
1. `from __future__ import annotations`
2. Standard library: `pathlib`, `typing`
3. Third-party: `pytest`, `yaml`
4. Internal `runtime.*` imports
5. Internal `tests.helpers.*` imports

**Path Aliases:**
- No path aliases configured (no `[tool.setuptools]` path rewriting)
- All imports use full absolute paths: `from runtime.tools.review_skillgen.loaders import load_gate_schema`
- Tests import from helpers via: `from tests.helpers.stage_fixtures import prepare_mandate`
- `pythonpath = ["."]` in pytest config enables this

**Key import convention:**
```python
from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    FIX_REQUIRED_OUTCOME,
    load_adversarial_review_request,
    load_reviewer_receipt,
)
```
- Constants first, then functions, each on its own line in parenthesized imports

## Error Handling

**Strategy:** Fail-fast with descriptive `ValueError` messages that include the file path and actionable context.

**Patterns:**
- Input validation uses private `_require_*` helper functions that raise `ValueError` with file path context:
  ```python
  def _require_string(payload: dict[str, Any], key: str, *, path: Path) -> str:
      value = payload.get(key)
      if not isinstance(value, str) or not value.strip():
          raise ValueError(f"{path}: {key} must be a non-empty string")
      return value.strip()
  ```
- Configuration errors use custom exception classes with multi-line diagnostic messages:
  ```python
  raise ReviewRuntimeConfigurationError(
      "\n".join([
          "QROS review runtime configuration error:",
          f"missing stage gate: {stage}",
          f"stage_dir: {stage_dir}",
          f"fix: add `{stage}:` under `stages:` in `{relative_path}`",
      ])
  )
  ```
- Protected state violations use `ProtectedStateError(RuntimeError)` with structured payload containing `reason_code`, `protected_path`, `message`, and `next_action` fields.
- Error codes as constants: `PROTECTED_STATE_DRIFT`, `REVIEW_STATE_PROJECTION_DRIFT`, `REVIEWER_FINDINGS_UNBOUND`
- Tests for errors use `try/except/else` pattern rather than `pytest.raises`:
  ```python
  try:
      run_stage_review(...)
  except ValueError as exc:
      assert "reviewer identity must differ" in str(exc)
  else:
      raise AssertionError("expected self-review rejection")
  ```

## Logging

**Framework:** No structured logging framework. No `logging` module usage detected.

**Patterns:**
- Errors are communicated via exceptions, not log statements
- Runtime state is persisted to YAML/JSONL files (e.g., `review_cycle_trace.jsonl`) rather than logs
- Timestamps use `datetime.now(timezone.utc).isoformat()` format

## Comments

**When to Comment:**
- Module-level docstrings describe purpose (especially in `tests/helpers/`)
- Inline comments explain non-obvious logic, often in Chinese:
  ```python
  # 先把合同里写明的关键数值门禁落成真实 blocking findings，避免"有产物但坏结果也放行"。
  blocking_findings.extend(deterministic_gate_findings)
  ```
  ```python
  # Stage content gate 只处理当前阶段自身内容；上游绑定验证单独走 deterministic validator。
  ```
- Error messages use Chinese in exception docstrings: `"""QROS review runtime 配置缺口，面向 CLI 输出可操作修复信息。"""`
- Bilingual documentation: Chinese inline comments coexist with English code

**JSDoc/TSDoc:**
- No docstrings on most functions; intent is conveyed through clear naming
- Docstrings appear primarily on public helper functions and test classes: `"""Shared stage fixture builders for CSF pipeline tests."""`

## Function Design

**Size:** Functions range from small helpers (5-20 lines) to large orchestrators (100+ lines). The `run_stage_review()` function in `runtime/tools/review_skillgen/review_engine.py` is ~320 lines, which is atypical; most functions are under 50 lines.

**Parameters:**
- Keyword-only arguments with `*` separator for functions with many parameters:
  ```python
  def run_stage_review(
      *,
      cwd: Path | None = None,
      explicit_context: dict[str, Any] | None = None,
      reviewer_identity: str | None = None,
  ) -> dict[str, Any]:
  ```
- `Path | None` for optional path arguments, defaulting to `None`
- Return type is almost always `dict[str, Any]` for runtime functions

**Return Values:**
- Runtime functions return `dict[str, Any]` payloads (not typed dataclasses for most return values)
- Dataclasses used for configuration/spec objects: `StageEvaluatorSpec`, `ReviewerRuntimeIdentity`
- Boolean functions return plain `bool`

## Module Design

**Exports:**
- No `__all__` exports; modules rely on `_` prefix convention for private functions
- Public API is the set of non-underscore-prefixed functions
- Entry points are in `runtime/bin/` (shell scripts) and `runtime/scripts/` (Python scripts)

**Barrel Files:**
- `__init__.py` files are empty or minimal (just to mark packages)
- No re-export barrel files; all imports use full paths

## Data Format Conventions

**YAML files:**
- Written with `yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)` for ordered, readable output
- Read with `yaml.safe_load()`
- Always specify `encoding="utf-8"` on read/write

**JSON files:**
- Written with `json.dumps(payload, ensure_ascii=False, indent=2) + "\n"`
- Read with `json.loads()`

**Parquet files:**
- Use `polars` in test fixtures: `pl.DataFrame(rows).write_parquet(path)`
- Use `pyarrow` in runtime: `pq.read_table(path).to_pylist()`

## Path Conventions

- All file paths use `pathlib.Path`, never string concatenation
- `ROOT = Path(__file__).resolve().parents[N]` for repo-relative paths
- `stage_dir / "author" / "formal"` for artifact directories
- `stage_dir / "review" / "request"` and `stage_dir / "review" / "result"` for review protocol
- `stage_dir / "review" / "closure"` for closure artifacts
- Stage directories numbered: `00_idea_intake/`, `01_mandate/`, `02_data_ready/`, ... `07_holdout/`
- CSF routes: `02_csf_data_ready/`, `03_csf_signal_ready/`, etc.
- TSS routes: `02_tss_data_ready/`, `03_tss_signal_ready/`, etc.

---

*Convention analysis: 2026-05-20*
