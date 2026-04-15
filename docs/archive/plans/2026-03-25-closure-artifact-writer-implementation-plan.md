# Closure Artifact Writer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a shared closure artifact writer that stage review skills can trigger at the end of a review, writing stage-level closure artifacts plus a lineage-level latest mirror for `mandate`, `data_ready`, and `signal_ready`.

**Architecture:** Implement a shared Python module under `tools/review_skillgen/` with three responsibilities: infer review context, normalize a review payload, and write `latest_review_pack.yaml`, `stage_gate_review.yaml`, and `stage_completion_certificate.yaml` into the current stage directory while mirroring `latest_review_pack.yaml` to the lineage root. Keep the first version Codex-only and compatible with the existing generator-based review skill system.

**Tech Stack:** Python 3.11, `PyYAML`, `pytest`, existing `tools/review_skillgen/` package, existing gate/checklist docs under `docs/`

---

### Task 1: Define The Shared Closure Payload And Output Models

**Files:**
- Create: `tools/review_skillgen/closure_models.py`
- Create: `tests/test_closure_models.py`

**Step 1: Write the failing model tests**

```python
from tools.review_skillgen.closure_models import build_review_payload


def test_build_review_payload_requires_stage_and_verdict() -> None:
    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
    )
    assert payload["lineage_id"] == "topic_a"
    assert payload["stage"] == "mandate"
    assert payload["final_verdict"] == "PASS"
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_closure_models.py -v
```

Expected: FAIL with import error because the model module does not exist yet.

**Step 3: Implement the minimal payload builder**

Create `tools/review_skillgen/closure_models.py` with:

- one `ALLOWED_VERDICTS` constant derived from the current shared vocabulary
- one `build_review_payload()` helper
- minimal normalization for:
  - `lineage_id`
  - `stage`
  - `final_verdict`
  - `stage_status`
  - `blocking_findings`
  - `reservation_findings`
  - `info_findings`
  - `residual_risks`
  - `review_timestamp_utc`

Keep it minimal; plain dictionaries are fine for v1.

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_closure_models.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tools/review_skillgen/closure_models.py tests/test_closure_models.py
git commit -m "feat: add closure artifact payload models"
```

### Task 2: Implement Context Inference

**Files:**
- Create: `tools/review_skillgen/context_inference.py`
- Create: `tests/test_context_inference.py`

**Step 1: Write the failing inference tests**

```python
from pathlib import Path

from tools.review_skillgen.context_inference import infer_review_context


def test_infer_review_context_from_outputs_tree(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    stage_dir.mkdir(parents=True)

    ctx = infer_review_context(stage_dir)

    assert ctx["lineage_id"] == "topic_a"
    assert ctx["stage"] == "mandate"
    assert ctx["stage_dir"] == stage_dir
    assert ctx["lineage_root"] == tmp_path / "outputs" / "topic_a"
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_context_inference.py -v
```

Expected: FAIL with import error.

**Step 3: Implement minimal context inference**

Create `tools/review_skillgen/context_inference.py` with:

- `infer_review_context(path: Path) -> dict`
- search upward for a directory shape like `outputs/<lineage>/<stage>`
- return:
  - `lineage_id`
  - `stage`
  - `stage_dir`
  - `lineage_root`
- raise a clear `ValueError` if inference fails

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_context_inference.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tools/review_skillgen/context_inference.py tests/test_context_inference.py
git commit -m "feat: infer lineage and stage context for closure writing"
```

### Task 3: Implement Stage-Level Closure Writing

**Files:**
- Create: `tools/review_skillgen/closure_writer.py`
- Create: `tests/test_closure_writer_stage_outputs.py`

**Step 1: Write the failing writer tests**

```python
from pathlib import Path

from tools.review_skillgen.closure_models import build_review_payload
from tools.review_skillgen.closure_writer import write_closure_artifacts


def test_write_closure_artifacts_creates_stage_files(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    stage_dir.mkdir(parents=True)

    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
    )

    write_closure_artifacts(payload, explicit_context={"stage_dir": stage_dir, "lineage_root": stage_dir.parent})

    assert (stage_dir / "latest_review_pack.yaml").exists()
    assert (stage_dir / "stage_gate_review.yaml").exists()
    assert (stage_dir / "stage_completion_certificate.yaml").exists()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_closure_writer_stage_outputs.py -v
```

Expected: FAIL with import error.

**Step 3: Implement the minimal stage writer**

Create `tools/review_skillgen/closure_writer.py`:

- accept `payload`
- accept either inferred or explicit context
- write these files into `stage_dir`:
  - `latest_review_pack.yaml`
  - `stage_gate_review.yaml`
  - `stage_completion_certificate.yaml`
- use `yaml.safe_dump(..., sort_keys=False, allow_unicode=True)`

First version can map the payload into a compact schema. It does not need to fill every field from the full Chinese template yet, but it must include:

- `lineage_id`
- `stage`
- `stage_status`
- `final_verdict`
- `review_timestamp_utc`
- `blocking_findings`
- `reservation_findings`
- `rollback_stage`
- `allowed_modifications`
- `downstream_permissions`

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_closure_writer_stage_outputs.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tools/review_skillgen/closure_writer.py tests/test_closure_writer_stage_outputs.py
git commit -m "feat: write stage-level closure artifacts"
```

### Task 4: Implement Lineage-Level Latest Mirror

**Files:**
- Create: `tests/test_closure_writer_lineage_mirror.py`
- Modify: `tools/review_skillgen/closure_writer.py`

**Step 1: Write the failing lineage mirror test**

```python
from tools.review_skillgen.closure_models import build_review_payload
from tools.review_skillgen.closure_writer import write_closure_artifacts


def test_write_closure_artifacts_updates_lineage_latest_review_pack(tmp_path) -> None:
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    stage_dir.mkdir(parents=True)
    lineage_root = stage_dir.parent

    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
    )

    write_closure_artifacts(payload, explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})

    assert (lineage_root / "latest_review_pack.yaml").exists()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_closure_writer_lineage_mirror.py -v
```

Expected: FAIL because the lineage mirror does not exist yet.

**Step 3: Extend the writer**

Update `tools/review_skillgen/closure_writer.py`:

- after writing the stage-level `latest_review_pack.yaml`
- also write a lineage-level mirror at:
  - `<lineage_root>/latest_review_pack.yaml`

The lineage mirror may be identical to the stage-level review pack in v1.

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_closure_writer_lineage_mirror.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tools/review_skillgen/closure_writer.py tests/test_closure_writer_lineage_mirror.py
git commit -m "feat: mirror latest review pack at lineage root"
```

### Task 5: Add Explicit Context Fallback And Inference Failure Coverage

**Files:**
- Create: `tests/test_closure_writer_context_modes.py`
- Modify: `tools/review_skillgen/closure_writer.py`

**Step 1: Write the failing context mode tests**

```python
from pathlib import Path
import pytest

from tools.review_skillgen.closure_models import build_review_payload
from tools.review_skillgen.closure_writer import write_closure_artifacts


def test_writer_uses_explicit_context_when_inference_is_not_available(tmp_path: Path) -> None:
    stage_dir = tmp_path / "custom_stage"
    stage_dir.mkdir()
    lineage_root = tmp_path / "custom_lineage"
    lineage_root.mkdir()

    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
    )

    write_closure_artifacts(payload, explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root})
    assert (stage_dir / "stage_gate_review.yaml").exists()


def test_writer_raises_when_neither_inference_nor_explicit_context_is_available(tmp_path: Path) -> None:
    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
    )

    with pytest.raises(ValueError):
        write_closure_artifacts(payload, cwd=tmp_path)
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_closure_writer_context_modes.py -v
```

Expected: FAIL until fallback logic is implemented.

**Step 3: Implement mixed-mode behavior**

Update `tools/review_skillgen/closure_writer.py`:

- if `explicit_context` is present, use it directly
- else try `infer_review_context(cwd or Path.cwd())`
- if inference fails, raise `ValueError` with a clear message telling the caller to provide explicit args

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_closure_writer_context_modes.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tools/review_skillgen/closure_writer.py tests/test_closure_writer_context_modes.py
git commit -m "feat: support mixed context inference for closure writing"
```

### Task 6: Document The Writer Contract

**Files:**
- Create: `docs/experience/closure-artifact-writer-usage.md`
- Modify: `tests/test_project_bootstrap.py`

**Step 1: Write the failing doc existence test**

Add to `tests/test_project_bootstrap.py`:

```python
def test_closure_writer_usage_doc_exists() -> None:
    assert Path("docs/experience/closure-artifact-writer-usage.md").exists()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_project_bootstrap.py -v
```

Expected: FAIL because the new usage doc does not exist yet.

**Step 3: Write the usage doc**

Create `docs/experience/closure-artifact-writer-usage.md` covering:

- what closure artifacts are
- what files are written at stage level
- what gets mirrored at lineage root
- what the payload must contain
- how context inference works
- how explicit context fallback works

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_project_bootstrap.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add docs/experience/closure-artifact-writer-usage.md tests/test_project_bootstrap.py
git commit -m "docs: add closure artifact writer usage guide"
```

### Verification Checklist

Run these before claiming the implementation is complete:

```bash
python -m pytest tests/test_closure_models.py -v
python -m pytest tests/test_context_inference.py -v
python -m pytest tests/test_closure_writer_stage_outputs.py -v
python -m pytest tests/test_closure_writer_lineage_mirror.py -v
python -m pytest tests/test_closure_writer_context_modes.py -v
python -m pytest tests -v
git status --short
```

Expected:

- all new writer tests pass
- the existing test suite still passes
- git status only shows intentional changes

### Notes For The Implementer

- This plan still keeps the writer independent from full skill execution.
- Do not wire it into generated `SKILL.md` files yet unless the tests and base writer are stable.
- v1 schema should be compact and machine-readable, not a full expansion of every field from the human template.
- Reuse the existing verdict vocabulary; do not invent another status system.

### Execution Order Summary

1. Define payload models
2. Infer context
3. Write stage-level closure artifacts
4. Mirror lineage-level latest review pack
5. Add mixed inference/explicit context handling
6. Document usage
