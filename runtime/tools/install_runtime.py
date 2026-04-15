from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal


InstallMode = Literal["repo-local", "user-global", "auto"]
ResolvedInstallMode = Literal["repo-local", "user-global"]
InstallHost = Literal["codex"]

SUPPORTED_HOSTS: set[str] = {"codex"}
SUPPORTED_MODES: set[str] = {"repo-local", "user-global", "auto"}
SKILLS_SOURCE_DIR = Path("skills")
GLOBAL_METADATA_ROOT = Path(".codex") / "qros"


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
    RuntimeAsset(Path("docs/governance"), Path("docs/governance")),
    RuntimeAsset(Path("docs/README.codex.md"), Path("docs/README.codex.md")),
    RuntimeAsset(Path("contracts"), Path("contracts")),
)

REPO_LOCAL_RUNTIME_ASSETS = (
    RuntimeAsset(Path("runtime/bin"), Path("bin")),
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
        return "repo-local" if (cwd / "skills").exists() else "user-global"
    return mode


def resolve_install_target(mode: str, cwd: Path, home: Path) -> InstallTarget:
    resolved_mode = resolve_install_mode(mode, cwd)
    if resolved_mode == "repo-local":
        runtime_root = cwd / ".qros"
        return InstallTarget(
            mode=resolved_mode,
            skills_root=home / ".codex" / "skills",
            runtime_root=runtime_root,
            manifest_path=runtime_root / "install-manifest.json",
        )

    runtime_root = home / GLOBAL_METADATA_ROOT
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
    runtime_assets = list_runtime_assets(repo_root) if target.mode == "repo-local" else []

    target.skills_root.mkdir(parents=True, exist_ok=True)
    if target.mode == "repo-local" and target.runtime_root.exists():
        shutil.rmtree(target.runtime_root)
    target.runtime_root.mkdir(parents=True, exist_ok=True)

    skills_written: list[str] = []
    for skill_dir in skill_dirs:
        destination = target.skills_root / skill_dir.name
        if skill_dir.resolve() != destination.resolve():
            _copy_asset(skill_dir, destination)
        skills_written.append(skill_dir.name)

    runtime_written: list[str] = []
    for asset in runtime_assets:
        source = repo_root / asset.source_rel
        destination = target.runtime_root / asset.dest_rel
        _copy_asset(source, destination)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install QROS runtime assets for Codex.")
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
        target = resolve_install_target(mode=args.mode, cwd=cwd, home=home)
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
