from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from runtime.tools.install_runtime import SUPPORTED_HOSTS, check_install, install_qros


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
    host: str


def global_manifest_path(home: Path, host: str = "codex") -> Path:
    host_dir = ".claude" if host == "claude-code" else ".codex"
    return home / host_dir / "qros" / "install-manifest.json"


def default_source_repo(home: Path) -> Path:
    return home / "workspace" / "quant-research-os"


def resolve_update_host(
    requested_host: str | None = "auto",
    *,
    target_cwd: Path,
    environ: Mapping[str, str] | None = None,
    legacy_default_host: bool = False,
) -> str:
    """解析 qros-update 的目标 host。

    显式 `--host` 优先；`auto` 依次读取 QROS_HOST、repo-local manifest、当前 agent 环境。
    旧版 qros-update wrapper 会无条件传 `--host codex`，这里把它作为兼容默认值重走 auto。
    """

    legacy_codex_default = legacy_default_host and requested_host == "codex"
    if requested_host in SUPPORTED_HOSTS and not legacy_codex_default:
        return str(requested_host)
    if requested_host not in (None, "", "auto") and not legacy_codex_default:
        raise UpdateError(f"unsupported host: {requested_host}")

    env = os.environ if environ is None else environ
    env_host = _normalize_host(env.get("QROS_HOST"))
    if env_host is not None:
        return env_host

    local_host = _host_from_manifest(target_cwd / ".qros" / "install-manifest.json")
    if local_host is not None:
        return local_host

    if _looks_like_claude_code(env):
        return "claude-code"
    if _looks_like_codex(env):
        return "codex"
    return "codex"


def resolve_source_repo(
    *,
    explicit_source_repo: Path | None,
    home: Path,
    repo_root_fallback: Path | None,
    host: str = "codex",
) -> Path:
    if explicit_source_repo is not None:
        return explicit_source_repo.resolve()

    manifest_repo = _source_repo_from_manifest(global_manifest_path(home, host=host))
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
    host: str = "auto",
    legacy_default_host: bool = False,
) -> UpdateResult:
    resolved_target_cwd = target_cwd.resolve()
    resolved_host = resolve_update_host(
        host,
        target_cwd=resolved_target_cwd,
        legacy_default_host=legacy_default_host,
    )
    source_repo = resolve_source_repo(
        explicit_source_repo=explicit_source_repo,
        home=home,
        repo_root_fallback=repo_root_fallback,
        host=resolved_host,
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
        host=resolved_host,
    )
    install_qros(
        repo_root=updated_repo,
        cwd=resolved_target_cwd,
        home=home,
        mode="repo-local",
        host=resolved_host,
    )

    global_ok, global_messages = check_install(
        repo_root=updated_repo,
        cwd=updated_repo,
        home=home,
        mode="user-global",
        host=resolved_host,
    )
    local_ok, local_messages = check_install(
        repo_root=updated_repo,
        cwd=resolved_target_cwd,
        home=home,
        mode="repo-local",
        host=resolved_host,
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
        global_manifest_path=global_manifest_path(home, host=resolved_host),
        local_manifest_path=resolved_target_cwd / ".qros" / "install-manifest.json",
        host=resolved_host,
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


def _host_from_manifest(manifest_path: Path) -> str | None:
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return _normalize_host(payload.get("host"))


def _normalize_host(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("_", "-")
    if normalized in SUPPORTED_HOSTS:
        return normalized
    return None


def _looks_like_claude_code(environ: Mapping[str, str]) -> bool:
    return any(
        environ.get(name)
        for name in (
            "CLAUDECODE",
            "CLAUDE_CODE",
            "CLAUDECODE_CWD",
            "CLAUDE_CODE_ENTRYPOINT",
            "CLAUDE_CODE_SSE_PORT",
        )
    )


def _looks_like_codex(environ: Mapping[str, str]) -> bool:
    return any(
        environ.get(name)
        for name in (
            "CODEX_THREAD_ID",
            "CODEX_SANDBOX",
            "CODEX_CI",
            "CODEX_MANAGED_BY_NPM",
        )
    )


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
