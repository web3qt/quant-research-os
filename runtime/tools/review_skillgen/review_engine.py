from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
import os
from typing import Any

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    FIX_REQUIRED_OUTCOME,
    ReviewerRuntimeIdentity,
    canonicalize_runtime_review_result,
    load_adversarial_review_request,
    load_adversarial_review_result,
    load_spawned_reviewer_receipt,
    resolve_closure_verdict,
    SPAWNED_REVIEWER_RECEIPT_FILENAME,
    validate_receipt_against_request,
    validate_result_against_request,
)
from runtime.tools.review_skillgen.closure_models import build_review_payload
from runtime.tools.review_skillgen.closure_writer import write_closure_artifacts
from runtime.tools.review_skillgen.context_inference import build_stage_context, infer_review_context
from runtime.tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from runtime.tools.review_skillgen.review_findings import load_review_findings_if_present


ROOT = Path(__file__).resolve().parents[3]
GATES_PATH = ROOT / "contracts" / "stages" / "workflow_stage_gates.yaml"
CHECKLIST_PATH = ROOT / "contracts" / "review" / "review_checklist_master.yaml"


def _find_stage_file(stage_dir: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        if "*" in pattern:
            matches = sorted(stage_dir.glob(pattern))
            if matches:
                return matches[0]
            continue

        candidate = stage_dir / pattern
        if candidate.exists():
            return candidate

    return None


def _check_required_outputs(stage_dir: Path, required_outputs: list[str]) -> list[str]:
    missing: list[str] = []
    for item in required_outputs:
        if not (stage_dir / item).exists():
            missing.append(item)
    return missing


def _check_global_evidence(stage_dir: Path, stage_checks: dict[str, Any]) -> list[str]:
    findings: list[str] = []

    if not (stage_dir / "artifact_catalog.md").exists():
        findings.append("Missing required global evidence: artifact_catalog.md")

    if _find_stage_file(stage_dir, ["field_dictionary.md", "*_fields.md"]) is None:
        findings.append("Missing required global evidence: field_dictionary.md or *_fields.md")

    if _find_stage_file(stage_dir, ["run_manifest.json", "repro_manifest.json"]) is None:
        findings.append("Missing required global evidence: run_manifest.json or repro_manifest.json")

    recommended_gate_doc = stage_checks.get("recommended_gate_doc")
    if recommended_gate_doc and not (stage_dir / recommended_gate_doc).exists():
        findings.append(f"Missing recommended gate document: {recommended_gate_doc}")

    return findings


def _is_automatable_evidence(pattern: str) -> bool:
    return pattern.endswith("/") or "*" in pattern or "." in Path(pattern).name


def _check_stage_evidence(stage_dir: Path, checks: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    reservations: list[str] = []

    for check in checks:
        evidence_patterns = [item for item in check.get("evidence", []) if _is_automatable_evidence(item)]
        if not evidence_patterns:
            continue

        if any(_find_stage_file(stage_dir, [pattern]) is not None for pattern in evidence_patterns):
            continue

        message = f"{check['id']}: missing evidence for '{check['check']}'"
        if check.get("severity") == "reservation":
            reservations.append(message)
        else:
            blocking.append(message)

    return blocking, reservations


def _read_structured_payload(path: Path, fmt: str) -> Any:
    if fmt == "json":
        return json.loads(path.read_text(encoding="utf-8"))
    if fmt == "yaml":
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise ValueError(f"unsupported structured artifact format: {fmt}")


def _read_tabular_rows(path: Path, fmt: str) -> list[dict[str, Any]]:
    if fmt == "csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    if fmt == "parquet":
        import pyarrow.parquet as pq

        return pq.read_table(path).to_pylist()
    raise ValueError(f"unsupported tabular artifact format: {fmt}")


def _resolve_field_path(payload: Any, field_path: str) -> Any:
    value = payload
    for part in field_path.split("."):
        if not isinstance(value, dict):
            raise ValueError(f"field path {field_path!r} is not addressable")
        value = value.get(part)
    return value


def _is_non_empty_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _check_structural_gates(author_formal_dir: Path, structural_checks: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []

    for check in structural_checks:
        artifact_path = author_formal_dir / str(check["artifact"])
        fmt = str(check["format"])
        check_type = str(check["check_type"])

        try:
            if check_type in {"non_empty", "enum_in"}:
                payload = _read_structured_payload(artifact_path, fmt)
                field_value = _resolve_field_path(payload, str(check["field"]))
                if check_type == "non_empty":
                    if not _is_non_empty_value(field_value):
                        findings.append(f"{check['id']}: {check['message']}; observed={field_value!r}")
                elif field_value not in list(check.get("allowed_values", [])):
                    findings.append(f"{check['id']}: {check['message']}; observed={field_value!r}")
                continue

            rows = _read_tabular_rows(artifact_path, fmt)
            if check_type == "row_count_gt":
                threshold = int(check["threshold"])
                if len(rows) <= threshold:
                    findings.append(f"{check['id']}: {check['message']}; observed_row_count={len(rows)}")
                continue

            if check_type == "unique_key":
                fields = [str(field) for field in check.get("fields", [])]
                if not fields:
                    raise ValueError("unique_key requires fields")
                seen: set[tuple[Any, ...]] = set()
                duplicate_key: tuple[Any, ...] | None = None
                for row in rows:
                    key = tuple(row.get(field) for field in fields)
                    if key in seen:
                        duplicate_key = key
                        break
                    seen.add(key)
                if duplicate_key is not None:
                    findings.append(f"{check['id']}: {check['message']}; observed_duplicate_key={duplicate_key!r}")
                continue

            raise ValueError(f"unsupported structural check type: {check_type}")
        except Exception as exc:
            findings.append(f"{check['id']}: structural gate evaluation failed for {check['artifact']}: {exc}")

    return findings


def _load_factor_role(lineage_root: Path) -> str | None:
    route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
    if not route_path.exists():
        return None
    data = yaml.safe_load(route_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return None
    factor_role = data.get("factor_role")
    if isinstance(factor_role, str) and factor_role.strip():
        return factor_role.strip()
    return None


def _coerce_metric_value(value: Any, value_type: str) -> Any:
    if value_type == "number":
        if isinstance(value, bool):
            raise ValueError("boolean is not a valid numeric value")
        return float(value)
    if value_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        raise ValueError(f"could not coerce {value!r} to boolean")
    raise ValueError(f"unsupported value_type: {value_type}")


def _read_metric_values(author_formal_dir: Path, check: dict[str, Any]) -> list[Any]:
    artifact_path = author_formal_dir / str(check["artifact"])
    fmt = str(check["format"])
    field = str(check["field"])

    if fmt == "json":
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        if field not in payload:
            raise ValueError(f"missing field {field!r} in {artifact_path.name}")
        return [payload[field]]

    if fmt == "csv":
        with artifact_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError(f"{artifact_path.name} has no rows")
        return [row[field] for row in rows if field in row]

    if fmt == "parquet":
        import pyarrow.parquet as pq

        table = pq.read_table(artifact_path, columns=[field])
        return table.column(field).to_pylist()

    raise ValueError(f"unsupported metric artifact format: {fmt}")


def _resolve_metric_threshold(author_formal_dir: Path, check: dict[str, Any]) -> float:
    if "threshold" in check:
        return float(check["threshold"])

    threshold_artifact = check.get("threshold_artifact")
    threshold_format = check.get("threshold_format")
    threshold_field = check.get("threshold_field")
    if threshold_artifact and threshold_format and threshold_field:
        payload = _read_structured_payload(author_formal_dir / str(threshold_artifact), str(threshold_format))
        value = _resolve_field_path(payload, str(threshold_field))
        return float(value)

    raise ValueError(f"metric gate {check['id']} missing threshold configuration")


def _metric_check_failed(value: Any, check: dict[str, Any]) -> bool:
    operator = str(check["operator"])
    value_type = str(check["value_type"])
    coerced = _coerce_metric_value(value, value_type)
    if operator == "gt":
        return not (coerced > float(check["threshold"]))
    if operator == "ge":
        return not (coerced >= float(check["threshold"]))
    if operator == "eq":
        expected = check.get("expected")
        if value_type == "boolean":
            expected = _coerce_metric_value(expected, value_type)
        return coerced != expected
    raise ValueError(f"unsupported operator: {operator}")


def _check_metric_gates(
    *,
    lineage_root: Path,
    author_formal_dir: Path,
    stage_contract: dict[str, Any],
) -> list[str]:
    findings: list[str] = []
    factor_role = _load_factor_role(lineage_root)

    for check in stage_contract.get("metric_gate_checks", []):
        factor_roles = check.get("factor_role_in", [])
        if factor_roles:
            if factor_role is None:
                findings.append(
                    f"{check['id']}: could not resolve factor_role for metric gate evaluation"
                )
                continue
            if factor_role not in factor_roles:
                continue

        try:
            values = _read_metric_values(author_formal_dir, check)
            threshold = _resolve_metric_threshold(author_formal_dir, check) if str(check["operator"]) in {"gt", "ge"} else None
        except Exception as exc:
            findings.append(f"{check['id']}: metric gate evaluation failed for {check['artifact']}: {exc}")
            continue

        if not values:
            findings.append(f"{check['id']}: metric gate {check['artifact']} produced no values")
            continue

        normalized_check = dict(check)
        if threshold is not None:
            normalized_check["threshold"] = threshold
        failures = [value for value in values if _metric_check_failed(value, normalized_check)]
        if failures:
            findings.append(f"{check['id']}: {check['message']}; observed={failures[0]!r}")

    return findings


def _resolve_verdict(
    review_result: dict[str, Any],
    reviewer_findings: dict[str, Any],
    blocking_findings: list[str],
    reservation_findings: list[str],
) -> tuple[str | None, str]:
    review_loop_outcome = review_result["review_loop_outcome"]
    recommended = reviewer_findings.get("recommended_verdict")
    final_verdict = resolve_closure_verdict(review_loop_outcome)
    if review_loop_outcome == FIX_REQUIRED_OUTCOME:
        return None, FIX_REQUIRED_OUTCOME

    if recommended:
        gates = load_gate_schema(GATES_PATH)
        passing_verdicts = set(gates["review_passing_verdicts"])
        retry_verdicts = set(gates["review_retry_verdicts"])
        if blocking_findings and recommended in passing_verdicts:
            return "RETRY", "CLOSURE_READY_RETRY"
        if recommended in retry_verdicts:
            if not reviewer_findings.get("rollback_stage") or not reviewer_findings.get("allowed_modifications"):
                raise ValueError(f"{recommended} requires rollback_stage and allowed_modifications")
        return recommended, review_loop_outcome

    if blocking_findings:
        return "RETRY", review_loop_outcome
    if reservation_findings:
        return final_verdict or "CONDITIONAL PASS", review_loop_outcome
    return final_verdict or "PASS", review_loop_outcome


def _runtime_identity(
    *,
    reviewer_identity: str | None,
    reviewer_role: str | None,
    reviewer_session_id: str | None,
    reviewer_mode: str | None,
) -> ReviewerRuntimeIdentity:
    resolved_identity = reviewer_identity or os.environ.get("QROS_REVIEWER_ID") or "codex-reviewer"
    resolved_role = reviewer_role or os.environ.get("QROS_REVIEWER_ROLE") or "reviewer"
    resolved_session = reviewer_session_id or os.environ.get("QROS_REVIEWER_SESSION_ID") or "local-review-session"
    resolved_mode = reviewer_mode or os.environ.get("QROS_REVIEWER_MODE") or "adversarial"
    return ReviewerRuntimeIdentity(
        reviewer_identity=resolved_identity,
        reviewer_role=resolved_role,
        reviewer_session_id=resolved_session,
        reviewer_mode=resolved_mode,
    )


def run_stage_review(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
    reviewer_identity: str | None = None,
    reviewer_role: str | None = None,
    reviewer_session_id: str | None = None,
    reviewer_mode: str | None = None,
) -> dict[str, Any]:
    if explicit_context is not None:
        inferred = build_stage_context(Path(explicit_context["stage_dir"]))
        context = {
            **inferred,
            **explicit_context,
        }
    else:
        context = infer_review_context(cwd or Path.cwd())
    stage_dir = Path(context["stage_dir"]).resolve()
    lineage_root = Path(context["lineage_root"]).resolve()
    author_formal_dir = Path(context["author_formal_dir"]).resolve()
    review_request_dir = Path(context["review_request_dir"]).resolve()
    review_result_dir = Path(context["review_result_dir"]).resolve()
    stage = context["stage"]
    lineage_id = context["lineage_id"]

    gates = load_gate_schema(GATES_PATH)
    checklist = load_checklist_schema(CHECKLIST_PATH)
    stage_contract = gates["stages"][stage]
    stage_checks = checklist["stages"][stage]

    request_path = review_request_dir / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    receipt_path = review_request_dir / SPAWNED_REVIEWER_RECEIPT_FILENAME
    result_path = review_result_dir / ADVERSARIAL_REVIEW_RESULT_FILENAME
    request_payload = load_adversarial_review_request(request_path)
    runtime_identity = _runtime_identity(
        reviewer_identity=reviewer_identity,
        reviewer_role=reviewer_role,
        reviewer_session_id=reviewer_session_id,
        reviewer_mode=reviewer_mode,
    )
    receipt_payload = load_spawned_reviewer_receipt(receipt_path)
    validate_receipt_against_request(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=runtime_identity,
    )
    review_result = load_adversarial_review_result(result_path)
    review_result = canonicalize_runtime_review_result(
        result_path,
        request_payload=request_payload,
        result_payload=review_result,
    )
    validate_result_against_request(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        result_payload=review_result,
        runtime_identity=runtime_identity,
    )
    reviewer_findings = load_review_findings_if_present(review_result_dir / "review_findings.yaml")

    missing_required_outputs = _check_required_outputs(author_formal_dir, stage_contract.get("required_outputs", []))
    blocking_findings = [f"Missing required output: {item}" for item in missing_required_outputs]
    blocking_findings.extend(_check_global_evidence(author_formal_dir, stage_checks))

    auto_stage_blocking, auto_stage_reservations = _check_stage_evidence(author_formal_dir, stage_checks.get("checks", []))
    blocking_findings.extend(auto_stage_blocking)
    # 前半段 CSF stage 先执行合同/结构 gate，确保语义冻结和可复现性先过，再谈后段统计表现。
    blocking_findings.extend(_check_structural_gates(author_formal_dir, stage_contract.get("structural_gate_checks", [])))
    # 先把合同里写明的关键数值门禁落成真实 blocking findings，避免“有产物但坏结果也放行”。
    blocking_findings.extend(
        _check_metric_gates(
            lineage_root=lineage_root,
            author_formal_dir=author_formal_dir,
            stage_contract=stage_contract,
        )
    )

    reservation_findings = list(auto_stage_reservations)
    reservation_findings.extend(reviewer_findings["reservation_findings"])

    blocking_findings.extend(reviewer_findings["blocking_findings"])
    blocking_findings.extend(review_result["blocking_findings"])
    info_findings = list(reviewer_findings["info_findings"])
    info_findings.extend(review_result["info_findings"])
    residual_risks = list(reviewer_findings["residual_risks"])
    residual_risks.extend(review_result["residual_risks"])

    final_verdict, review_loop_outcome = _resolve_verdict(
        review_result,
        reviewer_findings,
        blocking_findings,
        reservation_findings,
    )
    rollback_stage = review_result.get("rollback_stage") or reviewer_findings.get("rollback_stage") or stage_contract.get("rollback_rules", {}).get(
        "default_rollback_stage"
    )
    allowed_modifications = review_result.get("allowed_modifications") or reviewer_findings.get("allowed_modifications") or list(
        stage_contract.get("rollback_rules", {}).get("allowed_modifications", [])
    )
    downstream_permissions = review_result.get("downstream_permissions") or reviewer_findings.get("downstream_permissions") or list(
        stage_contract.get("downstream_permissions", {}).get("may_advance_to", [])
    )
    review_timestamp_utc = datetime.now(timezone.utc).isoformat()

    common_payload = {
        "lineage_id": lineage_id,
        "stage": stage,
        "review_loop_outcome": review_loop_outcome,
        "stage_status": review_loop_outcome,
        "blocking_findings": blocking_findings,
        "reservation_findings": reservation_findings,
        "info_findings": info_findings,
        "residual_risks": residual_risks,
        "review_timestamp_utc": review_timestamp_utc,
        "reviewer_identity": review_result["reviewer_identity"],
        "reviewer_role": review_result["reviewer_role"],
        "reviewer_session_id": review_result["reviewer_session_id"],
        "reviewer_mode": review_result["reviewer_mode"],
        "author_identity": request_payload["author_identity"],
        "author_session_id": request_payload["author_session_id"],
        "rollback_stage": rollback_stage,
        "allowed_modifications": allowed_modifications,
        "downstream_permissions": downstream_permissions,
        "review_scope": {
            "required_program_dir": request_payload["required_program_dir"],
            "required_program_entrypoint": request_payload["required_program_entrypoint"],
            "required_artifact_paths": request_payload["required_artifact_paths"],
            "required_provenance_paths": request_payload["required_provenance_paths"],
            "reviewed_program_dir": review_result["reviewed_program_dir"],
            "reviewed_program_entrypoint": review_result["reviewed_program_entrypoint"],
            "reviewed_artifact_paths": review_result["reviewed_artifact_paths"],
            "reviewed_provenance_paths": review_result["reviewed_provenance_paths"],
        },
        "adversarial_review_request": request_payload,
        "spawned_reviewer_receipt": receipt_payload,
        "adversarial_review_result": review_result,
        "contract_source": str(GATES_PATH.relative_to(ROOT)),
        "checklist_source": str(CHECKLIST_PATH.relative_to(ROOT)),
        "required_outputs_checked": {
            "expected": list(stage_contract.get("required_outputs", [])),
            "missing": missing_required_outputs,
        },
        "evidence_summary": {
            "recommended_gate_doc": stage_checks.get("recommended_gate_doc"),
            "review_summary": review_result.get("review_summary"),
        },
    }

    if review_loop_outcome == FIX_REQUIRED_OUTCOME:
        return {
            **common_payload,
            "final_verdict": None,
        }

    payload = build_review_payload(
        lineage_id=lineage_id,
        stage=stage,
        final_verdict=final_verdict,
        stage_status=final_verdict,
        blocking_findings=blocking_findings,
        reservation_findings=reservation_findings,
        info_findings=info_findings,
        residual_risks=residual_risks,
        review_timestamp_utc=review_timestamp_utc,
        reviewer_identity=review_result["reviewer_identity"],
        reviewer_role=review_result["reviewer_role"],
        reviewer_session_id=review_result["reviewer_session_id"],
        reviewer_mode=review_result["reviewer_mode"],
        author_identity=request_payload["author_identity"],
        author_session_id=request_payload["author_session_id"],
        review_loop_outcome=review_loop_outcome,
        rollback_stage=rollback_stage,
        allowed_modifications=allowed_modifications,
        downstream_permissions=downstream_permissions,
        review_scope=common_payload["review_scope"],
        adversarial_review_request=request_payload,
        spawned_reviewer_receipt=receipt_payload,
        adversarial_review_result=review_result,
        contract_source=common_payload["contract_source"],
        checklist_source=common_payload["checklist_source"],
        required_outputs_checked=common_payload["required_outputs_checked"],
        evidence_summary=common_payload["evidence_summary"],
    )

    write_closure_artifacts(
        payload,
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
    )
    return payload
