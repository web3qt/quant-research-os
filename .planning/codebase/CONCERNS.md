# Codebase Concerns

**Analysis Date:** 2026-05-20

## Tech Debt

**GOD file: `research_session.py` (5346 lines, 225 functions):**
- Issue: Single file contains session state machine, stage detection, route dispatch, review orchestration, output validation, and scaffolding for 3 research routes (CSF, TSS, legacy) across 7+ stages each.
- Files: `runtime/tools/research_session.py`
- Impact: Any change to any stage or route requires editing this monolith. High merge-conflict risk when multiple features touch different stages simultaneously. Cognitive overload for contributors. Slow review cycles.
- Fix approach: Extract per-stage handler classes or functions into `runtime/tools/session_stages/`. Move `REQUIRED_OUTPUTS` constants into their respective stage runtime modules (e.g., `csf_data_ready_runtime.py` already owns its outputs but `research_session.py` duplicates them). Extract `detect_session_stage()` into a standalone `runtime/tools/stage_detector.py`. Extract route dispatch into `runtime/tools/session_router.py`.

**Pattern duplication across CSF/TSS/legacy routes:**
- Issue: The CSF and TSS routes each repeat the same 7-stage pattern (data_ready, signal_ready, train_freeze, test_evidence, backtest_ready, holdout_validation) with near-identical logic. There are 18 `_outputs_complete` functions, 18 `_closure_complete` functions, and 18 `REQUIRED_OUTPUTS` lists -- each a 1-line wrapper calling the same `stage_outputs_complete()` with a different constant.
- Files: `runtime/tools/research_session.py` (lines 4284-4351 for outputs, 4703-4767 for closures, 368-640 for constants)
- Impact: Adding a new research route (e.g., `event_trigger`) requires adding ~50 near-identical functions and constants. Bug fixes must be applied in triplicate.
- Fix approach: Define a `RouteStageConfig` dataclass holding the stage list, required outputs, draft files, and group orders. Build a registry keyed by `(route, stage)` that replaces the `_csf_*`/`_tss_*` function explosion with generic dispatch.

**TSS fallback scaffolds in `research_session.py` lines 59-170:**
- Issue: Six `try/except ModuleNotFoundError` blocks define inline fallback implementations for TSS stage scaffolds. This couples the session module to TSS module availability and hides import failures silently.
- Files: `runtime/tools/research_session.py` (lines 59-170)
- Impact: If a TSS module is moved or renamed, the session silently falls back to a default scaffold rather than failing loudly. Debugging requires tracing through exception handlers.
- Fix approach: Make TSS modules a required dependency (they exist in the repo), or use a proper plugin registry pattern with explicit module discovery.

**No type-checking or linting tooling configured:**
- Issue: `pyproject.toml` contains no `mypy`, `pyright`, `ruff`, `flake8`, or `pylint` configuration. No static analysis runs in CI.
- Files: `pyproject.toml`
- Impact: Type errors, unused imports, and style drift accumulate undetected. The `# type: ignore` comments in 15+ files suggest known type issues being deferred indefinitely.
- Fix approach: Add `ruff` (formatter + linter) and `mypy` or `pyright` to dev dependencies. Configure in `pyproject.toml`. Add a lint step to CI before the existing anti-drift gate.

**No logging framework:**
- Issue: Runtime code uses no logging module (`logging`, `structlog`, etc.). The `install_runtime.py` CLI uses `print()` statements. Scripts use `print()` for JSON output. Library code has no observable diagnostics.
- Files: `runtime/tools/install_runtime.py` (lines 626-651), `runtime/scripts/review_cycle.py` (lines 98-144), all `runtime/tools/*.py`
- Impact: No structured way to debug production issues. No log levels to filter noise. No audit trail for stage transitions or review cycles.
- Fix approach: Adopt Python `logging` module with a project-level logger convention. Replace `print()` in library code with `logging.info/debug/warning`. Keep `print()` only in CLI entry points where JSON output is intentional.

## Known Bugs

**No known critical bugs detected.** The anti-drift CI pipeline (`tests/anti_drift/`) provides regression coverage for the deterministic output paths. The `todo.md` item 8 ("current artifacts are duplicated") and item 9 ("reduce artifact files") suggest known output redundancy issues tracked informally.

## Security Considerations

**Subprocess invocation with environment passthrough:**
- Risk: `runtime/tools/lineage_program_runtime.py` (line 374) passes `**os.environ` to subprocess, then adds `QROS_*` variables. Any secrets in the parent environment are inherited by spawned stage programs.
- Files: `runtime/tools/lineage_program_runtime.py` (lines 373-389)
- Current mitigation: The framework runs locally as a research tool, not as a network service. No user-supplied input controls the subprocess command directly (commands come from validated program manifests).
- Recommendations: Filter `os.environ` to pass only `QROS_*` and `PATH` variables. Document which environment variables are expected by stage programs.

**`update_runtime.py` clones git repositories via subprocess:**
- Risk: The update mechanism (`runtime/tools/update_runtime.py`) runs `git clone` and `git checkout` with a URL derived from a constant (`DEFAULT_REPO_URL = "https://github.com/web3qt/quant-research-os.git"`). The clone target path is derived from user home directory.
- Files: `runtime/tools/update_runtime.py` (lines 268, 367-469)
- Current mitigation: URL is a hardcoded constant, not user-supplied. Git operations are standard.
- Recommendations: Validate that resolved paths stay within expected directory bounds. Add a checksum or tag verification step after clone.

**No input sanitization on idea slug:**
- Risk: `slugify_idea()` in `research_session.py` (line 1388) strips non-alphanumeric characters and uses the result as a directory name. While it raises on empty results, path traversal via crafted inputs is not explicitly prevented.
- Files: `runtime/tools/research_session.py` (lines 1388-1393)
- Current mitigation: `re.sub(r"[^a-z0-9]+", "_", ...)` effectively strips any path separator or special character. Only lowercase alphanumeric and underscore remain.
- Recommendations: Add an explicit check that the slug does not start with `.` or `_`, and does not match reserved names like `..`.

## Performance Bottlenecks

**`detect_session_stage()` probes all stage directories sequentially:**
- Problem: Called on every session invocation. Checks 21 directories (7 stages x 3 routes) plus their output files. Each check calls `stage_outputs_complete()` which reads file existence for 5-10 required outputs.
- Files: `runtime/tools/research_session.py` (lines 1449-1650)
- Cause: No caching or early-exit optimization. The function walks from the last stage backward through all stages every time.
- Improvement path: Cache the detected stage in a session state file (e.g., `.qros_session_state.yaml`). Read the cache first, only re-detect if the cache is stale or missing. Alternatively, walk forward from the current stage rather than backward from the end.

**Review cycle artifact I/O without streaming:**
- Problem: Review engine reads entire YAML/CSV/Parquet artifacts into memory for validation. For large datasets (backtest results with many rows), this can consume significant memory.
- Files: `runtime/tools/review_skillgen/stage_content_gate.py` (lines 94, 265), `runtime/tools/review_skillgen/artifact_realism.py` (lines 127-159)
- Cause: No streaming or chunked reading for large artifact files.
- Improvement path: For Parquet files, use row-group-level reading with `pyarrow.parquet.ParquetFile` and iterate row groups. For CSV, use row-by-row validation where possible. Add a file-size check before full load with a warning for files exceeding a threshold (e.g., 100MB).

## Fragile Areas

**SessionStage Literal union with 100+ members:**
- Files: `runtime/tools/research_session.py` (lines 254-356)
- Why fragile: The `SessionStage` type is a `Literal[...]` with approximately 100 string values. Adding a stage requires updating this type, the `detect_session_stage()` function, the stage-to-skill mapping, the `_outputs_complete` functions, the `_closure_complete` functions, the `_approval_path` functions, and the gate status functions. Missing any one of these causes silent misrouting.
- Safe modification: When adding a stage, grep for all `_csf_data_ready` references and replicate the pattern for the new stage. Run the full anti-drift test suite before committing.
- Test coverage: `tests/session/test_research_session_runtime.py` (2922 lines) provides comprehensive session coverage but adding a stage still requires updates to 7+ locations.

**Review skillgen module (20 files, 5200 lines) with dense cross-references:**
- Files: `runtime/tools/review_skillgen/` (20 Python files)
- Why fragile: `adversarial_review_contract.py` imports from `review_scope_builder`, `review_cycle_trace`. `review_engine.py` imports from 5+ sibling modules. `protocol_validator.py` imports from 3 modules. Changes to the review request schema in `adversarial_review_contract.py` ripple through the entire module.
- Safe modification: The review module is well-tested (`tests/review/`). Always run `tests/review/test_adversarial_review_runtime.py` (1427 lines) after changes. The contract constants at the top of `adversarial_review_contract.py` (lines 18-56) are the key extension points.
- Test coverage: Good within the review module, but the integration between `research_session.py` and the review module is tested primarily through session-level tests.

**Stage output lists duplicated between stage runtimes and `research_session.py`:**
- Files: `runtime/tools/research_session.py` (lines 368-640), plus individual `*_runtime.py` files that define their own outputs
- Why fragile: `csf_data_ready_runtime.py` defines its scaffold outputs, and `research_session.py` independently defines `CSF_DATA_READY_REQUIRED_OUTPUTS`. These lists must stay synchronized but have no programmatic link.
- Safe modification: After modifying outputs in any `*_runtime.py`, always update the corresponding `*_REQUIRED_OUTPUTS` list in `research_session.py` and run `tests/runtime/test_csf_data_ready_runtime.py` plus `tests/session/test_research_session_runtime.py`.

## Scaling Limits

**Research routes scale linearly with stage count:**
- Current capacity: 3 routes x 7 stages = 21 stage variants
- Limit: Each new route requires ~500 lines in `research_session.py` (constants, detection, dispatch, outputs, closures, approvals). The file is already 5346 lines. At 5-6 routes it becomes unmaintainable.
- Scaling path: Extract route definitions into declarative YAML or dataclass registries. Replace the 100+ `SessionStage` literals with a computed type or generic `stage(phase, route)` pattern.

**CI only runs anti-drift tests, not the full suite:**
- Current capacity: CI (`anti-drift.yml`) runs ~10 specific test files. Full suite has 110 test files.
- Limit: Regression bugs in non-anti-drift areas (contract runtimes, review engine, install/update) are not caught by CI.
- Scaling path: Add a separate CI job for the full test suite. Start with a nightly run, then promote to PR gate once timing is acceptable.

## Dependencies at Risk

**`pyarrow>=20.0`:**
- Risk: `pyarrow` is a heavy dependency (large binary wheels) used for Parquet file reading in review validation and artifact realism checks. The minimum version 20.0 is very recent.
- Impact: If `pyarrow` has compatibility issues on a target platform, the entire review pipeline is blocked. Version pinning may conflict with downstream consumers.
- Migration plan: Evaluate whether `polars` (which bundles its own Parquet reader) or the lighter `fastparquet` could serve as a fallback. Alternatively, isolate pyarrow usage behind an optional import with graceful degradation for non-Parquet workflows.

**No lockfile pinning for runtime dependencies:**
- Risk: `pyproject.toml` specifies `PyYAML>=6.0` and `pyarrow>=20.0` with loose version ranges. The `uv.lock` exists but is not enforced for installed runtime copies.
- Impact: Different environments may resolve to different dependency versions, causing subtle behavioral differences in YAML serialization or Parquet handling.
- Migration plan: Pin exact versions in `pyproject.toml` or document that `uv.lock` is the source of truth and must be used for reproducible installs.

## Missing Critical Features

**No structured error catalog:**
- Problem: Errors are raised as `RuntimeError`, `ValueError`, or custom exceptions with string messages. No error codes, no structured error catalog, no way to programmatically match on error types for automated recovery.
- Files: All `runtime/tools/*.py` files use ad-hoc error classes.
- Blocks: Automated failure recovery, structured SOP dispatch, and programmatic error handling.

**No concurrency or parallel execution support:**
- Problem: The session state machine is entirely sequential. No support for running independent stages in parallel (e.g., TSS and CSF data_ready for the same idea).
- Files: `runtime/tools/research_session.py`
- Blocks: Research throughput when exploring multiple route hypotheses simultaneously.

**No session persistence / resume-from-middle:**
- Problem: `detect_session_stage()` always probes the filesystem to infer state. There is no explicit session state file that records the current stage, recent transitions, or pending operations.
- Files: `runtime/tools/research_session.py` (lines 1449+)
- Blocks: Reliable resumption after interruption, audit logging of session lifecycle, and fast stage detection.

**No `conftest.py` shared fixtures:**
- Problem: Tests use per-test fixtures defined inline (e.g., `@pytest.fixture()` in each test class). No shared `conftest.py` at any level despite 110 test files.
- Files: `tests/` directory (no `conftest.py` files found)
- Blocks: Test refactorability and fixture reuse. Contributors must recreate common setups (lineage roots, stage scaffolds) in each test file.

## Test Coverage Gaps

**Non-anti-drift test files not in CI:**
- What's not tested by CI: Contract runtime validators, semantic validation tests, install/update smoke tests, agent behavior eval, pipeline tests, and all review engine tests.
- Files: `tests/runtime/`, `tests/review/`, `tests/bootstrap/`, `tests/pipeline/`, `tests/agent_eval/`
- Risk: Changes that break non-anti-drift functionality pass CI. The anti-drift tests are important for deterministic output verification but do not exercise most runtime paths.
- Priority: High -- Add a full-suite CI job.

**No integration tests for update/install lifecycle:**
- What's not tested: End-to-end `qros-update` and `qros-install` flows in CI. Tests exist (`tests/bootstrap/test_qros_update_script.py` at 703 lines, `tests/bootstrap/test_install_runtime.py`) but are not run in CI.
- Files: `tests/bootstrap/`
- Risk: Update or install regressions are only caught when a user attempts to update.
- Priority: Medium

**No test for concurrent or interleaved session access:**
- What's not tested: What happens if two `qros-session` processes target the same lineage root simultaneously.
- Files: No test files found for this scenario.
- Risk: File corruption from concurrent writes to the same stage directory. Race conditions in stage detection.
- Priority: Low (single-user research tool, but worth documenting as a known limitation).

---

*Concerns audit: 2026-05-20*
