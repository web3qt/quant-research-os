# Post-Mandate Stage Program Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove post-mandate runtime auto-program generation from the real research flow, require Codex-authored lineage-local stage programs with Chinese comments, and block thin wrappers or fake artifacts before reviewer launch.

**Architecture:** Keep `run_research_session` focused on orchestration, stage detection, program contract validation, and execution. Move all “real stage program authoring” responsibility into post-mandate author skills, add a new program-identity gate that rejects framework thin wrappers, and strengthen review preflight so fake machine artifacts never reach the reviewer lane. Preserve fixture helpers for tests only, but make them explicit test-support APIs rather than a production-path fallback.

**Tech Stack:** Python 3, `pytest`, YAML/Markdown contract docs, existing QROS runtime helpers under `runtime/tools/`, existing skill tree under `skills/`

---

### Task 1: Lock The New Boundary With Failing Tests

**Files:**
- Create: `tests/session/test_post_mandate_stage_program_boundary.py`
- Create: `tests/runtime/test_stage_program_identity.py`
- Create: `tests/review/test_review_preflight_program_identity.py`
- Test: `tests/session/test_post_mandate_stage_program_boundary.py`
- Test: `tests/runtime/test_stage_program_identity.py`
- Test: `tests/review/test_review_preflight_program_identity.py`

- [ ] **Step 1: Write the failing session-boundary tests**

```python
from pathlib import Path

import yaml

from runtime.tools.research_session import run_research_session
from tests.helpers.lineage_program_support import write_fake_stage_provenance


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_csf_stage_without_program(lineage_root: Path) -> None:
    mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    mandate_closure_dir = lineage_root / "01_mandate" / "review" / "closure"
    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    mandate_closure_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (mandate_formal_dir / name).write_text("ok\n", encoding="utf-8")
    _write_yaml(
        mandate_formal_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "short_only_rank",
            "neutralization_policy": "none",
        },
    )
    _write_yaml(mandate_closure_dir / "stage_completion_certificate.yaml", {"stage_status": "PASS", "final_verdict": "PASS"})
    _write_yaml(
        lineage_root / "01_mandate" / "author" / "draft" / "next_stage_transition_approval.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "decision": "CONFIRM_NEXT_STAGE",
            "approved_by": "tester",
            "approved_at": "2026-04-22T09:00:00Z",
            "source_stage": "mandate_next_stage_confirmation_pending",
        },
    )
    _write_yaml(
        lineage_root / "02_csf_data_ready" / "author" / "draft" / "csf_data_ready_freeze_draft.yaml",
        {
            "groups": {
                "panel_contract": {"confirmed": True, "draft": {"panel_primary_key": ["date", "asset"], "cross_section_time_key": "date", "asset_key": "asset", "universe_membership_rule": "use frozen universe"}, "missing_items": []},
                "taxonomy_contract": {"confirmed": True, "draft": {"group_taxonomy_reference": "", "group_mapping_rule": "not_applicable", "taxonomy_note": "not_applicable"}, "missing_items": []},
                "eligibility_contract": {"confirmed": True, "draft": {"eligibility_base_rule": "min liquidity", "coverage_floor_rule": "0.95", "mask_audit_note": "keep separate"}, "missing_items": []},
                "shared_feature_base": {"confirmed": True, "draft": {"shared_feature_outputs": ["returns_panel"], "shared_feature_note": "shared only"}, "missing_items": []},
                "delivery_contract": {"confirmed": True, "draft": {"machine_artifacts": ["panel_manifest.json"], "consumer_stage": "csf_signal_ready", "frozen_inputs_note": "downstream reads frozen outputs"}, "missing_items": []},
            }
        },
    )
    _write_yaml(
        lineage_root / "02_csf_data_ready" / "author" / "draft" / "data_ready_transition_approval.yaml",
        {
            "lineage_id": lineage_root.name,
            "decision": "CONFIRM_DATA_READY",
            "approved_by": "tester",
            "approved_at": "2026-04-22T09:01:00Z",
            "source_stage": "mandate_review_complete",
        },
    )
    write_fake_stage_provenance(lineage_root, "mandate")


def test_run_research_session_stops_at_stage_program_missing_for_csf_data_ready(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_k"
    _prepare_csf_stage_without_program(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_alt_k")

    assert status.current_stage == "csf_data_ready_author"
    assert status.blocking_reason_code == "STAGE_PROGRAM_MISSING"
    assert status.required_program_dir == "program/cross_sectional_factor/data_ready"
    assert "Codex author skill" in status.next_action
    assert not (lineage_root / "program" / "cross_sectional_factor" / "data_ready").exists()
```

- [ ] **Step 2: Write the failing thin-wrapper identity tests**

```python
from pathlib import Path

import yaml

from runtime.tools.lineage_program_runtime import StageProgramRuntimeError, validate_stage_program


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_validate_stage_program_rejects_post_mandate_thin_wrapper(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)
    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate\n"
        "def main():\n"
        "    build_csf_data_ready_from_mandate(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-1"},
        },
    )

    try:
        validate_stage_program(lineage_root, "data_ready", "cross_sectional_factor")
    except StageProgramRuntimeError as exc:
        assert exc.code == "STAGE_PROGRAM_INVALID"
        assert "thin wrapper" in str(exc)
    else:
        raise AssertionError("thin wrapper should be rejected")
```

- [ ] **Step 3: Write the failing preflight realism tests**

```python
from pathlib import Path

import yaml

from runtime.tools.review_skillgen.review_preflight import run_review_preflight


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_review_preflight_fails_when_machine_artifact_is_placeholder_text(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc_alt_k" / "05_csf_test_evidence"
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "rank_ic_summary.json",
        "bucket_returns.parquet",
        "monotonicity_report.json",
        "breadth_coverage_report.parquet",
        "subperiod_stability_report.json",
        "filter_condition_panel.parquet",
        "target_strategy_condition_compare.parquet",
        "gated_vs_ungated_summary.json",
        "csf_test_gate_table.csv",
        "csf_selected_variants_test.csv",
        "csf_test_contract.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "program_execution_manifest.json",
    ]:
        (author_formal_dir / name).write_text("{}\n", encoding="utf-8")
    (author_formal_dir / "rank_ic_timeseries.parquet").write_text("placeholder parquet payload\n", encoding="utf-8")

    payload = run_review_preflight(
        explicit_context={
            "stage": "csf_test_evidence",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(author_formal_dir),
            "lineage_id": "btc_alt_k",
        }
    )

    assert payload["status"] == "FAIL"
    assert any("placeholder" in finding for finding in payload["content_findings"])
```

- [ ] **Step 4: Run the new tests to verify they fail**

Run: `python -m pytest tests/session/test_post_mandate_stage_program_boundary.py tests/runtime/test_stage_program_identity.py tests/review/test_review_preflight_program_identity.py -q`

Expected: FAIL because `run_research_session` still auto-generates `csf_data_ready`, `validate_stage_program` still accepts the scaffold wrapper, and `run_review_preflight` has no placeholder-artifact realism check.

- [ ] **Step 5: Commit**

```bash
git add tests/session/test_post_mandate_stage_program_boundary.py tests/runtime/test_stage_program_identity.py tests/review/test_review_preflight_program_identity.py
git commit -m "test: lock post-mandate stage program boundary"
```

### Task 2: Remove Post-Mandate Auto-Generation From The Production Path

**Files:**
- Modify: `runtime/tools/research_session.py`
- Create: `tests/helpers/fixture_stage_program_support.py`
- Modify: `tests/helpers/lineage_program_support.py`
- Modify: `tests/runtime/test_csf_data_ready_auto_program.py`
- Test: `tests/session/test_post_mandate_stage_program_boundary.py`
- Test: `tests/runtime/test_csf_data_ready_auto_program.py`

- [ ] **Step 1: Remove the production-path import of `materialize_stage_program`**

```python
# runtime/tools/research_session.py
from runtime.tools.stage_program_scaffold import materialize_stage_program
```

Replace it by deleting the import entirely. The production session path should not call a scaffold helper after this task.

- [ ] **Step 2: Replace post-mandate build helpers with one no-autogen helper**

```python
def _invoke_author_stage_without_autogen(
    lineage_root: Path,
    *,
    required_session_stage: str,
    runtime_stage_name: str,
) -> list[str]:
    if detect_session_stage(lineage_root) != required_session_stage:
        return []
    try:
        return _invoke_program_stage(lineage_root, runtime_stage_name)
    except StageProgramRuntimeError:
        return []


def build_csf_data_ready_if_admitted(lineage_root: Path) -> list[str]:
    if next_csf_data_ready_freeze_group(lineage_root) is not None:
        return []
    return _invoke_author_stage_without_autogen(
        lineage_root,
        required_session_stage="csf_data_ready_author",
        runtime_stage_name="csf_data_ready_author",
    )
```

Then rewrite every `mandate`-after author build function on both routes to use that helper:

- `build_data_ready_if_admitted`
- `build_signal_ready_if_admitted`
- `build_train_freeze_if_admitted`
- `build_test_evidence_if_admitted`
- `build_backtest_ready_if_admitted`
- `build_holdout_validation_if_admitted`
- `build_csf_data_ready_if_admitted`
- `build_csf_signal_ready_if_admitted`
- `build_csf_train_freeze_if_admitted`
- `build_csf_test_evidence_if_admitted`
- `build_csf_backtest_ready_if_admitted`
- `build_csf_holdout_validation_if_admitted`

Each rewritten function should be a thin delegator to `_invoke_author_stage_without_autogen(...)`, plus any existing freeze-group guard that is still needed.

- [ ] **Step 3: Change the runtime status messaging so missing programs clearly point to Codex authoring**

```python
# runtime/tools/research_session.py
next_action = f"Use the current post-mandate author skill to author the lineage-local stage program under {inspection.required_program_dir}."
resume_hint = (
    "Codex must explicitly write the stage program, including Chinese comments on the key generation logic, "
    "before the author build can continue."
)
```

Apply this wording only for `mandate`-after stages. Keep `mandate` behavior unchanged.

- [ ] **Step 4: Move scaffold generation into an explicit test-support helper**

```python
# tests/helpers/fixture_stage_program_support.py
from pathlib import Path

from runtime.tools.stage_program_scaffold import materialize_stage_program


def materialize_fixture_stage_program(
    lineage_root: Path,
    stage_key: str,
    *,
    agent_id: str = "fixture-agent",
    agent_role: str = "fixture-builder",
    session_id: str = "fixture-stage-program",
) -> Path:
    return materialize_stage_program(
        lineage_root,
        stage_key,
        authored_by_agent_id=agent_id,
        authored_by_agent_role=agent_role,
        authoring_session_id=session_id,
    )
```

Update `tests/helpers/lineage_program_support.py` and `tests/runtime/test_csf_data_ready_auto_program.py` so fixture tests call `materialize_fixture_stage_program(...)` explicitly instead of depending on the production session path.

- [ ] **Step 5: Rewrite the old auto-program test to assert “fixture helper works” instead of “real flow auto-generates”**

```python
def test_fixture_helper_materializes_valid_csf_data_ready_program(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"

    program_dir = materialize_fixture_stage_program(lineage_root, "csf_data_ready")

    assert program_dir == lineage_root / "program/cross_sectional_factor/data_ready"
    inspection = inspect_stage_program(lineage_root, "data_ready", "cross_sectional_factor")
    assert inspection.program_contract_status == "valid"
```

Delete or replace the old expectation that `run_research_session(...)` silently creates `program/cross_sectional_factor/data_ready/`.

- [ ] **Step 6: Run boundary and fixture tests to verify they pass**

Run: `python -m pytest tests/session/test_post_mandate_stage_program_boundary.py tests/runtime/test_csf_data_ready_auto_program.py -q`

Expected: PASS. The real session path must stop at `STAGE_PROGRAM_MISSING`, while the explicit fixture helper still creates a valid test program.

- [ ] **Step 7: Commit**

```bash
git add runtime/tools/research_session.py runtime/tools/stage_program_scaffold.py tests/helpers/fixture_stage_program_support.py tests/helpers/lineage_program_support.py tests/runtime/test_csf_data_ready_auto_program.py tests/session/test_post_mandate_stage_program_boundary.py
git commit -m "refactor: remove post-mandate auto program generation from runtime"
```

### Task 3: Add Stage Program Identity Validation For Real Research Flow

**Files:**
- Create: `runtime/tools/stage_program_identity.py`
- Modify: `runtime/tools/lineage_program_runtime.py`
- Modify: `tests/runtime/test_stage_program_identity.py`
- Test: `tests/runtime/test_stage_program_identity.py`

- [ ] **Step 1: Add a dedicated identity validator module**

```python
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Protocol


CHINESE_COMMENT_RE = re.compile(r"#.*[\u4e00-\u9fff]")
FRAMEWORK_IMPORT_PREFIX = "runtime.tools."


class StageProgramIdentity(Protocol):
    stage_id: str
    program_dir: Path
    entrypoint_path: Path


def validate_stage_program_identity(validated: StageProgramIdentity) -> str | None:
    if validated.stage_id == "mandate":
        return None

    program_dir = validated.program_dir
    entrypoint_path = validated.entrypoint_path
    source = entrypoint_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(entrypoint_path))

    if _looks_like_framework_thin_wrapper(tree):
        return f"{program_dir}: post-mandate stage program cannot be a thin wrapper around framework builders"

    if not CHINESE_COMMENT_RE.search(source):
        return f"{program_dir}: run_stage.py must contain Chinese comments for key generation logic"

    for helper_path in sorted(program_dir.glob("*.py")):
        if helper_path.name == entrypoint_path.name:
            continue
        helper_source = helper_path.read_text(encoding="utf-8")
        if "def " not in helper_source:
            continue
        if not CHINESE_COMMENT_RE.search(helper_source):
            return f"{program_dir}: helper {helper_path.name} must contain Chinese comments for key logic"

    return None


def _looks_like_framework_thin_wrapper(tree: ast.AST) -> bool:
    framework_import = False
    helper_functions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(FRAMEWORK_IMPORT_PREFIX):
            framework_import = True
        if isinstance(node, ast.FunctionDef):
            helper_functions.add(node.name)
    return framework_import and helper_functions <= {"main"}
```

- [ ] **Step 2: Call the identity validator from `validate_stage_program(...)`**

```python
# runtime/tools/lineage_program_runtime.py
from runtime.tools.stage_program_identity import validate_stage_program_identity


def validate_stage_program(lineage_root: Path, stage_id: str, route: str) -> ValidatedStageProgram:
    lineage_root = lineage_root.resolve()
    program_dir = stage_program_dir(lineage_root, stage_id, route)
    manifest_path = program_dir / PROGRAM_MANIFEST_FILE
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest_stage_id = _require_string(payload, "stage_id")
    manifest_route = _require_string(payload, "route")
    lineage_id = _require_string(payload, "lineage_id")
    entrypoint = _require_relative_program_path(payload, "entrypoint", program_dir)
    entrypoint_path = program_dir / entrypoint
    entry_type = _require_string(payload, "entry_type")
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
    shared_libs = payload.get("shared_libs", [])
    authored_by_payload = payload.get("authored_by")
    authored_by = AuthoredBy(
        agent_id=_require_string(authored_by_payload, "agent_id", field_prefix="authored_by"),
        agent_role=_require_string(authored_by_payload, "agent_role", field_prefix="authored_by"),
        session_id=_require_string(authored_by_payload, "session_id", field_prefix="authored_by"),
    )
    program_hash = _compute_program_hash(program_dir)
    validated = ValidatedStageProgram(
        stage_id=manifest_stage_id,
        route=manifest_route,
        lineage_id=lineage_id,
        program_dir=program_dir,
        manifest_path=manifest_path,
        entrypoint_path=entrypoint_path,
        entrypoint=entrypoint,
        entry_type=entry_type,
        inputs=tuple(inputs),
        outputs=tuple(outputs),
        depends_on_programs=tuple(depends_on_programs),
        shared_libs=tuple(shared_libs),
        authored_by=authored_by,
        program_hash=program_hash,
    )
    identity_error = validate_stage_program_identity(validated)
    if identity_error is not None:
        raise StageProgramRuntimeError("STAGE_PROGRAM_INVALID", identity_error)
    return validated
```

This keeps one canonical validation entrypoint. Do not duplicate identity logic in `research_session.py`.

- [ ] **Step 3: Extend the failing tests so they also cover the Chinese-comment requirement**

```python
def test_validate_stage_program_rejects_missing_chinese_comments_for_helper(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "time_series" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)
    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "helpers.py").write_text(
        "def build_dataset():\n"
        "    return {'status': 'ok'}\n",
        encoding="utf-8",
    )
    (program_dir / "run_stage.py").write_text(
        "# 读取冻结合同并生成正式数据产物\n"
        "from helpers import build_dataset\n"
        "def main():\n"
        "    build_dataset()\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "data_ready",
            "route": "time_series_signal",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-2"},
        },
    )

    try:
        validate_stage_program(lineage_root, "data_ready", "time_series_signal")
    except StageProgramRuntimeError as exc:
        assert exc.code == "STAGE_PROGRAM_INVALID"
        assert "Chinese comments" in str(exc)
    else:
        raise AssertionError("missing Chinese comments should be rejected")
```

- [ ] **Step 4: Run the identity tests to verify they pass**

Run: `python -m pytest tests/runtime/test_stage_program_identity.py -q`

Expected: PASS. Thin wrappers and uncommented helper logic must be rejected as `STAGE_PROGRAM_INVALID`.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/stage_program_identity.py runtime/tools/lineage_program_runtime.py tests/runtime/test_stage_program_identity.py
git commit -m "feat: validate post-mandate stage program identity"
```

### Task 4: Tighten Preflight To Reject Thin Wrappers And Fake Machine Artifacts Before Review

**Files:**
- Create: `runtime/tools/review_skillgen/artifact_realism.py`
- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Modify: `tests/review/test_review_preflight_program_identity.py`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Test: `tests/review/test_review_preflight_program_identity.py`

- [ ] **Step 1: Add a realism checker for machine-readable outputs**

```python
from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq


PLACEHOLDER_MARKERS = (
    "placeholder",
    "占位",
    "contract-only",
)


def check_machine_artifact_realism(author_formal_dir: Path, required_outputs: list[str]) -> list[str]:
    findings: list[str] = []
    for relative_path in required_outputs:
        path = author_formal_dir / relative_path
        if not path.exists() or path.is_dir():
            continue
        if path.suffix == ".parquet":
            findings.extend(_check_parquet(path))
        elif path.suffix == ".json":
            findings.extend(_check_json(path))
        elif path.suffix == ".csv":
            findings.extend(_check_csv(path))
    return findings


def _check_parquet(path: Path) -> list[str]:
    raw = path.read_bytes()[:256]
    lowered = raw.decode("utf-8", errors="ignore").lower()
    if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
        return [f"{path.name} is placeholder text, not a real parquet artifact"]
    try:
        table = pq.read_table(path)
    except Exception as exc:  # pragma: no cover - exercised through caller
        return [f"{path.name} is not a readable parquet artifact: {exc}"]
    if table.num_rows == 0:
        return [f"{path.name} is empty and cannot enter reviewer lane"]
    return []


def _check_json(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if any(marker in text.lower() for marker in PLACEHOLDER_MARKERS):
        return [f"{path.name} contains placeholder text"]
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        return [f"{path.name} is not valid JSON: {exc}"]
    return []


def _check_csv(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if any(marker in text.lower() for marker in PLACEHOLDER_MARKERS):
        return [f"{path.name} contains placeholder text"]
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return [f"{path.name} must contain a header and at least one data row"]
    return []
```

- [ ] **Step 2: Wire both identity and realism checks into review preflight**

```python
# runtime/tools/review_skillgen/review_preflight.py
from runtime.tools.lineage_program_runtime import validate_stage_program
from runtime.tools.review_skillgen.artifact_realism import check_machine_artifact_realism


def run_review_preflight(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if explicit_context is not None:
        inferred = build_stage_context(Path(explicit_context["stage_dir"]))
        context = {**inferred, **explicit_context}
    else:
        context = infer_review_context(cwd or Path.cwd())

    stage_dir = Path(context["stage_dir"]).resolve()
    lineage_root = Path(context["lineage_root"]).resolve()
    author_formal_dir = Path(context["author_formal_dir"]).resolve()
    stage = context["stage"]
    gates = load_gate_schema(GATES_PATH)
    checklist = load_checklist_schema(CHECKLIST_PATH)
    stage_contract = gates["stages"][stage]
    stage_checks = checklist["stages"][stage]
    stage_content_checks, upstream_binding_checks = _split_structural_checks(
        stage_contract.get("structural_gate_checks", [])
    )
    stage_content_review_checks, upstream_binding_review_checks = _split_review_checks(
        stage_checks.get("checks", [])
    )
    content_findings: list[str] = []

    if stage != "idea_intake":
        route = context.get("current_route") or context.get("route_family")
        validate_stage_program(lineage_root, stage_contract["stage_id"], route)
    content_findings.extend(
        f"Missing required output: {item}"
        for item in check_required_outputs(author_formal_dir, stage_contract.get("required_outputs", []))
    )
    content_findings.extend(check_global_evidence(author_formal_dir, stage_checks))
    content_blocking, _ = check_stage_evidence(author_formal_dir, stage_content_review_checks)
    content_findings.extend(content_blocking)
    content_findings.extend(check_structural_gates(author_formal_dir, stage_content_checks))
    content_findings.extend(check_metric_gates(author_formal_dir, stage_contract.get("metric_gate_checks", [])))
    content_findings.extend(
        check_machine_artifact_realism(
            author_formal_dir,
            list(stage_contract.get("required_outputs", [])),
        )
    )
    upstream_findings = validate_upstream_bindings(
        stage=stage,
        lineage_root=lineage_root,
        author_formal_dir=author_formal_dir,
        structural_binding_checks=upstream_binding_checks,
    )
    upstream_evidence_findings, _ = check_stage_evidence(author_formal_dir, upstream_binding_review_checks)
    upstream_findings.extend(upstream_evidence_findings)
    return {
        "stage": stage,
        "lineage_id": context["lineage_id"],
        "content_findings": content_findings,
        "upstream_binding_findings": upstream_findings,
        "status": "PASS" if not content_findings and not upstream_findings else "FAIL",
    }
```

Use the stage’s existing required-output list. Do not create a second divergent list inside preflight.

- [ ] **Step 3: Update the preflight test to assert the new failure wording**

```python
def test_review_preflight_fails_when_machine_artifact_is_placeholder_text(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc_alt_k" / "05_csf_test_evidence"
    author_formal_dir = stage_dir / "author" / "formal"
    author_formal_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "rank_ic_summary.json",
        "bucket_returns.parquet",
        "monotonicity_report.json",
        "breadth_coverage_report.parquet",
        "subperiod_stability_report.json",
        "filter_condition_panel.parquet",
        "target_strategy_condition_compare.parquet",
        "gated_vs_ungated_summary.json",
        "csf_test_gate_table.csv",
        "csf_selected_variants_test.csv",
        "csf_test_contract.md",
        "artifact_catalog.md",
        "field_dictionary.md",
        "program_execution_manifest.json",
    ]:
        (author_formal_dir / name).write_text("{}\n", encoding="utf-8")
    (author_formal_dir / "rank_ic_timeseries.parquet").write_text("placeholder parquet payload\n", encoding="utf-8")

    payload = run_review_preflight(
        explicit_context={
            "stage": "csf_test_evidence",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(author_formal_dir),
            "lineage_id": "btc_alt_k",
        }
    )
    assert payload["status"] == "FAIL"
    assert any("not a real parquet artifact" in finding for finding in payload["content_findings"])
```

Add one more test where `validate_stage_program(...)` rejects a thin wrapper and `run_review_preflight(...)` returns `FAIL` without opening reviewer lane.

- [ ] **Step 4: Update the shared review protocol doc so the preflight responsibility is explicit**

```md
- preflight 必须在 reviewer lane 之前拒绝 thin wrapper stage program
- preflight 必须在 reviewer lane 之前拒绝 placeholder / fake machine-readable artifacts
- reviewer 不承担第一轮“作者到底有没有真的写程序/真的生成产物”的筛查职责
```

- [ ] **Step 5: Run the focused preflight tests**

Run: `python -m pytest tests/review/test_review_preflight_program_identity.py -q`

Expected: PASS. Placeholder parquet text and thin-wrapper programs must both fail preflight.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_skillgen/artifact_realism.py runtime/tools/review_skillgen/review_preflight.py tests/review/test_review_preflight_program_identity.py docs/guides/qros-review-shared-protocol.md
git commit -m "feat: reject thin wrappers and fake artifacts in review preflight"
```

### Task 5: Rewrite Post-Mandate Author Skill And Documentation Contracts

**Files:**
- Create: `tests/skills/test_post_mandate_program_authoring_contracts.py`
- Create: `tests/docs/test_post_mandate_program_boundary_docs.py`
- Modify: `skills/data_ready/qros-data-ready-author/SKILL.md`
- Modify: `skills/signal_ready/qros-signal-ready-author/SKILL.md`
- Modify: `skills/train_freeze/qros-train-freeze-author/SKILL.md`
- Modify: `skills/test_evidence/qros-test-evidence-author/SKILL.md`
- Modify: `skills/backtest_ready/qros-backtest-ready-author/SKILL.md`
- Modify: `skills/holdout_validation/qros-holdout-validation-author/SKILL.md`
- Modify: `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
- Modify: `skills/csf_signal_ready/qros-csf-signal-ready-author/SKILL.md`
- Modify: `skills/csf_train_freeze/qros-csf-train-freeze-author/SKILL.md`
- Modify: `skills/csf_test_evidence/qros-csf-test-evidence-author/SKILL.md`
- Modify: `skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md`
- Modify: `skills/csf_holdout_validation/qros-csf-holdout-validation-author/SKILL.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/sop/main-flow/research_workflow_sop.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `docs/guides/qros-verification-tiers.md`
- Modify: `docs/guides/qros-authoring-language-discipline.md`
- Test: `tests/skills/test_post_mandate_program_authoring_contracts.py`
- Test: `tests/docs/test_post_mandate_program_boundary_docs.py`

- [ ] **Step 1: Write failing skill-contract tests**

```python
from tests.helpers.skill_test_utils import skill_text


POST_MANDATE_AUTHOR_SKILLS = (
    "qros-data-ready-author",
    "qros-signal-ready-author",
    "qros-train-freeze-author",
    "qros-test-evidence-author",
    "qros-backtest-ready-author",
    "qros-holdout-validation-author",
    "qros-csf-data-ready-author",
    "qros-csf-signal-ready-author",
    "qros-csf-train-freeze-author",
    "qros-csf-test-evidence-author",
    "qros-csf-backtest-ready-author",
    "qros-csf-holdout-validation-author",
)


REQUIRED_SUBSTRINGS = (
    "显式生成或刷新本 stage 的 lineage-local stage program",
    "真实产生产物的程序",
    "thin wrapper",
    "关键步骤",
    "中文注释",
)


def test_post_mandate_author_skills_require_explicit_stage_program_authoring() -> None:
    for skill_name in POST_MANDATE_AUTHOR_SKILLS:
        text = skill_text(skill_name)
        for needle in REQUIRED_SUBSTRINGS:
            assert needle in text, f"{needle} missing in {skill_name}"
```

- [ ] **Step 2: Add failing documentation boundary tests**

```python
from pathlib import Path


def test_qros_research_session_usage_explains_codex_authored_stage_program_boundary() -> None:
    content = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    assert "Codex" in content
    assert "显式生成" in content
    assert "lineage-local stage program" in content
    assert "program_hash" in content
    assert "整个 `program_dir`" in content


def test_qros_verification_tiers_marks_stage_program_boundary_change_as_full_smoke() -> None:
    content = Path("docs/guides/qros-verification-tiers.md").read_text(encoding="utf-8")
    assert "stage-program authoring contract" in content
    assert "full-smoke" in content
```

- [ ] **Step 3: Update every post-mandate author skill with the new hard contract**

```md
- 必须先显式生成或刷新本 stage 的 lineage-local stage program，再执行 author build
- 该 program 必须真实解释本阶段 formal artifacts 如何生成，不能只是 framework builder 的 thin wrapper
- `run_stage.py` 与关键 helper 必须为关键步骤补清晰、简短、面向维护者的中文注释
- 若当前只有 skeleton、thin wrapper、placeholder 或 fake artifact，必须判为未完成
```

Apply the wording consistently across both mainline and CSF author skills. Reuse `docs/guides/qros-authoring-language-discipline.md` instead of inlining divergent comment rules.

- [ ] **Step 4: Update the user-facing docs to match the new product boundary**

```md
真实研究流里，`mandate` 之后的 stage program 由 Codex 在当前 author lane 显式编写或刷新。
QROS runtime 负责校验和调用，不再后台静默生成默认 wrapper。
`program_hash` 记录的是整个 `program_dir` 的 hash，而不是单个 `run_stage.py` 文件。
thin wrapper、placeholder 文件、contract-only fake artifact 不能进入真实研究流 reviewer lane。
fixture/demo-only helper 必须与真实研究流主路径隔离。
```

Make those ideas explicit in:

- `docs/guides/qros-research-session-usage.md`
- `docs/sop/main-flow/research_workflow_sop.md`
- `docs/guides/qros-review-shared-protocol.md`
- `docs/guides/qros-verification-tiers.md`

- [ ] **Step 5: Run the focused skill/doc tests**

Run: `python -m pytest tests/skills/test_post_mandate_program_authoring_contracts.py tests/docs/test_post_mandate_program_boundary_docs.py -q`

Expected: PASS. Skills and docs must all reflect the same post-mandate boundary.

- [ ] **Step 6: Commit**

```bash
git add tests/skills/test_post_mandate_program_authoring_contracts.py tests/docs/test_post_mandate_program_boundary_docs.py skills/data_ready/qros-data-ready-author/SKILL.md skills/signal_ready/qros-signal-ready-author/SKILL.md skills/train_freeze/qros-train-freeze-author/SKILL.md skills/test_evidence/qros-test-evidence-author/SKILL.md skills/backtest_ready/qros-backtest-ready-author/SKILL.md skills/holdout_validation/qros-holdout-validation-author/SKILL.md skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md skills/csf_signal_ready/qros-csf-signal-ready-author/SKILL.md skills/csf_train_freeze/qros-csf-train-freeze-author/SKILL.md skills/csf_test_evidence/qros-csf-test-evidence-author/SKILL.md skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md skills/csf_holdout_validation/qros-csf-holdout-validation-author/SKILL.md docs/guides/qros-research-session-usage.md docs/sop/main-flow/research_workflow_sop.md docs/guides/qros-review-shared-protocol.md docs/guides/qros-verification-tiers.md docs/guides/qros-authoring-language-discipline.md
git commit -m "docs: codify codex-authored post-mandate stage programs"
```

### Task 6: Run Full Verification For The Boundary Change

**Files:**
- Verify: `runtime/tools/research_session.py`
- Verify: `runtime/tools/stage_program_identity.py`
- Verify: `runtime/tools/review_skillgen/review_preflight.py`
- Verify: `docs/guides/qros-research-session-usage.md`
- Verify: `docs/sop/main-flow/research_workflow_sop.md`
- Verify: `skills/*/*-author/SKILL.md`

- [ ] **Step 1: Run the full focused test set**

Run: `python -m pytest tests/session/test_post_mandate_stage_program_boundary.py tests/runtime/test_csf_data_ready_auto_program.py tests/runtime/test_stage_program_identity.py tests/review/test_review_preflight_program_identity.py tests/skills/test_post_mandate_program_authoring_contracts.py tests/docs/test_post_mandate_program_boundary_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Run smoke verification**

Run: `python runtime/scripts/run_verification_tier.py --tier smoke`

Expected: PASS. No regressions in the default verification tier.

- [ ] **Step 3: Run full-smoke verification**

Run: `python runtime/scripts/run_verification_tier.py --tier full-smoke`

Expected: PASS. This change alters post-mandate stage flow, authoring seam, and review gate semantics, so full-smoke is mandatory.

- [ ] **Step 4: Review the diff against the spec before closing**

Run: `git diff -- runtime/tools/research_session.py runtime/tools/lineage_program_runtime.py runtime/tools/stage_program_identity.py runtime/tools/review_skillgen/review_preflight.py skills docs tests`

Expected: the diff shows the same four product decisions frozen in the spec:

- no post-mandate production auto-generation
- Codex-authored lineage-local stage programs
- Chinese comments as a hard authoring contract
- fixture/demo-only helper isolation

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_session.py runtime/tools/lineage_program_runtime.py runtime/tools/stage_program_identity.py runtime/tools/review_skillgen/review_preflight.py skills docs tests
git commit -m "feat: enforce codex-authored post-mandate stage program boundary"
```
