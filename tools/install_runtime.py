from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


InstallHost = Literal["codex"]
InstallMode = Literal["repo-local", "user-global", "auto"]

SUPPORTED_HOSTS: tuple[str, ...] = ("codex",)
SUPPORTED_MODES: tuple[str, ...] = ("repo-local", "user-global", "auto")
INSTALL_VERSION_MARKER = "qros-install-runtime-v1"


class InstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class InstallTarget:
    root: Path
    skills_root: Path
    runtime_root: Path
    manifest_path: Path


@dataclass(frozen=True)
class InstallResult:
    mode: str
    host: str
    target: InstallTarget
    installed_skills: list[str]
    installed_runtime_files: list[str]
    manifest_path: Path


def _validate_host(host: str) -> None:
    if host not in SUPPORTED_HOSTS:
        raise InstallError(f"Unsupported host: {host}")


def resolve_install_mode(mode: str, cwd: Path) -> str:
    if mode not in SUPPORTED_MODES:
        raise InstallError(f"Invalid install mode: {mode}")
    if mode != "auto":
        return mode
    return "repo-local" if (cwd / ".agents").exists() else "user-global"


def resolve_install_target(mode: str, cwd: Path, home: Path) -> InstallTarget:
    if mode == "repo-local":
        root = cwd
        skills_root = root / ".agents" / "skills"
        runtime_root = root / ".qros"
    elif mode == "user-global":
        root = home
        skills_root = root / ".codex" / "skills"
        runtime_root = root / ".qros"
    else:
        raise InstallError(f"Invalid resolved install mode: {mode}")

    return InstallTarget(
        root=root,
        skills_root=skills_root,
        runtime_root=runtime_root,
        manifest_path=runtime_root / "install-manifest.json",
    )


def _skill_sources(repo_root: Path) -> list[Path]:
    skills_root = repo_root / ".agents" / "skills"
    if not skills_root.exists():
        raise InstallError(f"Missing skills source directory: {skills_root}")

    skill_dirs = sorted(
        path
        for path in skills_root.iterdir()
        if path.is_dir() and path.name.startswith("qros-") and (path / "SKILL.md").exists()
    )
    if not skill_dirs:
        raise InstallError(f"No qros-* skills found under {skills_root}")
    return skill_dirs


def _runtime_sources(repo_root: Path) -> list[tuple[Path, Path]]:
    runtime_roots = [
        (repo_root / "scripts", Path("scripts")),
        (repo_root / "tools", Path("tools")),
        (repo_root / "templates", Path("templates")),
        (repo_root / "docs" / "experience", Path("docs") / "experience"),
        (repo_root / "docs" / "gates", Path("docs") / "gates"),
        (repo_root / "docs" / "check-sop", Path("docs") / "check-sop"),
        (repo_root / "docs" / "intake-sop", Path("docs") / "intake-sop"),
    ]
    sources: list[tuple[Path, Path]] = []
    for source, relative_target in runtime_roots:
        if source.exists():
            sources.append((source, relative_target))
    if not sources:
        raise InstallError("No runtime assets found to install")
    return sources


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_tree(source: Path, destination: Path) -> list[str]:
    copied: list[str] = []
    for root, dirs, files in os.walk(source):
        dirs[:] = [entry for entry in dirs if entry != "__pycache__" and not entry.startswith(".")]
        root_path = Path(root)
        relative_root = root_path.relative_to(source)
        destination_root = destination / relative_root
        destination_root.mkdir(parents=True, exist_ok=True)
        for filename in files:
            if filename.endswith((".pyc", ".pyo")):
                continue
            source_file = root_path / filename
            destination_file = destination_root / filename
            _copy_file(source_file, destination_file)
            copied.append((destination_file.relative_to(destination)).as_posix())
    return copied


def _source_git_commit(repo_root: Path) -> str:
    try:
        return (
            subprocess.check_output(["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True)
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _build_manifest(
    *,
    repo_root: Path,
    target: InstallTarget,
    host: str,
    mode: str,
    installed_skills: list[str],
    installed_runtime_files: list[str],
) -> dict[str, object]:
    return {
        "host": host,
        "install_mode": mode,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "source_repo_path": str(repo_root),
        "source_git_commit": _source_git_commit(repo_root),
        "skills_root": str(target.skills_root),
        "runtime_root": str(target.runtime_root),
        "installed_skills": installed_skills,
        "installed_runtime_files": installed_runtime_files,
        "version_marker": INSTALL_VERSION_MARKER,
    }


def _write_manifest(target: InstallTarget, manifest: dict[str, object]) -> None:
    target.runtime_root.mkdir(parents=True, exist_ok=True)
    target.manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def install_qros(
    repo_root: Path,
    cwd: Path,
    home: Path,
    mode: str,
    host: str = "codex",
) -> InstallResult:
    _validate_host(host)
    resolved_mode = resolve_install_mode(mode, cwd)
    target = resolve_install_target(resolved_mode, cwd, home)

    skill_sources = _skill_sources(repo_root)
    runtime_sources = _runtime_sources(repo_root)

    target.skills_root.mkdir(parents=True, exist_ok=True)
    target.runtime_root.mkdir(parents=True, exist_ok=True)

    installed_skills: list[str] = []
    for source in skill_sources:
        destination = target.skills_root / source.name
        _copy_tree(source, destination)
        installed_skills.append(source.name)

    installed_runtime_files: list[str] = []
    for source, relative_target in runtime_sources:
        destination = target.runtime_root / relative_target
        if source.is_file():
            _copy_file(source, destination)
            installed_runtime_files.append(relative_target.as_posix())
        else:
            installed_runtime_files.extend(_copy_tree(source, destination))

    manifest = _build_manifest(
        repo_root=repo_root,
        target=target,
        host=host,
        mode=resolved_mode,
        installed_skills=installed_skills,
        installed_runtime_files=installed_runtime_files,
    )
    _write_manifest(target, manifest)

    return InstallResult(
        mode=resolved_mode,
        host=host,
        target=target,
        installed_skills=installed_skills,
        installed_runtime_files=installed_runtime_files,
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
    resolved_mode = resolve_install_mode(mode, cwd)
    target = resolve_install_target(resolved_mode, cwd, home)

    messages: list[str] = []
    ok = True

    try:
        skill_sources = _skill_sources(repo_root)
        runtime_sources = _runtime_sources(repo_root)
    except InstallError as exc:
        return False, [str(exc)]

    if not target.skills_root.exists():
        ok = False
        messages.append(f"Missing skills root: {target.skills_root}")
    for source in skill_sources:
        skill_dir = target.skills_root / source.name
        if not skill_dir.exists() or not (skill_dir / "SKILL.md").exists():
            ok = False
            messages.append(f"Missing installed skill: {skill_dir}")

    if not target.runtime_root.exists():
        ok = False
        messages.append(f"Missing runtime root: {target.runtime_root}")
    for source, relative_target in runtime_sources:
        destination = target.runtime_root / relative_target
        if source.is_file():
            if not destination.exists():
                ok = False
                messages.append(f"Missing runtime file: {destination}")
        else:
            if not destination.exists():
                ok = False
                messages.append(f"Missing runtime directory: {destination}")

    if not target.manifest_path.exists():
        ok = False
        messages.append(f"Missing manifest: {target.manifest_path}")
    else:
        try:
            manifest = json.loads(target.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            ok = False
            messages.append(f"Invalid manifest JSON: {exc}")
        else:
            for key in [
                "host",
                "install_mode",
                "installed_skills",
                "installed_runtime_files",
                "source_git_commit",
            ]:
                if key not in manifest:
                    ok = False
                    messages.append(f"Manifest missing field: {key}")

    return ok, messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install or verify QROS runtime assets.")
    parser.add_argument("--host", default="codex")
    parser.add_argument("--mode", default="auto")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args(argv)

    if args.check and args.refresh:
        raise InstallError("--check and --refresh cannot be combined")

    if args.check:
        ok, messages = check_install(
            repo_root=args.repo_root,
            cwd=args.cwd,
            home=args.home,
            mode=args.mode,
            host=args.host,
        )
        for message in messages:
            print(message)
        return 0 if ok else 1

    result = install_qros(
        repo_root=args.repo_root,
        cwd=args.cwd,
        home=args.home,
        mode=args.mode,
        host=args.host,
    )
    print(f"Installed QROS in {result.mode} mode")
    print(f"Skills: {result.target.skills_root}")
    print(f"Runtime: {result.target.runtime_root}")
    print(f"Manifest: {result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
