from __future__ import annotations

import csv
import json
import itertools
from pathlib import Path
import re
import tomllib
from typing import Any

import pyarrow.parquet as pq
import yaml


MACHINE_READABLE_SUFFIXES = {
    ".csv",
    ".json",
    ".jsonl",
    ".ndjson",
    ".parquet",
    ".toml",
    ".yaml",
    ".yml",
    ".tsv",
}

_PLACEHOLDER_PATTERNS = (
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bcontract-only\b", re.IGNORECASE),
    re.compile(r"\bstub\b", re.IGNORECASE),
    re.compile(r"占位"),
)

MAX_PARQUET_SAMPLE_ROWS = 1
MAX_CSV_SAMPLE_ROWS = 16
MAX_JSONL_SAMPLE_LINES = 16


def check_machine_artifact_realism(author_formal_dir: Path, machine_artifacts: list[str]) -> list[str]:
    findings: list[str] = []

    for machine_artifact in machine_artifacts:
        path = author_formal_dir / machine_artifact
        if not path.exists():
            continue
        if path.is_dir():
            findings.extend(_check_directory_realism(path, author_formal_dir))
            continue
        if path.suffix.lower() not in MACHINE_READABLE_SUFFIXES:
            continue
        finding = _check_single_machine_artifact(path, author_formal_dir)
        if finding is not None:
            findings.append(finding)

    return findings


def _check_directory_realism(directory: Path, author_formal_dir: Path) -> list[str]:
    findings: list[str] = []
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in MACHINE_READABLE_SUFFIXES:
            continue
        finding = _check_single_machine_artifact(path, author_formal_dir)
        if finding is not None:
            findings.append(finding)
    return findings


def _check_single_machine_artifact(path: Path, author_formal_dir: Path) -> str | None:
    rel_path = path.relative_to(author_formal_dir).as_posix()
    suffix = path.suffix.lower()

    if suffix == ".parquet":
        return _check_parquet_realism(path, rel_path)

    try:
        payload = _parse_structured_payload(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return f"ARTIFACT-REALISM-001: unreadable machine artifact rejected for {rel_path}: {exc}"
    except ValueError as exc:
        return f"ARTIFACT-REALISM-001: malformed machine artifact rejected for {rel_path}: {exc}"

    if not _payload_has_meaningful_content(payload):
        return f"ARTIFACT-REALISM-001: empty machine artifact rejected for {rel_path}"
    if _payload_has_placeholder_marker(payload):
        return f"ARTIFACT-REALISM-001: placeholder machine artifact rejected for {rel_path}"
    return None


def _check_parquet_realism(path: Path, rel_path: str) -> str | None:
    try:
        parquet_file = pq.ParquetFile(path)
    except Exception as exc:
        return f"ARTIFACT-REALISM-001: unreadable machine artifact rejected for {rel_path}: {exc}"
    metadata = parquet_file.metadata
    if metadata is None or metadata.num_rows <= 0 or metadata.num_columns <= 0 or metadata.num_row_groups <= 0:
        return f"ARTIFACT-REALISM-001: placeholder machine artifact rejected for {rel_path}"

    try:
        batch = next(parquet_file.iter_batches(batch_size=MAX_PARQUET_SAMPLE_ROWS))
    except StopIteration:
        return f"ARTIFACT-REALISM-001: empty machine artifact rejected for {rel_path}"
    except Exception as exc:
        return f"ARTIFACT-REALISM-001: unreadable machine artifact rejected for {rel_path}: {exc}"

    if batch.num_rows <= 0 or batch.num_columns <= 0:
        return f"ARTIFACT-REALISM-001: empty machine artifact rejected for {rel_path}"

    sample_payload = {
        name: column[0].as_py()
        for name, column in zip(batch.schema.names, batch.columns, strict=False)
    }
    if not _payload_has_meaningful_content(sample_payload):
        return f"ARTIFACT-REALISM-001: empty machine artifact rejected for {rel_path}"
    if _payload_has_placeholder_marker(sample_payload):
        return f"ARTIFACT-REALISM-001: placeholder machine artifact rejected for {rel_path}"
    return None


def _parse_structured_payload(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix == ".json" or suffix in {".jsonl", ".ndjson"}:
        return _parse_json_payload(path)
    if suffix in {".yaml", ".yml"}:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    if suffix == ".toml":
        with path.open("rb") as handle:
            return tomllib.load(handle)
    if suffix in {".csv", ".tsv"}:
        return _parse_tabular_payload(path, delimiter="\t" if suffix == ".tsv" else ",")
    raise ValueError(f"unsupported machine artifact format: {suffix}")


def _parse_json_payload(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix == ".jsonl" or suffix == ".ndjson":
        return _parse_jsonl_payload(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_jsonl_payload(path: Path) -> list[Any]:
    rows: list[Any] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if len(rows) >= MAX_JSONL_SAMPLE_LINES:
                break
    return rows


def _parse_tabular_payload(path: Path, *, delimiter: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        try:
            headers = next(reader)
        except StopIteration:
            return rows
        if _text_has_placeholder_marker(" ".join(headers)):
            return [{"__header__": " ".join(headers)}]
        for row in itertools.islice(reader, MAX_CSV_SAMPLE_ROWS):
            if not any(cell.strip() for cell in row):
                continue
            rows.append({headers[index]: value for index, value in enumerate(row) if index < len(headers)})
    return rows


def _payload_has_meaningful_content(payload: Any) -> bool:
    if payload is None:
        return False
    if isinstance(payload, str):
        return bool(payload.strip())
    if isinstance(payload, (bytes, bytearray)):
        return len(payload) > 0
    if isinstance(payload, dict):
        if not payload:
            return False
        return any(_payload_has_meaningful_content(value) for value in payload.values())
    if isinstance(payload, (list, tuple, set)):
        if not payload:
            return False
        return any(_payload_has_meaningful_content(item) for item in payload)
    return True


def _payload_has_placeholder_marker(payload: Any) -> bool:
    if isinstance(payload, str):
        return _text_has_placeholder_marker(payload)
    if isinstance(payload, dict):
        return any(_payload_has_placeholder_marker(value) for value in payload.values())
    if isinstance(payload, (list, tuple, set)):
        return any(_payload_has_placeholder_marker(item) for item in payload)
    return False


def _text_has_placeholder_marker(text: str) -> bool:
    return any(pattern.search(text) is not None for pattern in _PLACEHOLDER_PATTERNS)
