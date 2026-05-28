# QROS Progress Stage Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `qros-progress` and `qros-research-session` resolve `current_stage` from the latest real materialized QROS stage instead of rewinding to stale closed upstream review requests.

**Architecture:** Keep `runtime.tools.research_session.detect_session_stage` as the single source of truth and make `progress_runtime` continue to consume it. Add a narrowly named historical advancing-closure helper for closed upstream stages, then use route-aware stage-order tests to prevent malformed legacy upstream request files from overriding later real CSF progress. Keep active/highest-stage proof-chain validation strict.

**Tech Stack:** Python 3.11+, PyYAML, pytest, existing QROS runtime modules under `runtime/tools/`.

---

## File Structure

- Modify `runtime/tools/research_session.py`
  - Owns the shared stage resolver.
  - Add `_historical_stage_advancing_closure_exists(stage_dir: Path) -> bool`.
  - Keep `_review_closure_complete(stage_dir: Path) -> bool` strict for active review interpretation.
  - Adjust the route-aware resolver so stale upstream proof-chain defects cannot pull state backward after later real materialization exists.
- Modify `tests/session/test_research_session_runtime.py`
  - Add helper fixtures for legacy malformed review request files.
  - Add shared resolver regression tests.
- Modify `tests/session/test_qros_progress_runtime.py`
  - Add progress parity coverage that uses the same CSF lineage fixture.
- Modify `docs/guides/qros-research-session-usage.md`
  - Add a short current-stage semantics note.
- Modify `docs/guides/qros-review-shared-protocol.md`
  - Add the same proof-chain boundary in review terminology.

## Task 1: Add Historical Advancing Closure Helper

**Files:**
- Modify: `runtime/tools/research_session.py`
- Test: `tests/session/test_research_session_runtime.py`

- [ ] **Step 1: Write the failing helper semantics test**

Add this test near the existing completion-certificate tests in `tests/session/test_research_session_runtime.py`:

```python
def _write_legacy_malformed_review_request(stage_dir: Path, *, stage: str) -> None:
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    _write_yaml(
        request_path,
        {
            "lineage_id": stage_dir.parent.name,
            "stage_id": stage,
            "author_identity": "legacy-author",
            "required_artifact_paths": [],
            "required_provenance_paths": ["program_execution_manifest.json"],
        },
    )


def test_historical_advancing_closure_accepts_legacy_malformed_request_for_closed_stage(
    tmp_path: Path,
) -> None:
    from runtime.tools import research_session as research_session_module

    lineage_root = tmp_path / "outputs" / "legacy_closed_case"
    mandate_dir = lineage_root / "01_mandate"
    _write_minimal_stage_outputs(mandate_dir, stage="mandate")
    _write_stage_completion_certificate(
        mandate_dir / "stage_completion_certificate.yaml",
        stage_status="PASS",
    )
    _write_legacy_malformed_review_request(mandate_dir, stage="mandate")
    write_fake_stage_provenance(lineage_root, "mandate")

    assert research_session_module._review_closure_complete(mandate_dir) is False
    assert research_session_module._historical_stage_advancing_closure_exists(mandate_dir) is True
```

- [ ] **Step 2: Run the helper test and verify it fails**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_historical_advancing_closure_accepts_legacy_malformed_request_for_closed_stage -q
```

Expected: FAIL with `AttributeError: module 'runtime.tools.research_session' has no attribute '_historical_stage_advancing_closure_exists'`.

- [ ] **Step 3: Implement the helper**

Add this helper in `runtime/tools/research_session.py` immediately after `_completion_certificate_allows_progress`:

```python
def _historical_stage_advancing_closure_exists(stage_dir: Path) -> bool:
    certificate_path = _review_closure_path(stage_dir, "stage_completion_certificate.yaml")
    if not certificate_path.exists():
        return False

    payload = _read_yaml(certificate_path)
    if not payload:
        return False

    stage_status = payload.get("stage_status") or payload.get("final_verdict")
    return stage_status in ADVANCING_COMPLETION_STATUSES
```

Do not change `_review_closure_complete` in this task.

- [ ] **Step 4: Run the helper test and verify it passes**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_historical_advancing_closure_accepts_legacy_malformed_request_for_closed_stage -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_session.py tests/session/test_research_session_runtime.py
git commit -m "test: define historical qros closure evidence"
```

## Task 2: Lock Shared Resolver And Progress Parity

**Files:**
- Modify: `tests/session/test_research_session_runtime.py`
- Modify: `tests/session/test_qros_progress_runtime.py`

- [ ] **Step 1: Add a reusable CSF fixture in the session test file**

Add these helpers in `tests/session/test_research_session_runtime.py` near `_write_minimal_stage_outputs`:

```python
def _write_csf_route_contract(mandate_dir: Path) -> None:
    _write_yaml(
        _stage_output_path(mandate_dir, "research_route.yaml"),
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "regime_filter",
            "factor_structure": "multi_factor_score",
            "portfolio_expression": "long_only_rank",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "trend_combo_v1",
            "group_taxonomy_reference": "sector_bucket_v1",
            "excluded_routes": ["time_series_signal"],
            "route_rationale": ["Cross-sectional factor route is the frozen route."],
            "route_change_policy": {
                "before_downstream_freeze": "rollback_to_mandate",
                "after_downstream_freeze": "child_lineage",
            },
            "route_contract_version": "v1",
        },
    )


def _prepare_csf_stage_pass_closed(lineage_root: Path, *, stage_dir_name: str, stage: str) -> Path:
    stage_dir = lineage_root / stage_dir_name
    _write_minimal_stage_outputs(stage_dir, stage=stage)
    if stage == "mandate":
        _write_csf_route_contract(stage_dir)
    _write_stage_completion_certificate(
        stage_dir / "stage_completion_certificate.yaml",
        stage_status="PASS",
    )
    write_fake_stage_provenance(lineage_root, stage)
    return stage_dir


def _prepare_csf_train_freeze_closed_with_legacy_upstream_request(lineage_root: Path) -> None:
    mandate_dir = _prepare_csf_stage_pass_closed(
        lineage_root,
        stage_dir_name="01_mandate",
        stage="mandate",
    )
    _write_legacy_malformed_review_request(mandate_dir, stage="mandate")
    _prepare_csf_stage_pass_closed(
        lineage_root,
        stage_dir_name="02_csf_data_ready",
        stage="csf_data_ready",
    )
    _prepare_csf_stage_pass_closed(
        lineage_root,
        stage_dir_name="03_csf_signal_ready",
        stage="csf_signal_ready",
    )
    _prepare_csf_stage_pass_closed(
        lineage_root,
        stage_dir_name="04_csf_train_freeze",
        stage="csf_train_freeze",
    )
```

- [ ] **Step 2: Add the shared resolver regression tests**

Add these tests near the existing `detect_session_stage` completion-certificate tests:

```python
def test_detect_session_stage_uses_latest_csf_closed_stage_over_legacy_upstream_request(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "csf_legacy_upstream_case"
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request(lineage_root)

    assert detect_session_stage(lineage_root) == "csf_train_freeze_next_stage_confirmation_pending"


def test_detect_session_stage_enters_csf_test_evidence_after_train_next_stage_confirmation(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "csf_legacy_upstream_case"
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request(lineage_root)
    _write_next_stage_confirmation(
        lineage_root / "04_csf_train_freeze",
        stage="csf_train_freeze",
    )

    assert detect_session_stage(lineage_root) == "csf_test_evidence_confirmation_pending"


def test_detect_session_stage_keeps_highest_malformed_review_request_strict(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "highest_malformed_case"
    _prepare_csf_stage_pass_closed(
        lineage_root,
        stage_dir_name="01_mandate",
        stage="mandate",
    )
    stage_dir = lineage_root / "02_csf_data_ready"
    _write_minimal_stage_outputs(stage_dir, stage="csf_data_ready")
    _write_stage_completion_certificate(
        stage_dir / "stage_completion_certificate.yaml",
        stage_status="PASS",
    )
    _write_legacy_malformed_review_request(stage_dir, stage="csf_data_ready")
    write_fake_stage_provenance(lineage_root, "csf_data_ready")

    assert detect_session_stage(lineage_root) == "csf_data_ready_review"
```

- [ ] **Step 3: Add progress parity test**

Update the import list in `tests/session/test_qros_progress_runtime.py`:

```python
from tests.session.test_research_session_runtime import (
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request,
    _review_request_payload,
    _write_adversarial_review_request,
    _write_minimal_stage_outputs,
    _write_next_stage_confirmation,
    _write_reviewer_receipt,
    _write_yaml,
)
```

Add this test near the existing progress handoff tests:

```python
def test_progress_reports_latest_csf_closed_stage_over_legacy_upstream_request(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_legacy_upstream_case"
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request(lineage_root)

    payload = progress_status_payload(
        outputs_root=outputs_root,
        lineage_id=lineage_root.name,
    )

    assert payload["current_stage"] == "csf_train_freeze_next_stage_confirmation_pending"
    assert payload["current_skill"] == "qros-research-session"
    assert payload["recommended_skill"] == "qros-research-session"


def test_progress_reports_csf_test_evidence_after_train_next_stage_confirmation(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_legacy_upstream_case"
    _prepare_csf_train_freeze_closed_with_legacy_upstream_request(lineage_root)
    _write_next_stage_confirmation(
        lineage_root / "04_csf_train_freeze",
        stage="csf_train_freeze",
    )

    payload = progress_status_payload(
        outputs_root=outputs_root,
        lineage_id=lineage_root.name,
    )

    assert payload["current_stage"] == "csf_test_evidence_confirmation_pending"
    assert payload["current_skill"] == "qros-research-session"
```

- [ ] **Step 4: Run the new resolver tests and capture current behavior**

Run:

```bash
python -m pytest \
  tests/session/test_research_session_runtime.py::test_detect_session_stage_uses_latest_csf_closed_stage_over_legacy_upstream_request \
  tests/session/test_research_session_runtime.py::test_detect_session_stage_enters_csf_test_evidence_after_train_next_stage_confirmation \
  tests/session/test_research_session_runtime.py::test_detect_session_stage_keeps_highest_malformed_review_request_strict \
  tests/session/test_qros_progress_runtime.py::test_progress_reports_latest_csf_closed_stage_over_legacy_upstream_request \
  tests/session/test_qros_progress_runtime.py::test_progress_reports_csf_test_evidence_after_train_next_stage_confirmation \
  -q
```

Expected before implementation on the affected runtime: FAIL by reporting an older review state or by treating highest-stage malformed closure as completed. Record the observed stdout/stderr. Do not commit after this step; Task 3 commits the tests with the implementation.

## Task 3: Refine Shared Stage Resolution

**Files:**
- Modify: `runtime/tools/research_session.py`
- Test: `tests/session/test_research_session_runtime.py`
- Test: `tests/session/test_qros_progress_runtime.py`

- [ ] **Step 1: Add a route-stage candidate type**

Add imports near the existing imports in `runtime/tools/research_session.py`:

```python
from collections.abc import Callable
```

Add this dataclass near `FailurePackageRuntimeStatus`:

```python
@dataclass(frozen=True)
class StageResolutionCandidate:
    stage_base: str
    stage_dir: Path
    outputs_complete: Callable[[Path], bool]
    closure_complete: Callable[[Path], bool]
```

- [ ] **Step 2: Add route candidate builders**

Add these helpers before `detect_session_stage`. The candidate order is forward workflow order because the downstream-materialization check asks whether a later stage already exists.

```python
def _mainline_stage_resolution_candidates(lineage_root: Path) -> list[StageResolutionCandidate]:
    return [
        StageResolutionCandidate(
            "mandate",
            lineage_root / "01_mandate",
            _mandate_outputs_complete,
            _mandate_closure_complete,
        ),
        StageResolutionCandidate(
            "data_ready",
            lineage_root / "02_data_ready",
            _data_ready_outputs_complete,
            _data_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "signal_ready",
            lineage_root / "03_signal_ready",
            _signal_ready_outputs_complete,
            _signal_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "train_freeze",
            lineage_root / "04_train_freeze",
            _train_freeze_outputs_complete,
            _train_freeze_closure_complete,
        ),
        StageResolutionCandidate(
            "test_evidence",
            lineage_root / "05_test_evidence",
            _test_evidence_outputs_complete,
            _test_evidence_closure_complete,
        ),
        StageResolutionCandidate(
            "backtest_ready",
            lineage_root / "06_backtest",
            _backtest_ready_outputs_complete,
            _backtest_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "holdout_validation",
            lineage_root / "07_holdout",
            _holdout_validation_outputs_complete,
            _holdout_validation_closure_complete,
        ),
    ]


def _csf_stage_resolution_candidates(lineage_root: Path) -> list[StageResolutionCandidate]:
    return [
        StageResolutionCandidate(
            "mandate",
            lineage_root / "01_mandate",
            _mandate_outputs_complete,
            _mandate_closure_complete,
        ),
        StageResolutionCandidate(
            "csf_data_ready",
            lineage_root / "02_csf_data_ready",
            _csf_data_ready_outputs_complete,
            _csf_data_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "csf_signal_ready",
            lineage_root / "03_csf_signal_ready",
            _csf_signal_ready_outputs_complete,
            _csf_signal_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "csf_train_freeze",
            lineage_root / "04_csf_train_freeze",
            _csf_train_freeze_outputs_complete,
            _csf_train_freeze_closure_complete,
        ),
        StageResolutionCandidate(
            "csf_test_evidence",
            lineage_root / "05_csf_test_evidence",
            _csf_test_evidence_outputs_complete,
            _csf_test_evidence_closure_complete,
        ),
        StageResolutionCandidate(
            "csf_backtest_ready",
            lineage_root / "06_csf_backtest_ready",
            _csf_backtest_ready_outputs_complete,
            _csf_backtest_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "csf_holdout_validation",
            lineage_root / "07_csf_holdout_validation",
            _csf_holdout_validation_outputs_complete,
            _csf_holdout_validation_closure_complete,
        ),
    ]


def _tss_stage_resolution_candidates(lineage_root: Path) -> list[StageResolutionCandidate]:
    return [
        StageResolutionCandidate(
            "mandate",
            lineage_root / "01_mandate",
            _mandate_outputs_complete,
            _mandate_closure_complete,
        ),
        StageResolutionCandidate(
            "tss_data_ready",
            lineage_root / "02_tss_data_ready",
            _tss_data_ready_outputs_complete,
            _tss_data_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "tss_signal_ready",
            lineage_root / "03_tss_signal_ready",
            _tss_signal_ready_outputs_complete,
            _tss_signal_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "tss_train_freeze",
            lineage_root / "04_tss_train_freeze",
            _tss_train_freeze_outputs_complete,
            _tss_train_freeze_closure_complete,
        ),
        StageResolutionCandidate(
            "tss_test_evidence",
            lineage_root / "05_tss_test_evidence",
            _tss_test_evidence_outputs_complete,
            _tss_test_evidence_closure_complete,
        ),
        StageResolutionCandidate(
            "tss_backtest_ready",
            lineage_root / "06_tss_backtest_ready",
            _tss_backtest_ready_outputs_complete,
            _tss_backtest_ready_closure_complete,
        ),
        StageResolutionCandidate(
            "tss_holdout_validation",
            lineage_root / "07_tss_holdout_validation",
            _tss_holdout_validation_outputs_complete,
            _tss_holdout_validation_closure_complete,
        ),
    ]
```

- [ ] **Step 3: Add downstream materialization helpers**

Add these helpers before `_review_closure_complete`:

```python
def _stage_resolution_candidates_for_lineage(lineage_root: Path) -> list[StageResolutionCandidate]:
    if _is_csf_route(lineage_root):
        return _csf_stage_resolution_candidates(lineage_root)
    if _is_tss_route(lineage_root):
        return _tss_stage_resolution_candidates(lineage_root)
    return _mainline_stage_resolution_candidates(lineage_root)


def _stage_has_downstream_materialization(stage_dir: Path) -> bool:
    lineage_root = stage_dir.parent
    stage_base = _stage_name_from_stage_dir(stage_dir)
    candidates = _stage_resolution_candidates_for_lineage(lineage_root)
    for index, candidate in enumerate(candidates):
        if candidate.stage_base != stage_base:
            continue
        return any(
            downstream.outputs_complete(downstream.stage_dir)
            for downstream in candidates[index + 1 :]
        )
    return False
```

- [ ] **Step 4: Use historical closure only for superseded upstream stages**

Replace `_review_closure_complete` with this implementation:

```python
def _review_closure_complete(stage_dir: Path) -> bool:
    has_historical_downstream_progress = (
        _historical_stage_advancing_closure_exists(stage_dir)
        and _stage_has_downstream_materialization(stage_dir)
    )
    if _review_proof_chain_error(stage_dir) is not None and not has_historical_downstream_progress:
        return False
    if _review_write_scope_audit_error(stage_dir) is not None and not has_historical_downstream_progress:
        return False
    if _review_closure_path(stage_dir, "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(stage_dir)
    return all(_review_closure_path(stage_dir, name).exists() for name in MANDATE_CLOSURE_OUTPUTS)
```

This keeps the highest materialized stage strict because `_stage_has_downstream_materialization(stage_dir)` returns `False` for that stage.

- [ ] **Step 5: Add one direct resolver guard test**

Add this test near the helper semantics test in `tests/session/test_research_session_runtime.py`:

```python
def test_review_closure_complete_uses_historical_certificate_only_after_downstream_materialization(
    tmp_path: Path,
) -> None:
    from runtime.tools import research_session as research_session_module

    lineage_root = tmp_path / "outputs" / "legacy_closed_with_downstream_case"
    mandate_dir = _prepare_csf_stage_pass_closed(
        lineage_root,
        stage_dir_name="01_mandate",
        stage="mandate",
    )
    _write_legacy_malformed_review_request(mandate_dir, stage="mandate")

    assert research_session_module._mandate_closure_complete(mandate_dir) is False

    _prepare_csf_stage_pass_closed(
        lineage_root,
        stage_dir_name="02_csf_data_ready",
        stage="csf_data_ready",
    )

    assert research_session_module._mandate_closure_complete(mandate_dir) is True
```

- [ ] **Step 6: Run focused resolver tests**

Run:

```bash
python -m pytest \
  tests/session/test_research_session_runtime.py::test_historical_advancing_closure_accepts_legacy_malformed_request_for_closed_stage \
  tests/session/test_research_session_runtime.py::test_review_closure_complete_uses_historical_certificate_only_after_downstream_materialization \
  tests/session/test_research_session_runtime.py::test_detect_session_stage_uses_latest_csf_closed_stage_over_legacy_upstream_request \
  tests/session/test_research_session_runtime.py::test_detect_session_stage_enters_csf_test_evidence_after_train_next_stage_confirmation \
  tests/session/test_research_session_runtime.py::test_detect_session_stage_keeps_highest_malformed_review_request_strict \
  tests/session/test_qros_progress_runtime.py::test_progress_reports_latest_csf_closed_stage_over_legacy_upstream_request \
  tests/session/test_qros_progress_runtime.py::test_progress_reports_csf_test_evidence_after_train_next_stage_confirmation \
  -q
```

Expected: PASS.

- [ ] **Step 7: Run broader session/progress tests**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py
```

Expected: PASS.

- [ ] **Step 8: Commit runtime fix**

```bash
git add runtime/tools/research_session.py tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py
git commit -m "fix: resolve qros progress from latest materialized stage"
```

## Task 4: Document Current-Stage Semantics

**Files:**
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Test: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Update research-session usage guide**

In `docs/guides/qros-research-session-usage.md`, add this paragraph near the existing `qros-progress` description:

```markdown
`qros-session` / `qros-progress` 的 `current_stage` 由最新真实物化的 stage 决定：该 stage 必须有 required `author/formal` outputs、`program_execution_manifest.json` provenance，以及 advancing `review/closure/stage_completion_certificate.yaml` 才能作为 completed progression fact。已经被后序真实 stage 超越的 legacy upstream review request 缺陷，不应把进度回退到旧 review；但当前最高物化 stage 的 proof-chain 缺陷仍然 fail closed，必须按 runtime 暴露的 repair / failure 状态处理。
```

- [ ] **Step 2: Update shared review protocol**

In `docs/guides/qros-review-shared-protocol.md`, add this short note near the closure/proof-chain discussion:

```markdown
Progress projection may ignore malformed legacy upstream review requests only after a later stage is already materially present and PASS/GO-closed. This is a progress-resolution rule, not a review-closure shortcut: the active or highest materialized review cycle still requires a valid request, receipt, final review, projected result, write-scope audit, and runtime-owned closure.
```

- [ ] **Step 3: Run docs check**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit docs**

```bash
git add docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md tests/docs/test_install_docs.py
git commit -m "docs: clarify qros current stage resolution"
```

## Task 5: Required Verification

**Files:**
- No source edits.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py
```

Expected: PASS.

- [ ] **Step 2: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 3: Run full-smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS.

- [ ] **Step 4: Inspect final git state**

Run:

```bash
git status --short
```

Expected: only intentional committed changes are present, or a clean worktree.

- [ ] **Step 5: Final report**

Report:

```text
Focused tests: python -m pytest tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py
Smoke: python runtime/scripts/run_verification_tier.py --tier smoke
Full-smoke: python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Include any failed command and the exact blocking reason if verification does not pass.
