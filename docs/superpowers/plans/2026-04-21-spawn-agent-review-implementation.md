# Spawn-Agent Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the manual second-Codex review flow with stage-specific review skills that launch a Codex reviewer child via `spawn_agent`, wait for `review/result/*`, and then run deterministic closure.

**Architecture:** Keep `qros-mandate-review` and the other stage-specific review skills as the user-facing review entrypoints, but move shared spawn/wait/closure orchestration into runtime helpers. The helper will register a spawned-agent review cycle, generate a strict reviewer-child handoff, bind the proof chain on disk, and let `qros-review` remain the only deterministic closer.

**Tech Stack:** Python runtime helpers, generated Markdown skill bundles, YAML review contracts, pytest, existing QROS review engine.

---

### Task 1: Lock Spawned-Agent Runtime Behavior With Tests

**Files:**
- Modify: `tests/review/test_start_review_session.py`
- Modify: `tests/review/test_adversarial_review_runtime.py`
- Modify: `tests/review/test_review_result_writer.py`
- Modify: `tests/review/test_run_stage_review_script.py`

- [ ] **Step 1: Write the failing tests for spawned-agent receipt and closure flow**

```python
def test_start_spawned_review_cycle_writes_spawned_agent_receipt(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    payload = start_spawned_review_cycle(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="launcher-session-1",
        launcher_thread_id="launcher-thread-1",
        spawned_agent_id="reviewer-child-1",
    )

    receipt = yaml.safe_load((stage_dir / "review" / "request" / "spawned_reviewer_receipt.yaml").read_text())
    assert receipt["spawn_mode"] == "spawned_agent"
    assert receipt["spawned_agent_id"] == "reviewer-child-1"
    assert payload["review_cycle_id"] == receipt["review_cycle_id"]


def test_run_stage_review_keeps_spawned_agent_execution_mode_from_receipt(tmp_path: Path) -> None:
    _, stage_dir = _prepare_mandate_stage(tmp_path)
    _write_adversarial_review_request(stage_dir, stage_key="mandate", author_identity="author-agent")
    issue_spawned_reviewer_receipt(
        stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="reviewer-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        spawned_agent_id="reviewer-child-agent",
        spawn_mode="spawned_agent",
    )
    (stage_dir / "review" / "result" / "reviewer_findings.raw.yaml").write_text(
        yaml.safe_dump(
            {
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": ["spawned reviewer path"],
                "residual_risks": [],
                "allowed_modifications": [],
                "downstream_permissions": ["data_ready"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="adversarial-reviewer",
        reviewer_session_id="reviewer-session",
        reviewer_mode="adversarial",
    )

    assert payload["reviewer_execution_mode"] == "spawned_agent"
```

- [ ] **Step 2: Run the focused tests and confirm they fail for the missing spawned-agent path**

Run: `python -m pytest tests/review/test_start_review_session.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_result_writer.py tests/review/test_run_stage_review_script.py -q`

Expected: FAIL because `start_spawned_review_cycle` does not exist yet and the receipt path still defaults to `review_session`.

- [ ] **Step 3: Add the minimal test helpers needed for spawned-agent setup**

```python
def _write_spawned_agent_receipt(stage_dir: Path, *, reviewer_identity: str = "reviewer-agent") -> None:
    issue_spawned_reviewer_receipt(
        stage_dir,
        reviewer_identity=reviewer_identity,
        reviewer_session_id="reviewer-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        spawned_agent_id="reviewer-child-agent",
        spawn_mode="spawned_agent",
    )
```

- [ ] **Step 4: Re-run the focused tests to keep the failure pinned to missing runtime implementation**

Run: `python -m pytest tests/review/test_start_review_session.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_result_writer.py tests/review/test_run_stage_review_script.py -q`

Expected: FAIL only on the new spawned-agent expectations, not on syntax or import errors.

- [ ] **Step 5: Commit the red test state once the failures are correct**

```bash
git add tests/review/test_start_review_session.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_result_writer.py tests/review/test_run_stage_review_script.py
git commit -m "test: lock spawned-agent review runtime behavior"
```

### Task 2: Implement Spawned-Agent Review Runtime Helpers

**Files:**
- Modify: `runtime/tools/review_session_runtime.py`
- Modify: `runtime/tools/review_skillgen/adversarial_review_contract.py`
- Modify: `runtime/tools/review_skillgen/review_runtime_state.py`
- Modify: `runtime/tools/review_skillgen/review_result_writer.py`
- Modify: `runtime/tools/review_skillgen/review_engine.py`

- [ ] **Step 1: Implement the new spawned review cycle entrypoint**

```python
def start_spawned_review_cycle(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
    reviewer_identity: str,
    reviewer_session_id: str,
    launcher_session_id: str,
    launcher_thread_id: str,
    spawned_agent_id: str,
) -> dict[str, Any]:
    context = _stage_dir_for_context(cwd=cwd, explicit_context=explicit_context)
    stage_dir = Path(context["stage_dir"]).resolve()
    lineage_root = Path(context["lineage_root"]).resolve()
    current_stage = detect_session_stage(lineage_root)
    spec = _program_spec_for_session_stage(current_stage)
    if spec is None:
        raise ValueError(f"current_stage {current_stage} is not a reviewable stage")

    archived_paths = _archive_if_stale_or_closed(stage_dir, current_digest=_current_author_digest(stage_dir, spec))
    request_payload = ensure_adversarial_review_request(...)
    state_payload = write_review_runtime_state(...)
    receipt_payload = issue_spawned_reviewer_receipt(
        stage_dir,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id=launcher_session_id,
        launcher_thread_id=launcher_thread_id,
        spawned_agent_id=spawned_agent_id,
        spawn_mode="spawned_agent",
    )
    return {
        "lineage_id": lineage_root.name,
        "stage": spec.stage_id,
        "stage_dir": str(stage_dir),
        "current_stage": current_stage,
        "review_cycle_id": request_payload["review_cycle_id"],
        "request_payload": request_payload,
        "receipt_payload": receipt_payload,
        "review_runtime_state": state_payload,
        "archived_paths": archived_paths,
    }
```

- [ ] **Step 2: Keep the old review-session entrypoint by sharing preflight logic, not by mutating a spawned receipt after the fact**

```python
def _prepare_review_cycle(...):
    ...
    return stage_dir, lineage_root, current_stage, spec, archived_paths, request_payload, state_payload


def start_review_session(...):
    stage_dir, lineage_root, current_stage, spec, archived_paths, request_payload, state_payload = _prepare_review_cycle(...)
    receipt_payload = issue_spawned_reviewer_receipt(
        stage_dir,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id=launcher_session_id,
        launcher_thread_id=launcher_thread_id,
        spawned_agent_id=reviewer_session_id,
        spawn_mode="review_session",
    )
    return {...}
```

- [ ] **Step 3: Update runtime canonicalization to preserve spawned-agent receipts**

```python
if raw_path.exists():
    result_payload = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "reviewer_identity": runtime_identity.reviewer_identity,
        "reviewer_role": runtime_identity.reviewer_role,
        "reviewer_session_id": runtime_identity.reviewer_session_id,
        "reviewer_mode": runtime_identity.reviewer_mode,
        "reviewer_agent_id": receipt_payload["spawned_agent_id"],
        "reviewer_execution_mode": receipt_payload["spawn_mode"],
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        ...
    }
```

- [ ] **Step 4: Run the focused runtime tests and make them pass**

Run: `python -m pytest tests/review/test_start_review_session.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_result_writer.py tests/review/test_run_stage_review_script.py -q`

Expected: PASS with the new spawned-agent receipt path covered end to end.

- [ ] **Step 5: Commit the runtime helper implementation**

```bash
git add runtime/tools/review_session_runtime.py runtime/tools/review_skillgen/adversarial_review_contract.py runtime/tools/review_skillgen/review_runtime_state.py runtime/tools/review_skillgen/review_result_writer.py runtime/tools/review_skillgen/review_engine.py tests/review/test_start_review_session.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_result_writer.py tests/review/test_run_stage_review_script.py
git commit -m "feat: add spawned-agent review runtime"
```

### Task 3: Generate Stage-Specific Review Skills For Spawn-Agent Flow

**Files:**
- Modify: `templates/skills/review-stage/SKILL.md.tmpl`
- Modify: `runtime/tools/review_skillgen/render.py`
- Modify: `runtime/scripts/gen_codex_stage_review_skills.py`
- Modify: `skills/mandate/qros-mandate-review/SKILL.md`
- Modify: `skills/data_ready/qros-data-ready-review/SKILL.md`
- Modify: `skills/signal_ready/qros-signal-ready-review/SKILL.md`
- Modify: `skills/train_freeze/qros-train-freeze-review/SKILL.md`
- Modify: `skills/test_evidence/qros-test-evidence-review/SKILL.md`
- Modify: `skills/backtest_ready/qros-backtest-ready-review/SKILL.md`
- Modify: `skills/holdout_validation/qros-holdout-validation-review/SKILL.md`
- Modify: `skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md`
- Modify: `skills/csf_signal_ready/qros-csf-signal-ready-review/SKILL.md`
- Modify: `skills/csf_train_freeze/qros-csf-train-freeze-review/SKILL.md`
- Modify: `skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md`
- Modify: `skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md`
- Modify: `skills/csf_holdout_validation/qros-csf-holdout-validation-review/SKILL.md`
- Modify: `tests/review/test_adversarial_review_skill_generation.py`
- Modify: `tests/review/test_generated_skills_fresh.py`

- [ ] **Step 1: Write the failing generator tests for the new launcher wording**

```python
def test_generated_review_skill_template_describes_spawned_agent_review_loop(tmp_path: Path) -> None:
    ...
    skill_text = (output_root / "skills" / "test_evidence" / "qros-test-evidence-review" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "spawn_agent" in skill_text
    assert "当前会话" in skill_text
    assert "reviewer 子 agent" in skill_text
    assert "qros-review" in skill_text
    assert "不再需要手动再开一个 Codex review session" not in skill_text
    assert "独立 review session" not in skill_text
```

- [ ] **Step 2: Run the generator tests and verify they fail on the old template**

Run: `python -m pytest tests/review/test_adversarial_review_skill_generation.py tests/review/test_generated_skills_fresh.py -q`

Expected: FAIL because the checked-in template and generated skills still describe the separate review-session flow.

- [ ] **Step 3: Update the review skill template and regenerate the checked-in skills**

```text
1. 在当前会话中完成 review-ready / handoff 自查
2. 调共享 runtime helper 注册 spawned review cycle
3. 用 `spawn_agent` 拉起 adversarial reviewer 子 agent
4. 等待 reviewer 子 agent 只写 `review/result/reviewer_findings.raw.yaml`
5. 调 `./.qros/bin/qros-review` 完成 canonical result、audit 与 closure
```

Run: `python runtime/scripts/gen_codex_stage_review_skills.py`

- [ ] **Step 4: Re-run the generator freshness tests**

Run: `python -m pytest tests/review/test_adversarial_review_skill_generation.py tests/review/test_generated_skills_fresh.py -q`

Expected: PASS with the new spawned-agent wording and fresh generated bundles.

- [ ] **Step 5: Commit the skill-generation changes**

```bash
git add templates/skills/review-stage/SKILL.md.tmpl runtime/tools/review_skillgen/render.py runtime/scripts/gen_codex_stage_review_skills.py skills/mandate/qros-mandate-review/SKILL.md skills/data_ready/qros-data-ready-review/SKILL.md skills/signal_ready/qros-signal-ready-review/SKILL.md skills/train_freeze/qros-train-freeze-review/SKILL.md skills/test_evidence/qros-test-evidence-review/SKILL.md skills/backtest_ready/qros-backtest-ready-review/SKILL.md skills/holdout_validation/qros-holdout-validation-review/SKILL.md skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md skills/csf_signal_ready/qros-csf-signal-ready-review/SKILL.md skills/csf_train_freeze/qros-csf-train-freeze-review/SKILL.md skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md skills/csf_holdout_validation/qros-csf-holdout-validation-review/SKILL.md tests/review/test_adversarial_review_skill_generation.py tests/review/test_generated_skills_fresh.py
git commit -m "feat: regenerate review skills for spawned-agent flow"
```

### Task 4: Align User-Facing Docs And Research-Session Guidance

**Files:**
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/codex-stage-review-skill-usage.md`
- Modify: `tests/session/test_research_session_assets.py`
- Modify: `tests/session/test_research_session_runtime.py`
- Modify: `tests/bootstrap/test_native_skill_runtime_paths.py`

- [ ] **Step 1: Write the failing doc/runtime assertions for the new flow**

```python
def test_research_session_assets_describe_spawned_agent_review_loop() -> None:
    content = (REPO_ROOT / "skills" / "core" / "qros-research-session" / "SKILL.md").read_text(encoding="utf-8")
    assert "spawn_agent" in content
    assert "reviewer 子 agent" in content
    assert "qros-start-review" not in content
```

- [ ] **Step 2: Run the focused doc/runtime tests and verify they fail**

Run: `python -m pytest tests/session/test_research_session_assets.py tests/session/test_research_session_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py -q`

Expected: FAIL because the current docs and session guidance still mention explicit review sessions and `qros-start-review`.

- [ ] **Step 3: Update the docs and research-session guidance to match the spawned-agent flow**

```text
- author 主会话仍停在 `*_review_confirmation_pending`
- 用户显式进入对应 `qros-*-review`
- review skill 在当前会话中拉起 reviewer 子 agent
- reviewer child 只写 raw findings
- `qros-review` 完成 deterministic closure
```

- [ ] **Step 4: Re-run the focused doc/runtime tests**

Run: `python -m pytest tests/session/test_research_session_assets.py tests/session/test_research_session_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py -q`

Expected: PASS with all user-facing guidance aligned to runtime behavior.

- [ ] **Step 5: Run the required broader verification**

Run: `python -m pytest tests/review/test_start_review_session.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_result_writer.py tests/review/test_run_stage_review_script.py tests/review/test_adversarial_review_skill_generation.py tests/review/test_generated_skills_fresh.py tests/session/test_research_session_assets.py tests/session/test_research_session_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py -q`

Expected: PASS

Run: `python runtime/scripts/run_verification_tier.py --tier smoke`

Expected: PASS

Run: `python runtime/scripts/run_verification_tier.py --tier full-smoke`

Expected: PASS

- [ ] **Step 6: Commit the docs and orchestration alignment**

```bash
git add skills/core/qros-research-session/SKILL.md docs/guides/qros-review-shared-protocol.md docs/guides/qros-research-session-usage.md docs/guides/codex-stage-review-skill-usage.md tests/session/test_research_session_assets.py tests/session/test_research_session_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py docs/superpowers/plans/2026-04-21-spawn-agent-review-implementation.md
git commit -m "docs: align review guidance with spawned-agent flow"
```
