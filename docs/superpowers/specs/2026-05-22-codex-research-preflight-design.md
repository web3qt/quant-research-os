# Codex Research Preflight Design

## Context

会话 `019e4e11-5b7c-7d31-9a58-95f9a963039d` 暴露出的核心问题，不是某个单点 bug，而是整条 Codex 研究路径里有一批本应在前面确认或直接计算出来的事实，被拖到了 reviewer lane 才暴露。

结果是：

- 用户已经反复做了“确认”
- runtime 也已经多次推进 stage
- 但 reviewer 仍然在拦最基础的事实缺口
- 主线程越来越多地在修 review protocol、digest drift、request/closure schema，而不是推进研究本身

这类问题如果只按单条 lineage 修补，下次用户研究一个新策略，仍然会踩到同样的坑。

因此，这份设计不把目标限定为“修会话 `019e4e11...`”，而是把它提升成一个通用能力：

- 把能在研究前段确认的事实前置确认
- 把能由 runtime / 数据源直接决定的事实前置计算
- 把 review 从“替系统发现基础问题”收窄成“审真正值得审的东西”

## Problem Statement

当前 Codex 上的 QROS 研究流程，存在三个结构性问题。

### 1. 泛化确认词和具体 gate 没有强绑定

用户常输入：

- `接受`
- `确认`
- `确认全部`
- `确认进入`
- `进入`

这些词如果没有被系统绑定到一个唯一 gate，用户会默认“当前这一步已经被确认了”，但实际 runtime 可能还停留在：

- admission verdict 未落盘
- freeze group digest 未更新
- final stage approval 未写入
- next-stage confirmation 尚未发生

这会制造持续性的状态错觉。

### 2. review 承担了太多前置事实确认工作

当前 reviewer 经常在 review lane 才暴露的问题包括：

- 数据时间覆盖范围与冻结时间窗不一致
- route 其实还没锁清
- factor / signal / contract identity 仍不够明确
- stage program 只是薄 wrapper 或 provenance 不可信
- run manifest / evidence binding 仍有明显缺件

这些不属于“reviewer 独立判断的高价值部分”，而是本应在更前面的 gate 就被挡下的前置条件问题。

### 3. review lane 的协议复杂度吞噬了研究推进

当基础事实没有前置锁死时，review lane 不只是给 verdict，而是开始承担：

- author digest 绑定
- stale cycle 归档
- request / receipt / final_review 对齐
- closure / proof-chain / runtime-state 收口

一旦 reviewer 再发现 formal package 仍不稳定，主线程就会陷入“修 review protocol 本身”的循环。这会极大稀释用户的研究体验。

## Goal

建立一套适用于 Codex 上所有 QROS 新研究线的前置确认与前置计算机制，使系统在进入 reviewer lane 之前，已经锁死或算清绝大多数基础事实。

目标不是减少 rigor，而是重新分配 rigor：

- 前段 gate 负责锁事实
- runtime 负责算确定性真值
- reviewer 负责审高价值判断

## Non-Goals

- 不重写 QROS 的全部 stage contract
- 不取消 reviewer 独立性
- 不把所有错误都前置成 admission 阶段处理
- 不试图把所有策略研究差异都抽象成一套万能问卷
- 不减少 failure handling / child lineage / change control 的治理强度

## Design Principles

### 1. Review is not a first-pass discovery engine

reviewer 不应成为第一轮“帮系统发现最基础问题的人”。

### 2. Ask once, bind once

能通过用户确认锁死的问题，尽量只问一次，并明确绑定到唯一 gate。

### 3. Compute before you ask a human to review

凡是可以从真实数据、真实 artifact、真实 runtime 直接算出的事实，应优先由系统计算，而不是交给 reviewer 判断。

### 4. Freeze facts before freeze opinions

先锁事实层，再锁研究判断层。否则后面的所有 stage 都会反复暴露同一个前提问题。

### 5. New lineages should inherit discipline automatically

这套机制必须对未来新策略自动生效，而不是只对当前某条 lineage 特判。

## Proposed Architecture

## A. Add a research preflight layer before review-heavy stages

在当前主流程中，增加一个明确的“前置事实层”。它不替代 author，也不替代 reviewer，而是在关键阶段之间插入一层 deterministic preflight truth。

优先加在以下边界：

- `mandate_admission -> mandate_freeze_confirmation_pending`
- `mandate_freeze_confirmation_pending -> mandate`
- `mandate review pass -> next-stage confirmation`
- `*_author complete -> *_review_confirmation_pending`

这个 preflight layer 只做一件事：

- 判断当前 stage 是否已经具备进入下一步的基础事实条件

## B. Split preflight facts into two categories

### User-confirmed facts

必须由用户显式确认的事实，例如：

- 研究问题到底是什么
- 路由到底是 `cross_sectional_factor` 还是 `time_series_signal`
- 哪些路线被排除
- 哪些假设被视为 kill criteria
- 哪些表达式模板属于当前研究身份

### Runtime-derived facts

必须由 runtime 直接计算的事实，例如：

- 数据源最早/最晚时间
- 可用 symbol 范围
- bar size / interval
- 数据是否覆盖冻结的 train/test/backtest/holdout
- required stage program / required provenance 是否存在
- required machine artifacts 是否为真实、可读、非 placeholder

这两类事实要明确分开，避免把“需要用户拍板的”与“应该系统自己算的”混在一起。

## C. Introduce explicit preflight contracts

建议新增或显式化以下 preflight contract 概念。

### 1. `data_viability_contract`

锁定：

- 数据源路径
- 数据资产类别
- interval / bar size
- 当前 repo 内可见的数据时间覆盖
- 是否足够支撑当前研究路线

### 2. `time_coverage_contract`

锁定：

- `train/test/backtest/holdout` 是否都落在真实数据覆盖内
- 若不满足，是 admission 阶段就应重写窗口，还是 mandate freeze 时拒绝确认

### 3. `route_viability_contract`

锁定：

- 当前研究问题和 route 的一致性
- 当前表达方式究竟是在做横截面排序，还是单资产时间序列判断

### 4. `expression_identity_contract`

锁定：

- 因子/信号/突破质量分数的基本表达式模板
- 当前研究允许变化的参数维度
- 当前研究不允许 downstream 自由改写的部分

### 5. `provenance_viability_contract`

锁定：

- stage program 是否 lineage-local
- 是否存在关键 provenance 字段
- 是否已经明显存在 “real_input / synthetic_input” 语义冲突

## D. Move common blockers out of reviewer lane

以下类型的问题应尽量在 reviewer 之前拦下：

- 冻结时间窗与真实数据覆盖不一致
- route 与研究问题不匹配
- factor / signal / score 的基本定义未冻结
- stage program 是薄 wrapper 或 provenance 明显不可信
- required machine artifacts 是空壳或 placeholder
- run manifest / formal evidence binding 缺关键字段

如果这些问题在 preflight 已经能判定，就不应再让 reviewer 成为第一发现者。

## E. Narrow reviewer scope

前置事实层建立后，reviewer 的工作应收窄为三类：

### 1. Stage-local gate satisfaction

当前 formal package 是否真的满足本 stage 的 gate，而不是只满足 artifact shape。

### 2. Research semantic drift

当前 author outputs 是否偷偷改题、改 route、改 expression identity、改 universe 语义。

### 3. Governance outcome

当前 stage 的：

- residual risk
- rollback stage
- downstream permissions
- 是否需要进入 failure handling / disposition

这才是 reviewer 的高价值部分。

## F. Strengthen confirmation UX

为了避免泛化确认词制造状态错觉，系统在每次确认前应尽量显式回显：

- 当前正在确认的是哪一个 gate
- 这次确认会写哪个 artifact
- 确认后下一步预期进入哪个状态

例如，不再只问“是否确认”，而是应清楚表述：

- 是否接受进入 `mandate_freeze_confirmation_pending`
- 是否确认当前 5 个 `csf_data_ready` freeze groups
- 是否确认进入 `mandate review`
- 是否确认进入 `csf_data_ready review`

用户仍然可以回答“确认”，但系统必须在内部先把当前确认对象唯一化。

## Expected User Experience Change

如果这套机制成立，未来用户在 Codex 上研究新策略时，体验应变成：

1. 先确认研究问题和路由
2. 系统先自动核对数据覆盖与基本 contract
3. 用户再确认冻结组
4. 系统构建 formal package
5. 只有当前 stage 真正 review-eligible 时，才进入 `CONFIRM_REVIEW`
6. reviewer 主要审研究语义和治理结论，而不是反复抓基础事实缺口

## Expected Runtime Change

runtime 应逐步形成两层清晰语义：

### 1. Preflight blocking semantics

这层回答：

- 当前为什么还不能进下一步
- 是用户没确认，还是数据不够，还是 contract 没锁，还是 program/provenance 不成立

### 2. Review blocking semantics

这层只在 preflight facts 已经满足后才成立，回答：

- 当前 formal package 是否通过 reviewer gate
- 如果不通过，是 author-fix、failure handling、还是 formal disposition

## Risks

### 1. 前置确认过多，用户会觉得更繁琐

缓解方式：

- 不是什么都问用户
- 能算的绝不问
- 能复用上游冻结的绝不重复问

### 2. 过早冻结表达式，可能抑制研究探索

缓解方式：

- admission / mandate 只冻结“研究身份级别”的表达式模板
- 参数级探索仍留给 downstream stage

### 3. Preflight 逻辑太重，会拖慢普通推进

缓解方式：

- 只把高复发、恢复成本高的问题前置
- 优先覆盖最伤用户体验和最难恢复的那批共性断点

## Acceptance Criteria

这份设计成立后，应至少达到：

1. 同类新研究线不再反复在 reviewer lane 首次暴露数据覆盖与时间窗冲突
2. route、expression identity、basic provenance 这类问题在 reviewer 之前就已被确认或拒绝
3. `review` 的主要发现从“基础事实没锁住”转向“stage-local gate / semantic drift / governance outcome”
4. 用户的“确认”输入更少依赖聊天语境猜测，而更多绑定到单一 gate
5. 新策略研究时，即使完全换一条 lineage，也能复用同一套前置纪律

## Recommended Next Step

下一步不应直接写实现代码，而应把这份设计拆成一个 implementation plan，明确：

- 哪些 preflight contracts 先落地
- 哪些 gate 先改
- 哪些 prompt / runtime / docs / tests 一起改
- 哪些改动属于 product UX，哪些属于 deterministic runtime
