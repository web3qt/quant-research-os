# 2026-04-20 Review Session Separation Checklist

## 目标

把 review 从“主 author 会话里半自动编排 reviewer”改成：

- review 由人显式在独立 session 发起
- author resume 也由人显式发起
- runtime 不再替主线程偷偷编排 reviewer
- runtime 继续强约束 review cycle / stale / closure / 并发冲突

这份清单只保留最小迁移步骤，不展开大设计。

## 当前问题

当前主研究会话仍承担了过多 review 编排职责：

- 自动 issue review request
- 自动决定何时起 reviewer 子代理
- 主线程直接处理 stale cycle 清理
- author / review lane 在一个会话里来回切换

结果是：

- 边界不够硬
- 调试成本高
- review 独立性依赖线程内约定而不是显式 session 边界

## 目标状态

### Author Session

- 只负责 freeze / build / author fix
- 最多推进到 `*_review_confirmation_pending`
- 不再自动 spawn reviewer
- 不再自动 issue active review request
- 不再自动做 review closure

### Review Session

- 由人显式发起
- 进入时先向 runtime 注册 active review cycle
- 只允许 review scope 内读写
- reviewer 只写 `reviewer_findings.raw.yaml`
- deterministic closer 负责 canonical result / audit / closure

### Runtime

- 记录当前 stage
- 记录 review state
- 记录 active review cycle
- 记录 request 绑定的 author outputs digest
- 记录 stale / closure / verdict
- 拒绝同一 stage 并发 active review

## 最小实施步骤

### Step 1: 增加 review_state 真值层

在 runtime 状态模型里明确区分：

- `author_ready_for_review`
- `review_in_progress`
- `awaiting_author_fix`
- `review_closed_pass`
- `review_closed_nonadvancing`

最低需要新增或稳定这些字段：

- `active_review_cycle_id`
- `review_state`
- `review_requested_at`
- `review_bound_author_digest`
- `last_review_verdict`
- `closure_written_at`

### Step 2: 停止 author 主线程自动编排 reviewer

从 `qros-session` 主路径里移除：

- 自动 issue active review request
- 自动 spawn reviewer
- 自动驱动 reviewer proof chain
- 自动触发 deterministic closure

保留：

- 到 `*_review_confirmation_pending` 的推进
- `review-ready` preflight
- 清晰 `resume_hint`

### Step 3: 引入 review session 的显式入口

需要一个稳定入口，至少支持：

- 指定 `lineage_id`
- 指定 `stage`
- 注册新的 active review cycle
- 绑定当前 author outputs digest
- 拒绝当下已有 active review cycle 的重复启动

入口形式可以是：

- 新 wrapper，例如 `qros-start-review`
- 或各 `qros-*-review` skill 统一第一步强制调用 runtime 注册

关键点不是命令名，而是“进入 review session 必须先注册 active cycle”。

### Step 4: 把 stale cycle archive 内建化

当前 stale cycle 不应再由主线程手工 `mv`。

runtime 应提供唯一做法：

- 旧 cycle 从 `review/request/*` / `review/result/*` 移到 `review/archive/`
- archive 命名稳定，保留 `review_cycle_id`
- active slot 始终只保留当前 cycle 文件

### Step 5: author resume 必须显式

当 verdict 是：

- `FIX_REQUIRED`
- `RETRY`
- `PASS FOR RETRY`

runtime 只给：

- `awaiting_author_fix`
- `resume_hint`
- `allowed_modifications`

但不自动切回 author 执行。

恢复 author lane 必须由人显式触发。

### Step 6: closure 只由 review session 完成

review session 成为唯一合法 closer：

- raw findings
- canonical result
- write-scope audit
- closure artifacts

author session 只重新读取 closure 结果，不直接写 closure。

## 要删掉的旧行为

- 主 author 会话里自动 spawn reviewer
- 主 author 会话里自动推进 reviewer 生命周期
- 主 author 会话里手工处理 stale review files
- 把 review 和 author 当成同一会话里的两段子流程

## 要保留的旧行为

- stage-specific 固定 review skill 映射
- request / receipt / result / audit / closure 的 deterministic contract
- stale 判定
- reviewer write-scope audit
- closure 产物作为最终推进真值

## 验收标准

### 行为验收

- author session 停在 `*_review_confirmation_pending` 后，不会再自动起 reviewer
- 人显式开 review session 后，runtime 注册 active cycle
- review session 未结束前，第二个 review session 不能并发进入同一 stage
- review 完成后，author session 只读取状态，不再代跑 closure
- verdict 需要修复时，runtime 只给 `awaiting_author_fix`，不自动回 author lane

### 约束验收

- 同一 stage 同时只有一个 active review cycle
- author outputs 更新后，旧 cycle 必定 stale
- stale cycle archive 不需要人工 `mv`
- closure 一旦写出，session 只认 closure，不再被旧 result 干扰

### 测试验收

至少新增覆盖：

- review session 注册 active cycle
- 并发 review session 拒绝
- author resume 显式化
- stale cycle 自动 archive
- closure 后 session 只认 closure

## 非目标

这轮不做：

- reviewer judgement 全量 deterministic 化
- 新数据库或后台服务
- 改变 stage gate / checklist 真值的语义边界
- 一次性重写所有 author / review skills

## 关联文档

- [QROS Review Constraint Map](../guides/qros-review-constraint-map.md)
- [QROS Review Shared Protocol](../guides/qros-review-shared-protocol.md)
- [QROS Research Session Usage](../guides/qros-research-session-usage.md)
