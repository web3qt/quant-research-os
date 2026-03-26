# QROS Global Codex Skill Install Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert QROS from a repo-driven installer into a globally installed Codex tool where users keep the `qros-*` skill names, but every skill executes through a stable global `qros` CLI and writes research outputs into the current research project.

**Architecture:** Add a real Python package-level CLI with `qros` console entrypoints for Codex install, diagnostics, session orchestration, and review execution. Replace repo-relative skill commands with rendered Codex skill files that call `qros ...` against the current project directory. Move install state to `~/.codex/skills/` plus `~/.qros/manifest.json` and keep workflow templates/docs as package resources instead of copied runtime trees.

**Tech Stack:** Python 3.11, `pytest`, `importlib.resources`, existing QROS runtime modules under `tools/`, Codex skill files under `.agents/skills/`

---

### Task 1: Lock The New Packaging And Skill Expectations

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/test_qros_package_metadata.py`
- Modify: `tests/test_project_bootstrap.py`
- Modify: `tests/test_install_docs.py`

**Step 1: Write the failing package metadata test**

Create `tests/test_qros_package_metadata.py` with assertions like:

```python
from pathlib import Path


def test_pyproject_exposes_qros_console_script() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "qros"' in text
    assert "[project.scripts]" in text
    assert 'qros = "qros.cli:main"' in text
```

Also assert the package includes resource globs for skill templates and docs.

**Step 2: Write the failing bootstrap expectations**

Extend `tests/test_project_bootstrap.py` to assert these files exist:

- `qros/__init__.py`
- `qros/cli.py`
- `qros/codex_install.py`
- `qros/resources/`

Extend `tests/test_install_docs.py` so it expects docs to mention:

- `pipx install qros`
- `uv tool install qros`
- `qros codex install`
- `qros codex check`

**Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_qros_package_metadata.py tests/test_project_bootstrap.py tests/test_install_docs.py -v`

Expected: FAIL because the package is still named `quant-research-os`, no console script exists, and the new docs/files are not present yet.

**Step 4: Commit**

```bash
git add pyproject.toml tests/test_qros_package_metadata.py tests/test_project_bootstrap.py tests/test_install_docs.py
git commit -m "test: lock qros packaging expectations"
```

### Task 2: Create The Installable `qros` CLI Skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `qros/__init__.py`
- Create: `qros/cli.py`
- Create: `qros/paths.py`
- Create: `qros/resources/__init__.py`
- Test: `tests/test_qros_package_metadata.py`
- Create: `tests/test_qros_cli.py`

**Step 1: Write the failing CLI behavior tests**

Create `tests/test_qros_cli.py` covering:

- `qros --help` exits `0`
- `qros doctor --help` exits `0`
- `qros codex --help` exits `0`
- `qros session --help` exits `0`

Use `subprocess.run([sys.executable, "-m", "qros.cli", ...])` first so the tests do not depend on an installed wheel.

**Step 2: Add the package and console script**

Update `pyproject.toml`:

```toml
[project]
name = "qros"

[project.scripts]
qros = "qros.cli:main"
```

Create `qros/cli.py` with a top-level parser:

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qros")
    subparsers = parser.add_subparsers(dest="command", required=True)
    ...
    return parser
```

Add subcommands:

- `codex`
- `doctor`
- `session`
- `review`

Return proper exit codes instead of calling `print`-and-exit ad hoc.

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_qros_package_metadata.py tests/test_qros_cli.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add pyproject.toml qros/__init__.py qros/cli.py qros/paths.py qros/resources/__init__.py tests/test_qros_package_metadata.py tests/test_qros_cli.py
git commit -m "feat: add installable qros cli skeleton"
```

### Task 3: Implement Codex Skill Rendering And Global Skill Installation

**Files:**
- Create: `qros/codex_install.py`
- Create: `qros/skill_renderer.py`
- Create: `qros/resources/skill_templates/`
- Modify: `.agents/skills/qros-research-session/SKILL.md`
- Modify: `.agents/skills/qros-mandate-review/SKILL.md`
- Modify: `.agents/skills/qros-data-ready-review/SKILL.md`
- Modify: `.agents/skills/qros-signal-ready-review/SKILL.md`
- Modify: `.agents/skills/qros-train-freeze-review/SKILL.md`
- Modify: `.agents/skills/qros-test-evidence-review/SKILL.md`
- Modify: `.agents/skills/qros-backtest-ready-review/SKILL.md`
- Modify: `.agents/skills/qros-holdout-validation-review/SKILL.md`
- Create: `tests/test_codex_skill_install.py`

**Step 1: Write the failing install/render tests**

Create `tests/test_codex_skill_install.py` with coverage for:

- `install_codex_skills(home=tmp_home)` creates `tmp_home/.codex/skills/qros-research-session/SKILL.md`
- rendered skills contain `qros session` or `qros review`
- rendered skills do not contain `python scripts/`
- `qros codex check` reports success after install

Example assertion:

```python
text = installed_skill.read_text(encoding="utf-8")
assert "qros session" in text
assert "python scripts/" not in text
```

**Step 2: Implement the installer**

Create `qros/codex_install.py` with functions:

- `install_codex_skills(home: Path) -> InstallReport`
- `refresh_codex_skills(home: Path) -> InstallReport`
- `check_codex_install(home: Path) -> tuple[bool, list[str]]`

Create `qros/skill_renderer.py` that renders package-owned skill templates into concrete Codex skills with stable commands like:

```text
qros session --cwd "$PWD" --raw-idea "<idea>"
qros review --cwd "$PWD"
```

Write `~/.qros/manifest.json` with:

- package version
- installed skills
- installed at
- codex skills root

Wire `qros codex install`, `qros codex refresh`, and `qros codex check` in `qros/cli.py`.

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_codex_skill_install.py tests/test_qros_cli.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add qros/codex_install.py qros/skill_renderer.py qros/resources/skill_templates tests/test_codex_skill_install.py qros/cli.py .agents/skills/qros-research-session/SKILL.md .agents/skills/qros-mandate-review/SKILL.md .agents/skills/qros-data-ready-review/SKILL.md .agents/skills/qros-signal-ready-review/SKILL.md .agents/skills/qros-train-freeze-review/SKILL.md .agents/skills/qros-test-evidence-review/SKILL.md .agents/skills/qros-backtest-ready-review/SKILL.md .agents/skills/qros-holdout-validation-review/SKILL.md
git commit -m "feat: install codex skills from qros cli"
```

### Task 4: Route Research Session Execution Through The Global CLI

**Files:**
- Create: `qros/session_cli.py`
- Modify: `tools/research_session.py`
- Modify: `scripts/run_research_session.py`
- Modify: `.agents/skills/qros-research-session/SKILL.md`
- Create: `tests/test_qros_session_cli.py`
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Write the failing runtime-routing tests**

Create `tests/test_qros_session_cli.py` to verify:

- `python -m qros.cli session --cwd <tmp> --raw-idea "idea"` exits `0`
- outputs are written under `<tmp>/outputs/`
- nothing is written under `Path.home() / ".qros" / "outputs"`

Example assertion:

```python
assert (project_root / "outputs").exists()
assert not (home_root / ".qros" / "outputs").exists()
```

**Step 2: Implement the session CLI adapter**

Create `qros/session_cli.py` with a function like:

```python
def run_session_from_cli(*, cwd: Path, raw_idea: str | None, lineage_id: str | None, confirm_flag: str | None) -> int:
    outputs_root = cwd / "outputs"
    status = run_research_session(outputs_root=outputs_root, ...)
    ...
    return 0
```

Update `qros/cli.py` so `qros session` delegates into this adapter.

Keep `scripts/run_research_session.py` as a thin wrapper around the same shared function so script-level tests still cover the runtime entrypoint during the refactor.

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_qros_session_cli.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add qros/session_cli.py qros/cli.py tools/research_session.py scripts/run_research_session.py tests/test_qros_session_cli.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py .agents/skills/qros-research-session/SKILL.md
git commit -m "feat: route research session through qros cli"
```

### Task 5: Route Stage Review Execution Through The Global CLI

**Files:**
- Create: `qros/review_cli.py`
- Modify: `scripts/run_stage_review.py`
- Modify: `tools/review_skillgen/review_engine.py`
- Modify: `.agents/skills/qros-mandate-review/SKILL.md`
- Modify: `.agents/skills/qros-data-ready-review/SKILL.md`
- Modify: `.agents/skills/qros-signal-ready-review/SKILL.md`
- Modify: `.agents/skills/qros-train-freeze-review/SKILL.md`
- Modify: `.agents/skills/qros-test-evidence-review/SKILL.md`
- Modify: `.agents/skills/qros-backtest-ready-review/SKILL.md`
- Modify: `.agents/skills/qros-holdout-validation-review/SKILL.md`
- Create: `tests/test_qros_review_cli.py`
- Modify: `tests/test_run_stage_review_script.py`
- Modify: `tests/test_review_engine.py`

**Step 1: Write the failing review CLI tests**

Create `tests/test_qros_review_cli.py` with coverage for:

- `python -m qros.cli review --cwd <stage_dir>` exits `0`
- review artifacts are written relative to the supplied stage directory
- generated review skills call `qros review --cwd "$PWD"` or an equivalent stable path contract

**Step 2: Implement the review adapter**

Create `qros/review_cli.py` with a shared wrapper:

```python
def run_review_from_cli(*, cwd: Path) -> int:
    payload = run_stage_review(cwd=cwd)
    print(payload["verdict"])
    return 0
```

Wire `qros review` into `qros/cli.py` and keep `scripts/run_stage_review.py` as a thin compatibility wrapper around the shared function during implementation.

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_qros_review_cli.py tests/test_run_stage_review_script.py tests/test_review_engine.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add qros/review_cli.py qros/cli.py scripts/run_stage_review.py tools/review_skillgen/review_engine.py tests/test_qros_review_cli.py tests/test_run_stage_review_script.py tests/test_review_engine.py .agents/skills/qros-mandate-review/SKILL.md .agents/skills/qros-data-ready-review/SKILL.md .agents/skills/qros-signal-ready-review/SKILL.md .agents/skills/qros-train-freeze-review/SKILL.md .agents/skills/qros-test-evidence-review/SKILL.md .agents/skills/qros-backtest-ready-review/SKILL.md .agents/skills/qros-holdout-validation-review/SKILL.md
git commit -m "feat: route stage review through qros cli"
```

### Task 6: Replace Install Docs With The New Global Tool Story

**Files:**
- Modify: `README.md`
- Modify: `docs/experience/installation.md`
- Modify: `docs/experience/quickstart-codex.md`
- Modify: `docs/experience/qros-research-session-usage.md`
- Modify: `docs/experience/codex-stage-review-skill-usage.md`
- Modify: `tests/test_install_docs.py`

**Step 1: Write the failing documentation assertions**

Update `tests/test_install_docs.py` so it expects:

- `pipx install qros`
- `uv tool install qros`
- `qros codex install`
- `qros codex refresh`
- `qros session`
- no recommended `./setup --host codex ...` path in primary install instructions

**Step 2: Rewrite the docs**

Update the user-facing docs so the primary path is:

```bash
pipx install qros
qros codex install
```

or

```bash
uv tool install qros
qros codex install
```

Quickstart examples should show users opening Codex in a research repo and invoking:

```text
qros-research-session 帮我研究这个想法：...
```

Explain explicitly that skills resolve to the global `qros` CLI while research outputs are written to the current project.

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_install_docs.py tests/test_project_bootstrap.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add README.md docs/experience/installation.md docs/experience/quickstart-codex.md docs/experience/qros-research-session-usage.md docs/experience/codex-stage-review-skill-usage.md tests/test_install_docs.py tests/test_project_bootstrap.py
git commit -m "docs: rewrite qros install story around global codex skills"
```

### Task 7: Add Diagnostics And Run Full Verification

**Files:**
- Modify: `qros/cli.py`
- Modify: `qros/codex_install.py`
- Create: `tests/test_qros_doctor.py`
- Verify only: repository-wide

**Step 1: Write the failing diagnostics test**

Create `tests/test_qros_doctor.py` with assertions that `python -m qros.cli doctor` prints:

- package version
- codex skills root
- installed skill count
- manifest path

**Step 2: Implement `qros doctor`**

Add a doctor command that reports:

- package version
- `~/.codex/skills` path
- `~/.qros/manifest.json` path
- whether required `qros-*` skills are installed
- whether the current environment can resolve the `qros` executable

**Step 3: Run the full test suite**

Run: `python -m pytest tests -v`

Expected: PASS with the new package, CLI, skill install, docs, and runtime routing tests all green.

**Step 4: Smoke-check the new flow locally**

Run:

```bash
python -m qros.cli codex install
python -m qros.cli codex check
python -m qros.cli doctor
```

Then create a temporary project directory and run:

```bash
python -m qros.cli session --cwd /tmp/qros-smoke --raw-idea "BTC leads high-liquidity alts"
```

Expected:

- Codex install succeeds
- `doctor` reports installed skills
- `/tmp/qros-smoke/outputs/` is created
- `~/.qros/` contains state/manifest only, not research outputs

**Step 5: Commit**

```bash
git add qros/cli.py qros/codex_install.py tests/test_qros_doctor.py
git commit -m "feat: add qros doctor diagnostics"
```
