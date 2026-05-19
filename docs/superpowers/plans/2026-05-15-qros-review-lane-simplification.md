# QROS Review Lane Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify QROS review so an independent reviewer agent writes one canonical final review artifact directly, and the main thread only consumes the verdict to continue author-fix, next-stage, or failure handling.

**Architecture:** Replace the current `receipt -> raw findings -> qros-review closer -> canonical result -> closure` path with `prepare request/handoff -> reviewer writes review/final_review.yaml -> runtime consumes final verdict`. Keep reviewer isolation and write-boundary protections, but remove receipt/raw/closer as the ordinary review path. Preserve immutable ledger and failure routing semantics by making `FIX_REQUIRED` and `RETRY` diverge in the session/runtime layer.

**Tech Stack:** Python 3.12/3.13, PyYAML, pytest, existing QROS runtime helpers under `runtime/tools/`, review skills under `skills/*/*review*/`, and docs under `docs/guides/`.

---

## File Structure

- Modify `runtime/tools/review_skillgen/adversarial_review_contract.py`
  - Add canonical `final_review.yaml` filename and loader/validator.
  - Narrow review binding to reviewer-owned final artifact digests and verdict schema.
- Modify `runtime/tools/review_skillgen/review_runtime_state.py`
  - Make `final_review.yaml` the canonical review result file for active/closed cycles.
  - Remove ordinary-path dependence on `reviewer_receipt.yaml`, `reviewer_findings.raw.yaml`, and `adversarial_review_result.yaml`.
- Modify `runtime/tools/research_session.py`
  - Replace “run `qros-review` / read raw + canonical result” guidance with “launch reviewer / wait for `review/final_review.yaml` / consume final verdict”.
  - Separate `FIX_REQUIRED` from `RETRY` in next-action text and state routing.
- Modify `runtime/tools/review_session_runtime.py`
  - Update reviewer handoff prompt so reviewer writes `review/final_review.yaml` directly.
- Modify `runtime/tools/review_skillgen/protocol_validator.py`
  - Validate direct-final-review existence and binding instead of raw/receipt/closer chain for ordinary review cycles.
- Modify `runtime/scripts/run_research_session.py` and any runtime entrypoints that surface review guidance
  - Ensure user-visible instructions no longer tell ordinary agents to run `qros-review`.
- Modify review skills that currently hardcode raw/receipt/closer protocol:
  - `skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md`
  - `skills/signal_ready/qros-signal-ready-review/SKILL.md`
  - `skills/train_freeze/qros-train-freeze-review/SKILL.md`
  - `skills/backtest_ready/qros-backtest-ready-review/SKILL.md`
  - `skills/holdout_validation/qros-holdout-validation-review/SKILL.md`
- Modify shared docs:
  - `docs/guides/qros-review-shared-protocol.md`
  - `docs/guides/qros-research-session-usage.md`
  - `docs/guides/how-qros-works.md`
- Add or modify tests:
  - `tests/review/test_adversarial_review_runtime.py`
  - `tests/review/test_review_engine_csf_metric_gates.py`
  - `tests/session/test_research_session_assets.py`
  - `tests/session/test_lineage_lock_session_status.py`
  - `tests/agent_eval/test_agent_behavior_eval_case_contract.py`

---

### Task 1: Introduce Reviewer-Owned `review/final_review.yaml`

**Files:**
- Modify: `runtime/tools/review_skillgen/adversarial_review_contract.py`
- Modify: `runtime/tools/review_skillgen/review_runtime_state.py`
- Test: `tests/review/test_adversarial_review_runtime.py`

- [ ] **Step 1: Write the failing test for direct final review loading**

Add this test near the current review artifact loading tests in `tests/review/test_adversarial_review_runtime.py`:

```python
def test_load_final_review_requires_reviewer_identity_and_scope_binding(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "lineage_a" / "02_csf_data_ready"
    review_dir = stage_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "lineage_id": "lineage_a",
        "stage_id": "csf_data_ready",
        "reviewer_identity": "qros-csf-data-ready-reviewer",
        "reviewer_agent_id": "agent-123",
        "reviewed_artifact_paths": ["author/formal/panel_manifest.json"],
        "reviewed_program_path": "program/cross_sectional_factor/data_ready/run_stage.py",
        "reviewed_artifact_digest": "sha256:artifact-digest",
        "reviewed_program_digest": "sha256:program-digest",
        "verdict": "FIX_REQUIRED",
        "review_summary": "coverage evidence is incomplete",
        "blocking_findings": ["coverage snapshot set is incomplete"],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": ["refresh current stage formal artifacts"],
        "rollback_stage": "csf_data_ready",
        "downstream_permissions": [],
        "recommended_next_action": "resume author-fix",
    }
    (review_dir / "final_review.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    loaded = load_final_review(review_dir / "final_review.yaml")
    assert loaded["verdict"] == "FIX_REQUIRED"
    assert loaded["reviewer_identity"] == "qros-csf-data-ready-reviewer"
    assert loaded["reviewed_artifact_digest"] == "sha256:artifact-digest"
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py::test_load_final_review_requires_reviewer_identity_and_scope_binding -q
```

Expected: FAIL because `load_final_review(...)` does not exist and `final_review.yaml` is not part of the runtime state model.

- [ ] **Step 3: Add the new canonical filename and loader**

In `runtime/tools/review_skillgen/adversarial_review_contract.py`, add:

```python
FINAL_REVIEW_FILENAME = "final_review.yaml"
ALLOWED_FINAL_REVIEW_VERDICTS = {
    "PASS",
    "CONDITIONAL PASS",
    "FIX_REQUIRED",
    "RETRY",
    "NO-GO",
    "CHILD LINEAGE",
}
```

Then add a loader alongside `load_adversarial_review_result(...)`:

```python
def load_final_review(path: str | Path) -> dict[str, Any]:
    final_review_path = Path(path)
    payload = _load_yaml(final_review_path)
    data = {
        "lineage_id": _require_string(payload, "lineage_id", path=final_review_path),
        "stage_id": _require_string(payload, "stage_id", path=final_review_path),
        "reviewer_identity": _require_string(payload, "reviewer_identity", path=final_review_path),
        "reviewer_agent_id": _require_string(payload, "reviewer_agent_id", path=final_review_path),
        "reviewed_artifact_paths": _normalize_string_list(payload.get("reviewed_artifact_paths"), field_name="reviewed_artifact_paths", path=final_review_path),
        "reviewed_program_path": _require_string(payload, "reviewed_program_path", path=final_review_path),
        "reviewed_artifact_digest": _require_string(payload, "reviewed_artifact_digest", path=final_review_path),
        "reviewed_program_digest": _require_string(payload, "reviewed_program_digest", path=final_review_path),
        "verdict": _require_string(payload, "verdict", path=final_review_path),
        "review_summary": _require_string(payload, "review_summary", path=final_review_path),
        "blocking_findings": _normalize_string_list(payload.get("blocking_findings"), field_name="blocking_findings", path=final_review_path),
        "reservation_findings": _normalize_string_list(payload.get("reservation_findings"), field_name="reservation_findings", path=final_review_path),
        "info_findings": _normalize_string_list(payload.get("info_findings"), field_name="info_findings", path=final_review_path),
        "residual_risks": _normalize_string_list(payload.get("residual_risks"), field_name="residual_risks", path=final_review_path),
        "allowed_modifications": _normalize_string_list(payload.get("allowed_modifications"), field_name="allowed_modifications", path=final_review_path),
        "rollback_stage": _require_nullable_string(payload, "rollback_stage", path=final_review_path),
        "downstream_permissions": _normalize_string_list(payload.get("downstream_permissions"), field_name="downstream_permissions", path=final_review_path),
        "recommended_next_action": _require_string(payload, "recommended_next_action", path=final_review_path),
    }
    if data["verdict"] not in ALLOWED_FINAL_REVIEW_VERDICTS:
        raise ValueError(f"{final_review_path}: unsupported verdict {data['verdict']!r}")
    return data
```

- [ ] **Step 4: Make final review part of review runtime state**

In `runtime/tools/review_skillgen/review_runtime_state.py`, replace the ordinary-path protected review result file set with:

```python
REVIEW_RUNTIME_RESULT_FILENAMES = (
    "final_review.yaml",
    "review_findings.yaml",
)
```

If there is a helper that loads the canonical review result path, point it to:

```python
final_review_path = review_dir / "final_review.yaml"
```

and use:

```python
from runtime.tools.review_skillgen.adversarial_review_contract import load_final_review
```

- [ ] **Step 5: Run the focused test to verify it passes**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py::test_load_final_review_requires_reviewer_identity_and_scope_binding -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_skillgen/adversarial_review_contract.py runtime/tools/review_skillgen/review_runtime_state.py tests/review/test_adversarial_review_runtime.py
git commit -m "feat: add canonical final review artifact"
```

---

### Task 2: Change Reviewer Handoff To Write Final Review Directly

**Files:**
- Modify: `runtime/tools/review_session_runtime.py`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md`
- Test: `tests/session/test_research_session_assets.py`

- [ ] **Step 1: Write the failing handoff-prompt test**

Add this test to `tests/session/test_research_session_assets.py` near the current review-handoff assertions:

```python
def test_review_handoff_instructs_reviewer_to_write_final_review_yaml(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    project_root.mkdir(parents=True, exist_ok=True)
    content = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")

    assert "review/final_review.yaml" in content
    assert "review/result/reviewer_findings.raw.yaml" not in content
    assert "qros-review" not in content
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/session/test_research_session_assets.py::test_review_handoff_instructs_reviewer_to_write_final_review_yaml -q
```

Expected: FAIL because docs and prompts still reference `reviewer_findings.raw.yaml` and `qros-review`.

- [ ] **Step 3: Update reviewer handoff prompt**

In `runtime/tools/review_session_runtime.py`, replace the reviewer write instruction block with:

```python
        "Permitted write only:",
        "- review/final_review.yaml",
        "",
        "Write exactly one canonical machine-readable review artifact.",
        "Do not write reviewer_findings.raw.yaml.",
        "Do not run qros-review or any closer step.",
```

And replace the schema block with:

```python
        "Required final review schema:",
        "lineage_id: <lineage id>",
        "stage_id: <stage id>",
        "reviewer_identity: <reviewer identity>",
        "reviewer_agent_id: <reviewer agent id>",
        "reviewed_artifact_paths: [<relative paths>]",
        "reviewed_program_path: <relative path>",
        "reviewed_artifact_digest: <artifact digest>",
        "reviewed_program_digest: <program digest>",
        "verdict: one of PASS, CONDITIONAL PASS, FIX_REQUIRED, RETRY, NO-GO, CHILD LINEAGE",
        "review_summary: <single sentence>",
        "blocking_findings: []",
        "reservation_findings: []",
        "info_findings: []",
        "residual_risks: []",
        "allowed_modifications: []",
        "rollback_stage: <stage or null>",
        "downstream_permissions: []",
        "recommended_next_action: <single sentence>",
```

- [ ] **Step 4: Update shared protocol and one representative review skill**

In `docs/guides/qros-review-shared-protocol.md`, replace the launcher/reviewer/closer duties section with:

```markdown
- launcher 主线程不得自己撰写 `review/final_review.yaml`
- reviewer 子代理不得修改 `author/formal/*`
- reviewer 子代理正常只写 `review/final_review.yaml`
- ordinary review path no longer uses `reviewer_receipt.yaml` / `reviewer_findings.raw.yaml` / `qros-review`
- 主线程在 reviewer 完成后只读取 `review/final_review.yaml` 并推进状态
```

In `skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md`, replace the reviewer-write and closer steps with:

```markdown
- reviewer 子代理只允许写入 `review/final_review.yaml`
- reviewer 完成后，主线程读取 `review/final_review.yaml`
- 若 `verdict = FIX_REQUIRED`，回 author-fix；若 `PASS` 或 `CONDITIONAL PASS`，推进到 next-stage confirmation；若 `RETRY / NO-GO / CHILD LINEAGE`，转入对应治理路径
```

- [ ] **Step 5: Run the focused test to verify it passes**

Run:

```bash
python -m pytest tests/session/test_research_session_assets.py::test_review_handoff_instructs_reviewer_to_write_final_review_yaml -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_session_runtime.py docs/guides/qros-review-shared-protocol.md skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md tests/session/test_research_session_assets.py
git commit -m "feat: switch reviewer handoff to final review artifact"
```

---

### Task 3: Route Main Thread By Final Verdict Instead Of Closer Artifacts

**Files:**
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/scripts/run_research_session.py`
- Test: `tests/session/test_lineage_lock_session_status.py`

- [ ] **Step 1: Write the failing session-routing test**

Add this test to `tests/session/test_lineage_lock_session_status.py`:

```python
def test_session_routes_fix_required_and_retry_differently_from_final_review(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "lineage_a" / "04_csf_train_freeze"
    review_dir = stage_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    fix_required = {
        "lineage_id": "lineage_a",
        "stage_id": "csf_train_freeze",
        "reviewer_identity": "reviewer",
        "reviewer_agent_id": "agent-1",
        "reviewed_artifact_paths": ["author/formal/train_manifest.yaml"],
        "reviewed_program_path": "program/cross_sectional_factor/train_freeze/run_stage.py",
        "reviewed_artifact_digest": "sha256:a",
        "reviewed_program_digest": "sha256:b",
        "verdict": "FIX_REQUIRED",
        "review_summary": "binding mismatch",
        "blocking_findings": ["binding mismatch"],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": ["refresh current stage formal artifacts"],
        "rollback_stage": "csf_train_freeze",
        "downstream_permissions": [],
        "recommended_next_action": "resume author-fix",
    }
    (review_dir / "final_review.yaml").write_text(yaml.safe_dump(fix_required, sort_keys=False), encoding="utf-8")

    fix_payload = _build_stage_status_payload(stage_dir)
    assert "author-fix" in fix_payload["next_action"]

    retry_payload = dict(fix_required)
    retry_payload["verdict"] = "RETRY"
    retry_payload["recommended_next_action"] = "enter failure handling"
    (review_dir / "final_review.yaml").write_text(yaml.safe_dump(retry_payload, sort_keys=False), encoding="utf-8")

    retry_status = _build_stage_status_payload(stage_dir)
    assert "failure" in retry_status["next_action"]
    assert "author-fix" not in retry_status["next_action"]
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/session/test_lineage_lock_session_status.py::test_session_routes_fix_required_and_retry_differently_from_final_review -q
```

Expected: FAIL because session status still consumes `adversarial_review_result.yaml` and closer-oriented guidance.

- [ ] **Step 3: Replace closer-based review reads with final-review reads**

In `runtime/tools/research_session.py`, change the review result loader usage from:

```python
review_result = _load_adversarial_review_result_if_present(stage_dir)
```

to:

```python
review_result = _load_final_review_if_present(stage_dir)
```

Add the loader:

```python
def _load_final_review_if_present(stage_dir: Path) -> dict[str, Any] | None:
    path = stage_dir / "review" / "final_review.yaml"
    if not path.exists():
        return None
    return load_final_review(path)
```

Then change the verdict mapping branch to:

```python
    if review_result and review_result["verdict"] == "FIX_REQUIRED":
        return {
            "status": "AUTHOR_FIX_REQUIRED",
            "next_action": "Read review/final_review.yaml, resume the author lane, refresh author/formal outputs, then launch a fresh reviewer cycle.",
        }
    if review_result and review_result["verdict"] == "RETRY":
        return {
            "status": "RETRY_REQUIRES_FAILURE_PROTOCOL",
            "next_action": "Do not replay locked formal artifacts. Enter the stage failure/retry protocol described in review/final_review.yaml.",
        }
```

And change the review-confirmation branch text from `qros-review-cycle prepare` + `qros-review` to:

```python
        "Enter the stage review skill in the current session. It should launch an independent reviewer and wait for review/final_review.yaml.",
```

- [ ] **Step 4: Update CLI-facing review guidance**

In `runtime/scripts/run_research_session.py`, replace any ordinary-path strings like:

```python
"Run ./.qros/bin/qros-review to complete deterministic review closure."
```

with:

```python
"Wait for the independent reviewer to write review/final_review.yaml, then continue from qros-research-session."
```

- [ ] **Step 5: Run the focused test to verify it passes**

Run:

```bash
python -m pytest tests/session/test_lineage_lock_session_status.py::test_session_routes_fix_required_and_retry_differently_from_final_review -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/research_session.py runtime/scripts/run_research_session.py tests/session/test_lineage_lock_session_status.py
git commit -m "feat: route session state from final review verdicts"
```

---

### Task 4: Remove Ordinary-Path Dependencies On Receipt/Raw/Closer And Refresh Coverage

**Files:**
- Modify: `runtime/tools/review_skillgen/protocol_validator.py`
- Modify: `tests/review/test_review_engine_csf_metric_gates.py`
- Modify: `tests/agent_eval/test_agent_behavior_eval_case_contract.py`
- Modify: `docs/guides/how-qros-works.md`

- [ ] **Step 1: Write the failing ordinary-path validator test**

Add this test to `tests/review/test_review_engine_csf_metric_gates.py`:

```python
def test_protocol_validator_accepts_final_review_without_receipt_raw_or_closer(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "lineage_a" / "03_csf_signal_ready"
    review_dir = stage_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "lineage_id": "lineage_a",
        "stage_id": "csf_signal_ready",
        "reviewer_identity": "reviewer",
        "reviewer_agent_id": "agent-1",
        "reviewed_artifact_paths": ["author/formal/factor_contract.md"],
        "reviewed_program_path": "program/cross_sectional_factor/signal_ready/run_stage.py",
        "reviewed_artifact_digest": "sha256:a",
        "reviewed_program_digest": "sha256:b",
        "verdict": "CONDITIONAL PASS",
        "review_summary": "volume and liquidity components remain coupled",
        "blocking_findings": [],
        "reservation_findings": ["volume and liquidity components remain coupled"],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "rollback_stage": None,
        "downstream_permissions": ["may proceed to csf_train_freeze confirmation"],
        "recommended_next_action": "advance to next-stage confirmation",
    }
    (review_dir / "final_review.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_review_protocol_state(stage_dir)
    assert result["status"] == "PASS"
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/review/test_review_engine_csf_metric_gates.py::test_protocol_validator_accepts_final_review_without_receipt_raw_or_closer -q
```

Expected: FAIL because protocol validation still requires `reviewer_receipt.yaml`, `reviewer_findings.raw.yaml`, and/or `adversarial_review_result.yaml`.

- [ ] **Step 3: Simplify protocol validation**

In `runtime/tools/review_skillgen/protocol_validator.py`, replace the active-cycle ordinary-path requirement:

```python
raw_path = review_result_dir / "reviewer_findings.raw.yaml"
...
"reviewer_findings.raw.yaml is required for active-cycle review closure"
```

with:

```python
final_review_path = stage_dir / "review" / "final_review.yaml"
if not final_review_path.exists():
    errors.append("review/final_review.yaml is required for ordinary review completion")
else:
    load_final_review(final_review_path)
```

If the validator currently expects `adversarial_review_result.yaml`, change it to:

```python
canonical_review_path = stage_dir / "review" / "final_review.yaml"
```

and update any downstream comparison names accordingly.

- [ ] **Step 4: Update docs and agent-eval contract**

In `docs/guides/how-qros-works.md`, replace the ordinary review path paragraph with:

```markdown
普通 review 路径不再要求 reviewer 先写 raw findings 再由 closer 合并。独立 reviewer 子代理直接写 `review/final_review.yaml`。主线程读取该文件的 `verdict`，继续 author-fix、next-stage confirmation 或 failure handling。
```

In `tests/agent_eval/test_agent_behavior_eval_case_contract.py`, change forbidden/expected substrings so ordinary review success cases no longer require:

```python
"qros-review-preflight",
"qros-review-cycle prepare",
```

as mandatory terminal actions. Replace with:

```python
"review/final_review.yaml",
```

for direct-review completion assertions.

- [ ] **Step 5: Run focused regression checks**

Run:

```bash
python -m pytest tests/review/test_review_engine_csf_metric_gates.py::test_protocol_validator_accepts_final_review_without_receipt_raw_or_closer -q
python -m pytest tests/agent_eval/test_agent_behavior_eval_case_contract.py -q
python -m pytest tests/session/test_research_session_assets.py tests/session/test_lineage_lock_session_status.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_skillgen/protocol_validator.py tests/review/test_review_engine_csf_metric_gates.py tests/agent_eval/test_agent_behavior_eval_case_contract.py docs/guides/how-qros-works.md
git commit -m "feat: retire ordinary review raw closer chain"
```

---

## Self-Review

### Spec Coverage

- Reviewer remains independent: covered by Tasks 2 and 4 handoff/protocol edits.
- Reviewer cannot modify `author/formal/*`: covered by Task 2 docs/skill updates and reviewer write-target narrowing.
- Reviewer writes one final machine-readable review artifact: covered by Tasks 1 and 2.
- Main thread consumes verdict and continues fixing: covered by Task 3.
- `FIX_REQUIRED` vs `RETRY` diverge hard: covered by Task 3.
- Receipt/raw/closer removed from ordinary path: covered by Tasks 1, 2, and 4.

### Placeholder Scan

- No `TODO`, `TBD`, or “implement later” markers.
- Every task names exact files and concrete commands.
- Every code-changing step includes the intended code shape.

### Type Consistency

- The canonical file name is consistently `review/final_review.yaml`.
- The canonical verdict field is consistently `verdict`.
- The governance fields are consistently `allowed_modifications`, `rollback_stage`, `downstream_permissions`, and `recommended_next_action`.
