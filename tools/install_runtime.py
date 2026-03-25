from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal


InstallMode = Literal["repo-local", "user-global", "auto"]
ResolvedInstallMode = Literal["repo-local", "user-global"]
InstallHost = Literal["codex"]

SUPPORTED_HOSTS: set[str] = {"codex"}
SUPPORTED_MODES: set[str] = {"repo-local", "user-global", "auto"}
SKILLS_SOURCE_DIR = Path(".agents/skills")
RUNTIME_TREE_NAMES = ("scripts", "tools", "templates")
DOC_TREE_NAMES = (
    "docs/experience",
    "docs/gates",
    "docs/check-sop",
    "docs/intake-sop",
)


class InstallError(RuntimeError):
    pass


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
        return "repo-local" if (cwd / ".agents").exists() else "user-global"
    return mode


def resolve_install_target(mode: str, cwd: Path, home: Path) -> InstallTarget:
    resolved_mode = resolve_install_mode(mode, cwd)
    if resolved_mode == "repo-local":
        runtime_root = cwd / ".qros"
        return InstallTarget(
            mode=resolved_mode,
            skills_root=cwd / ".agents" / "skills",
            runtime_root=runtime_root,
            manifest_path=runtime_root / "install-manifest.json",
        )

    runtime_root = home / ".qros"
    return InstallTarget(
        mode=resolved_mode,
        skills_root=home / ".codex" / "skills",
        runtime_root=runtime_root,
        manifest_path=runtime_root / "install-manifest.json",
    )


def list_skill_dirs(repo_root: Path) -> list[Path]:
    skills_root = repo_root / SKILLS_SOURCE_DIR
    if not skills_root.exists():
        raise InstallError(f"missing skills directory: {skills_root}")

    skill_dirs = sorted(
        path for path in skills_root.iterdir() if path.is_dir() and path.name.startswith("qros-")
    )
    if not skill_dirs:
        raise InstallError(f"no qros skill directories found under {skills_root}")
    return skill_dirs


def list_runtime_assets(repo_root: Path) -> list[Path]:
    assets: list[Path] = []
    for name in RUNTIME_TREE_NAMES:
        asset = repo_root / name
        if not asset.exists():
            raise InstallError(f"missing runtime asset: {asset}")
        assets.append(asset)

    for name in DOC_TREE_NAMES:
        asset = repo_root / name
        if not asset.exists():
            raise InstallError(f"missing documentation asset: {asset}")
        assets.append(asset)

    return assets


def build_manifest(
    *,
    repo_root: Path,
    target: InstallTarget,
    installed_skills: list[str],
    installed_runtime_files: list[str],
) -> dict[str, object]:
    return {
        "project_name": repo_root.name,
        "host": "codex",
        "install_mode": target.mode,
        "installed_at": datetime.now(UTC).isoformat(),
        "source_repo_path": str(repo_root),
        "source_git_commit": _git_commit(repo_root),
        "skills_root": str(target.skills_root),
        "runtime_root": str(target.runtime_root),
        "installed_skills": installed_skills,
        "installed_runtime_files": installed_runtime_files,
        "version_marker": _git_commit(repo_root) or "unknown",
    }


def install_qros(
    repo_root: Path,
    cwd: Path,
    home: Path,
    mode: str,
    host: str = "codex",
) -> InstallResult:
    _validate_host(host)
    repo_root = repo_root.resolve()
    target = resolve_install_target(mode=mode, cwd=cwd.resolve(), home=home.resolve())
    skill_dirs = list_skill_dirs(repo_root)
    runtime_assets = list_runtime_assets(repo_root)

    target.skills_root.mkdir(parents=True, exist_ok=True)
    target.runtime_root.mkdir(parents=True, exist_ok=True)

    skills_written: list[str] = []
    for skill_dir in skill_dirs:
        destination = target.skills_root / skill_dir.name
        _copy_tree(skill_dir, destination)
        skills_written.append(skill_dir.name)

    runtime_written: list[str] = []
    for asset in runtime_assets:
        destination = target.runtime_root / asset.relative_to(repo_root)
        _copy_tree(asset, destination)
        runtime_written.extend(_collect_files(destination, root=target.runtime_root))

    manifest = build_manifest(
        repo_root=repo_root,
        target=target,
        installed_skills=skills_written,
        installed_runtime_files=sorted(runtime_written),
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


def check_install(
    repo_root: Path,
    cwd: Path,
    home: Path,
    mode: str,
    host: str = "codex",
) -> tuple[bool, list[str]]:
    _validate_host(host)
    repo_root = repo_root.resolve()
    target = resolve_install_target(mode=mode, cwd=cwd.resolve(), home=home.resolve())
    messages: list[str] = []

    expected_skills = [path.name for path in list_skill_dirs(repo_root)]
    expected_assets = list_runtime_assets(repo_root)

    for skill_name in expected_skills:
        if not (target.skills_root / skill_name / "SKILL.md").exists():
            messages.append(f"missing skill: {target.skills_root / skill_name / 'SKILL.md'}")

    for asset in expected_assets:
        destination = target.runtime_root / asset.relative_to(repo_root)
        if not destination.exists():
            messages.append(f"missing runtime asset: {destination}")

    if not target.manifest_path.exists():
        messages.append(f"missing manifest: {target.manifest_path}")
        return False, messages

    manifest = json.loads(target.manifest_path.read_text(encoding="utf-8"))
    for key in ("host", "install_mode", "installed_skills", "installed_runtime_files", "source_git_commit"):
        if key not in manifest:
            messages.append(f"manifest missing field: {key}")

    if manifest.get("host") != host:
        messages.append(f"manifest host mismatch: expected {host}, found {manifest.get('host')}")
    if manifest.get("install_mode") != target.mode:
        messages.append(
            f"manifest install_mode mismatch: expected {target.mode}, found {manifest.get('install_mode')}"
        )

    return not messages, messages


def _validate_host(host: str) -> None:
    if host not in SUPPORTED_HOSTS:
        raise InstallError(f"unsupported host: {host}")


def _copy_tree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def _collect_files(path: Path, *, root: Path) -> list[str]:
    return sorted(str(file.relative_to(root)) for file in path.rglob("*") if file.is_file())


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
