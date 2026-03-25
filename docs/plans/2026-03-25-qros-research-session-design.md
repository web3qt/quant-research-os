# QROS Research Session Design

**Date:** 2026-03-25  
**Status:** Draft approved for direction  
**Scope:** `Codex-only`, `single orchestrator skill`, `idea_intake -> mandate -> mandate_review`

## Goal

把当前“用户记技能 + 手动敲脚本”的使用方式，升级成一个真正的对话式研究入口。

第一版只解决一件事：

- 新增一个统一入口 skill：`qros-research-session`
- 让用户从一个 skill 开始对话
- skill 自动推进 `idea_intake -> mandate -> mandate_review`
- 只有遇到关键信息缺失、gate 分歧或明确治理选择时才停下来问

## Core Principle

这层不是替换当前脚本和 runtime，而是把它们藏到统一入口后面。

所以目标不是：

`skill 解释流程 -> 用户记命令 -> 用户手动推进`

而是：

`skill 对话 -> orchestrator 判断阶段 -> runtime 写盘 -> skill 汇报状态`

这与 `gstack` 的核心范式一致：

- 流程先于工具
- 统一入口
- 显式阶段推进
- 底层 runtime 隐藏在高层 skill 后面

## Current Gap

当前仓库已经有：

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`
- `scaffold_idea_intake.py`
- `build_mandate_from_intake.py`
- `run_stage_review.py`

但用户体验仍是分裂的：

- 用户要记多个 skill 名称
- 用户还要记 2 到 3 个脚本命令
- skill 和 runtime 没有统一的阶段编排入口

这会让系统看起来像“有很多能力”，但不像“有一个工作流”。

## Recommended Direction

第一版新增一个 orchestrator skill：

- `qros-research-session`

它不替代已有 skill 和脚本的能力，而是复用它们：

- 复用 `idea_intake` 的 author discipline
- 复用 `mandate` 的 author discipline
- 复用 `mandate review` 的 gate discipline
- 复用现有 runtime 和 review engine

用户面对的是一个入口，系统内部仍然分层。

## Approaches Considered

### Approach A: Thin Router

只新增一个 skill，负责识别当前阶段，然后把用户导向现有 skills 和命令。

优点：

- 改动最小
- 复用率高

缺点：

- 仍然要求用户记脚本
- 仍然暴露内部结构
- 不是真正的对话式编排

### Approach B: Single Orchestrator

新增一个总入口 skill，内部自动：

- 创建或识别 lineage
- scaffold `00_idea_intake`
- 通过对话补齐 intake artifacts
- gate 通过后生成 mandate
- 进入 mandate review

优点：

- 最符合“通过一个 skill 开始对话”的目标
- 能复用当前 runtime，不推翻现有底座
- 第一版范围清晰

缺点：

- skill 设计更复杂
- 需要清楚定义阶段识别和停顿点

### Approach C: Full Session Engine

单独引入更完整的 session runtime / state machine，再让 skill 只是调用会话引擎。

优点：

- 长期扩展性最好
- 更容易统一到更后面的 `data_ready`、`signal_ready`

缺点：

- 第一版范围过大
- 会同时做编排器、状态机和更多 runtime 抽象

## Recommendation

第一版采用 **Approach B: Single Orchestrator**。

原因：

- 用户明确希望“从一个 skill 开始对话”
- 现有 runtime 已足够支撑最小闭环
- 当前最缺的是统一入口，不是新一层更大的基础设施

## First-Wave Scope

第一版只覆盖：

- `00_idea_intake`
- `01_mandate`
- `mandate review`

不覆盖：

- `data_ready`
- `signal_ready`
- 更后续的训练、测试、回测、holdout、shadow

这样可以确保第一刀真正闭环，而不是把整个系统再次拉大。

## User Experience

理想的一次使用是：

1. 用户调用 `qros-research-session`
2. 用户描述 raw idea
3. skill 自动识别或创建 lineage
4. skill 自动写 `00_idea_intake/` 基础 artifacts
5. skill 通过对话补齐 intake 内容
6. skill 形成 `idea_gate_decision.yaml`
7. 若 verdict = `GO_TO_MANDATE`，自动生成 `01_mandate/`
8. skill 继续推进 mandate authoring
9. skill 生成 `review_findings.yaml`
10. skill 自动调用 review engine，写 closure artifacts

用户不需要记住底层脚本。

## Architecture

建议拆成四层。

### 1. Conversation Layer

由 `qros-research-session` 承担：

- 接收 raw idea
- 提问并收集关键信息
- 汇报当前阶段
- 汇报本次写盘结果
- 决定是否继续推进或停下来等用户决策

### 2. State Layer

正式状态以磁盘 artifacts 为主，对话上下文为辅。

主要状态根：

- `outputs/<lineage>/00_idea_intake/`
- `outputs/<lineage>/01_mandate/`
- `review` closure artifacts

也就是说：

- 对话决定内容
- 文件决定状态

这样在任意时刻，另一个 agent 或下一次会话都能恢复上下文。

### 3. Orchestration Layer

新增一个轻量编排 runtime，用于：

- 识别或创建 lineage
- 判断当前 stage
- 决定下一步动作
- 调用现有脚本和 helper

建议新增：

- `tools/research_session.py`
- `scripts/run_research_session.py`

这层应是 skill 的稳定后端，而不是把全部逻辑塞进 `SKILL.md`。

### 4. Gate Layer

继续复用当前 gate / review 规则：

- `idea_gate_decision.yaml` 不过，不能进 mandate
- `mandate review` 不通过，不能假装下一阶段已开放

这意味着 orchestrator 不是快捷方式，而是合规入口。

## Stage Detection

第一版建议按磁盘状态决定阶段：

### No Lineage Yet

如果没有给定 lineage，或指定 lineage 不存在：

- 从 raw idea 派生一个 slug
- 创建 `outputs/<lineage>/`
- scaffold `00_idea_intake/`
- 当前阶段 = `idea_intake`

### Intake In Progress

如果 `00_idea_intake/` 存在，且：

- 缺 intake 必需 artifacts
- 或 `idea_gate_decision.yaml.verdict != GO_TO_MANDATE`

则继续 `idea_intake`。

### Mandate Authoring

如果：

- `idea_gate_decision.yaml.verdict == GO_TO_MANDATE`
- 但 `01_mandate/` 缺正式产物

则调用 mandate build，并进入 mandate authoring。

### Mandate Review

如果：

- `01_mandate/` 已存在必需产物
- 但还没有最新 review closure artifacts

则进入 mandate review。

### Mandate Review Complete

如果 mandate review closure artifacts 已存在，则 orchestrator 不继续越权推进，而是：

- 汇报当前 stage 已收口
- 指出下一步将是未来的 `data_ready`

## Orchestration Flow

第一版建议固定流程：

1. resolve lineage
2. detect stage
3. scaffold intake if needed
4. gather intake content
5. write/update intake artifacts
6. compute `idea_gate_decision.yaml`
7. if `GO_TO_MANDATE`, build mandate artifacts
8. fill/update mandate narrative artifacts
9. create/update `review_findings.yaml`
10. run review engine
11. report stage result and next action

## Interaction Rules

第一版只在必要时停下来问。

### Ask The User Only When

- 缺研究边界：市场、标的、周期、任务定义
- 缺 counter-hypothesis
- 缺 kill criteria
- qualification 存在明显治理分歧
- 需要用户确认是 `NEEDS_REFRAME` 还是 `DROP`

### Do Not Ask The User When

- 只是缺目录或模板文件
- 需要执行确定性的 scaffold / build / review 脚本
- 能从已有 artifacts 明确推断当前 stage

## Status Reporting

每次 orchestrator 推进后，统一给用户返回：

- `lineage`
- `current_stage`
- `artifacts_written`
- `gate_status`
- `next_action`

这样用户不需要再猜“系统现在到哪了”。

## Internal Reuse

第一版应最大程度复用已有资产。

### Reused Skills As Discipline Sources

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`

即使 orchestrator 不显式“调用 skill”，也应复用这些 skill 中定义的工作纪律和产物契约。

### Reused Runtime

- `tools/idea_runtime.py`
- `tools/review_skillgen/review_engine.py`
- `scripts/scaffold_idea_intake.py`
- `scripts/build_mandate_from_intake.py`
- `scripts/run_stage_review.py`

第一版尽量不重写已有稳定逻辑。

## New Assets

建议第一版新增：

- `.agents/skills/qros-research-session/SKILL.md`
- `.agents/skills/qros-research-session/agents/openai.yaml`
- `tools/research_session.py`
- `scripts/run_research_session.py`
- `docs/experience/qros-research-session-usage.md`

## Minimal Runtime Contract

`tools/research_session.py` 建议提供这类能力：

- `resolve_lineage(...)`
- `detect_session_stage(...)`
- `ensure_intake_scaffold(...)`
- `build_mandate_if_admitted(...)`
- `run_mandate_review_if_ready(...)`
- `summarize_session_status(...)`

这层负责确定性动作，不负责研究性判断。

## Non-Goals

第一版不做：

- 把所有后续 stage 一次性编排进去
- 统一所有 skill 为单一 mega-skill
- 会话级数据库或远程状态存储
- 全自动代替用户做所有治理判断

这些都应该留到第二阶段。

## Expected Outcome

完成后，用户的体验会从：

`安装 -> 记 skill -> 记脚本 -> 手动推进`

变成：

`安装 -> 调用 qros-research-session -> 对话推进研究`

这才是当前系统从“有底座”走向“有工作流入口”的关键一步。
