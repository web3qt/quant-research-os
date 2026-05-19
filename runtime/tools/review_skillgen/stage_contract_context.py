from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from runtime.tools.artifact_contract_runtime import ARTIFACT_CONTRACTS
from runtime.tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from runtime.tools.review_skillgen.review_engine import CHECKLIST_PATH, GATES_PATH


STAGE_CONTRACT_CONTEXT_YAML_FILENAME = "stage_contract_context.yaml"
STAGE_CONTRACT_CONTEXT_MD_FILENAME = "stage_contract_context.md"
ROOT = Path(__file__).resolve().parents[3]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def _artifact_contract_relpath(stage_id: str) -> str:
    contract_path = ARTIFACT_CONTRACTS.get(stage_id)
    if contract_path is None:
        raise ValueError(f"REVIEW_CONTRACT_CONTEXT_MISSING: missing artifact contract for stage {stage_id}")
    return _repo_relative(contract_path)


def _semantic_code_for_stage(stage_id: str) -> str | None:
    return {
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
    }.get(stage_id)


def build_stage_contract_context(
    *,
    stage_id: str,
    lineage_id: str,
    review_cycle_id: str,
    author_materialization_digest: str,
    review_cycle_stage_dir: Path,
) -> dict[str, Any]:
    gates = load_gate_schema(GATES_PATH)
    checklist = load_checklist_schema(CHECKLIST_PATH)
    stage_contract = gates["stages"].get(stage_id)
    checklist_contract = checklist["stages"].get(stage_id)
    if stage_contract is None or checklist_contract is None:
        raise ValueError(f"REVIEW_CONTRACT_CONTEXT_MISSING: missing review contract entries for stage {stage_id}")

    artifact_relpath = _artifact_contract_relpath(stage_id)
    artifact_contract_path = ROOT / artifact_relpath
    artifact_text = artifact_contract_path.read_text(encoding="utf-8")
    gate_text = GATES_PATH.read_text(encoding="utf-8")
    checklist_text = CHECKLIST_PATH.read_text(encoding="utf-8")

    review_checks: dict[str, list[str]] = {"blocking": [], "reservation": [], "info": []}
    for item in checklist_contract.get("checks", []):
        severity = item.get("severity", "info")
        check_text = str(item["check"])
        if severity == "blocking":
            review_checks["blocking"].append(check_text)
        elif severity == "reservation":
            review_checks["reservation"].append(check_text)
        else:
            review_checks["info"].append(check_text)

    return {
        "lineage_id": lineage_id,
        "stage_id": stage_id,
        "stage_name": stage_contract["stage_name"],
        "review_cycle_id": review_cycle_id,
        "stage_dir": str(review_cycle_stage_dir),
        "contract_sources": {
            "workflow_stage_gate": _repo_relative(GATES_PATH),
            "review_checklist": _repo_relative(CHECKLIST_PATH),
            "artifact_contract": artifact_relpath,
        },
        "contract_digests": {
            _repo_relative(GATES_PATH): _sha256_text(gate_text),
            _repo_relative(CHECKLIST_PATH): _sha256_text(checklist_text),
            artifact_relpath: _sha256_text(artifact_text),
        },
        "author_materialization_digest": author_materialization_digest,
        "required_inputs": list(stage_contract.get("required_inputs", [])),
        "required_outputs": list(stage_contract.get("required_outputs", [])),
        "formal_gate": {
            "pass_all_of": list(stage_contract.get("formal_gate", {}).get("pass_all_of", [])),
            "fail_any_of": list(stage_contract.get("formal_gate", {}).get("fail_any_of", [])),
        },
        "review_checks": review_checks,
        "audit_only": list(stage_contract.get("audit_only", [])),
        "rollback_rules": dict(stage_contract.get("rollback_rules", {})),
        "downstream_permissions": dict(stage_contract.get("downstream_permissions", {})),
        "deterministic_preflight": {
            "required": True,
            "artifact_contract_code": "ARTIFACT-CONTRACT-001",
            "semantic_code": _semantic_code_for_stage(stage_id),
            "upstream_binding_scope": True,
        },
        "reviewer_focus": [
            "Review current stage formal package credibility.",
            "Review residual risks not covered by deterministic preflight.",
        ],
    }


def render_stage_contract_context_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['stage_name']} Review Context",
        "",
        "This file is the review-cycle-local rendering of current contracts and current author outputs.",
        "",
        "## Sources",
        f"- {payload['contract_sources']['workflow_stage_gate']}",
        f"- {payload['contract_sources']['review_checklist']}",
        f"- {payload['contract_sources']['artifact_contract']}",
        "",
        "## Reviewer Focus",
    ]
    for item in payload["reviewer_focus"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Formal Gate Summary"])
    for item in payload["formal_gate"]["pass_all_of"]:
        lines.append(f"- PASS requires: {item}")
    for item in payload["formal_gate"]["fail_any_of"]:
        lines.append(f"- FAIL if: {item}")

    return "\n".join(lines) + "\n"
