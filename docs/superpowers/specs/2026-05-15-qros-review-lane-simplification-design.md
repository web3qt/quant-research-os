# QROS Review Lane Simplification Design

## Context

一条真实的 QROS 研究会话暴露出一个核心问题：系统复杂度正在从“研究治理”滑向“治理协议治理”。

原本用户期望的是一条直观路径：

1. author 产出当前 stage formal artifacts
2. 独立 reviewer 审查这些 artifacts
3. 如果 reviewer 发现问题，主线程继续修复
4. 修复后重新 review，直到通过或进入失败处理

但当前 review lane 已经膨胀为：

- launcher prepare
- reviewer receipt
- handoff manifest
- reviewer raw findings
- deterministic closer
- canonical review result projection
- closure artifacts
- latest review pack sync

这套链条的目标本来是增强独立性、可审计性和 deterministic closure；但实际代价是：

- reviewer 明明只是给出 findings，却要配合多层中间协议
- 主线程需要花大量精力修补 receipt/raw/closure 之间的结构漂移
- review 结果可能在 raw、closer、runtime state 之间不一致
- 出现错误时，agent 容易开始“维护 review 协议本身”，而不是推进研究

这份设计只讨论一个收缩方向：**在保留独立 reviewer 的前提下，显著简化 review lane。**

## Goal

将 QROS review lane 简化到如下目标态：

- review 仍然必须由独立 reviewer 子 agent 完成
- reviewer 仍然不得修改 `author/formal/*`
- reviewer 直接写最终、唯一、机器可读的 review 结果
- 主线程不再扮演 closer，也不再解释 reviewer 原始意图
- 主线程只负责读取最终 verdict，并按规则推进 author-fix、next-stage、failure handling 或 child lineage

## Non-Goals

- 不移除 immutable ledger
- 不移除 child lineage / failure handling / change control
- 不降低 freeze、formal artifact、review 独立性这些治理底线
- 不试图在这一轮同时重写全局 stage 状态机
- 不要求一次性重构所有 stage author/review skills 的业务判断逻辑

## Problem Statement

当前 review lane 的问题不在于“review 不该复杂”，而在于复杂度集中在了错误的地方。

### 1. Review 结果被拆成多段真值

reviewer 写 raw findings，closer 再合并成 canonical result，closure 再投影成另一组 artifacts。这样会出现：

- reviewer raw 看起来是 pass-like
- closer 经过 deterministic checks 变成 `RETRY`
- 主线程此前却已经按 pass-like 心智在推进

这会让“谁在给 verdict”变得不清楚。

### 2. 独立性保障和协议栈绑定过深

当前系统把 reviewer 独立性、repo root 绑定、write scope audit、canonical closure 全都绑在 receipt/raw/closer 这条链上。结果是：

- 想保独立 reviewer，就必须保整套协议
- 想删掉复杂度，就会担心独立性一起丢掉

这说明边界没有被切干净。

### 3. 主线程在 review 后的动作过于依赖中间状态

主线程本来只应该关心：

- 当前最终 verdict 是什么
- 允许修哪些内容
- 是否还能在原 lineage 上继续

但现在主线程还要处理：

- stale raw
- consumed raw
- closer partial success
- projection drift
- latest review pack sync failure

这些都不是研究推进层应该背负的复杂度。

## Design Principles

### 1. Reviewer judges, main thread acts

reviewer 负责做独立判断并写最终 review 结果。  
主线程负责读取结果并采取后续动作。  
两者职责必须清楚分离。

### 2. One canonical review artifact

review lane 只能有一个 reviewer-owned 的最终真值文件。  
不再允许 raw result、merged result、closure projection 之间多段真值并存。

### 3. Keep independence, remove protocol layers

保留 reviewer 子 agent 和写边界；删除为此额外引入的 receipt/raw/closer 中间层。

### 4. `FIX_REQUIRED` and `RETRY` must diverge hard

`FIX_REQUIRED` 代表普通 author-fix。  
`RETRY` 代表不能再视作普通修复。  
这两条路径必须在主线程动作层面明确分开。

## Proposed Architecture

### High-Level Flow

简化后的 review lane 收敛为四步：

1. 主线程确认 stage 已 review-ready
2. 主线程创建独立 reviewer 子 agent，并提供明确 handoff
3. reviewer 读取允许范围内的 request/formal artifacts，直接写最终 review result
4. 主线程读取该最终 review result，并据此推进 runtime 状态

新的主路径是：

`spawn reviewer -> handoff -> reviewer writes canonical review -> main thread reads verdict`

原来的这些层全部删除：

- `reviewer_receipt.yaml`
- `reviewer_findings.raw.yaml`
- `qros-review` closer
- closer 生成的中间 canonical merge
- 依赖 closer 才能写出的额外 closure projection

## Reviewer Write Boundary

reviewer 仍然必须是独立子 agent，且写权限仍严格限制在 review 目录内。

保留以下约束：

- reviewer 不能修改 `author/formal/*`
- reviewer 不能修改 `review/request/*`
- reviewer 不能修改 lineage root 下的非 review 文件
- reviewer 只允许写入最终 canonical review artifact

### Single Write Target

建议 reviewer 的唯一正常写入目标为：

- `review/final_review.yaml`

这个文件直接取代现有的：

- `review/result/reviewer_findings.raw.yaml`
- `review/result/adversarial_review_result.yaml`
- 以及依赖 closer 再投影出的 pass/fail closure 中间语义

## Canonical Review Artifact

`review/final_review.yaml` 是 reviewer-owned、machine-readable、single-source-of-truth 的最终结果。

建议包含四类字段。

### Identity

- `lineage_id`
- `stage_id`
- `reviewer_identity`
- `reviewer_agent_id`

### Reviewed Scope Binding

- `reviewed_artifact_paths`
- `reviewed_program_path`
- `reviewed_artifact_digest`
- `reviewed_program_digest`

这里的重点不是复刻 receipt，而是直接绑定“reviewer 审的是哪一版 outputs / program”。

### Verdict and Findings

- `verdict`
- `review_summary`
- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`

### Main-Thread Governance Fields

- `allowed_modifications`
- `rollback_stage`
- `downstream_permissions`
- `recommended_next_action`

这样 reviewer 一次写完它想表达的最终治理判断。  
主线程不再负责把 reviewer 的“原始意图”翻译成另一份 canonical 结果。

## Main Thread Behavior

主线程不再 close review，而是消费 review。

### PASS

- 进入 `*_next_stage_confirmation_pending`

### CONDITIONAL PASS

- 同样进入 `*_next_stage_confirmation_pending`
- reservations 只留在 `review/final_review.yaml`
- 不再额外生成另一套 conditional-pass closure 语义

### FIX_REQUIRED

- 回到当前 stage 的 `author-fix`
- 允许主线程修当前 stage 的 draft、program、formal artifacts
- 修完后必须重新发起一轮全新 review

这是普通修复路径，也是 review 后“主线程继续解决问题”的标准场景。

### RETRY

- 不视为普通 author-fix
- 不允许主线程直接 replay 原 locked formal artifacts
- 进入 failure / retry protocol

也就是说，主线程当然继续解决问题，但它解决问题的 lane 不能再假装是普通 `author-fix`。

### NO-GO

- 停止推进
- 输出终止结论

### CHILD LINEAGE

- 停止在原 lineage 上继续修
- 转为 child lineage handoff

## What Gets Removed

### Remove Entirely

- `reviewer_receipt.yaml`
- `reviewer_findings.raw.yaml`
- `qros-review` closer as raw-to-final merger
- closer-owned `adversarial_review_result.yaml`
- raw consumed / receipt mismatch / projection drift / closure partial success 这类 review-lane-only 中间态

### Keep

- 独立 reviewer 子 agent
- reviewer 只读 `author/formal/*`
- reviewer 只能写 review 目录
- final review artifact 的固定 schema
- reviewed output/program digest 绑定
- 主线程基于 verdict 推进状态

### Weaken

`closure` 不再是一整套额外文书系统，而退化为：

- 一个合法存在的 `review/final_review.yaml`
- runtime 已消费该 verdict 并更新 stage state

换句话说，closure 变成状态事实，而不是另一条协议栈。

## Migration Shape

为了降低迁移风险，建议分两步落地。

### Phase 1: Introduce the new canonical file

- 新增 `review/final_review.yaml`
- 允许 reviewer 直接写该文件
- 主线程开始优先读取该文件
- receipt/raw/closer 暂时仍保留，但不再作为普通路径必需

### Phase 2: Retire legacy review protocol

- 移除 `reviewer_receipt.yaml`
- 移除 `reviewer_findings.raw.yaml`
- 移除 `qros-review` closer
- runtime 只消费 `review/final_review.yaml`

这样能先验证新路径的可用性，再删除旧协议。

## Why This Is Simpler

这版设计的简化不在于“少几个文件”，而在于把职责重新拉直：

- reviewer 不再写 raw，然后等别人替它完成 review
- 主线程不再一边说自己不是 reviewer，一边又靠 closer 再解释 reviewer 意图
- 最终 verdict 不再分散在 raw、canonical result、closure、runtime state 多处

用户心智也会更接近期望：

1. reviewer 独立给意见
2. reviewer 直接写最终结果
3. 主线程看结果继续修或推进

这比当前协议栈更符合“review 发现问题之后，主线程继续解决问题”的直觉。

## Risks

### 1. Lose some fail-closed checks if removed too early

如果 receipt/raw/closer 还承担了 runtime 当前唯一的 identity/digest 校验职责，那么在 Phase 1 前不能直接硬删。  
需要先把必要绑定平移到 `review/final_review.yaml` 读取逻辑上。

### 2. Reviewer schema must be stable

因为 reviewer 直接写 final result，这个 schema 一旦经常改，负担会重新回到 reviewer 侧。  
因此 final review schema 必须尽量小且稳定。

### 3. Main-thread overreach must stay prohibited

简化 review lane 不代表主线程可以回去自审。  
runtime 仍应硬性禁止主线程生成 reviewer-owned final review artifact。

## Recommendation

推荐采用：

- **独立 reviewer 子 agent保留**
- **reviewer 唯一写入 `review/final_review.yaml`**
- **主线程不再调用 closer，只消费最终 verdict**

这是在你当前偏好下最合适的收缩点：

- 保留 `A` 独立性
- 保留 `B` reviewer 不碰 `author/formal`
- 保留 reviewer 直接写最终结果
- 砍掉现在最重、最容易漂移的 review 协议中间层

它不会把 QROS 退化成“主线程自己 review”，也不会继续维持目前这条过重的 review 协议栈。
