from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = ROOT / "templates" / "skills" / "review-stage" / "SKILL.md.tmpl"


def _render_simple_list(title: str, items: list[str]) -> str:
    lines = [f"{title}:"]
    if not items:
        lines.append("- 无")
        return "\n".join(lines)
    for item in items:
        lines.append(f"- {item}")
    return "\n".join(lines)


def _render_formal_gate(stage_contract: dict[str, Any]) -> str:
    lines = [f"阶段：{stage_contract['stage_name']}"]
    lines.append("")
    lines.append("正式门禁摘要：")

    pass_items = stage_contract.get("formal_gate", {}).get("pass_all_of", [])
    fail_items = stage_contract.get("formal_gate", {}).get("fail_any_of", [])

    if pass_items:
        lines.append("必须全部满足：")
        for item in pass_items:
            lines.append(f"- {item}")
    if fail_items:
        lines.append("以下任一情况都不得出现：")
        for item in fail_items:
            lines.append(f"- {item}")

    return "\n".join(lines)


def _render_checklist(stage_checks: list[dict[str, Any]]) -> str:
    lines = ["阶段检查项："]
    for check in stage_checks:
        severity = check.get("severity", "info")
        check_text = check.get("check", "")
        lines.append(f"- [{severity}] {check_text}")
    return "\n".join(lines)


def _render_audit_only(stage_contract: dict[str, Any]) -> str:
    return _render_simple_list("仅审计项", stage_contract.get("audit_only", []))


def _render_verdicts(gate_schema: dict[str, Any]) -> str:
    lines = []
    for verdict, meta in gate_schema.get("status_vocabulary", {}).items():
        meaning = meta.get("meaning", "")
        lines.append(f"- `{verdict}`: {meaning}")
    return "\n".join(lines)


def _render_rollback(stage_contract: dict[str, Any]) -> str:
    rollback = stage_contract.get("rollback_rules", {})
    lines = [f"- 默认 rollback stage：{rollback.get('default_rollback_stage', '未指定')}"]
    for item in rollback.get("allowed_modifications", []):
        lines.append(f"- 允许修改：{item}")
    for item in rollback.get("must_open_child_lineage_when", []):
        lines.append(f"- 以下情况必须开 child lineage：{item}")
    return "\n".join(lines)


def _render_downstream(stage_contract: dict[str, Any]) -> str:
    downstream = stage_contract.get("downstream_permissions", {})
    lines = []
    for item in downstream.get("may_advance_to", []):
        lines.append(f"- 可进入下游阶段：{item}")
    for item in downstream.get("frozen_outputs_consumable_by_next_stage", []):
        lines.append(f"- 下游可直接消费的冻结产物：{item}")
    blocked = list(downstream.get("next_stage_must_not_consume", [])) + list(
        downstream.get("next_stage_must_not_reestimate", [])
    )
    for item in blocked:
        lines.append(f"- 下游不得消费 / 重估：{item}")
    if not lines:
        lines.append("- 未指定")
    return "\n".join(lines)


def render_stage_skill(
    stage_key: str,
    skill_name: str,
    gate_schema: dict[str, Any],
    checklist_schema: dict[str, Any],
) -> str:
    stage_contract = gate_schema["stages"][stage_key]
    stage_checks = checklist_schema["stages"][stage_key]["checks"]
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        template.replace("{{SKILL_NAME}}", skill_name)
        .replace("{{STAGE_NAME}}", stage_contract["stage_name"])
        .replace("{{STAGE_PURPOSE}}", stage_contract["purpose"])
        .replace(
            "{{REQUIRED_INPUTS_BLOCK}}",
            _render_simple_list("必需输入", stage_contract.get("required_inputs", [])),
        )
        .replace(
            "{{REQUIRED_OUTPUTS_BLOCK}}",
            _render_simple_list("必需输出", stage_contract.get("required_outputs", [])),
        )
        .replace("{{FORMAL_GATE_BLOCK}}", _render_formal_gate(stage_contract))
        .replace("{{CHECKLIST_BLOCK}}", _render_checklist(stage_checks))
        .replace("{{AUDIT_ONLY_BLOCK}}", _render_audit_only(stage_contract))
        .replace("{{VERDICT_BLOCK}}", _render_verdicts(gate_schema))
        .replace("{{ROLLBACK_BLOCK}}", _render_rollback(stage_contract))
        .replace("{{DOWNSTREAM_BLOCK}}", _render_downstream(stage_contract))
    )
