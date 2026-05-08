from __future__ import annotations

from pathlib import Path
from subprocess import run
import sys

import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from tests.helpers.repo_paths import REPO_ROOT


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_run_agent_behavior_eval_lists_cases_when_no_agent_command(tmp_path: Path) -> None:
    result = run(
        [
            sys.executable,
            "runtime/scripts/run_agent_behavior_eval.py",
            "--cases",
            "contracts/agent_eval/qros_agent_behavior_eval_cases.yaml",
            "--case",
            "naive_raw_idea_triggers_research_session",
            "--work-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "agent command template is required for live eval" in result.stderr
    assert "naive_raw_idea_triggers_research_session" in result.stdout


def test_run_agent_behavior_eval_accepts_fake_transcript_and_writes_result(tmp_path: Path) -> None:
    runtime_status = tmp_path / "runtime_status.json"
    runtime_status.write_text('{"current_stage":"idea_intake_confirmation_pending"}\n', encoding="utf-8")
    lineage_root = tmp_path / "outputs" / "agent_eval_btc_alt"
    (lineage_root / "00_idea_intake").mkdir(parents=True)
    _write_yaml(lineage_root / "00_idea_intake" / "scope_canvas.yaml", {"market": ""})

    result = run(
        [
            sys.executable,
            "runtime/scripts/run_agent_behavior_eval.py",
            "--cases",
            "contracts/agent_eval/qros_agent_behavior_eval_cases.yaml",
            "--case",
            "naive_raw_idea_triggers_research_session",
            "--work-root",
            str(tmp_path / "runs"),
            "--transcript-path",
            "tests/agent_eval/fixtures/fake_agent_success.jsonl",
            "--runtime-status-path",
            str(runtime_status),
            "--lineage-root",
            str(lineage_root),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    result_path = tmp_path / "runs" / "naive_raw_idea_triggers_research_session" / "result.yaml"
    assert result_path.exists()
    payload = yaml.safe_load(result_path.read_text(encoding="utf-8"))
    assert payload["case_id"] == "naive_raw_idea_triggers_research_session"
    assert payload["passed"] is True


def test_run_agent_behavior_eval_reports_missing_skill_from_fake_transcript(tmp_path: Path) -> None:
    result = run(
        [
            sys.executable,
            "runtime/scripts/run_agent_behavior_eval.py",
            "--cases",
            "contracts/agent_eval/qros_agent_behavior_eval_cases.yaml",
            "--case",
            "naive_raw_idea_triggers_research_session",
            "--work-root",
            str(tmp_path),
            "--transcript-path",
            "tests/agent_eval/fixtures/fake_agent_missing_skill.jsonl",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "expected skill was not triggered: qros-research-session" in result.stderr


def test_live_agent_command_overwrites_stale_stdout_transcript(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "explicit_idea_intake_author_skill_first"
    run_dir.mkdir(parents=True)
    (run_dir / "transcript.jsonl").write_text('{"event_type":"assistant_text","name":"assistant"}\n', encoding="utf-8")

    emitter = tmp_path / "emit_transcript.py"
    emitter.write_text(
        "print('{\"event_type\":\"skill_call\",\"name\":\"qros-idea-intake-author\"}')\n",
        encoding="utf-8",
    )

    result = run(
        [
            sys.executable,
            "runtime/scripts/run_agent_behavior_eval.py",
            "--cases",
            "contracts/agent_eval/qros_agent_behavior_eval_cases.yaml",
            "--case",
            "explicit_idea_intake_author_skill_first",
            "--work-root",
            str(tmp_path / "runs"),
            "--agent-command-template",
            f"{sys.executable} {emitter}",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "qros-idea-intake-author" in (run_dir / "transcript.jsonl").read_text(encoding="utf-8")


def test_live_agent_command_surfaces_child_stderr_on_failure(tmp_path: Path) -> None:
    failing_agent = tmp_path / "failing_agent.py"
    failing_agent.write_text(
        "import sys\nsys.stderr.write('agent failed before transcript\\n')\nsys.exit(7)\n",
        encoding="utf-8",
    )

    result = run(
        [
            sys.executable,
            "runtime/scripts/run_agent_behavior_eval.py",
            "--cases",
            "contracts/agent_eval/qros_agent_behavior_eval_cases.yaml",
            "--case",
            "explicit_idea_intake_author_skill_first",
            "--work-root",
            str(tmp_path / "runs"),
            "--agent-command-template",
            f"{sys.executable} {failing_agent}",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 7
    assert "agent failed before transcript" in result.stderr
