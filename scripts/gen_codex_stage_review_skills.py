#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from tools.review_skillgen.render import render_stage_skill


DRY_RUN = "--dry-run" in sys.argv[1:]
GATE_SCHEMA_PATH = ROOT / "docs" / "gates" / "workflow_stage_gates.yaml"
CHECKLIST_SCHEMA_PATH = ROOT / "docs" / "review-sop" / "review_checklist_master.yaml"
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


def _require_existing_file(path: Path, *, label: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def _parse_output_root(argv: list[str]) -> Path:
    if "--output-root" not in argv:
        return ROOT
    idx = argv.index("--output-root")
    if idx + 1 >= len(argv):
        raise SystemExit("--output-root requires a path")
    return Path(argv[idx + 1]).resolve()


def _render_skill_outputs(
    stage_key: str,
    skill_name: str,
    gates: dict,
    checklist: dict,
    output_root: Path,
) -> dict[Path, str]:
    stage_name = gates["stages"][stage_key]["stage_name"]
    skill_md = render_stage_skill(stage_key, skill_name, gates, checklist)
    openai_yaml = "\n".join(
        [
            f"name: {skill_name}",
            f"description: Codex review skill for {stage_name} stage verification.",
            "",
        ]
    )

    skill_dir = output_root / ".agents" / "skills" / skill_name
    return {
        skill_dir / "SKILL.md": skill_md,
        skill_dir / "agents" / "openai.yaml": openai_yaml,
        output_root / "skills" / skill_name / "SKILL.md": skill_md,
    }


def _write_skill(stage_key: str, skill_name: str, gates: dict, checklist: dict, output_root: Path) -> None:
    outputs = _render_skill_outputs(stage_key, skill_name, gates, checklist, output_root)
    skill_dir = output_root / ".agents" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

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


def main() -> int:
    output_root = _parse_output_root(sys.argv[1:])
    gates = load_gate_schema(_require_existing_file(GATE_SCHEMA_PATH, label="gate schema"))
    checklist = load_checklist_schema(_require_existing_file(CHECKLIST_SCHEMA_PATH, label="checklist schema"))

    any_stale = False
    for stage_key, skill_name in REVIEW_SKILLS.items():
        outputs = _render_skill_outputs(stage_key, skill_name, gates, checklist, output_root)
        if DRY_RUN:
            if _is_fresh(outputs):
                print(f"FRESH: {skill_name}")
            else:
                print(f"STALE: {skill_name}")
                any_stale = True
        else:
            _write_skill(stage_key, skill_name, gates, checklist, output_root)

    return 1 if any_stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
