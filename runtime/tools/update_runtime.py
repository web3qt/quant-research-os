from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from runtime.tools.install_runtime import check_install, install_qros


DEFAULT_BRANCH = "main"
DEFAULT_REPO_URL = "https://github.com/web3qt/quant-research-os.git"


class UpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class UpdateResult:
    source_repo: Path
    target_cwd: Path
    source_git_commit: str
    global_manifest_path: Path
    local_manifest_path: Path


def global_manifest_path(home: Path) -> Path:
    return home / ".codex" / "qros" / "install-manifest.json"


def default_source_repo(home: Path) -> Path:
    return home / "workspace" / "quant-research-os"


def resolve_source_repo(
    *,
    explicit_source_repo: Path | None,
    home: Path,
    repo_root_fallback: Path | None,
) -> Path:
    if explicit_source_repo is not None:
        return explicit_source_repo.resolve()

    manifest_repo = _source_repo_from_manifest(global_manifest_path(home))
    if manifest_repo is not None and manifest_repo.exists():
        return manifest_repo.resolve()

    if repo_root_fallback is not None and repo_root_fallback.exists():
        return repo_root_fallback.resolve()

    return default_source_repo(home).resolve()


def run_qros_update(
    *,
    target_cwd: Path,
    home: Path,
    explicit_source_repo: Path | None = None,
    repo_root_fallback: Path | None = None,
    repo_url: str = DEFAULT_REPO_URL,
    branch: str = DEFAULT_BRANCH,
) -> UpdateResult:
    resolved_target_cwd = target_cwd.resolve()
    source_repo = resolve_source_repo(
        explicit_source_repo=explicit_source_repo,
        home=home,
        repo_root_fallback=repo_root_fallback,
    )
    updated_repo = ensure_managed_source_repo(
        source_repo=source_repo,
        repo_url=repo_url,
        branch=branch,
    )

    install_qros(
        repo_root=updated_repo,
        cwd=updated_repo,
        home=home,
        mode="user-global",
    )
    install_qros(
        repo_root=updated_repo,
        cwd=resolved_target_cwd,
        home=home,
        mode="repo-local",
    )

    global_ok, global_messages = check_install(
        repo_root=updated_repo,
        cwd=updated_repo,
        home=home,
        mode="user-global",
    )
    local_ok, local_messages = check_install(
        repo_root=updated_repo,
        cwd=resolved_target_cwd,
        home=home,
        mode="repo-local",
    )
    if not global_ok or not local_ok:
        raise UpdateError(
            "\n".join(
                [
                    "QROS update verification failed.",
                    *global_messages,
                    *local_messages,
                ]
            )
        )

    return UpdateResult(
        source_repo=updated_repo,
        target_cwd=resolved_target_cwd,
        source_git_commit=_git_commit(updated_repo),
        global_manifest_path=global_manifest_path(home),
        local_manifest_path=resolved_target_cwd / ".qros" / "install-manifest.json",
    )


def ensure_managed_source_repo(
    *,
    source_repo: Path,
    repo_url: str,
    branch: str,
) -> Path:
    if not source_repo.exists():
        return clone_managed_source_repo(source_repo=source_repo, repo_url=repo_url, branch=branch)

    if not (source_repo / ".git").exists():
        raise UpdateError(f"managed source repo is not a git repository: {source_repo}")

    _ensure_origin_remote(source_repo=source_repo, repo_url=repo_url)
    try:
        _git(source_repo, "fetch", "origin", branch)
        _clean_worktree(source_repo)
        _checkout_branch(source_repo, branch)
        _git(source_repo, "pull", "--ff-only", "origin", branch)
    except UpdateError:
        _git(source_repo, "fetch", "origin", branch)
        _clean_worktree(source_repo)
        _checkout_branch(source_repo, branch)
        _git(source_repo, "reset", "--hard", f"origin/{branch}")
        _git(source_repo, "clean", "-fd")
    return source_repo.resolve()


def clone_managed_source_repo(*, source_repo: Path, repo_url: str, branch: str) -> Path:
    source_repo.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["git", "clone", "--branch", branch, repo_url, str(source_repo)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise UpdateError(_format_git_error(completed, source_repo))
    return source_repo.resolve()


def _source_repo_from_manifest(manifest_path: Path) -> Path | None:
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    source_repo_path = payload.get("source_repo_path")
    if not isinstance(source_repo_path, str) or not source_repo_path.strip():
        return None
    return Path(source_repo_path).expanduser()


def _ensure_origin_remote(*, source_repo: Path, repo_url: str) -> None:
    current = subprocess.run(
        ["git", "-C", str(source_repo), "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True,
    )
    if current.returncode == 0:
        if current.stdout.strip() != repo_url:
            _git(source_repo, "remote", "set-url", "origin", repo_url)
        return
    _git(source_repo, "remote", "add", "origin", repo_url)


def _checkout_branch(source_repo: Path, branch: str) -> None:
    existing = subprocess.run(
        ["git", "-C", str(source_repo), "show-ref", "--verify", f"refs/heads/{branch}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if existing.returncode == 0:
        _git(source_repo, "checkout", branch)
        return
    _git(source_repo, "checkout", "-b", branch, f"origin/{branch}")


def _clean_worktree(source_repo: Path) -> None:
    _git(source_repo, "reset", "--hard")
    _git(source_repo, "clean", "-fd")


def _git_commit(source_repo: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source_repo), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _git(source_repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source_repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise UpdateError(_format_git_error(completed, source_repo))
    return completed.stdout.strip()


def _format_git_error(completed: subprocess.CompletedProcess[str], source_repo: Path) -> str:
    detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
    return f"git update failed for {source_repo}: {detail}"
