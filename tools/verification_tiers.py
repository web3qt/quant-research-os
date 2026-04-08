from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SMOKE_TEST_PATHS: tuple[str, ...] = (
    "tests/test_verification_tiers.py",
    "tests/test_research_session_runtime.py",
    "tests/test_run_research_session_script.py",
    "tests/test_stage_display_skill_assets.py",
    "tests/test_stage_display_skill.py",
    "tests/test_stage_display_runtime.py",
    "tests/test_stage_substep_normalization.py",
    "tests/test_skill_tree.py",
    "tests/test_research_session_assets.py",
    "tests/test_project_bootstrap.py",
    "tests/test_install_docs.py",
)

FULL_SMOKE_EXTRA_TEST_PATHS: tuple[str, ...] = (
    "tests/test_csf_research_session_routing.py",
    "tests/test_csf_data_ready_auto_program.py",
    "tests/test_research_session_reflection.py",
    "tests/test_stage_summary_html_export.py",
    "tests/test_anti_drift.py",
    "tests/test_anti_drift_replay.py",
    "tests/test_export_anti_drift_snapshots.py",
)

SUPPORTED_VERIFICATION_TIERS: tuple[str, ...] = ("smoke", "full-smoke")


@dataclass(frozen=True)
class VerificationTier:
    name: str
    description: str
    test_paths: tuple[str, ...]


def _dedupe(paths: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        ordered.append(path)
    return tuple(ordered)


def tier_definition(tier: str) -> VerificationTier:
    if tier == "smoke":
        return VerificationTier(
            name="smoke",
            description="Fast critical orchestration smoke across qros-session, stage-display, bootstrap, and install-doc contracts.",
            test_paths=SMOKE_TEST_PATHS,
        )
    if tier == "full-smoke":
        return VerificationTier(
            name="full-smoke",
            description="Broader route-level and anti-drift smoke that extends smoke with CSF routing, auto-program, reflection/export, and snapshot replay coverage.",
            test_paths=_dedupe(SMOKE_TEST_PATHS + FULL_SMOKE_EXTRA_TEST_PATHS),
        )
    raise ValueError(f"Unsupported verification tier: {tier}")


def pytest_command(*, tier: str, python_bin: str = "python") -> list[str]:
    definition = tier_definition(tier)
    return [python_bin, "-m", "pytest", *definition.test_paths, "-q"]


def repo_relative_existing_paths(repo_root: Path, *, tier: str) -> tuple[str, ...]:
    definition = tier_definition(tier)
    missing = [path for path in definition.test_paths if not (repo_root / path).exists()]
    if missing:
        raise FileNotFoundError(f"Missing test paths for {tier}: {', '.join(missing)}")
    return definition.test_paths
