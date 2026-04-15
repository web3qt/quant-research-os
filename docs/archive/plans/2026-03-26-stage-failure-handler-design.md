# QROS Stage Failure Handler Design

**Date:** 2026-03-26  
**Status:** Draft approved for direction  
**Scope:** `Codex-only`, `single failure-entry skill`, `data_ready -> shadow`

## Goal

把当前“阶段失败后靠 agent 自己理解文档”的模式，升级成一个统一、可强制执行的失败处置入口。

第一版只解决一件事：

- 新增一个统一失败 skill：`qros-stage-failure-handler`
- 让 `qros-research-session` 在读到失败类 verdict 后自动切换到失败处置协议
- 让失败处理按当前 stage 自动分流
- 让失败结论以正式治理产物落盘，而不是停留在聊天里

## Core Principle

失败不是普通 debug。

在 QROS 里，不同阶段失败的语义不同：

- `data_ready` 失败，核心是数据正确性、覆盖、泄漏、schema 与边界
- `test_evidence` 失败，核心是正式样本证据、选择偏差、freeze discipline
- `holdout` 失败，核心是泛化、purity、是否终止原线
- `shadow` 失败，核心是运营、执行、容量与研究主假设区分

所以统一失败入口的作用不是“给 agent 一个通用修错模板”，而是：

- 先冻结失败
- 再按阶段协议分类
- 再给出合法的机构处置方向

## Current Gap

仓库已经有：

- 分阶段 fail-SOP，覆盖 `data_ready -> shadow`
- `lineage_change_control_sop_cn.md`
- `qros-research-session`
- `tools/research_session.py`

但仍有三个问题：

1. 失败处理目前只是文档存在，不是 skill 行为。
2. `research_session` 虽然已经不会在 `RETRY / NO-GO / CHILD LINEAGE` 时推进下游，但也只会停住，不会自动切到失败处置模式。
3. agent 一旦没有被强约束，很容易把阶段失败当成普通修 bug，跳过“冻结失败 -> 变更分类 -> 合法回退”的机构流程。

## Recommended Direction

第一版采用：

- 一个统一失败入口 skill：`qros-stage-failure-handler`
- `qros-research-session` 自动切入这个失败 skill 的工作协议
- `tools/research_session.py` 暴露显式 failure-routing 信号

也就是说，失败流转不是：

`review fail -> agent 自己决定接下来怎么办`

而是：

`review fail -> session 停止主线推进 -> 进入 failure handler -> 按阶段分流`

## Approaches Considered

### Approach A: 文档化失败处理

只保留当前 fail-SOP 文档，不新增 skill，不改 session 行为。

优点：

- 改动最小
- 不需要改 runtime

缺点：

- agent 是否遵守完全靠自觉
- 不能形成稳定行为
- 无法保证失败后停止主线推进并切换协议

### Approach B: 统一失败入口 + 自动切入

新增 `qros-stage-failure-handler`，并让 `qros-research-session` 在失败 verdict 出现时自动切入。

优点：

- 用户入口统一
- agent 行为稳定
- 与现有阶段 orchestration 兼容
- 能把 fail-SOP 从“参考文档”升级成“强约束工作协议”

缺点：

- 需要同时修改 skill、runtime、测试与使用说明

### Approach C: 完整失败状态机

把每种失败 verdict 都编码成 runtime 的正式状态，如 `test_evidence_failure_retry`。

优点：

- 机器可判定性最强
- 长期最一致

缺点：

- 第一版复杂度过高
- 会过早把状态空间做得很重

## Recommendation

第一版采用 **Approach B: 统一失败入口 + 自动切入**。

原因：

- 用户的核心诉求是“agent 一旦在某阶段失败，就被引导进该阶段的机构处置流程”
- 这需要 skill 级别的统一入口和 session 级别的自动切换
- 当前 runtime 只差一步显式 failure routing，就足以支撑首版闭环

## Scope

第一版失败 skill 覆盖：

- `data_ready`
- `signal_ready`
- `train_freeze`
- `test_evidence`
- `backtest_ready`
- `holdout_validation`
- `shadow`

自动切入首版实际生效范围：

- `data_ready review`
- `signal_ready review`
- `train_freeze review`
- `test_evidence review`
- `backtest_ready review`
- `holdout_validation review`

说明：

- `shadow` 已有 fail-SOP，因此纳入统一 skill 的分流范围
- 但当前 `research_session` 主线还没编排到 `shadow`，所以自动切入先不会在 runtime 中触发到 `shadow`

明确不在首版范围：

- `idea_intake`
- `mandate`

原因是这些阶段当前没有独立 fail-SOP，不应在首版假装已经具备同等制度完备度。

## Trigger Contract

`qros-research-session` 在以下 review verdict 出现时，必须立即停止正常推进并切换到失败处置协议：

- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

不允许的行为：

- 继续进入下一个 `*_confirmation_pending`
- 先“修一修再说”
- 把失败 verdict 当成普通 review note
- 不冻结失败事实就直接改产物

## Failure Handler Architecture

统一失败 skill 分成两层。

### 1. Shared Failure Harness

这是所有阶段共用的骨架，顺序固定：

1. 识别当前失败 stage
2. 读取 review verdict
3. 冻结失败事实与失败证据
4. 汇总当前允许沿用的上游冻结对象
5. 读取阶段 fail-SOP 与 `lineage_change_control_sop_cn.md`
6. 形成正式分流判断

这一层只回答：

- 失败是什么
- 失败发生在哪一层
- 当前原线是否还能继续承载修复
- 应该走 `PATCH`、`CONTROLLED_RETRY`、`STAGE_ROLLBACK`、`CHILD_LINEAGE` 还是 `NO_GO`

### 2. Stage-Specific Routing

共享 harness 之后，再按当前阶段套用对应 fail-SOP：

- `data_ready`：`DATA_MISSING`、`DATA_MISALIGNMENT`、`LEAKAGE_FAIL`、`QUALITY_FAIL`、`SCHEMA_FAIL`、`REPRO_FAIL`、`SCOPE_FAIL`
- `signal_ready`：依 `02_signal_ready_failure_sop_cn.md` 的阶段失败分类
- `train_freeze`：依 `03_train_freeze_failure_sop_cn.md` 的阶段失败分类
- `test_evidence`：`EVIDENCE_ABSENT`、`EVIDENCE_FRAGILE`、`REGIME_SPECIFIC_FAIL`、`SELECTION_BIAS_FAIL`、`ARTIFACT_REPRO_FAIL`、`SCOPE_DRIFT_FAIL`
- `backtest_ready`：依 `05_backtest_failure_sop_cn.md` 的阶段失败分类
- `holdout_validation`：依 `06_holdout_failure_sop_cn.md` 的阶段失败分类
- `shadow`：`OPS_FAIL`、`EXECUTION_FAIL`、`CAPACITY_FAIL`、`GENERALIZATION_FAIL`、`THESIS_FAIL`、`SCOPE_FAIL`

skill 不重新发明每阶段错误规则，而是把现有 fail-SOP 变成 agent 的执行协议。

## Runtime Contract

`tools/research_session.py` 除了当前的“阻止错误 verdict 继续推进”以外，首版还应显式输出 failure routing 信号。

建议在 session status 中新增：

- `review_verdict`
- `requires_failure_handling`
- `failure_stage`
- `failure_reason_summary`

其中：

- 当 verdict 是 `PASS FOR RETRY / RETRY / NO-GO / CHILD LINEAGE` 时，`requires_failure_handling = true`
- `failure_stage` 使用当前失败 stage 的标准名
- `failure_reason_summary` 可以先用简短 deterministic 文本，不需要在 runtime 里做复杂归因

runtime 的职责是：

- 明确指出“现在必须走失败处置”
- 不负责替 skill 完成完整失败分类

## Skill Contract

新增 skill：`skills/qros-stage-failure-handler/SKILL.md`

它必须明确：

- 统一失败入口的目的
- 覆盖范围只到 `data_ready -> shadow`
- 使用共享 harness
- 根据当前 stage 读取对应 fail-SOP
- 输出正式治理结论
- 在 failure disposition 未形成前，不得恢复主线推进

它还必须告诉 agent：

- 失败处理默认不是让用户重新解释研究想法
- 失败处理默认不是重跑全部阶段
- 失败处理必须显式说明允许修改和禁止修改
- 一旦涉及研究主问题、冻结对象身份或交易语义改变，必须升级到 `CHILD_LINEAGE` 或更高等级 change control

## Formal Outputs

统一失败 skill 的首版正式产物建议固定为：

- `failure_intake.md`
- `failure_evidence_index.yaml`
- `failure_classification.yaml`
- `failure_disposition.yaml`
- `change_control_decision.yaml`

其中最核心的是 `failure_disposition.yaml`，最少包含：

- `failed_stage`
- `review_verdict`
- `failure_class`
- `disposition`
- `rollback_stage`
- `allowed_changes`
- `forbidden_changes`
- `next_action`

这样每次失败后，系统都会留下正式、可审计的治理对象。

## Interaction Model

失败处理模式下，agent 的顺序应当固定：

1. 报告当前失败阶段和 verdict
2. 明确说明主线推进已停止
3. 回显当前 fail-SOP 关注的检查轴
4. 输出失败分类草案
5. 输出正式处置方向草案
6. 只有在需要明确治理判断时才问用户

也就是说，失败 skill 的默认姿态不是“继续探索”，而是“先把失败治理结构搭起来”。

## Testing Strategy

首版验证分三层：

### 1. Skill Asset Tests

检查：

- `qros-stage-failure-handler` skill 存在
- skill 明确覆盖 `data_ready -> shadow`
- skill 包含共享 harness、阶段分流、正式输出与自动切入约束

### 2. Runtime Tests

扩展 `tests/test_research_session_runtime.py`：

- 对每个已编排 review 阶段
- 当 certificate verdict 为 `PASS FOR RETRY / RETRY / NO-GO / CHILD LINEAGE`
- session status 必须返回 `requires_failure_handling = true`
- 且不得推进到下一个阶段

### 3. Script / Session Smoke Tests

扩展 `tests/test_run_research_session_script.py`：

- 模拟 `test_evidence review` 输出 `RETRY`
- 预期：
  - 不进入 `backtest_ready_confirmation_pending`
  - 输出 failure routing 信号
  - `next_action` 指向 failure handling 而不是下一阶段 authoring

## Known Gaps

首版需要明确两个现实问题：

1. fail-SOP 文件编号仍是旧口径，如 `01_data_ready`、`02_signal_ready`，与当前 runtime 的阶段编号并不完全一致。
2. 多份 fail-SOP 依赖 `stage-failure-harness`，但仓库里当前没有单独落地这个文档文件。

因此首版 skill 应直接把共享 harness 内嵌进 `SKILL.md`，不要等待一个尚未存在的独立文档。

## Success Criteria

当 `qros-research-session` 运行到任何已覆盖阶段的 review，并读到失败类 verdict 时：

- 不会推进下游
- 不会让 agent 按普通 debug 继续工作
- 会明确进入统一失败处理协议
- 会按当前 stage 分流到对应 fail-SOP
- 会要求输出正式 failure disposition

## One-Line Summary

第一版不是把 fail-SOP “补充给 agent 看”，而是把失败处理正式做成一个统一 skill，并由 `qros-research-session` 在失败 verdict 出现时强制切换进去，让阶段失败真正按机构协议被处理。
