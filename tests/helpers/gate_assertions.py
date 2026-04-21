"""Gate assertion helpers for pipeline tests.

Loads stage gate configuration from workflow_stage_gates.yaml and runs
structural/metric gate checks, asserting all pass.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from runtime.tools.review_skillgen.stage_content_gate import (
    check_global_evidence,
    check_required_outputs,
    check_structural_gates,
    check_metric_gates,
)
from tests.helpers.repo_paths import REPO_ROOT

_GATES_YAML = REPO_ROOT / "contracts" / "stages" / "workflow_stage_gates.yaml"


def _load_stage_config(stage_id: str) -> dict:
    payload = yaml.safe_load(_GATES_YAML.read_text(encoding="utf-8"))
    stages = payload.get("stages", payload)
    if stage_id not in stages:
        raise KeyError(f"stage {stage_id!r} not found in {_GATES_YAML}")
    return stages[stage_id]


def load_structural_checks(stage_id: str) -> list[dict]:
    return _load_stage_config(stage_id).get("structural_gate_checks", [])


def load_metric_checks(stage_id: str) -> list[dict]:
    return _load_stage_config(stage_id).get("metric_gate_checks", [])


def load_required_outputs(stage_id: str) -> list[str]:
    return _load_stage_config(stage_id).get("required_outputs", [])


def assert_structural_gates_pass(formal_dir: Path, stage_id: str) -> None:
    """Run structural gate checks and assert no findings."""
    checks = load_structural_checks(stage_id)
    if not checks:
        return
    findings = check_structural_gates(formal_dir, checks)
    assert findings == [], (
        f"{stage_id} structural gate failures:\n" + "\n".join(f"  - {f}" for f in findings)
    )


def assert_metric_gates_pass(formal_dir: Path, stage_id: str) -> None:
    """Run metric gate checks and assert no findings."""
    checks = load_metric_checks(stage_id)
    if not checks:
        return
    findings = check_metric_gates(formal_dir, checks)
    assert findings == [], (
        f"{stage_id} metric gate failures:\n" + "\n".join(f"  - {f}" for f in findings)
    )


def assert_required_outputs_present(stage_dir: Path, stage_id: str) -> None:
    """Check that all required outputs exist under stage_dir."""
    outputs = load_required_outputs(stage_id)
    if not outputs:
        return
    missing = check_required_outputs(stage_dir, outputs)
    assert missing == [], (
        f"{stage_id} missing required outputs:\n" + "\n".join(f"  - {m}" for m in missing)
    )


def assert_global_evidence_present(stage_dir: Path, stage_id: str) -> None:
    """Check that global evidence files exist."""
    config = _load_stage_config(stage_id)
    findings = check_global_evidence(stage_dir, config)
    assert findings == [], (
        f"{stage_id} global evidence failures:\n" + "\n".join(f"  - {f}" for f in findings)
    )


def assert_all_gates_pass(stage_dir: Path, stage_id: str) -> None:
    """Run all gate checks for a stage and assert everything passes.

    stage_dir should be the stage's formal artifacts directory (e.g. .../03_csf_signal_ready/author/formal).
    """
    assert_required_outputs_present(stage_dir, stage_id)
    assert_structural_gates_pass(stage_dir, stage_id)
    assert_metric_gates_pass(stage_dir, stage_id)
    assert_global_evidence_present(stage_dir, stage_id)
