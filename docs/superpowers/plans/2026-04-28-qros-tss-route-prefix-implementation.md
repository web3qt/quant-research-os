# QROS TSS Route Prefix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `research_route = time_series_signal` 的 canonical post-mandate 主线迁移到 `tss_*` 阶段，并让 TSS 在 contracts、runtime、skills、review preflight 和 diagnostics 结构上对齐现有 CSF 路线。

**Architecture:** 先建立 canonical stage naming 和 artifact contracts，再接入通用 artifact validator、TSS semantic validators、session routing、author/review skills、docs 和 diagnostics。每批都以 focused tests 收敛，只有触及 session routing / stage naming / route split 的批次才扩大到 smoke 或 full-smoke。

**Tech Stack:** Python stdlib, PyYAML, PyArrow/Polars parquet validation, pytest, existing QROS runtime helpers under `runtime/tools/`, existing skill layout under `skills/`, existing review preflight machinery under `runtime/tools/review_skillgen/`.

**Execution constraints:** 不得 `git commit`、`git push`、创建 PR 或改 `main`，除非用户在看到 diff 和验证结果后明确确认。当前 plan 文件位于 `docs/superpowers/plans/`，该目录被 `.gitignore` 忽略；若要纳入版本控制，需要显式 `git add -f`。

---

## Final Target

After migration, a new `time_series_signal` lineage must follow:

```text
00_idea_intake
01_mandate
02_tss_data_ready
03_tss_signal_ready
04_tss_train_freeze
05_tss_test_evidence
06_tss_backtest_ready
07_tss_holdout_validation
```

New time-series lineages must not create or advertise these old post-mandate stage directories as canonical:

```text
02_data_ready
03_signal_ready
04_train_freeze
05_test_evidence
06_backtest
07_holdout
```

The CSF branch remains unchanged:

```text
02_csf_data_ready
03_csf_signal_ready
04_csf_train_freeze
05_csf_test_evidence
06_csf_backtest_ready
07_csf_holdout_validation
```

---

## File Map

### Contracts

- Create: `contracts/artifacts/tss_data_ready_artifacts.yaml`
- Create: `contracts/artifacts/tss_signal_ready_artifacts.yaml`
- Create: `contracts/artifacts/tss_train_freeze_artifacts.yaml`
- Create: `contracts/artifacts/tss_test_evidence_artifacts.yaml`
- Create: `contracts/artifacts/tss_backtest_ready_artifacts.yaml`
- Create: `contracts/artifacts/tss_holdout_validation_artifacts.yaml`
- Modify: `contracts/stages/workflow_stage_gates.yaml`
- Modify: `contracts/agent_eval/qros_agent_behavior_eval_cases.yaml`

### Runtime

- Modify: `runtime/tools/artifact_contract_runtime.py`
- Create: `runtime/tools/tss_data_ready_runtime.py`
- Create: `runtime/tools/tss_signal_ready_runtime.py`
- Create: `runtime/tools/tss_train_runtime.py`
- Create: `runtime/tools/tss_test_evidence_runtime.py`
- Create: `runtime/tools/tss_backtest_runtime.py`
- Create: `runtime/tools/tss_holdout_runtime.py`
- Create: `runtime/tools/tss_data_ready_contract_runtime.py`
- Create: `runtime/tools/tss_signal_ready_contract_runtime.py`
- Create: `runtime/tools/tss_train_freeze_contract_runtime.py`
- Create: `runtime/tools/tss_test_evidence_contract_runtime.py`
- Create: `runtime/tools/tss_backtest_ready_contract_runtime.py`
- Create: `runtime/tools/tss_holdout_validation_contract_runtime.py`
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/scripts/run_research_session.py`
- Modify: `runtime/scripts/run_verification_tier.py`
- Modify: `runtime/tools/review_skillgen/context_inference.py`
- Modify: `runtime/tools/review_skillgen/render.py`
- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Modify: `runtime/tools/review_skillgen/upstream_binding_validator.py`
- Modify: `runtime/tools/progress_runtime.py`
- Modify: `runtime/tools/research_session_reflection.py`
- Modify: `runtime/tools/stage_display_runtime.py` if present in the active branch; otherwise update the stage display module that owns supported stage metadata.

### Skills

- Create: `skills/tss_data_ready/qros-tss-data-ready-author/SKILL.md`
- Create: `skills/tss_data_ready/qros-tss-data-ready-review/SKILL.md`
- Create: `skills/tss_signal_ready/qros-tss-signal-ready-author/SKILL.md`
- Create: `skills/tss_signal_ready/qros-tss-signal-ready-review/SKILL.md`
- Create: `skills/tss_train_freeze/qros-tss-train-freeze-author/SKILL.md`
- Create: `skills/tss_train_freeze/qros-tss-train-freeze-review/SKILL.md`
- Create: `skills/tss_test_evidence/qros-tss-test-evidence-author/SKILL.md`
- Create: `skills/tss_test_evidence/qros-tss-test-evidence-review/SKILL.md`
- Create: `skills/tss_backtest_ready/qros-tss-backtest-ready-author/SKILL.md`
- Create: `skills/tss_backtest_ready/qros-tss-backtest-ready-review/SKILL.md`
- Create: `skills/tss_holdout_validation/qros-tss-holdout-validation-author/SKILL.md`
- Create: `skills/tss_holdout_validation/qros-tss-holdout-validation-review/SKILL.md`
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `skills/core/using-qros/SKILL.md`
- Modify: legacy unprefixed time-series skills under `skills/data_ready/`, `skills/signal_ready/`, `skills/train_freeze/`, `skills/test_evidence/`, `skills/backtest_ready/`, `skills/holdout_validation/` to mark them non-canonical or remove them after tests stop referencing them.

### Diagnostics

- Create: `contracts/diagnostics/tss_metric_library.yaml`
- Create: `contracts/diagnostics/tss_stage_diagnostic_profiles.yaml`
- Create: `runtime/tools/signal_diagnostics.py`
- Create: `runtime/scripts/run_signal_diagnostics.py`
- Create: `runtime/bin/qros-signal-diagnostics`
- Create: `skills/core/qros-signal-diagnostics/SKILL.md`

### Docs

- Modify: `docs/sop/main-flow/research_workflow_sop.md`
- Create: `docs/sop/main-flow/02_tss_data_ready_sop_cn.md`
- Create: `docs/sop/main-flow/03_tss_signal_ready_sop_cn.md`
- Create: `docs/sop/main-flow/04_tss_train_freeze_sop_cn.md`
- Create: `docs/sop/main-flow/05_tss_test_evidence_sop_cn.md`
- Create: `docs/sop/main-flow/06_tss_backtest_ready_sop_cn.md`
- Create: `docs/sop/main-flow/07_tss_holdout_validation_sop_cn.md`
- Modify: `docs/guides/qros-verification-tiers.md`
- Modify or create docs/tests that lock user-facing TSS naming.

### Tests

- Create: `tests/contracts/test_tss_artifact_contracts.py`
- Create: `tests/runtime/test_tss_data_ready_runtime.py`
- Create: `tests/runtime/test_tss_signal_ready_runtime.py`
- Create: `tests/runtime/test_tss_train_runtime.py`
- Create: `tests/runtime/test_tss_test_evidence_runtime.py`
- Create: `tests/runtime/test_tss_backtest_runtime.py`
- Create: `tests/runtime/test_tss_holdout_runtime.py`
- Create: `tests/runtime/test_tss_contract_validators.py`
- Create: `tests/session/test_tss_research_session_routing.py`
- Create: `tests/skills/test_tss_author_review_skills.py`
- Create: `tests/docs/test_tss_route_docs.py`
- Create: `tests/runtime/test_signal_diagnostics.py`
- Create: `tests/docs/test_signal_diagnostics_docs.py`

---

## Batch 1: Lock TSS Stage Naming And Contracts

### Task 1.1: Write contract existence tests

**Files:**
- Create: `tests/contracts/test_tss_artifact_contracts.py`

- [ ] **Step 1: Add failing tests for all six TSS contracts**

Write tests that load the expected YAML files directly and assert `stage`, `stage_dir`, and required artifact names.

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIR = ROOT / "contracts" / "artifacts"


EXPECTED = {
    "tss_data_ready": {
        "path": "tss_data_ready_artifacts.yaml",
        "stage_dir": "02_tss_data_ready/author/formal",
        "artifacts": {
            "time_index_manifest.json",
            "asset_time_index.parquet",
            "quality_flags.parquet",
            "split_sample_adequacy_report.yaml",
            "run_manifest.json",
            "rebuild_tss_data_ready.py",
        },
    },
    "tss_signal_ready": {
        "path": "tss_signal_ready_artifacts.yaml",
        "stage_dir": "03_tss_signal_ready/author/formal",
        "artifacts": {
            "signal_manifest.yaml",
            "param_manifest.csv",
            "signal_panel.parquet",
            "signal_event_panel.parquet",
            "route_inheritance_contract.yaml",
        },
    },
    "tss_train_freeze": {
        "path": "tss_train_freeze_artifacts.yaml",
        "stage_dir": "04_tss_train_freeze/author/formal",
        "artifacts": {
            "tss_train_freeze.yaml",
            "train_threshold_ledger.csv",
            "train_variant_ledger.csv",
            "train_variant_rejects.csv",
        },
    },
    "tss_test_evidence": {
        "path": "tss_test_evidence_artifacts.yaml",
        "stage_dir": "05_tss_test_evidence/author/formal",
        "artifacts": {
            "event_forward_return.parquet",
            "signal_performance_summary.json",
            "tss_test_gate_table.csv",
            "tss_selected_variants_test.csv",
        },
    },
    "tss_backtest_ready": {
        "path": "tss_backtest_ready_artifacts.yaml",
        "stage_dir": "06_tss_backtest_ready/author/formal",
        "artifacts": {
            "strategy_contract.yaml",
            "engine_compare.csv",
            "position_timeseries.parquet",
            "trade_ledger.csv",
            "tss_backtest_gate_table.csv",
        },
    },
    "tss_holdout_validation": {
        "path": "tss_holdout_validation_artifacts.yaml",
        "stage_dir": "07_tss_holdout_validation/author/formal",
        "artifacts": {
            "tss_holdout_run_manifest.json",
            "holdout_signal_diagnostics.parquet",
            "holdout_event_compare.parquet",
            "holdout_backtest_compare.parquet",
        },
    },
}


def _load_contract(filename: str) -> dict:
    return yaml.safe_load((CONTRACT_DIR / filename).read_text(encoding="utf-8"))


def test_tss_artifact_contract_files_exist_and_declare_stage_shape() -> None:
    for stage, expected in EXPECTED.items():
        contract_path = CONTRACT_DIR / expected["path"]
        assert contract_path.exists(), f"{contract_path} missing"
        contract = _load_contract(expected["path"])
        assert contract["stage"] == stage
        assert contract["stage_dir"] == expected["stage_dir"]
        assert contract["unknown_machine_top_level_fields"] == "forbid"


def test_tss_artifact_contracts_lock_required_artifact_names() -> None:
    for stage, expected in EXPECTED.items():
        contract = _load_contract(expected["path"])
        artifacts = set(contract["artifacts"])
        missing = expected["artifacts"] - artifacts
        assert not missing, f"{stage} missing artifacts: {sorted(missing)}"
```

- [ ] **Step 2: Run the tests and confirm RED**

Run:

```bash
python -m pytest tests/contracts/test_tss_artifact_contracts.py -q
```

Expected:

```text
FAILED ... tss_data_ready_artifacts.yaml missing
```

### Task 1.2: Create TSS artifact contracts

**Files:**
- Create: `contracts/artifacts/tss_data_ready_artifacts.yaml`
- Create: `contracts/artifacts/tss_signal_ready_artifacts.yaml`
- Create: `contracts/artifacts/tss_train_freeze_artifacts.yaml`
- Create: `contracts/artifacts/tss_test_evidence_artifacts.yaml`
- Create: `contracts/artifacts/tss_backtest_ready_artifacts.yaml`
- Create: `contracts/artifacts/tss_holdout_validation_artifacts.yaml`

- [ ] **Step 1: Add contracts with explicit required fields**

Use the schema style from existing `contracts/artifacts/csf_*_artifacts.yaml`. Each contract must include:

```yaml
schema_version: v1
stage: <tss_stage>
stage_dir: <canonical_stage_dir>/author/formal
unknown_machine_top_level_fields: forbid
artifacts:
  artifact_name:
    type: json | yaml | csv | parquet | directory | markdown | script
```

For machine-readable mapping artifacts, require these common fields:

```yaml
- path: stage
  type: enum
  values:
    - <tss_stage>
- path: lineage_id
  type: string
- path: research_route
  type: enum
  values:
    - time_series_signal
```

Use these stage-specific primary keys:

```text
tss_data_ready: asset, timestamp
tss_signal_ready: asset, timestamp, param_id, horizon
tss_train_freeze: variant_id
tss_test_evidence: variant_id, horizon
tss_backtest_ready: timestamp, strategy_id
tss_holdout_validation: strategy_id
```

- [ ] **Step 2: Run the contract tests and confirm GREEN**

Run:

```bash
python -m pytest tests/contracts/test_tss_artifact_contracts.py -q
```

Expected:

```text
2 passed
```

### Task 1.3: Register TSS contracts in artifact runtime

**Files:**
- Modify: `runtime/tools/artifact_contract_runtime.py`
- Test: `tests/contracts/test_tss_artifact_contracts.py`

- [ ] **Step 1: Add failing test for `load_artifact_contract()`**

Append:

```python
from runtime.tools.artifact_contract_runtime import load_artifact_contract


def test_tss_contracts_are_registered_in_artifact_runtime() -> None:
    for stage in EXPECTED:
        contract = load_artifact_contract(stage)
        assert contract["stage"] == stage
```

Run:

```bash
python -m pytest tests/contracts/test_tss_artifact_contracts.py::test_tss_contracts_are_registered_in_artifact_runtime -q
```

Expected:

```text
FAILED ... unsupported artifact contract stage: tss_data_ready
```

- [ ] **Step 2: Register contracts**

Modify `ARTIFACT_CONTRACTS`:

```python
ARTIFACT_CONTRACTS = {
    "idea_intake": ROOT / "contracts" / "artifacts" / "idea_intake_artifacts.yaml",
    "mandate": ROOT / "contracts" / "artifacts" / "mandate_artifacts.yaml",
    "csf_data_ready": ROOT / "contracts" / "artifacts" / "csf_data_ready_artifacts.yaml",
    "csf_signal_ready": ROOT / "contracts" / "artifacts" / "csf_signal_ready_artifacts.yaml",
    "csf_train_freeze": ROOT / "contracts" / "artifacts" / "csf_train_freeze_artifacts.yaml",
    "csf_test_evidence": ROOT / "contracts" / "artifacts" / "csf_test_evidence_artifacts.yaml",
    "csf_backtest_ready": ROOT / "contracts" / "artifacts" / "csf_backtest_ready_artifacts.yaml",
    "csf_holdout_validation": ROOT / "contracts" / "artifacts" / "csf_holdout_validation_artifacts.yaml",
    "tss_data_ready": ROOT / "contracts" / "artifacts" / "tss_data_ready_artifacts.yaml",
    "tss_signal_ready": ROOT / "contracts" / "artifacts" / "tss_signal_ready_artifacts.yaml",
    "tss_train_freeze": ROOT / "contracts" / "artifacts" / "tss_train_freeze_artifacts.yaml",
    "tss_test_evidence": ROOT / "contracts" / "artifacts" / "tss_test_evidence_artifacts.yaml",
    "tss_backtest_ready": ROOT / "contracts" / "artifacts" / "tss_backtest_ready_artifacts.yaml",
    "tss_holdout_validation": ROOT / "contracts" / "artifacts" / "tss_holdout_validation_artifacts.yaml",
}
```

- [ ] **Step 3: Run focused contract tests**

Run:

```bash
python -m pytest tests/contracts/test_tss_artifact_contracts.py -q
```

Expected:

```text
3 passed
```

---

## Batch 2: Build TSS Runtime Scaffolds And Semantic Validators

### Task 2.1: Add TSS runtime scaffold tests

**Files:**
- Create: `tests/runtime/test_tss_data_ready_runtime.py`
- Create: `tests/runtime/test_tss_signal_ready_runtime.py`
- Create: `tests/runtime/test_tss_train_runtime.py`
- Create: `tests/runtime/test_tss_test_evidence_runtime.py`
- Create: `tests/runtime/test_tss_backtest_runtime.py`
- Create: `tests/runtime/test_tss_holdout_runtime.py`

- [ ] **Step 1: Write RED tests for scaffold paths**

Use one test per stage. Example for data ready:

```python
from pathlib import Path

import yaml

from runtime.tools.tss_data_ready_runtime import scaffold_tss_data_ready


def test_scaffold_tss_data_ready_creates_draft_under_tss_stage_dir(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"

    stage_dir = scaffold_tss_data_ready(lineage_root)

    assert stage_dir == lineage_root / "02_tss_data_ready"
    draft_path = stage_dir / "author" / "draft" / "tss_data_ready_freeze_draft.yaml"
    assert draft_path.exists()
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
    assert set(payload["groups"]) == {
        "time_index_contract",
        "quality_semantics",
        "label_contract",
        "feature_base",
        "delivery_contract",
    }
```

Replicate with stage-specific function names:

```text
scaffold_tss_signal_ready -> 03_tss_signal_ready / tss_signal_ready_freeze_draft.yaml
scaffold_tss_train_freeze -> 04_tss_train_freeze / tss_train_freeze_draft.yaml
scaffold_tss_test_evidence -> 05_tss_test_evidence / tss_test_evidence_draft.yaml
scaffold_tss_backtest_ready -> 06_tss_backtest_ready / tss_backtest_ready_draft.yaml
scaffold_tss_holdout_validation -> 07_tss_holdout_validation / tss_holdout_validation_draft.yaml
```

Run:

```bash
python -m pytest tests/runtime/test_tss_*_runtime.py -q
```

Expected:

```text
FAILED ... ModuleNotFoundError: No module named 'runtime.tools.tss_data_ready_runtime'
```

### Task 2.2: Implement TSS scaffold modules

**Files:**
- Create: `runtime/tools/tss_data_ready_runtime.py`
- Create: `runtime/tools/tss_signal_ready_runtime.py`
- Create: `runtime/tools/tss_train_runtime.py`
- Create: `runtime/tools/tss_test_evidence_runtime.py`
- Create: `runtime/tools/tss_backtest_runtime.py`
- Create: `runtime/tools/tss_holdout_runtime.py`

- [ ] **Step 1: Implement scaffold functions only**

Each module should follow the pattern from existing `csf_*_runtime.py`, but only implement scaffold and blank freeze draft in this batch.

Example skeleton for `runtime/tools/tss_data_ready_runtime.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


TSS_DATA_READY_FREEZE_DRAFT_FILE = "tss_data_ready_freeze_draft.yaml"
TSS_DATA_READY_FREEZE_GROUP_ORDER = [
    "time_index_contract",
    "quality_semantics",
    "label_contract",
    "feature_base",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_tss_data_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "time_index_contract": {
                "confirmed": False,
                "draft": {
                    "asset_key": "asset",
                    "timestamp_key": "timestamp",
                    "bar_size": "",
                    "timestamp_semantics": "",
                },
                "missing_items": [],
            },
            "quality_semantics": {
                "confirmed": False,
                "draft": {
                    "missing_policy": "",
                    "stale_policy": "",
                    "bad_price_policy": "",
                    "outlier_policy": "",
                    "low_liquidity_policy": "",
                },
                "missing_items": [],
            },
            "label_contract": {
                "confirmed": False,
                "draft": {
                    "horizons": [],
                    "forward_return_fields": [],
                    "label_availability_rule": "",
                    "no_lookahead_guardrail": "",
                },
                "missing_items": [],
            },
            "feature_base": {
                "confirmed": False,
                "draft": {
                    "feature_outputs": [],
                    "forbidden_label_inputs": ["forward_label_base"],
                    "feature_asof_rule": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "tss_signal_ready",
                    "frozen_inputs_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_tss_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "02_tss_data_ready"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / TSS_DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_tss_data_ready_freeze_draft())
    return stage_dir
```

- [ ] **Step 2: Run scaffold tests**

Run:

```bash
python -m pytest tests/runtime/test_tss_*_runtime.py -q
```

Expected:

```text
6 passed
```

### Task 2.3: Add semantic validator tests

**Files:**
- Create: `tests/runtime/test_tss_contract_validators.py`

- [ ] **Step 1: Write failing tests for the most important route-specific checks**

Add tests:

```python
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.tss_signal_ready_contract_runtime import validate_tss_signal_ready_semantics


def _write_parquet(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {key: [row.get(key) for row in rows] for key in rows[0]}
    pq.write_table(pa.table(columns), path)


def test_tss_signal_ready_rejects_forward_label_input_binding(tmp_path: Path) -> None:
    formal_dir = tmp_path / "outputs" / "tss_case" / "03_tss_signal_ready" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    yaml.safe_dump(
        {
            "stage": "tss_signal_ready",
            "lineage_id": "tss_case",
            "research_route": "time_series_signal",
            "signal_id": "breakout",
            "input_field_map": [
                {"field": "return_5m_forward", "source_artifact": "forward_label_base/labels.parquet"},
            ],
        },
        (formal_dir / "signal_manifest.yaml").open("w", encoding="utf-8"),
        sort_keys=False,
        allow_unicode=True,
    )

    result = validate_tss_signal_ready_semantics(formal_dir, formal_dir.parents[3])

    assert not result.valid
    assert any("forward_label_base" in item for item in result.errors)


def test_tss_signal_ready_accepts_feature_base_inputs(tmp_path: Path) -> None:
    formal_dir = tmp_path / "outputs" / "tss_case" / "03_tss_signal_ready" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    yaml.safe_dump(
        {
            "stage": "tss_signal_ready",
            "lineage_id": "tss_case",
            "research_route": "time_series_signal",
            "signal_id": "breakout",
            "input_field_map": [
                {"field": "rolling_return_20", "source_artifact": "feature_base/technical.parquet"},
            ],
        },
        (formal_dir / "signal_manifest.yaml").open("w", encoding="utf-8"),
        sort_keys=False,
        allow_unicode=True,
    )

    result = validate_tss_signal_ready_semantics(formal_dir, formal_dir.parents[3])

    assert result.valid
```

Run:

```bash
python -m pytest tests/runtime/test_tss_contract_validators.py -q
```

Expected:

```text
FAILED ... ModuleNotFoundError: No module named 'runtime.tools.tss_signal_ready_contract_runtime'
```

### Task 2.4: Implement semantic validator result helpers and first validators

**Files:**
- Create: `runtime/tools/tss_signal_ready_contract_runtime.py`
- Create later in same pattern: `runtime/tools/tss_data_ready_contract_runtime.py`, `runtime/tools/tss_train_freeze_contract_runtime.py`, `runtime/tools/tss_test_evidence_contract_runtime.py`, `runtime/tools/tss_backtest_ready_contract_runtime.py`, `runtime/tools/tss_holdout_validation_contract_runtime.py`

- [ ] **Step 1: Implement `TssSemanticValidationResult` and signal validator**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TssSemanticValidationResult:
    errors: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_tss_signal_ready_semantics(author_formal_dir: Path, lineage_root: Path) -> TssSemanticValidationResult:
    del lineage_root
    errors: list[str] = []
    manifest_path = author_formal_dir / "signal_manifest.yaml"
    if not manifest_path.exists():
        return TssSemanticValidationResult(errors=["TSS-SIGNAL-SEMANTIC-001: signal_manifest.yaml is missing"])
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if payload.get("stage") != "tss_signal_ready":
        errors.append("TSS-SIGNAL-SEMANTIC-002: signal_manifest.yaml stage must be tss_signal_ready")
    if payload.get("research_route") != "time_series_signal":
        errors.append("TSS-SIGNAL-SEMANTIC-003: signal_manifest.yaml research_route must be time_series_signal")
    for item in payload.get("input_field_map", []) or []:
        source = str(item.get("source_artifact", ""))
        if "forward_label_base" in source:
            errors.append(
                "TSS-SIGNAL-SEMANTIC-004: signal inputs must not bind to forward_label_base"
            )
    return TssSemanticValidationResult(errors=errors)
```

- [ ] **Step 2: Run validator tests**

Run:

```bash
python -m pytest tests/runtime/test_tss_contract_validators.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 3: Extend validators for all stages**

Add one focused semantic check per stage before expanding:

```text
tss_data_ready: forward label timestamps must be after signal timestamps when both columns exist.
tss_train_freeze: kept_variant_ids must be a subset of candidate_variant_ids.
tss_test_evidence: selected variants must be a subset of train kept variants.
tss_backtest_ready: strategy_contract.yaml must include net_after_cost_rule.
tss_holdout_validation: holdout_run_manifest must not declare tuning_performed: true.
```

Run:

```bash
python -m pytest tests/runtime/test_tss_contract_validators.py -q
```

Expected:

```text
all tests passed
```

---

## Batch 3: Add TSS Stage Gates And Review Preflight

### Task 3.1: Add workflow stage gate tests

**Files:**
- Create: `tests/contracts/test_tss_workflow_stage_gates.py`
- Modify: `contracts/stages/workflow_stage_gates.yaml`

- [ ] **Step 1: Write RED tests for TSS stage gate presence**

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _workflow() -> dict:
    return yaml.safe_load((ROOT / "contracts" / "stages" / "workflow_stage_gates.yaml").read_text(encoding="utf-8"))


def test_tss_stages_exist_and_route_to_each_other() -> None:
    stages = _workflow()["stages"]
    assert stages["tss_data_ready"]["downstream_permissions"]["may_advance_to"] == ["tss_signal_ready"]
    assert stages["tss_signal_ready"]["allowed_previous_stages"] == ["tss_data_ready"]
    assert stages["tss_train_freeze"]["allowed_previous_stages"] == ["tss_signal_ready"]
    assert stages["tss_test_evidence"]["allowed_previous_stages"] == ["tss_train_freeze"]
    assert stages["tss_backtest_ready"]["allowed_previous_stages"] == ["tss_test_evidence"]
    assert stages["tss_holdout_validation"]["allowed_previous_stages"] == ["tss_backtest_ready"]
```

Run:

```bash
python -m pytest tests/contracts/test_tss_workflow_stage_gates.py -q
```

Expected:

```text
FAILED ... KeyError: 'tss_data_ready'
```

- [ ] **Step 2: Add TSS stages to `workflow_stage_gates.yaml`**

Create stage entries with these core questions:

```text
tss_data_ready: 是否已经形成可复现、无前视、可供信号层消费的 asset x timestamp 数据底座。
tss_signal_ready: 下游 train/test 到底消费哪个 param_id、signal field、horizon 和触发语义。
tss_train_freeze: 后续 test 应复用哪把冻结尺子，而不是边验证边调 threshold。
tss_test_evidence: 信号触发后未来路径是否比 base rate 更好，且证据不是少数事件支撑。
tss_backtest_ready: 冻结信号进入交易规则后是否仍具备成本后收益和可控风险。
tss_holdout_validation: 最终冻结方案在 holdout 中是否出现方向翻转、频率塌陷或成本后失效。
```

Run:

```bash
python -m pytest tests/contracts/test_tss_workflow_stage_gates.py -q
```

Expected:

```text
1 passed
```

### Task 3.2: Connect review preflight to TSS validators

**Files:**
- Modify: `runtime/tools/review_skillgen/context_inference.py`
- Modify: `runtime/tools/review_skillgen/render.py`
- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Modify: `runtime/tools/review_skillgen/upstream_binding_validator.py`
- Test: `tests/runtime/test_tss_contract_validators.py`

- [ ] **Step 1: Add RED test for review preflight stage support**

Add:

```python
from runtime.tools.review_skillgen.context_inference import canonical_stage_from_path_hint


def test_review_skillgen_infers_tss_stage_names() -> None:
    assert canonical_stage_from_path_hint("02_tss_data_ready") == "tss_data_ready"
    assert canonical_stage_from_path_hint("03_tss_signal_ready") == "tss_signal_ready"
    assert canonical_stage_from_path_hint("04_tss_train_freeze") == "tss_train_freeze"
```

Use the actual exported helper name in `context_inference.py`; if no helper exists, add a small exported function that wraps the existing mapping.

Run:

```bash
python -m pytest tests/runtime/test_tss_contract_validators.py::test_review_skillgen_infers_tss_stage_names -q
```

Expected:

```text
FAILED ... assertion or import error for tss stage mapping
```

- [ ] **Step 2: Add TSS mapping and validator dispatch**

Add mappings:

```python
"tss_data_ready": "tss_data_ready",
"02_tss_data_ready": "tss_data_ready",
"tss_signal_ready": "tss_signal_ready",
"03_tss_signal_ready": "tss_signal_ready",
"tss_train_freeze": "tss_train_freeze",
"04_tss_train_freeze": "tss_train_freeze",
"tss_test_evidence": "tss_test_evidence",
"05_tss_test_evidence": "tss_test_evidence",
"tss_backtest_ready": "tss_backtest_ready",
"06_tss_backtest_ready": "tss_backtest_ready",
"tss_holdout_validation": "tss_holdout_validation",
"07_tss_holdout_validation": "tss_holdout_validation",
```

In review preflight, dispatch:

```python
if stage == "tss_signal_ready":
    result = validate_tss_signal_ready_semantics(author_formal_dir, lineage_root)
```

Repeat for all TSS stages.

- [ ] **Step 3: Run focused review preflight tests**

Run:

```bash
python -m pytest tests/runtime/test_tss_contract_validators.py tests/session/test_review_entry_preflight_scope.py -q
```

Expected:

```text
all tests passed
```

---

## Batch 4: Migrate Research Session Routing To TSS

### Task 4.1: Add routing tests

**Files:**
- Create: `tests/session/test_tss_research_session_routing.py`
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/scripts/run_research_session.py`

- [ ] **Step 1: Write RED test for time_series route**

```python
from pathlib import Path

import yaml

from tests.helpers.lineage_program_support import write_fake_stage_provenance
from runtime.tools.research_session import detect_session_stage, run_research_session


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_tss_mandate_review_complete(lineage_root: Path) -> None:
    formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    _write_yaml(
        formal_dir / "research_route.yaml",
        {"research_route": "time_series_signal", "excluded_routes": ["cross_sectional_factor"]},
    )
    closure_dir = lineage_root / "01_mandate" / "review" / "closure"
    closure_dir.mkdir(parents=True)
    _write_yaml(closure_dir / "stage_completion_certificate.yaml", {"stage_status": "PASS", "final_verdict": "PASS"})
    (closure_dir / "latest_review_pack.yaml").write_text("status: ok\n", encoding="utf-8")
    (closure_dir / "stage_gate_review.yaml").write_text("status: ok\n", encoding="utf-8")
    write_fake_stage_provenance(lineage_root, "mandate")


def test_time_series_route_uses_tss_next_stage_after_mandate_review(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_mandate_review_complete(lineage_root)

    status = run_research_session(outputs_root=tmp_path / "outputs", lineage_id="tss_case")

    assert status.current_route == "time_series_signal"
    assert status.current_stage == "mandate_next_stage_confirmation_pending"
    assert not (lineage_root / "02_data_ready").exists()
    assert not (lineage_root / "02_tss_data_ready").exists()
```

Add a second test that writes next-stage confirmation and expects `02_tss_data_ready`:

```python
def test_time_series_route_scaffolds_tss_data_ready_after_next_stage_confirmation(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_mandate_review_complete(lineage_root)
    _write_yaml(
        lineage_root / "01_mandate" / "author" / "draft" / "next_stage_transition_approval.yaml",
        {
            "lineage_id": "tss_case",
            "stage_id": "mandate",
            "decision": "CONFIRM_NEXT_STAGE",
            "approved_by": "tester",
            "approved_at": "2026-04-28T10:00:00Z",
            "source_stage": "mandate_next_stage_confirmation_pending",
        },
    )

    status = run_research_session(outputs_root=tmp_path / "outputs", lineage_id="tss_case")

    assert status.current_stage in {"tss_data_ready_confirmation_pending", "tss_data_ready_author"}
    assert (lineage_root / "02_tss_data_ready" / "author" / "draft" / "tss_data_ready_freeze_draft.yaml").exists()
    assert not (lineage_root / "02_data_ready").exists()
```

Run:

```bash
python -m pytest tests/session/test_tss_research_session_routing.py -q
```

Expected:

```text
FAILED ... current_stage is data_ready_confirmation_pending or 02_data_ready exists
```

### Task 4.2: Update session route map

**Files:**
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/scripts/run_research_session.py`
- Modify: `runtime/tools/progress_runtime.py`
- Modify: `runtime/tools/research_session_reflection.py`

- [ ] **Step 1: Replace time-series stage constants with TSS names**

Use these canonical stage states:

```text
tss_data_ready_confirmation_pending
tss_data_ready_author
tss_data_ready_review_confirmation_pending
tss_signal_ready_confirmation_pending
tss_signal_ready_author
tss_signal_ready_review_confirmation_pending
tss_train_freeze_confirmation_pending
tss_train_freeze_author
tss_train_freeze_review_confirmation_pending
tss_test_evidence_confirmation_pending
tss_test_evidence_author
tss_test_evidence_review_confirmation_pending
tss_backtest_ready_confirmation_pending
tss_backtest_ready_author
tss_backtest_ready_review_confirmation_pending
tss_holdout_validation_confirmation_pending
tss_holdout_validation_author
tss_holdout_validation_review_confirmation_pending
```

Route `research_route == "time_series_signal"` to `scaffold_tss_data_ready()` after mandate next-stage confirmation.

- [ ] **Step 2: Run routing tests**

Run:

```bash
python -m pytest tests/session/test_tss_research_session_routing.py tests/session/test_csf_research_session_routing.py -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 3: Run smoke because canonical session routing changed**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected:

```text
all smoke tests passed
```

Run full-smoke if anti-drift or canonical session naming snapshots fail or are updated:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected:

```text
all full-smoke tests passed
```

---

## Batch 5: Add TSS Skills And User-Facing Docs

### Task 5.1: Add skill existence tests

**Files:**
- Create: `tests/skills/test_tss_author_review_skills.py`

- [ ] **Step 1: Write RED tests for TSS skills**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


EXPECTED_SKILLS = [
    "skills/tss_data_ready/qros-tss-data-ready-author/SKILL.md",
    "skills/tss_data_ready/qros-tss-data-ready-review/SKILL.md",
    "skills/tss_signal_ready/qros-tss-signal-ready-author/SKILL.md",
    "skills/tss_signal_ready/qros-tss-signal-ready-review/SKILL.md",
    "skills/tss_train_freeze/qros-tss-train-freeze-author/SKILL.md",
    "skills/tss_train_freeze/qros-tss-train-freeze-review/SKILL.md",
    "skills/tss_test_evidence/qros-tss-test-evidence-author/SKILL.md",
    "skills/tss_test_evidence/qros-tss-test-evidence-review/SKILL.md",
    "skills/tss_backtest_ready/qros-tss-backtest-ready-author/SKILL.md",
    "skills/tss_backtest_ready/qros-tss-backtest-ready-review/SKILL.md",
    "skills/tss_holdout_validation/qros-tss-holdout-validation-author/SKILL.md",
    "skills/tss_holdout_validation/qros-tss-holdout-validation-review/SKILL.md",
]


def test_tss_skills_exist_and_use_tss_stage_names() -> None:
    for relpath in EXPECTED_SKILLS:
        path = ROOT / relpath
        assert path.exists(), f"{relpath} missing"
        content = path.read_text(encoding="utf-8")
        stage_name = relpath.split("/")[1]
        assert stage_name in content
        assert "qros-validate-stage --stage " + stage_name in content or "-review" in relpath
```

Run:

```bash
python -m pytest tests/skills/test_tss_author_review_skills.py -q
```

Expected:

```text
FAILED ... qros-tss-data-ready-author/SKILL.md missing
```

### Task 5.2: Create TSS author/review skills

**Files:**
- Create the 12 `skills/tss_*/qros-tss-*-author|review/SKILL.md` files.
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `skills/core/using-qros/SKILL.md`

- [ ] **Step 1: Copy CSF skill structure and rewrite semantics**

Each author skill must contain:

```text
Artifact Contract Truth
Required Inputs
Required Outputs
Freeze Groups
Mandatory Discipline
Gate Discipline
Working Rules
```

Each review skill must contain:

```text
共享审查协议
独立 reviewer 子代理要求
共用输入
必需输入
必需输出
正式门禁
审查清单
Rollback 规则
下游权限
执行顺序
```

The TSS author skills must explicitly state:

```text
只能消费 research_route = time_series_signal 的上游产物。
不得产出或消费 csf_* 横截面因子产物。
不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。
```

- [ ] **Step 2: Update `qros-research-session` skill**

Replace time-series mainline text with:

```text
When research_route = time_series_signal, use the TSS branch:
- tss_data_ready_confirmation_pending
- tss_data_ready
- tss_data_ready review
...
```

The confirmation questions must be:

```text
是否按以上内容冻结 tss_data_ready？
是否按以上内容冻结 tss_signal_ready？
是否按以上内容冻结 tss_train_freeze？
是否按以上内容冻结 tss_test_evidence？
是否按以上内容冻结 tss_backtest_ready？
是否按以上内容冻结 tss_holdout_validation？
```

- [ ] **Step 3: Run skill tests**

Run:

```bash
python -m pytest tests/skills/test_tss_author_review_skills.py tests/session/test_research_session_assets.py -q
```

Expected:

```text
all tests passed
```

### Task 5.3: Update SOP docs

**Files:**
- Modify: `docs/sop/main-flow/research_workflow_sop.md`
- Create six `docs/sop/main-flow/0*_tss_*_sop_cn.md` files.
- Create: `tests/docs/test_tss_route_docs.py`

- [ ] **Step 1: Write docs test**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_research_workflow_sop_uses_tss_route_names() -> None:
    content = (ROOT / "docs" / "sop" / "main-flow" / "research_workflow_sop.md").read_text(encoding="utf-8")
    assert "02_tss_data_ready" in content
    assert "03_tss_signal_ready" in content
    assert "02_data_ready → 03_signal_ready" not in content


def test_tss_stage_sops_exist() -> None:
    for name in [
        "02_tss_data_ready_sop_cn.md",
        "03_tss_signal_ready_sop_cn.md",
        "04_tss_train_freeze_sop_cn.md",
        "05_tss_test_evidence_sop_cn.md",
        "06_tss_backtest_ready_sop_cn.md",
        "07_tss_holdout_validation_sop_cn.md",
    ]:
        path = ROOT / "docs" / "sop" / "main-flow" / name
        assert path.exists(), f"{name} missing"
        assert "time_series_signal" in path.read_text(encoding="utf-8")
```

Run:

```bash
python -m pytest tests/docs/test_tss_route_docs.py -q
```

Expected:

```text
FAILED ... 02_tss_data_ready_sop_cn.md missing
```

- [ ] **Step 2: Update docs and run tests**

Run:

```bash
python -m pytest tests/docs/test_tss_route_docs.py tests/docs/test_install_docs.py -q
```

Expected:

```text
all tests passed
```

---

## Batch 6: Add `$qros-signal-diagnostics`

### Task 6.1: Add diagnostics contract tests

**Files:**
- Create: `tests/contracts/test_tss_diagnostic_contracts.py`
- Create: `contracts/diagnostics/tss_metric_library.yaml`
- Create: `contracts/diagnostics/tss_stage_diagnostic_profiles.yaml`

- [ ] **Step 1: Write RED tests**

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_tss_metric_library_exists_and_has_core_metrics() -> None:
    path = ROOT / "contracts" / "diagnostics" / "tss_metric_library.yaml"
    assert path.exists()
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    for key in ["mean_forward_return", "hit_rate", "base_rate_uplift", "signal_frequency", "mfe_mae"]:
        assert key in metrics


def test_tss_stage_diagnostic_profiles_cover_all_tss_stages() -> None:
    path = ROOT / "contracts" / "diagnostics" / "tss_stage_diagnostic_profiles.yaml"
    assert path.exists()
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    profiles = payload["profiles"]
    assert set(profiles) == {
        "tss_data_ready",
        "tss_signal_ready",
        "tss_train_freeze",
        "tss_test_evidence",
        "tss_backtest_ready",
        "tss_holdout_validation",
    }
```

Run:

```bash
python -m pytest tests/contracts/test_tss_diagnostic_contracts.py -q
```

Expected:

```text
FAILED ... tss_metric_library.yaml missing
```

### Task 6.2: Implement signal diagnostics runtime and skill

**Files:**
- Create: `runtime/tools/signal_diagnostics.py`
- Create: `runtime/scripts/run_signal_diagnostics.py`
- Create: `runtime/bin/qros-signal-diagnostics`
- Create: `skills/core/qros-signal-diagnostics/SKILL.md`
- Create: `tests/runtime/test_signal_diagnostics.py`
- Create: `tests/docs/test_signal_diagnostics_docs.py`

- [ ] **Step 1: Write RED runtime tests**

Test expected behavior:

```text
find latest lineage
detect tss_test_evidence stage
read signal_performance_summary.json
explain hit_rate and mean_forward_return in Chinese
never emit PASS / FAIL review verdict
```

Run:

```bash
python -m pytest tests/runtime/test_signal_diagnostics.py -q
```

Expected:

```text
FAILED ... ModuleNotFoundError: No module named 'runtime.tools.signal_diagnostics'
```

- [ ] **Step 2: Implement minimal diagnostics engine**

Runtime report shape:

```python
{
    "route": "time_series_signal",
    "stage": "tss_test_evidence",
    "lineage_id": "...",
    "summary": "...",
    "observed_metrics": [
        {
            "name": "hit_rate",
            "value": 0.56,
            "severity": "info",
            "interpretation": "命中率高于 50% 表示方向判断略优于随机基准，但还要结合 base rate 和成本后表现。",
            "strategy_link": "如果信号频率很低，命中率本身不足以说明策略可交易。"
        }
    ],
    "missing_metrics": [],
    "is_review_verdict": False
}
```

- [ ] **Step 3: Add skill usage examples**

Skill must explain user asks in Codex like:

```text
$qros-signal-diagnostics 帮我解释这条 TSS 研究线的 test evidence，重点看 hit rate、forward return 和事件数量
```

Do not document raw CLI usage as the primary user path.

- [ ] **Step 4: Run focused diagnostics tests**

Run:

```bash
python -m pytest tests/contracts/test_tss_diagnostic_contracts.py tests/runtime/test_signal_diagnostics.py tests/docs/test_signal_diagnostics_docs.py -q
```

Expected:

```text
all tests passed
```

---

## Batch 7: Cleanup Legacy Canonical References And Verify

### Task 7.1: Add anti-regression tests for legacy names

**Files:**
- Create or modify: `tests/session/test_tss_research_session_routing.py`
- Create or modify: `tests/docs/test_tss_route_docs.py`
- Create or modify: `tests/skills/test_tss_author_review_skills.py`

- [ ] **Step 1: Add tests that reject old canonical route wording**

Assertions:

```python
assert "02_data_ready -> 03_signal_ready" not in content
assert "data_ready_confirmation_pending" not in tss_route_section
assert "qros-data-ready-author" not in tss_route_section
```

Allow old names only in explicitly labeled legacy migration sections.

- [ ] **Step 2: Update old docs/skills or mark legacy**

For legacy skill files that remain, add a clear line:

```text
Legacy note: this unprefixed time-series stage is no longer the canonical route for new `time_series_signal` lineages. Use the corresponding `qros-tss-*` skill.
```

Do not leave user-facing docs that tell new users to use old unprefixed stages.

### Task 7.2: Verification

**Files:**
- All touched files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest \
  tests/contracts/test_tss_artifact_contracts.py \
  tests/contracts/test_tss_workflow_stage_gates.py \
  tests/contracts/test_tss_diagnostic_contracts.py \
  tests/runtime/test_tss_*_runtime.py \
  tests/runtime/test_tss_contract_validators.py \
  tests/runtime/test_signal_diagnostics.py \
  tests/session/test_tss_research_session_routing.py \
  tests/skills/test_tss_author_review_skills.py \
  tests/docs/test_tss_route_docs.py \
  tests/docs/test_signal_diagnostics_docs.py \
  -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 2: Run minimum docs/bootstrap checks**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 3: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected:

```text
all smoke tests passed
```

- [ ] **Step 4: Run full-smoke because canonical session stage naming changed**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected:

```text
all full-smoke tests passed
```

- [ ] **Step 5: Report final state**

Final report must include:

```text
Focused tests: <commands and results>
Smoke: <command and result>
Full-smoke: <command and result>
Not run: <any skipped command and reason>
Known migration residue: <legacy files intentionally retained>
```

---

## Self-Review Checklist

- Spec coverage: this plan covers TSS stage naming, contracts, runtime scaffolds, semantic validators, session routing, skills, docs, diagnostics and verification.
- Scope control: implementation is split into batches; Batch 1-3 create infrastructure, Batch 4 changes canonical route behavior, Batch 5-6 handle user-facing skills/docs/diagnostics, Batch 7 verifies and cleans up.
- Ambiguity removed: canonical new stage names are fixed as `tss_*`; old unprefixed post-mandate stages are not canonical for new `time_series_signal` lineages.
- Verification escalation: full-smoke is required after canonical session stage naming changes.

