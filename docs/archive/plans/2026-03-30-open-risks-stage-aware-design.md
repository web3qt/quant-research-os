# Open Risks Stage-Aware Design

**Date:** 2026-03-30  
**Status:** Approved for design handoff  
**Scope:** 修正 `run_research_session` 状态摘要里 `open_risks` 的语义，使其按 `current_stage` 生成，而不是在后续阶段继续回显 intake 阶段的 `rollback_target`

## Goal

当前 `open_risks` 由 `tools/research_session.py` 中的 `session_transition_summary()` 统一从 `00_idea_intake/idea_gate_decision.yaml` 读取：

- `required_reframe_actions`
- `rollback_target`

这会导致研究线已经进入 `mandate` 之后的阶段，尤其是 `csf_data_ready_confirmation_pending`，仍然显示：

```text
rollback_target remains 00_idea_intake
```

这不是当前阶段的真实开放风险，而是早期 artifact 的历史字段泄漏进了后续状态摘要。

本次设计要把 `open_risks` 改成 stage-aware，确保它只表达当前阶段仍然开放、且对当前阶段有意义的风险。

## Decision

采用“按 `current_stage` 生成 `open_risks`”的方案，不做全量 stage-specific 风险引擎。

原因：

- 这能修正当前语义错误
- 改动范围小，只需要调整 runtime 状态摘要和测试
- 以后如果要给某些 stage 增加真实 risk source，也有自然扩展位

## Rejected Alternatives

### 1. 进入 `mandate` 后硬编码屏蔽 intake `rollback_target`

优点：最小补丁。  
缺点：仍然不是 stage-aware 设计，后续会继续产生类似问题。

### 2. 给每个 stage 新建完整 risk artifact

优点：最完整。  
缺点：明显超出本次修正范围，属于过度设计。

## Stage-Aware Rule

`open_risks` 必须表示“当前阶段仍然开放的真实风险”。

因此：

- 在 `idea_intake` 与 `idea_intake_confirmation_pending`，仍然允许复用 intake gate 中的：
  - `required_reframe_actions`
  - `rollback_target`
- 一旦进入 `mandate` 及其后续所有 stage：
  - 如果当前阶段没有新的 risk source
  - `open_risks` 必须返回空列表 `[]`

## Implementation Shape

### Runtime

修改 `tools/research_session.py`：

- 将 `session_transition_summary(lineage_root)` 改为 `session_transition_summary(lineage_root, current_stage)`
- 在函数内部判断当前阶段是否仍属于 intake 语义阶段
- 若不是 intake 阶段，则不再从 intake gate 内读取 `rollback_target` 作为 `open_risks`

`why_now` 不在本次设计中修改。

### Tests

更新或新增两类测试：

- `tests/test_research_session_runtime.py`
  - 覆盖 `csf_data_ready_confirmation_pending` 场景
  - 断言 `status.open_risks == []`
- `tests/test_run_research_session_script.py`
  - 覆盖相同场景的 CLI 输出
  - 断言 stdout 不再包含：
    - `Open risks:`
    - `rollback_target remains 00_idea_intake`

同时保留 intake 阶段原有语义，避免回归。

## Non-Goals

本次不做：

- 不修改 `idea_gate_decision.yaml` schema
- 不修改 `why_now` 逻辑
- 不新增 stage-specific risk artifact
- 不改 docs、skills、gate truth

## Acceptance Criteria

修正完成后应满足：

- `idea_intake` 阶段仍能显示 intake 的 reframe 风险
- `mandate` 之后若没有新的真实风险，`open_risks == []`
- `csf_data_ready_confirmation_pending` 不再显示 `rollback_target remains 00_idea_intake`
- CLI 输出与 runtime 状态一致

## Validation

最小验证包括：

- `python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -q`
- `git diff --check`

无需跑全量测试，因为本次只改状态摘要逻辑和对应回归测试。
