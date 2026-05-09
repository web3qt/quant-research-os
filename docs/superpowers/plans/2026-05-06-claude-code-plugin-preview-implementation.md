# Claude Code Plugin Preview + Repo Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase 1 — Add a Claude Code plugin marketplace preview surface that lets Claude Code discover QROS skills without claiming full cross-host workflow support. Phase 2 — Let Claude Code users initialize and refresh `./.qros` runtime in active research repos via host-aware install/update.

**Architecture:** Phase 1 — Plugin manifest + marketplace for discovery metadata and preview documentation. The plugin manifest explicitly lists the current grouped QROS skill bundle paths because the repository does not use Claude Code's default flat `skills/<name>/SKILL.md` layout. Phase 2 — Extend `install_runtime.py` and `update_runtime.py` from hard-coded `codex` host to host profiles with separate global metadata roots. Runtime bootstrap and host-neutral review stay out of scope and remain documented as future phases.

**Tech Stack:** JSON plugin manifests, Markdown docs, Python runtime tools, shell wrappers, `pytest`, existing QROS docs/bootstrap test layout.

---

## Scope Boundary

Implement Phase 1 and Phase 2 from `docs/superpowers/specs/2026-05-06-claude-code-support-design.md`.

### Phase 1 scope

Do not modify:

- `runtime/tools/install_runtime.py`
- `runtime/bin/*`
- `skills/*/SKILL.md`
- review closure runtime
- Codex install behavior

Do not claim:

- Claude Code is fully supported.
- Claude Code review subagent orchestration is equivalent to Codex.
- Plugin install initializes `./.qros/bin`.

### Phase 2 scope

Do not modify:

- review closure runtime (receipt, closer, raw findings validation)
- `skills/*/SKILL.md` (except `qros-update` skill for host-awareness)
- Codex install behavior (all code paths default to `host=codex`)
- stage flow or gate semantics

Do not claim:

- Claude Code plugin auto-bootstraps `./.qros` in every research repo.
- Plugin install replaces repo-local runtime initialization.
- Claude Code review workflow is equivalent to Codex.

## File Structure

- Create: `.claude-plugin/plugin.json`
  - Claude Code plugin manifest.
  - Declares plugin metadata and explicit skill paths.

- Create: `.claude-plugin/marketplace.json`
  - Marketplace catalog allowing `/plugin marketplace add web3qt/quant-research-os` and `/plugin install qros@quant-research-os`.

- Create: `tests/bootstrap/test_claude_plugin_preview.py`
  - Locks JSON validity, marketplace shape, skill path coverage, and preview wording.

- Modify: `docs/guides/installation.md`
  - Adds a clearly labeled Claude Code preview section.
  - Keeps Codex as the current fully supported host.

- Modify if needed: `README.md`
  - Optional short pointer to the Claude Code preview docs.
  - Only do this if the docs test in Task 3 requires a top-level pointer.

## Task 1: Add Failing Tests For Claude Plugin Preview

**Files:**
- Create: `tests/bootstrap/test_claude_plugin_preview.py`

- [ ] **Step 1: Write the failing test**

Create `tests/bootstrap/test_claude_plugin_preview.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _expected_skill_paths() -> list[str]:
    return sorted(
        f"./{skill_md.parent.relative_to(ROOT).as_posix()}/"
        for skill_md in (ROOT / "skills").rglob("SKILL.md")
    )


def test_claude_plugin_manifest_lists_all_grouped_qros_skills() -> None:
    manifest = _read_json(".claude-plugin/plugin.json")

    assert manifest["name"] == "qros"
    assert manifest["version"] == "0.4.4"
    assert "Preview" in str(manifest["description"])
    assert manifest["repository"] == "https://github.com/web3qt/quant-research-os"
    assert manifest["homepage"] == "https://github.com/web3qt/quant-research-os/blob/main/docs/guides/installation.md"

    skills = manifest["skills"]
    assert isinstance(skills, list)
    assert sorted(skills) == _expected_skill_paths()
    assert "./skills/core/qros-research-session/" in skills
    assert "./skills/core/qros-update/" in skills
    assert "./skills/mandate/qros-mandate-review/" in skills
    assert "./skills/csf_data_ready/qros-csf-data-ready-review/" in skills
    assert "./skills/tss_data_ready/qros-tss-data-ready-review/" in skills


def test_claude_plugin_marketplace_points_at_this_repository_plugin() -> None:
    marketplace = _read_json(".claude-plugin/marketplace.json")

    assert marketplace["name"] == "quant-research-os"
    assert marketplace["owner"] == {"name": "web3qt"}

    plugins = marketplace["plugins"]
    assert isinstance(plugins, list)
    assert len(plugins) == 1

    plugin = plugins[0]
    assert plugin["name"] == "qros"
    assert plugin["source"] == "./"
    assert plugin["version"] == "0.4.4"
    assert plugin["strict"] is True
    assert "Preview" in plugin["description"]


def test_claude_code_preview_docs_do_not_claim_full_support() -> None:
    installation = (ROOT / "docs/guides/installation.md").read_text(encoding="utf-8")

    assert "Claude Code preview" in installation
    assert "/plugin marketplace add web3qt/quant-research-os" in installation
    assert "/plugin install qros@quant-research-os" in installation
    assert "Plugin install 不等于 QROS workflow ready" in installation
    assert "Codex remains the fully supported host for review-subagent orchestration" in installation
    assert "Claude Code 完整支持" not in installation
    assert "Claude Code full support" not in installation
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
python -m pytest tests/bootstrap/test_claude_plugin_preview.py -q
```

Expected:

```text
FAILED tests/bootstrap/test_claude_plugin_preview.py::test_claude_plugin_manifest_lists_all_grouped_qros_skills
```

The failure should be caused by missing `.claude-plugin/plugin.json`, not by a Python syntax error.

- [ ] **Step 3: Checkpoint**

Do not commit unless the user explicitly authorizes commits. The repository rule forbids committing without explicit approval.

## Task 2: Add Claude Plugin And Marketplace Manifests

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Generate the exact skills path array**

Run this command from repo root to print the exact JSON array for `plugin.json.skills`:

```bash
python - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
skills = sorted(
    f"./{skill_md.parent.relative_to(root).as_posix()}/"
    for skill_md in (root / "skills").rglob("SKILL.md")
)
print(json.dumps(skills, indent=2, ensure_ascii=False))
PY
```

Expected:

```text
[
  "./skills/backtest_ready/qros-backtest-failure/",
  "./skills/backtest_ready/qros-backtest-ready-author/",
  "./skills/backtest_ready/qros-backtest-ready-review/"
]
```

The actual generated output will contain more entries after the three shown above. The exact list must contain every current `SKILL.md` parent directory and must remain sorted. The final entry in the current repository should be:

```text
"./skills/tss_train_freeze/qros-tss-train-freeze-review/"
```

- [ ] **Step 2: Create `.claude-plugin/plugin.json`**

Use the generated skills array from Step 1 and this metadata:

```json
{
  "name": "qros",
  "version": "0.4.4",
  "description": "Preview QROS skills for Claude Code. Discovery only; full workflow still requires active research repo ./.qros bootstrap and Codex remains the fully supported review-subagent host until host-neutral review is implemented.",
  "author": {
    "name": "web3qt"
  },
  "homepage": "https://github.com/web3qt/quant-research-os/blob/main/docs/guides/installation.md",
  "repository": "https://github.com/web3qt/quant-research-os",
  "license": "UNLICENSED",
  "keywords": [
    "quant",
    "research",
    "qros",
    "workflow",
    "governance"
  ],
  "skills": []
}
```

Replace the empty `skills` array with the generated array.

- [ ] **Step 3: Create `.claude-plugin/marketplace.json`**

Create this exact file:

```json
{
  "name": "quant-research-os",
  "owner": {
    "name": "web3qt"
  },
  "metadata": {
    "description": "QROS Claude Code plugin preview marketplace.",
    "version": "0.1.0"
  },
  "plugins": [
    {
      "name": "qros",
      "source": "./",
      "description": "Preview QROS skills for Claude Code. Discovery only; full workflow still requires active research repo ./.qros bootstrap.",
      "version": "0.4.4",
      "author": {
        "name": "web3qt"
      },
      "strict": true,
      "category": "quant-research",
      "tags": [
        "quant",
        "research",
        "workflow",
        "governance"
      ]
    }
  ]
}
```

- [ ] **Step 4: Run the focused test and verify only docs still fail**

Run:

```bash
python -m pytest tests/bootstrap/test_claude_plugin_preview.py -q
```

Expected:

```text
FAILED tests/bootstrap/test_claude_plugin_preview.py::test_claude_code_preview_docs_do_not_claim_full_support
```

The manifest and marketplace tests should pass.

- [ ] **Step 5: Checkpoint**

Do not commit unless the user explicitly authorizes commits.

## Task 3: Document Claude Code Preview Install Path

**Files:**
- Modify: `docs/guides/installation.md`
- Optional modify: `README.md`
- Test: `tests/bootstrap/test_claude_plugin_preview.py`
- Existing test: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Add a supported-hosts clarification**

In `docs/guides/installation.md`, change:

```markdown
当前版本支持：

- `Codex`
```

to:

```markdown
当前版本支持：

- `Codex`：完整支持，当前主路径
- `Claude Code preview`：仅支持 plugin discovery preview；完整 workflow 仍需要后续 repo bootstrap 与 host-neutral review
```

- [ ] **Step 2: Add a Claude Code preview section after the Codex recommended path**

Insert this section after the paragraph that says Codex will initialize the current research repo runtime:

```markdown
## Claude Code preview

Claude Code preview 参考 `superpowers` 的 plugin marketplace 方式，只解决 QROS skill discovery，不等于完整 workflow ready。

在 Claude Code 中可以先添加 marketplace：

```text
/plugin marketplace add web3qt/quant-research-os
```

然后安装 preview plugin：

```text
/plugin install qros@quant-research-os
```

安装后，Claude Code 会以 plugin namespace 暴露 QROS skills。Plugin install 不等于 QROS workflow ready：当前 active research repo 仍然需要 `./.qros/bin` repo-local runtime 才能运行 `qros-session`、`qros-progress` 和 `qros-review`。

Codex remains the fully supported host for review-subagent orchestration until host-neutral review is implemented.

当前不要把 Claude Code preview 解释为完整 review flow 支持：

- preview 会让 Claude Code 发现 QROS skill 入口
- preview 不会自动初始化每个 research repo 的 `./.qros/`
- preview 不会把 Codex-only `spawn_agent` review 流转换成 Claude subagent review 流
- 完整 Claude Code workflow 需要后续 `claude-repo-bootstrap` 和 `host-neutral-review`
```

- [ ] **Step 3: Keep Codex install wording unchanged**

Verify the file still contains:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

and:

```text
Restart Codex
```

Do not rename the existing `Codex 用户推荐路径` section.

- [ ] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/bootstrap/test_claude_plugin_preview.py tests/docs/test_install_docs.py -q
```

Expected:

```text
6 passed
```

The exact count may be higher if existing docs tests change, but all selected tests must pass.

- [ ] **Step 5: Checkpoint**

Do not commit unless the user explicitly authorizes commits.

## Task 4: Run Required Verification

**Files:**
- No file edits.

- [ ] **Step 1: Run docs/bootstrap minimal checks**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py tests/bootstrap/test_claude_plugin_preview.py
```

Expected:

```text
passed
```

- [ ] **Step 2: Explain why smoke/full-smoke are not required**

Record this in the final implementation report:

```text
This change only adds Claude Code preview plugin metadata and install documentation. It does not modify runtime helpers, workflow contracts, stage gates, review orchestration, route split logic, anti-drift snapshots, canonical session naming, stage-display contracts, or lineage-local stage-program seams. Therefore focused tests plus docs/bootstrap checks satisfy the repository rules; smoke and full-smoke were not run.
```

- [ ] **Step 3: Check git diff**

Run:

```bash
git diff -- .claude-plugin/plugin.json .claude-plugin/marketplace.json docs/guides/installation.md tests/bootstrap/test_claude_plugin_preview.py
```

Expected:

```text
Diff contains only plugin preview manifests, preview docs, and preview tests.
```

- [ ] **Step 4: Final report**

Include:

```text
Changed:
- .claude-plugin/plugin.json
- .claude-plugin/marketplace.json
- docs/guides/installation.md
- tests/bootstrap/test_claude_plugin_preview.py

Verification:
- python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py tests/bootstrap/test_claude_plugin_preview.py

Not run:
- smoke
- full-smoke

Reason:
- Plugin preview/docs only; no runtime or workflow contract changes.
```

Do not say "Claude Code is fully supported." Say "Claude Code plugin preview discovery is supported."

---

# Phase 2: `claude-repo-bootstrap`

> **Goal:** Let Claude Code users initialize and refresh `./.qros` runtime in active research repos, without changing the Codex-first path.

**Architecture:** Extend `install_runtime.py` from hard-coded `codex` host to host profiles. Split global metadata roots by host. Make the update flow host-aware. Keep Codex install behavior unchanged.

**Scope boundary:** Do NOT implement Phase 3 `host-neutral-review`. Do NOT modify review closure, receipt schemas, or review skills. Do NOT change stage flow or gate semantics.

## Task 5: Add Failing Tests For Claude Repo Bootstrap

**Files:**
- Create: `tests/bootstrap/test_claude_repo_bootstrap.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/bootstrap/test_claude_repo_bootstrap.py` with:

```python
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from runtime.tools.install_runtime import (
    InstallError,
    SUPPORTED_HOSTS,
    check_install,
    install_qros,
    resolve_install_target,
)
from runtime.tools.update_runtime import global_manifest_path, run_qros_update


def test_supported_hosts_includes_claude_code() -> None:
    assert "claude-code" in SUPPORTED_HOSTS
    assert "codex" in SUPPORTED_HOSTS


def test_claude_code_repo_local_install_writes_runtime_locally_and_global_skills_under_claude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(
        repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local", host="claude-code"
    )

    assert result.mode == "repo-local"
    assert (install_root / ".qros").exists()
    assert (install_root / ".qros" / "bin" / "qros-session").exists()
    assert (install_root / ".qros" / "bin" / "qros-progress").exists()
    assert not (install_root / ".qros" / "tools").exists()

    assert (home_root / ".claude" / "skills").exists()
    assert (home_root / ".claude" / "skills" / "qros-progress" / "SKILL.md").exists()
    assert (home_root / ".claude" / "skills" / "qros-research-session" / "SKILL.md").exists()

    assert not (home_root / ".codex" / "skills").exists()

    manifest_path = install_root / ".qros" / "install-manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["host"] == "claude-code"
    assert manifest["install_mode"] == "repo-local"
    assert "qros-progress" in manifest["installed_skills"]


def test_claude_code_user_global_install_writes_skills_under_claude_and_manifest_under_claude_qros(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(
        repo_root=repo_root, cwd=cwd, home=home_root, mode="user-global", host="claude-code"
    )

    assert result.mode == "user-global"
    assert (home_root / ".claude" / "skills").exists()
    assert (home_root / ".claude" / "skills" / "qros-research-session" / "SKILL.md").exists()
    assert (home_root / ".claude" / "qros").exists()
    assert (home_root / ".claude" / "qros" / "install-manifest.json").exists()
    assert not (home_root / ".codex" / "skills").exists()
    assert not (home_root / ".codex" / "qros").exists()


def test_claude_code_check_install_reports_host_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(
        repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local", host="claude-code"
    )

    ok, messages = check_install(
        repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local", host="codex"
    )
    assert ok is False
    assert any("host mismatch" in m for m in messages)


def test_claude_code_manifest_writes_host_claude_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(
        repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local", host="claude-code"
    )

    manifest = json.loads(
        (install_root / ".qros" / "install-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["host"] == "claude-code"
    assert manifest["install_mode"] == "repo-local"


def test_codex_install_behavior_unchanged_after_claude_code_host_added(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(
        repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local", host="codex"
    )

    assert result.mode == "repo-local"
    assert (home_root / ".codex" / "skills").exists()
    assert (home_root / ".codex" / "skills" / "qros-progress" / "SKILL.md").exists()
    manifest = json.loads(
        (install_root / ".qros" / "install-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["host"] == "codex"


def test_global_manifest_path_respects_host() -> None:
    home = Path("/home/user")
    assert global_manifest_path(home, host="codex") == home / ".codex" / "qros" / "install-manifest.json"
    assert global_manifest_path(home, host="claude-code") == home / ".claude" / "qros" / "install-manifest.json"


def test_claude_code_update_refreshes_claude_global_and_repo_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_qros_update_script import _init_origin_repo, _clone_managed_repo

    _, origin_repo = _init_origin_repo(tmp_path)
    managed_repo = tmp_path / "managed-repo"
    _clone_managed_repo(origin_repo, managed_repo)

    home_root = tmp_path / "home"
    home_root.mkdir()
    target_cwd = tmp_path / "research-project"
    target_cwd.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = run_qros_update(
        target_cwd=target_cwd,
        home=home_root,
        explicit_source_repo=managed_repo,
        repo_root_fallback=managed_repo,
        repo_url=str(origin_repo),
        host="claude-code",
    )

    assert result.source_repo == managed_repo.resolve()
    assert (home_root / ".claude" / "qros" / "install-manifest.json").exists()
    assert (home_root / ".claude" / "skills" / "qros-update" / "SKILL.md").exists()
    assert (target_cwd / ".qros" / "install-manifest.json").exists()
    assert (target_cwd / ".qros" / "bin" / "qros-update").exists()
    assert result.source_git_commit

    local_manifest = json.loads(
        (target_cwd / ".qros" / "install-manifest.json").read_text(encoding="utf-8")
    )
    assert local_manifest["host"] == "claude-code"

    assert not (home_root / ".codex" / "skills").exists()
    assert not (home_root / ".codex" / "qros").exists()


def test_install_runtime_rejects_unknown_host() -> None:
    with pytest.raises(InstallError, match="unsupported host"):
        install_qros(
            repo_root=Path.cwd(),
            cwd=Path.cwd(),
            home=Path.home(),
            mode="repo-local",
            host="gemini-cli",
        )
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
python -m pytest tests/bootstrap/test_claude_repo_bootstrap.py -q
```

Expected:

```text
FAILED tests/bootstrap/test_claude_repo_bootstrap.py::test_supported_hosts_includes_claude_code
```

The failure should be caused by `"claude-code"` not yet being in `SUPPORTED_HOSTS`.

- [ ] **Step 3: Checkpoint**

Do not commit unless the user explicitly authorizes commits.

## Task 6: Extend install_runtime.py For Claude Code Host

**Files:**
- Modify: `runtime/tools/install_runtime.py`

- [ ] **Step 1: Add host-to-metadata-root mapping**

Replace the hard-coded `GLOBAL_METADATA_ROOT` with a host-aware mapping:

```python
InstallHost = Literal["codex", "claude-code"]

SUPPORTED_HOSTS: set[str] = {"codex", "claude-code"}
SUPPORTED_MODES: set[str] = {"repo-local", "user-global", "auto"}
SKILLS_SOURCE_DIR = Path("skills")

_HOST_METADATA_DIR: dict[str, str] = {
    "codex": ".codex",
    "claude-code": ".claude",
}

_HOST_SKILLS_DIR: dict[str, str] = {
    "codex": ".codex",
    "claude-code": ".claude",
}
```

- [ ] **Step 2: Make `resolve_install_target` host-aware**

Update `resolve_install_target` to accept a `host` parameter and route skill/global-metadata roots by host:

```python
def resolve_install_target(mode: str, cwd: Path, home: Path, host: str = "codex") -> InstallTarget:
    resolved_mode = resolve_install_mode(mode, cwd)
    skills_dir = _HOST_SKILLS_DIR[host]
    metadata_dir = _HOST_METADATA_DIR[host]

    if resolved_mode == "repo-local":
        runtime_root = cwd / ".qros"
        return InstallTarget(
            mode=resolved_mode,
            skills_root=home / skills_dir / "skills",
            runtime_root=runtime_root,
            manifest_path=runtime_root / "install-manifest.json",
        )

    runtime_root = home / metadata_dir / "qros"
    return InstallTarget(
        mode=resolved_mode,
        skills_root=home / skills_dir / "skills",
        runtime_root=runtime_root,
        manifest_path=runtime_root / "install-manifest.json",
    )
```

- [ ] **Step 3: Update `install_qros` to pass host through**

In `install_qros`, pass `host` to `resolve_install_target`:

```python
def install_qros(
    repo_root: Path,
    cwd: Path,
    home: Path,
    mode: str,
    host: str = "codex",
) -> InstallResult:
    _validate_host(host)
    repo_root = repo_root.resolve()
    target = resolve_install_target(mode=mode, cwd=cwd.resolve(), home=home.resolve(), host=host)
    ...
```

- [ ] **Step 4: Update `build_manifest` to record actual host**

Change the hard-coded `"host": "codex"` in `build_manifest` to use the passed host value:

```python
def build_manifest(
    *,
    repo_root: Path,
    target: InstallTarget,
    installed_skills: list[str],
    installed_runtime_files: list[str],
    host: str = "codex",
) -> dict[str, object]:
    return {
        "project_name": repo_root.name,
        "host": host,
        ...
    }
```

Then update the call site in `install_qros` to pass `host=host`.

- [ ] **Step 5: Update `check_install` to pass host through to `resolve_install_target`**

Already accepts `host` parameter - verify it passes through to `resolve_install_target`:

```python
target = resolve_install_target(mode=mode, cwd=cwd.resolve(), home=home.resolve(), host=host)
```

- [ ] **Step 6: Update the `main()` CLI parser description**

Change the argparse description from `"Install QROS runtime assets for Codex."` to `"Install QROS runtime assets."` and ensure `--host` accepts both values.

- [ ] **Step 7: Run focused tests for Task 6**

Run:

```bash
python -m pytest tests/bootstrap/test_claude_repo_bootstrap.py tests/bootstrap/test_install_runtime.py -q
```

Expected: All Task 6 tests pass. Existing install_runtime tests continue to pass with host=codex default.

- [ ] **Step 8: Checkpoint**

Do not commit unless the user explicitly authorizes commits.

## Task 7: Extend update_runtime.py For Host Awareness

**Files:**
- Modify: `runtime/tools/update_runtime.py`
- Modify: `runtime/scripts/run_qros_update.py`
- Modify: `runtime/bin/qros-update`
- Modify: `skills/core/qros-update/SKILL.md`

- [ ] **Step 1: Make `global_manifest_path` host-aware**

Update the function signature to accept a `host` parameter:

```python
def global_manifest_path(home: Path, host: str = "codex") -> Path:
    metadata_dir = ".claude" if host == "claude-code" else ".codex"
    return home / metadata_dir / "qros" / "install-manifest.json"
```

- [ ] **Step 2: Make `run_qros_update` host-aware**

Add a `host` parameter and thread it through to `install_qros`, `check_install`, and `global_manifest_path`:

```python
def run_qros_update(
    *,
    target_cwd: Path,
    home: Path,
    explicit_source_repo: Path | None = None,
    repo_root_fallback: Path | None = None,
    repo_url: str = DEFAULT_REPO_URL,
    branch: str = DEFAULT_BRANCH,
    host: str = "codex",
) -> UpdateResult:
    ...
    install_qros(
        repo_root=updated_repo,
        cwd=updated_repo,
        home=home,
        mode="user-global",
        host=host,
    )
    install_qros(
        repo_root=updated_repo,
        cwd=resolved_target_cwd,
        home=home,
        mode="repo-local",
        host=host,
    )
    ...
    return UpdateResult(
        ...
        global_manifest_path=global_manifest_path(home, host=host),
        ...
    )
```

- [ ] **Step 3: Add `--host` flag to `run_qros_update.py` CLI**

```python
parser.add_argument("--host", default="codex", choices=["codex", "claude-code"])
```

And pass `host=args.host` through to `run_qros_update`.

- [ ] **Step 4: Add `--host` passthrough to `runtime/bin/qros-update` wrapper**

Add host argument parsing to the shell wrapper so `--host claude-code` is forwarded:

```bash
HOST="codex"
# ... in argument parsing loop:
    --host)
      HOST="$2"
      shift 2
      ;;

# ... in the exec line:
exec "$PYTHON_BIN" "$RUNTIME_ROOT/scripts/run_qros_update.py" --cwd "$TARGET_CWD" --host "$HOST" "${ARGS[@]}"
```

- [ ] **Step 5: Update `qros-update` skill for host awareness**

In `skills/core/qros-update/SKILL.md`, replace Codex-only wording with host-aware sections:

- Add a "Host awareness" paragraph that explains the difference between Codex and Claude Code update behavior.
- For Codex: refresh `~/.codex/skills` and current repo-local runtime.
- For Claude Code: refresh `~/.claude/skills` (plugin-managed, so warn that skills installed via plugin must be refreshed via plugin update), and refresh current repo-local runtime.
- Keep existing self-heal expectations and recovery order for Codex path.
- Update the success response template to include host name.

The update to the SKILL.md should add a section like:

```markdown
## Host awareness

This skill is host-aware. The update behavior differs by host:

- **Codex** (`--host codex`, default): Refreshes `~/.codex/skills/` and the current repo's `./.qros/` runtime.
- **Claude Code** (`--host claude-code`): Refreshes `~/.claude/skills/` and the current repo's `./.qros/` runtime. Note: if QROS skills were installed via `/plugin install qros@quant-research-os`, the plugin-managed skill copy takes precedence. Run `/plugin update qros@quant-research-os` to refresh plugin-managed skills, then run this update for repo-local runtime refresh.
```

- [ ] **Step 6: Run focused tests for Task 7**

Run:

```bash
python -m pytest tests/bootstrap/test_claude_repo_bootstrap.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_qros_update_script.py -q
```

Expected: All selected tests pass. Existing update tests continue to pass with host=codex default.

- [ ] **Step 7: Checkpoint**

Do not commit unless the user explicitly authorizes commits.

## Task 8: Document Claude Code Repo Bootstrap Path

**Files:**
- Modify: `docs/guides/installation.md`
- Test: `tests/docs/test_install_docs.py`
- Test: `tests/bootstrap/test_claude_repo_bootstrap.py`

- [ ] **Step 1: Update supported hosts section**

In `docs/guides/installation.md`, update the supported hosts section to include Claude Code repo bootstrap:

Change:
```markdown
当前版本支持：

- `Codex`
```

To:
```markdown
当前版本支持：

- `Codex`：完整支持，当前主路径
- `Claude Code preview`：plugin discovery + repo bootstrap；完整 review workflow 需要 host-neutral review (Phase 3)
```

- [ ] **Step 2: Add Claude Code repo bootstrap section**

After the Claude Code preview section (added in Task 3), insert a new section:

```markdown
## Claude Code repo bootstrap

Claude Code preview 安装 plugin 之后，还需要初始化 active research repo 的 `./.qros` runtime 才能运行 `qros-session`、`qros-progress` 和 `qros-review`。

在 active research repo 根目录运行 repo bootstrap：

```bash
<source_repo>/setup --host claude-code --mode repo-local
```

这会写入：
- `./.qros/bin/*` (wrapper 脚本)
- `./.qros/install-manifest.json` (记录 `host = claude-code`)

Claude Code 的 global skills 存储在 `~/.claude/skills/`，global install manifest 在 `~/.claude/qros/install-manifest.json`。

### 更新

Claude Code 用户更新 QROS runtime：

```bash
<source_repo>/runtime/bin/qros-update --host claude-code --cwd "$PWD"
```

注意：如果 QROS skills 是通过 `/plugin install qros@quant-research-os` 安装的，plugin-managed skills 优先于 `~/.claude/skills/` 下的文件。需要同时运行：
- `/plugin update qros@quant-research-os` (刷新 plugin-managed skills)
- `qros-update --host claude-code` (刷新 repo-local `./.qros/` runtime)

### 检查

检查 Claude Code 安装状态：

```bash
ls ~/.claude/skills | grep qros-
test -f ~/.claude/qros/install-manifest.json
test -d ./.qros
```

或使用 setup 检查：

```bash
<source_repo>/setup --host claude-code --mode repo-local --check
```
```

- [ ] **Step 3: Verify Codex docs remain unchanged**

The existing Codex sections (`Codex 用户推荐路径`, installation layout, update, check) must remain intact with Codex-specific paths (`~/.codex/skills`, `Restart Codex`).

Run the existing docs tests to verify:

```bash
python -m pytest tests/docs/test_install_docs.py -q
```

- [ ] **Step 4: Update docs test for new Claude Code bootstrap content**

In `tests/docs/test_install_docs.py`, add assertions for the new Claude Code bootstrap docs content. Add a new test or extend an existing one:

```python
def test_claude_code_bootstrap_docs_present() -> None:
    installation = Path("docs/guides/installation.md").read_text(encoding="utf-8")

    assert "Claude Code repo bootstrap" in installation
    assert "--host claude-code --mode repo-local" in installation
    assert "~/.claude/skills" in installation
    assert "~/.claude/qros/install-manifest.json" in installation
    assert "--host claude-code --cwd" in installation
    assert "host = claude-code" in installation
    assert "Claude Code preview" in installation
    # Codex paths still present
    assert "~/.codex/skills" in installation
    assert "Restart Codex" in installation
```

- [ ] **Step 5: Run all relevant tests**

Run:

```bash
python -m pytest tests/bootstrap/test_claude_repo_bootstrap.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_qros_update_script.py tests/docs/test_install_docs.py -q
```

Expected: All tests pass.

- [ ] **Step 6: Checkpoint**

Do not commit unless the user explicitly authorizes commits.

## Task 9: Run Required Verification

**Files:**
- No file edits.

- [ ] **Step 1: Run focused + docs/bootstrap checks**

Run:

```bash
python -m pytest tests/bootstrap/test_claude_repo_bootstrap.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_qros_update_script.py tests/bootstrap/test_project_bootstrap.py tests/bootstrap/test_claude_plugin_preview.py tests/docs/test_install_docs.py tests/contracts/test_agents_layout.py
```

Expected:

```text
all passed
```

- [ ] **Step 2: Run smoke tests**

Phase 2 touches install/runtime workflow (`install_runtime.py`, `update_runtime.py`, `qros-update` wrapper). Run smoke:

```bash
python -m pytest tests/bootstrap/test_native_install_smoke.py -q
```

Expected: All smoke tests pass.

- [ ] **Step 3: Evaluate full-smoke necessity**

If smoke passes and the change scope is limited to:
- Host-aware install routing (new `claude-code` path, default `codex` unchanged)
- Host-aware update (new `--host` flag, default `codex` unchanged)
- Docs additions (no Codex wording removal)

Then full-smoke may be skipped with justification. If any stage flow, gate semantics, or review orchestration code paths changed, run full-smoke.

- [ ] **Step 4: Check git diff**

Run:

```bash
git diff -- runtime/tools/install_runtime.py runtime/tools/update_runtime.py runtime/scripts/run_qros_update.py runtime/bin/qros-update skills/core/qros-update/SKILL.md docs/guides/installation.md tests/bootstrap/test_claude_repo_bootstrap.py tests/docs/test_install_docs.py
```

Expected:

```text
Diff contains only:
- Host-aware install_runtime (claude-code host, backward-compatible codex default)
- Host-aware update_runtime (--host flag, backward-compatible codex default)
- Host-aware qros-update wrapper (--host passthrough)
- Updated qros-update skill (host awareness section)
- Claude Code bootstrap docs
- Claude repo bootstrap tests
- Updated install docs tests
```

- [ ] **Step 5: Final report**

Include:

```text
Changed:
- runtime/tools/install_runtime.py (host-aware: codex + claude-code)
- runtime/tools/update_runtime.py (host-aware update)
- runtime/scripts/run_qros_update.py (--host flag)
- runtime/bin/qros-update (--host passthrough)
- skills/core/qros-update/SKILL.md (host awareness section)
- docs/guides/installation.md (Claude Code repo bootstrap section)
- tests/bootstrap/test_claude_repo_bootstrap.py (new)
- tests/docs/test_install_docs.py (Claude Code bootstrap assertions)

Verification:
- python -m pytest tests/bootstrap/test_claude_repo_bootstrap.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_qros_update_script.py tests/bootstrap/test_project_bootstrap.py tests/bootstrap/test_claude_plugin_preview.py tests/docs/test_install_docs.py tests/contracts/test_agents_layout.py
- python -m pytest tests/bootstrap/test_native_install_smoke.py

Not run:
- full-smoke (if smoke passes and scope is limited to host-aware routing)

Reason:
- Phase 2 adds claude-code host profile alongside existing codex profile. All code paths default to codex when host is not specified. No review orchestration, artifact contract, stage gate, or receipt schema changes.
```

Do not say "Claude Code is fully supported." Say "Claude Code plugin preview discovery and repo bootstrap are supported. Full review workflow requires Phase 3 host-neutral-review."

---

## Self-Review

### Phase 1 spec coverage:

- Phase 1 plugin manifest: covered by Task 2.
- Phase 1 marketplace: covered by Task 2.
- Nested skill path coverage: covered by Task 1 and Task 2.
- Preview docs: covered by Task 3.
- Codex path preserved: covered by Task 3 and existing install docs tests.
- No Phase 2/3 claims: covered by Task 1 docs assertions and final report guidance.

### Phase 2 spec coverage:

- Host-aware install (`claude-code` added to `SUPPORTED_HOSTS`): covered by Task 6.
- Separate global metadata roots (`~/.codex/` vs `~/.claude/`): covered by Task 6.
- Claude repo-local install writes `./.qros/bin/*`: covered by Task 5 and Task 6.
- Claude manifest writes `host = claude-code`: covered by Task 5 and Task 6.
- Host-aware update (`run_qros_update` host parameter): covered by Task 7.
- `qros-update` becomes host-aware (CLI, wrapper, skill): covered by Task 7.
- Codex install/update unchanged: covered by Task 5 (`test_codex_install_behavior_unchanged`) and existing tests.
- Claude Code bootstrap docs: covered by Task 8.
- No Phase 3 review changes: enforced by scope boundary.

### Quality checks:

No placeholders:

- No step uses TBD, TODO, or "implement later".
- Plugin JSON metadata is specified.
- Host mappings are explicit.
- Test code is complete.
- Verification commands are exact.

Type consistency:

- Plugin name is consistently `qros`.
- Marketplace name is consistently `quant-research-os`.
- Version is consistently `0.4.4`, matching `pyproject.toml`.
- Host literal: `codex` | `claude-code` in `InstallHost`.
- Host flags: `--host codex` (default), `--host claude-code`.

### Backward compatibility:

- All `install_qros` calls default to `host="codex"` when not specified.
- All `run_qros_update` calls default to `host="codex"` when not specified.
- All `resolve_install_target` calls default to `host="codex"` when not specified.
- Existing Codex tests pass without modification.
- Existing docs references to `~/.codex/skills` and `Restart Codex` remain intact.
- `GLOBAL_METADATA_ROOT` constant removed in favor of `_HOST_METADATA_DIR` dict; callers use the host-aware `resolve_install_target` which already resolved the correct path.
