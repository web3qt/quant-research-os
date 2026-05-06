#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from runtime.tools.review_skillgen.render import render_stage_skill


GATE_SCHEMA_PATH = ROOT / "contracts" / "stages" / "workflow_stage_gates.yaml"
CHECKLIST_SCHEMA_PATH = ROOT / "contracts" / "review" / "review_checklist_master.yaml"
REVIEW_SKILLS = {
    "mandate": "qros-mandate-review",
    "data_ready": "qros-data-ready-review",
    "csf_data_ready": "qros-csf-data-ready-review",
    "signal_ready": "qros-signal-ready-review",
    "csf_signal_ready": "qros-csf-signal-ready-review",
    "train_calibration": "qros-train-freeze-review",
    "csf_train_freeze": "qros-csf-train-freeze-review",
    "test_evidence": "qros-test-evidence-review",
    "csf_test_evidence": "qros-csf-test-evidence-review",
    "backtest_ready": "qros-backtest-ready-review",
    "csf_backtest_ready": "qros-csf-backtest-ready-review",
    "holdout_validation": "qros-holdout-validation-review",
    "csf_holdout_validation": "qros-csf-holdout-validation-review",
}
SKILL_GROUPS = {
    "qros-mandate-review": "mandate",
    "qros-data-ready-review": "data_ready",
    "qros-csf-data-ready-review": "csf_data_ready",
    "qros-signal-ready-review": "signal_ready",
    "qros-csf-signal-ready-review": "csf_signal_ready",
    "qros-train-freeze-review": "train_freeze",
    "qros-csf-train-freeze-review": "csf_train_freeze",
    "qros-test-evidence-review": "test_evidence",
    "qros-csf-test-evidence-review": "csf_test_evidence",
    "qros-backtest-ready-review": "backtest_ready",
    "qros-csf-backtest-ready-review": "csf_backtest_ready",
    "qros-holdout-validation-review": "holdout_validation",
    "qros-csf-holdout-validation-review": "csf_holdout_validation",
}

HOST_OUTPUT_ROOTS: dict[str, str] = {
    "codex": "skills",
    "claude-code": ".claude-plugin/skills",
}

HOST_LABELS: dict[str, str] = {
    "codex": "Codex",
    "claude-code": "Claude Code",
}


def _require_existing_file(path: Path, *, label: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def _render_skill_outputs(
    stage_key: str,
    skill_name: str,
    gates: dict,
    checklist: dict,
    output_root: Path,
    host: str,
) -> dict[Path, str]:
    stage_name = gates["stages"][stage_key]["stage_name"]
    host_label = HOST_LABELS.get(host, "Codex")
    skill_md = render_stage_skill(stage_key, skill_name, gates, checklist, host=host)
    openai_yaml = "\n".join(
        [
            f"name: {skill_name}",
            f"description: {host_label} review skill for {stage_name} stage verification.",
            "",
        ]
    )

    skill_group = SKILL_GROUPS[skill_name]
    skills_root = HOST_OUTPUT_ROOTS.get(host, "skills")
    skill_dir = output_root / skills_root / skill_group / skill_name
    return {
        skill_dir / "SKILL.md": skill_md,
        skill_dir / "agents" / "openai.yaml": openai_yaml,
    }


def _write_skill(stage_key: str, skill_name: str, gates: dict, checklist: dict, output_root: Path, host: str) -> None:
    outputs = _render_skill_outputs(stage_key, skill_name, gates, checklist, output_root, host)
    for output_path, content in outputs.items():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")


def _is_fresh(outputs: dict[Path, str]) -> bool:
    for output_path, expected in outputs.items():
        if not output_path.exists():
            return False
        existing = output_path.read_text(encoding="utf-8")
        if existing != expected:
            return False
    return True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate QROS stage review skills.")
    parser.add_argument("--host", choices=["codex", "claude-code"], required=True)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    gates = load_gate_schema(_require_existing_file(GATE_SCHEMA_PATH, label="gate schema"))
    checklist = load_checklist_schema(_require_existing_file(CHECKLIST_SCHEMA_PATH, label="checklist schema"))

    any_stale = False
    for stage_key, skill_name in REVIEW_SKILLS.items():
        outputs = _render_skill_outputs(stage_key, skill_name, gates, checklist, args.output_root, args.host)
        if args.dry_run:
            if _is_fresh(outputs):
                print(f"FRESH: {skill_name}")
            else:
                print(f"STALE: {skill_name}")
                any_stale = True
        else:
            _write_skill(stage_key, skill_name, gates, checklist, args.output_root, args.host)

    return 1 if any_stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
