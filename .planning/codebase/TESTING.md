# Testing Patterns

**Analysis Date:** 2026-05-06

## Test Framework

**Runner:**
- pytest >=8.0 (declared in `pyproject.toml` `[project.optional-dependencies] dev`)
- Config: `[tool.pytest.ini_options]` in `pyproject.toml`
  - `testpaths = ["tests"]`
  - `pythonpath = ["."]`

**Assertion Library:**
- pytest built-in `assert` statements
- No additional assertion libraries (no `assertpy`, no `hypothesis`)

**Run Commands:**
```bash
python -m pytest                        # Run all tests
python -m pytest tests/review/          # Run specific test directory
python -m pytest tests/pipeline/        # Run pipeline tests
python -m pytest -k "test_name"         # Run specific test by name
```

**No coverage tool configured:** There is no `--cov` flag, no `[tool.coverage]` section in pyproject.toml, and no `.coveragerc` file.

## Test File Organization

**Location:**
- Centralized test directory: `tests/` at project root
- Mirrors source structure: `tests/review/` for `runtime/tools/review_skillgen/`, `tests/runtime/` for `runtime/tools/*_runtime.py`
- Test helpers in `tests/helpers/`
- Test fixtures in `tests/fixtures/anti_drift/`

**Naming:**
- `test_<module_name>.py` for test files: `test_review_engine.py`, `test_stage_evaluator.py`
- `test_<feature_description>.py` for feature tests: `test_csf_pipeline.py`, `test_docs_hygiene.py`
- Helper files use descriptive names without `test_` prefix: `stage_fixtures.py`, `gate_assertions.py`, `repo_paths.py`

**Structure:**
```
tests/
├── __init__.py
├── agent_eval/          # Agent behavior evaluation tests
├── anti_drift/          # Anti-drift/snapshot regression tests
├── bootstrap/           # Install and setup tests
├── contracts/           # YAML contract schema tests
├── docs/                # Documentation validation tests
├── e2e/                 # End-to-end agent session tests
├── fixtures/            # Test fixture data (JSON snapshots)
│   └── anti_drift/      # Canonical decision snapshots
├── helpers/             # Shared test utilities
├── pipeline/            # Multi-stage pipeline tests
├── review/              # Review engine and protocol tests
├── runtime/             # Per-stage runtime build tests
├── session/             # Session routing and artifact shape tests
└── skills/              # Skill file content and structure tests
```

## Test Statistics

- **228 test files** across 14 test directories
- **100 runtime Python files** (library code)
- Test-to-source ratio: ~2.3x (very high)
- No `conftest.py` files -- fixtures are organized as importable helper modules

## Test Structure

**Suite Organization:**
Tests use both flat functions and class-based organization depending on complexity.

**Flat function style (most common):**
```python
def test_run_stage_review_pass_path(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    _write_review_result(stage_dir)

    payload = run_stage_review(cwd=stage_dir, ...)

    assert payload["stage"] == "mandate"
    assert payload["final_verdict"] == "PASS"
```

**Class-based style (pipeline tests):**
```python
class TestCsfSignalReadyGates:
    """Verify csf_signal_ready runtime output passes all 14 structural gates."""

    @pytest.fixture()
    def signal_ready_dir(self, tmp_path: Path) -> Path:
        lineage_root = tmp_path / "outputs" / "csf_case"
        stage_dir = prepare_csf_signal_ready(lineage_root)
        return stage_dir / "author" / "formal"

    def test_structural_gates_pass(self, signal_ready_dir: Path) -> None:
        assert_structural_gates_pass(signal_ready_dir, "csf_signal_ready")
```

**Parametrized tests:**
```python
@pytest.mark.parametrize("current_stage", POST_MANDATE_REVIEW_CONFIRMATION_STAGES)
def test_review_entry_preflight_scope(current_stage: str) -> None:
    ...
```

**Patterns:**
- **Setup:** Private `_prepare_*()` functions create temporary directory structures with required artifacts
- **Teardown:** No explicit teardown needed -- `tmp_path` fixture handles cleanup
- **Assertions:** Direct `assert` statements with descriptive failure messages in helper functions

## Mocking

**Framework:** No mocking framework used. No `unittest.mock`, no `pytest-mock`.

**Patterns:**
- Tests exercise real runtime code against temporary filesystem structures (`tmp_path`)
- Filesystem interactions are the primary "external dependency" -- handled by creating real temp files
- No monkeypatching of imports or environment variables except in `tests/bootstrap/` which uses `monkeypatch: pytest.MonkeyPatch` for install path testing
- The `tests/helpers/human_simulator.py` provides a scripted response mechanism for E2E tests instead of mocking agent interactions

**What is NOT mocked:**
- YAML contract loading (tests read real contract files from `contracts/`)
- File I/O (tests create real files in `tmp_path`)
- Stage runtime build functions (tests call real builders)
- Parquet/JSON/YAML serialization

## Fixtures and Factories

**Test Data:**
```python
# From tests/helpers/stage_fixtures.py
def prepare_csf_data_ready(lineage_root: Path) -> Path:
    """Create csf_data_ready stage with realistic parquet artifacts."""
    stage_dir = lineage_root / "02_csf_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)
    _write_json(formal_dir / "panel_manifest.json", {...})
    _write_parquet(formal_dir / "asset_universe_membership.parquet", [...])
    ...
    prepare_mandate(lineage_root)  # Always build upstream first
    return stage_dir
```

**Location:**
- `tests/helpers/stage_fixtures.py` -- 640 lines of composable stage builders for CSF and TSS pipelines
- `tests/helpers/gate_assertions.py` -- Gate assertion helpers that load contract YAML and run checks
- `tests/helpers/repo_paths.py` -- `REPO_ROOT` and `TESTS_ROOT` path constants
- `tests/helpers/skill_test_utils.py` -- Skill file discovery and reading utilities
- `tests/helpers/agent_harness.py` -- Agent session simulation harness for E2E tests
- `tests/helpers/human_simulator.py` -- Scripted human response simulator
- `tests/fixtures/anti_drift/` -- 24 canonical decision snapshot JSON files

**Fixture builder pattern:**
- Builders are composable: `prepare_csf_signal_ready()` calls `prepare_csf_data_ready()` which calls `prepare_mandate()`
- Each builder creates a complete stage directory with all required formal artifacts
- Parquet files are created using `polars.DataFrame(rows).write_parquet(path)` within fixtures
- YAML fixtures are defined as module-level constants: `MANDATE_FREEZE_DRAFT`, `CSF_DATA_READY_FREEZE_DRAFT`

## Coverage

**Requirements:** None enforced. No coverage tool is configured.

**No coverage reporting.** There is no mechanism to measure or report test coverage.

## Test Types

**Unit Tests (dominant):**
- Located in `tests/review/`, `tests/runtime/`, `tests/contracts/`
- Test individual functions and classes in isolation
- Use `tmp_path` for filesystem-dependent tests
- Example: `test_review_engine.py` tests `run_stage_review()` with prepared directory structures

**Integration Tests (pipeline):**
- Located in `tests/pipeline/`
- Test multi-stage chains: `mandate -> data_ready -> signal_ready`
- Verify cross-stage handoffs and data flow
- Example: `test_csf_pipeline.py::test_three_stage_pipeline` chains three stages

**E2E Tests (agent sessions):**
- Located in `tests/e2e/`
- Simulate full research sessions with mock agents and human simulators
- `test_csf_agent_session.py` and `test_tss_agent_session.py`
- Use `AgentHarness` to drive scripted question-answer flows through all stages

**Contract/Schema Tests:**
- Located in `tests/contracts/`
- Validate YAML contract schemas have required fields
- Example: `test_stage_evaluator_contract.py` validates JSON schema required fields

**Documentation Tests:**
- Located in `tests/docs/`
- Verify documentation files exist and contain expected content
- Check README summaries, installation docs, release notes
- Example: `test_docs_hygiene.py`, `test_install_docs.py`

**Anti-Drift/Regression Tests:**
- Located in `tests/anti_drift/`
- Snapshot-based regression testing against canonical decision snapshots
- Compare current behavior against blessed JSON snapshots
- Example: `test_anti_drift.py::test_canonical_snapshot_preserves_semantic_fields_for_review_stage`

**Bootstrap/Install Tests:**
- Located in `tests/bootstrap/`
- Test installation scripts and setup procedures
- Use `monkeypatch` for path manipulation
- Example: `test_install_runtime.py`, `test_claude_repo_bootstrap.py`

## CI Test Pipelines

**GitHub Actions workflow:** `.github/workflows/anti-drift.yml`

**PR gate job** (runs on PRs and pushes to main):
```bash
python -m pytest \
  tests/anti_drift/test_build_anti_drift_release_artifact.py \
  tests/anti_drift/test_build_anti_drift_gate_summary.py \
  tests/anti_drift/test_export_anti_drift_snapshots.py \
  tests/anti_drift/test_anti_drift_replay.py \
  tests/anti_drift/test_render_anti_drift_nightly_report.py \
  tests/anti_drift/test_anti_drift_baseline.py \
  tests/anti_drift/test_anti_drift.py \
  tests/session/test_run_research_session_script.py \
  tests/contracts/test_schema_loaders.py \
  tests/review/test_generation.py \
  tests/review/test_generated_skills_fresh.py
```

Plus additional steps:
- `python runtime/scripts/gen_stage_review_skills.py --dry-run` (generator freshness)
- Snapshot baseline comparison
- Nightly gate summary smoke test

**Nightly release gate job** (cron + manual):
- Full anti-drift pipeline including snapshot generation and comparison
- Runs a full research session: `run_research_session.py --snapshot`
- Builds release artifact JSON

**Important:** CI does NOT run the full test suite. Only 11 specific test files are run in CI. The remaining ~217 test files run only locally.

## Common Patterns

**Error Testing:**
```python
def test_run_stage_review_rejects_self_review(tmp_path: Path) -> None:
    ...
    try:
        run_stage_review(cwd=stage_dir, ...)
    except ValueError as exc:
        assert "reviewer identity must differ" in str(exc)
    else:
        raise AssertionError("expected self-review rejection")
```

Also uses `pytest.raises`:
```python
def test_pipeline_rejects_empty_data_ready(self, tmp_path: Path) -> None:
    ...
    with pytest.raises((ValueError, FileNotFoundError)):
        build_csf_signal_ready_from_data_ready(lineage_root)
```

**Gate Assertion Pattern:**
```python
def test_all_gates_pass(self, signal_ready_dir: Path) -> None:
    assert_all_gates_pass(signal_ready_dir, "csf_signal_ready")
```
Where `assert_all_gates_pass` (from `tests/helpers/gate_assertions.py`) runs structural, metric, required output, and global evidence checks.

**Snapshot Comparison Pattern:**
```python
def test_canonical_snapshot_preserves_semantic_fields_for_review_stage() -> None:
    status = summarize_session_status(...)
    snapshot = canonical_snapshot_from_session_context(status, fixture_id="...")
    assert snapshot.fixture_id == "data-ready-review-core"
    assert snapshot.stage_id == "data_ready"
    ...
```

**E2E Agent Session Pattern:**
```python
class TestCsfAgentSession:
    @pytest.fixture()
    def harness(self, tmp_path: Path) -> AgentHarness:
        lineage_root = tmp_path / "outputs" / "csf_e2e"
        return AgentHarness(lineage_root, stages=[
            StageStep("mandate", MANDATE_QUESTIONS, build_mandate_stage),
            StageStep("csf_data_ready", CSF_DATA_READY_QUESTIONS, build_data_ready_stage),
            ...
        ])
```

## Test Data Management

**Anti-drift snapshots:** 24 JSON files in `tests/fixtures/anti_drift/` serve as canonical decision snapshots. These are blessed baselines that the anti-drift system compares against.

**Stage draft fixtures:** Defined as Python dict constants in `tests/helpers/stage_fixtures.py`:
- `MANDATE_FREEZE_DRAFT` -- mandate stage freeze draft with realistic values
- `CSF_DATA_READY_FREEZE_DRAFT` -- CSF data ready freeze draft
- `CSF_SIGNAL_READY_FREEZE_DRAFT` -- CSF signal ready freeze draft

**Runtime-built fixtures:** Tests call real runtime builder functions (`build_csf_data_ready_from_mandate()`, etc.) to generate realistic artifact structures, then validate against gate contracts.

**No database or external service dependencies:** All test data is created in-memory or in `tmp_path`.

## Test Coverage Gaps

**No coverage measurement:** The lack of a coverage tool means there is no visibility into which lines/branches are tested.

**CI runs only a subset:** Only 11 of ~228 test files run in CI. The remaining tests (runtime builds, session routing, skill content, etc.) run only on developer machines.

**Untested areas (identified):**
- `runtime/tools/research_session.py` (4887 lines, the largest file) -- only tested indirectly through snapshot tests and session tests, not with comprehensive unit tests
- `runtime/scripts/` CLI entry points -- limited direct testing (only `test_run_research_session_script.py` and a few others)
- `runtime/bin/` shell scripts -- no automated tests
- `runtime/hooks/` -- no test directory for hooks
- `runtime/tools/review_skillgen/closure_writer.py` -- tested but only through integration paths
- `runtime/tools/review_skillgen/context_inference.py` -- tested indirectly
- `runtime/tools/review_skillgen/review_scope_builder.py` -- tested indirectly

**Priority: High** -- Adding coverage measurement and expanding CI test scope would significantly improve regression safety.

---

*Testing analysis: 2026-05-06*
