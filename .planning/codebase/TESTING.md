# Testing Patterns

**Analysis Date:** 2026-05-20

## Test Framework

**Runner:**
- pytest >= 8.0
- Config: `pyproject.toml` `[tool.pytest.ini_options]`
- Test paths: `["tests"]`
- Python path: `["."]` (enables absolute imports like `from runtime.tools...` and `from tests.helpers...`)

**Assertion Library:**
- Plain `assert` statements throughout (no `unittest` asserts)
- No assertion helper library (no `assertpy`, `expects`, etc.)

**Run Commands:**
```bash
pytest                          # Run all tests
pytest tests/review/            # Run review tests only
pytest tests/contracts/         # Run contract tests only
pytest -x                       # Stop on first failure
pytest -k "test_csf_data_ready" # Run tests matching pattern
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root (not co-located with source)
- Mirrors runtime structure: `tests/runtime/`, `tests/review/`, `tests/contracts/`, etc.

**Naming:**
- All test files: `test_<module_or_feature>.py`
- All test functions: `def test_<behavior_description>() -> None:`
- Test classes: `class Test<Feature>E2E:` or `class Test<Feature>Gates:`

**Structure:**
```
tests/
├── __init__.py
├── agent_eval/              # Agent behavior evaluation tests
│   ├── test_agent_behavior_assertions.py
│   ├── test_agent_behavior_eval_runner.py
│   ├── test_csf_*_agent_behavior_cases.py  # Per-stage agent tests
│   └── test_tss_*_agent_behavior_cases.py
├── anti_drift/              # Anti-drift regression tests
│   ├── test_anti_drift.py
│   ├── test_anti_drift_baseline.py
│   ├── test_anti_drift_metamorphic.py
│   └── test_anti_drift_replay.py
├── bootstrap/               # Install/setup smoke tests
│   ├── test_install_runtime.py
│   ├── test_setup_script.py
│   └── test_uv_runtime_env.py
├── contracts/               # Artifact contract validation tests
│   ├── test_csf_*_artifact_contract.py  # Per-stage CSF contracts
│   ├── test_tss_*_artifact_contract.py  # Per-stage TSS contracts
│   └── test_stage_evaluator_contract.py
├── docs/                    # Documentation validation tests
│   ├── test_docs_hygiene.py
│   └── test_*_contract_first_docs.py    # Per-stage doc coverage
├── e2e/                     # End-to-end agent session tests
│   ├── test_csf_agent_session.py
│   └── test_tss_agent_session.py
├── fixtures/                # Snapshot fixtures (JSON)
│   ├── anti_drift/
│   └── *_snapshot.json      # Per-stage expected outputs
├── helpers/                 # Shared test utilities
│   ├── agent_harness.py
│   ├── gate_assertions.py
│   ├── human_simulator.py
│   ├── stage_fixtures.py
│   └── skill_test_utils.py
├── pipeline/                # Full pipeline integration tests
│   ├── test_csf_pipeline.py
│   └── test_tss_pipeline.py
├── review/                  # Review engine tests
│   ├── test_review_engine.py
│   ├── test_adversarial_review_runtime.py
│   ├── test_protocol_validator.py
│   └── test_review_preflight_*.py        # Per-stage preflight tests
├── runtime/                 # Runtime module tests
│   ├── test_csf_*_runtime.py             # Per-stage CSF runtime tests
│   ├── test_tss_*_runtime.py             # Per-stage TSS runtime tests
│   └── test_*_semantic_validation.py     # Per-stage semantic tests
├── session/                 # Research session tests
│   ├── test_research_session_runtime.py
│   └── test_*_artifact_shape.py          # Per-stage artifact shape tests
└── skills/                  # Skill validation tests
    ├── test_skill_tree.py
    └── test_*_contract_first_guidance.py # Per-stage skill guidance
```

## Test Structure

**Suite Organization:**
```python
# Flat test functions (most common)
def test_run_stage_review_pass_path(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    _write_review_result(stage_dir)

    payload = run_stage_review(cwd=stage_dir, ...)

    assert payload["stage"] == "mandate"
    assert payload["final_verdict"] == "PASS"
```

```python
# Class-based grouping (pipeline and E2E tests)
class TestCsfAgentSessionE2E:
    @pytest.fixture()
    def lineage_root(self, tmp_path: Path) -> Path:
        return tmp_path / "outputs" / "csf_momentum_session"

    def test_full_session_passes_all_gates(self, lineage_root: Path) -> None:
        ...
```

**Patterns:**
- **Setup**: Private helper functions build stage fixtures in `tmp_path`:
  ```python
  def _prepare_mandate_stage(tmp_path: Path) -> Path:
      stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
      (stage_dir / "author" / "formal").mkdir(parents=True)
      ...
      return stage_dir
  ```
- **Teardown**: No explicit teardown; `tmp_path` handles cleanup
- **Assertion**: Plain `assert` with descriptive comparison values

## Test Helpers & Shared Utilities

**`tests/helpers/stage_fixtures.py`** — Composable stage builders:
- `prepare_mandate(lineage_root)` creates mandate stage with `cross_sectional_factor` route
- `prepare_csf_data_ready(lineage_root)` creates CSF data ready stage
- `prepare_csf_signal_ready(lineage_root)` builds from data_ready
- Full chain: `prepare_csf_holdout_validation(lineage_root)` builds all upstream stages
- TSS equivalents: `prepare_tss_mandate()`, `prepare_tss_data_ready()`, etc.
- Each builder returns `Path` (the `stage_dir`)
- Builders are composable: downstream builders call upstream builders

**`tests/helpers/gate_assertions.py`** — Gate verification utilities:
- `assert_all_gates_pass(stage_dir, stage_id)` runs all gate checks
- `assert_structural_gates_pass(formal_dir, stage_id)` for structural checks
- `assert_required_outputs_present(stage_dir, stage_id)` for output completeness
- Loads gate config from `contracts/stages/workflow_stage_gates.yaml`

**`tests/helpers/agent_harness.py`** — E2E agent simulation:
- `AgentHarness` drives a mock session through scripted stages
- `StageStep` defines questions + builder + gate assertions per stage
- `HumanSimulator` provides pre-scripted responses to agent questions

**`tests/helpers/skill_test_utils.py`** — Skill bundle discovery:
- `skill_bundle_dir(skill_name)` finds skill directory by name
- `skill_path(skill_name)` returns path to SKILL.md
- `skill_text(skill_name)` reads SKILL.md content

**`tests/helpers/repo_paths.py`** — Repository root resolution:
```python
TESTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TESTS_ROOT.parent
```

**`tests/helpers/freeze_draft_support.py`** — Freeze digest injection:
- `with_freeze_digests(payload)` adds deterministic digests for test YAML payloads

## Mocking

**Framework:** No mocking framework. Tests do not use `unittest.mock`, `pytest-mock`, or similar.

**Patterns:**
- **Real file I/O in `tmp_path`**: Tests create real directory trees and files in pytest's temporary directory
- **Builder functions substitute for mocks**: Instead of mocking runtimes, tests call builder functions that produce the same file layout the real runtime would
- **No network calls in codebase**: No HTTP clients to mock
- **YAML/JSON file creation**: Tests write protocol files directly:
  ```python
  def _write_yaml(path: Path, payload: dict) -> None:
      path.parent.mkdir(parents=True, exist_ok=True)
      payload = with_freeze_digests(payload)
      path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
  ```

**What to Mock:**
- Nothing explicitly mocked in this codebase
- Tests use real implementations with real file I/O

**What NOT to Mock:**
- Runtime functions under test — always call the real implementation
- File system operations — use `tmp_path` for real filesystem tests
- YAML/JSON parsing — use real `yaml.safe_load()` / `json.loads()`

## Fixtures and Factories

**Test Data:**
- Snapshot fixtures in `tests/fixtures/*.json` contain expected stage evaluator outputs for each stage and outcome combination:
  - `csf_data_ready_confirmation_snapshot.json` — PASS case
  - `train_freeze_pass_for_retry_snapshot.json` — RETRY case
  - `data_ready_child_lineage_snapshot.json` — CHILD LINEAGE case
- Anti-drift fixtures in `tests/fixtures/anti_drift/` for regression testing

**Factory Pattern:**
- Stage fixtures use composable builder pattern:
  ```python
  def prepare_csf_signal_ready(lineage_root: Path) -> Path:
      from runtime.tools.csf_signal_ready_runtime import build_csf_signal_ready_from_data_ready
      prepare_csf_data_ready(lineage_root)  # Build upstream first
      stage_dir = lineage_root / "03_csf_signal_ready"
      stage_dir.mkdir(parents=True, exist_ok=True)
      _write_yaml(stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml", CSF_SIGNAL_READY_FREEZE_DRAFT)
      build_csf_signal_ready_from_data_ready(lineage_root)
      return stage_dir
  ```
- Freeze draft constants defined as module-level dicts: `MANDATE_FREEZE_DRAFT`, `CSF_DATA_READY_FREEZE_DRAFT`

**Location:**
- `tests/helpers/stage_fixtures.py` — Stage builders
- `tests/fixtures/` — JSON snapshots
- `tests/fixtures/anti_drift/` — Anti-drift test data

## Coverage

**Requirements:** None enforced (no coverage config, no minimum threshold)

**View Coverage:**
```bash
pytest --cov=runtime tests/     # With pytest-cov (if installed)
pytest --cov=runtime --cov-report=html tests/  # HTML report
```

## Test Types

**Unit Tests (~70% of test files):**
- Scope: Single function or module behavior
- Pattern: Build a minimal `tmp_path` fixture, call the function, assert on the result or file side effects
- Located: `tests/runtime/`, `tests/review/`, `tests/contracts/`, `tests/skills/`
- Example: `tests/review/test_review_engine.py` tests `run_stage_review()` with various protocol configurations

**Integration Tests (~20% of test files):**
- Scope: Multi-module interactions within a stage pipeline
- Pattern: Compose stage builders, call runtime chain functions, verify end-to-end gate passing
- Located: `tests/pipeline/`, `tests/session/`
- Example: `tests/pipeline/test_csf_pipeline.py` tests mandate through signal_ready as a chain

**E2E Tests (~10% of test files):**
- Scope: Full agent session simulation with human interaction
- Pattern: AgentHarness drives stages, HumanSimulator answers questions, gate assertions verify outputs
- Located: `tests/e2e/`
- Example: `tests/e2e/test_csf_agent_session.py` simulates a full CSF momentum research session

**Contract Tests:**
- Scope: YAML artifact schema validation
- Pattern: Load artifact contract YAML, assert field presence, types, and allowed values
- Located: `tests/contracts/`
- Example: `tests/contracts/test_csf_data_ready_artifact_contract.py` validates parquet column requirements

**Anti-Drift Tests:**
- Scope: Regression protection for behavioral invariants
- Pattern: Canonical snapshot creation, semantic projection comparison, replay against saved snapshots
- Located: `tests/anti_drift/`

**Documentation Tests:**
- Scope: Verify documentation exists and matches code
- Located: `tests/docs/`

## Common Patterns

**Async Testing:**
- Not used. All code is synchronous Python.

**Error Testing:**
```python
# Pattern 1: try/except/else (most common in this codebase)
try:
    run_stage_review(...)
except ValueError as exc:
    assert "reviewer identity must differ" in str(exc)
else:
    raise AssertionError("expected self-review rejection")

# Pattern 2: pytest.raises (less common)
# Not observed in current codebase
```

**Parameterized Testing:**
```python
@pytest.mark.parametrize("current_stage", POST_MANDATE_REVIEW_CONFIRMATION_STAGES)
def test_something(current_stage: str) -> None:
    ...
```

**Filesystem Testing (primary pattern):**
```python
def test_something(tmp_path: Path) -> None:
    # 1. Build directory tree
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    (stage_dir / "author" / "formal").mkdir(parents=True)

    # 2. Create artifacts
    (stage_dir / "author" / "formal" / "mandate.md").write_text("ok\n", encoding="utf-8")

    # 3. Call runtime
    payload = run_stage_review(cwd=stage_dir)

    # 4. Assert on result and side effects
    assert payload["final_verdict"] == "PASS"
    assert (stage_dir / "review" / "closure" / "stage_completion_certificate.yaml").exists()
```

**Stage Gate Testing:**
```python
def test_stage_gates(formal_dir: Path) -> None:
    from tests.helpers.gate_assertions import assert_all_gates_pass
    assert_all_gates_pass(formal_dir, "csf_data_ready")
```

**Contract Validation Testing:**
```python
CONTRACT_PATH = Path("contracts/artifacts/csf_data_ready_artifacts.yaml")

def test_csf_data_ready_artifact_contract_exists_and_declares_stage_shape() -> None:
    assert CONTRACT_PATH.exists()
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["stage"] == "csf_data_ready"
    assert set(contract["artifacts"]) == {"panel_manifest.json", "asset_universe_membership.parquet", ...}
```

## Test Count

- **~109 test files** across 11 test directories
- **~230 runtime source files** under test
- Test-to-source ratio: approximately 0.47 test files per source file

## Key Test Directories by Purpose

| Directory | Purpose | Example File |
|-----------|---------|-------------|
| `tests/runtime/` | Per-stage runtime behavior | `tests/runtime/test_csf_data_ready_runtime.py` |
| `tests/review/` | Review engine + protocol validation | `tests/review/test_review_engine.py` |
| `tests/contracts/` | Artifact schema contracts | `tests/contracts/test_csf_data_ready_artifact_contract.py` |
| `tests/pipeline/` | Multi-stage integration | `tests/pipeline/test_csf_pipeline.py` |
| `tests/e2e/` | Full agent session simulation | `tests/e2e/test_csf_agent_session.py` |
| `tests/anti_drift/` | Behavioral regression | `tests/anti_drift/test_anti_drift.py` |
| `tests/agent_eval/` | Agent behavior evaluation | `tests/agent_eval/test_csf_data_ready_agent_behavior_cases.py` |
| `tests/session/` | Research session lifecycle | `tests/session/test_research_session_runtime.py` |
| `tests/skills/` | Skill bundle validation | `tests/skills/test_skill_tree.py` |
| `tests/docs/` | Documentation coverage | `tests/docs/test_docs_hygiene.py` |
| `tests/bootstrap/` | Install/setup smoke tests | `tests/bootstrap/test_install_runtime.py` |

---

*Testing analysis: 2026-05-20*
