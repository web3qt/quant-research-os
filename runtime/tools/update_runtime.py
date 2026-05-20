from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

from runtime.tools.install_runtime import SUPPORTED_HOSTS, check_install, install_qros


DEFAULT_BRANCH = "main"
DEFAULT_REPO_URL = "https://github.com/web3qt/quant-research-os.git"


class UpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class UpdateTarget:
    mode: Literal["stable", "main", "tag", "ref"]
    requested_ref: str | None
    resolved_git_ref: str
    resolved_git_tag: str | None


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


def resolve_update_target(*, target: str | None, available_tags: list[str]) -> UpdateTarget:
    normalized_target = target.strip() if isinstance(target, str) else ""
    if not normalized_target:
        stable_tag = _select_latest_stable_semver_tag(available_tags)
        return UpdateTarget(
            mode="stable",
            requested_ref=None,
            resolved_git_ref=f"refs/tags/{stable_tag}",
            resolved_git_tag=stable_tag,
        )

    if normalized_target == DEFAULT_BRANCH:
        return UpdateTarget(
            mode="main",
            requested_ref=normalized_target,
            resolved_git_ref=f"origin/{DEFAULT_BRANCH}",
            resolved_git_tag=None,
        )

    if normalized_target in available_tags:
        return UpdateTarget(
            mode="tag",
            requested_ref=normalized_target,
            resolved_git_ref=f"refs/tags/{normalized_target}",
            resolved_git_tag=normalized_target,
        )

    if _looks_like_commit_sha(normalized_target):
        return UpdateTarget(
            mode="ref",
            requested_ref=normalized_target,
            resolved_git_ref=normalized_target,
            resolved_git_tag=None,
        )

    raise UpdateError(f"unknown update target: {normalized_target}")


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

    if _looks_like_claude_code(env):
        return "claude-code"
    if _looks_like_codex(env):
        return "codex"

    local_host = _host_from_manifest(target_cwd / ".qros" / "install-manifest.json")
    if local_host is not None:
        return local_host

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
    target: str | None = None,
    branch: str | None = None,
    host: str = "auto",
    legacy_default_host: bool = False,
    environ: Mapping[str, str] | None = None,
) -> UpdateResult:
    resolved_target_cwd = target_cwd.resolve()
    resolved_host = resolve_update_host(
        host,
        target_cwd=resolved_target_cwd,
        environ=environ,
        legacy_default_host=legacy_default_host,
    )
    source_repo = resolve_source_repo(
        explicit_source_repo=explicit_source_repo,
        home=home,
        repo_root_fallback=repo_root_fallback,
        host=resolved_host,
    )
    requested_target = target or branch
    update_target = resolve_update_target(
        target=requested_target,
        available_tags=_available_tags_for_update(source_repo=source_repo, repo_url=repo_url),
    )
    updated_repo = ensure_managed_source_repo(
        source_repo=source_repo,
        repo_url=repo_url,
        update_target=update_target,
    )

    install_qros(
        repo_root=updated_repo,
        cwd=updated_repo,
        home=home,
        mode="user-global",
        host=resolved_host,
        update_channel=update_target.mode,
        requested_ref=update_target.requested_ref,
        resolved_ref_type=_resolved_ref_type(update_target),
        resolved_git_ref=update_target.resolved_git_ref,
        resolved_git_tag=update_target.resolved_git_tag,
    )
    install_qros(
        repo_root=updated_repo,
        cwd=resolved_target_cwd,
        home=home,
        mode="repo-local",
        host=resolved_host,
        update_channel=update_target.mode,
        requested_ref=update_target.requested_ref,
        resolved_ref_type=_resolved_ref_type(update_target),
        resolved_git_ref=update_target.resolved_git_ref,
        resolved_git_tag=update_target.resolved_git_tag,
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
    update_target: UpdateTarget,
) -> Path:
    if not source_repo.exists():
        return clone_managed_source_repo(source_repo=source_repo, repo_url=repo_url, update_target=update_target)

    if not (source_repo / ".git").exists():
        raise UpdateError(f"managed source repo is not a git repository: {source_repo}")

    _ensure_origin_remote(source_repo=source_repo, repo_url=repo_url)
    try:
        _clean_worktree(source_repo)
        _update_managed_repo_to_target(source_repo=source_repo, update_target=update_target)
    except UpdateError:
        _clean_worktree(source_repo)
        _recover_managed_repo_to_target(source_repo=source_repo, update_target=update_target)
    return source_repo.resolve()


def clone_managed_source_repo(*, source_repo: Path, repo_url: str, update_target: UpdateTarget) -> Path:
    source_repo.parent.mkdir(parents=True, exist_ok=True)
    clone_args = ["git", "clone"]
    if update_target.mode == "main":
        clone_args.extend(["--branch", DEFAULT_BRANCH])
    clone_args.extend([repo_url, str(source_repo)])
    completed = subprocess.run(clone_args, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise UpdateError(_format_git_error(completed, source_repo))
    if update_target.mode != "main":
        _update_managed_repo_to_target(source_repo=source_repo, update_target=update_target)
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


def _resolved_ref_type(target: UpdateTarget) -> str:
    if target.mode == "main":
        return "branch"
    if target.mode == "tag":
        return "tag"
    if target.mode == "stable":
        return "tag"
    return "commit"


def _looks_like_commit_sha(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", value))


def _select_latest_stable_semver_tag(available_tags: list[str]) -> str:
    stable_tags = [
        (_parse_stable_semver_tag(tag), tag)
        for tag in available_tags
        if _parse_stable_semver_tag(tag) is not None
    ]
    if not stable_tags:
        raise UpdateError("no stable semver tag available")
    stable_tags.sort(key=lambda item: item[0])
    return stable_tags[-1][1]


def _parse_stable_semver_tag(tag: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", tag.strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


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


def _checkout_detached(source_repo: Path, git_ref: str) -> None:
    _git(source_repo, "checkout", "--detach", git_ref)


def _clean_worktree(source_repo: Path) -> None:
    _git(source_repo, "reset", "--hard")
    _git(source_repo, "clean", "-fd")


def _available_tags_for_update(*, source_repo: Path, repo_url: str) -> list[str]:
    if source_repo.exists() and (source_repo / ".git").exists():
        _ensure_origin_remote(source_repo=source_repo, repo_url=repo_url)
        _git(source_repo, "fetch", "--tags", "origin")
        output = _git(source_repo, "tag", "--list")
        return [line.strip() for line in output.splitlines() if line.strip()]

    completed = subprocess.run(
        ["git", "ls-remote", "--tags", repo_url],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise UpdateError(f"git update failed for {source_repo}: {completed.stderr.strip() or completed.stdout.strip()}")
    tags: list[str] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        _, ref = line.split("\t", 1)
        if ref.endswith("^{}"):
            ref = ref[:-3]
        if ref.startswith("refs/tags/"):
            tag = ref.removeprefix("refs/tags/")
            if tag not in tags:
                tags.append(tag)
    return tags


def _update_managed_repo_to_target(*, source_repo: Path, update_target: UpdateTarget) -> None:
    if update_target.mode == "main":
        _git(source_repo, "fetch", "origin", DEFAULT_BRANCH)
        _checkout_branch(source_repo, DEFAULT_BRANCH)
        _git(source_repo, "pull", "--ff-only", "origin", DEFAULT_BRANCH)
        return

    _git(source_repo, "fetch", "--tags", "origin")
    _git(source_repo, "fetch", "origin")
    _checkout_detached(source_repo, update_target.resolved_git_ref)


def _recover_managed_repo_to_target(*, source_repo: Path, update_target: UpdateTarget) -> None:
    if update_target.mode == "main":
        _git(source_repo, "fetch", "origin", DEFAULT_BRANCH)
        _checkout_branch(source_repo, DEFAULT_BRANCH)
        _git(source_repo, "reset", "--hard", f"origin/{DEFAULT_BRANCH}")
        _git(source_repo, "clean", "-fd")
        return

    _git(source_repo, "fetch", "--tags", "origin")
    _git(source_repo, "fetch", "origin")
    _checkout_detached(source_repo, update_target.resolved_git_ref)


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
