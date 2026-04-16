# QROS Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `qros-update` skill and stable update entry so Codex users can refresh the published `main` version and the current repo's `./.qros/` runtime in one step.

**Architecture:** Introduce a thin runtime wrapper plus a Python update script that resolves the managed source repo, self-heals common install drift, fast-forwards to `origin/main`, refreshes `user-global`, refreshes the current repo's `repo-local` runtime, and validates both installs. Pair it with a new core skill that tells the agent to keep fixing common update failures instead of surfacing them immediately to the user.

**Tech Stack:** Bash wrappers, Python installer/update runtime, Markdown skill docs, pytest

---

### Task 1: Lock the update surface with failing tests

**Files:**
- Modify: `tests/test_skill_tree.py`
- Modify: `tests/test_project_bootstrap.py`
- Modify: `tests/test_install_docs.py`
- Modify: `tests/test_setup_script.py`
- Create: `tests/test_qros_update_script.py`

**Step 1: Write the failing tests**

- Assert `qros-update` exists in the public skill tree.
- Assert `runtime/bin/qros-update` exists in bootstrap expectations.
- Assert install docs mention `qros-update` as the preferred update path.
- Assert repo-local setup writes `.qros/bin/qros-update`.
- Add update-script tests covering:
  - source repo resolution from global manifest
  - end-to-end refresh of both `user-global` and current repo `./.qros/`
  - self-heal path when the managed repo is dirty and needs reset to `origin/main`

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_qros_update_script.py tests/test_skill_tree.py tests/test_project_bootstrap.py tests/test_install_docs.py tests/test_setup_script.py -q`

Expected: failures for missing `qros-update` assets and script behavior.

### Task 2: Add the stable update command

**Files:**
- Create: `runtime/scripts/run_qros_update.py`
- Create: `runtime/bin/qros-update`

**Step 1: Implement the update runtime**

- Resolve the managed source repo from:
  1. `--source-repo` if provided
  2. `~/.codex/qros/install-manifest.json:source_repo_path`
  3. default clone path `~/workspace/quant-research-os`
  4. current script repo as final fallback
- Update the managed source repo to `origin/main`.
- Auto-heal common drift by resetting and cleaning the managed install repo before retrying.
- Refresh `user-global` install via `install_qros(..., mode="user-global")`.
- Refresh the current repo's `repo-local` runtime via `install_qros(..., mode="repo-local")`.
- Run `check_install` for both surfaces and print a concise success summary.

**Step 2: Implement the wrapper**

- Match the style of other runtime wrappers.
- Forward `--cwd` to the Python script.
- Prefer the adjacent install manifest's `source_repo_path`, then fallback to the checked-out repo.

**Step 3: Run the focused tests to verify green**

Run: `python -m pytest tests/test_qros_update_script.py tests/test_setup_script.py -q`

Expected: all update-runtime tests pass.

### Task 3: Add the Codex skill and user-facing docs

**Files:**
- Create: `skills/core/qros-update/SKILL.md`
- Modify: `README.md`
- Modify: `.codex/INSTALL.md`
- Modify: `docs/guides/installation.md`
- Modify: `docs/README.codex.md`
- Modify: `docs/guides/quickstart-codex.md`

**Step 1: Add the skill**

- Tell the agent to update the user to the latest published `main`.
- Tell the agent to refresh both global install state and the current repo's `./.qros/`.
- Explicitly require self-healing of common update failures before surfacing a blocker to the user.

**Step 2: Update docs**

- Make `qros-update` the preferred Codex-side update path.
- Keep the manual `git pull && setup ...` steps as a lower-level fallback.

**Step 3: Run docs and bootstrap tests**

Run: `python -m pytest tests/test_skill_tree.py tests/test_project_bootstrap.py tests/test_install_docs.py -q`

Expected: docs and bootstrap expectations pass with the new skill and wrapper.

### Task 4: Final verification

**Files:**
- Verify only

**Step 1: Run the full focused suite**

Run: `python -m pytest tests/test_qros_update_script.py tests/test_skill_tree.py tests/test_project_bootstrap.py tests/test_install_docs.py tests/test_setup_script.py -q`

Expected: all focused tests pass.

**Step 2: Run smoke**

Run: `python runtime/scripts/run_verification_tier.py --tier smoke`

Expected: smoke passes.
