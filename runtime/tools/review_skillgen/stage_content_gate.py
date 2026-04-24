from __future__ import annotations

import csv
import json
import signal
import tempfile
import warnings
from pathlib import Path
from typing import Any, Iterator

import yaml

# 单次 parquet 检查的超时秒数。
PARQUET_CHECK_TIMEOUT_SECONDS = 120


class ParquetCheckTimeout(Exception):
    """parquet gate 检查超时。"""


def find_stage_file(stage_dir: Path, patterns: list[str]) -> Path | None:
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


def check_required_outputs(stage_dir: Path, required_outputs: list[str]) -> list[str]:
    return [item for item in required_outputs if not (stage_dir / item).exists()]


def check_global_evidence(stage_dir: Path, stage_checks: dict[str, Any]) -> list[str]:
    findings: list[str] = []

    if not (stage_dir / "artifact_catalog.md").exists():
        findings.append("Missing required global evidence: artifact_catalog.md")

    if find_stage_file(stage_dir, ["field_dictionary.md", "*_fields.md"]) is None:
        findings.append("Missing required global evidence: field_dictionary.md or *_fields.md")

    if find_stage_file(stage_dir, ["run_manifest.json", "repro_manifest.json", "*run_manifest.json"]) is None:
        findings.append("Missing required global evidence: run_manifest.json or repro_manifest.json")

    recommended_gate_doc = stage_checks.get("recommended_gate_doc")
    if recommended_gate_doc and not (stage_dir / recommended_gate_doc).exists():
        findings.append(f"Missing recommended gate document: {recommended_gate_doc}")

    return findings


def _is_automatable_evidence(pattern: str) -> bool:
    return pattern.endswith("/") or "*" in pattern or "." in Path(pattern).name


def check_stage_evidence(stage_dir: Path, checks: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    reservations: list[str] = []

    for check in checks:
        evidence_patterns = [item for item in check.get("evidence", []) if _is_automatable_evidence(item)]
        if not evidence_patterns:
            continue

        if any(find_stage_file(stage_dir, [pattern]) is not None for pattern in evidence_patterns):
            continue

        message = f"{check['id']}: missing evidence for '{check['check']}'"
        if check.get("severity") == "reservation":
            reservations.append(message)
        else:
            blocking.append(message)

    return blocking, reservations


def read_structured_payload(path: Path, fmt: str) -> Any:
    if fmt == "json":
        return json.loads(path.read_text(encoding="utf-8"))
    if fmt == "yaml":
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise ValueError(f"unsupported structured artifact format: {fmt}")


def read_tabular_rows(path: Path, fmt: str) -> list[dict[str, Any]]:
    if fmt == "csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    if fmt == "parquet":
        import polars as pl

        return pl.read_parquet(path).to_dicts()
    raise ValueError(f"unsupported tabular artifact format: {fmt}")


def parquet_row_count(path: Path) -> int:
    import polars as pl

    return pl.scan_parquet(path).select(pl.len()).collect().item()


def parquet_iter_rows(path: Path, *, columns: list[str] | None = None) -> Iterator[dict[str, Any]]:
    import polars as pl

    lf = pl.scan_parquet(path)
    if columns:
        lf = lf.select(columns)
    yield from lf.collect().iter_rows(named=True)


def parquet_find_duplicate_key(path: Path, *, fields: list[str]) -> tuple[Any, ...] | None:
    import polars as pl

    df = pl.scan_parquet(path).select(fields).collect()
    dup_mask = df.is_duplicated()
    if dup_mask.any():
        return tuple(df.filter(dup_mask).row(0))
    return None


def resolve_field_path(payload: Any, field_path: str) -> Any:
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


def _run_with_timeout(func, timeout_seconds: int):
    """在 Unix 上用 SIGALRM 给 func 加超时保护。超时抛 ParquetCheckTimeout。"""
    old_handler = signal.signal(signal.SIGALRM, lambda _sig, _frame: (_ for _ in ()).throw(ParquetCheckTimeout("parquet gate check timed out")))
    signal.alarm(timeout_seconds)
    try:
        return func()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def check_structural_gates(author_formal_dir: Path, structural_checks: list[dict[str, Any]], *, timeout_seconds: int = PARQUET_CHECK_TIMEOUT_SECONDS) -> list[str]:
    findings: list[str] = []

    for check in structural_checks:
        artifact_path = author_formal_dir / str(check["artifact"])
        fmt = str(check["format"])
        check_type = str(check["check_type"])

        # parquet 格式的检查走超时保护
        if fmt == "parquet":
            try:
                result = _run_with_timeout(
                    lambda c=check, ap=artifact_path, ct=check_type: _check_single_structural_gate(ap, c, ct),
                    timeout_seconds=timeout_seconds,
                )
                if result is not None:
                    findings.append(result)
            except ParquetCheckTimeout:
                findings.append(f"{check['id']}: parquet gate check timed out after {timeout_seconds}s for {check['artifact']}")
            continue

        try:
            result = _check_single_structural_gate(artifact_path, check, check_type)
            if result is not None:
                findings.append(result)
        except Exception as exc:
            findings.append(f"{check['id']}: structural gate evaluation failed for {check['artifact']}: {exc}")

    return findings


def _check_single_structural_gate(artifact_path: Path, check: dict[str, Any], check_type: str) -> str | None:
    """执行单条 structural gate 检查。返回 finding 字符串或 None。"""
    fmt = str(check["format"])

    if check_type in {"non_empty", "enum_in"}:
        payload = read_structured_payload(artifact_path, fmt)
        field_value = resolve_field_path(payload, str(check["field"]))
        if check_type == "non_empty":
            if not _is_non_empty_value(field_value):
                return f"{check['id']}: {check['message']}; observed={field_value!r}"
        elif field_value not in list(check.get("allowed_values", [])):
            return f"{check['id']}: {check['message']}; observed={field_value!r}"
        return None

    if check_type == "row_count_gt":
        threshold = int(check["threshold"])
        if fmt == "parquet":
            row_count = parquet_row_count(artifact_path)
        else:
            row_count = len(read_tabular_rows(artifact_path, fmt))
        if row_count <= threshold:
            return f"{check['id']}: {check['message']}; observed_row_count={row_count}"
        return None

    if check_type == "unique_key":
        fields = [str(field) for field in check.get("fields", [])]
        if not fields:
            raise ValueError("unique_key requires fields")
        if fmt == "parquet":
            duplicate_key = parquet_find_duplicate_key(artifact_path, fields=fields)
        else:
            seen: set[tuple[Any, ...]] = set()
            duplicate_key: tuple[Any, ...] | None = None
            for row in read_tabular_rows(artifact_path, fmt):
                key = tuple(row.get(field) for field in fields)
                if key in seen:
                    duplicate_key = key
                    break
                seen.add(key)
        if duplicate_key is not None:
            return f"{check['id']}: {check['message']}; observed_duplicate_key={duplicate_key!r}"
        return None

    raise ValueError(f"unsupported structural check type: {check_type}")


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
        import polars as pl

        return pl.scan_parquet(artifact_path).select(field).collect().to_series().to_list()

    raise ValueError(f"unsupported metric artifact format: {fmt}")


def _resolve_metric_threshold(author_formal_dir: Path, check: dict[str, Any]) -> float:
    if "threshold" in check:
        return float(check["threshold"])

    threshold_artifact = check.get("threshold_artifact")
    threshold_format = check.get("threshold_format")
    threshold_field = check.get("threshold_field")
    if threshold_artifact and threshold_format and threshold_field:
        payload = read_structured_payload(author_formal_dir / str(threshold_artifact), str(threshold_format))
        value = resolve_field_path(payload, str(threshold_field))
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


def check_metric_gates(author_formal_dir: Path, metric_checks: list[dict[str, Any]], *, timeout_seconds: int = PARQUET_CHECK_TIMEOUT_SECONDS) -> list[str]:
    findings: list[str] = []

    for check in metric_checks:
        fmt = str(check.get("format", ""))

        # parquet 格式的 metric 读取走超时保护
        if fmt == "parquet":
            try:
                values = _run_with_timeout(
                    lambda c=check: _read_metric_values(author_formal_dir, c),
                    timeout_seconds=timeout_seconds,
                )
            except ParquetCheckTimeout:
                findings.append(f"{check['id']}: parquet metric gate timed out after {timeout_seconds}s for {check['artifact']}")
                continue
            except Exception as exc:
                findings.append(f"{check['id']}: metric gate evaluation failed for {check['artifact']}: {exc}")
                continue
        else:
            try:
                values = _read_metric_values(author_formal_dir, check)
            except Exception as exc:
                findings.append(f"{check['id']}: metric gate evaluation failed for {check['artifact']}: {exc}")
                continue

        try:
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
