# QROS Post-Clear Skill Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace user-facing `qros-resume` recommendations at PASS-like review boundaries with the next stage's long QROS author skill while keeping `qros-resume` as backend/debug recovery.

**Architecture:** Extend the existing shared `review_resume_protocol` helper so all text and JSON call sites derive the same `/clear` handoff fields. The helper will compute `recommended_skill`, `recommended_skill_reason`, and `backend_resume_command` from disk-derived session state; text renderers show the skill, while JSON keeps the backend command. Author skill docs reinforce that post-clear author entry must revalidate disk state before writing artifacts.

**Tech Stack:** Python 3.13, existing QROS runtime scripts/tools, pytest, Markdown skill/docs.

---

### Task 1: Change the shared clear capsule to recommend skills

**Files:**
- Modify: `runtime/tools/review_resume_protocol.py`
- Test: `tests/session/test_lineage_lock_session_status.py`
- Test: `tests/session/test_run_resume_script.py`

- [ ] **Step 1: Write the failing progress payload test**

In `tests/session/test_lineage_lock_session_status.py`, update `test_progress_payload_exposes_clear_required_for_review_complete` to assert the new field names:

```python
    assert payload["clear_required"] is True
    assert payload["clear_instruction"] == "Run /clear in Codex or Claude Code before continuing."
    assert payload["recommended_skill"] == "qros-csf-data-ready-author"
    assert payload["recommended_skill_reason"] == (
        "mandate PASS allows csf_data_ready authoring after next-stage handoff."
    )
    assert payload["backend_resume_command"] == f"./.qros/bin/qros-resume --lineage-id {lineage_root.name}"
    assert "qros-csf-data-ready-author" in payload["next_action"]
    assert "qros-resume" not in payload["next_action"]
```

- [ ] **Step 2: Write the failing resume JSON test**

In `tests/session/test_run_resume_script.py`, update `test_run_resume_script_reports_clear_handoff_from_disk_state`:

```python
    assert payload["current_stage"] == "mandate_next_stage_confirmation_pending"
    assert payload["clear_required"] is True
    assert payload["clear_instruction"] == "Run /clear in Codex or Claude Code before continuing."
    assert payload["recommended_skill"] == "qros-csf-data-ready-author"
    assert payload["backend_resume_command"] == "./.qros/bin/qros-resume --lineage-id topic_a"
    assert "qros-csf-data-ready-author" in payload["next_action"]
```

- [ ] **Step 3: Run the targeted tests to verify they fail**

Run:

```bash
python -m pytest tests/session/test_lineage_lock_session_status.py::test_progress_payload_exposes_clear_required_for_review_complete tests/session/test_run_resume_script.py::test_run_resume_script_reports_clear_handoff_from_disk_state -v
```

Expected: FAIL because `recommended_skill` and `backend_resume_command` do not exist yet.

- [ ] **Step 4: Implement stage-to-author-skill mapping**

In `runtime/tools/review_resume_protocol.py`, replace `recommended_command` as the primary field with helper functions:

```python
NEXT_AUTHOR_SKILL_BY_REVIEWED_STAGE: dict[str, str] = {
    "mandate:cross_sectional_factor": "qros-csf-data-ready-author",
    "mandate:time_series_signal": "qros-tss-data-ready-author",
    "data_ready": "qros-signal-ready-author",
    "signal_ready": "qros-train-freeze-author",
    "train_freeze": "qros-test-evidence-author",
    "test_evidence": "qros-backtest-ready-author",
    "backtest_ready": "qros-holdout-validation-author",
    "csf_data_ready": "qros-csf-signal-ready-author",
    "csf_signal_ready": "qros-csf-train-freeze-author",
    "csf_train_freeze": "qros-csf-test-evidence-author",
    "csf_test_evidence": "qros-csf-backtest-ready-author",
    "csf_backtest_ready": "qros-csf-holdout-validation-author",
    "tss_data_ready": "qros-tss-signal-ready-author",
    "tss_signal_ready": "qros-tss-train-freeze-author",
    "tss_train_freeze": "qros-tss-test-evidence-author",
    "tss_test_evidence": "qros-tss-backtest-ready-author",
    "tss_backtest_ready": "qros-tss-holdout-validation-author",
}


def _stage_base(current_stage: str) -> str:
    for suffix in (
        "_review_confirmation_pending",
        "_next_stage_confirmation_pending",
        "_confirmation_pending",
        "_author",
        "_review_complete",
        "_review",
    ):
        if current_stage.endswith(suffix):
            return current_stage[: -len(suffix)]
    return current_stage


def _recommended_skill(status: ResumeStatus) -> str | None:
    reviewed_stage = _stage_base(status.current_stage)
    current_route = getattr(status, "current_route", None)
    if reviewed_stage == "mandate" and isinstance(current_route, str):
        return NEXT_AUTHOR_SKILL_BY_REVIEWED_STAGE.get(f"mandate:{current_route}")
    return NEXT_AUTHOR_SKILL_BY_REVIEWED_STAGE.get(reviewed_stage)
```

Extend `ResumeStatus` with `current_route: str | None`. `build_clear_resume_capsule(...)` should return:

```python
{
    "clear_required": clear_required,
    "clear_instruction": CLEAR_INSTRUCTION if clear_required else None,
    "recommended_skill": recommended_skill,
    "recommended_skill_reason": reason,
    "backend_resume_command": backend_resume_command,
    "resume_hint": (
        f"{CLEAR_INSTRUCTION} Then enter {recommended_skill} in the new session."
        if clear_required and recommended_skill is not None
        else status.resume_hint
    ),
    "next_action": (
        f"Run /clear first, then enter {recommended_skill} in the new session."
        if clear_required and recommended_skill is not None
        else status.next_action
    ),
}
```

Keep `backend_resume_command = ./.qros/bin/qros-resume --lineage-id ...` when `clear_required` is true. Do not return `recommended_command`.

- [ ] **Step 5: Run the targeted tests to verify they pass**

Run:

```bash
python -m pytest tests/session/test_lineage_lock_session_status.py::test_progress_payload_exposes_clear_required_for_review_complete tests/session/test_run_resume_script.py::test_run_resume_script_reports_clear_handoff_from_disk_state -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add runtime/tools/review_resume_protocol.py tests/session/test_lineage_lock_session_status.py tests/session/test_run_resume_script.py
git commit -m "feat: recommend post-clear author skills"
```

### Task 2: Update user-facing renderers

**Files:**
- Modify: `runtime/scripts/run_progress.py`
- Modify: `runtime/scripts/run_research_session.py`
- Modify: `runtime/scripts/run_resume.py`
- Modify: `runtime/scripts/run_stage_review.py`
- Test: `tests/review/test_run_stage_review_script.py`
- Test: `tests/session/test_run_research_session_script.py`

- [ ] **Step 1: Write the failing review output test**

In `tests/review/test_run_stage_review_script.py`, update the PASS assertions:

```python
    assert "Run /clear in Codex or Claude Code before continuing." in result.stdout
    assert "Recommended next skill: qros-csf-data-ready-author" in result.stdout
    assert "Recommended resume command" not in result.stdout
    assert "qros-resume --lineage-id" not in result.stdout
```

- [ ] **Step 2: Write the failing session text output test**

In `tests/session/test_run_research_session_script.py`, update the mandate review complete assertions:

```python
    assert "🧹 Clear instruction: Run /clear in Codex or Claude Code before continuing." in result.stdout
    assert "🧹 Recommended next skill: qros-csf-data-ready-author" in result.stdout
    assert "qros-resume --lineage-id" not in result.stdout
```

- [ ] **Step 3: Run the targeted tests to verify they fail**

Run:

```bash
python -m pytest tests/review/test_run_stage_review_script.py::test_run_stage_review_script_creates_closure_artifacts tests/session/test_run_research_session_script.py::test_run_research_session_reports_mandate_review_complete_when_closure_exists -v
```

Expected: FAIL because text renderers still print `Recommended command` / `Recommended resume command`.

- [ ] **Step 4: Update text renderers**

In `runtime/scripts/run_progress.py`, `runtime/scripts/run_research_session.py`, and `runtime/scripts/run_resume.py`, replace user-facing `Recommended command` lines with:

```python
f"Recommended next skill: {payload['recommended_skill']}"
```

or, in the emoji panel:

```python
print(f"🧹 Recommended next skill: {clear_resume['recommended_skill']}")
```

Only print the line when `recommended_skill` is truthy. Do not print `backend_resume_command` in text mode.

In `runtime/scripts/run_stage_review.py`, replace:

```python
print(f"Recommended resume command: {clear_notice['recommended_command']}")
```

with:

```python
if clear_notice.get("recommended_skill"):
    print(f"Recommended next skill: {clear_notice['recommended_skill']}")
```

- [ ] **Step 5: Teach review notices enough context**

Change `build_review_clear_resume_notice(...)` in `runtime/tools/review_resume_protocol.py` to accept optional `stage` and `current_route`:

```python
def build_review_clear_resume_notice(
    *,
    lineage_id: str,
    final_verdict: str | None,
    stage: str | None = None,
    current_route: str | None = None,
    continue_mode: bool = False,
) -> dict[str, Any]:
```

In `runtime/scripts/run_stage_review.py`, pass `payload["stage"]` and infer route for mandate review from the closure payload if present; if unavailable, use the existing `payload["stage"] == "mandate"` fallback by reading `payload.get("current_route")` only when present. If no route can be inferred for mandate, leave `recommended_skill` as `None` and do not print a downstream skill.

- [ ] **Step 6: Run targeted tests to verify they pass**

Run:

```bash
python -m pytest tests/review/test_run_stage_review_script.py::test_run_stage_review_script_creates_closure_artifacts tests/session/test_run_research_session_script.py::test_run_research_session_reports_mandate_review_complete_when_closure_exists -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add runtime/scripts/run_progress.py runtime/scripts/run_research_session.py runtime/scripts/run_resume.py runtime/scripts/run_stage_review.py runtime/tools/review_resume_protocol.py tests/review/test_run_stage_review_script.py tests/session/test_run_research_session_script.py
git commit -m "fix: show post-clear skill in text handoff"
```

### Task 3: Update docs and skill guidance

**Files:**
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `skills/core/qros-progress/SKILL.md`
- Modify: `tests/bootstrap/test_native_skill_runtime_paths.py`
- Modify: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Write failing docs/skill expectations**

In `tests/bootstrap/test_native_skill_runtime_paths.py`, replace the session skill expectation:

```python
    assert "qros-csf-data-ready-author" in session_skill
    assert "backend/debug recovery" in session_skill
```

Do not require `./.qros/bin/qros-resume` in the session skill text.

In `tests/docs/test_install_docs.py`, keep the install docs assertion for `./.qros/bin/qros-resume` because the wrapper still exists, but add:

```python
    assert "qros-resume` is a backend/debug recovery command" in combined
```

- [ ] **Step 2: Run docs/bootstrap tests to verify they fail**

Run:

```bash
python -m pytest tests/bootstrap/test_native_skill_runtime_paths.py::test_public_skills_reference_repo_local_wrappers tests/docs/test_install_docs.py::test_install_docs_reference_supported_commands -v
```

Expected: FAIL until docs and skill guidance are updated.

- [ ] **Step 3: Update research session usage docs**

In `docs/guides/qros-research-session-usage.md`, replace the paragraph that says users should run `qros-resume` after `/clear` with:

```markdown
`qros-resume` 是 backend/debug recovery 命令，不是普通用户在 PASS boundary 后的主入口。正常 review 放行后，Codex 或 Claude Code 应先执行 `/clear`，然后在新会话中进入 runtime 推荐的下一阶段 author skill，例如 `qros-csf-data-ready-author` 或 `qros-tss-data-ready-author`。新会话里的 agent 再从磁盘状态重验 lineage、review closure、next-stage handoff 和 stage-entry guard。
```

Replace the resume command block with examples of long skill names:

```text
qros-csf-data-ready-author
qros-tss-data-ready-author
qros-csf-signal-ready-author
```

- [ ] **Step 4: Update shared review protocol docs**

In `docs/guides/qros-review-shared-protocol.md`, replace the clear/resume boundary sentence with:

```markdown
`CLOSURE_READY_PASS` 和 `CLOSURE_READY_CONDITIONAL_PASS` 关闭后会形成 clear/resume boundary。`./.qros/bin/qros-review` closer 必须提醒 Codex 或 Claude Code 先执行 `/clear`，再在新会话中进入 runtime 推荐的下一阶段 author skill，例如 `qros-csf-data-ready-author`。`qros-resume` 只保留为 backend/debug recovery 命令，不作为普通用户下一步。
```

- [ ] **Step 5: Update core skill guidance**

In `skills/core/qros-research-session/SKILL.md`, replace the `/clear` section with:

```markdown
When `qros-review`, `qros-session`, or `qros-progress` reports `clear_required = true`, the current agent must:

- tell the user to run `/clear` in Codex or Claude Code
- stop trying to start the next stage in the same long conversation
- after `/clear`, tell the user to enter the printed `recommended_skill`, for example `qros-csf-data-ready-author`
- treat `backend_resume_command` / `qros-resume` as backend/debug recovery, not the ordinary user-facing next step
- ensure the post-clear author skill revalidates disk state before writing artifacts
```

In `skills/core/qros-progress/SKILL.md`, replace the `recommended_command` guidance with:

```markdown
- `clear_required = true`，必须提醒用户先在 Codex 或 Claude Code 执行 `/clear`，再进入输出里的 `recommended_skill`；`backend_resume_command` 只作为 agent/debug recovery，不作为普通用户下一步。
```

- [ ] **Step 6: Run docs/bootstrap tests to verify they pass**

Run:

```bash
python -m pytest tests/bootstrap/test_native_skill_runtime_paths.py::test_public_skills_reference_repo_local_wrappers tests/docs/test_install_docs.py::test_install_docs_reference_supported_commands -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md skills/core/qros-research-session/SKILL.md skills/core/qros-progress/SKILL.md tests/bootstrap/test_native_skill_runtime_paths.py tests/docs/test_install_docs.py
git commit -m "docs: document post-clear skill entry"
```

### Task 4: Full validation

**Files:**
- No code files; verification only.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/bootstrap/test_install_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py tests/bootstrap/test_project_bootstrap.py tests/bootstrap/test_claude_repo_bootstrap.py tests/docs/test_install_docs.py tests/review/test_run_stage_review_script.py tests/session/test_lineage_lock_session_status.py tests/session/test_run_research_session_script.py tests/session/test_run_resume_script.py -v
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

- [ ] **Step 4: Confirm no validation-driven fixes remain**

Run:

```bash
git status --short
```

Expected: no unstaged or staged runtime/doc/test changes. If validation did require fixes, rerun the failed validation command before finishing and commit the exact fixed files with a message matching the scope of the fix.
