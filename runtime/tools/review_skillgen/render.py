from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = ROOT / "templates" / "skills" / "review-stage" / "SKILL.md.tmpl"

HOST_VARS: dict[str, dict[str, str]] = {
    "codex": {
        "HOST_LABEL": "Codex",
        "HOST_KEY": "codex",
        "HOST_SPAWN_TOOL": "`spawn_agent`",
        "HOST_ISOLATION_POLICY": "且 `fork_context` 必须是 `false`",
        "HOST_HANDOFF_METHOD": "`send_input`",
        "HOST_SPAWNED_AGENT_ID_FLAG": "--reviewer-agent-id",
    },
    "claude-code": {
        "HOST_LABEL": "Claude Code",
        "HOST_KEY": "claude-code",
        "HOST_SPAWN_TOOL": "通过 `.claude-plugin/agents/qros-reviewer.md` 创建 task",
        "HOST_ISOLATION_POLICY": "子代理上下文由 Claude Code 平台隔离保证",
        "HOST_HANDOFF_METHOD": "将 handoff manifest 作为 task prompt 传入",
        "HOST_SPAWNED_AGENT_ID_FLAG": "--reviewer-agent-id",
    },
}


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


def _render_deterministic_preflight(stage_key: str) -> str:
    semantic_codes = {
        "csf_data_ready": "CSF-DATA-SEMANTIC-001",
        "csf_signal_ready": "CSF-SIGNAL-SEMANTIC-001",
        "csf_train_freeze": "CSF-TRAIN-SEMANTIC-001",
        "csf_test_evidence": "CSF-TEST-SEMANTIC-001",
        "csf_backtest_ready": "CSF-BACKTEST-SEMANTIC-001",
        "csf_holdout_validation": "CSF-HOLDOUT-SEMANTIC-001",
        "tss_data_ready": "TSS-DATA-SEMANTIC-001",
        "tss_signal_ready": "TSS-SIGNAL-SEMANTIC-001",
        "tss_train_freeze": "TSS-TRAIN-SEMANTIC-001",
        "tss_test_evidence": "TSS-TEST-SEMANTIC-001",
        "tss_backtest_ready": "TSS-BACKTEST-SEMANTIC-001",
        "tss_holdout_validation": "TSS-HOLDOUT-SEMANTIC-001",
    }
    artifact_contracts = {
        "csf_data_ready": "contracts/artifacts/csf_data_ready_artifacts.yaml",
        "csf_signal_ready": "contracts/artifacts/csf_signal_ready_artifacts.yaml",
        "csf_train_freeze": "contracts/artifacts/csf_train_freeze_artifacts.yaml",
        "csf_test_evidence": "contracts/artifacts/csf_test_evidence_artifacts.yaml",
        "csf_backtest_ready": "contracts/artifacts/csf_backtest_ready_artifacts.yaml",
        "csf_holdout_validation": "contracts/artifacts/csf_holdout_validation_artifacts.yaml",
        "tss_data_ready": "contracts/artifacts/tss_data_ready_artifacts.yaml",
        "tss_signal_ready": "contracts/artifacts/tss_signal_ready_artifacts.yaml",
        "tss_train_freeze": "contracts/artifacts/tss_train_freeze_artifacts.yaml",
        "tss_test_evidence": "contracts/artifacts/tss_test_evidence_artifacts.yaml",
        "tss_backtest_ready": "contracts/artifacts/tss_backtest_ready_artifacts.yaml",
        "tss_holdout_validation": "contracts/artifacts/tss_holdout_validation_artifacts.yaml",
    }
    semantic_code = semantic_codes.get(stage_key)
    if semantic_code is None:
        return (
            "- 进入 reviewer lane 前必须先完成 deterministic review-ready 自查；"
            "若 preflight 有 blocking finding，必须先修 author outputs。"
        )
    artifact_contract = artifact_contracts[stage_key]
    stage_specific: list[str] = []
    if stage_key == "csf_backtest_ready":
        stage_specific = [
            "- 必须检查 `return_accounting_provenance.yaml` 是否存在，并确认 `portfolio_summary.parquet` 与 `csf_backtest_gate_table.csv` 的 formal metrics 受该 provenance 支撑",
            "- 如果 formal return field、formula 或 stage-local program 使用 `mom_ret`、signal/factor score、rank score、neutralized factor 或其他 proxy PnL，必须判为 blocking",
            "- proxy PnL 只能作为 diagnostic evidence；一旦进入 formal gate metrics，不得进入 csf_holdout_validation",
            "- 如果缺少 tradable return source，应要求修复当前 `csf_backtest_ready` stage 或进入 failure handling；除非需要改变 mandate 路线或已有下游 freeze 依赖，否则不要默认开 child lineage",
        ]
    return "\n".join(
        [
            f"- reviewer 不替 runtime 重定义字段；artifact shape 以 `{artifact_contract}` 与 deterministic preflight 为准",
            f"- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage {stage_key}`，并通过 deterministic preflight",
            f"- preflight 中的 `ARTIFACT-CONTRACT-001` 与 `{semantic_code}` 都是 review 前阻断项",
            "- preflight 覆盖 artifact contract validation、semantic validation 与 upstream binding validation；reviewer 仍需审查机制和残留风险",
            *stage_specific,
        ]
    )


def render_stage_skill(
    stage_key: str,
    skill_name: str,
    gate_schema: dict[str, Any],
    checklist_schema: dict[str, Any],
    host: str = "codex",
) -> str:
    stage_contract = gate_schema["stages"][stage_key]
    stage_checks = checklist_schema["stages"][stage_key]["checks"]
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    host_vars = HOST_VARS.get(host, HOST_VARS["codex"])
    rendered = template
    for var_name, var_value in host_vars.items():
        rendered = rendered.replace("{{" + var_name + "}}", var_value)
    rendered = (
        rendered.replace("{{SKILL_NAME}}", skill_name)
        .replace("{{STAGE_KEY}}", stage_key)
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
        .replace("{{ROLLBACK_BLOCK}}", _render_rollback(stage_contract))
        .replace("{{DOWNSTREAM_BLOCK}}", _render_downstream(stage_contract))
        .replace("{{DETERMINISTIC_PREFLIGHT_BLOCK}}", _render_deterministic_preflight(stage_key))
    )
    return rendered
