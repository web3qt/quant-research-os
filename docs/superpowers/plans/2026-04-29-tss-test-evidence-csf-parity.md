# TSS Test Evidence CSF Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `tss_test_evidence` fail deterministic preflight when split, threshold, selected-variant, or upstream-binding proof is missing, matching the stronger `csf_test_evidence` discipline.

**Architecture:** Add three review-scoped proof artifacts to `05_tss_test_evidence/author/formal`, generate them in the TSS test evidence runtime builder, validate them in the TSS semantic validator, and expose them in review handoff upstream-binding scope. Keep reviewer isolation unchanged: reviewer reads only `review/request/*` and `author/formal/*`.

**Tech Stack:** Python runtime helpers, PyYAML, JSON/CSV stdlib, PyArrow parquet fixtures, QROS artifact contracts, QROS review preflight, pytest.

---

## Implementation Notes

Do not commit unless the user explicitly approves. The repository AGENTS rule overrides the generic superpowers frequent-commit guidance. When a task says "checkpoint", report the diff or stage-specific verification instead of committing.

Run implementation from:

```bash
/Users/mac08/workspace/web3qt/quant-research-os
```

## File Structure

- Modify `contracts/artifacts/tss_test_evidence_artifacts.yaml`: declare the three new proof artifacts and stronger `run_manifest` / `event_forward_return` shape.
- Modify `runtime/tools/tss_test_evidence_runtime.py`: generate proof artifacts and run contract/semantic validation before returning.
- Modify `runtime/tools/tss_test_evidence_contract_runtime.py`: validate proof artifacts, timestamps, selected rows, digest ledger, and manifest bindings.
- Modify `runtime/tools/review_skillgen/review_scope_builder.py`: classify TSS proof artifacts as upstream-binding artifacts in review handoff.
- Modify `tests/runtime/test_tss_test_evidence_runtime.py`: strengthen runtime fixture and proof artifact tests.
- Create or modify `tests/runtime/test_tss_test_evidence_semantic_validation.py`: focused semantic failure tests.
- Modify `tests/review/test_review_preflight_tss_test_evidence_contract.py`: preflight and review-scope tests.
- Modify `skills/tss_test_evidence/qros-tss-test-evidence-author/SKILL.md`: require proof artifacts and pre-review validation.
- Modify `skills/tss_test_evidence/qros-tss-test-evidence-review/SKILL.md`: require preflight and non-empty upstream-binding scope before reviewer launch.
- Modify `docs/sop/main-flow/05_tss_test_evidence_sop_cn.md`: document proof artifacts and validation flow.

## Task 1: Lock Runtime Proof Artifact Expectations

**Files:**
- Modify: `tests/runtime/test_tss_test_evidence_runtime.py`
- Test: `tests/runtime/test_tss_test_evidence_runtime.py`

- [ ] **Step 1: Replace the local TSS train fixture with a reviewed upstream fixture**

Update `_prepare_tss_train_freeze_stage()` so the runtime test has the mandate split and train closure required by the new contract.

```python
import json
from pathlib import Path

import pyarrow.parquet as pq
import yaml
```

Use this helper body:

```python
def _prepare_tss_train_freeze_stage(lineage_root: Path) -> None:
    mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    mandate_formal_dir.mkdir(parents=True)
    (mandate_formal_dir / "time_split.json").write_text(
        json.dumps(
            {
                "train": "2024-01-01/2024-01-01",
                "test": "2024-01-02/2024-01-02",
                "backtest": "2024-01-03/2024-01-03",
                "holdout": "2024-01-04/2024-01-04",
                "bar_size": "1d",
                "holding_horizons": ["1d"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    formal_dir = lineage_root / "04_tss_train_freeze" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "tss_train_freeze.yaml").write_text(
        yaml.safe_dump(
            {
                "stage": "tss_train_freeze",
                "lineage_id": lineage_root.name,
                "research_route": "time_series_signal",
                "train_window": {"source": "time_split.json::train"},
                "kept_variant_ids": ["baseline_v1"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (formal_dir / "train_threshold_ledger.csv").write_text(
        "variant_id,threshold_name,threshold_value,selection_rule\nbaseline_v1,signal_value,0.0,baseline threshold\n",
        encoding="utf-8",
    )
    (formal_dir / "train_variant_ledger.csv").write_text(
        "variant_id,status,selection_rule\nbaseline_v1,kept,baseline-only\n",
        encoding="utf-8",
    )
    (formal_dir / "train_variant_rejects.csv").write_text("variant_id,reject_reason\n", encoding="utf-8")

    closure_dir = lineage_root / "04_tss_train_freeze" / "review" / "closure"
    closure_dir.mkdir(parents=True)
    (closure_dir / "stage_completion_certificate.yaml").write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "stage": "tss_train_freeze",
                "stage_status": "PASS",
                "final_verdict": "PASS",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
```

- [ ] **Step 2: Add a failing runtime proof artifact test**

Append this test:

```python
def test_build_tss_test_evidence_writes_review_scoped_proof_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_train_freeze_stage(lineage_root)
    stage_dir = lineage_root / "05_tss_test_evidence"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml",
        _tss_test_evidence_draft(confirmed=True),
    )

    build_tss_test_evidence_from_train_freeze(lineage_root)

    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "split_threshold_attestation.yaml").exists()
    assert (formal_dir / "selected_variant_membership_proof.csv").exists()
    assert (formal_dir / "upstream_binding_digest_ledger.yaml").exists()

    attestation = yaml.safe_load((formal_dir / "split_threshold_attestation.yaml").read_text(encoding="utf-8"))
    assert attestation["stage"] == "tss_test_evidence"
    assert attestation["test_window"]["source"] == "time_split.json::test"
    assert attestation["threshold_provenance"]["no_test_window_retuning"] is True

    membership = (formal_dir / "selected_variant_membership_proof.csv").read_text(encoding="utf-8")
    assert "baseline_v1,1d,selected,kept" in membership

    digest_ledger = yaml.safe_load((formal_dir / "upstream_binding_digest_ledger.yaml").read_text(encoding="utf-8"))
    assert {item["logical_name"] for item in digest_ledger["bindings"]} >= {
        "time_split",
        "train_freeze_contract",
        "train_variant_ledger",
        "train_threshold_ledger",
        "train_freeze_review_closure",
    }

    manifest = json.loads((formal_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert "split_threshold_attestation.yaml" in manifest["stage_outputs"]
    assert "../04_tss_train_freeze/author/formal/tss_train_freeze.yaml" in manifest["input_roots"]
```

- [ ] **Step 3: Run the runtime test and confirm it fails**

Run:

```bash
python -m pytest tests/runtime/test_tss_test_evidence_runtime.py::test_build_tss_test_evidence_writes_review_scoped_proof_artifacts -q
```

Expected: FAIL because `split_threshold_attestation.yaml`, `selected_variant_membership_proof.csv`, and `upstream_binding_digest_ledger.yaml` are not generated yet.

## Task 2: Extend the Artifact Contract

**Files:**
- Modify: `contracts/artifacts/tss_test_evidence_artifacts.yaml`
- Test: `tests/runtime/test_tss_test_evidence_runtime.py`

- [ ] **Step 1: Add proof artifacts to the contract**

Insert these artifact definitions under `artifacts:`:

```yaml
  split_threshold_attestation.yaml:
    type: yaml
    unknown_top_level_fields: forbid
    fields:
      - path: stage
        description: 标识该 artifact 所属的 QROS 阶段。
        type: enum
        values:
          - tss_test_evidence
      - path: lineage_id
        description: 当前研究线 ID。
        type: string
      - path: research_route
        description: 确认该产物属于 TSS 路线。
        type: enum
        values:
          - time_series_signal
      - path: train_window
        description: train window 来源与边界。
        type: map
      - path: test_window
        description: test window 来源与边界。
        type: map
      - path: label_window
        description: label timestamp 最大允许边界。
        type: map
      - path: threshold_provenance
        description: train threshold 复用证明。
        type: map

  selected_variant_membership_proof.csv:
    type: csv
    required_columns:
      - variant_id
      - horizon
      - status
      - train_kept_status
      - threshold_source
      - membership_verdict
    non_empty: true

  upstream_binding_digest_ledger.yaml:
    type: yaml
    unknown_top_level_fields: forbid
    fields:
      - path: stage
        description: 标识该 artifact 所属的 QROS 阶段。
        type: enum
        values:
          - tss_test_evidence
      - path: lineage_id
        description: 当前研究线 ID。
        type: string
      - path: bindings
        description: 上游冻结产物 digest 绑定。
        type: list[map]
```

- [ ] **Step 2: Strengthen `event_forward_return.parquet` required columns**

Ensure the column list is:

```yaml
  event_forward_return.parquet:
    type: parquet
    required_columns:
      - variant_id
      - horizon
      - asset
      - timestamp
      - forward_return
      - asset_forward_return
      - signal_direction
      - label_timestamp
    non_empty: true
```

- [ ] **Step 3: Extend `run_manifest.json` fields**

Add these field specs while preserving existing fields:

```yaml
      - path: input_roots
        description: 列出本阶段绑定的上游输入路径。
        type: list[string]
      - path: stage_outputs
        description: 列出本阶段正式输出文件。
        type: list[string]
      - path: program_dir
        description: 记录 lineage-local stage program 目录。
        type: string
      - path: program_entrypoint
        description: 记录 stage program 入口。
        type: string
      - path: program_execution_manifest
        description: 记录程序执行清单。
        type: string
      - path: selected_variant_ids
        description: 冻结进入下游的 selected variants。
        type: list[string]
      - path: selection_rule
        description: 记录 selected variants 的选择规则。
        type: string
      - path: primary_evidence_contract
        description: 声明本阶段主证据合同。
        type: string
```

- [ ] **Step 4: Run the same runtime test**

Run:

```bash
python -m pytest tests/runtime/test_tss_test_evidence_runtime.py::test_build_tss_test_evidence_writes_review_scoped_proof_artifacts -q
```

Expected: still FAIL because runtime generation is not implemented.

## Task 3: Generate Proof Artifacts in the Runtime Builder

**Files:**
- Modify: `runtime/tools/tss_test_evidence_runtime.py`
- Test: `tests/runtime/test_tss_test_evidence_runtime.py`

- [ ] **Step 1: Add imports and constants**

Add imports:

```python
import hashlib
from datetime import datetime, time, timezone
```

Add constants near `TSS_TEST_EVIDENCE_GROUP_ORDER`:

```python
TSS_TEST_EVIDENCE_STAGE_OUTPUTS = [
    "event_forward_return.parquet",
    "signal_performance_summary.json",
    "tss_test_gate_table.csv",
    "tss_selected_variants_test.csv",
    "split_threshold_attestation.yaml",
    "selected_variant_membership_proof.csv",
    "upstream_binding_digest_ledger.yaml",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
]

TSS_TEST_REQUIRED_INPUT_ROOTS = [
    "../01_mandate/author/formal/time_split.json",
    "../04_tss_train_freeze/author/formal/tss_train_freeze.yaml",
    "../04_tss_train_freeze/author/formal/train_variant_ledger.csv",
    "../04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
    "../04_tss_train_freeze/review/closure/stage_completion_certificate.yaml",
    "author/draft/tss_test_evidence_freeze_draft.yaml",
]
```

- [ ] **Step 2: Require upstream files in `build_tss_test_evidence_from_train_freeze()`**

Extend the `missing` check to include:

```python
mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
train_closure_dir = lineage_root / "04_tss_train_freeze" / "review" / "closure"
required_paths = [
    mandate_formal_dir / "time_split.json",
    upstream_formal_dir / "tss_train_freeze.yaml",
    upstream_formal_dir / "train_threshold_ledger.csv",
    upstream_formal_dir / "train_variant_ledger.csv",
    upstream_formal_dir / "train_variant_rejects.csv",
    train_closure_dir / "stage_completion_certificate.yaml",
]
missing_paths = [str(path.relative_to(lineage_root)) for path in required_paths if not path.exists()]
if missing_paths:
    raise ValueError(
        "tss upstream artifacts missing before tss_test_evidence build: " + ", ".join(missing_paths)
    )
```

- [ ] **Step 3: Add helper functions**

Append these helpers near the existing private helpers:

```python
def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path.name}: json read failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name}: expected json map")
    return payload


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_window(value: Any) -> tuple[str, str]:
    if isinstance(value, dict):
        start = str(value.get("start", "")).strip()
        end = str(value.get("end", "")).strip()
    else:
        parts = str(value).split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"time split value must be start/end, got {value!r}")
        start, end = parts[0].strip(), parts[1].strip()
    return _normalize_window_start(start), _normalize_window_end(end)


def _normalize_window_start(value: str) -> str:
    if "T" in value:
        return value.replace("Z", "+00:00")
    return datetime.combine(datetime.fromisoformat(value).date(), time.min, tzinfo=timezone.utc).isoformat()


def _normalize_window_end(value: str) -> str:
    if "T" in value:
        return value.replace("Z", "+00:00")
    return datetime.combine(datetime.fromisoformat(value).date(), time.max, tzinfo=timezone.utc).isoformat()
```

- [ ] **Step 4: Generate event rows with the new required columns**

Replace the event row payload with:

```python
{
    "variant_id": variant_id,
    "asset": "BTCUSDT",
    "timestamp": "2024-01-02T00:00:00+00:00",
    "horizon": "1d",
    "forward_return": 0.01,
    "asset_forward_return": 0.01,
    "signal_direction": 1.0,
    "label_timestamp": "2024-01-02T23:59:59+00:00",
}
```

- [ ] **Step 5: Write proof artifacts**

After selected CSV generation, write:

```python
time_split = _load_json(mandate_formal_dir / "time_split.json")
train_start, train_end = _parse_window(time_split["train"])
test_start, test_end = _parse_window(time_split["test"])
train_rows = _read_csv_rows(upstream_formal_dir / "train_variant_ledger.csv")
kept_ids = {row["variant_id"] for row in train_rows if row.get("status") == "kept"}

_dump_yaml(
    formal_dir / "split_threshold_attestation.yaml",
    {
        "stage": "tss_test_evidence",
        "lineage_id": lineage_root.name,
        "research_route": "time_series_signal",
        "train_window": {"source": "time_split.json::train", "start": train_start, "end": train_end},
        "test_window": {"source": "time_split.json::test", "start": test_start, "end": test_end},
        "label_window": {"max_label_timestamp": test_end},
        "threshold_provenance": {
            "source_stage": "tss_train_freeze",
            "threshold_artifact": "04_tss_train_freeze/author/formal/tss_train_freeze.yaml",
            "threshold_ledger": "04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
            "no_test_window_retuning": True,
        },
    },
)

_write_csv_rows(
    formal_dir / "selected_variant_membership_proof.csv",
    [
        {
            "variant_id": variant_id,
            "horizon": "1d",
            "status": "selected",
            "train_kept_status": "kept" if variant_id in kept_ids else "missing",
            "threshold_source": "04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
            "membership_verdict": "pass" if variant_id in kept_ids else "fail",
        }
        for variant_id in selected_variant_ids
    ],
    ["variant_id", "horizon", "status", "train_kept_status", "threshold_source", "membership_verdict"],
)

binding_paths = [
    ("time_split", mandate_formal_dir / "time_split.json"),
    ("train_freeze_contract", upstream_formal_dir / "tss_train_freeze.yaml"),
    ("train_variant_ledger", upstream_formal_dir / "train_variant_ledger.csv"),
    ("train_threshold_ledger", upstream_formal_dir / "train_threshold_ledger.csv"),
    ("train_freeze_review_closure", train_closure_dir / "stage_completion_certificate.yaml"),
]
_dump_yaml(
    formal_dir / "upstream_binding_digest_ledger.yaml",
    {
        "stage": "tss_test_evidence",
        "lineage_id": lineage_root.name,
        "bindings": [
            {
                "logical_name": logical_name,
                "path": str(path.relative_to(lineage_root)),
                "required": True,
                "digest": _sha256_file(path),
            }
            for logical_name, path in binding_paths
        ],
    },
)
```

- [ ] **Step 6: Expand `run_manifest.json`**

Replace the manifest payload with:

```python
{
    "stage": "tss_test_evidence",
    "lineage_id": lineage_root.name,
    "research_route": "time_series_signal",
    "source_stage": "tss_train_freeze",
    "primary_key": ["variant_id", "horizon"],
    "machine_artifacts": TSS_TEST_EVIDENCE_STAGE_OUTPUTS,
    "input_roots": TSS_TEST_REQUIRED_INPUT_ROOTS,
    "stage_outputs": TSS_TEST_EVIDENCE_STAGE_OUTPUTS,
    "program_dir": "program/time_series_signal/tss_test_evidence",
    "program_entrypoint": "run_stage.py",
    "program_execution_manifest": "program_execution_manifest.json",
    "selected_variant_ids": selected_variant_ids,
    "selection_rule": str(variant_contract.get("selection_rule", "")).strip() or "Admit only train-kept variants.",
    "primary_evidence_contract": primary_evidence_contract,
    "consumer_stage": delivery_contract.get("consumer_stage", "tss_backtest_ready"),
    "replay_command": "python -m runtime.tools.tss_test_evidence_runtime",
}
```

- [ ] **Step 7: Run contract and semantic validation before returning**

Add imports at the top:

```python
from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.tss_test_evidence_contract_runtime import validate_tss_test_evidence_semantics
```

Before `return stage_dir`, add:

```python
shape_result = validate_stage_artifacts(formal_dir, load_artifact_contract("tss_test_evidence"))
semantic_result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)
errors = [*shape_result.errors, *semantic_result.errors]
if errors:
    raise ValueError("tss_test_evidence formal artifacts do not match contract: " + "; ".join(errors))
```

- [ ] **Step 8: Run runtime tests**

Run:

```bash
python -m pytest tests/runtime/test_tss_test_evidence_runtime.py -q
```

Expected: PASS after Task 2 and Task 3 are complete.

## Task 4: Harden the TSS Semantic Validator

**Files:**
- Modify: `runtime/tools/tss_test_evidence_contract_runtime.py`
- Create: `tests/runtime/test_tss_test_evidence_semantic_validation.py`
- Test: `tests/runtime/test_tss_test_evidence_semantic_validation.py`

- [ ] **Step 1: Create semantic validation tests**

Create `tests/runtime/test_tss_test_evidence_semantic_validation.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.tss_test_evidence_contract_runtime import validate_tss_test_evidence_semantics
from runtime.tools.tss_test_evidence_runtime import build_tss_test_evidence_from_train_freeze
from tests.runtime.test_tss_test_evidence_runtime import (
    _prepare_tss_train_freeze_stage,
    _tss_test_evidence_draft,
    _write_yaml,
)


def _prepare_valid_tss_test_evidence(lineage_root: Path) -> Path:
    _prepare_tss_train_freeze_stage(lineage_root)
    stage_dir = lineage_root / "05_tss_test_evidence"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml",
        _tss_test_evidence_draft(confirmed=True),
    )
    build_tss_test_evidence_from_train_freeze(lineage_root)
    return stage_dir / "author" / "formal"


def _write_event_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def test_tss_test_evidence_semantics_rejects_missing_membership_proof_row(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = _prepare_valid_tss_test_evidence(lineage_root)
    (formal_dir / "selected_variant_membership_proof.csv").write_text(
        "variant_id,horizon,status,train_kept_status,threshold_source,membership_verdict\n",
        encoding="utf-8",
    )

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert "selected_variant_membership_proof.csv: missing selected rows [('baseline_v1', '1d')]" in result.errors


def test_tss_test_evidence_semantics_rejects_stale_digest_ledger(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = _prepare_valid_tss_test_evidence(lineage_root)
    (lineage_root / "04_tss_train_freeze" / "author" / "formal" / "train_variant_ledger.csv").write_text(
        "variant_id,status,selection_rule\nbaseline_v1,kept,changed-after-ledger\n",
        encoding="utf-8",
    )

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any("upstream_binding_digest_ledger.yaml: digest mismatch for train_variant_ledger" in error for error in result.errors)


def test_tss_test_evidence_semantics_rejects_event_timestamp_outside_test_window(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = _prepare_valid_tss_test_evidence(lineage_root)
    _write_event_rows(
        formal_dir / "event_forward_return.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "horizon": "1d",
                "asset": "BTCUSDT",
                "timestamp": "2024-01-03T00:00:00+00:00",
                "forward_return": 0.01,
                "asset_forward_return": 0.01,
                "signal_direction": 1.0,
                "label_timestamp": "2024-01-03T23:59:59+00:00",
            }
        ],
    )

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any("event_forward_return.parquet: timestamp outside test_window" in error for error in result.errors)


def test_tss_test_evidence_semantics_rejects_label_not_after_timestamp(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = _prepare_valid_tss_test_evidence(lineage_root)
    _write_event_rows(
        formal_dir / "event_forward_return.parquet",
        [
            {
                "variant_id": "baseline_v1",
                "horizon": "1d",
                "asset": "BTCUSDT",
                "timestamp": "2024-01-02T00:00:00+00:00",
                "forward_return": 0.01,
                "asset_forward_return": 0.01,
                "signal_direction": 1.0,
                "label_timestamp": "2024-01-01T23:59:59+00:00",
            }
        ],
    )

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert any("event_forward_return.parquet: label_timestamp must be after timestamp" in error for error in result.errors)


def test_tss_test_evidence_semantics_rejects_run_manifest_missing_upstream_binding(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    formal_dir = _prepare_valid_tss_test_evidence(lineage_root)
    manifest = json.loads((formal_dir / "run_manifest.json").read_text(encoding="utf-8"))
    manifest["input_roots"] = []
    (formal_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)

    assert "run_manifest.json: input_roots must bind to ../04_tss_train_freeze/author/formal/tss_train_freeze.yaml" in result.errors
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
python -m pytest tests/runtime/test_tss_test_evidence_semantic_validation.py -q
```

Expected: FAIL until validator hardening is implemented.

- [ ] **Step 3: Replace `runtime/tools/tss_test_evidence_contract_runtime.py` with a full validator**

Keep the existing public function name:

```python
def validate_tss_test_evidence_semantics(
    stage_formal_dir: Path,
    lineage_root: Path | None = None,
) -> ArtifactValidationResult:
```

Implement these checks in small helpers:

```python
REQUIRED_INPUT_ROOTS = {
    "../01_mandate/author/formal/time_split.json",
    "../04_tss_train_freeze/author/formal/tss_train_freeze.yaml",
    "../04_tss_train_freeze/author/formal/train_variant_ledger.csv",
    "../04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
    "../04_tss_train_freeze/review/closure/stage_completion_certificate.yaml",
}

REQUIRED_STAGE_OUTPUTS = {
    "event_forward_return.parquet",
    "signal_performance_summary.json",
    "tss_test_gate_table.csv",
    "tss_selected_variants_test.csv",
    "split_threshold_attestation.yaml",
    "selected_variant_membership_proof.csv",
    "upstream_binding_digest_ledger.yaml",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
}
```

The validator must:

```python
selected_rows = _read_csv_rows(stage_formal_dir / "tss_selected_variants_test.csv", errors)
selected_keys = _csv_selected_keys(selected_rows)
train_kept_ids = _read_train_kept_variant_ids(lineage_root, errors)
errors.extend(_validate_selected_variants(selected_keys, train_kept_ids))
errors.extend(_validate_membership_proof(stage_formal_dir / "selected_variant_membership_proof.csv", selected_keys))
errors.extend(_validate_summary(stage_formal_dir / "signal_performance_summary.json", selected_keys))
errors.extend(_validate_gate_table(stage_formal_dir / "tss_test_gate_table.csv", selected_keys))
attestation = _load_yaml_mapping(stage_formal_dir / "split_threshold_attestation.yaml", errors)
errors.extend(_validate_event_table(stage_formal_dir / "event_forward_return.parquet", selected_keys, attestation))
errors.extend(_validate_digest_ledger(stage_formal_dir / "upstream_binding_digest_ledger.yaml", lineage_root))
errors.extend(_validate_run_manifest(stage_formal_dir / "run_manifest.json"))
return ArtifactValidationResult(errors=errors)
```

Use clear error strings matching the tests in Step 1.

- [ ] **Step 4: Run semantic validation tests**

Run:

```bash
python -m pytest tests/runtime/test_tss_test_evidence_semantic_validation.py -q
```

Expected: PASS.

## Task 5: Wire Review Preflight and Review Scope

**Files:**
- Modify: `runtime/tools/review_skillgen/review_scope_builder.py`
- Modify: `tests/review/test_review_preflight_tss_test_evidence_contract.py`
- Test: `tests/review/test_review_preflight_tss_test_evidence_contract.py`

- [ ] **Step 1: Expand review preflight tests**

Replace the current one-test file with:

```python
from pathlib import Path

from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from runtime.tools.review_skillgen.review_scope_builder import build_review_scope
from runtime.tools.tss_test_evidence_runtime import build_tss_test_evidence_from_train_freeze
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.runtime.test_tss_test_evidence_runtime import (
    _prepare_tss_train_freeze_stage,
    _tss_test_evidence_draft,
    _write_yaml,
)


def _prepare_valid_tss_test_evidence_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_train_freeze_stage(lineage_root)
    ensure_stage_program(lineage_root, "tss_test_evidence")
    write_fake_stage_provenance(lineage_root, "tss_test_evidence")
    stage_dir = lineage_root / "05_tss_test_evidence"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml",
        _tss_test_evidence_draft(confirmed=True),
    )
    build_tss_test_evidence_from_train_freeze(lineage_root)
    return stage_dir


def _run_tss_test_evidence_preflight(stage_dir: Path) -> dict:
    return run_review_preflight(
        explicit_context={
            "stage": "tss_test_evidence",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": stage_dir.parent.name,
        }
    )


def test_review_preflight_tss_test_evidence_passes_runtime_built_outputs(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_tss_test_evidence_stage(tmp_path)

    payload = _run_tss_test_evidence_preflight(stage_dir)

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_tss_test_evidence_blocks_missing_proof_artifact(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_tss_test_evidence_stage(tmp_path)
    (stage_dir / "author" / "formal" / "split_threshold_attestation.yaml").unlink()

    payload = _run_tss_test_evidence_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("ARTIFACT-CONTRACT-001: split_threshold_attestation.yaml: missing required artifact" in item for item in payload["content_findings"])


def test_review_preflight_tss_test_evidence_blocks_variant_drift(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_tss_test_evidence_stage(tmp_path)
    (stage_dir / "author" / "formal" / "tss_selected_variants_test.csv").write_text(
        "variant_id,horizon,status\nleaked_variant,1d,selected\n",
        encoding="utf-8",
    )

    payload = _run_tss_test_evidence_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("TSS-TEST-SEMANTIC-001" in item for item in payload["content_findings"])


def test_tss_test_evidence_review_scope_marks_proof_artifacts_as_upstream_binding() -> None:
    scope = build_review_scope(
        stage="tss_test_evidence",
        required_artifact_paths=[
            "event_forward_return.parquet",
            "signal_performance_summary.json",
            "tss_test_gate_table.csv",
            "tss_selected_variants_test.csv",
            "split_threshold_attestation.yaml",
            "selected_variant_membership_proof.csv",
            "upstream_binding_digest_ledger.yaml",
        ],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert scope["upstream_binding_artifact_paths"] == [
        "selected_variant_membership_proof.csv",
        "split_threshold_attestation.yaml",
        "upstream_binding_digest_ledger.yaml",
    ]
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
python -m pytest tests/review/test_review_preflight_tss_test_evidence_contract.py -q
```

Expected: FAIL until review scope classification and semantic validator changes are complete.

- [ ] **Step 3: Modify `build_review_scope()`**

Add this stage-specific branch after the existing CSF branch:

```python
    if stage == "tss_test_evidence":
        upstream_binding.update(
            {
                "split_threshold_attestation.yaml",
                "selected_variant_membership_proof.csv",
                "upstream_binding_digest_ledger.yaml",
            }
        )
```

- [ ] **Step 4: Run review tests**

Run:

```bash
python -m pytest tests/review/test_review_preflight_tss_test_evidence_contract.py -q
```

Expected: PASS.

## Task 6: Update Skills and SOP

**Files:**
- Modify: `skills/tss_test_evidence/qros-tss-test-evidence-author/SKILL.md`
- Modify: `skills/tss_test_evidence/qros-tss-test-evidence-review/SKILL.md`
- Modify: `docs/sop/main-flow/05_tss_test_evidence_sop_cn.md`
- Test: `tests/helpers/tss_stage_parity.py`

- [ ] **Step 1: Add proof artifacts to author skill required outputs**

In `skills/tss_test_evidence/qros-tss-test-evidence-author/SKILL.md`, add these outputs to `Required Outputs`:

```markdown
- `split_threshold_attestation.yaml`
- `selected_variant_membership_proof.csv`
- `upstream_binding_digest_ledger.yaml`
```

Add this sentence under `Gate Discipline`:

```markdown
- 进入 review 前必须已物化 split/threshold、selected membership 和 upstream digest proof；缺少这些 proof artifacts 时不得进入 reviewer lane。
```

- [ ] **Step 2: Add preflight language to review skill**

In `skills/tss_test_evidence/qros-tss-test-evidence-review/SKILL.md`, add proof artifacts to required inputs:

```markdown
- `05_tss_test_evidence/author/formal/split_threshold_attestation.yaml`
- `05_tss_test_evidence/author/formal/selected_variant_membership_proof.csv`
- `05_tss_test_evidence/author/formal/upstream_binding_digest_ledger.yaml`
```

Add this under formal gate:

```markdown
- 进入 reviewer lane 前必须通过 deterministic preflight；`ARTIFACT-CONTRACT-001` 与 `TSS-TEST-SEMANTIC-001` 都是 review 前阻断项。
- `adversarial_review_request.yaml` 中 `upstream_binding_artifact_paths` 不得为空，且必须包含本阶段 proof artifacts。
```

- [ ] **Step 3: Update SOP required outputs and formal gate**

In `docs/sop/main-flow/05_tss_test_evidence_sop_cn.md`, add the three proof artifacts under `3. 必备输出`.

Under `4. Formal Gate`, add:

```markdown
进入 reviewer lane 前还必须通过 review preflight。缺少 split/threshold attestation、selected membership proof 或 upstream digest ledger 时，应在 preflight 阶段失败，不得交给 reviewer 作为普通 finding。
```

- [ ] **Step 4: Add doc parity assertions**

In `tests/helpers/tss_stage_parity.py`, extend the existing TSS parity checks for `tss_test_evidence` so the stage's author skill, review skill, and SOP mention:

```python
required_terms = [
    "split_threshold_attestation.yaml",
    "selected_variant_membership_proof.csv",
    "upstream_binding_digest_ledger.yaml",
    "TSS-TEST-SEMANTIC-001",
]
```

Use `skill_text(meta["author_skill"])`, `skill_text(meta["review_skill"])`, and `meta["sop_path"].read_text(encoding="utf-8")` to assert the terms for `stage == "tss_test_evidence"`.

- [ ] **Step 5: Run doc/parity tests**

Run:

```bash
python -m pytest tests/session/test_tss_test_evidence_artifact_shape.py tests/session/test_research_session_assets.py tests/review/test_review_preflight_tss_test_evidence_contract.py -q
```

Expected: PASS.

## Task 7: Focused Verification

**Files:**
- No source changes.
- Test: focused TSS test evidence and review preflight tests.

- [ ] **Step 1: Run focused runtime and review tests**

Run:

```bash
python -m pytest tests/runtime/test_tss_test_evidence_runtime.py tests/runtime/test_tss_test_evidence_semantic_validation.py tests/review/test_review_preflight_tss_test_evidence_contract.py -q
```

Expected: PASS.

- [ ] **Step 2: Run artifact contract regression tests**

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py tests/session/test_tss_test_evidence_artifact_shape.py -q
```

Expected: PASS. If failures are from minimal fixture outputs, update fixtures to include the three new proof artifacts rather than relaxing the contract.

- [ ] **Step 3: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 4: Run full-smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS. Full-smoke is required because this changes TSS stage gate semantics, review preflight, and next-stage eligibility.

## Task 8: Final Review Checklist

**Files:**
- Inspect all modified files.

- [ ] **Step 1: Check for stale references**

Run:

```bash
rg -n "tss_test_evidence|split_threshold_attestation|selected_variant_membership_proof|upstream_binding_digest_ledger|TSS-TEST-SEMANTIC" contracts runtime tests skills docs
```

Expected: references are consistent with the new artifact names and no document still lists only the old seven TSS test evidence outputs.

- [ ] **Step 2: Check diff**

Run:

```bash
git diff -- contracts/artifacts/tss_test_evidence_artifacts.yaml runtime/tools/tss_test_evidence_runtime.py runtime/tools/tss_test_evidence_contract_runtime.py runtime/tools/review_skillgen/review_scope_builder.py tests/runtime/test_tss_test_evidence_runtime.py tests/runtime/test_tss_test_evidence_semantic_validation.py tests/review/test_review_preflight_tss_test_evidence_contract.py skills/tss_test_evidence/qros-tss-test-evidence-author/SKILL.md skills/tss_test_evidence/qros-tss-test-evidence-review/SKILL.md docs/sop/main-flow/05_tss_test_evidence_sop_cn.md
```

Expected: diff is limited to the TSS test evidence parity work and does not modify CSF runtime behavior.

- [ ] **Step 3: Report verification**

Final report must include:

- Focused tests run and result.
- Smoke run and result.
- Full-smoke run and result.
- Any remaining compatibility risk for older active research repos with pre-existing `05_tss_test_evidence` outputs.
