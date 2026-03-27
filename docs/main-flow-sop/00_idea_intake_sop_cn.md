# 00_idea_intake_sop

Doc ID: SOP-IDEA-INTAKE-v1.0
Title: `00_idea_intake_sop` — Idea Intake 阶段标准操作流程（机构级）
Date: 2026-03-27
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research
Audience:

- Research
- Reviewer / Referee

Depends On:
- `research_workflow_sop`
- `docs/intake-sop/qualification_scorecard_schema.yaml`
- `docs/intake-sop/idea_gate_decision_schema.yaml`

---

# 1. 文档目的

本 SOP 只回答一件事：

**一个原始想法，是否值得正式投入研究预算，并进入 Mandate 阶段。**

它不是 Mandate 的替代品，也不是回答"能不能赚钱"。它回答的是更上游的问题：**这个想法是否达到了可以冻结研究边界的成熟度。**

与周边文档的关系：

| 文档 | 角色 | 本 SOP 如何使用 |
|------|------|-----------------|
| `research_workflow_sop.md` | 全流程解释层 | 本 SOP 是其前置阶段的执行展开 |
| `qualification_scorecard_schema.yaml` | Scorecard 字段真值 | 本 SOP 的评分维度必须与 schema 一致 |
| `idea_gate_decision_schema.yaml` | Gate decision 字段真值 | 本 SOP 的 gate 词汇必须与 schema 一致 |
| `00_mandate_sop_cn.md` | Mandate 执行合同 | Idea Intake 的下游消费者，本阶段产出是其输入 |

---

# 2. 阶段定位

## 2.1 核心问题

> **这个想法是否成熟到值得开始冻结研究边界？**

Idea Intake 不是在探索信号，也不是在看数据。它回答的是：这个想法是否有可观测的变量、合理的机制假设、足够清晰的边界，以及值得花正式研究预算的可行性。

## 2.2 为什么必须独立存在

没有正式 Idea Intake，团队面临两种困境：

- **跳过**：直接进入 Mandate，但研究问题没有经过显式资格评估，边界模糊，结果倒逼问题是常态。
- **跳进数据**：以"临时探索"为名看了分布、扫了参数，再回来"补"研究问题——但研究问题已经被结果污染。

Idea Intake 的价值是：**在看任何真实数据结果之前，给想法一个显式的资格判断。**

## 2.3 上游输入合同

Idea Intake 是研究管线的第一个阶段，没有正式前置阶段。其输入为：

- 原始想法（一句话描述、直觉、市场观察、文献参考）；
- 研究员对机制的初步猜想；
- 初步的 market / universe / data source 设想。

## 2.4 下游消费者

| 下游阶段 | 消费内容 |
|----------|----------|
| `mandate` | `qualification_scorecard.yaml`, `research_question_set.md`, `scope_canvas.yaml`, `idea_gate_decision.yaml` |

只有 verdict 为 `GO_TO_MANDATE` 的 idea，才允许进入 Mandate 阶段。

---

# 3. 适用范围

## 3.1 适用于

所有打算进入正式研究管线的想法，包括但不限于：

- 市场结构观察驱动的信号假设；
- 文献或外部研究启发的机制猜想；
- 历史异常事件引发的研究动机；
- 策略组合扩充需求驱动的研究方向；
- 任何需要决定"要不要正式研究"的阶段。

## 3.2 不适用于

- 已经进行过 Idea Intake 并通过 gate 的研究线（直接进入 Mandate）；
- Mandate 已冻结后的子谱系（子谱系有自己的 intake 或直接继承上游 mandate）；
- 纯工程类任务（数据基础设施建设、框架升级等，不需要 Intake）。

---

# 4. 执行步骤

Idea Intake 分为三个阶段：**访谈收敛 → Qualification 评分 → Gate Decision**。每一步以"输入 → 动作 → 输出 → 验证点"四要素展开。

## 步骤 1：生成 Intake 目录结构

- **输入**：确定了 lineage_id 的原始想法。
- **动作**：
  1. 确定 lineage_id（命名规则：`<研究主题>_v<版本号>`，例如 `btc_led_alt_transmission_v1`）。
  2. 运行脚手架命令，生成空白模板：
     ```bash
     python scripts/scaffold_idea_intake.py --lineage-root outputs/<lineage_id>
     ```
  3. 确认目录结构已生成：`outputs/<lineage_id>/00_idea_intake/`。
- **输出**：空白 artifact 模板集合。
- **验证点**：目录是否存在？模板文件是否齐全？

## 步骤 2：完成 Intake 访谈

- **输入**：原始想法描述。
- **动作**：
  进行 intake 访谈，至少收敛以下信息后，才允许进入正式填写：
  1. `observation`：可观测到什么现象？
  2. `primary_hypothesis`：核心机制假设是什么？
  3. `counter_hypothesis`：反驳假设是什么？（强制要求，不可留空）
  4. `market` / `universe` / `target_task`：研究对象的粗口径。
  5. `data_source` / `bar_size`：数据基础的初步判断。
  6. `kill_criteria`：什么情况下应该停止研究这个想法？（强制要求）

  **禁止**：访谈阶段不得看任何真实数据分布或回测结果。只允许基于先验知识和市场直觉进行判断。
- **输出**：`idea_brief.md`（访谈结论的人类可读记录）；`observation_hypothesis_map.md`（观察与假设的对应关系）。
- **验证点**：
  - `counter_hypothesis` 是否已写明？
  - `kill_criteria` 是否至少有一条？
  - 访谈期间是否完全没有查看真实数据结果？

## 步骤 3：定义研究问题集合

- **输入**：`idea_brief.md`。
- **动作**：
  1. 将访谈中的假设整理成结构化研究问题集合。
  2. 区分主问题（primary research question）和辅助问题（secondary questions）。
  3. 写清楚每个问题的"可证伪条件"：什么样的证据会否定这个问题？
- **输出**：`research_question_set.md`。
- **验证点**：
  - 主问题是否只有一个？
  - 每个问题是否都有可证伪条件？

## 步骤 4：填写 Scope Canvas

- **输入**：`idea_brief.md`、`research_question_set.md`。
- **动作**：
  填写 `scope_canvas.yaml`，覆盖以下字段：
  - `market`：交易场所（例如 Binance perpetual）
  - `universe`：研究对象范围（粗口径，不要求精确列表）
  - `bar_size`：基础时间粒度
  - `horizons`：研究的预测窗口列表
  - `target_task`：研究任务类型（例如 event-driven relative return study）
  - `excluded_scope`：显式排除什么（不研究什么）
  - `data_source`：数据来源判断

  **注意**：scope_canvas 只要求粗口径，不要求正式 universe 列表。精确冻结在 Mandate 阶段完成。
- **输出**：`scope_canvas.yaml`。
- **验证点**：
  - `excluded_scope` 是否有至少一条？
  - `horizons` 是否已列出？

## 步骤 5：完成 Qualification Scorecard

- **输入**：`idea_brief.md`、`research_question_set.md`、`scope_canvas.yaml`。
- **动作**：
  按 `qualification_scorecard_schema.yaml` 对 6 个维度逐一评分（1-5 分）：

  | 维度 | 核心问题 |
  |------|----------|
  | `observability` | 观测变量是否可以被稳定定义？ |
  | `mechanism_plausibility` | 机制是否 plausible，且可与其他解释区分？ |
  | `tradeability` | 在真实成本假设下是否存在可交易空间？ |
  | `data_feasibility` | 所需数据是否可得、版本稳定？ |
  | `scoping_clarity` | 研究边界是否可以收窄到可研究的程度？ |
  | `distinctiveness` | 与已有研究线是否有足够区分？ |

  每个维度必须填：`score`、`evidence`（支持的理由）、`uncertainty`（已知的不确定性）、`kill_reason`（什么情况下停止）。
- **输出**：`qualification_scorecard.yaml`（machine-readable，符合 schema）。
- **验证点**：
  - 6 个维度是否都已评分？
  - 每个维度是否都有 `kill_reason`？
  - 是否存在只有分数没有 evidence 的维度？

## 步骤 6：给出 Idea Gate Decision

- **输入**：`qualification_scorecard.yaml`。
- **动作**：
  1. 综合 6 个维度的评分，给出正式 verdict（三选一）：
     - `GO_TO_MANDATE`：想法通过 qualification，允许申请进入 Mandate。
     - `NEEDS_REFRAME`：方向可研究，但当前边界或变量定义不足，需重写后再审。
     - `DROP`：不值得投入进一步研究预算。
  2. 填写 `idea_gate_decision.yaml`，覆盖所有 required fields：`idea_id`、`verdict`、`why`、`approved_scope`、`required_reframe_actions`、`rollback_target`。
  3. `GO_TO_MANDATE` 的 `approved_scope` 必须非空（至少包含 market、universe、bar_size、horizons、target_task、excluded_scope）。
- **输出**：`idea_gate_decision.yaml`（machine-readable，符合 schema）。
- **验证点**：
  - verdict 是否是三个允许值之一？
  - `GO_TO_MANDATE` 时 `approved_scope` 是否非空？
  - `NEEDS_REFRAME` 时 `required_reframe_actions` 是否非空？

## 步骤 7：生成 artifact_catalog

- **输入**：步骤 1-6 的所有输出。
- **动作**：
  1. 汇总所有已生成的 artifact，登记到 `artifact_catalog.md`。
  2. 确认每个 machine-readable artifact（`scope_canvas.yaml`、`qualification_scorecard.yaml`、`idea_gate_decision.yaml`）都有对应的人类可读说明（`idea_brief.md`、`research_question_set.md`）。
- **输出**：`artifact_catalog.md`。
- **验证点**：
  - `artifact_catalog.md` 是否列出了所有 required_outputs？
  - machine-readable artifact 是否都有 companion 说明文档？

---

# 5. 必备输出与 Artifact 规范

## 5.1 Artifact 总览

| Artifact | 类型 | 用途 |
|----------|------|------|
| `idea_brief.md` | 人类可读 | 访谈结论、原始想法、假设陈述 |
| `observation_hypothesis_map.md` | 人类可读 | 观察与假设的对应关系 |
| `research_question_set.md` | 人类可读 | 结构化研究问题集合与可证伪条件 |
| `scope_canvas.yaml` | 机器可读 | 粗口径 scope 定义（market/universe/bar_size/horizons） |
| `qualification_scorecard.yaml` | 机器可读 | 6 维度评分结果 |
| `idea_gate_decision.yaml` | 机器可读 | 正式 gate verdict 与 approved scope |
| `artifact_catalog.md` | 人类可读 | 所有产物的登记清单 |

## 5.2 机器可读 Artifact Schema 示例

### scope_canvas.yaml

```yaml
idea_id: "btc_led_alt_transmission_v1"
market: "Binance perpetual"
universe: "top liquidity alts"
bar_size: "5m"
horizons:
  - "15m"
  - "30m"
  - "60m"
target_task: "event-driven relative return study"
excluded_scope:
  - "low liquidity meme tails"
  - "cross-exchange propagation"
data_source: "Binance REST / WebSocket"
```

### qualification_scorecard.yaml（最小示例）

```yaml
idea_id: "btc_led_alt_transmission_v1"
reviewer_identity: "researcher"
dimensions:
  observability:
    score: 4
    evidence:
      - "可定义 btc_shock_size 和 alt_future_relative_return"
    uncertainty:
      - "事件阈值仍需正式化"
    kill_reason:
      - "若观测变量无法稳定定义，则停止"
  mechanism_plausibility:
    score: 4
    evidence:
      - "BTC 价格发现主导假设"
    uncertainty:
      - "需排除共同 beta 解释"
    kill_reason:
      - "若只有同步相关无滞后机制，则停止"
  # ... 其余 4 个维度
```

### idea_gate_decision.yaml

```yaml
idea_id: "btc_led_alt_transmission_v1"
verdict: GO_TO_MANDATE
why:
  - "观察变量可定义"
  - "存在 plausible mechanism"
  - "可先做事件研究 baseline"
approved_scope:
  market: "Binance perpetual"
  universe: "top liquidity alts"
  bar_size: "5m"
  horizons: ["15m", "30m", "60m"]
  target_task: "event-driven relative return study"
  excluded_scope:
    - "low liquidity meme tails"
    - "cross-exchange propagation"
required_reframe_actions: []
rollback_target: "00_idea_intake"
```

---

# 6. Formal Gate 规则

## 6.1 通过条件（pass_all_of）

以下条件**全部满足**方可通过：

| # | 条件 | 对应步骤 |
|---|------|----------|
| 1 | `idea_brief.md` 已完成，包含 observation、primary hypothesis、counter hypothesis、kill criteria | 步骤 2 |
| 2 | `research_question_set.md` 已完成，主问题唯一，每个问题有可证伪条件 | 步骤 3 |
| 3 | `scope_canvas.yaml` 已完成，`excluded_scope` 非空 | 步骤 4 |
| 4 | `qualification_scorecard.yaml` 已完成，6 个维度全部有分，每个维度有 kill_reason | 步骤 5 |
| 5 | `idea_gate_decision.yaml` 已完成，verdict 为三个允许值之一，required fields 全部非空 | 步骤 6 |
| 6 | `artifact_catalog.md` 已完成，所有 required outputs 已登记 | 步骤 7 |

## 6.2 失败条件（fail_any_of）

以下条件**任一触发**即判失败：

| # | 条件 | 严重性 |
|---|------|--------|
| 1 | `counter_hypothesis` 未写明 | 硬性 |
| 2 | `kill_criteria` 未写明 | 硬性 |
| 3 | Qualification 期间查看了真实数据结果 | 硬性 |
| 4 | `idea_gate_decision.yaml` 的 verdict 不是允许值之一 | 硬性 |
| 5 | `GO_TO_MANDATE` 但 `approved_scope` 为空 | 硬性 |
| 6 | required outputs 缺失 | 硬性 |

## 6.3 Verdict 规则

| Verdict | 适用条件 |
|---------|----------|
| **GO_TO_MANDATE** | 通过 qualification，`approved_scope` 已写明，`counter_hypothesis` 已写明，`kill_criteria` 已写明 |
| **NEEDS_REFRAME** | 方向可研究，但当前边界或变量定义不足；`required_reframe_actions` 非空 |
| **DROP** | 不值得投入进一步研究预算；`why` 已写明 |

**GO_TO_MANDATE 不等于立即进入 Mandate。** 系统会停在 `mandate_confirmation_pending`，等待研究员显式确认四组合同（`research_intent`、`scope_contract`、`data_contract`、`execution_contract`）后，才允许生成 Mandate 产物。

---

# 7. Audit-Only 检查项

以下项目不影响 formal gate verdict，但会被记录：

- Qualification 评分的理由是否充分？
- Scope canvas 的粗口径是否合理（不要求精确，但不能过于宽泛）？
- 研究问题的写法是否便于后续阶段引用？
- `counter_hypothesis` 是否真正有挑战性，而不只是形式上存在？

Audit-only 发现**不得**被 reviewer 偷换为 formal gate 阻断条件。

---

# 8. 常见陷阱与误区

## 8.1 在访谈阶段看了数据

**表现**：以"随便扫一眼"为由，在填写 qualification_scorecard 前先看了某个参数的分布或收益序列。

**危害**：qualification 结论被数据结果倒逼，observability 和 tradeability 的分数失去先验独立性。整个 intake 流程的认识论价值消失。

**正确做法**：访谈和 qualification 必须完全在先验知识和市场直觉的基础上进行，不查看任何真实数据结果。

## 8.2 counter_hypothesis 只是 primary hypothesis 的弱化版

**表现**：`primary_hypothesis` 是"BTC 冲击传导给 ALT"，`counter_hypothesis` 是"BTC 冲击传导效果较弱"。

**危害**：没有真正的对立机制假设，无法在后续 signal_ready 和 test_evidence 阶段设计有效的对照实验。

**正确做法**：`counter_hypothesis` 必须是一个**机制层面**的对立解释，例如"这只是共同 beta 暴露，不存在可交易滞后"。

## 8.3 kill_criteria 过于宽泛

**表现**：kill_criteria 只写"如果结果不好就停止"或"如果收益为负就停止"。

**危害**：这样的 kill_criteria 不能在 intake 阶段被评估，实质上没有作用。

**正确做法**：kill_criteria 应该能在 intake 阶段（不看数据）就初步判断，例如"若观测变量无法稳定定义，则停止"或"若目标市场无法提供覆盖 horizon 的稳定报价，则停止"。

## 8.4 NEEDS_REFRAME 后直接修改后升格

**表现**：verdict 给了 `NEEDS_REFRAME`，研究员直接修改了几行描述，然后自行宣布升格到 GO_TO_MANDATE。

**危害**：NEEDS_REFRAME 是需要重新走 qualification 流程的，不是简单改文字就能升格。

**正确做法**：NEEDS_REFRAME 后，必须重新完成 `required_reframe_actions` 中的所有动作，并重新走步骤 2-6，重新给出新的 `idea_gate_decision.yaml`。

## 8.5 qualification_scorecard 只给分不写 evidence

**表现**：6 个维度都有分数，但 evidence 字段为空或只写了"尚可"。

**危害**：reviewer 无法验证评分依据，scorecard 变成了没有信息量的形式文档。

**正确做法**：每个维度的 evidence 必须至少有一条具体说明，能够支持该分数的给出。

---

# 9. 失败与回退

## 9.1 失败后的允许动作

| 情形 | 允许动作 | 需要重新走 qualification？ |
|------|----------|--------------------------|
| 文档表述不清楚 | 澄清文档表述 | 否 |
| Artifact 字段缺失 | 补全缺失字段 | 否 |
| counter_hypothesis 不够有力 | 重写 counter_hypothesis | 是（步骤 2 起） |
| kill_criteria 不具体 | 重写 kill_criteria | 是（步骤 2 起） |
| Scorecard 评分缺少 evidence | 补充 evidence | 是（步骤 5 重新填写） |
| 访谈期间查看了数据 | 必须清空所有 intake 结论，重新从步骤 2 开始 | 是（完整重走） |

## 9.2 Rollback 规则

```yaml
default_rollback_stage: "00_idea_intake"
allowed_modifications:
  - 澄清文档表述
  - 补全缺失字段
must_restart_qualification_when:
  - counter_hypothesis 被认定无效
  - kill_criteria 过于宽泛
  - 访谈期间发现看了数据
  - NEEDS_REFRAME 后进行了实质修改
```

---

# 10. 从 Idea Intake 进入 Mandate 的交接规则

## 10.1 交接触发条件

当 `idea_gate_decision.yaml.verdict == GO_TO_MANDATE` 时，不得直接调用 mandate-author。必须先通过交互式确认：

```bash
python scripts/run_research_session.py \
  --outputs-root outputs \
  --lineage-id <lineage_id> \
  --confirm-mandate
```

## 10.2 四组确认合同

系统会逐组回显 mandate freeze draft，等待显式确认：

| 确认组 | 内容 |
|--------|------|
| `research_intent` | 研究问题、假设、判断标准 |
| `scope_contract` | market、universe、target_task、预算边界 |
| `data_contract` | 数据源、bar_size、horizons、时间语义 |
| `execution_contract` | time_split、参数边界、artifact contract |

四组全部确认后，才允许生成 Mandate 产物：

```bash
python scripts/build_mandate_from_intake.py --lineage-root outputs/<lineage_id>
```

## 10.3 Mandate 的输入消费清单

Mandate 阶段只消费以下 Intake 输出：

| Intake Artifact | Mandate 使用方式 |
|-----------------|-----------------|
| `qualification_scorecard.yaml` | 提取 approved dimensions 作为研究问题边界参考 |
| `research_question_set.md` | 作为 `mandate.md` 研究主问题的起草基础 |
| `scope_canvas.yaml` | 作为 `mandate.md` universe 与时间窗提案的初始输入 |
| `idea_gate_decision.yaml` | 提取 `approved_scope` 作为 Mandate 边界约束 |

---

# 11. Checklist 速查表

提交 gate review 前，逐项勾选：

- [ ] `idea_brief.md` 已完成
- [ ] `observation` 已写明
- [ ] `primary_hypothesis` 已写明
- [ ] `counter_hypothesis` 已写明（非弱化版，是机制层对立假设）
- [ ] `kill_criteria` 已写明（至少一条可在 intake 阶段评估的条件）
- [ ] `observation_hypothesis_map.md` 已完成
- [ ] `research_question_set.md` 已完成，主问题唯一，每个问题有可证伪条件
- [ ] `scope_canvas.yaml` 已完成，`excluded_scope` 非空
- [ ] `qualification_scorecard.yaml` 已完成
- [ ] 6 个维度全部已评分
- [ ] 每个维度有 `evidence`（至少一条具体说明）
- [ ] 每个维度有 `kill_reason`
- [ ] `idea_gate_decision.yaml` 已完成
- [ ] `verdict` 为允许值之一
- [ ] `GO_TO_MANDATE` 时 `approved_scope` 非空
- [ ] `NEEDS_REFRAME` 时 `required_reframe_actions` 非空
- [ ] `artifact_catalog.md` 已完成，所有 required outputs 已登记
- [ ] 访谈期间没有查看任何真实数据结果（自审）
- [ ] 自审已通过 formal gate 规则（§6.1 全满足、§6.2 全不触发）

---

# 12. 关联文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 主流程 SOP | `docs/main-flow-sop/research_workflow_sop.md` | 全流程解释层，Idea Intake 的上下文 |
| Qualification Scorecard Schema | `docs/intake-sop/qualification_scorecard_schema.yaml` | Scorecard 字段真值 |
| Idea Gate Decision Schema | `docs/intake-sop/idea_gate_decision_schema.yaml` | Gate decision 字段真值 |
| Schema 示例 | `docs/intake-sop/examples/` | 填写示例参考 |
| Intake 流程指南 | `docs/experience/idea-intake-to-mandate-flow.md` | 用户视角的操作指南 |
| Mandate SOP | `docs/main-flow-sop/00_mandate_sop_cn.md` | 下游阶段执行合同 |
| Mandate 失败 SOP | `docs/all-sops/第二层-阶段失败 sop/00_mandate_failure_sop_cn.md` | 尚未建立 |
