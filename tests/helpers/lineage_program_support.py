from __future__ import annotations

import json
from pathlib import Path

from runtime.tools.stage_program_scaffold import STAGE_PROGRAM_SPECS, materialize_stage_program


def ensure_stage_program(lineage_root: Path, stage_key: str) -> Path:
    return materialize_stage_program(
        lineage_root,
        stage_key,
        authored_by_agent_id="test-agent",
        authored_by_agent_role="executor",
        authoring_session_id="test-session",
    )



def write_fake_stage_provenance(lineage_root: Path, stage_key: str) -> Path:
    spec = STAGE_PROGRAM_SPECS[stage_key]
    stage_dir = lineage_root / spec["stage_dir"] / "author" / "formal"
    stage_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage_id": spec["stage_id"],
        "route": spec["route"],
        "lineage_id": lineage_root.name,
        "stage_status": "awaiting_review_closure",
        "program_dir": str(spec["program_dir"]),
        "stage_program_manifest_path": str(Path(spec["program_dir"]) / "stage_program.yaml"),
        "entrypoint": "run_stage.py",
        "entry_type": "python",
        "program_hash": "test-hash",
        "framework_revision": "test-revision",
        "invoked_at": "2026-04-03T00:00:00+00:00",
        "input_refs": [],
        "output_refs": [],
        "authored_by_agent_id": "test-agent",
        "authored_by_agent_role": "executor",
        "authoring_session_id": "test-session",
        "status": "success",
    }
    path = stage_dir / "program_execution_manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
