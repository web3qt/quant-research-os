from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any

import yaml

from runtime.tools.paper_to_spec import PaperToSpecError, validate_strategy_spec


class BaselineScaffoldError(RuntimeError):
    pass


@dataclass(frozen=True)
class BaselineScaffoldResult:
    layout_mode: str
    bundle_root: Path
    run_entrypoint: Path
    smoke_test_path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "layout_mode": self.layout_mode,
            "bundle_root": str(self.bundle_root),
            "run_entrypoint": str(self.run_entrypoint),
            "smoke_test_path": str(self.smoke_test_path),
        }


def scaffold_baseline_from_spec(
    *,
    target_repo: Path,
    spec_path: Path,
    prefer_repo_native: bool = True,
) -> dict[str, str]:
    target_repo = Path(target_repo)
    spec_path = Path(spec_path)

    if not target_repo.exists() or not target_repo.is_dir():
        raise BaselineScaffoldError(f"target repo not found: {target_repo}")

    spec_payload = _load_spec_payload(spec_path)
    slug = _resolve_slug(spec_path)

    repo_native_root = _discover_repo_native_root(target_repo) if prefer_repo_native else None
    if repo_native_root is not None:
        return _scaffold_bundle(
            bundle_root=repo_native_root / slug,
            layout_mode="repo_native",
            spec_path=spec_path,
            spec_payload=spec_payload,
        ).as_dict()

    return _scaffold_bundle(
        bundle_root=target_repo / "paper_specs" / slug,
        layout_mode="fallback",
        spec_path=spec_path,
        spec_payload=spec_payload,
    ).as_dict()


def _load_spec_payload(spec_path: Path) -> dict[str, Any]:
    if not spec_path.exists() or not spec_path.is_file():
        raise BaselineScaffoldError(f"strategy spec not found: {spec_path}")

    try:
        raw_payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BaselineScaffoldError(f"failed to parse strategy spec {spec_path}: {exc}") from exc
    except OSError as exc:
        raise BaselineScaffoldError(f"failed to read strategy spec {spec_path}: {exc}") from exc

    try:
        return validate_strategy_spec(raw_payload)
    except PaperToSpecError as exc:
        raise BaselineScaffoldError(f"invalid strategy spec {spec_path}: {exc}") from exc


def _resolve_slug(spec_path: Path) -> str:
    slug = spec_path.parent.name.strip()
    if not slug:
        raise BaselineScaffoldError(f"could not derive slug from spec path: {spec_path}")
    return slug


def _discover_repo_native_root(target_repo: Path) -> Path | None:
    # repo-native 模式优先锁定明确的研究目录，避免把任意 src/ 误判成研究根。
    for candidate in ("research", "strategies"):
        candidate_path = target_repo / candidate
        if candidate_path.exists() and candidate_path.is_dir():
            return candidate_path
    return None


def _scaffold_bundle(
    *,
    bundle_root: Path,
    layout_mode: str,
    spec_path: Path,
    spec_payload: dict[str, Any],
) -> BaselineScaffoldResult:
    strategy_type = _read_strategy_type(spec_payload)
    validation_targets = _read_validation_targets(spec_payload)

    try:
        bundle_root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise BaselineScaffoldError(f"target bundle already exists: {bundle_root}") from exc
    except OSError as exc:
        raise BaselineScaffoldError(f"failed to create target bundle {bundle_root}: {exc}") from exc

    try:
        tests_dir = bundle_root / "tests"
        tests_dir.mkdir(parents=False, exist_ok=False)

        _write_yaml(
            bundle_root / "strategy_config.yaml",
            {
                "strategy_slug": bundle_root.name,
                "spec_path": str(spec_path.resolve()),
                "strategy_type": strategy_type,
                "validation_targets": validation_targets,
            },
        )
        _write_text(
            bundle_root / "build_dataset.py",
            _dataset_stub(slug=bundle_root.name, strategy_type=strategy_type),
        )
        _write_text(
            bundle_root / "build_signal.py",
            _signal_stub(slug=bundle_root.name, strategy_type=strategy_type),
        )
        _write_text(
            bundle_root / "run_backtest.py",
            _backtest_stub(slug=bundle_root.name, strategy_type=strategy_type),
        )
        _write_text(
            tests_dir / "test_smoke.py",
            _smoke_test_stub(),
        )
    except OSError as exc:
        _cleanup_partial_bundle(bundle_root)
        raise BaselineScaffoldError(f"failed to scaffold baseline bundle {bundle_root}: {exc}") from exc

    return BaselineScaffoldResult(
        layout_mode=layout_mode,
        bundle_root=bundle_root,
        run_entrypoint=bundle_root / "run_backtest.py",
        smoke_test_path=tests_dir / "test_smoke.py",
    )


def _read_strategy_type(spec_payload: dict[str, Any]) -> str:
    strategy_identity = spec_payload.get("strategy_identity")
    if not isinstance(strategy_identity, dict):
        raise BaselineScaffoldError("strategy spec missing strategy_identity mapping")

    strategy_type = strategy_identity.get("strategy_type")
    if not isinstance(strategy_type, str) or not strategy_type.strip():
        raise BaselineScaffoldError("strategy spec missing strategy_identity.strategy_type")
    return strategy_type


def _read_validation_targets(spec_payload: dict[str, Any]) -> list[str]:
    implementation_handoff = spec_payload.get("implementation_handoff")
    if not isinstance(implementation_handoff, dict):
        raise BaselineScaffoldError("strategy spec missing implementation_handoff mapping")

    validation_targets = implementation_handoff.get("validation_targets")
    if not isinstance(validation_targets, list) or not all(
        isinstance(item, str) for item in validation_targets
    ):
        raise BaselineScaffoldError(
            "strategy spec missing implementation_handoff.validation_targets"
        )
    return validation_targets


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _cleanup_partial_bundle(bundle_root: Path) -> None:
    try:
        shutil.rmtree(bundle_root)
    except FileNotFoundError:
        return
    except OSError:
        return


def _dataset_stub(*, slug: str, strategy_type: str) -> str:
    return f"""#!/usr/bin/env python3
from __future__ import annotations


def main() -> int:
    print("build_dataset placeholder: {slug} ({strategy_type})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _signal_stub(*, slug: str, strategy_type: str) -> str:
    return f"""#!/usr/bin/env python3
from __future__ import annotations


def main() -> int:
    print("build_signal placeholder: {slug} ({strategy_type})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _backtest_stub(*, slug: str, strategy_type: str) -> str:
    return f"""#!/usr/bin/env python3
from __future__ import annotations


def main() -> int:
    print("run_backtest placeholder: {slug} ({strategy_type})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _smoke_test_stub() -> str:
    return """from pathlib import Path


def test_baseline_scaffold_files_exist() -> None:
    bundle_root = Path(__file__).resolve().parents[1]

    assert (bundle_root / "strategy_config.yaml").exists()
    assert (bundle_root / "build_dataset.py").exists()
    assert (bundle_root / "build_signal.py").exists()
    assert (bundle_root / "run_backtest.py").exists()
"""
