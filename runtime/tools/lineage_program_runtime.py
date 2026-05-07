from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Literal, Sequence

import yaml

from runtime.tools.review_skillgen.context_inference import build_stage_context
from runtime.tools.stage_program_identity import validate_stage_program_identity


StageId = Literal[
    "mandate",
    "data_ready",
    "signal_ready",
    "train_freeze",
    "test_evidence",
    "backtest_ready",
    "holdout_validation",
    "tss_data_ready",
    "tss_signal_ready",
    "tss_train_freeze",
    "tss_test_evidence",
    "tss_backtest_ready",
    "tss_holdout_validation",
    "csf_data_ready",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
]
RouteId = Literal["route_neutral", "time_series_signal", "cross_sectional_factor"]
EntryType = Literal["python", "rust", "bash"]

PROVENANCE_MANIFEST_FILE = "program_execution_manifest.json"
PROGRAM_MANIFEST_FILE = "stage_program.yaml"
ALLOWED_DEPENDS_ON_PROGRAMS = {
    "mandate",
    "time_series/data_ready",
    "time_series/signal_ready",
    "time_series/train_freeze",
    "time_series/test_evidence",
    "time_series/backtest_ready",
    "time_series/holdout_validation",
    "time_series_signal/tss_data_ready",
    "time_series_signal/tss_signal_ready",
    "time_series_signal/tss_train_freeze",
    "time_series_signal/tss_test_evidence",
    "time_series_signal/tss_backtest_ready",
    "time_series_signal/tss_holdout_validation",
    "cross_sectional_factor/data_ready",
    "cross_sectional_factor/signal_ready",
    "cross_sectional_factor/train_freeze",
    "cross_sectional_factor/test_evidence",
    "cross_sectional_factor/backtest_ready",
    "cross_sectional_factor/holdout_validation",
}
HASH_EXCLUDED_FILES = {PROVENANCE_MANIFEST_FILE}
HASH_EXCLUDED_DIRS = {".cache", "__pycache__", ".pytest_cache"}
CSF_STAGE_PROGRAM_LOCAL_NAMES = {
    "csf_data_ready": "data_ready",
    "csf_signal_ready": "signal_ready",
    "csf_train_freeze": "train_freeze",
    "csf_test_evidence": "test_evidence",
    "csf_backtest_ready": "backtest_ready",
    "csf_holdout_validation": "holdout_validation",
}


class StageProgramRuntimeError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.message = message


@dataclass(frozen=True)
class ProgramRef:
    kind: str
    path: str
    required: bool


@dataclass(frozen=True)
class AuthoredBy:
    agent_id: str
    agent_role: str
    session_id: str


@dataclass(frozen=True)
class ValidatedStageProgram:
    stage_id: StageId
    route: RouteId
    lineage_id: str
    program_dir: Path
    manifest_path: Path
    entrypoint_path: Path
    entrypoint: str
    entry_type: EntryType
    inputs: tuple[ProgramRef, ...]
    outputs: tuple[ProgramRef, ...]
    depends_on_programs: tuple[str, ...]
    shared_libs: tuple[str, ...]
    authored_by: AuthoredBy
    program_hash: str


@dataclass(frozen=True)
class ProgramInspection:
    program_dir: Path
    manifest_path: Path
    required_program_dir: str
    required_program_entrypoint: str | None
    program_contract_status: str
    error_code: str | None
    error_message: str | None


@dataclass(frozen=True)
class InvocationResult:
    stage_dir: Path
    manifest_path: Path
    output_refs: tuple[str, ...]
    input_refs: tuple[str, ...]
    provenance_path: Path


@dataclass(frozen=True)
class StageProgramSpec:
    stage_id: StageId
    route: RouteId
    stage_dir_name: str
    required_outputs: tuple[str, ...]


def stage_program_relative_dir(stage_id: StageId, route: RouteId) -> Path:
    if stage_id == "mandate":
        if route != "route_neutral":
            raise StageProgramRuntimeError(
                "STAGE_PROGRAM_INVALID",
                f"mandate stage requires route_neutral, got {route}",
            )
        return Path("program") / "mandate"
    if route == "time_series_signal":
        if stage_id.startswith("tss_"):
            return Path("program") / "time_series_signal" / stage_id
        return Path("program") / "time_series" / stage_id
    if route == "cross_sectional_factor":
        # CSF 的 gate identity 使用 csf_*，但 lineage-local program 目录沿用无前缀名称。
        local_name = CSF_STAGE_PROGRAM_LOCAL_NAMES.get(stage_id, stage_id)
        return Path("program") / "cross_sectional_factor" / local_name
    raise StageProgramRuntimeError(
        "STAGE_PROGRAM_INVALID",
        f"unsupported route for stage program resolution: {route}",
    )


def stage_program_dir(lineage_root: Path, stage_id: StageId, route: RouteId) -> Path:
    return lineage_root.resolve() / stage_program_relative_dir(stage_id, route)


def _author_formal_dir(stage_dir: Path) -> Path:
    stage_dir = stage_dir.resolve()
    if stage_dir.name == "formal" and stage_dir.parent.name == "author":
        return stage_dir
    return build_stage_context(stage_dir)["author_formal_dir"]



def provenance_manifest_path(stage_dir: Path) -> Path:
    return _author_formal_dir(stage_dir) / PROVENANCE_MANIFEST_FILE



def load_provenance_manifest(stage_dir: Path) -> dict[str, Any] | None:
    path = provenance_manifest_path(stage_dir)
    if not path.exists():
        return None
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    return None



def inspect_stage_program(lineage_root: Path, stage_id: StageId, route: RouteId) -> ProgramInspection:
    lineage_root = lineage_root.resolve()
    program_dir = stage_program_dir(lineage_root, stage_id, route)
    manifest_path = program_dir / PROGRAM_MANIFEST_FILE
    required_program_dir = str(program_dir.relative_to(lineage_root))
    if not program_dir.exists():
        return ProgramInspection(
            program_dir=program_dir,
            manifest_path=manifest_path,
            required_program_dir=required_program_dir,
            required_program_entrypoint=None,
            program_contract_status="missing",
            error_code="STAGE_PROGRAM_MISSING",
            error_message=f"Missing lineage-local stage program directory: {required_program_dir}",
        )
    try:
        validated = validate_stage_program(lineage_root, stage_id, route)
    except StageProgramRuntimeError as exc:
        required_entrypoint = None
        if manifest_path.exists():
            payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            candidate = payload.get("entrypoint")
            if isinstance(candidate, str) and candidate.strip():
                required_entrypoint = candidate.strip()
        return ProgramInspection(
            program_dir=program_dir,
            manifest_path=manifest_path,
            required_program_dir=required_program_dir,
            required_program_entrypoint=required_entrypoint,
            program_contract_status="invalid",
            error_code=exc.reason_code,
            error_message=exc.message,
        )
    return ProgramInspection(
        program_dir=program_dir,
        manifest_path=manifest_path,
        required_program_dir=required_program_dir,
        required_program_entrypoint=validated.entrypoint,
        program_contract_status="valid",
        error_code=None,
        error_message=None,
    )



def validate_stage_program(lineage_root: Path, stage_id: StageId, route: RouteId) -> ValidatedStageProgram:
    lineage_root = lineage_root.resolve()
    program_dir = stage_program_dir(lineage_root, stage_id, route)
    manifest_path = program_dir / PROGRAM_MANIFEST_FILE
    if not manifest_path.exists():
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"Missing {PROGRAM_MANIFEST_FILE} in {program_dir.relative_to(lineage_root)}",
        )

    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise StageProgramRuntimeError("STAGE_PROGRAM_INVALID", "stage_program.yaml must be a mapping")

    manifest_stage_id = _require_string(payload, "stage_id")
    manifest_route = _require_string(payload, "route")
    lineage_id = _require_string(payload, "lineage_id")
    if manifest_stage_id != stage_id:
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"stage_program.yaml stage_id {manifest_stage_id!r} does not match resolved stage {stage_id!r}",
        )
    if manifest_route != route:
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"stage_program.yaml route {manifest_route!r} does not match resolved route {route!r}",
        )
    if lineage_id != lineage_root.name:
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"stage_program.yaml lineage_id {lineage_id!r} does not match lineage root {lineage_root.name!r}",
        )

    entrypoint = _require_relative_program_path(payload, "entrypoint", program_dir)
    entrypoint_path = program_dir / entrypoint
    if not entrypoint_path.exists() or not entrypoint_path.is_file():
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"stage_program.yaml entrypoint does not point to an existing file: {entrypoint}",
        )

    entry_type = _require_string(payload, "entry_type")
    if entry_type not in {"python", "rust", "bash"}:
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"Unsupported entry_type {entry_type!r}; expected one of python, rust, bash",
        )

    inputs = _validate_refs(
        payload.get("inputs", []),
        lineage_root=lineage_root,
        allowed_kinds={"artifact", "program"},
        field_name="inputs",
    )
    outputs = _validate_refs(
        payload.get("outputs", []),
        lineage_root=lineage_root,
        allowed_kinds={"machine", "human", "provenance"},
        field_name="outputs",
    )

    depends_on_programs = payload.get("depends_on_programs", [])
    if not isinstance(depends_on_programs, list) or not all(isinstance(item, str) for item in depends_on_programs):
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            "depends_on_programs must be a list of strings",
        )
    unknown_dep = next((item for item in depends_on_programs if item not in ALLOWED_DEPENDS_ON_PROGRAMS), None)
    if unknown_dep is not None:
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"Unknown depends_on_programs entry: {unknown_dep}",
        )

    shared_libs = payload.get("shared_libs", [])
    if not isinstance(shared_libs, list) or not all(isinstance(item, str) for item in shared_libs):
        raise StageProgramRuntimeError("STAGE_PROGRAM_INVALID", "shared_libs must be a list of strings")
    normalized_shared_libs: list[str] = []
    for item in shared_libs:
        lib_path = _normalize_lineage_relative_path(item, lineage_root)
        if not lib_path.startswith("program/common/"):
            raise StageProgramRuntimeError(
                "STAGE_PROGRAM_INVALID",
                f"shared_libs entry must stay under program/common/: {item}",
            )
        normalized_shared_libs.append(lib_path)

    authored_by_payload = payload.get("authored_by")
    if not isinstance(authored_by_payload, dict):
        raise StageProgramRuntimeError("STAGE_PROGRAM_INVALID", "authored_by must be a mapping")
    authored_by = AuthoredBy(
        agent_id=_require_string(authored_by_payload, "agent_id", field_prefix="authored_by"),
        agent_role=_require_string(authored_by_payload, "agent_role", field_prefix="authored_by"),
        session_id=_require_string(authored_by_payload, "session_id", field_prefix="authored_by"),
    )

    program_hash = _compute_program_hash(program_dir)
    validated = ValidatedStageProgram(
        stage_id=stage_id,
        route=route,
        lineage_id=lineage_id,
        program_dir=program_dir,
        manifest_path=manifest_path,
        entrypoint_path=entrypoint_path,
        entrypoint=entrypoint,
        entry_type=entry_type,  # type: ignore[arg-type]
        inputs=tuple(inputs),
        outputs=tuple(outputs),
        depends_on_programs=tuple(depends_on_programs),
        shared_libs=tuple(normalized_shared_libs),
        authored_by=authored_by,
        program_hash=program_hash,
    )
    identity_error = validate_stage_program_identity(validated)
    if identity_error is not None:
        raise StageProgramRuntimeError("STAGE_PROGRAM_INVALID", identity_error)
    return validated



def invoke_stage_if_admitted(lineage_root: Path, spec: StageProgramSpec) -> InvocationResult:
    lineage_root = lineage_root.resolve()
    validated = validate_stage_program(lineage_root, spec.stage_id, spec.route)
    stage_dir = lineage_root / spec.stage_dir_name
    author_formal_dir = _author_formal_dir(stage_dir)
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    _run_prebuild_schema_gate_if_declared(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        author_formal_dir=author_formal_dir,
        validated=validated,
    )
    command = _command_for_entrypoint(validated)
    env = {
        **os.environ,
        "QROS_LINEAGE_ROOT": str(lineage_root),
        "QROS_STAGE_ID": spec.stage_id,
        "QROS_STAGE_ROUTE": spec.route,
        "QROS_STAGE_ROOT": str(stage_dir),
        "QROS_STAGE_DIR": str(author_formal_dir),
        "QROS_AUTHOR_FORMAL_DIR": str(author_formal_dir),
        "QROS_PROGRAM_DIR": str(validated.program_dir),
    }
    result = subprocess.run(
        command,
        cwd=lineage_root,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise StageProgramRuntimeError(
            "PROGRAM_EXECUTION_FAILED",
            stderr or f"Stage program exited with status {result.returncode}",
        )

    missing_outputs = [name for name in spec.required_outputs if not (author_formal_dir / name).exists()]
    if missing_outputs:
        raise StageProgramRuntimeError(
            "OUTPUTS_INVALID",
            "Stage program did not materialize required outputs: " + ", ".join(missing_outputs),
        )

    provenance_path = _write_provenance_manifest(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        validated=validated,
        stage_status="awaiting_review_closure",
        status="success",
    )
    return InvocationResult(
        stage_dir=stage_dir,
        manifest_path=validated.manifest_path,
        output_refs=tuple(ref.path for ref in validated.outputs),
        input_refs=tuple(ref.path for ref in validated.inputs),
        provenance_path=provenance_path,
    )


def _run_prebuild_schema_gate_if_declared(
    *,
    lineage_root: Path,
    stage_dir: Path,
    author_formal_dir: Path,
    validated: ValidatedStageProgram,
) -> None:
    payload = yaml.safe_load(validated.manifest_path.read_text(encoding="utf-8")) or {}
    gate = payload.get("prebuild_schema_gate")
    if gate is None:
        return
    if not isinstance(gate, dict):
        raise StageProgramRuntimeError("STAGE_PROGRAM_PREBUILD_FAILED", "prebuild_schema_gate must be a mapping")

    entrypoint_args = gate.get("entrypoint_args", [])
    if not isinstance(entrypoint_args, list) or not all(isinstance(item, str) for item in entrypoint_args):
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_PREBUILD_FAILED",
            "prebuild_schema_gate.entrypoint_args must be a list of strings",
        )
    report_path_value = gate.get("report_path", "prebuild_schema_report.json")
    if not isinstance(report_path_value, str) or not report_path_value.strip():
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_PREBUILD_FAILED",
            "prebuild_schema_gate.report_path must be a non-empty string",
        )
    report_path = author_formal_dir / report_path_value.strip()

    # 预构建门禁只写 schema report，避免在字段合同错误时触发昂贵全量构建。
    command = _command_for_entrypoint(validated) + entrypoint_args
    env = {
        **os.environ,
        "QROS_LINEAGE_ROOT": str(lineage_root),
        "QROS_STAGE_ID": validated.stage_id,
        "QROS_STAGE_ROUTE": validated.route,
        "QROS_STAGE_ROOT": str(stage_dir),
        "QROS_STAGE_DIR": str(author_formal_dir),
        "QROS_AUTHOR_FORMAL_DIR": str(author_formal_dir),
        "QROS_PROGRAM_DIR": str(validated.program_dir),
        "QROS_PREBUILD_SCHEMA_GATE": "1",
        "QROS_PREBUILD_SCHEMA_REPORT": str(report_path),
    }
    result = subprocess.run(command, cwd=lineage_root, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_PREBUILD_FAILED",
            stderr or f"Stage program prebuild schema gate exited with status {result.returncode}",
        )
    if not report_path.exists():
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_PREBUILD_FAILED",
            f"prebuild schema report was not written: {report_path.relative_to(author_formal_dir)}",
        )
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_PREBUILD_FAILED",
            f"prebuild schema report is not valid JSON: {exc}",
        ) from exc
    _validate_prebuild_schema_report(gate, report)


def _validate_prebuild_schema_report(gate: dict[str, Any], report: Any) -> None:
    if not isinstance(report, dict):
        raise StageProgramRuntimeError("STAGE_PROGRAM_PREBUILD_FAILED", "prebuild schema report must be a mapping")
    expected_artifacts = gate.get("artifacts", {})
    observed_artifacts = report.get("artifacts", {})
    if not isinstance(expected_artifacts, dict) or not isinstance(observed_artifacts, dict):
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_PREBUILD_FAILED",
            "prebuild schema gate and report must contain artifacts mappings",
        )
    findings: list[str] = []
    for artifact_name, expected in expected_artifacts.items():
        if not isinstance(artifact_name, str) or not isinstance(expected, dict):
            findings.append(f"{artifact_name}: gate artifact expectation must be a mapping")
            continue
        observed = observed_artifacts.get(artifact_name)
        if not isinstance(observed, dict):
            findings.append(f"{artifact_name}: missing from prebuild schema report")
            continue
        _check_expected_list_subset(
            findings,
            artifact_name=artifact_name,
            expected=expected,
            observed=observed,
            expected_key="required_columns",
            observed_key="columns",
        )
        _check_expected_list_subset(
            findings,
            artifact_name=artifact_name,
            expected=expected,
            observed=observed,
            expected_key="primary_key",
            observed_key="primary_key",
        )
        _check_expected_list_subset(
            findings,
            artifact_name=artifact_name,
            expected=expected,
            observed=observed,
            expected_key="coverage_fields",
            observed_key="coverage_fields",
        )
        _check_expected_list_subset(
            findings,
            artifact_name=artifact_name,
            expected=expected,
            observed=observed,
            expected_key="required_fields",
            observed_key="fields",
        )
    if findings:
        raise StageProgramRuntimeError("STAGE_PROGRAM_PREBUILD_FAILED", "; ".join(findings))


def _check_expected_list_subset(
    findings: list[str],
    *,
    artifact_name: str,
    expected: dict[str, Any],
    observed: dict[str, Any],
    expected_key: str,
    observed_key: str,
) -> None:
    expected_values = expected.get(expected_key)
    if expected_values is None:
        return
    observed_values = observed.get(observed_key, [])
    if not isinstance(expected_values, list) or not all(isinstance(item, str) for item in expected_values):
        findings.append(f"{artifact_name}: {expected_key} must be a list of strings")
        return
    if not isinstance(observed_values, list) or not all(isinstance(item, str) for item in observed_values):
        findings.append(f"{artifact_name}: report {observed_key} must be a list of strings")
        return
    missing = sorted(set(expected_values) - set(observed_values))
    if missing:
        findings.append(f"{artifact_name}: missing {expected_key}: {', '.join(missing)}")



def stage_outputs_complete(stage_dir: Path, required_outputs: Sequence[str]) -> bool:
    author_formal_dir = _author_formal_dir(stage_dir)
    if not all((author_formal_dir / name).exists() for name in required_outputs):
        return False
    provenance = load_provenance_manifest(stage_dir)
    return provenance is not None



def _command_for_entrypoint(validated: ValidatedStageProgram) -> list[str]:
    lineage_root = validated.program_dir.parents[1] if validated.stage_id == "mandate" else validated.program_dir.parents[2]
    if validated.entry_type == "python":
        return [sys.executable, str(validated.entrypoint_path), "--lineage-root", str(lineage_root)]
    if validated.entry_type == "bash":
        return ["bash", str(validated.entrypoint_path), str(lineage_root)]
    return [str(validated.entrypoint_path), str(lineage_root)]



def _write_provenance_manifest(
    *,
    lineage_root: Path,
    stage_dir: Path,
    validated: ValidatedStageProgram,
    stage_status: str,
    status: str,
) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    payload = {
        "stage_id": validated.stage_id,
        "route": validated.route,
        "lineage_id": validated.lineage_id,
        "stage_status": stage_status,
        "program_dir": str(validated.program_dir.relative_to(lineage_root)),
        "stage_program_manifest_path": str(validated.manifest_path.relative_to(lineage_root)),
        "entrypoint": validated.entrypoint,
        "entry_type": validated.entry_type,
        "program_hash": validated.program_hash,
        "framework_revision": _git_revision(repo_root),
        "invoked_at": datetime.now(timezone.utc).isoformat(),
        "input_refs": [ref.__dict__ for ref in validated.inputs],
        "output_refs": [ref.__dict__ for ref in validated.outputs],
        "authored_by_agent_id": validated.authored_by.agent_id,
        "authored_by_agent_role": validated.authored_by.agent_role,
        "authoring_session_id": validated.authored_by.session_id,
        "status": status,
    }
    path = provenance_manifest_path(stage_dir)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path



def _compute_program_hash(program_dir: Path) -> str:
    digest = hashlib.sha256()
    files: list[Path] = []
    for path in sorted(program_dir.rglob("*"), key=lambda item: item.relative_to(program_dir).as_posix()):
        rel = path.relative_to(program_dir)
        if any(part in HASH_EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.is_symlink():
            raise StageProgramRuntimeError(
                "STAGE_PROGRAM_INVALID",
                f"Symlinks are not allowed in stage programs: {rel.as_posix()}",
            )
        if path.is_dir():
            continue
        if path.name in HASH_EXCLUDED_FILES or path.suffix == ".pyc":
            continue
        files.append(path)
    for path in files:
        rel = path.relative_to(program_dir).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()



def _validate_refs(
    raw_refs: Any,
    *,
    lineage_root: Path,
    allowed_kinds: set[str],
    field_name: str,
) -> list[ProgramRef]:
    if not isinstance(raw_refs, list):
        raise StageProgramRuntimeError("STAGE_PROGRAM_INVALID", f"{field_name} must be a list")
    refs: list[ProgramRef] = []
    for index, item in enumerate(raw_refs):
        if not isinstance(item, dict):
            raise StageProgramRuntimeError(
                "STAGE_PROGRAM_INVALID",
                f"{field_name}[{index}] must be a mapping",
            )
        kind = _require_string(item, "kind", field_prefix=f"{field_name}[{index}]")
        if kind not in allowed_kinds:
            raise StageProgramRuntimeError(
                "STAGE_PROGRAM_INVALID",
                f"{field_name}[{index}].kind must be one of {sorted(allowed_kinds)}",
            )
        raw_path = _require_string(item, "path", field_prefix=f"{field_name}[{index}]")
        normalized_path = _normalize_lineage_relative_path(raw_path, lineage_root)
        required = item.get("required")
        if not isinstance(required, bool):
            raise StageProgramRuntimeError(
                "STAGE_PROGRAM_INVALID",
                f"{field_name}[{index}].required must be a boolean",
            )
        refs.append(ProgramRef(kind=kind, path=normalized_path, required=required))
    return refs



def _normalize_lineage_relative_path(raw_path: str, lineage_root: Path) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"Path must stay within the lineage root and cannot be absolute: {raw_path}",
        )
    resolved = (lineage_root / path).resolve()
    try:
        relative = resolved.relative_to(lineage_root.resolve())
    except ValueError as exc:
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"Path escapes the lineage root: {raw_path}",
        ) from exc
    return relative.as_posix()



def _require_relative_program_path(payload: dict[str, Any], key: str, program_dir: Path) -> str:
    value = _require_string(payload, key)
    path = Path(value)
    if path.is_absolute():
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"{key} must be relative to the stage program directory",
        )
    resolved = (program_dir / path).resolve()
    try:
        resolved.relative_to(program_dir.resolve())
    except ValueError as exc:
        raise StageProgramRuntimeError(
            "STAGE_PROGRAM_INVALID",
            f"{key} escapes the stage program directory: {value}",
        ) from exc
    return path.as_posix()



def _require_string(payload: dict[str, Any], key: str, *, field_prefix: str | None = None) -> str:
    value = payload.get(key)
    label = f"{field_prefix}.{key}" if field_prefix else key
    if not isinstance(value, str) or not value.strip():
        raise StageProgramRuntimeError("STAGE_PROGRAM_INVALID", f"Missing required string field: {label}")
    return value.strip()



def _git_revision(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
    return result.stdout.strip() or "unknown"
