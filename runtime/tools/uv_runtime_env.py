from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


PYTHON_RUNTIME = "3.12"


class UvRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeEnvMetadata:
    python_executable: str
    python_version: str
    lock_path: str
    lock_digest: str


def ensure_repo_local_uv_runtime(*, runtime_root: Path, repo_root: Path) -> RuntimeEnvMetadata:
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        raise UvRuntimeError(
            "uv is required to provision QROS Python 3.12 runtime. "
            "Install uv, then rerun qros-update from the active research repo."
        )

    repo_root = repo_root.resolve()
    runtime_root = runtime_root if runtime_root.is_absolute() else repo_root / runtime_root
    runtime_root = runtime_root.resolve()
    runtime_root.mkdir(parents=True, exist_ok=True)
    requirements_path = _write_runtime_requirements(runtime_root=runtime_root, repo_root=repo_root)
    venv_path = runtime_root / ".venv"
    python_bin = venv_path / "bin" / "python"
    lock_path = runtime_root / "uv.lock"

    selected_python = _select_python_for_repo_local_runtime(uv_bin=uv_bin, repo_root=repo_root)
    if selected_python != PYTHON_RUNTIME and _python_has_runtime_dependencies(selected_python, repo_root=repo_root):
        # 显式 QROS_PYTHON 视为外部已管理好的 3.12 运行时；repo-local setup 只写锁和 manifest，
        # wrapper 在同一环境里优先复用该解释器，避免受限环境下的 uv/ensurepip 失败。
        lock_path.write_text(requirements_path.read_text(encoding="utf-8"), encoding="utf-8")
        version = _python_version(Path(selected_python))
        if not version.startswith(f"{PYTHON_RUNTIME}."):
            raise UvRuntimeError(f"QROS managed runtime expected Python {PYTHON_RUNTIME}, found {version}")
        return RuntimeEnvMetadata(
            python_executable=str(Path(selected_python).resolve()),
            python_version=version,
            lock_path=str(lock_path.resolve()),
            lock_digest=_sha256(lock_path),
        )

    _run([uv_bin, "venv", "--allow-existing", "--python", selected_python, str(venv_path)], cwd=repo_root)
    _run(
        [
            uv_bin,
            "pip",
            "compile",
            "--no-header",
            "--python-version",
            PYTHON_RUNTIME,
            "-o",
            str(lock_path),
            str(requirements_path),
        ],
        cwd=repo_root,
    )
    _run(
        [
            uv_bin,
            "pip",
            "sync",
            "--python",
            str(python_bin),
            str(lock_path),
        ],
        cwd=repo_root,
    )

    version = _python_version(python_bin)
    if not version.startswith(f"{PYTHON_RUNTIME}."):
        raise UvRuntimeError(f"QROS managed runtime expected Python {PYTHON_RUNTIME}, found {version}")

    return RuntimeEnvMetadata(
        python_executable=str(python_bin.resolve()),
        python_version=version,
        lock_path=str(lock_path.resolve()),
        lock_digest=_sha256(lock_path),
    )


def _select_python_for_repo_local_runtime(*, uv_bin: str, repo_root: Path) -> str:
    env_python = os.environ.get("QROS_PYTHON", "").strip()
    candidates = [env_python] if env_python else []

    for candidate in candidates:
        if _python_matches_runtime(candidate):
            return candidate

    # 优先复用当前机器上已经存在的 3.12；只有确实缺失时才触发 uv 安装。
    _run([uv_bin, "python", "install", PYTHON_RUNTIME], cwd=repo_root)
    return PYTHON_RUNTIME


def _write_runtime_requirements(*, runtime_root: Path, repo_root: Path) -> Path:
    requirements_path = runtime_root / "runtime-requirements.txt"
    dependencies = _project_dependencies(repo_root)
    if dependencies:
        requirements_text = "\n".join(dependencies) + "\n"
    else:
        requirements_text = "# QROS runtime dependencies are not declared in pyproject.toml.\n"
    requirements_path.write_text(requirements_text, encoding="utf-8")
    return requirements_path


def _project_dependencies(repo_root: Path) -> list[str]:
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        return []
    return [dependency for dependency in dependencies if isinstance(dependency, str)]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _python_version(python_bin: Path) -> str:
    completed = _run(
        [
            str(python_bin),
            "-c",
            "import sys; print('.'.join(map(str, sys.version_info[:3])))",
        ],
        cwd=python_bin.parent,
    )
    return completed.stdout.strip()


def _python_matches_runtime(python_bin: str) -> bool:
    completed = subprocess.run(
        [
            python_bin,
            "-c",
            "import sys; print('.'.join(map(str, sys.version_info[:3])))",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return False
    return completed.stdout.strip().startswith(f"{PYTHON_RUNTIME}.")


def _python_has_runtime_dependencies(python_bin: str, *, repo_root: Path) -> bool:
    imports: list[str] = []
    for dependency in _project_dependencies(repo_root):
        normalized = dependency.split(";", 1)[0].strip()
        normalized = normalized.split("[", 1)[0]
        for marker in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            normalized = normalized.split(marker, 1)[0]
        package_name = normalized.strip()
        if not package_name:
            continue
        if package_name == "PyYAML":
            imports.append("yaml")
        else:
            imports.append(package_name.replace("-", "_"))

    if not imports:
        return True

    probe = "import " + ", ".join(imports)
    completed = subprocess.run(
        [python_bin, "-c", probe],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise UvRuntimeError(f"command failed: {' '.join(args)}\n{detail}")
    return completed
