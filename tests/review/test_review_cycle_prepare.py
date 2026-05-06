import json
from pathlib import Path
from subprocess import run
import sys

import pytest
import yaml

from tests.helpers.repo_paths import REPO_ROOT
from tests.review.test_start_review_session import _prepare_mandate_stage
from runtime.tools import review_session_runtime
from runtime.tools.review_session_runtime import start_review_cycle
from runtime.tools.review_skillgen.review_engine import ReviewRuntimeConfigurationError


def test_review_cycle_prepare_script_emits_handoff_prompt_and_closer_command(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = REPO_ROOT / "runtime" / "scripts" / "review_cycle.py"

    result = run(
        [
            sys.executable,
            str(script_path),
            "prepare",
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(lineage_root),
            "--reviewer-id",
            "codex-mandate-reviewer",
            "--reviewer-session-id",
            "review-session-1",
            "--launcher-session-id",
            "launcher-session-1",
            "--launcher-thread-id",
            "launcher-thread-1",
            "--reviewer-agent-id",
            "reviewer-child-1",
            "--json",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["stage"] == "mandate"
    assert payload["review_cycle_id"]
    assert "Permitted reads only" in payload["reviewer_handoff_prompt"]
    assert "outputs/topic_a/01_mandate/review/request/*" in payload["reviewer_handoff_prompt"]
    assert "reviewer_findings.raw.yaml" in payload["reviewer_handoff_prompt"]
    assert "./.qros/bin/qros-review" in payload["closer_command"]
    assert "--stage-dir outputs/topic_a/01_mandate" in payload["closer_command"]

    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    assert receipt_payload["reviewer_agent_id"] == "reviewer-child-1"


def test_review_cycle_prepare_preflights_runtime_config_before_writing_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    checklist_path = tmp_path / "review_checklist_master.yaml"
    checklist_path.write_text("stages: {}\n", encoding="utf-8")
    monkeypatch.setattr(review_session_runtime, "CHECKLIST_PATH", checklist_path, raising=False)

    with pytest.raises(ReviewRuntimeConfigurationError) as excinfo:
        start_review_cycle(
            explicit_context={
                "stage_dir": stage_dir,
                "lineage_root": lineage_root,
            },
            reviewer_identity="codex-mandate-reviewer",
            reviewer_session_id="review-session-1",
            launcher_session_id="launcher-session-1",
            launcher_thread_id="launcher-thread-1",
            reviewer_agent_id="reviewer-child-1",
        )

    message = str(excinfo.value)
    assert "missing review checklist stage: mandate" in message
    assert not (stage_dir / "review" / "request" / "adversarial_review_request.yaml").exists()
    assert not (stage_dir / "review" / "request" / "reviewer_receipt.yaml").exists()


def test_qros_review_cycle_wrapper_exists() -> None:
    assert Path("runtime/bin/qros-review-cycle").exists()
