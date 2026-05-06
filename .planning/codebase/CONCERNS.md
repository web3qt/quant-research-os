# Codebase Concerns

**Analysis Date:** 2026-05-06

## Security Concerns

### Shell Injection via `shell=True` in subprocess
- **Severity:** HIGH
- **Files:** `runtime/scripts/run_agent_behavior_eval.py:102`
- **What:** `subprocess.run(command, shell=True, ...)` where `command` is built from a format template that includes file paths read from the filesystem. The `command_template` variable is formatted with `prompt_path`, `transcript_path`, `work_dir`, and `prompt` (file contents), any of which could contain shell metacharacters.
- **Impact:** If a prompt file contains shell metacharacters (`;`, `` ` ``, `$()`, etc.), arbitrary command execution is possible.
- **Fix:** Use `subprocess.run([...], shell=False)` with an explicit argument list. If shell features are truly needed, use `shlex.quote()` on all dynamic values.

### No Timeout on Any subprocess.run Calls
- **Severity:** MEDIUM
- **Files:** All 14 `subprocess.run()` calls across the runtime:
  - `runtime/tools/data_ready_runtime.py:35`
  - `runtime/tools/update_runtime.py:158,183,197,215,227`
  - `runtime/tools/csf_data_ready_runtime.py:42`
  - `runtime/tools/install_runtime.py:300`
  - `runtime/tools/lineage_program_runtime.py:367,446,712`
  - `runtime/scripts/run_verification_tier.py:73`
  - `runtime/scripts/run_agent_behavior_eval.py:102`
- **What:** None of the subprocess calls specify a `timeout` parameter. A child process that hangs will block the calling process indefinitely.
- **Impact:** A stalled stage program or git operation could hang the entire orchestration pipeline with no recovery mechanism.
- **Fix:** Add explicit `timeout=` values to all `subprocess.run()` calls. Handle `subprocess.TimeoutExpired` exceptions appropriately.

### Missing `encoding` Parameter on 122 `write_text()` Calls
- **Severity:** LOW
- **Files:** Across all scaffold and runtime modules (e.g., `runtime/tools/stage_program_scaffold.py:314,319,344`, `runtime/tools/idea_runtime.py:304,367,405,429,445,456`, `runtime/tools/csf_backtest_runtime.py:266`, and 115+ more).
- **What:** `write_text()` calls without explicit `encoding=` parameter default to the platform encoding (e.g., `cp1252` on Windows). The codebase contains Chinese characters (e.g., `"验证报告"`, `"质量语义"`) and uses `encoding="utf-8"` consistently in `read_text()` calls, but inconsistently in `write_text()`.
- **Impact:** On non-UTF-8 platforms, scaffolded files could be written with wrong encoding, causing downstream `read_text(encoding="utf-8")` calls to fail with `UnicodeDecodeError`.
- **Fix:** Add `encoding="utf-8"` to all `write_text()` calls. This is a consistency issue -- `read_text()` calls already specify it.

---

## Maintainability Concerns

### God Object: `research_session.py` at 4,887 Lines with 204 Functions
- **Severity:** HIGH
- **Files:** `runtime/tools/research_session.py`
- **What:** This single file contains the entire session state machine, all stage transition logic, all scaffold orchestration, and all closure completion checks. It imports 21 modules from `runtime.tools.*`. The file defines 100+ `_closure_complete()` helper functions that are near-identical one-liners (e.g., `_data_ready_closure_complete`, `_csf_data_ready_closure_complete`, `_tss_data_ready_closure_complete`, each differing only by a path check).
- **Impact:** Any change to session logic requires understanding and testing a 5K-line file. The file is a merge conflict magnet. 10+ modules depend on it, creating a tight coupling bottleneck.
- **Fix:** Extract into sub-modules:
  - `research_session/stage_transitions.py` -- per-stage transition logic
  - `research_session/closure_checks.py` -- the 18+ `_closure_complete()` functions
  - `research_session/approval_paths.py` -- the 8+ `_approval_path()` functions
  - `research_session/scaffolding.py` -- scaffold orchestration

### Systemic CSF/TSS Code Duplication (24 Paired Files)
- **Severity:** HIGH
- **Files:** 24 paired files in `runtime/tools/`:
  - `csf_*_runtime.py` (12 files) and `tss_*_runtime.py` (12 files)
  - `csf_*_contract_runtime.py` (6 files) and `tss_*_contract_runtime.py` (6 files)
- **What:** The CSF and TSS routes are near-identical implementations that differ only in directory names (`02_csf_data_ready` vs `02_tss_data_ready`), metric library paths, and stage identifiers. This duplication is amplified in `research_session.py` which duplicates every transition, closure check, and approval path for both routes.
- **Impact:** A bug fix or feature addition must be applied in 2-4 places. The CSF and TSS paths can easily drift apart. This is already visible in function counts: CSF contract runtimes have 9-18 functions while TSS equivalents have 2-6, suggesting uneven maintenance.
- **Fix:** Introduce a route-abstracted base layer with a `RouteConfig` dataclass that captures route-specific names and paths. The scaffold/validate/load functions should be parameterized by route rather than duplicated.

### Near-Identical Diagnostics Modules
- **Severity:** MEDIUM
- **Files:** `runtime/tools/factor_diagnostics.py` (893 lines, 69 functions) and `runtime/tools/signal_diagnostics.py` (838 lines, 60 functions)
- **What:** These two files share identical helper functions (`_load_yaml`, `_read_json`, `_read_yaml_optional`, `_read_csv_rows`, `_read_parquet_rows`, `_observe_metric`, `_missing`, `_observed`, `_infer_stage`, `_latest_mtime`), differing only in error class names, stage directory mappings, and metric library paths. A diff of the first 60 lines shows only 4 lines differ (imports, path constants, class name, and one extra field).
- **Impact:** Bug fixes to shared utilities must be applied twice. The `_read_json` and `_read_yaml_optional` functions silently return `None` on any exception, hiding data corruption.
- **Fix:** Extract shared utilities into `runtime/tools/diagnostics_common.py` or a base class. The route-specific parts (stage dirs, metric library paths, error class) should be configuration, not duplication.

### Anti-Drift Scenarios Duplication
- **Severity:** LOW
- **Files:** `runtime/tools/anti_drift_scenarios_mainline.py` (113 lines), `runtime/tools/anti_drift_scenarios_csf.py` (89 lines), `runtime/tools/anti_drift_scenarios_failure.py` (167 lines), `runtime/tools/anti_drift_scenarios_support.py` (413 lines)
- **What:** Three scenario files (`mainline`, `csf`, `failure`) follow identical patterns with different stage names and snapshot functions. The function signatures are structurally identical, differing only in stage prefixes (`snapshot_data_ready_confirmation` vs `snapshot_csf_data_ready_confirmation`).
- **Impact:** Adding a new stage requires updating all three scenario files. Not directly tested (all three are in the UNTESTED list).
- **Fix:** Parameterize by route and stage, generating scenarios from a shared configuration.

---

## Reliability Concerns

### 67 Broad `except Exception` Catches Swallowing Errors
- **Severity:** HIGH
- **Files:** Contract runtimes and diagnostics modules:
  - `runtime/tools/csf_signal_ready_contract_runtime.py:62,74,88,98`
  - `runtime/tools/csf_holdout_validation_contract_runtime.py:62,75,85`
  - `runtime/tools/csf_train_freeze_contract_runtime.py:75,87,110,120`
  - `runtime/tools/csf_test_evidence_contract_runtime.py:75+`
  - `runtime/tools/tss_data_ready_contract_runtime.py:36`
  - `runtime/tools/tss_holdout_validation_contract_runtime.py:29`
  - `runtime/tools/tss_train_runtime.py:229`
  - `runtime/tools/tss_holdout_runtime.py:217`
  - `runtime/tools/factor_diagnostics.py:166,178,188,199,210`
  - `runtime/tools/signal_diagnostics.py:173,185,195,206`
- **What:** 67 `except Exception` catches in production code. Many silently swallow errors and return `None` or an error list, making it impossible to distinguish between "file does not exist" and "file is corrupted" or "permission denied".
- **Impact:** Corrupted artifacts, permission issues, or encoding errors are silently ignored. Diagnostics may report metrics as "missing" when the actual problem is a file system error.
- **Fix:** Catch specific exceptions (`FileNotFoundError`, `PermissionError`, `json.JSONDecodeError`, `yaml.YAMLError`, `UnicodeDecodeError`). Log the actual error. Distinguish between "file absent" (expected) and "file unreadable" (actual error).

### `except ModuleNotFoundError` Fallback Stubs in research_session.py
- **Severity:** MEDIUM
- **Files:** `runtime/tools/research_session.py:48-159` (6 `try/except ModuleNotFoundError` blocks)
- **What:** TSS runtime modules are imported with fallback stubs that define minimal versions of scaffold functions. If a TSS module fails to import for any reason other than absence (e.g., syntax error, import error in the module itself), the fallback stub silently takes over, providing a degraded experience.
- **Impact:** A broken TSS module will silently fall back to minimal stubs rather than surfacing the import error. Debugging this requires understanding the fallback pattern.
- **Fix:** Use `importlib.util.find_spec()` to check if the module exists, then import normally so that real import errors propagate. Or make TSS modules optional via `pyproject.toml` extras rather than runtime fallbacks.

### No File Locking for Concurrent Access
- **Severity:** MEDIUM
- **Files:** All runtime tools that write artifacts, especially `runtime/tools/research_session.py` (28 write operations) and `runtime/tools/lineage_program_runtime.py`.
- **What:** No file locking mechanism (`fcntl`, `filelock`, etc.) is used anywhere in the codebase. Multiple processes could read/write session state, freeze drafts, or transition approval files concurrently, leading to torn writes or race conditions.
- **Impact:** If two QROS sessions operate on the same lineage root simultaneously, state files could be corrupted or transitions could be applied twice.
- **Fix:** Add file-based locking around critical state transitions. At minimum, document that concurrent access to the same lineage root is unsupported.

---

## Dependency Concerns

### Minimal Dependency Surface (Low Risk)
- **Severity:** LOW
- **Files:** `pyproject.toml`
- **What:** The project has only 2 runtime dependencies (`PyYAML>=6.0`, `pyarrow>=20.0`) and 1 dev dependency (`pytest>=8.0`). The `uv.lock` file shows additional transitive deps are minimal (`colorama`, `iniconfig`, `packaging`, `pluggy`).
- **Impact:** Low supply-chain risk. However, `pip-audit` is not installed and no automated vulnerability scanning is configured.
- **Fix:** Add `pip-audit` to dev dependencies and integrate into CI pipeline.

---

## Test Coverage Gaps

### 21 Runtime Modules Have No Direct Tests
- **Severity:** HIGH
- **Files:** All untested modules in `runtime/tools/`:
  - All 6 TSS contract runtimes: `tss_data_ready_contract_runtime.py`, `tss_signal_ready_contract_runtime.py`, `tss_train_freeze_contract_runtime.py`, `tss_test_evidence_contract_runtime.py`, `tss_backtest_ready_contract_runtime.py`, `tss_holdout_validation_contract_runtime.py`
  - All 6 CSF contract runtimes: `csf_data_ready_contract_runtime.py`, `csf_signal_ready_contract_runtime.py`, `csf_train_freeze_contract_runtime.py`, `csf_test_evidence_contract_runtime.py`, `csf_backtest_ready_contract_runtime.py`, `csf_holdout_validation_contract_runtime.py`
  - `stage_program_scaffold.py`, `stage_artifact_layout.py`, `update_runtime.py`
  - `review_session_runtime.py`
  - All 3 anti_drift_scenarios files: `anti_drift_scenarios.py`, `anti_drift_scenarios_csf.py`, `anti_drift_scenarios_failure.py`
  - `anti_drift_scenarios_support.py`
- **What:** These 21 modules handle stage validation, scaffolding, and update logic but have zero dedicated test files. They are only tested indirectly through the monolithic `research_session.py` integration tests.
- **Impact:** Bugs in contract validation, scaffolding, or update logic may go undetected until they manifest in a full session run.

### CI Only Runs Subset of Tests
- **Severity:** HIGH
- **Files:** `.github/workflows/anti-drift.yml`
- **What:** The CI workflow runs tests from only 5 of 10+ test directories: `tests/anti_drift`, `tests/contracts`, `tests/review`, `tests/session`, and `tests/fixtures`. The following directories are NOT in CI:
  - `tests/agent_eval` -- agent behavior evaluation tests
  - `tests/bootstrap` -- installation bootstrap tests
  - `tests/runtime` -- runtime tool unit tests (lineage program, artifact contracts, stage identity)
  - `tests/skills` -- skill freshness tests
  - `tests/e2e` -- end-to-end tests
  - `tests/pipeline` -- pipeline tests
- **Impact:** 897 tests are collected but only a subset runs in CI. Bugs in runtime tools, agent evaluation, and skill generation can be committed without detection.
- **Fix:** Add all test directories to the CI pipeline, or at minimum add `tests/runtime` and `tests/agent_eval`.

### Stale Documentation References Deleted Scripts
- **Severity:** LOW
- **Files:** `docs/archive/plans/2026-03-25-hybrid-stage-review-engine-implementation-plan.md`, `docs/archive/plans/2026-03-25-codex-stage-review-engine-implementation-plan.md`, `docs/superpowers/plans/2026-04-21-spawn-agent-review-implementation.md`
- **What:** These archived plan documents reference deleted scripts (`gen_codex_stage_review_skills.py`, `start_spawned_review_cycle`, `issue_spawned_reviewer_receipt`) and deleted binaries (`qros-spawn-reviewer`, `qros-start-spawned-review`).
- **Impact:** Developers following archived plans will encounter missing files. Low severity since they are in `docs/archive/` and `docs/superpowers/`.
- **Fix:** Add deprecation notices to archived docs or remove references to deleted artifacts.

---

## Performance Concerns

### Excessive Synchronous Filesystem Operations
- **Severity:** LOW
- **Files:** `runtime/tools/research_session.py` (105 `.exists()`/`.is_file()`/`.is_dir()` calls per session), `runtime/tools/lineage_program_runtime.py`
- **What:** The session state machine performs dozens of synchronous filesystem checks on every invocation to determine current state (checking for the existence of transition approval files, closure markers, stage directories, etc.). Each session step may perform 50+ stat() calls.
- **Impact:** On network filesystems or slow storage, this adds perceptible latency. On local SSDs this is negligible (<10ms total).
- **Fix:** Low priority. If performance becomes an issue, cache the filesystem state at the start of each session invocation.

### No Atomic File Writes
- **Severity:** LOW
- **Files:** All runtime tools that write state files.
- **What:** Files are written directly with `path.write_text()` rather than using atomic write patterns (write to temp file, then `os.replace()`). If the process crashes mid-write, partial/corrupted files may be left behind.
- **Impact:** A crash during state transition could leave a partially written freeze draft or approval file, potentially corrupting the session state.
- **Fix:** Implement an atomic write helper: write to `path.with_suffix('.tmp')`, flush/fsync, then `os.replace()`. Low priority since crashes during file writes are rare.

---

## Structural Concerns

### Large Uncommitted Change Set (62 Files Modified)
- **Severity:** MEDIUM
- **Files:** Current working tree shows 62 files modified with 705 insertions and 793 deletions (per `git diff --stat`).
- **What:** A large set of changes on the `dev` branch includes modifications to runtime tools, test files, skills, docs, and CI configuration. Five runtime scripts/binaries have been deleted.
- **Impact:** Long-lived uncommitted changes increase merge conflict risk and make it harder to bisect bugs.
- **Fix:** Commit the changes in logical groups (e.g., "remove spawned review scripts", "update review protocol").

---

*Concerns audit: 2026-05-06*
