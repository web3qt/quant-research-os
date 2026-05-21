# QROS Canonical Review Eligibility Design

## Context

一条真实的 QROS CSF 会话暴露出两个互相放大的问题：

1. review runtime 本身不稳定，reviewer raw findings 经常因为字段形状、枚举值或中间协议不匹配而被 closer 打回，导致一轮 review 变成多轮机械返工。
2. session / progress / review entry 对“当前 stage 是否真的有资格进入 review”没有单一真值，导致 semantic fail、preflight fail 或 failure-required 状态仍可能被解释成 `*_review_confirmation_pending`，甚至继续推荐 `qros-*-review`。

这类错误会直接制造错误心智：

- 用户看到的是“现在可以确认 review”
- 但磁盘真值实际上已经表明“当前 stage 不该 review，应进入 failure handling”

同时，review 不顺本身不应该触发 child lineage。`CHILD_LINEAGE` 只能从正式 failure / disposition 链打开，而不是 author 来回修、reviewer 抓 blocker、或 preflight fail 后由 agent 自由裁量。

这份设计采用一个明确方向：

- 以 **review runtime 稳定化** 为第一优先
- 同时补上 **最小但强制的 review-entry 护栏**
- 不为旧错行为做兼容保留，直接确立新的 canonical review 规则

## User-Approved Policy Decisions

本设计锁定以下用户决策：

- 普通主流程里，agent 可以提示用户进入 stage-specific review skill，不强制所有 review 都只通过 `qros-research-session` 暴露。
- 只要 author / semantic / preflight 已经 hard fail，系统必须 **禁止进入 review**，直接转 failure-style blocking，不给“继续 review”假象。
- `CHILD_LINEAGE` 只能从正式 failure / disposition 链打开；review 不顺、author 反复修、preflight fail 都不能直接开 child lineage。
- 本次改动 **不做兼容保留**。旧的错误 review 入口行为、错误 progress 推荐口径、以及把不该 review 的 stage 暴露成 review-ready 的路径，应该直接废止。

## Goal

建立一套新的 canonical review eligibility model，使 QROS 在 review 相关边界上满足以下目标：

- 只有真正通过 author completeness、semantic validator、deterministic review preflight 的 stage，才能进入 `*_review_confirmation_pending`
- hard gate fail 的 stage 不能再被解释成 review-ready
- `qros-session`、`qros-progress`、stage-specific review entry 对 review 资格给出同一真值
- reviewer raw findings 的常见格式抖动由 deterministic normalizer 收口，不再制造多轮机械返工
- author outputs 变化后，旧 review cycle 必须 deterministic stale，不能继续证明新 outputs
- `CHILD_LINEAGE` 继续保持 formal-only 入口，不被 review lane 或 author lane 越权打开

## Non-Goals

- 不重写整个 `qros-research-session` 的用户交互流程
- 不重命名现有 major stage id、artifact path 或 closure artifact 路径
- 不修改 lineage lock ledger 的治理语义
- 不借这次机会一口气收敛所有 `current_skill` / `recommended_skill` 历史口径，只处理 review 边界相关真值
- 不把所有 stage-specific review skill 删除；它们仍保留为合法主流程入口或 debug/manual recovery 入口

## Problem Statement

## 1. Review eligibility 没有单一真值

当前系统把下列判断分散在多个地方：

- stage detection
- author completeness
- semantic validator
- deterministic preflight
- latest review failure routing
- failure disposition routing
- progress/runtime handoff generation

结果是不同入口可能给出不同结论：

- session 认为不该 review
- progress 却推荐 `qros-csf-test-evidence-review`
- author lane 明明 semantic fail，stage 名却还能停在 `*_review_confirmation_pending`

这是治理错误，不是单纯 UX 问题。

## 2. Review runtime 的协议摩擦过高

当前 review lane 的复杂度已经偏离“独立 reviewer 审查 formal package”的本意：

- reviewer 写 raw findings
- closer 再解释 raw findings
- closer 还要求严格枚举值和严格 findings 形状
- 小格式错误会触发整轮返工

这会让主线程反复维护协议细节，而不是推进研究治理。

## 3. Stale cycle 语义不够硬

author outputs 一旦变化，旧 request / receipt / closure 理应失效；但如果 stale 语义没有被 deterministic 收紧，就容易出现：

- 旧 reviewer 审过的 digest 继续被误认为当前有效
- 旧 closure 和新 formal outputs 混在一起
- 用户感知成“为什么 review 老是在绕圈”

## 4. Child lineage 边界必须继续收紧

`CHILD_LINEAGE` 是 failure governance 的正式分支，不是 review 不顺时的便捷出口。若 review lane 或 author lane 可以直接把“看起来像新题”升级成 child lineage，QROS 的 lineage 治理就会被削弱。

## Design Principles

### 1. Review eligibility 先于 review runtime

先判断“当前 stage 是否制度上允许进入 review”，再决定是否启动 reviewer。

### 2. Single truth, multiple projections

review 资格、blocking reason、recommended skill 必须来自同一个 deterministic truth layer；`session`、`progress` 和 stage review entry 只能投影它，不能各自重算。

### 3. Review runtime 只处理合法 review lane

一旦 stage 已被判定为不可 review，review runtime 不应再兜底解释它；它只负责合法 review lane 的 request / receipt / reviewer / closer / stale cycle 事务。

### 4. Hard fail means no review

hard gate fail 不是“reviewer 再看一次”的候选状态，而是 formal failure routing 的起点。

### 5. Child lineage remains formal-only

只有 failure / disposition 正式写出 `CHILD_LINEAGE`，系统才允许开 child lineage。

## Proposed Architecture

## A. Introduce a canonical review eligibility layer

新增一个统一判定层，供 runtime 内部消费。该层输入当前 lineage root 与 stage truth，输出结构至少包含：

- `eligible_for_review: bool`
- `blocking_reason_code`
- `blocking_reason`
- `review_blocking_surface`
- `authorized_review_skill: str | None`
- `requires_failure_handling: bool`
- `failure_stage: str | None`
- `failure_reason_summary: str | None`

这个层负责统一综合以下因素：

- 当前 detected stage
- artifact contract 是否满足 review-ready 基线
- semantic validator 是否 pass
- deterministic review preflight 是否 pass
- latest review closure / stale cycle / protected review state
- latest failure package / disposition routing
- lineage lock 是否 intact

任何调用方都不能重新拼一版“是否可以 review”的私有逻辑。

## B. Tighten stage-state semantics

在新模型下：

- `*_review_confirmation_pending` 只属于真正可审的 stage
- `*_review` 只属于已通过 review-entry 授权、且当前 review cycle 合法的 stage
- hard gate fail 不得再通过 stage 名伪装成 review-ready

因此，像 `csf_test_evidence` 这类在 author side 已知 `mean_rank_ic <= 0` 的 case，必须直接返回 failure-style blocking，而不是继续显示为 `csf_test_evidence_review_confirmation_pending`。

## C. Research session uses eligibility truth for routing

`runtime.tools.research_session` 不再在多个分支里零散判断 review 资格，而是统一依赖 canonical eligibility layer：

- `eligible_for_review = true`
  - 才允许进入 `*_review_confirmation_pending`
  - 才允许记录 `confirm_review`
  - 才允许推荐 `qros-*-review`
- `eligible_for_review = false`
  - 直接返回 failure-style blocking or disposition-required blocking
  - 不允许把 stage 暴露成 review-ready

这属于最小护栏，不是整套状态机重写。

## D. Progress becomes a projection, not an alternative truth

`runtime.tools.progress_runtime` 应复用同一 eligibility layer，只负责把 deterministic truth 投影成：

- `current_stage`
- `current_skill`
- `recommended_skill`
- `handoff_hint`
- `blocking_reason_code`

允许 `progress` 和 `session` 的显示文案不同，但不允许治理语义冲突。

## E. Review runtime focuses on cycle correctness and closure correctness

一旦 stage 已合法进入 review lane，review runtime 只处理 review lane 内部事务：

- request / receipt / handoff scope consistency
- reviewer write-scope audit
- raw findings normalization
- closer canonicalization
- stale cycle invalidation
- closure write

review runtime 不再承担“当前 stage 到底该不该 review”的主判断职责。

## F. Thin stage-specific review entry

stage-specific review skill 的入口职责收敛成两步：

1. 调统一 review eligibility / stage-entry guard
2. guard pass 后进入 `prepare -> reviewer -> closer`

guard fail 时，直接回报当前 stage 应走 failure handling 或其它 blocking reason；skill 本身不得越权补救。

## Canonical Boundary Rules

以下规则是新的 canonical review boundary：

1. `author success` 不等于 `review eligible`
2. contract / semantic / preflight 任一 hard fail => 不允许进入 review
3. `*_review_confirmation_pending` 只能代表“当前 stage 已制度上可审”
4. reviewer 只审可审对象，不替代 semantic gate
5. review 的非放行结论进入 formal failure routing，而不是继续假装普通 progression
6. `CHILD_LINEAGE` 只能来自 formal failure / disposition

## Review Runtime Hardening

## 1. Raw findings normalization

closer 前增加 deterministic normalizer，负责收敛 reviewer 常见的非恶意格式漂移，例如：

- `PASS` / `APPROVE` / `PASS_WITH_RESERVATIONS` 收敛成 canonical `review_loop_outcome`
- `blocking_findings` 的常见轻微形状偏差收敛成字符串列表
- 缺失但非关键的顶层字段填默认值

原则是“宽进严出”：

- reviewer 输入可以适度宽松
- closure 输出必须 canonical
- 真正缺核心语义时仍然 fail hard

## 2. Deterministic stale-cycle invalidation

review cycle 必须和当前 author outputs 绑定。至少要绑定：

- `review_cycle_id`
- `handoff_manifest_digest`
- current author digest
- request / receipt / final_review / audit

只要 author outputs 变化：

- 旧 cycle 立刻 stale
- 旧 closure 不能再证明当前 outputs
- 新 review 必须走新 cycle、新 digest、新 reviewer binding

## 3. Closure truth remains deterministic

即便增加 raw normalizer，也不能把 reviewer 变成 closure 真值的唯一解释器。最终 closure 仍然必须由 deterministic runtime 生成 canonical output，并显式记录：

- 当前 cycle 绑定的 reviewed scope
- write-scope audit 结果
- final verdict / review_loop_outcome
- whether closure applies to current outputs

## Module Boundaries

本次只建议动以下区域：

### 1. `runtime/tools/review_*`

主战场。负责：

- raw findings normalization
- closer canonicalization
- cycle versioning / stale invalidation
- request / receipt / final_review / audit consistency

### 2. `runtime/tools/research_session.py`

只补最小 review-entry 护栏，不做整套 orchestrator 重写。

### 3. `runtime/tools/progress_runtime.py`

只改为复用 eligibility truth，不保留第二套 review 资格判断。

### 4. `tests/session` and `tests/review`

增加 canonical review eligibility、session/progress 一致性、raw normalizer、stale cycle 的新测试，并删除把旧错误行为当成正确行为的旧 expectation。

### 5. `docs/guides` and `skills/*review*`

同步清理文档和 skill 口径：

- hard gate fail 不是 review lane 候选
- stage-specific review skill 不能越过 canonical eligibility guard
- child lineage 仍然只能从 formal failure / disposition 打开

## Migration Strategy

本次是不兼容清理，迁移顺序应固定为：

1. 先实现 canonical review eligibility layer
2. 让 `research_session` 改用它
3. 让 `progress_runtime` 改用它
4. 再收紧 review runtime normalizer / stale cycle
5. 最后统一 tests、docs、skills 口径

原因是：若先改 docs/skills 而真值层未统一，仓内会短时间出现更严重的语义分裂。

## Acceptance Criteria

以下条件全部满足，才算这次设计达标：

1. reviewer raw findings 不再因为常见格式问题产生多轮机械返工
2. author outputs 一旦变化，旧 review cycle deterministic stale
3. hard gate fail 的 stage 不能进入 `*_review_confirmation_pending`
4. `qros-session` 和 `qros-progress` 在 review 资格上保持一致
5. review 不顺、preflight fail、author 反复修都不能直接开 child lineage
6. stage-specific review skill 在 guard fail 时直接停止，不再制造“仍可 review”的错觉

## Test Plan

本次至少需要新增或重写以下测试族：

### Review eligibility truth tests

- contract + semantic + preflight 全 pass => eligible
- semantic fail => not eligible
- preflight fail => not eligible
- lineage lock broken => not eligible
- failure disposition required => not eligible

### Session / progress consistency tests

- 同一 lineage 在 review 相关边界上，`session` 和 `progress` 不再给出冲突的 stage / skill recommendation

### Review runtime normalization tests

- outcome alias 自动收敛
- findings 常见轻微形状漂移自动收敛
- 真缺核心语义时 deterministic reject

### Stale cycle tests

- author outputs 改变后旧 cycle stale
- 旧 closure 不能证明新 outputs
- 新 cycle 必须重新绑定 digest / reviewer

### Child lineage negative tests

- semantic fail 不能直接开 child lineage
- preflight fail 不能直接开 child lineage
- review FIX_REQUIRED 不能直接开 child lineage
- 只有 formal disposition = `CHILD_LINEAGE` 才允许开

## Risks

### 1. 旧测试会大面积翻红

这是预期内结果，因为这次不做兼容。真正要避免的不是翻红，而是保留错误 expectation。

### 2. 某些 stage-specific review 入口的历史行为会被直接废止

这是设计目标之一，而不是回归。

### 3. 如果最小护栏仍然挡不住状态机错路

那说明问题已经超出“review-runtime-first”的范围，应另开下一份 spec，做 session state machine 收敛，而不是在本次实现里继续堆 patch。

## Recommended Outcome

本设计推荐的实现方向是：

- 不做兼容
- 直接建立 canonical review eligibility truth
- 让 session / progress / review entry 共用这条真值
- 让 review runtime 专注于合法 review lane 的稳定执行
- 继续把 child lineage 锁在 formal failure / disposition 之后

这样能优先解决最危险的两类问题：

- 明明不该 review，却还被送进 review lane
- 明明只是 reviewer raw schema 抖动，却被放大成多轮 review 返工
