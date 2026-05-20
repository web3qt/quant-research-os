# QROS Update Stable Tag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change `qros-update` so the default update path resolves to the latest stable tag, while keeping `qros-update main` as the explicit developer path and preserving exact tag/SHA update modes.

**Architecture:** Replace the updater’s branch-first model with a target-first model. Parse an optional positional target into one of `stable`, `main`, `tag`, or `ref`; resolve that to a concrete git ref; update the managed source repo according to the target mode; and extend install manifests so they record update channel/tag/ref provenance in addition to the existing commit-based provenance.

**Tech Stack:** Python 3.13, git CLI, existing QROS install/update runtime under `runtime/tools/`, wrapper/CLI code under `runtime/scripts/` and `runtime/bin/`, manifest logic in `runtime/tools/install_runtime.py`, and pytest-based bootstrap/docs tests.

---

## File Structure

- Modify `runtime/tools/update_runtime.py`
  - Introduce target resolution for `stable`, `main`, `tag`, `ref`.
  - Replace default-branch semantics with target-first semantics.
  - Implement stable semver tag selection and target-specific managed-repo update flows.
- Modify `runtime/scripts/run_qros_update.py`
  - Replace branch-first CLI with positional target parsing while keeping legacy `--branch` compatibility.
- Modify `runtime/tools/install_runtime.py`
  - Extend manifest writing with update-source fields while preserving existing provenance fields.
- Modify docs:
  - `.codex/INSTALL.md`
  - `.claude/INSTALL.md`
  - `docs/guides/installation.md`
  - `docs/README.codex.md`
- Modify tests:
  - `tests/bootstrap/test_qros_update_script.py`
  - `tests/bootstrap/test_claude_repo_bootstrap.py`
  - `tests/bootstrap/test_install_runtime.py`
  - `tests/docs/test_install_docs.py`

## Task 1: Add Update Target Resolution

**Files:**
- Modify: `runtime/tools/update_runtime.py`
- Test: `tests/bootstrap/test_qros_update_script.py`

- [ ] **Step 1: Write the failing target-resolution tests**

Add these tests to `tests/bootstrap/test_qros_update_script.py` near the existing `resolve_update_host(...)` tests:

```python
from runtime.tools.update_runtime import (
    UpdateTarget,
    resolve_update_target,
)


def test_resolve_update_target_defaults_to_stable() -> None:
    target = resolve_update_target(
        target=None,
        available_tags=["v0.4.9", "v0.4.12", "v0.4.11-rc1"],
    )

    assert target.mode == "stable"
    assert target.requested_ref is None
    assert target.resolved_git_ref == "refs/tags/v0.4.12"
    assert target.resolved_git_tag == "v0.4.12"


def test_resolve_update_target_supports_main_tag_and_sha() -> None:
    main_target = resolve_update_target(target="main", available_tags=["v0.4.12"])
    tag_target = resolve_update_target(target="v0.4.12", available_tags=["v0.4.12"])
    sha_target = resolve_update_target(target="abc1234", available_tags=["v0.4.12"])

    assert main_target.mode == "main"
    assert main_target.resolved_git_ref == "origin/main"
    assert tag_target.mode == "tag"
    assert tag_target.resolved_git_ref == "refs/tags/v0.4.12"
    assert sha_target.mode == "ref"
    assert sha_target.resolved_git_ref == "abc1234"


def test_resolve_update_target_rejects_unknown_target() -> None:
    with pytest.raises(UpdateError, match="unsupported update target"):
        resolve_update_target(target="definitely-not-a-tag", available_tags=["v0.4.12"])
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run:

```bash
python -m pytest tests/bootstrap/test_qros_update_script.py::test_resolve_update_target_defaults_to_stable tests/bootstrap/test_qros_update_script.py::test_resolve_update_target_supports_main_tag_and_sha tests/bootstrap/test_qros_update_script.py::test_resolve_update_target_rejects_unknown_target -q
```

Expected: FAIL because `UpdateTarget` and `resolve_update_target(...)` do not exist.

- [ ] **Step 3: Implement the target model**

In `runtime/tools/update_runtime.py`, add:

```python
from typing import Literal


@dataclass(frozen=True)
class UpdateTarget:
    mode: Literal["stable", "main", "tag", "ref"]
    requested_ref: str | None
    resolved_git_ref: str
    resolved_git_tag: str | None
```

Add helpers:

```python
def _looks_like_commit_sha(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", value))


def _stable_semver_tags(tags: list[str]) -> list[tuple[int, int, int, str]]:
    parsed: list[tuple[int, int, int, str]] = []
    for tag in tags:
        match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag)
        if match is None:
            continue
        parsed.append((int(match.group(1)), int(match.group(2)), int(match.group(3)), tag))
    return sorted(parsed)


def resolve_update_target(*, target: str | None, available_tags: list[str]) -> UpdateTarget:
    normalized = (target or "").strip()
    if not normalized:
        stable_tags = _stable_semver_tags(available_tags)
        if not stable_tags:
            raise UpdateError("no stable semver tag is available for qros-update")
        latest = stable_tags[-1][3]
        return UpdateTarget(
            mode="stable",
            requested_ref=None,
            resolved_git_ref=f"refs/tags/{latest}",
            resolved_git_tag=latest,
        )
    if normalized == "main":
        return UpdateTarget(
            mode="main",
            requested_ref="main",
            resolved_git_ref="origin/main",
            resolved_git_tag=None,
        )
    if normalized in available_tags:
        return UpdateTarget(
            mode="tag",
            requested_ref=normalized,
            resolved_git_ref=f"refs/tags/{normalized}",
            resolved_git_tag=normalized,
        )
    if _looks_like_commit_sha(normalized):
        return UpdateTarget(
            mode="ref",
            requested_ref=normalized,
            resolved_git_ref=normalized,
            resolved_git_tag=None,
        )
    raise UpdateError(f"unsupported update target: {normalized}")
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run:

```bash
python -m pytest tests/bootstrap/test_qros_update_script.py::test_resolve_update_target_defaults_to_stable tests/bootstrap/test_qros_update_script.py::test_resolve_update_target_supports_main_tag_and_sha tests/bootstrap/test_qros_update_script.py::test_resolve_update_target_rejects_unknown_target -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/update_runtime.py tests/bootstrap/test_qros_update_script.py
git commit -m "feat: add target-based qros-update resolution"
```

## Task 2: Switch The CLI To Positional Target Parsing

**Files:**
- Modify: `runtime/scripts/run_qros_update.py`
- Test: `tests/bootstrap/test_qros_update_script.py`

- [ ] **Step 1: Write the failing CLI-parse test**

Add this test to `tests/bootstrap/test_qros_update_script.py`:

```python
def test_run_qros_update_parser_accepts_positional_target() -> None:
    parser_result = subprocess.run(
        [
            sys.executable,
            "runtime/scripts/run_qros_update.py",
            "main",
            "--help",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert parser_result.returncode == 0
```

Then add a direct parser-level test if the script exposes `_parse_args(...)` in importable form:

```python
from runtime.scripts.run_qros_update import _parse_args


def test_parse_args_sets_target_and_keeps_legacy_branch_optional(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_qros_update.py", "main"])
    args = _parse_args()

    assert args.target == "main"
    assert args.branch is None
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/bootstrap/test_qros_update_script.py::test_parse_args_sets_target_and_keeps_legacy_branch_optional -q
```

Expected: FAIL because the parser currently only exposes `--branch`.

- [ ] **Step 3: Update the script parser**

In `runtime/scripts/run_qros_update.py`:

```python
parser.add_argument("target", nargs="?", default=None)
parser.add_argument("--branch", default=None, help="Legacy compatibility override. Prefer positional target.")
```

Update description text to:

```python
parser = argparse.ArgumentParser(
    description="Update QROS to the latest stable tag by default, or to an explicit target such as main, a tag, or a commit ref."
)
```

Pass through both values:

```python
result = run_qros_update(
    ...,
    target=args.target,
    branch=args.branch,
    ...
)
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
python -m pytest tests/bootstrap/test_qros_update_script.py::test_parse_args_sets_target_and_keeps_legacy_branch_optional -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/scripts/run_qros_update.py tests/bootstrap/test_qros_update_script.py
git commit -m "refactor: make qros-update use positional target parsing"
```

## Task 3: Make Managed Repo Updates Target-First

**Files:**
- Modify: `runtime/tools/update_runtime.py`
- Test: `tests/bootstrap/test_qros_update_script.py`

- [ ] **Step 1: Write the failing managed-update tests**

Add tests to `tests/bootstrap/test_qros_update_script.py` that verify:

```python
def test_run_qros_update_defaults_to_latest_stable_tag(tmp_path: Path, monkeypatch) -> None:
    source_repo, origin_repo = _init_origin_repo(tmp_path)
    managed_repo = tmp_path / "managed-repo"
    target_cwd = tmp_path / "research-project"
    target_cwd.mkdir()
    _clone_managed_repo(origin_repo, managed_repo)

    _git(["tag", "v0.4.11"], cwd=source_repo)
    _git(["push", "origin", "v0.4.11"], cwd=source_repo)
    (source_repo / "README.md").write_text("stable release\n", encoding="utf-8")
    _git(["add", "README.md"], cwd=source_repo)
    _git(["commit", "-m", "release prep"], cwd=source_repo)
    _git(["tag", "v0.4.12"], cwd=source_repo)
    _git(["push", "origin", "main", "v0.4.12"], cwd=source_repo)

    home_root = tmp_path / "home"
    home_root.mkdir()
    manifest_path = home_root / ".codex" / "qros" / "install-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"source_repo_path": str(managed_repo)}), encoding="utf-8")

    result = run_qros_update(
        target_cwd=target_cwd,
        home=home_root,
        explicit_source_repo=None,
        repo_root_fallback=REPO_ROOT,
        repo_url=str(origin_repo),
        target=None,
        branch=None,
        host="codex",
    )

    assert result.source_git_commit == _git(["rev-list", "-n", "1", "v0.4.12"], cwd=managed_repo)
```

And:

```python
def test_run_qros_update_main_keeps_branch_tracking(tmp_path: Path, monkeypatch) -> None:
    ...
    result = run_qros_update(..., target="main", branch=None, ...)
    assert result.source_git_commit == _git(["rev-parse", "origin/main"], cwd=managed_repo)
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run:

```bash
python -m pytest tests/bootstrap/test_qros_update_script.py::test_run_qros_update_defaults_to_latest_stable_tag tests/bootstrap/test_qros_update_script.py::test_run_qros_update_main_keeps_branch_tracking -q
```

Expected: FAIL because `run_qros_update(...)` is still branch-first and does not accept `target`.

- [ ] **Step 3: Refactor `run_qros_update(...)`**

Change the signature in `runtime/tools/update_runtime.py`:

```python
def run_qros_update(
    *,
    target_cwd: Path,
    home: Path,
    explicit_source_repo: Path | None = None,
    repo_root_fallback: Path | None = None,
    repo_url: str = DEFAULT_REPO_URL,
    target: str | None = None,
    branch: str | None = None,
    host: str = "auto",
    legacy_default_host: bool = False,
    environ: Mapping[str, str] | None = None,
) -> UpdateResult:
```

Add helper flow:

```python
available_tags = _fetch_remote_tags(source_repo, repo_url=repo_url)
requested_target = target or branch
resolved_target = resolve_update_target(target=requested_target, available_tags=available_tags)
updated_repo = ensure_managed_source_repo(
    source_repo=source_repo,
    repo_url=repo_url,
    update_target=resolved_target,
)
```

Refactor `ensure_managed_source_repo(...)` to accept `update_target` instead of `branch`, and branch behavior by target mode:

```python
if update_target.mode == "main":
    _git(source_repo, "fetch", "origin", "main")
    _clean_worktree(source_repo)
    _checkout_branch(source_repo, "main")
    _git(source_repo, "pull", "--ff-only", "origin", "main")
else:
    _git(source_repo, "fetch", "--tags", "origin")
    _git(source_repo, "fetch", "origin")
    _clean_worktree(source_repo)
    _git(source_repo, "checkout", "--detach", update_target.resolved_git_ref)
```

On recovery:

```python
if update_target.mode == "main":
    _git(source_repo, "reset", "--hard", "origin/main")
    _git(source_repo, "clean", "-fd")
else:
    _git(source_repo, "fetch", "--tags", "origin")
    _git(source_repo, "fetch", "origin")
    _git(source_repo, "checkout", "--detach", update_target.resolved_git_ref)
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run:

```bash
python -m pytest tests/bootstrap/test_qros_update_script.py::test_run_qros_update_defaults_to_latest_stable_tag tests/bootstrap/test_qros_update_script.py::test_run_qros_update_main_keeps_branch_tracking -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/update_runtime.py tests/bootstrap/test_qros_update_script.py
git commit -m "feat: make qros-update target first"
```

## Task 4: Extend Install Manifests With Update Provenance

**Files:**
- Modify: `runtime/tools/install_runtime.py`
- Modify: `runtime/tools/update_runtime.py`
- Test: `tests/bootstrap/test_install_runtime.py`

- [ ] **Step 1: Write the failing manifest test**

Add this test to `tests/bootstrap/test_install_runtime.py`:

```python
def test_install_manifest_records_update_channel_and_resolved_ref(tmp_path: Path) -> None:
    runtime_root = tmp_path / ".qros"
    repo_root = tmp_path / "source"
    repo_root.mkdir()
    manifest = install_runtime._build_install_manifest(
        repo_root=repo_root,
        runtime_root=runtime_root,
        host="codex",
        mode="repo-local",
        update_channel="stable",
        requested_ref=None,
        resolved_ref_type="tag",
        resolved_git_ref="refs/tags/v0.4.12",
        resolved_git_tag="v0.4.12",
        runtime_env=RuntimeEnvMetadata(
            python_executable="/tmp/python",
            python_version="3.12.9",
            lock_path="/tmp/uv.lock",
            lock_digest="lock-digest",
        ),
    )

    assert manifest["update_channel"] == "stable"
    assert manifest["resolved_ref_type"] == "tag"
    assert manifest["resolved_git_ref"] == "refs/tags/v0.4.12"
    assert manifest["resolved_git_tag"] == "v0.4.12"
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/bootstrap/test_install_runtime.py::test_install_manifest_records_update_channel_and_resolved_ref -q
```

Expected: FAIL because the manifest builder does not accept these fields.

- [ ] **Step 3: Extend manifest writing**

In `runtime/tools/install_runtime.py`, extend the manifest builder/writer with optional fields:

```python
"update_channel": update_channel,
"requested_ref": requested_ref,
"resolved_ref_type": resolved_ref_type,
"resolved_git_ref": resolved_git_ref,
"resolved_git_tag": resolved_git_tag,
```

Keep old fields intact:

```python
"source_repo_path"
"source_git_commit"
"source_git_dirty"
```

Update `run_qros_update(...)` so the resolved target is passed through when calling `install_qros(...)`.

Compatibility rule:

- missing new fields must not break old manifest readers

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
python -m pytest tests/bootstrap/test_install_runtime.py::test_install_manifest_records_update_channel_and_resolved_ref -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/install_runtime.py runtime/tools/update_runtime.py tests/bootstrap/test_install_runtime.py
git commit -m "feat: record qros-update source provenance"
```

## Task 5: Update Docs And Validate End-To-End

**Files:**
- Modify: `.codex/INSTALL.md`
- Modify: `.claude/INSTALL.md`
- Modify: `docs/guides/installation.md`
- Modify: `docs/README.codex.md`
- Modify: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Write the failing docs tests**

Add assertions to `tests/docs/test_install_docs.py`:

```python
def test_install_docs_describe_stable_default_and_main_developer_path() -> None:
    combined = "\n".join(
        [
            Path(".codex/INSTALL.md").read_text(encoding="utf-8"),
            Path(".claude/INSTALL.md").read_text(encoding="utf-8"),
            Path("docs/guides/installation.md").read_text(encoding="utf-8"),
            Path("docs/README.codex.md").read_text(encoding="utf-8"),
        ]
    )

    assert "qros-update` updates to the latest stable" in combined or "最新稳定版本" in combined
    assert "qros-update main" in combined
    assert "latest published main" not in combined
```

- [ ] **Step 2: Run the focused docs test to verify it fails**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py::test_install_docs_describe_stable_default_and_main_developer_path -q
```

Expected: FAIL because current docs still describe `main` as the ordinary update path.

- [ ] **Step 3: Update the docs**

Change docs to teach:

```text
qros-update
```

as the ordinary stable path, and:

```text
qros-update main
```

as the developer path.

Do not remove advanced usage entirely, but move `qros-update <tag>` / `<sha>` into advanced or recovery wording instead of the main onboarding path.

- [ ] **Step 4: Run docs and updater verification**

Run:

```bash
python -m pytest tests/bootstrap/test_qros_update_script.py tests/bootstrap/test_claude_repo_bootstrap.py tests/bootstrap/test_install_runtime.py tests/docs/test_install_docs.py -q
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .codex/INSTALL.md .claude/INSTALL.md docs/guides/installation.md docs/README.codex.md tests/docs/test_install_docs.py tests/bootstrap/test_qros_update_script.py tests/bootstrap/test_claude_repo_bootstrap.py tests/bootstrap/test_install_runtime.py
git commit -m "docs: make qros-update stable by default"
```

## Spec Coverage Check

- Default `qros-update` -> latest stable tag: covered by Tasks 1 and 3.
- `qros-update main` developer path: covered by Tasks 2 and 3.
- Tag/SHA explicit forms remain supported: covered by Task 1.
- Target-first updater flow: covered by Task 3.
- Manifest extension with update source semantics: covered by Task 4.
- Legacy `--branch main`, old wrappers, old manifests compatibility: covered by Tasks 2 and 4.
- Docs updated from “latest main” to “latest stable”: covered by Task 5.

## Placeholder Scan

- No `TBD`, `TODO`, or deferred placeholders remain.
- Each task includes concrete code, commands, file paths, and expected outcomes.

## Type Consistency Check

- `UpdateTarget` is the single runtime target model throughout the plan.
- `update_channel`, `requested_ref`, `resolved_ref_type`, `resolved_git_ref`, and `resolved_git_tag` are used consistently across manifest and runtime tasks.
- The user-facing CLI model remains `qros-update [target]` throughout the plan.
