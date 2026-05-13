# QROS Review Boundary Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce fail-closed QROS review boundaries so launcher, reviewer, and closer roles cannot drift or silently disagree.

**Architecture:** Add canonical review context to request/receipt/handoff artifacts, require reviewer raw findings to attest identity and inspected paths, and make `qros-review` produce a closer-owned canonical result after deterministic gates. Identity/path violations fail before closure; deterministic hard-gate failures close as non-advancing verdicts with final blocking findings written to disk.

**Tech Stack:** Python 3.12/3.13, PyYAML, pytest, existing QROS runtime helpers under `runtime/tools/review_skillgen/`.

---

## File Structure

- Modify `runtime/tools/review_skillgen/adversarial_review_contract.py`
  - Add canonical path fields to request, handoff manifest, receipt loaders/validators.
  - Keep compatibility narrow: new active review cycles must include these fields.
- Modify `runtime/tools/review_skillgen/review_session_runtime.py`
  - Include launcher boundary and canonical paths in reviewer handoff prompt.
- Modify `runtime/tools/review_skillgen/review_result_writer.py`
  - Require `reviewer_session_id` and reviewed path attestations in `reviewer_findings.raw.yaml`.
  - Normalize raw reviewer projection into `review_findings.yaml`.
- Modify `runtime/tools/review_skillgen/review_engine.py`
  - Separate deterministic gate findings from reviewer findings.
  - Rewrite canonical `adversarial_review_result.yaml` after closer merges gates.
  - Detect hard-gate downgrade and projection drift.
- Modify `runtime/tools/review_skillgen/protocol_validator.py`
  - Treat stale canonical result without fresh raw findings as projection drift for active cycles.
- Test `tests/review/test_adversarial_review_runtime.py`
  - Identity collision, raw schema, repo root mismatch, handoff prompt.
- Test `tests/review/test_review_engine_csf_metric_gates.py`
  - Hard gate downgrade and canonical result consistency.
- Modify docs/skills only if runtime field names or review handoff text changes user-facing protocol:
  - `docs/guides/qros-review-shared-protocol.md`
  - `skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md`

---

### Task 1: Add Canonical Review Context To Request, Receipt, And Handoff

**Files:**
- Modify: `runtime/tools/review_skillgen/adversarial_review_contract.py`
- Modify: `runtime/tools/review_skillgen/review_session_runtime.py`
- Test: `tests/review/test_adversarial_review_runtime.py`

- [ ] **Step 1: Write failing test for canonical fields in request/receipt/handoff**

Add this test near the existing review-cycle preparation tests in `tests/review/test_adversarial_review_runtime.py`:

```python
def test_prepare_review_cycle_records_canonical_context_and_handoff_paths(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    status = run_research_session(outputs_root=lineage_root.parent, lineage_id=lineage_root.name, continue_mode=True)
    assert status.current_stage in {"mandate_review_confirmation_pending", "mandate_review"}

    from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff

    payload = prepare_review_cycle_for_handoff(
        cwd=stage_dir,
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="reviewer-agent",
        reviewer_session_id="reviewer-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="leader-thread",
        reviewer_agent_id="reviewer-child-agent",
        host="codex",
    )

    request = load_adversarial_review_request(stage_dir / "review" / "request" / "adversarial_review_request.yaml")
    receipt = yaml.safe_load((stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8"))
    handoff = payload["reviewer_handoff_prompt"]

    expected_project_root = str(lineage_root.parent.parent.resolve())
    expected_lineage_root = str(lineage_root.resolve())
    expected_stage_dir = str(stage_dir.resolve())

    assert request["project_root"] == expected_project_root
    assert request["lineage_root"] == expected_lineage_root
    assert request["stage_dir"] == expected_stage_dir
    assert request["author_formal_dir"] == str((stage_dir / "author" / "formal").resolve())
    assert request["review_request_dir"] == str((stage_dir / "review" / "request").resolve())
    assert request["review_result_dir"] == str((stage_dir / "review" / "result").resolve())
    assert receipt["project_root"] == expected_project_root
    assert receipt["lineage_root"] == expected_lineage_root
    assert receipt["stage_dir"] == expected_stage_dir
    assert "Launcher boundary:" in handoff
    assert "Do not write reviewer_findings.raw.yaml from the launcher conversation." in handoff
    assert f"Active research repo root: {expected_project_root}" in handoff
    assert f"Lineage root: {expected_lineage_root}" in handoff
    assert f"Stage dir: {expected_stage_dir}" in handoff
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py::test_prepare_review_cycle_records_canonical_context_and_handoff_paths -q
```

Expected: fails because `project_root`, `lineage_root`, and `stage_dir` are not yet loaded from request/receipt or printed in handoff.

- [ ] **Step 3: Add canonical context helpers**

In `runtime/tools/review_skillgen/adversarial_review_contract.py`, add these helpers near `_stage_dir_from_request_path` or other path helpers:

```python
def _canonical_review_context(stage_dir: Path) -> dict[str, str]:
    resolved_stage_dir = stage_dir.resolve()
    lineage_root = resolved_stage_dir.parent
    project_root = lineage_root.parent.parent
    return {
        "project_root": str(project_root),
        "lineage_root": str(lineage_root),
        "stage_dir": str(resolved_stage_dir),
        "author_formal_dir": str((resolved_stage_dir / "author" / "formal").resolve()),
        "review_request_dir": str((resolved_stage_dir / "review" / "request").resolve()),
        "review_result_dir": str((resolved_stage_dir / "review" / "result").resolve()),
    }
```

Update `_build_handoff_manifest_payload(...)` signature to accept `stage_dir: Path`, then include:

```python
    payload.update(_canonical_review_context(stage_dir))
```

Update `_write_handoff_manifest(...)` call to pass `stage_dir=stage_dir`.

In `ensure_adversarial_review_request(...)`, add:

```python
    payload.update(_canonical_review_context(stage_dir))
```

In `load_adversarial_review_request(...)`, add these required fields to `data`:

```python
        "project_root": _require_string(payload, "project_root", path=request_path),
        "lineage_root": _require_string(payload, "lineage_root", path=request_path),
        "stage_dir": _require_string(payload, "stage_dir", path=request_path),
        "author_formal_dir": _require_string(payload, "author_formal_dir", path=request_path),
        "review_request_dir": _require_string(payload, "review_request_dir", path=request_path),
        "review_result_dir": _require_string(payload, "review_result_dir", path=request_path),
```

After loading `data`, validate the paths:

```python
    expected_context = _canonical_review_context(_stage_dir_from_request_path(request_path))
    for key, expected in expected_context.items():
        if data[key] != expected:
            raise ValueError(f"{request_path}: {key} does not match canonical review context")
```

In `load_reviewer_handoff_manifest(...)`, load and require the same six fields.

In the manifest/request comparison loop, include the six canonical context keys:

```python
        "project_root",
        "lineage_root",
        "stage_dir",
        "author_formal_dir",
        "review_request_dir",
        "review_result_dir",
```

- [ ] **Step 4: Mirror canonical context into receipt**

In `issue_reviewer_receipt(...)`, after `request_payload = load_adversarial_review_request(request_path)`, add to `payload`:

```python
        "project_root": request_payload["project_root"],
        "lineage_root": request_payload["lineage_root"],
        "stage_dir": request_payload["stage_dir"],
```

In `load_reviewer_receipt(...)`, require these fields:

```python
        "project_root": _require_string(payload, "project_root", path=receipt_path),
        "lineage_root": _require_string(payload, "lineage_root", path=receipt_path),
        "stage_dir": _require_string(payload, "stage_dir", path=receipt_path),
```

In `validate_receipt_contract(...)`, add:

```python
    for key in ("project_root", "lineage_root", "stage_dir"):
        if receipt_payload[key] != request_payload[key]:
            raise ValueError(f"reviewer_receipt.yaml {key} does not match adversarial_review_request.yaml")
```

- [ ] **Step 5: Update handoff prompt**

In `runtime/tools/review_skillgen/review_session_runtime.py`, update `_reviewer_handoff_prompt(...)` to insert this block before `Hard constraints:`:

```python
        "Launcher boundary:",
        "- The current/main conversation is the launcher, not the reviewer.",
        "- Do not write reviewer_findings.raw.yaml from the launcher conversation.",
        "- Send this handoff to an independent reviewer/subagent.",
        "",
        f"Active research repo root: {payload['request_payload']['project_root']}",
        f"Lineage root: {payload['request_payload']['lineage_root']}",
        f"Stage dir: {payload['request_payload']['stage_dir']}",
        "The QROS governance repo is not the active research repo unless the canonical paths above point there.",
        "",
```

If `_build_review_cycle_payload(...)` does not currently pass `request_payload` into the returned payload, add:

```python
        "request_payload": request_payload,
```

- [ ] **Step 6: Run focused test**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py::test_prepare_review_cycle_records_canonical_context_and_handoff_paths -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add runtime/tools/review_skillgen/adversarial_review_contract.py runtime/tools/review_skillgen/review_session_runtime.py tests/review/test_adversarial_review_runtime.py
git commit -m "feat: bind reviews to canonical context"
```

---

### Task 2: Require Reviewer Raw Findings Attestation

**Files:**
- Modify: `runtime/tools/review_skillgen/review_result_writer.py`
- Modify: `runtime/tools/review_skillgen/adversarial_review_contract.py`
- Test: `tests/review/test_adversarial_review_runtime.py`

- [ ] **Step 1: Add failing tests for raw identity and path validation**

In `tests/review/test_adversarial_review_runtime.py`, update `_write_raw_reviewer_findings(...)` helper signature and payload:

```python
def _write_raw_reviewer_findings(
    stage_dir: Path,
    *,
    review_loop_outcome: str,
    reviewer_session_id: str = "reviewer-session",
    reviewer_agent_id: str = "reviewer-child-agent",
    reviewed_project_root: str | None = None,
    reviewed_lineage_root: str | None = None,
    reviewed_stage_dir: str | None = None,
    hard_gate_findings_acknowledged: bool = True,
    blocking_findings: list[str] | None = None,
    reservation_findings: list[str] | None = None,
    info_findings: list[str] | None = None,
    residual_risks: list[str] | None = None,
    allowed_modifications: list[str] | None = None,
    downstream_permissions: list[str] | None = None,
    rollback_stage: str | None = None,
) -> None:
    lineage_root = stage_dir.parent
    project_root = lineage_root.parent.parent
    payload = {
        "review_cycle_id": _request_review_cycle_id(stage_dir),
        "reviewer_session_id": reviewer_session_id,
        "reviewer_agent_id": reviewer_agent_id,
        "reviewed_project_root": reviewed_project_root or str(project_root.resolve()),
        "reviewed_lineage_root": reviewed_lineage_root or str(lineage_root.resolve()),
        "reviewed_stage_dir": reviewed_stage_dir or str(stage_dir.resolve()),
        "hard_gate_findings_acknowledged": hard_gate_findings_acknowledged,
        "review_loop_outcome": review_loop_outcome,
        "blocking_findings": blocking_findings or [],
        "reservation_findings": reservation_findings or [],
        "info_findings": info_findings or [],
        "residual_risks": residual_risks or [],
        "allowed_modifications": allowed_modifications or [],
        "downstream_permissions": downstream_permissions or [],
    }
    if rollback_stage:
        payload["rollback_stage"] = rollback_stage
    _write_yaml(stage_dir / "review" / "result" / "reviewer_findings.raw.yaml", payload)
```

Add tests:

```python
def test_run_stage_review_rejects_raw_findings_with_launcher_session(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir, reviewer_session_id="launcher-session")
    _write_raw_reviewer_findings(stage_dir, review_loop_outcome="CLOSURE_READY_PASS", reviewer_session_id="launcher-session")

    with pytest.raises(ValueError, match="REVIEWER_IDENTITY_COLLISION"):
        run_stage_review(cwd=stage_dir, reviewer_identity="reviewer-agent", reviewer_session_id="launcher-session")


def test_run_stage_review_rejects_raw_findings_session_mismatch(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir, reviewer_session_id="reviewer-session")
    _write_raw_reviewer_findings(stage_dir, review_loop_outcome="CLOSURE_READY_PASS", reviewer_session_id="other-session")

    with pytest.raises(ValueError, match="REVIEWER_IDENTITY_COLLISION"):
        run_stage_review(cwd=stage_dir, reviewer_identity="reviewer-agent", reviewer_session_id="reviewer-session")


def test_run_stage_review_rejects_raw_findings_context_root_mismatch(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    wrong_lineage_root = tmp_path / "wrong-repo" / "outputs" / "topic_a"
    _write_raw_reviewer_findings(
        stage_dir,
        review_loop_outcome="CLOSURE_READY_PASS",
        reviewed_lineage_root=str(wrong_lineage_root.resolve()),
    )

    with pytest.raises(ValueError, match="REVIEW_CONTEXT_ROOT_MISMATCH"):
        run_stage_review(cwd=stage_dir, reviewer_identity="reviewer-agent", reviewer_session_id="reviewer-session")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py::test_run_stage_review_rejects_raw_findings_with_launcher_session tests/review/test_adversarial_review_runtime.py::test_run_stage_review_rejects_raw_findings_session_mismatch tests/review/test_adversarial_review_runtime.py::test_run_stage_review_rejects_raw_findings_context_root_mismatch -q
```

Expected: fail because raw schema does not yet require session/path fields.

- [ ] **Step 3: Implement raw schema and validation**

In `runtime/tools/review_skillgen/review_result_writer.py`, add constants:

```python
REVIEWER_IDENTITY_COLLISION = "REVIEWER_IDENTITY_COLLISION"
REVIEW_CONTEXT_ROOT_MISMATCH = "REVIEW_CONTEXT_ROOT_MISMATCH"
```

In `_load_raw_reviewer_findings(...)`, include required fields:

```python
    return {
        "review_cycle_id": _require_raw_string(payload, "review_cycle_id", path=path),
        "reviewer_session_id": _require_raw_string(payload, "reviewer_session_id", path=path),
        "reviewer_agent_id": _require_raw_string(payload, "reviewer_agent_id", path=path),
        "reviewed_project_root": _require_raw_string(payload, "reviewed_project_root", path=path),
        "reviewed_lineage_root": _require_raw_string(payload, "reviewed_lineage_root", path=path),
        "reviewed_stage_dir": _require_raw_string(payload, "reviewed_stage_dir", path=path),
        "hard_gate_findings_acknowledged": bool(payload.get("hard_gate_findings_acknowledged") is True),
        "review_loop_outcome": outcome,
        "blocking_findings": _require_raw_string_list(payload, "blocking_findings", path=path),
        "reservation_findings": _require_raw_string_list(payload, "reservation_findings", path=path),
        "info_findings": _require_raw_string_list(payload, "info_findings", path=path),
        "residual_risks": _require_raw_string_list(payload, "residual_risks", path=path),
        "allowed_modifications": _require_raw_string_list(payload, "allowed_modifications", path=path),
        "downstream_permissions": _require_raw_string_list(payload, "downstream_permissions", path=path),
        "rollback_stage": payload.get("rollback_stage"),
        "review_summary": payload.get("review_summary"),
    }
```

In `ensure_runtime_review_result(...)`, after cycle/agent checks, add:

```python
        if raw_payload["reviewer_session_id"] != receipt_payload["requested_reviewer_session_id"]:
            raise ValueError(f"{REVIEWER_IDENTITY_COLLISION}: raw findings reviewer_session_id does not match reviewer_receipt.yaml")
        if raw_payload["reviewer_session_id"] == receipt_payload["launcher_session_id"]:
            raise ValueError(f"{REVIEWER_IDENTITY_COLLISION}: reviewer_session_id must differ from launcher_session_id")
        if raw_payload["reviewer_agent_id"] != receipt_payload["reviewer_agent_id"]:
            raise ValueError(f"{REVIEWER_IDENTITY_COLLISION}: raw findings reviewer_agent_id does not match reviewer_receipt.yaml")
        expected_paths = {
            "reviewed_project_root": request_payload["project_root"],
            "reviewed_lineage_root": request_payload["lineage_root"],
            "reviewed_stage_dir": request_payload["stage_dir"],
        }
        for key, expected in expected_paths.items():
            if raw_payload[key] != expected:
                raise ValueError(f"{REVIEW_CONTEXT_ROOT_MISMATCH}: raw findings {key} does not match active review request")
```

Add these fields to `result_payload`:

```python
            "reviewed_project_root": raw_payload["reviewed_project_root"],
            "reviewed_lineage_root": raw_payload["reviewed_lineage_root"],
            "reviewed_stage_dir": raw_payload["reviewed_stage_dir"],
            "hard_gate_findings_acknowledged": raw_payload["hard_gate_findings_acknowledged"],
```

- [ ] **Step 4: Allow canonical result loader to preserve reviewed path fields**

In `runtime/tools/review_skillgen/adversarial_review_contract.py`, update `load_adversarial_review_result(...)` to optionally include these fields when present:

```python
    for optional_key in (
        "reviewed_project_root",
        "reviewed_lineage_root",
        "reviewed_stage_dir",
        "hard_gate_findings_acknowledged",
        "hard_gate_downgrade_detected",
    ):
        if optional_key in payload:
            data[optional_key] = payload[optional_key]
```

In `validate_result_against_request(...)`, add when fields exist:

```python
    expected_paths = {
        "reviewed_project_root": request_payload["project_root"],
        "reviewed_lineage_root": request_payload["lineage_root"],
        "reviewed_stage_dir": request_payload["stage_dir"],
    }
    for key, expected in expected_paths.items():
        if result_payload.get(key) != expected:
            raise ValueError("adversarial_review_result.yaml reviewed context does not match active request")
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py::test_run_stage_review_rejects_raw_findings_with_launcher_session tests/review/test_adversarial_review_runtime.py::test_run_stage_review_rejects_raw_findings_session_mismatch tests/review/test_adversarial_review_runtime.py::test_run_stage_review_rejects_raw_findings_context_root_mismatch -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_skillgen/review_result_writer.py runtime/tools/review_skillgen/adversarial_review_contract.py tests/review/test_adversarial_review_runtime.py
git commit -m "feat: require reviewer findings attestation"
```

---

### Task 3: Rewrite Canonical Review Result After Deterministic Gates

**Files:**
- Modify: `runtime/tools/review_skillgen/review_engine.py`
- Modify: `runtime/tools/review_skillgen/protocol_validator.py`
- Test: `tests/review/test_review_engine_csf_metric_gates.py`
- Test: `tests/review/test_adversarial_review_runtime.py`

- [ ] **Step 1: Write failing hard-gate canonical result test**

In `tests/review/test_review_engine_csf_metric_gates.py`, extend `test_run_stage_review_blocks_csf_test_evidence_when_rank_ic_is_non_positive` after the payload assertions:

```python
    result_payload = yaml.safe_load(
        (stage_dir / "review" / "result" / "adversarial_review_result.yaml").read_text(encoding="utf-8")
    )
    state_payload = yaml.safe_load(
        (stage_dir / "review" / "state" / "review_runtime_state.yaml").read_text(encoding="utf-8")
    )
    closure_payload = yaml.safe_load(
        (stage_dir / "review" / "closure" / "stage_gate_review.yaml").read_text(encoding="utf-8")
    )
    assert result_payload["review_loop_outcome"] == "CLOSURE_READY_RETRY"
    assert result_payload["final_verdict"] == "RETRY"
    assert any("mean_rank_ic" in item for item in result_payload["blocking_findings"])
    assert state_payload["last_review_verdict"] == "RETRY"
    assert closure_payload["final_verdict"] == "RETRY"
```

Add a second test:

```python
def test_run_stage_review_marks_hard_gate_downgrade_when_reviewer_puts_gate_in_reservation(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_test_evidence",
        stage_dir_name="05_csf_test_evidence",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_json(
        formal_dir / "rank_ic_summary.json",
        {
            "variant_id": "mom_20d",
            "factor_role": "standalone_alpha",
            "mean_rank_ic": -0.031225,
            "median_rank_ic": -0.02,
            "num_dates": 140,
        },
    )
    (formal_dir / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    (formal_dir / "csf_test_gate_decision.md").write_text("metric gate snapshot\n", encoding="utf-8")
    _write_review_request_and_result(stage_dir, stage="csf_test_evidence")
    raw_path = stage_dir / "review" / "result" / "reviewer_findings.raw.yaml"
    raw_path.write_text(
        yaml.safe_dump(
            {
                "review_cycle_id": "csf_test_evidence-cycle-1",
                "reviewer_session_id": "review-session",
                "reviewer_agent_id": "reviewer-child-agent",
                "reviewed_project_root": str(stage_dir.parent.parent.parent.resolve()),
                "reviewed_lineage_root": str(stage_dir.parent.resolve()),
                "reviewed_stage_dir": str(stage_dir.resolve()),
                "hard_gate_findings_acknowledged": True,
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": ["CSF-TEST-METRIC-001 mean_rank_ic is negative but documented"],
                "info_findings": [],
                "residual_risks": [],
                "allowed_modifications": [],
                "downstream_permissions": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    result_payload = yaml.safe_load((stage_dir / "review" / "result" / "adversarial_review_result.yaml").read_text(encoding="utf-8"))
    assert payload["final_verdict"] == "RETRY"
    assert result_payload["final_verdict"] == "RETRY"
    assert result_payload["hard_gate_downgrade_detected"] is True
    assert any("CSF-TEST-METRIC-001" in item for item in result_payload["blocking_findings"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/review/test_review_engine_csf_metric_gates.py::test_run_stage_review_blocks_csf_test_evidence_when_rank_ic_is_non_positive tests/review/test_review_engine_csf_metric_gates.py::test_run_stage_review_marks_hard_gate_downgrade_when_reviewer_puts_gate_in_reservation -q
```

Expected: fail because `adversarial_review_result.yaml` remains reviewer-projection shaped.

- [ ] **Step 3: Add canonical result writer helper**

In `runtime/tools/review_skillgen/review_engine.py`, add near `_resolve_verdict(...)`:

```python
HARD_GATE_DOWNGRADED = "HARD_GATE_DOWNGRADED"


def _detect_hard_gate_downgrade(
    *,
    deterministic_gate_findings: list[str],
    review_result: dict[str, Any],
    reviewer_findings: dict[str, Any],
    final_verdict: str | None,
) -> bool:
    if final_verdict not in {"RETRY", "NO-GO", "CHILD LINEAGE"}:
        return False
    if not deterministic_gate_findings:
        return False
    raw_pass_like = review_result["review_loop_outcome"] in {
        "CLOSURE_READY_PASS",
        "CLOSURE_READY_CONDITIONAL_PASS",
    }
    recommended_pass_like = reviewer_findings.get("recommended_verdict") in {"PASS", "CONDITIONAL PASS"}
    reviewer_text = "\n".join(
        list(review_result.get("reservation_findings", []))
        + list(review_result.get("info_findings", []))
        + list(reviewer_findings.get("reservation_findings", []))
        + list(reviewer_findings.get("info_findings", []))
    )
    mentions_gate = any(item.split(":", 1)[0] in reviewer_text for item in deterministic_gate_findings)
    return bool((raw_pass_like or recommended_pass_like) and mentions_gate)


def _write_canonical_review_result(
    *,
    review_result_dir: Path,
    review_result: dict[str, Any],
    final_verdict: str | None,
    review_loop_outcome: str,
    blocking_findings: list[str],
    reservation_findings: list[str],
    info_findings: list[str],
    residual_risks: list[str],
    hard_gate_downgrade_detected: bool,
) -> None:
    canonical = dict(review_result)
    canonical["final_verdict"] = final_verdict
    canonical["review_loop_outcome"] = review_loop_outcome
    canonical["blocking_findings"] = list(blocking_findings)
    canonical["reservation_findings"] = list(reservation_findings)
    canonical["info_findings"] = list(info_findings)
    canonical["residual_risks"] = list(residual_risks)
    canonical["hard_gate_downgrade_detected"] = hard_gate_downgrade_detected
    if hard_gate_downgrade_detected:
        canonical["hard_gate_downgrade_code"] = HARD_GATE_DOWNGRADED
    (review_result_dir / "adversarial_review_result.yaml").write_text(
        yaml.safe_dump(canonical, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
```

- [ ] **Step 4: Track deterministic gate findings separately**

In `run_stage_review(...)`, replace the current direct metric-gate extension:

```python
    blocking_findings.extend(
        _check_metric_gates(
            lineage_root=lineage_root,
            author_formal_dir=author_formal_dir,
            stage_contract=stage_contract,
        )
    )
```

with:

```python
    deterministic_gate_findings = _check_metric_gates(
        lineage_root=lineage_root,
        author_formal_dir=author_formal_dir,
        stage_contract=stage_contract,
    )
    blocking_findings.extend(deterministic_gate_findings)
```

After `_resolve_verdict(...)`, add:

```python
    hard_gate_downgrade_detected = _detect_hard_gate_downgrade(
        deterministic_gate_findings=deterministic_gate_findings,
        review_result=review_result,
        reviewer_findings=reviewer_findings,
        final_verdict=final_verdict,
    )
```

Before the `if review_loop_outcome == FIX_REQUIRED_OUTCOME:` block returns, call `_write_canonical_review_result(...)` for non-`FIX_REQUIRED` paths only. For the normal closure path, call it immediately before `write_closure_artifacts(...)`:

```python
    _write_canonical_review_result(
        review_result_dir=review_result_dir,
        review_result=review_result,
        final_verdict=final_verdict,
        review_loop_outcome=review_loop_outcome,
        blocking_findings=blocking_findings,
        reservation_findings=reservation_findings,
        info_findings=info_findings,
        residual_risks=residual_risks,
        hard_gate_downgrade_detected=hard_gate_downgrade_detected,
    )
```

Ensure `common_payload` and final returned payload include:

```python
        "hard_gate_downgrade_detected": hard_gate_downgrade_detected,
```

- [ ] **Step 5: Make stale canonical projection fail closed**

In `runtime/tools/review_skillgen/protocol_validator.py`, before `ensure_runtime_review_result(...)`, add:

```python
    raw_path = review_result_dir / "reviewer_findings.raw.yaml"
    if result_path.exists() and not raw_path.exists():
        raise ValueError(
            "REVIEW_RESULT_PROJECTION_DRIFT: reviewer_findings.raw.yaml is required for active-cycle review closure"
        )
```

This preserves the existing `ensure_runtime_review_result(...)` drift behavior but surfaces the stable error code earlier.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python -m pytest tests/review/test_review_engine_csf_metric_gates.py::test_run_stage_review_blocks_csf_test_evidence_when_rank_ic_is_non_positive tests/review/test_review_engine_csf_metric_gates.py::test_run_stage_review_marks_hard_gate_downgrade_when_reviewer_puts_gate_in_reservation -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add runtime/tools/review_skillgen/review_engine.py runtime/tools/review_skillgen/protocol_validator.py tests/review/test_review_engine_csf_metric_gates.py
git commit -m "feat: write canonical review verdicts"
```

---

### Task 4: Update Protocol Docs And Review Skill Guidance

**Files:**
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md`
- Test: `tests/docs/test_install_docs.py`
- Test: `tests/skills/test_stage_entry_guard_guidance.py` if guidance tests need new wording coverage

- [ ] **Step 1: Add docs regression assertions**

In `tests/docs/test_install_docs.py`, add a test:

```python
def test_review_protocol_documents_fail_closed_boundaries() -> None:
    protocol = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")
    csf_review_skill = Path("skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md").read_text(encoding="utf-8")
    combined = protocol + "\n" + csf_review_skill
    assert "REVIEWER_IDENTITY_COLLISION" in protocol
    assert "REVIEW_CONTEXT_ROOT_MISMATCH" in protocol
    assert "HARD_GATE_DOWNGRADED" in protocol
    assert "REVIEW_RESULT_PROJECTION_DRIFT" in protocol
    assert "reviewer_findings.raw.yaml" in combined
    assert "mean_rank_ic <= 0" in csf_review_skill
    assert "不得降级为 reservation" in csf_review_skill
```

- [ ] **Step 2: Run docs test to verify it fails**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py::test_review_protocol_documents_fail_closed_boundaries -q
```

Expected: fail because the new error codes and wording are not documented yet.

- [ ] **Step 3: Update shared review protocol**

In `docs/guides/qros-review-shared-protocol.md`, under `## 执行门禁`, add:

```markdown
### Fail-closed review boundary

`qros-review` 必须把 launcher、reviewer 和 closer 分成三个不可互相替代的角色。

- `REVIEWER_IDENTITY_COLLISION`：raw findings 的 `reviewer_session_id` 缺失、等于 `launcher_session_id`，或与 `reviewer_receipt.yaml` 不一致时，拒绝 closure。
- `REVIEW_CONTEXT_ROOT_MISMATCH`：raw findings 声明的 `reviewed_project_root`、`reviewed_lineage_root` 或 `reviewed_stage_dir` 与 active request 的 canonical path 不一致时，拒绝 closure。
- `HARD_GATE_DOWNGRADED`：deterministic hard gate 失败但 reviewer 把它写成 reservation/info 且给出 pass-like outcome 时，最终 canonical result 必须是 non-advancing verdict，不能 PASS。
- `REVIEW_RESULT_PROJECTION_DRIFT`：active cycle 中存在 stale `adversarial_review_result.yaml` 但没有 fresh `reviewer_findings.raw.yaml` 时，拒绝继续关闭。

`adversarial_review_result.yaml` 是 closer 合并 reviewer findings 与 deterministic gates 后的 canonical result。它必须与 stdout、`review_runtime_state.yaml` 和 `review/closure/*` 的最终 verdict 一致。
```

- [ ] **Step 4: Update CSF test evidence review guidance**

In `skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md`, under the checklist item for `mean_rank_ic <= 0`, add:

```markdown
硬门禁说明：`standalone_alpha` 场景下，`mean_rank_ic <= 0` 是 blocking finding，必须写入 `blocking_findings`；不得降级为 reservation / info，也不得建议 `PASS` 或 `CONDITIONAL PASS` 后让 backtest 再看。
```

- [ ] **Step 5: Run docs tests**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py::test_review_protocol_documents_fail_closed_boundaries -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add docs/guides/qros-review-shared-protocol.md skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md tests/docs/test_install_docs.py
git commit -m "docs: document fail-closed review boundaries"
```

---

### Task 5: Run Integration Regression And Full Verification

**Files:**
- No new files.
- Use all modified files from Tasks 1-4.

- [ ] **Step 1: Run review focused tests**

Run:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py tests/review/test_review_engine_csf_metric_gates.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run session regression tests**

Run:

```bash
python -m pytest tests/session/test_run_research_session_script.py -q
```

Expected: all tests pass. Pay attention to PASS boundary output, failure routing, and review confirmation tests.

- [ ] **Step 3: Run docs/bootstrap minimum**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected: all tests pass.

- [ ] **Step 4: Run smoke tier**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: command exits 0.

- [ ] **Step 5: Run full-smoke tier**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: command exits 0. This is mandatory because review closure and failure routing semantics changed.

- [ ] **Step 6: Inspect git status**

Run:

```bash
git status --short
```

Expected: only intended source, docs, and tests are modified before final commit; no generated runtime output or active research artifacts are present.

- [ ] **Step 7: Final commit**

```bash
git add runtime/tools/review_skillgen/adversarial_review_contract.py runtime/tools/review_skillgen/review_session_runtime.py runtime/tools/review_skillgen/review_result_writer.py runtime/tools/review_skillgen/review_engine.py runtime/tools/review_skillgen/protocol_validator.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_engine_csf_metric_gates.py tests/docs/test_install_docs.py docs/guides/qros-review-shared-protocol.md skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md
git commit -m "feat: harden qros review boundaries"
```

---

## Self-Review Notes

- Spec coverage:
  - Reviewer independence is covered by Tasks 1 and 2.
  - Repo root drift is covered by Tasks 1 and 2.
  - Hard gate downgrade is covered by Task 3.
  - Canonical result consistency is covered by Task 3.
  - Docs and user-facing guidance are covered by Task 4.
  - Required focused, smoke, and full-smoke verification are covered by Task 5.
- Placeholder scan:
  - This plan intentionally contains no unfinished placeholder markers or unspecified implementation steps.
- Type consistency:
  - New field names are consistent across request, receipt, raw findings, canonical result, and tests:
    `project_root`, `lineage_root`, `stage_dir`, `reviewer_session_id`,
    `reviewed_project_root`, `reviewed_lineage_root`, `reviewed_stage_dir`.
