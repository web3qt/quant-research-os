# QROS Codex Native Skill Install Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the heavier pipx/global-CLI install story with a superpowers-style Codex-native install model based on `git clone`, a single skills symlink, and lightweight repo-local runtime entrypoints.

**Architecture:** Treat the QROS repo itself as the installed runtime. Expose `skills/` directly to Codex through `~/.agents/skills/qros -> ~/.codex/qros/skills`. Keep research orchestration and review execution inside repo-local scripts or very thin wrappers under `bin/`, and remove the package-distribution layer as the primary user path.

**Tech Stack:** Git, Bash shell helper scripts, existing QROS Python runtime under `scripts/` and `tools/`, `pytest`

---

### Task 1: Lock The New Native-Install Expectations

**Files:**
- Modify: `tests/test_install_docs.py`
- Modify: `tests/test_project_bootstrap.py`
- Create: `tests/test_codex_native_install_docs.py`

**Step 1: Write the failing doc/install tests**

Add assertions that the primary install story mentions:

- `git clone`
- `~/.codex/qros`
- `~/.agents/skills`
- `ln -s`
- `git pull`

Also assert the docs do **not** present `pipx install qros` or `uv tool install qros` as the primary path.

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_install_docs.py tests/test_codex_native_install_docs.py tests/test_project_bootstrap.py -v`

Expected: FAIL because current docs still describe the heavier global CLI install path.

**Step 3: Commit**

```bash
git add tests/test_install_docs.py tests/test_codex_native_install_docs.py tests/test_project_bootstrap.py
git commit -m "test: lock codex native install expectations"
```

### Task 2: Reshape The Repo Around Codex-Native Skill Discovery

**Files:**
- Create: `skills/`
- Modify: `.agents/skills/` or replace usage with `skills/`
- Create: `.codex/INSTALL.md`
- Create: `bin/`
- Create: `tests/test_skill_tree.py`

**Step 1: Add failing structure tests**

Add tests that assert:

- `skills/` exists
- `skills/qros-research-session/SKILL.md` exists
- review skills exist under `skills/`
- `.codex/INSTALL.md` exists

**Step 2: Implement the new tree**

Choose one repo-internal convention and make it consistent:

- either move canonical skills to `skills/`
- or generate/sync `skills/` from current sources

The important outcome is that `skills/` becomes the public install surface for Codex symlink discovery.

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_skill_tree.py tests/test_project_bootstrap.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add skills .codex/INSTALL.md bin tests/test_skill_tree.py tests/test_project_bootstrap.py
git commit -m "feat: add codex-native skill tree"
```

### Task 3: Replace The Heavy Install Story In Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/experience/installation.md`
- Modify: `docs/experience/quickstart-codex.md`
- Modify: `docs/experience/qros-research-session-usage.md`
- Modify: `docs/experience/codex-stage-review-skill-usage.md`
- Create: `.codex/INSTALL.md`

**Step 1: Rewrite the install docs**

Primary install instructions should become:

```bash
git clone <QROS_REPO_URL> ~/.codex/qros
mkdir -p ~/.agents/skills
ln -s ~/.codex/qros/skills ~/.agents/skills/qros
```

Update instructions should be:

```bash
cd ~/.codex/qros
git pull
```

**Step 2: Clarify how Codex discovers skills**

Explicitly document:

- Codex scans `~/.agents/skills/`
- `~/.agents/skills/qros` is a symlink
- the repo clone itself is the runtime

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_install_docs.py tests/test_codex_native_install_docs.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add README.md docs/experience/installation.md docs/experience/quickstart-codex.md docs/experience/qros-research-session-usage.md docs/experience/codex-stage-review-skill-usage.md .codex/INSTALL.md tests/test_install_docs.py tests/test_codex_native_install_docs.py
git commit -m "docs: rewrite qros install around codex native skills"
```

### Task 4: Replace Global CLI Entry With Thin Repo-Local Wrappers

**Files:**
- Create: `bin/qros-session`
- Create: `bin/qros-review`
- Modify: `skills/qros-research-session/SKILL.md`
- Modify: `skills/qros-mandate-review/SKILL.md`
- Modify: `skills/qros-data-ready-review/SKILL.md`
- Modify: `skills/qros-signal-ready-review/SKILL.md`
- Modify: `skills/qros-train-freeze-review/SKILL.md`
- Modify: `skills/qros-test-evidence-review/SKILL.md`
- Modify: `skills/qros-backtest-ready-review/SKILL.md`
- Modify: `skills/qros-holdout-validation-review/SKILL.md`
- Create: `tests/test_native_skill_runtime_paths.py`

**Step 1: Write the failing runtime-path tests**

Assert that installed/public skills reference repo-local stable wrappers such as:

- `~/.codex/qros/bin/qros-session`
- `~/.codex/qros/bin/qros-review`

and do not reference:

- `pipx install`
- `qros codex install`
- a heavy package-distribution-only path

**Step 2: Implement thin wrappers**

Keep them minimal:

- resolve current working directory
- delegate into existing Python runtime scripts
- avoid introducing a new full product CLI

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_native_skill_runtime_paths.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add bin/qros-session bin/qros-review skills tests/test_native_skill_runtime_paths.py
git commit -m "feat: add thin repo-local runtime wrappers for codex skills"
```

### Task 5: Verify Research Outputs Still Land In The Research Repo

**Files:**
- Modify: `tests/test_qros_session_cli.py` or replace with native-wrapper tests
- Modify: `tests/test_qros_review_cli.py` or replace with native-wrapper tests
- Create: `tests/test_native_install_smoke.py`

**Step 1: Add smoke tests**

Add tests that simulate:

- a repo clone root
- a research project root
- running the thin wrapper from inside the research project

Assert:

- `outputs/` lands in the research project
- no outputs are written into the QROS tool clone

**Step 2: Run focused tests**

Run: `python -m pytest tests/test_native_install_smoke.py tests/test_research_session_runtime.py tests/test_review_engine.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_native_install_smoke.py tests/test_research_session_runtime.py tests/test_review_engine.py
git commit -m "test: verify native codex install writes outputs in research repo"
```

### Task 6: Remove The Heavier Install Path As Primary Story

**Files:**
- Modify or delete: `qros/`
- Modify: `pyproject.toml`
- Modify: any docs that still present the package-first story

**Step 1: Decide what remains**

If the `qros/` package is no longer needed for the user path:

- remove it entirely

If parts remain useful for internal runtime reuse:

- keep them, but ensure docs clearly state they are not the primary install mechanism

**Step 2: Remove stale primary-path messaging**

Eliminate the package-first path from:

- user-facing install docs
- quickstart
- troubleshooting

**Step 3: Run broad verification**

Run: `python -m pytest tests -v`

Expected: PASS

**Step 4: Commit**

```bash
git add pyproject.toml qros README.md docs tests
git commit -m "refactor: make codex native skill install the primary qros model"
```
