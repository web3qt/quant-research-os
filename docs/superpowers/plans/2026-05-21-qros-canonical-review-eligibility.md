# QROS Canonical Review Eligibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a single canonical review-eligibility truth for QROS, stop hard-gate-failed stages from entering review, and harden review runtime normalization/stale-cycle handling without preserving old incorrect review-entry behavior.

**Architecture:** Introduce a dedicated review-eligibility module that computes whether a stage is institutionally allowed to enter review, then make both `research_session` and `progress_runtime` consume that single truth instead of re-deriving review readiness independently. Separately, harden the review runtime by normalizing reviewer raw findings before canonical closure and by making author-digest drift deterministically stale any old review cycle.

**Tech Stack:** Python 3.13, pytest, existing QROS runtime modules under `runtime/tools/`, existing CLI wrappers under `runtime/scripts/`, Markdown docs and skill files under `docs/` and `skills/`.

---

## File Map

### New files

- `runtime/tools/review_eligibility.py`
  Canonical truth layer for review eligibility. Owns the single deterministic answer to “may this lineage/stage enter review right now?”
- `runtime/tools/review_skillgen/raw_review_normalizer.py`
  Deterministic normalizer for reviewer raw payloads before closure.
- `tests/session/test_review_eligibility_runtime.py`
  Focused truth-layer tests for semantic fail, preflight fail, failure disposition, and successful review eligibility.
- `tests/review/test_raw_review_normalizer.py`
  Focused tests for outcome alias normalization, list-shape normalization, and hard failures on missing core semantics.

### Modified runtime files

- `runtime/tools/research_session.py`
  Consume canonical review eligibility; stop exposing `*_review_confirmation_pending` for hard-gate-failed stages.
- `runtime/tools/progress_runtime.py`
  Project the same review eligibility truth; stop recommending review skills for ineligible stages.
- `runtime/tools/review_session_runtime.py`
  Enforce stale-cycle invalidation against current author digest and canonical review scope.
- `runtime/tools/review_skillgen/review_result_writer.py`
  Consume normalized raw payloads before canonical closure.
- `runtime/tools/review_skillgen/review_findings.py`
  Reuse stricter shared list normalization helpers where appropriate.
- `runtime/tools/review_skillgen/protocol_validator.py`
  Keep active-cycle validation aligned with normalized raw findings and stale-cycle semantics.
- `runtime/tools/stage_evaluator.py`
  Reflect tightened stale-cycle / review-eligibility rules in stage-evaluator projections when review is blocked.

### Modified test files

- `tests/session/test_research_session_runtime.py`
- `tests/session/test_qros_progress_runtime.py`
- `tests/session/test_run_research_session_script.py`
- `tests/review/test_review_result_writer.py`
- `tests/review/test_protocol_validator.py`
- `tests/review/test_review_cycle_prepare.py`
- `tests/review/test_stage_evaluator.py`

### Modified docs and skill files

- `docs/guides/qros-research-session-usage.md`
- `docs/guides/qros-review-shared-protocol.md`
- `skills/core/qros-research-session/SKILL.md`
- `skills/core/qros-progress/SKILL.md`
- `skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md`
- `tests/skills/test_csf_test_evidence_contract_first_guidance.py`

## Task 1: Create the Canonical Review Eligibility Truth Layer

**Files:**
- Create: `runtime/tools/review_eligibility.py`
- Test: `tests/session/test_review_eligibility_runtime.py`

- [ ] **Step 1: Write the failing truth-layer tests**

```python
from pathlib import Path

from runtime.tools.review_eligibility import ReviewEligibilityStatus, compute_review_eligibility


def test_compute_review_eligibility_blocks_semantic_fail(tmp_path, monkeypatch):
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)

    monkeypatch.setattr(
        "runtime.tools.review_eligibility._semantic_gate_status",
        lambda *args, **kwargs: ("fail", "CSF_TEST_EVIDENCE_METRIC_FAIL", "mean_rank_ic <= 0"),
    )
    monkeypatch.setattr(
        "runtime.tools.review_eligibility._preflight_gate_status",
        lambda *args, **kwargs: ("pass", None, None),
    )
    monkeypatch.setattr(
        "runtime.tools.review_eligibility._failure_package_status",
        lambda *args, **kwargs: None,
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_test_evidence",
        review_skill="qros-csf-test-evidence-review",
    )

    assert status == ReviewEligibilityStatus(
        eligible_for_review=False,
        blocking_reason_code="CSF_TEST_EVIDENCE_METRIC_FAIL",
        blocking_reason="mean_rank_ic <= 0",
        review_blocking_surface="semantic_gate",
        authorized_review_skill=None,
        requires_failure_handling=True,
        failure_stage="csf_test_evidence",
        failure_reason_summary="mean_rank_ic <= 0",
    )


def test_compute_review_eligibility_allows_clean_review_entry(tmp_path, monkeypatch):
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)

    monkeypatch.setattr(
        "runtime.tools.review_eligibility._semantic_gate_status",
        lambda *args, **kwargs: ("pass", None, None),
    )
    monkeypatch.setattr(
        "runtime.tools.review_eligibility._preflight_gate_status",
        lambda *args, **kwargs: ("pass", None, None),
    )
    monkeypatch.setattr(
        "runtime.tools.review_eligibility._failure_package_status",
        lambda *args, **kwargs: None,
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_signal_ready",
        review_skill="qros-csf-signal-ready-review",
    )

    assert status.eligible_for_review is True
    assert status.authorized_review_skill == "qros-csf-signal-ready-review"
    assert status.requires_failure_handling is False


def test_compute_review_eligibility_blocks_failure_package_and_preserves_failure_routing_context(
    tmp_path,
    monkeypatch,
):
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)

    monkeypatch.setattr(
        "runtime.tools.review_eligibility._semantic_gate_status",
        lambda *args, **kwargs: ("pass", None, None),
    )
    monkeypatch.setattr(
        "runtime.tools.review_eligibility._preflight_gate_status",
        lambda *args, **kwargs: ("pass", None, None),
    )
    monkeypatch.setattr(
        "runtime.tools.review_eligibility._failure_package_status",
        lambda *args, **kwargs: {
            "blocking_reason_code": "FAILURE_PACKAGE_OPEN",
            "blocking_reason": "Failure handling package is still active.",
            "failure_stage": "csf_test_evidence",
            "failure_reason_summary": "Failure handling package is still active.",
        },
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_test_evidence",
        review_skill="qros-csf-test-evidence-review",
    )

    assert status.eligible_for_review is False
    assert status.authorized_review_skill is None
    assert status.requires_failure_handling is True
    assert status.failure_stage == "csf_test_evidence"
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `python -m pytest tests/session/test_review_eligibility_runtime.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'runtime.tools.review_eligibility'`

- [ ] **Step 3: Write the minimal canonical truth module**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from pathlib import Path


ReviewBlockingSurface = Literal[
    "semantic_gate",
    "preflight_gate",
    "failure_package",
    "lineage_lock",
    "protected_state",
]


@dataclass(frozen=True)
class ReviewEligibilityStatus:
    eligible_for_review: bool
    blocking_reason_code: str | None
    blocking_reason: str | None
    review_blocking_surface: ReviewBlockingSurface | None
    authorized_review_skill: str | None
    requires_failure_handling: bool
    failure_stage: str | None
    failure_reason_summary: str | None


def compute_review_eligibility(
    *,
    lineage_root: Path,
    current_stage: str,
    review_skill: str,
) -> ReviewEligibilityStatus:
    semantic_state, semantic_code, semantic_reason = _semantic_gate_status(
        lineage_root=lineage_root,
        current_stage=current_stage,
    )
    if semantic_state == "fail":
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code=semantic_code,
            blocking_reason=semantic_reason,
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=True,
            failure_stage=current_stage,
            failure_reason_summary=semantic_reason,
        )

    preflight_state, preflight_code, preflight_reason = _preflight_gate_status(
        lineage_root=lineage_root,
        current_stage=current_stage,
    )
    if preflight_state == "fail":
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code=preflight_code,
            blocking_reason=preflight_reason,
            review_blocking_surface="preflight_gate",
            authorized_review_skill=None,
            requires_failure_handling=False,
            failure_stage=None,
            failure_reason_summary=None,
        )

    failure_package = _failure_package_status(lineage_root=lineage_root)
    if failure_package is not None:
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code=failure_package.blocking_reason_code,
            blocking_reason=failure_package.blocking_reason,
            review_blocking_surface="failure_package",
            authorized_review_skill=None,
            requires_failure_handling=True,
            failure_stage=failure_package.failure_stage,
            failure_reason_summary=failure_package.failure_reason_summary,
        )

    return ReviewEligibilityStatus(
        eligible_for_review=True,
        blocking_reason_code=None,
        blocking_reason=None,
        review_blocking_surface=None,
        authorized_review_skill=review_skill,
        requires_failure_handling=False,
        failure_stage=None,
        failure_reason_summary=None,
    )
```

- [ ] **Step 4: Run the truth-layer tests and make them pass**

Run: `python -m pytest tests/session/test_review_eligibility_runtime.py -v`

Expected: PASS for both tests

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_eligibility.py tests/session/test_review_eligibility_runtime.py
git commit -m "feat: add canonical review eligibility truth layer"
```

## Task 2: Route `qros-session` Through the Canonical Truth

**Files:**
- Modify: `runtime/tools/research_session.py`
- Test: `tests/session/test_research_session_runtime.py`
- Test: `tests/session/test_run_research_session_script.py`

- [ ] **Step 1: Add failing session-runtime tests for blocked review entry**

```python
from runtime.tools.review_eligibility import ReviewEligibilityStatus
from runtime.tools.research_session import run_research_session


def test_run_research_session_blocks_review_confirmation_when_stage_is_not_review_eligible(
    tmp_path,
    monkeypatch,
):
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "blocked_case"
    lineage_root.mkdir(parents=True)

    monkeypatch.setattr(
        "runtime.tools.research_session.detect_session_stage",
        lambda root: "csf_test_evidence",
    )
    monkeypatch.setattr(
        "runtime.tools.research_session._resolve_review_skill_for_stage",
        lambda stage: "qros-csf-test-evidence-review",
    )
    monkeypatch.setattr(
        "runtime.tools.research_session.compute_review_eligibility",
        lambda **kwargs: ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="CSF_TEST_EVIDENCE_METRIC_FAIL",
            blocking_reason="mean_rank_ic <= 0",
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=True,
            failure_stage="csf_test_evidence",
            failure_reason_summary="mean_rank_ic <= 0",
        ),
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="blocked_case", continue_mode=True)

    assert status.current_stage == "csf_test_evidence"
    assert status.current_skill == "qros-stage-failure-handler"
    assert status.requires_failure_handling is True
    assert status.gate_status == "FAILURE_HANDLING_REQUIRED"
```

- [ ] **Step 2: Run the focused session tests to verify failure**

Run: `python -m pytest tests/session/test_research_session_runtime.py -k "review_eligible or failure_handler" -v`

Expected: FAIL because `run_research_session()` still exposes review confirmation or does not consult `compute_review_eligibility()`

- [ ] **Step 3: Wire `research_session` to the new truth layer**

```python
from runtime.tools.review_eligibility import compute_review_eligibility


def _review_status_override(*, lineage_root: Path, current_stage: str):
    review_skill = _resolve_review_skill_for_stage(current_stage)
    if review_skill is None:
        return None

    eligibility = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage=current_stage,
        review_skill=review_skill,
    )
    if eligibility.eligible_for_review:
        return None

    return {
        "current_stage": current_stage,
        "current_skill": "qros-stage-failure-handler" if eligibility.requires_failure_handling else "qros-research-session",
        "gate_status": "FAILURE_HANDLING_REQUIRED" if eligibility.requires_failure_handling else "OUTPUTS_INVALID",
        "blocking_reason_code": eligibility.blocking_reason_code,
        "blocking_reason": eligibility.blocking_reason,
        "next_action": (
            f"Enter failure handling for {eligibility.failure_stage}"
            if eligibility.requires_failure_handling
            else "Fix current author outputs before review"
        ),
    }
```

- [ ] **Step 4: Run the focused session tests and script output tests**

Run: `python -m pytest tests/session/test_research_session_runtime.py tests/session/test_run_research_session_script.py -k "review_eligible or failure_handler or review_confirmation_pending" -v`

Expected: PASS, with blocked cases no longer surfacing `*_review_confirmation_pending`

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_session.py tests/session/test_research_session_runtime.py tests/session/test_run_research_session_script.py
git commit -m "feat: gate review entry on canonical eligibility"
```

## Task 3: Make `qros-progress` Project the Same Review Truth

**Files:**
- Modify: `runtime/tools/progress_runtime.py`
- Test: `tests/session/test_qros_progress_runtime.py`

- [ ] **Step 1: Add failing progress tests for ineligible review stages**

```python
from runtime.tools.review_eligibility import ReviewEligibilityStatus
from runtime.tools.progress_runtime import progress_status_payload


def test_progress_does_not_recommend_review_skill_when_stage_is_not_review_eligible(
    tmp_path,
    monkeypatch,
):
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "blocked_case"
    lineage_root.mkdir(parents=True)

    monkeypatch.setattr("runtime.tools.progress_runtime.detect_session_stage", lambda root: "csf_test_evidence")
    monkeypatch.setattr(
        "runtime.tools.progress_runtime.compute_review_eligibility",
        lambda **kwargs: ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="CSF_TEST_EVIDENCE_METRIC_FAIL",
            blocking_reason="mean_rank_ic <= 0",
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=True,
            failure_stage="csf_test_evidence",
            failure_reason_summary="mean_rank_ic <= 0",
        ),
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id="blocked_case")

    assert payload["current_stage"] == "csf_test_evidence"
    assert payload["recommended_skill"] == "qros-stage-failure-handler"
    assert payload["blocking_reason_code"] == "CSF_TEST_EVIDENCE_METRIC_FAIL"
```

- [ ] **Step 2: Run the progress tests to verify failure**

Run: `python -m pytest tests/session/test_qros_progress_runtime.py -k "review_eligible or recommended_skill" -v`

Expected: FAIL because `progress_runtime.py` still recommends a review skill or review-confirmation state

- [ ] **Step 3: Reuse the canonical truth in `progress_runtime.py`**

```python
from runtime.tools.review_eligibility import compute_review_eligibility


eligibility = compute_review_eligibility(
    lineage_root=lineage_root,
    current_stage=current_stage,
    review_skill=_resolve_review_skill_for_stage(current_stage),
)
if not eligibility.eligible_for_review:
    gate_status = "FAILURE_HANDLING_REQUIRED" if eligibility.requires_failure_handling else "OUTPUTS_INVALID"
    next_action = (
        f"Enter failure handling for {eligibility.failure_stage}"
        if eligibility.requires_failure_handling
        else "Fix current author outputs before review"
    )
    current_skill = "qros-stage-failure-handler" if eligibility.requires_failure_handling else "qros-research-session"
```

- [ ] **Step 4: Run the progress tests and confirm projection consistency**

Run: `python -m pytest tests/session/test_qros_progress_runtime.py -v`

Expected: PASS, with blocked review cases no longer recommending `qros-*-review`

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/progress_runtime.py tests/session/test_qros_progress_runtime.py
git commit -m "feat: align qros-progress with canonical review eligibility"
```

## Task 4: Add Raw Review Payload Normalization Before Closure

**Files:**
- Create: `runtime/tools/review_skillgen/raw_review_normalizer.py`
- Modify: `runtime/tools/review_skillgen/review_result_writer.py`
- Modify: `runtime/tools/review_skillgen/review_findings.py`
- Test: `tests/review/test_raw_review_normalizer.py`
- Test: `tests/review/test_review_result_writer.py`

- [ ] **Step 1: Write the failing normalizer tests**

```python
from runtime.tools.review_skillgen.raw_review_normalizer import normalize_raw_review_payload


def test_normalize_raw_review_payload_converts_pass_alias_and_single_string_findings():
    payload = normalize_raw_review_payload(
        {
            "review_loop_outcome": "PASS",
            "blocking_findings": "",
            "reservation_findings": "watch liquidity drift",
            "info_findings": ["shape ok"],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        }
    )

    assert payload["review_loop_outcome"] == "CLOSURE_READY_PASS"
    assert payload["blocking_findings"] == []
    assert payload["reservation_findings"] == ["watch liquidity drift"]


def test_normalize_raw_review_payload_rejects_missing_core_outcome():
    try:
        normalize_raw_review_payload({"blocking_findings": []})
    except ValueError as exc:
        assert "review_loop_outcome" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run the normalizer and writer tests to verify failure**

Run: `python -m pytest tests/review/test_raw_review_normalizer.py tests/review/test_review_result_writer.py -v`

Expected: FAIL because the normalizer module does not exist and `review_result_writer.py` still expects already-canonical raw payloads

- [ ] **Step 3: Implement deterministic raw normalization and hook it into closure**

```python
RAW_OUTCOME_ALIASES = {
    "PASS": "CLOSURE_READY_PASS",
    "APPROVE": "CLOSURE_READY_PASS",
    "PASS_WITH_RESERVATIONS": "CLOSURE_READY_CONDITIONAL_PASS",
}


def normalize_raw_review_payload(payload: dict[str, object]) -> dict[str, object]:
    outcome = str(payload.get("review_loop_outcome", "")).strip()
    if not outcome:
        raise ValueError("review_loop_outcome must be present")
    normalized_outcome = RAW_OUTCOME_ALIASES.get(outcome, outcome)

    def _normalize_strings(value: object) -> list[str]:
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return list(value)
        raise ValueError(f"unsupported findings payload: {value!r}")

    return {
        **payload,
        "review_loop_outcome": normalized_outcome,
        "blocking_findings": _normalize_strings(payload.get("blocking_findings")),
        "reservation_findings": _normalize_strings(payload.get("reservation_findings")),
        "info_findings": _normalize_strings(payload.get("info_findings")),
        "residual_risks": _normalize_strings(payload.get("residual_risks")),
        "allowed_modifications": _normalize_strings(payload.get("allowed_modifications")),
        "downstream_permissions": _normalize_strings(payload.get("downstream_permissions")),
    }
```

- [ ] **Step 4: Run the focused normalizer and writer tests**

Run: `python -m pytest tests/review/test_raw_review_normalizer.py tests/review/test_review_result_writer.py -v`

Expected: PASS, with alias outcomes and string findings normalized before canonical closure

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_skillgen/raw_review_normalizer.py runtime/tools/review_skillgen/review_result_writer.py runtime/tools/review_skillgen/review_findings.py tests/review/test_raw_review_normalizer.py tests/review/test_review_result_writer.py
git commit -m "feat: normalize reviewer raw payloads before closure"
```

## Task 5: Make Author-Digest Drift Deterministically Stale the Old Review Cycle

**Files:**
- Modify: `runtime/tools/review_session_runtime.py`
- Modify: `runtime/tools/review_skillgen/protocol_validator.py`
- Modify: `runtime/tools/stage_evaluator.py`
- Test: `tests/review/test_review_cycle_prepare.py`
- Test: `tests/review/test_protocol_validator.py`
- Test: `tests/review/test_stage_evaluator.py`

- [ ] **Step 1: Add failing stale-cycle tests**

```python
def test_protocol_validator_rejects_final_review_bound_to_old_author_digest(tmp_path):
    stage_dir = tmp_path / "outputs" / "lineage" / "03_csf_signal_ready"
    stage_dir.mkdir(parents=True)

    _write_active_review_request(stage_dir, author_digest="digest-a")
    _write_final_review(stage_dir)
    _mutate_author_digest(stage_dir, new_digest="digest-b")

    with pytest.raises(ValueError, match="stale author digest"):
        validate_active_review_cycle(stage_dir)
```

- [ ] **Step 2: Run the stale-cycle focused tests to verify failure**

Run: `python -m pytest tests/review/test_review_cycle_prepare.py tests/review/test_protocol_validator.py tests/review/test_stage_evaluator.py -k "stale or digest" -v`

Expected: FAIL because current stale handling archives obvious old cycles but does not reject every current-cycle closure bound to an old author digest

- [ ] **Step 3: Tighten stale-cycle checks across prepare, validation, and evaluation**

```python
def _require_current_author_digest(*, bound_digest: str, current_digest: str) -> None:
    if bound_digest != current_digest:
        raise ValueError(
            f"stale author digest: bound={bound_digest} current={current_digest}; "
            "reset the archived cycle and request a fresh reviewer run"
        )


def validate_active_review_cycle(stage_dir: Path) -> dict[str, object]:
    request_payload = _load_active_request(stage_dir)
    current_digest = _compute_author_digest(stage_dir)
    _require_current_author_digest(
        bound_digest=request_payload["bound_author_digest"],
        current_digest=current_digest,
    )
    ...
```

- [ ] **Step 4: Run the stale-cycle tests**

Run: `python -m pytest tests/review/test_review_cycle_prepare.py tests/review/test_protocol_validator.py tests/review/test_stage_evaluator.py -k "stale or digest" -v`

Expected: PASS, with digest drift deterministically invalidating old review cycles

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_session_runtime.py runtime/tools/review_skillgen/protocol_validator.py runtime/tools/stage_evaluator.py tests/review/test_review_cycle_prepare.py tests/review/test_protocol_validator.py tests/review/test_stage_evaluator.py
git commit -m "feat: stale review cycles on author digest drift"
```

## Task 6: Update Docs and Skills to the New Canonical Rules

**Files:**
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `skills/core/qros-progress/SKILL.md`
- Modify: `skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md`
- Test: `tests/skills/test_csf_test_evidence_contract_first_guidance.py`

- [ ] **Step 1: Add the failing doc/skill assertions**

```python
from pathlib import Path


def test_csf_test_evidence_review_skill_says_semantic_fail_cannot_enter_review():
    content = Path("skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md").read_text(encoding="utf-8")
    assert "semantic validator / deterministic preflight 不通过，不得进入 `csf_test_evidence` review" in content
    assert "hard gate fail 不是 reviewer 再裁一次的候选状态" in content
```

- [ ] **Step 2: Run the focused skill/doc tests to verify failure**

Run: `python -m pytest tests/skills/test_csf_test_evidence_contract_first_guidance.py -v`

Expected: FAIL because the doc/skill text still permits or implies review entry without canonical eligibility wording

- [ ] **Step 3: Rewrite the affected docs and skills to the new canonical model**

```markdown
- 只有在 artifact contract、semantic validator、deterministic review preflight 都通过后，当前 stage 才能进入 `*_review_confirmation_pending`
- hard gate fail 直接转 failure-style blocking，不得进入 review
- `qros-progress` 与 `qros-research-session` 必须对 review 资格给出同一真值
- `CHILD_LINEAGE` 只能从 formal failure / disposition 链打开
```

- [ ] **Step 4: Run the doc/skill tests**

Run: `python -m pytest tests/skills/test_csf_test_evidence_contract_first_guidance.py tests/docs/test_install_docs.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md skills/core/qros-research-session/SKILL.md skills/core/qros-progress/SKILL.md skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md tests/skills/test_csf_test_evidence_contract_first_guidance.py
git commit -m "docs: codify canonical review eligibility rules"
```

## Task 7: Run Full Verification for the Review-Orchestration Change Set

**Files:**
- Test: `tests/session/test_review_eligibility_runtime.py`
- Test: `tests/session/test_research_session_runtime.py`
- Test: `tests/session/test_qros_progress_runtime.py`
- Test: `tests/review/test_raw_review_normalizer.py`
- Test: `tests/review/test_review_result_writer.py`
- Test: `tests/review/test_review_cycle_prepare.py`
- Test: `tests/review/test_protocol_validator.py`
- Test: `tests/review/test_stage_evaluator.py`

- [ ] **Step 1: Run the focused review-eligibility and review-runtime suite**

Run:

```bash
python -m pytest \
  tests/session/test_review_eligibility_runtime.py \
  tests/session/test_research_session_runtime.py \
  tests/session/test_qros_progress_runtime.py \
  tests/review/test_raw_review_normalizer.py \
  tests/review/test_review_result_writer.py \
  tests/review/test_review_cycle_prepare.py \
  tests/review/test_protocol_validator.py \
  tests/review/test_stage_evaluator.py -v
```

Expected: PASS

- [ ] **Step 2: Run the repository smoke tier**

Run: `python runtime/scripts/run_verification_tier.py --tier smoke`

Expected: PASS

- [ ] **Step 3: Run the repository full-smoke tier**

Run: `python runtime/scripts/run_verification_tier.py --tier full-smoke`

Expected: PASS

- [ ] **Step 4: Run the documentation/bootstrap minimum checks after the code and skill updates**

Run:

```bash
python -m pytest \
  tests/contracts/test_agents_layout.py \
  tests/bootstrap/test_project_bootstrap.py \
  tests/docs/test_install_docs.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add \
  runtime/tools/review_eligibility.py \
  runtime/tools/research_session.py \
  runtime/tools/progress_runtime.py \
  runtime/tools/review_session_runtime.py \
  runtime/tools/review_skillgen/raw_review_normalizer.py \
  runtime/tools/review_skillgen/review_result_writer.py \
  runtime/tools/review_skillgen/review_findings.py \
  runtime/tools/review_skillgen/protocol_validator.py \
  runtime/tools/stage_evaluator.py \
  docs/guides/qros-research-session-usage.md \
  docs/guides/qros-review-shared-protocol.md \
  skills/core/qros-research-session/SKILL.md \
  skills/core/qros-progress/SKILL.md \
  skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md \
  tests/session/test_review_eligibility_runtime.py \
  tests/session/test_research_session_runtime.py \
  tests/session/test_run_research_session_script.py \
  tests/session/test_qros_progress_runtime.py \
  tests/review/test_raw_review_normalizer.py \
  tests/review/test_review_result_writer.py \
  tests/review/test_review_cycle_prepare.py \
  tests/review/test_protocol_validator.py \
  tests/review/test_stage_evaluator.py \
  tests/skills/test_csf_test_evidence_contract_first_guidance.py
git commit -m "feat: enforce canonical review eligibility"
```

## Spec Coverage Check

- Canonical review eligibility truth layer: Task 1
- Session uses single truth instead of ad hoc review routing: Task 2
- Progress uses the same truth projection: Task 3
- Review runtime normalization for raw reviewer payloads: Task 4
- Deterministic stale-cycle invalidation on author-digest drift: Task 5
- Docs and skill cleanup for non-compatible canonical review rules: Task 6
- Required focused tests + smoke + full-smoke for review/stage-flow changes: Task 7

## Self-Review Notes

- Placeholder scan complete: no unfinished placeholder markers or deferred-action instructions remain.
- Type consistency check complete: all tasks use `ReviewEligibilityStatus`, `compute_review_eligibility()`, and `normalize_raw_review_payload()` consistently.
- Scope check complete: this plan is intentionally limited to review eligibility truth, review runtime hardening, and documentation/test cleanup. It does not attempt a full session-state-machine rewrite.
