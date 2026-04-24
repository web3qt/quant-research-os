from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts


@dataclass(frozen=True)
class AgentEvent:
    event_type: str
    name: str
    payload: dict[str, Any]
    raw: dict[str, Any]


@dataclass(frozen=True)
class BehaviorEvalResult:
    case_id: str
    passed: bool
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "errors": self.errors,
        }


def load_eval_cases(path: Path) -> dict[str, dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload.get("cases", [])}


def parse_transcript_jsonl(path: Path) -> list[AgentEvent]:
    events: list[AgentEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        event = _normalize_event(raw)
        if event is not None:
            events.append(event)
    return events


def assert_skill_triggered(events: list[AgentEvent], expected_skill: str) -> None:
    if not any(event.event_type == "skill_call" and event.name == expected_skill for event in events):
        raise AssertionError(f"expected skill was not triggered: {expected_skill}")


def assert_no_premature_tool_use(events: list[AgentEvent], *, before_skill: str) -> None:
    for event in events:
        if event.event_type == "skill_call" and event.name == before_skill:
            return
        if event.event_type == "tool_call":
            raise AssertionError(f"premature tool call before {before_skill}: {event.name}")


def assert_runtime_status(runtime_status: dict[str, Any], *, current_stage: str) -> None:
    observed = runtime_status.get("current_stage")
    if observed != current_stage:
        raise AssertionError(f"runtime current_stage mismatch: expected {current_stage}, found {observed}")


def assert_artifacts_present(lineage_root: Path, paths: list[str]) -> None:
    for relative_path in paths:
        if not (lineage_root / relative_path).exists():
            raise AssertionError(f"artifact missing: {relative_path}")


def assert_artifacts_absent(lineage_root: Path, paths: list[str]) -> None:
    for relative_path in paths:
        if (lineage_root / relative_path).exists():
            raise AssertionError(f"artifact should be absent: {relative_path}")


def evaluate_behavior_case(
    case: dict[str, Any],
    events: list[AgentEvent],
    *,
    lineage_root: Path,
    runtime_status: dict[str, Any] | None = None,
) -> BehaviorEvalResult:
    errors: list[str] = []

    checks = [
        lambda: assert_skill_triggered(events, case["expected_skill"]),
        lambda: _assert_premature_tool_policy(events, case),
        lambda: _assert_expected_runtime(case, runtime_status),
        lambda: assert_artifacts_present(lineage_root, case.get("expected_artifacts", {}).get("present", [])),
        lambda: assert_artifacts_absent(lineage_root, case.get("expected_artifacts", {}).get("absent", [])),
        lambda: _assert_validators(case, lineage_root),
    ]
    for check in checks:
        try:
            check()
        except AssertionError as exc:
            errors.append(str(exc))
    return BehaviorEvalResult(case_id=case["id"], passed=not errors, errors=errors)


def _normalize_event(raw: dict[str, Any]) -> AgentEvent | None:
    event_type = raw.get("event_type")
    if event_type in {"skill_call", "tool_call", "assistant_text", "command_output"}:
        return AgentEvent(
            event_type=str(event_type),
            name=str(raw.get("name", event_type)),
            payload=dict(raw.get("payload", {})),
            raw=raw,
        )

    if raw.get("type") == "tool_use":
        name = str(raw.get("name", ""))
        payload = raw.get("input", {}) if isinstance(raw.get("input", {}), dict) else {}
        if name == "Skill":
            skill_name = str(payload.get("skill", payload.get("name", "")))
            return AgentEvent(event_type="skill_call", name=skill_name, payload=payload, raw=raw)
        return AgentEvent(event_type="tool_call", name=name, payload=payload, raw=raw)

    if raw.get("type") == "assistant":
        return AgentEvent(event_type="assistant_text", name="assistant", payload=_assistant_payload(raw), raw=raw)

    if raw.get("type") == "command_output":
        return AgentEvent(event_type="command_output", name=str(raw.get("name", "command_output")), payload=raw, raw=raw)

    if raw.get("type") in {"item.started", "item.completed"}:
        return _normalize_codex_item(raw)

    return None


def _normalize_codex_item(raw: dict[str, Any]) -> AgentEvent | None:
    item = raw.get("item")
    if not isinstance(item, dict):
        return None

    item_type = item.get("type")
    if item_type == "agent_message":
        return AgentEvent(event_type="assistant_text", name="assistant", payload={"message": item}, raw=raw)

    if item_type == "command_execution":
        command = str(item.get("command", ""))
        payload = dict(item)
        skill_name = _skill_name_from_command(command)
        if skill_name is not None:
            return AgentEvent(event_type="skill_call", name=skill_name, payload=payload, raw=raw)
        return AgentEvent(event_type="tool_call", name="command_execution", payload=payload, raw=raw)

    return None


def _skill_name_from_command(command: str) -> str | None:
    superpowers_match = re.search(r"/superpowers/skills/([^/]+)/SKILL\.md\b", command)
    if superpowers_match:
        return f"superpowers:{superpowers_match.group(1)}"

    match = re.search(r"/skills/([^/]+)/SKILL\.md\b", command)
    if match:
        return match.group(1)
    return None


def _assistant_payload(raw: dict[str, Any]) -> dict[str, Any]:
    message = raw.get("message")
    if isinstance(message, dict):
        return {"message": message}
    return {}


def _assert_premature_tool_policy(events: list[AgentEvent], case: dict[str, Any]) -> None:
    if case.get("premature_tool_policy") == "forbid_before_expected_skill":
        assert_no_premature_tool_use(events, before_skill=case["expected_skill"])


def _assert_expected_runtime(case: dict[str, Any], runtime_status: dict[str, Any] | None) -> None:
    expected_runtime = case.get("expected_runtime")
    if not expected_runtime:
        return
    if runtime_status is None:
        raise AssertionError("runtime status payload is required for this case")
    if "current_stage" in expected_runtime:
        assert_runtime_status(runtime_status, current_stage=expected_runtime["current_stage"])


def _assert_validators(case: dict[str, Any], lineage_root: Path) -> None:
    for validator in case.get("validators", []):
        stage = validator["stage"]
        contract = load_artifact_contract(stage)
        stage_dir = lineage_root / str(contract["stage_dir"])
        result = validate_stage_artifacts(stage_dir, contract)
        if not result.valid:
            raise AssertionError(f"{stage} artifact validator failed: {'; '.join(result.errors)}")
