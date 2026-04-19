from __future__ import annotations

import json
from pathlib import Path
from subprocess import run
import sys

from tests.helpers.repo_paths import REPO_ROOT
from runtime.tools.verification_tiers import (
    FULL_SMOKE_EXTRA_TEST_PATHS,
    SMOKE_TEST_PATHS,
    SUPPORTED_VERIFICATION_TIERS,
    pytest_command,
    tier_definition,
)


def test_verification_tiers_are_declared_and_non_empty() -> None:
    assert SUPPORTED_VERIFICATION_TIERS == ("smoke", "full-smoke")
    assert SMOKE_TEST_PATHS
    assert FULL_SMOKE_EXTRA_TEST_PATHS
    assert len(tier_definition("full-smoke").test_paths) > len(tier_definition("smoke").test_paths)


def test_full_smoke_contains_smoke_suite() -> None:
    smoke = set(tier_definition("smoke").test_paths)
    full_smoke = set(tier_definition("full-smoke").test_paths)
    assert smoke <= full_smoke


def test_pytest_command_uses_quiet_pytest_invocation() -> None:
    command = pytest_command(tier="smoke", python_bin="python3")
    assert command[:3] == ["python3", "-m", "pytest"]
    assert command[-1] == "-q"
    assert "tests/session/test_research_session_runtime.py" in command


def test_run_verification_tier_script_lists_tiers_as_json() -> None:
    repo_root = REPO_ROOT
    script = repo_root / "runtime" / "scripts" / "run_verification_tier.py"

    result = run(
        [sys.executable, str(script), "--tier", "smoke", "--list", "--json"],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    names = [item["name"] for item in payload["tiers"]]
    assert names == ["smoke", "full-smoke"]
    assert any("tests/session/test_research_session_runtime.py" in item["tests"] for item in payload["tiers"])


def test_run_verification_tier_script_supports_dry_run_json() -> None:
    repo_root = REPO_ROOT
    script = repo_root / "runtime" / "scripts" / "run_verification_tier.py"

    result = run(
        [sys.executable, str(script), "--tier", "full-smoke", "--dry-run", "--json"],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["tier"] == "full-smoke"
    assert payload["command"][0] == sys.executable
    assert payload["command"][1:3] == ["-m", "pytest"]
    assert "tests/anti_drift/test_anti_drift_replay.py" in payload["tests"]
    assert "tests/anti_drift/test_anti_drift_metamorphic.py" in payload["tests"]
    assert "tests/review/test_closure_writer_context_modes.py" in payload["tests"]


def test_qros_verify_wrapper_exists_and_is_executable() -> None:
    wrapper = Path("runtime/bin/qros-verify")
    assert wrapper.exists()
    assert wrapper.stat().st_mode & 0o111
