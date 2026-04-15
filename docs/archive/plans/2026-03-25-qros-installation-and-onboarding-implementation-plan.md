# QROS Installation And Onboarding Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a gstack-style installation and onboarding layer for Codex so users can run `./setup`, install QROS in `repo-local` or `user-global` mode, and follow a documented first workflow from `idea_intake` to `mandate review`.

**Architecture:** Add a thin top-level `setup` wrapper and a shared Python installer core in `tools/install_runtime.py`. The installer copies a bounded asset set into `.agents/skills/` plus `.qros/` for repo-local installs, or into `~/.codex/skills/` plus `~/.qros/` for user-global installs. Documentation is anchored by a new `README.md` and two experience docs so the install path and first-run workflow are consistent with the actual runtime.

**Tech Stack:** Python 3.11, `pytest`, Bash `setup`, existing QROS scripts and skills

---

### Task 1: Lock Bootstrap Expectations For Install Assets

**Files:**
- Modify: `tests/test_project_bootstrap.py`
- Create: `tests/test_install_runtime.py`

**Step 1: Write the failing bootstrap assertions**

Update `tests/test_project_bootstrap.py` to assert these files exist:

- `README.md`
- `setup`
- `tools/install_runtime.py`
- `docs/experience/installation.md`
- `docs/experience/quickstart-codex.md`

Add targeted assertions for new install-facing docs so the repo bootstrap test fails before implementation exists.

**Step 2: Write failing installer tests**

Create `tests/test_install_runtime.py` with coverage for:

- repo-local install copies `qros-*` skills into `<target>/.agents/skills/`
- repo-local install copies runtime files into `<target>/.qros/`
- user-global install copies skills into `<home>/.codex/skills/`
- user-global install copies runtime files into `<home>/.qros/`
- `auto` mode picks repo-local when `.agents/` exists
- `check` mode reports missing assets without writing files
- manifest contains `host`, `install_mode`, `installed_skills`, and `source_git_commit`

Use `tmp_path` and monkeypatched home directories so tests do not touch the real user environment.

**Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_project_bootstrap.py tests/test_install_runtime.py -v`

Expected: FAIL because install files and installer module do not exist yet.

**Step 4: Commit**

```bash
git add tests/test_project_bootstrap.py tests/test_install_runtime.py
git commit -m "test: add installer bootstrap expectations"
```

### Task 2: Implement The Shared Installer Core

**Files:**
- Create: `tools/install_runtime.py`
- Test: `tests/test_install_runtime.py`

**Step 1: Write minimal installer structures**

Implement:

- `InstallMode = Literal["repo-local", "user-global", "auto"]`
- `InstallHost = Literal["codex"]`
- `InstallTarget` dataclass with `skills_root`, `runtime_root`, `manifest_path`
- `InstallResult` dataclass with `mode`, `skills_written`, `runtime_written`, `manifest_path`

Add helpers:

- `resolve_install_mode(mode: str, cwd: Path) -> str`
- `resolve_install_target(mode: str, cwd: Path, home: Path) -> InstallTarget`
- `list_skill_dirs(repo_root: Path) -> list[Path]`
- `list_runtime_assets(repo_root: Path) -> list[Path]`
- `build_manifest(...) -> dict`

**Step 2: Implement install and check behavior**

Implement public functions:

- `install_qros(repo_root: Path, cwd: Path, home: Path, mode: str, host: str = "codex") -> InstallResult`
- `check_install(repo_root: Path, cwd: Path, home: Path, mode: str, host: str = "codex") -> tuple[bool, list[str]]`

Rules:

- Copy only `qros-*` skills
- Copy runtime/docs/templates into `.qros/` or `~/.qros/`
- Write `install-manifest.json`
- Preserve unknown files
- Raise clear errors for unsupported host, missing assets, or invalid mode

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_install_runtime.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add tools/install_runtime.py tests/test_install_runtime.py
git commit -m "feat: add qros installer core"
```

### Task 3: Add The Top-Level `setup` Entry Point

**Files:**
- Create: `setup`
- Modify: `tools/install_runtime.py`
- Create: `tests/test_setup_script.py`

**Step 1: Write the failing setup wrapper tests**

Create `tests/test_setup_script.py` to verify:

- `./setup --host codex --mode repo-local` exits `0` and installs into the current repo
- `./setup --host codex --mode user-global` exits `0` and installs into a temporary home
- `./setup --host codex --check` exits nonzero or prints failures when install is incomplete

Use `subprocess.run(...)` with a temporary copied fixture repo rooted at `tmp_path`.

**Step 2: Implement the wrapper**

Create executable `setup`:

```bash
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"
python tools/install_runtime.py "$@"
```

Extend `tools/install_runtime.py` with a `main()` that parses:

- `--host codex`
- `--mode repo-local|user-global|auto`
- `--refresh`
- `--check`

Printing a concise summary:

- resolved mode
- skills destination
- runtime destination
- number of files written or check failures

**Step 3: Run targeted tests**

Run: `python -m pytest tests/test_setup_script.py tests/test_install_runtime.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add setup tools/install_runtime.py tests/test_setup_script.py tests/test_install_runtime.py
git commit -m "feat: add top-level setup entry point"
```

### Task 4: Document Installation And First Workflow

**Files:**
- Create: `README.md`
- Create: `docs/experience/installation.md`
- Create: `docs/experience/quickstart-codex.md`
- Modify: `docs/experience/idea-intake-to-mandate-flow.md`
- Test: `tests/test_project_bootstrap.py`

**Step 1: Write the failing documentation consistency test**

Extend `tests/test_project_bootstrap.py` so it asserts the new files exist and that the install docs mention:

- `./setup --host codex --mode repo-local`
- `./setup --host codex --mode user-global`
- `python scripts/scaffold_idea_intake.py`
- `python scripts/build_mandate_from_intake.py`
- `python scripts/run_stage_review.py`

If the assertions are easier as a new test file, create `tests/test_install_docs.py` instead.

**Step 2: Write the docs**

Create `README.md` with sections:

- project one-liner
- Quick start
- Install
- First workflow
- Install modes
- Runtime layout
- Troubleshooting

Create `docs/experience/installation.md` with:

- repo-local install
- user-global install
- auto mode
- refresh
- check
- install layout
- troubleshooting

Create `docs/experience/quickstart-codex.md` with:

- install command
- first lineage scaffold
- which skills to use first
- mandate build
- mandate review

Update `docs/experience/idea-intake-to-mandate-flow.md` so it references the new install path and quickstart docs.

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_project_bootstrap.py tests/test_install_docs.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add README.md docs/experience/installation.md docs/experience/quickstart-codex.md docs/experience/idea-intake-to-mandate-flow.md tests/test_project_bootstrap.py tests/test_install_docs.py
git commit -m "docs: add qros install and quickstart guides"
```

### Task 5: Run Full Verification And Prepare Handoff

**Files:**
- Verify only: repository-wide

**Step 1: Run the full test suite**

Run: `python -m pytest tests -v`

Expected: PASS with all tests green, including install and documentation coverage.

**Step 2: Smoke-check the actual installer**

Run in the worktree root:

```bash
./setup --host codex --mode repo-local
./setup --host codex --check
```

Expected:

- repo-local install succeeds
- `.qros/install-manifest.json` exists
- `.agents/skills/qros-*` are present
- `--check` reports success

**Step 3: Review git status**

Run: `git status --short`

Expected: clean, or only intended install outputs if the smoke check writes tracked assets that should be excluded from commit.

**Step 4: Commit final implementation**

```bash
git add README.md setup tools/install_runtime.py docs/experience/installation.md docs/experience/quickstart-codex.md docs/experience/idea-intake-to-mandate-flow.md tests/test_project_bootstrap.py tests/test_install_runtime.py tests/test_setup_script.py tests/test_install_docs.py
git commit -m "feat: add qros installation and onboarding flow"
```
