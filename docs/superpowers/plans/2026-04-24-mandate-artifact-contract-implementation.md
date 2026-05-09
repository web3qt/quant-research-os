# Mandate Artifact Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote mandate formal artifact shape into a machine-readable contract and enforce it through runtime validation, CLI validation, focused tests, and thinner skill/docs guidance.

**Architecture:** Add `contracts/artifacts/mandate_artifacts.yaml` as the source of truth for `01_mandate/author/formal/*`. Extend the existing artifact contract validator instead of adding a second validation system, then call that validator after mandate artifact generation and through `qros-validate-stage --stage mandate`.

**Tech Stack:** Python stdlib `json` and `tomllib`, PyYAML, pytest, existing QROS runtime helpers under `runtime/tools/`.

**Execution constraint:** Do not run `git commit`, `git push`, or create a PR unless the user explicitly confirms after reviewing the diff and verification results.

---

## File Structure

- Create: `contracts/artifacts/mandate_artifacts.yaml`
  - Contract for `01_mandate/author/formal` artifact file names, markdown sections, YAML fields, JSON fields, and TOML fields.
- Create: `tests/contracts/test_mandate_artifact_contract.py`
  - Contract-level regression tests that lock the mandate artifact list, critical field paths, enum sets, and duplicate field protection.
- Modify: `runtime/tools/artifact_contract_runtime.py`
  - Register `mandate`, add JSON and TOML artifact validation, add `list[map]` type support, and keep YAML behavior unchanged.
- Modify: `runtime/tools/idea_runtime.py`
  - Add `non_rust_exceptions = []` to `run_config.toml`, include `field_dictionary.md` in `artifact_catalog.md`, and validate generated mandate formal artifacts against the mandate contract before returning.
- Modify: `tests/runtime/test_artifact_contract_runtime.py`
  - Unit tests for JSON, TOML, `list[map]`, and generated mandate artifact validation.
- Modify: `tests/runtime/test_validate_stage_artifacts_script.py`
  - CLI tests for `--stage mandate`.
- Create: `tests/session/test_mandate_artifact_shape.py`
  - Shape snapshot tests for generated mandate formal outputs.
- Modify: `tests/session/test_idea_runtime_scripts.py`
  - Lock `run_config.toml` `non_rust_exceptions` output and post-build validator behavior.
- Modify: `tests/bootstrap/test_project_bootstrap.py`
  - Add the new contract path to bootstrap asset coverage.
- Modify: `skills/mandate/qros-mandate-author/SKILL.md`
  - Thin the skill so field truth points to the artifact contract, not free text.
- Modify: `docs/guides/idea-intake-to-mandate-flow.md`
  - Document mandate validation command and the contract-first rule.
- Modify: `tests/session/test_idea_intake_assets.py`
  - Lock the skill/doc references to the mandate artifact contract and validator command.

---

### Task 1: Lock The Mandate Artifact Contract Shape First

**Files:**
- Create: `tests/contracts/test_mandate_artifact_contract.py`
- Create: `contracts/artifacts/mandate_artifacts.yaml`

- [ ] **Step 1: Write failing contract tests**

Create `tests/contracts/test_mandate_artifact_contract.py`:

```python
from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/mandate_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _artifact(contract: dict, artifact_name: str) -> dict:
    return contract["artifacts"][artifact_name]


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_mandate_artifact_contract_exists_and_declares_stage_shape() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["stage"] == "mandate"
    assert contract["stage_dir"] == "01_mandate/author/formal"
    assert contract["schema_id"] == "mandate-artifacts-v1"
    assert contract["schema_version"] == "v1"
    assert contract["unknown_machine_top_level_fields"] == "forbid"

    assert set(contract["artifacts"]) == {
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    }


def test_mandate_contract_locks_research_route_shape_and_enums() -> None:
    contract = _load_contract()
    research_route = _artifact(contract, "research_route.yaml")
    paths = _field_paths(research_route)

    assert research_route["type"] == "yaml"
    assert research_route["unknown_top_level_fields"] == "forbid"
    assert {
        "research_route",
        "factor_role",
        "factor_structure",
        "portfolio_expression",
        "neutralization_policy",
        "target_strategy_reference",
        "group_taxonomy_reference",
        "excluded_routes",
        "route_rationale",
        "route_change_policy",
        "route_change_policy.before_downstream_freeze",
        "route_change_policy.after_downstream_freeze",
        "route_contract_version",
    }.issubset(paths)

    route_field = next(field for field in research_route["fields"] if field["path"] == "research_route")
    assert route_field["type"] == "enum"
    assert route_field["values"] == ["time_series_signal", "cross_sectional_factor"]

    role_field = next(field for field in research_route["fields"] if field["path"] == "factor_role")
    assert role_field["allowed_values_if_nonempty"] == ["standalone_alpha", "regime_filter", "combo_filter"]


def test_mandate_contract_locks_time_split_and_run_config_shape() -> None:
    contract = _load_contract()
    time_split = _artifact(contract, "time_split.json")
    run_config = _artifact(contract, "run_config.toml")

    assert time_split["type"] == "json"
    assert _field_paths(time_split) == {
        "train",
        "test",
        "backtest",
        "holdout",
        "bar_size",
        "holding_horizons",
        "policy_note",
    }

    assert run_config["type"] == "toml"
    assert _field_paths(run_config) == {
        "stage",
        "lineage_id",
        "market",
        "universe",
        "target_task",
        "data_source",
        "bar_size",
        "non_rust_exceptions",
    }

    stage_field = next(field for field in run_config["fields"] if field["path"] == "stage")
    assert stage_field["type"] == "enum"
    assert stage_field["values"] == ["mandate"]


def test_mandate_contract_locks_parameter_grid_shape() -> None:
    contract = _load_contract()
    parameter_grid = _artifact(contract, "parameter_grid.yaml")

    assert parameter_grid["type"] == "yaml"
    assert _field_paths(parameter_grid) == {"parameters", "note"}
    parameters_field = next(field for field in parameter_grid["fields"] if field["path"] == "parameters")
    assert parameters_field["type"] == "list[map]"


def test_mandate_contract_field_paths_are_unique() -> None:
    contract = _load_contract()

    for artifact_name, artifact in contract["artifacts"].items():
        paths = [field["path"] for field in artifact.get("fields", [])]
        assert len(paths) == len(set(paths)), artifact_name
```

- [ ] **Step 2: Run contract test and verify it fails**

Run:

```bash
python -m pytest tests/contracts/test_mandate_artifact_contract.py -q
```

Expected:

```text
FAILED ... FileNotFoundError ... contracts/artifacts/mandate_artifacts.yaml
```

- [ ] **Step 3: Add the mandate artifact contract**

Create `contracts/artifacts/mandate_artifacts.yaml` with this content:

```yaml
schema_id: mandate-artifacts-v1
schema_version: v1
stage: mandate
stage_dir: 01_mandate/author/formal
unknown_machine_top_level_fields: forbid

artifacts:
  mandate.md:
    type: markdown
    required_sections:
      - Mandate
      - 目标
      - 研究意图
      - 路线理由
      - 成功标准
      - 失败标准
      - 已冻结执行输入
      - 执行合同
      - Gate 依据

  research_scope.md:
    type: markdown
    required_sections:
      - Research Scope

  research_route.yaml:
    type: yaml
    unknown_top_level_fields: forbid
    fields:
      - path: research_route
        type: enum
        values:
          - time_series_signal
          - cross_sectional_factor
      - path: factor_role
        type: string
        allowed_values_if_nonempty:
          - standalone_alpha
          - regime_filter
          - combo_filter
      - path: factor_structure
        type: string
        allowed_values_if_nonempty:
          - single_factor
          - multi_factor_score
      - path: portfolio_expression
        type: string
        allowed_values_if_nonempty:
          - long_short_market_neutral
          - long_only_rank
          - short_only_rank
          - benchmark_relative_long_only
          - group_relative_long_short
          - target_strategy_filter
          - target_strategy_overlay
      - path: neutralization_policy
        type: string
        allowed_values_if_nonempty:
          - none
          - market_beta_neutral
          - group_neutral
      - path: target_strategy_reference
        type: string
      - path: group_taxonomy_reference
        type: string
      - path: excluded_routes
        type: list[string]
        allowed_values_if_nonempty:
          - time_series_signal
          - cross_sectional_factor
      - path: route_rationale
        type: list[string]
      - path: route_change_policy
        type: map
      - path: route_change_policy.before_downstream_freeze
        type: string
      - path: route_change_policy.after_downstream_freeze
        type: string
      - path: route_contract_version
        type: string

  time_split.json:
    type: json
    unknown_top_level_fields: forbid
    fields:
      - path: train
        type: string
      - path: test
        type: string
      - path: backtest
        type: string
      - path: holdout
        type: string
      - path: bar_size
        type: string
      - path: holding_horizons
        type: list[string]
      - path: policy_note
        type: string

  parameter_grid.yaml:
    type: yaml
    unknown_top_level_fields: forbid
    fields:
      - path: parameters
        type: list[map]
      - path: note
        type: string

  run_config.toml:
    type: toml
    unknown_top_level_fields: forbid
    fields:
      - path: stage
        type: enum
        values:
          - mandate
      - path: lineage_id
        type: string
      - path: market
        type: string
      - path: universe
        type: string
      - path: target_task
        type: string
      - path: data_source
        type: string
      - path: bar_size
        type: string
      - path: non_rust_exceptions
        type: list[string]

  artifact_catalog.md:
    type: markdown
    required_sections:
      - 产物清单

  field_dictionary.md:
    type: markdown
    required_sections:
      - 字段字典
```

- [ ] **Step 4: Run contract test and verify it passes**

Run:

```bash
python -m pytest tests/contracts/test_mandate_artifact_contract.py -q
```

Expected:

```text
5 passed
```

---

### Task 2: Extend Artifact Validator For JSON, TOML, And list[map]

**Files:**
- Modify: `runtime/tools/artifact_contract_runtime.py`
- Modify: `tests/runtime/test_artifact_contract_runtime.py`

- [ ] **Step 1: Write failing validator tests**

Append these tests to `tests/runtime/test_artifact_contract_runtime.py`:

```python
def test_validate_stage_artifacts_reports_json_type_mismatch(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    stage_dir.mkdir()
    _write_minimal_valid_mandate_formal(stage_dir)
    (stage_dir / "time_split.json").write_text(
        '{"train":"","test":"","backtest":"","holdout":"","bar_size":"5m","holding_horizons":"15m","policy_note":"locked"}\n',
        encoding="utf-8",
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("mandate"))

    assert result.valid is False
    assert "time_split.json: holding_horizons expected list[string], found str" in result.errors


def test_validate_stage_artifacts_reports_toml_missing_field(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    stage_dir.mkdir()
    _write_minimal_valid_mandate_formal(stage_dir)
    (stage_dir / "run_config.toml").write_text(
        "\n".join(
            [
                'stage = "mandate"',
                'lineage_id = "btc_alt_transmission_v1"',
                'market = "Binance perpetual"',
                'universe = "top liquidity alts"',
                'target_task = "event-driven relative return study"',
                'data_source = "Binance UM futures klines"',
                'bar_size = "5m"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("mandate"))

    assert result.valid is False
    assert "run_config.toml: missing required field non_rust_exceptions" in result.errors


def test_validate_stage_artifacts_accepts_list_of_maps(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    stage_dir = tmp_path / "formal"
    stage_dir.mkdir()
    _write_minimal_valid_mandate_formal(stage_dir)
    _write_yaml(
        stage_dir / "parameter_grid.yaml",
        {
            "parameters": [
                {"name": "lookback", "type": "integer", "min": 5, "max": 60, "step": 5}
            ],
            "note": "locked parameter family",
        },
    )

    result = validate_stage_artifacts(stage_dir, load_artifact_contract("mandate"))

    assert result.valid is True
    assert result.errors == []
```

Also add this helper near the existing `_write_yaml()` helper:

```python
def _write_minimal_valid_mandate_formal(stage_dir: Path) -> None:
    (stage_dir / "mandate.md").write_text(
        "\n".join(
            [
                "# Mandate",
                "## 目标",
                "## 研究意图",
                "## 路线理由",
                "## 成功标准",
                "## 失败标准",
                "## 已冻结执行输入",
                "## 执行合同",
                "## Gate 依据",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "research_scope.md").write_text("# Research Scope\n", encoding="utf-8")
    _write_yaml(
        stage_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "",
            "group_taxonomy_reference": "sector_bucket_v1",
            "excluded_routes": ["time_series_signal"],
            "route_rationale": ["Cross-asset ranking expresses the edge best."],
            "route_change_policy": {
                "before_downstream_freeze": "rollback_to_mandate",
                "after_downstream_freeze": "child_lineage",
            },
            "route_contract_version": "v1",
        },
    )
    (stage_dir / "time_split.json").write_text(
        '{"train":"","test":"","backtest":"","holdout":"","bar_size":"5m","holding_horizons":["15m"],"policy_note":"locked"}\n',
        encoding="utf-8",
    )
    _write_yaml(stage_dir / "parameter_grid.yaml", {"parameters": [], "note": "locked parameter family"})
    (stage_dir / "run_config.toml").write_text(
        "\n".join(
            [
                'stage = "mandate"',
                'lineage_id = "btc_alt_transmission_v1"',
                'market = "Binance perpetual"',
                'universe = "top liquidity alts"',
                'target_task = "event-driven relative return study"',
                'data_source = "Binance UM futures klines"',
                'bar_size = "5m"',
                "non_rust_exceptions = []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "artifact_catalog.md").write_text("# 产物清单\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("# 字段字典\n", encoding="utf-8")
```

- [ ] **Step 2: Run validator tests and verify they fail**

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py -q
```

Expected:

```text
FAILED ... unsupported artifact contract stage: mandate
```

or:

```text
FAILED ... unsupported artifact type 'json'
```

- [ ] **Step 3: Implement validator support**

Modify `runtime/tools/artifact_contract_runtime.py`:

```python
import json
import tomllib
```

Update `ARTIFACT_CONTRACTS`:

```python
ARTIFACT_CONTRACTS = {
    "idea_intake": ROOT / "contracts" / "artifacts" / "idea_intake_artifacts.yaml",
    "mandate": ROOT / "contracts" / "artifacts" / "mandate_artifacts.yaml",
}
```

In `validate_stage_artifacts()`, add JSON/TOML branches:

```python
        if artifact_type == "json":
            errors.extend(_validate_mapping_artifact(artifact_name, artifact_path, artifact_contract, contract, parser="json"))
            continue
        if artifact_type == "toml":
            errors.extend(_validate_mapping_artifact(artifact_name, artifact_path, artifact_contract, contract, parser="toml"))
            continue
```

Replace `_validate_yaml_artifact()` body with a parser wrapper that delegates to a shared mapping validator:

```python
def _validate_yaml_artifact(
    artifact_name: str,
    artifact_path: Path,
    artifact_contract: dict[str, Any],
    stage_contract: dict[str, Any],
) -> list[str]:
    return _validate_mapping_artifact(artifact_name, artifact_path, artifact_contract, stage_contract, parser="yaml")
```

Add:

```python
def _validate_mapping_artifact(
    artifact_name: str,
    artifact_path: Path,
    artifact_contract: dict[str, Any],
    stage_contract: dict[str, Any],
    *,
    parser: str,
) -> list[str]:
    errors: list[str] = []
    try:
        payload = _load_mapping_payload(artifact_path, parser=parser)
    except Exception as exc:
        return [f"{artifact_name}: {parser} parse failed: {exc}"]

    if not isinstance(payload, dict):
        return [f"{artifact_name}: expected {parser} map, found {type(payload).__name__}"]

    if _unknown_top_level_fields_forbidden(artifact_contract, stage_contract):
        allowed = _allowed_top_level_fields(artifact_contract)
        for key in payload:
            if key not in allowed:
                errors.append(f"{artifact_name}: unknown top-level field {key}")

    for field in artifact_contract.get("fields", []):
        field_path = str(field["path"])
        exists, value = _resolve_field(payload, field_path)
        if not exists:
            errors.append(f"{artifact_name}: missing required field {field_path}")
            continue
        errors.extend(_validate_field_value(artifact_name, field_path, value, field))

    errors.extend(_validate_declared_groups(artifact_name, payload, artifact_contract))
    return errors
```

Add:

```python
def _load_mapping_payload(path: Path, *, parser: str) -> Any:
    if parser == "yaml":
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    if parser == "json":
        return json.loads(path.read_text(encoding="utf-8"))
    if parser == "toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise ArtifactContractError(f"unsupported mapping parser: {parser}")
```

Update `_matches_type()`:

```python
    if expected_type == "list[map]":
        return isinstance(value, list) and all(isinstance(item, dict) for item in value)
```

Update `_unknown_top_level_fields_forbidden()` so `unknown_machine_top_level_fields` applies to JSON/TOML/YAML unless artifact-specific policy exists:

```python
def _unknown_top_level_fields_forbidden(artifact_contract: dict[str, Any], stage_contract: dict[str, Any]) -> bool:
    artifact_policy = artifact_contract.get("unknown_top_level_fields")
    if artifact_policy is not None:
        return artifact_policy == "forbid"
    machine_policy = stage_contract.get("unknown_machine_top_level_fields")
    if machine_policy is not None:
        return machine_policy == "forbid"
    return stage_contract.get("unknown_yaml_top_level_fields") == "forbid"
```

- [ ] **Step 4: Run validator tests and verify they pass**

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py tests/contracts/test_mandate_artifact_contract.py -q
```

Expected:

```text
all tests passed
```

---

### Task 3: Make Runtime Mandate Output Pass The Contract

**Files:**
- Modify: `runtime/tools/idea_runtime.py`
- Modify: `tests/session/test_idea_runtime_scripts.py`
- Create: `tests/session/test_mandate_artifact_shape.py`

- [ ] **Step 1: Write failing generated-output tests**

Create `tests/session/test_mandate_artifact_shape.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from subprocess import run
import sys
import tomllib

import yaml

from tests.helpers.lineage_program_support import ensure_stage_program
from tests.helpers.repo_paths import REPO_ROOT
from tests.session.test_idea_runtime_scripts import _mandate_freeze_draft, _route_assessment, _write_yaml


def _build_valid_mandate(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "route_assessment": _route_assessment(),
            "approved_scope": {
                "market": "Binance perpetual",
                "data_source": "Binance UM futures klines",
                "universe": "top liquidity alts",
                "bar_size": "5m",
                "horizons": ["15m", "30m", "60m"],
                "target_task": "event-driven relative return study",
                "excluded_scope": ["low liquidity tails"],
            },
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {
            "market": "Binance perpetual",
            "data_source": "Binance UM futures klines",
            "instrument_type": "perpetual",
            "universe": "top liquidity alts",
            "bar_size": "5m",
            "holding_horizons": ["15m", "30m", "60m"],
            "target_task": "event-driven relative return study",
            "excluded_scope": ["low liquidity tails"],
            "budget_days": 10,
            "max_iterations": 3,
        },
    )
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n", encoding="utf-8")
    (intake_dir / "qualification_scorecard.yaml").write_text("idea_id: btc_alt_transmission_v1\n", encoding="utf-8")
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "mandate")

    result = run(
        [sys.executable, "runtime/scripts/build_mandate_from_intake.py", "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return lineage_root / "01_mandate" / "author" / "formal"


def test_generated_mandate_file_tree_matches_artifact_contract(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract

    formal_dir = _build_valid_mandate(tmp_path)
    contract = load_artifact_contract("mandate")

    assert sorted(path.name for path in formal_dir.iterdir()) == sorted(
        [*contract["artifacts"], "program_execution_manifest.json"]
    )


def test_generated_mandate_machine_shapes_match_contract(tmp_path: Path) -> None:
    formal_dir = _build_valid_mandate(tmp_path)

    route = yaml.safe_load((formal_dir / "research_route.yaml").read_text(encoding="utf-8"))
    assert list(route) == [
        "research_route",
        "factor_role",
        "factor_structure",
        "portfolio_expression",
        "neutralization_policy",
        "target_strategy_reference",
        "group_taxonomy_reference",
        "excluded_routes",
        "route_rationale",
        "route_change_policy",
        "route_contract_version",
    ]

    time_split = json.loads((formal_dir / "time_split.json").read_text(encoding="utf-8"))
    assert list(time_split) == ["train", "test", "backtest", "holdout", "bar_size", "holding_horizons", "policy_note"]

    run_config = tomllib.loads((formal_dir / "run_config.toml").read_text(encoding="utf-8"))
    assert list(run_config) == [
        "stage",
        "lineage_id",
        "market",
        "universe",
        "target_task",
        "data_source",
        "bar_size",
        "non_rust_exceptions",
    ]
    assert run_config["non_rust_exceptions"] == []


def test_generated_mandate_passes_artifact_shape_validator(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    formal_dir = _build_valid_mandate(tmp_path)

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("mandate"))

    assert result.valid is True
    assert result.errors == []
```

Append this assertion to `test_build_mandate_from_intake_creates_mandate_artifacts()` in `tests/session/test_idea_runtime_scripts.py`:

```python
    assert "non_rust_exceptions = []" in (mandate_formal_dir / "run_config.toml").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run generated-output tests and verify they fail**

Run:

```bash
python -m pytest tests/session/test_mandate_artifact_shape.py tests/session/test_idea_runtime_scripts.py::test_build_mandate_from_intake_creates_mandate_artifacts -q
```

Expected:

```text
FAILED ... missing required field non_rust_exceptions
```

- [ ] **Step 3: Update mandate builder output and post-build validation**

Modify `runtime/tools/idea_runtime.py`.

In the `run_config.toml` write block, add:

```python
                "non_rust_exceptions = []",
```

In `artifact_catalog.md`, include `field_dictionary.md`:

```python
    (mandate_formal_dir / "artifact_catalog.md").write_text(
        "# 产物清单\n\n- mandate.md\n- research_scope.md\n- research_route.yaml\n- time_split.json\n- parameter_grid.yaml\n- run_config.toml\n- field_dictionary.md\n",
        encoding="utf-8",
    )
```

Immediately before `return mandate_dir`, add:

```python
    validation = validate_stage_artifacts(mandate_formal_dir, load_artifact_contract("mandate"))
    if not validation.valid:
        joined_errors = "; ".join(validation.errors)
        raise ValueError(f"mandate formal artifacts do not match artifact contract: {joined_errors}")
```

- [ ] **Step 4: Run generated-output tests and verify they pass**

Run:

```bash
python -m pytest tests/session/test_mandate_artifact_shape.py tests/session/test_idea_runtime_scripts.py::test_build_mandate_from_intake_creates_mandate_artifacts -q
```

Expected:

```text
all tests passed
```

---

### Task 4: Enable qros-validate-stage For Mandate

**Files:**
- Modify: `tests/runtime/test_validate_stage_artifacts_script.py`

- [ ] **Step 1: Replace unsupported mandate test with mandate CLI tests**

In `tests/runtime/test_validate_stage_artifacts_script.py`, replace `test_validate_stage_artifacts_script_rejects_unsupported_stage()` with:

```python
def test_validate_stage_artifacts_script_accepts_valid_mandate(tmp_path: Path) -> None:
    from tests.helpers.lineage_program_support import ensure_stage_program
    from tests.session.test_idea_runtime_scripts import _mandate_freeze_draft, _route_assessment

    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_transmission_v1"
    intake_dir = lineage_root / "00_idea_intake"
    intake_dir.mkdir(parents=True)
    _write_yaml(
        intake_dir / "idea_gate_decision.yaml",
        {
            "idea_id": "btc_alt_transmission_v1",
            "verdict": "GO_TO_MANDATE",
            "why": ["variables are observable"],
            "route_assessment": _route_assessment(),
            "approved_scope": {},
            "required_reframe_actions": [],
            "rollback_target": "00_idea_intake",
        },
    )
    _write_yaml(
        intake_dir / "scope_canvas.yaml",
        {
            "market": "Binance perpetual",
            "data_source": "Binance UM futures klines",
            "instrument_type": "perpetual",
            "universe": "top liquidity alts",
            "bar_size": "5m",
            "holding_horizons": ["15m"],
            "target_task": "event-driven relative return study",
            "excluded_scope": [],
            "budget_days": 10,
            "max_iterations": 3,
        },
    )
    (intake_dir / "research_question_set.md").write_text("# Research Questions\n", encoding="utf-8")
    (intake_dir / "qualification_scorecard.yaml").write_text("idea_id: btc_alt_transmission_v1\n", encoding="utf-8")
    _write_yaml(intake_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    ensure_stage_program(lineage_root, "mandate")

    build = run(
        [sys.executable, "runtime/scripts/build_mandate_from_intake.py", "--lineage-root", str(lineage_root)],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert build.returncode == 0, build.stderr

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "mandate",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert "mandate artifact shape valid" in result.stdout


def test_validate_stage_artifacts_script_reports_invalid_mandate_shape(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    formal_dir = outputs_root / "btc_alt_transmission_v1" / "01_mandate" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "mandate.md").write_text("# Mandate\n", encoding="utf-8")

    result = run(
        [
            sys.executable,
            "runtime/scripts/validate_stage_artifacts.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_alt_transmission_v1",
            "--stage",
            "mandate",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 1
    assert "research_scope.md: missing required artifact" in result.stderr
```

- [ ] **Step 2: Run CLI validation tests**

Run:

```bash
python -m pytest tests/runtime/test_validate_stage_artifacts_script.py -q
```

Expected:

```text
all tests passed
```

---

### Task 5: Thin Mandate Skill And Update User Docs

**Files:**
- Modify: `skills/mandate/qros-mandate-author/SKILL.md`
- Modify: `docs/guides/idea-intake-to-mandate-flow.md`
- Modify: `tests/session/test_idea_intake_assets.py`
- Modify: `tests/bootstrap/test_project_bootstrap.py`

- [ ] **Step 1: Write failing docs/assets assertions**

Append assertions to `tests/session/test_idea_intake_assets.py`:

```python
    assert "contracts/artifacts/mandate_artifacts.yaml" in mandate_text
    assert "qros-validate-stage" in mandate_text
    assert "不得把 SKILL.md 作为字段真值" in mandate_text
```

Add this assertion in `test_usage_doc_exists()` or the nearest doc-content test in the same file:

```python
    flow_text = Path("docs/guides/idea-intake-to-mandate-flow.md").read_text(encoding="utf-8")
    assert "qros-validate-stage --stage mandate" in flow_text
    assert "contracts/artifacts/mandate_artifacts.yaml" in flow_text
```

Add this assertion to `tests/bootstrap/test_project_bootstrap.py`:

```python
    assert Path("contracts/artifacts/mandate_artifacts.yaml").exists()
```

- [ ] **Step 2: Run docs/assets tests and verify they fail**

Run:

```bash
python -m pytest tests/session/test_idea_intake_assets.py tests/bootstrap/test_project_bootstrap.py -q
```

Expected:

```text
FAILED ... contracts/artifacts/mandate_artifacts.yaml
```

or:

```text
FAILED ... qros-validate-stage --stage mandate
```

- [ ] **Step 3: Thin the mandate author skill**

Modify `skills/mandate/qros-mandate-author/SKILL.md`.

Under `## Mandatory Discipline`, add:

```markdown
- `contracts/artifacts/mandate_artifacts.yaml` 是 `01_mandate/author/formal` 的字段真值层
- 不得把 `SKILL.md` 作为字段真值；skill 只负责执行顺序、freeze 访谈和 runtime 调用
- 生成正式 mandate artifacts 后，必须运行 `qros-validate-stage --stage mandate`
- validator 不通过，不得进入 mandate review
```

Under `## Working Rules`, add after formal artifact generation:

```markdown
14. 运行 `qros-validate-stage --stage mandate`
15. validator 不通过时，修复 formal artifacts；不得宣布 mandate 完成或进入 review
```

- [ ] **Step 4: Update idea-to-mandate docs**

Modify `docs/guides/idea-intake-to-mandate-flow.md` near the mandate build instructions:

````markdown
`01_mandate/author/formal` 的正式 artifact shape 由 `contracts/artifacts/mandate_artifacts.yaml` 定义。`qros-mandate-author` 不再维护字段真值，只维护 freeze 顺序、确认规则和 validator 调用纪律。

构建 mandate 后必须运行：

```bash
qros-validate-stage --stage mandate --lineage-id <lineage_id>
```

如果 validator 失败，不得进入 mandate review。
````

- [ ] **Step 5: Run docs/assets tests and verify they pass**

Run:

```bash
python -m pytest tests/session/test_idea_intake_assets.py tests/bootstrap/test_project_bootstrap.py -q
```

Expected:

```text
all tests passed
```

---

### Task 6: Focused Verification And Smoke

**Files:**
- No source edits.

- [ ] **Step 1: Run focused contract/runtime/session tests**

Run:

```bash
python -m pytest \
  tests/contracts/test_idea_intake_artifact_contract.py \
  tests/contracts/test_mandate_artifact_contract.py \
  tests/runtime/test_artifact_contract_runtime.py \
  tests/runtime/test_validate_stage_artifacts_script.py \
  tests/session/test_idea_intake_artifact_shape.py \
  tests/session/test_mandate_artifact_shape.py \
  tests/session/test_idea_runtime_scripts.py \
  tests/session/test_idea_intake_assets.py \
  tests/bootstrap/test_project_bootstrap.py \
  -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 2: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected:

```text
all tests passed
```

- [ ] **Step 3: Decide whether full-smoke is required**

Run full-smoke only if the implementation changes `qros-research-session` stage flow, gate semantics, review orchestration, route split, CSF routing, anti-drift snapshots, canonical session naming, or stage-display supported stage contracts.

For the planned MVP, expected decision:

```text
full-smoke not required: artifact contract validation only; no session flow/gate semantic change
```

- [ ] **Step 4: Show diff and wait for user confirmation**

Run:

```bash
git status --short --branch
git diff --stat
git diff -- contracts/artifacts/mandate_artifacts.yaml runtime/tools/artifact_contract_runtime.py runtime/tools/idea_runtime.py
```

Report:

```text
No commit has been created.
No push has been run.
Waiting for explicit user confirmation before commit.
```

---

## Self-Review

**Spec coverage:** The plan covers mandate contract creation, validator support, runtime post-validation, CLI wrapper behavior, shape snapshot tests, skill/docs thinning, focused tests, and smoke.

**Placeholder scan:** No `TBD`, broad "add tests" instruction, or unspecified edge handling remains. Each task names exact files, commands, expected outcomes, and concrete snippets.

**Type consistency:** Contract types are limited to existing validator types plus `json`, `toml`, and `list[map]`, all introduced in Task 2 before use in generated artifact validation.
