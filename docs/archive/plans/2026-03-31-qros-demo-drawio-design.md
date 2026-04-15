# QROS Demo Draw.io Design

**Goal:** 生成一个可直接在 `draw.io` / `diagrams.net` 打开的双页 `.drawio` 文件，用于演示 QROS 的整体定位和主流程。

**Audience**

- 老板：看项目定位、治理价值、组织收益。
- 开发：看 runtime、skills、artifacts、review 和 failure routing 的关系。
- 研究员：看从 idea 到 holdout 的主研究路径。

**Approved Approach**

- 生成一个单文件：`docs/show/qros-demo.drawio`
- 双页结构：
  - 第 1 页：`Overview`
  - 第 2 页：`Flow`

**Design**

## Page 1: Overview

- 用一张高层总览图回答“QROS 是什么”。
- 核心结构：
  - `Raw Idea`
  - `Idea Intake`
  - `Mandate Freeze`
  - `QROS Governance Layer`
  - `Runtime / Skills / Session`
  - `Outputs / Research Line`
- 治理层展开 5 个子点：
  - `Stage Contract`
  - `Formal Artifacts`
  - `Review Gates`
  - `Failure Handling`
  - `Lineage Control`
- Runtime 展开 3 个子点：
  - `qros-research-session`
  - stage-specific skills
  - `outputs/<lineage_id>/<stage>`
- 结果层展开 4 个子点：
  - 可复现
  - 可审查
  - 可恢复
  - 可晋级 / 回退 / 开子谱系

## Page 2: Flow

- 用一张主流程图回答“QROS 怎么运转”。
- 在左侧增加一个 `idea_intake` 案例化提问面板，直接展示：
  - `recommended_route`
  - `market / data_source / bar_size`
  - `universe`
  - `target_task`
  - `primary_hypothesis / counter_hypothesis`
  - `kill_criteria`
- 每个问题后面都补一句“为什么问”，让听众理解 `idea_intake` 的作用不是走表单，而是在冻结研究语义和停止条件。
- 固定主干：
  - `00 idea_intake`
  - `mandate_confirmation_pending`
  - `00 mandate`
  - `research_route`
- `mandate_confirmation_pending` 必须表现为一个显式治理停顿：
  - `idea_intake` 的 `GO_TO_MANDATE` 只表示具备进入 mandate 的资格
  - 不是立即生成 mandate artifact
  - 需要先确认四组 grouped freeze 合同：
    - `research_intent`
    - `scope_contract`
    - `data_contract`
    - `execution_contract`
- grouped freeze 不应只显示组名，还要在图上展开每组冻结的核心内容：
  - `research_intent`：研究问题、primary/counter hypothesis、route、CSF 身份
  - `scope_contract`：market、universe、target_task、excluded_scope、预算边界
  - `data_contract`：data_source、bar_size、horizons、时间语义、no-lookahead
  - `execution_contract`：time_split、参数边界、artifact contract、capacity/crowding benchmark、实现栈
- `research_intent` 还要进一步展开成一条**垂直鱼骨主干**，中间是竖向主干，左右交错挂载冻结节点。
- 这些节点优先展示“字段职责”，而不是某个具体题目的实例值：
  - `research_question`：这条研究线到底要回答什么问题
  - `primary_hypothesis / counter_hypothesis`：主机制解释与最强反方解释
  - `research_route / excluded_routes / route_rationale`：为什么走这条流程，不走另一条
  - `factor_role / factor_structure / portfolio_expression / neutralization_policy`：若走 CSF，这条线的研究身份是什么
  - `success_criteria / failure_criteria`：什么证据算成功，什么情况算失败
- mandate 后拆成两条线：
  - `time_series_signal`
  - `cross_sectional_factor`
- 时序主线固定为：
  - `01 data_ready`
  - `02 signal_ready`
  - `03 train_freeze`
  - `04 test_evidence`
  - `05 backtest_ready`
  - `06 holdout_validation`
- CSF 主线固定为：
  - `01 csf_data_ready`
  - `02 csf_signal_ready`
  - `03 csf_train_freeze`
  - `04 csf_test_evidence`
  - `05 csf_backtest_ready`
  - `06 csf_holdout_validation`
- 两条线汇合到：
  - `07 promotion_decision`
  - `08 shadow_admission`
  - `09 canary_production`
- 额外放两个治理提示节点：
  - 每阶段都要 `formal artifacts + review closure`
  - `RETRY / NO-GO / CHILD LINEAGE` 时转 `failure handling`

**Visual Conventions**

- 标题和核心节点：绿色
- 时序主线：蓝色
- CSF 主线：紫色
- 决策节点：橙色菱形
- 治理提示：浅橙色
- 注释 / 辅助说明：浅灰色

**Validation**

- 文件可通过 `xmllint --noout docs/show/qros-demo.drawio`
- 文件中存在 2 个 `<diagram>` 页面
- 页面名分别是 `Overview` 和 `Flow`
