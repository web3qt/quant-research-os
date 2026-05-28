from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from runtime.tools.uv_runtime_env import RuntimeEnvMetadata, UvRuntimeError, ensure_repo_local_uv_runtime


InstallMode = Literal["repo-local", "user-global", "auto"]
ResolvedInstallMode = Literal["repo-local", "user-global"]
InstallHost = Literal["codex", "claude-code"]

SUPPORTED_HOSTS: set[str] = {"codex", "claude-code"}
SUPPORTED_MODES: set[str] = {"repo-local", "user-global", "auto"}
SKILLS_SOURCE_DIR = Path("skills")
RESEARCH_REPO_AGENTS_TEMPLATE = Path("templates/research-repo/AGENTS.md.tmpl")

_HOST_CONFIG: dict[str, str] = {
    "codex": ".codex",
    "claude-code": ".claude",
}


@dataclass(frozen=True)
class RuntimeAsset:
    source_rel: Path
    dest_rel: Path


RUNTIME_ASSETS = (
    RuntimeAsset(Path("runtime/bin"), Path("bin")),
    RuntimeAsset(Path("runtime/scripts"), Path("scripts")),
    RuntimeAsset(Path("runtime/tools"), Path("tools")),
    RuntimeAsset(Path("runtime/hooks"), Path("hooks")),
    RuntimeAsset(Path("templates"), Path("templates")),
    RuntimeAsset(Path("docs/guides"), Path("docs/guides")),
    RuntimeAsset(Path("docs/README.codex.md"), Path("docs/README.codex.md")),
    RuntimeAsset(Path("contracts"), Path("contracts")),
)

REPO_LOCAL_RUNTIME_ASSETS = (
    RuntimeAsset(Path("runtime/bin"), Path("bin")),
)
QROS_INSTALL_LOCK_NAME = ".qros.install.lock"
QROS_STAGING_MARKER_NAME = ".qros-staging.json"
QROS_INSTALL_LOCK_STALE_SECONDS = 60 * 60 * 2


class InstallError(RuntimeError):
    pass


class _RepoLocalInstallLock:
    def __init__(self, parent: Path) -> None:
        self.path = parent / QROS_INSTALL_LOCK_NAME
        self.acquired = False

    def acquire(self) -> None:
        while True:
            try:
                self.path.mkdir()
            except FileExistsError:
                if _qros_install_lock_is_stale(self.path):
                    shutil.rmtree(self.path, ignore_errors=True)
                    continue
                raise InstallError(
                    f"another QROS runtime install is already running for {self.path.parent}. "
                    "Wait for it to finish, then rerun qros-update."
                )
            self.acquired = True
            _write_qros_install_lock_owner(self.path)
            return

    def release(self) -> None:
        if self.acquired and self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)
        self.acquired = False


@dataclass(frozen=True)
class InstallTarget:
    mode: ResolvedInstallMode
    skills_root: Path
    runtime_root: Path
    manifest_path: Path


@dataclass(frozen=True)
class InstallResult:
    mode: ResolvedInstallMode
    skills_written: list[str]
    runtime_written: list[str]
    manifest_path: Path


def resolve_install_mode(mode: str, cwd: Path) -> ResolvedInstallMode:
    if mode not in SUPPORTED_MODES:
        raise InstallError(f"unsupported install mode: {mode}")
    if mode == "auto":
        return "repo-local" if (cwd / "skills").exists() else "user-global"
    return mode


def resolve_install_target(mode: str, cwd: Path, home: Path, host: str = "codex") -> InstallTarget:
    resolved_mode = resolve_install_mode(mode, cwd)
    host_dir = _HOST_CONFIG[host]

    if resolved_mode == "repo-local":
        runtime_root = cwd / ".qros"
        return InstallTarget(
            mode=resolved_mode,
            skills_root=home / host_dir / "skills",
            runtime_root=runtime_root,
            manifest_path=runtime_root / "install-manifest.json",
        )

    runtime_root = home / host_dir / "qros"
    return InstallTarget(
        mode=resolved_mode,
        skills_root=home / host_dir / "skills",
        runtime_root=runtime_root,
        manifest_path=runtime_root / "install-manifest.json",
    )


def list_skill_dirs(repo_root: Path) -> list[Path]:
    skills_root = repo_root / SKILLS_SOURCE_DIR
    if not skills_root.exists():
        raise InstallError(f"missing skills directory: {skills_root}")

    skill_dirs = sorted(
        {
            skill_md.parent
            for skill_md in skills_root.rglob("SKILL.md")
            if skill_md.is_file()
        },
        key=lambda path: str(path.relative_to(skills_root)),
    )
    if not skill_dirs:
        raise InstallError(f"no skill bundles found under {skills_root}")

    seen_names: set[str] = set()
    duplicate_names: set[str] = set()
    for skill_dir in skill_dirs:
        if skill_dir.name in seen_names:
            duplicate_names.add(skill_dir.name)
        seen_names.add(skill_dir.name)
    if duplicate_names:
        duplicates = ", ".join(sorted(duplicate_names))
        raise InstallError(f"duplicate skill bundle names found under {skills_root}: {duplicates}")
    return skill_dirs


def list_runtime_assets(repo_root: Path) -> list[RuntimeAsset]:
    assets: list[RuntimeAsset] = []
    for asset in REPO_LOCAL_RUNTIME_ASSETS:
        source = repo_root / asset.source_rel
        if not source.exists():
            raise InstallError(f"missing runtime asset: {source}")
        assets.append(asset)
    return assets


def build_manifest(
    *,
    repo_root: Path,
    target: InstallTarget,
    installed_skills: list[str],
    installed_runtime_files: list[str],
    runtime_env: RuntimeEnvMetadata | None = None,
    host: str = "codex",
    update_channel: str | None = None,
    requested_ref: str | None = None,
    resolved_ref_type: str | None = None,
    resolved_git_ref: str | None = None,
    resolved_git_tag: str | None = None,
) -> dict[str, object]:
    git_status_short = _git_status_short(repo_root)
    manifest: dict[str, object] = {
        "project_name": repo_root.name,
        "host": host,
        "install_mode": target.mode,
        "installed_at": datetime.now(UTC).isoformat(),
        "source_repo_path": str(repo_root),
        "source_git_commit": _git_commit(repo_root),
        "source_git_dirty": bool(git_status_short.strip()),
        "source_git_status_short": git_status_short.splitlines(),
        "python_executable": _python_executable(),
        "python_version": _python_version(),
        "skills_root": str(target.skills_root),
        "runtime_root": str(target.runtime_root),
        "installed_skills": installed_skills,
        "installed_runtime_files": installed_runtime_files,
        "version_marker": _git_commit(repo_root) or "unknown",
    }
    if runtime_env is not None:
        manifest.update(
            {
                "runtime_python_executable": runtime_env.python_executable,
                "runtime_python_version": runtime_env.python_version,
                "runtime_lock_path": runtime_env.lock_path,
                "runtime_lock_digest": runtime_env.lock_digest,
            }
        )
    if update_channel is not None:
        manifest["update_channel"] = update_channel
    if requested_ref is not None:
        manifest["requested_ref"] = requested_ref
    if resolved_ref_type is not None:
        manifest["resolved_ref_type"] = resolved_ref_type
    if resolved_git_ref is not None:
        manifest["resolved_git_ref"] = resolved_git_ref
    if resolved_git_tag is not None:
        manifest["resolved_git_tag"] = resolved_git_tag
    return manifest


def install_qros(
    repo_root: Path,
    cwd: Path,
    home: Path,
    mode: str,
    host: str = "codex",
    update_channel: str | None = None,
    requested_ref: str | None = None,
    resolved_ref_type: str | None = None,
    resolved_git_ref: str | None = None,
    resolved_git_tag: str | None = None,
) -> InstallResult:
    _validate_host(host)
    repo_root = repo_root.resolve()
    target = resolve_install_target(mode=mode, cwd=cwd.resolve(), home=home.resolve(), host=host)
    skill_dirs = list_skill_dirs(repo_root)
    runtime_assets = list_runtime_assets(repo_root) if target.mode == "repo-local" else []

    target.skills_root.mkdir(parents=True, exist_ok=True)

    skills_written: list[str] = []
    for skill_dir in skill_dirs:
        destination = target.skills_root / skill_dir.name
        if skill_dir.resolve() != destination.resolve():
            _copy_asset(skill_dir, destination)
        skills_written.append(skill_dir.name)

    if target.mode == "repo-local":
        runtime_written = _install_repo_local_runtime(
            repo_root=repo_root,
            target=target,
            runtime_assets=runtime_assets,
            installed_skills=skills_written,
            host=host,
            update_channel=update_channel,
            requested_ref=requested_ref,
            resolved_ref_type=resolved_ref_type,
            resolved_git_ref=resolved_git_ref,
            resolved_git_tag=resolved_git_tag,
        )
        return InstallResult(
            mode=target.mode,
            skills_written=skills_written,
            runtime_written=runtime_written,
            manifest_path=target.manifest_path,
        )

    target.runtime_root.mkdir(parents=True, exist_ok=True)
    runtime_written: list[str] = []

    runtime_env: RuntimeEnvMetadata | None = None
    manifest = build_manifest(
        repo_root=repo_root,
        target=target,
        installed_skills=skills_written,
        installed_runtime_files=sorted(runtime_written),
        runtime_env=runtime_env,
        host=host,
        update_channel=update_channel,
        requested_ref=requested_ref,
        resolved_ref_type=resolved_ref_type,
        resolved_git_ref=resolved_git_ref,
        resolved_git_tag=resolved_git_tag,
    )
    target.manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return InstallResult(
        mode=target.mode,
        skills_written=skills_written,
        runtime_written=sorted(runtime_written),
        manifest_path=target.manifest_path,
    )


def _install_repo_local_runtime(
    *,
    repo_root: Path,
    target: InstallTarget,
    runtime_assets: list[RuntimeAsset],
    installed_skills: list[str],
    host: str,
    update_channel: str | None,
    requested_ref: str | None,
    resolved_ref_type: str | None,
    resolved_git_ref: str | None,
    resolved_git_tag: str | None,
) -> list[str]:
    target.runtime_root.parent.mkdir(parents=True, exist_ok=True)
    install_lock = _RepoLocalInstallLock(target.runtime_root.parent)
    install_lock.acquire()
    try:
        _cleanup_qros_staging_dirs(parent=target.runtime_root.parent, runtime_name=target.runtime_root.name)
        staging_root = Path(
            tempfile.mkdtemp(
                prefix=f"{target.runtime_root.name}.tmp-",
                dir=target.runtime_root.parent,
            )
        ).resolve()
        _write_qros_staging_marker(staging_root)
        staging_target = InstallTarget(
            mode=target.mode,
            skills_root=target.skills_root,
            runtime_root=staging_root,
            manifest_path=staging_root / target.manifest_path.name,
        )

        try:
            runtime_written: list[str] = []
            for asset in runtime_assets:
                source = repo_root / asset.source_rel
                destination = staging_target.runtime_root / asset.dest_rel
                _copy_asset(source, destination)
                runtime_written.extend(_collect_files(destination, root=staging_target.runtime_root))

            try:
                staging_runtime_env = ensure_repo_local_uv_runtime(
                    runtime_root=staging_target.runtime_root, repo_root=repo_root
                )
            except UvRuntimeError as exc:
                raise InstallError(str(exc)) from exc

            runtime_env = _relocate_runtime_env_metadata(
                staging_runtime_env,
                from_root=staging_target.runtime_root,
                to_root=target.runtime_root,
            )
            manifest = build_manifest(
                repo_root=repo_root,
                target=target,
                installed_skills=installed_skills,
                installed_runtime_files=sorted(runtime_written),
                runtime_env=runtime_env,
                host=host,
                update_channel=update_channel,
                requested_ref=requested_ref,
                resolved_ref_type=resolved_ref_type,
                resolved_git_ref=resolved_git_ref,
                resolved_git_tag=resolved_git_tag,
            )
            staging_target.manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            _replace_runtime_root(staging_root=staging_target.runtime_root, final_root=target.runtime_root)
            _ensure_research_repo_agents(repo_root=repo_root, research_repo_root=target.runtime_root.parent)
            return sorted(runtime_written)
        finally:
            if staging_root.exists():
                shutil.rmtree(staging_root)
    finally:
        install_lock.release()


def _write_qros_install_lock_owner(lock_path: Path) -> None:
    (lock_path / "owner.json").write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "created_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _qros_install_lock_is_stale(lock_path: Path) -> bool:
    if time.time() - lock_path.stat().st_mtime > QROS_INSTALL_LOCK_STALE_SECONDS:
        return True

    owner_path = lock_path / "owner.json"
    if not owner_path.exists():
        return False

    try:
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    pid = owner.get("pid")
    return isinstance(pid, int) and not _pid_is_running(pid)


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _cleanup_qros_staging_dirs(*, parent: Path, runtime_name: str) -> None:
    for path in parent.glob(f"{runtime_name}.tmp-*"):
        if not path.is_dir():
            continue
        try:
            shutil.rmtree(path)
        except OSError as exc:
            raise InstallError(f"unable to remove stale QROS staging directory: {path}") from exc


def _write_qros_staging_marker(staging_root: Path) -> None:
    (staging_root / QROS_STAGING_MARKER_NAME).write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "created_at": datetime.now(UTC).isoformat(),
                "purpose": "qros repo-local runtime staging",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _ensure_research_repo_agents(*, repo_root: Path, research_repo_root: Path) -> None:
    destination = research_repo_root / "AGENTS.md"
    if destination.exists():
        return

    source = repo_root / RESEARCH_REPO_AGENTS_TEMPLATE
    if not source.exists():
        raise InstallError(f"missing research repo AGENTS template: {source}")

    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _relocate_runtime_env_metadata(
    metadata: RuntimeEnvMetadata,
    *,
    from_root: Path,
    to_root: Path,
) -> RuntimeEnvMetadata:
    return RuntimeEnvMetadata(
        python_executable=str(_relocate_path(Path(metadata.python_executable), from_root=from_root, to_root=to_root)),
        python_version=metadata.python_version,
        lock_path=str(_relocate_path(Path(metadata.lock_path), from_root=from_root, to_root=to_root)),
        lock_digest=metadata.lock_digest,
    )


def _relocate_path(path: Path, *, from_root: Path, to_root: Path) -> Path:
    try:
        return to_root / path.resolve().relative_to(from_root.resolve())
    except ValueError:
        return path


def _replace_runtime_root(*, staging_root: Path, final_root: Path) -> None:
    backup_root: Path | None = None
    if final_root.exists():
        backup_root = _unique_backup_path(final_root)
        final_root.rename(backup_root)

    try:
        staging_root.rename(final_root)
    except Exception:
        if backup_root is not None and backup_root.exists() and not final_root.exists():
            backup_root.rename(final_root)
        raise

    if backup_root is not None and backup_root.exists():
        shutil.rmtree(backup_root)


def _unique_backup_path(final_root: Path) -> Path:
    for index in range(1000):
        candidate = final_root.with_name(f"{final_root.name}.bak-{index}")
        if not candidate.exists():
            return candidate
    raise InstallError(f"unable to allocate backup path for {final_root}")


def check_install(
    repo_root: Path,
    cwd: Path,
    home: Path,
    mode: str,
    host: str = "codex",
) -> tuple[bool, list[str]]:
    _validate_host(host)
    repo_root = repo_root.resolve()
    target = resolve_install_target(mode=mode, cwd=cwd.resolve(), home=home.resolve(), host=host)
    messages: list[str] = []

    expected_skill_dirs = list_skill_dirs(repo_root)
    expected_assets = list_runtime_assets(repo_root) if target.mode == "repo-local" else []

    for skill_dir in expected_skill_dirs:
        destination_root = target.skills_root / skill_dir.name
        for relative_file in _collect_files(skill_dir, root=skill_dir):
            destination_file = destination_root / relative_file
            if not destination_file.exists():
                messages.append(f"missing skill asset: {destination_file}")

    for asset in expected_assets:
        destination = target.runtime_root / asset.dest_rel
        if not destination.exists():
            messages.append(f"missing runtime asset: {destination}")

    if not target.manifest_path.exists():
        messages.append(f"missing manifest: {target.manifest_path}")
        return False, messages

    manifest = json.loads(target.manifest_path.read_text(encoding="utf-8"))
    for key in (
        "host",
        "install_mode",
        "installed_skills",
        "installed_runtime_files",
        "source_repo_path",
        "source_git_commit",
        "source_git_dirty",
        "source_git_status_short",
        "python_executable",
        "python_version",
    ):
        if key not in manifest:
            messages.append(f"manifest missing field: {key}")

    if target.mode == "repo-local":
        for key in (
            "runtime_python_executable",
            "runtime_python_version",
            "runtime_lock_path",
            "runtime_lock_digest",
        ):
            if key not in manifest:
                messages.append(f"manifest missing field: {key}")

    if manifest.get("host") != host:
        messages.append(f"manifest host mismatch: expected {host}, found {manifest.get('host')}")
    if manifest.get("install_mode") != target.mode:
        messages.append(
            f"manifest install_mode mismatch: expected {target.mode}, found {manifest.get('install_mode')}"
        )
    installed_source_repo_path = manifest.get("source_repo_path")
    if isinstance(installed_source_repo_path, str) and installed_source_repo_path.strip():
        current_source_repo_path = str(repo_root)
        if installed_source_repo_path.strip() != current_source_repo_path:
            messages.append(
                "\n".join(
                    [
                        "QROS source repo path drift detected:",
                        f"manifest: {target.manifest_path}",
                        f"installed source_repo_path: {installed_source_repo_path.strip()}",
                        f"current source_repo_path: {current_source_repo_path}",
                        "fix: run qros-update from the active research repo",
                    ]
                )
            )
    installed_commit = manifest.get("source_git_commit")
    current_commit = _git_commit(repo_root)
    if (
        isinstance(installed_commit, str)
        and installed_commit.strip()
        and current_commit
        and installed_commit.strip() != current_commit
    ):
        messages.append(
            "\n".join(
                [
                    "QROS install drift detected:",
                    f"manifest: {target.manifest_path}",
                    f"installed source_git_commit: {installed_commit.strip()}",
                    f"current source_git_commit: {current_commit}",
                    "fix: run `qros-update` from the active research repo, then Restart Codex "
                    "so installed skills and repo-local wrappers match the source repo.",
                ]
            )
        )
    current_git_status_short = _git_status_short(repo_root)
    current_git_dirty = bool(current_git_status_short.strip())
    if manifest.get("source_git_dirty") is False and current_git_dirty:
        messages.append(
            "\n".join(
                [
                    "QROS source_git_dirty drift detected:",
                    f"manifest: {target.manifest_path}",
                    "installed source_git_dirty: false",
                    "current source_git_dirty: true",
                    "fix: commit, stash, or reinstall QROS from the intended source checkout",
                ]
            )
        )

    if target.mode == "repo-local":
        runtime_lock_path = target.runtime_root / "uv.lock"
        if not runtime_lock_path.exists():
            messages.append(
                "\n".join(
                    [
                        "missing runtime lock:",
                        str(runtime_lock_path),
                        "fix: run qros-update from the active research repo",
                    ]
                )
            )
        else:
            installed_runtime_lock_digest = manifest.get("runtime_lock_digest")
            if isinstance(installed_runtime_lock_digest, str) and installed_runtime_lock_digest.strip():
                current_runtime_lock_digest = _file_sha256(runtime_lock_path)
                if installed_runtime_lock_digest.strip() != current_runtime_lock_digest:
                    messages.append(
                        "\n".join(
                            [
                                "QROS runtime lock drift detected:",
                                f"manifest: {target.manifest_path}",
                                f"installed runtime_lock_digest: {installed_runtime_lock_digest.strip()}",
                                f"current runtime_lock_digest: {current_runtime_lock_digest}",
                                "fix: run qros-update from the active research repo",
                            ]
                        )
                    )

    return not messages, messages


def _validate_host(host: str) -> None:
    if host not in SUPPORTED_HOSTS:
        raise InstallError(f"unsupported host: {host}")


def _copy_asset(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return
    shutil.copy2(source, destination)


def _collect_files(path: Path, *, root: Path) -> list[str]:
    if path.is_file():
        return [str(path.relative_to(root))]
    return sorted(str(file.relative_to(root)) for file in path.rglob("*") if file.is_file())


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def _git_status_short(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--short"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    lines = [
        line
        for line in result.stdout.splitlines()
        if not _is_qros_staging_status_line(line)
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def _is_qros_staging_status_line(line: str) -> bool:
    if not line.startswith("?? "):
        return False
    path = line[3:] if len(line) > 3 else ""
    return (
        path == QROS_INSTALL_LOCK_NAME
        or path.startswith(f"{QROS_INSTALL_LOCK_NAME}/")
        or path.startswith(".qros.tmp-")
        or "/.qros.tmp-" in path
    )


def _python_version() -> str:
    return ".".join(map(str, sys.version_info[:3]))


def _python_executable() -> str:
    return str(Path(sys.executable).resolve())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install QROS runtime assets.")
    parser.add_argument("--host", default="codex")
    parser.add_argument("--mode", default="auto", choices=sorted(SUPPORTED_MODES))
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--target-cwd", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    cwd = (args.target_cwd or Path.cwd()).resolve()
    home = Path.home()

    try:
        target = resolve_install_target(mode=args.mode, cwd=cwd, home=home, host=args.host)
        if args.check:
            ok, messages = check_install(
                repo_root=repo_root,
                cwd=cwd,
                home=home,
                mode=args.mode,
                host=args.host,
            )
            print(f"QROS check mode: {target.mode}")
            print(f"Skills root: {target.skills_root}")
            print(f"Runtime root: {target.runtime_root}")
            if ok:
                print("QROS install check: OK")
                return 0
            for message in messages:
                print(message)
            return 1

        result = install_qros(
            repo_root=repo_root,
            cwd=cwd,
            home=home,
            mode=args.mode,
            host=args.host,
        )
    except InstallError as exc:
        print(f"QROS setup failed: {exc}", file=sys.stderr)
        return 1

    action = "refreshed" if args.refresh else "installed"
    print(f"QROS {action} for host={args.host} mode={result.mode}")
    print(f"Skills written: {len(result.skills_written)} -> {target.skills_root}")
    print(f"Runtime files written: {len(result.runtime_written)} -> {target.runtime_root}")
    print(f"Manifest: {result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
