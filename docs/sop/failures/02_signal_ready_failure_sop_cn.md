# 02_signal_ready_failure_sop

Doc ID: SOP-SIGNALREADY-FAILURE-v1.0
Title: `02_signal_ready_failure_sop` — Signal Ready 阶段失败处置标准操作流程（机构级）
Date: 2026-03-23
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research / Quant Dev / Reviewer / Referee
Audience:
- Research
- Quant Dev
- Reviewer / Referee
Depends On:
- `research_workflow_master_spec`
- `00_mandate`
- `01_data_ready`
- `stage-failure-harness`

---

# 1. 文档目的

本 SOP 只回答一件事：

**当 research lineage 在 `02_signal_ready` 阶段未通过时，团队应如何冻结失败、分类问题、限定修改范围、决定回退层级，并输出可审计结论。**

它不是“把信号尽快跑出来”的实现手册，也不是策略表现说明书。
它是 `02_signal_ready` **失败后的标准处置合同**。

---

# 2. 适用范围

本 SOP 适用于所有需要在 `02_signal_ready` 阶段正式物化字段的研究线，包括但不限于：

- 方向 / 结构类字段，如 `DC_up`、`DC_down`、`DownLinkGap`
- 截面 / 排名 / 状态类字段
- `ResidualZ`、`OB/OS`、`OBRate/OSRate`、`kappa`
- 质量门禁字段，如 `low_sample`、`missing_rate_window`、`pair_missing`
- 任何下游 `03_train_freeze` 会正式消费的信号字段、状态字段、质量字段、审计字段

只要本阶段需要回答以下问题，本 SOP 就适用：

- 信号表达式是否严格符合 `00_mandate` 与字段合同？
- 字段名与字段语义是否一致？
- 是否存在前视、未来函数、未来冻结对象提前消费？
- 质量门禁是否足以保护下游 train / test / backtest？
- 当前产物是否可复现、可解释、可审计？

---

# 3. 阶段职责

`02_signal_ready` 的职责不是证明策略有效，而是：

1. 把 `00_mandate` 声明的研究对象物化成**可复验字段**；
2. 保证字段表达式、窗口、滞后、样本门槛、质量字段满足合同；
3. 隔离所有会污染后续统计证据与交易审计的时间因果错误；
4. 产出可被 `03_train_freeze` 安全消费的信号产物与字段字典。

因此，`02_signal_ready` 失败不能被当成普通编码 bug。
它属于**研究对象物化失败**，因为错误字段会直接污染后续冻结、证据与回测。

---

# 4. 失败触发条件

出现下列任一情形，即触发 `02_signal_ready_failure_sop`：

## 4.1 硬性失败（自动 FAIL）

- 信号字段无法按合同成功物化；
- 发现表达式、窗口、滞后、分母或样本门槛实现与合同不符；
- 发现前视、未来函数、标签泄漏或未来冻结对象提前消费；
- 字段名未变，但语义已经偏离原研究问题；
- 关键质量字段缺失，导致下游无法安全拒绝劣质样本；
- schema / 类型 / 路径不满足下游消费合同；
- 同一配置重复运行结果不一致；
- 当前信号层已经引入新的研究问题，超出 `00_mandate` 边界。

## 4.2 软性失败（需 Referee 判断）

- 表达式大体正确，但少量边界条件、命名或审计字段不完整；
- 质量门禁缺口存在，但尚未确认是否改变主研究问题；
- artifact catalog、field dictionary、review sidecar 不完整；
- Reviewer 无法根据当前产物确认“这还是不是原题”。

软性失败仍必须进入 failure harness，先冻结、再分类、再决定是：

- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

---

# 5. 失败分类

`02_signal_ready` 的失败必须先映射 shared harness，再落到 stage-specific failure class。

## 5.1 `FORMULA_FAIL`

Shared layer: `IMPLEMENTATION`

定义：信号表达式、窗口边界、分母、门槛或样本条件实现错误。

典型表现：
- `DC_up` / `DC_down` 分母错；
- `ResidualZ` 标准化窗口不对；
- `OB/OS` 阈值实现与合同不符；
- `kappa` 读取错误或回退逻辑错误；
- `DownLinkGap` 方向写反。

## 5.2 `TEMPORAL_LEAK_FAIL`

Shared layer: `INTEGRITY`

定义：信号使用了 `t` 时点不可见信息，或提前消费未来冻结对象。

典型表现：
- 使用未来 bar 计算当前信号；
- 在 `02` 层使用 `best_h`、test quantile、正式白名单；
- 使用未来窗口均值 / 标准差；
- 直接或间接消费 `04_test_evidence` 结果。

## 5.3 `SEMANTIC_DRIFT_FAIL`

Shared layer: `SCOPE`

定义：字段名看似不变，但字段语义已不再回答原研究问题。

典型表现：
- 名叫 `ResidualZ`，实际加入未声明过滤；
- 名叫 `topicC-3A`，却把 `OS` 一侧纳入正式决策；
- `topicA` 本应只做结构诊断，却在信号层偷偷加入交易触发；
- 用多层 if-rule 把字段变成后验收益优化器。

## 5.4 `QUALITY_GATE_FAIL`

Shared layer: `IMPLEMENTATION`

定义：信号物化成功，但质量门禁不足，无法安全支持下游消费。

典型表现：
- 缺少 `low_sample`；
- 缺少 `missing_rate_window`；
- `pair_missing` 未正确传播；
- 没有窗口有效覆盖率；
- 下游无法判断某条记录是否应被拒绝。

## 5.5 `SCHEMA_FAIL`

Shared layer: `IMPLEMENTATION`

定义：字段命名、类型、序列化、分区规则或 artifact catalog 不满足合同。

典型表现：
- 字段缺失或拼写不一致；
- 同名字段类型不一致；
- parquet 分区不一致；
- artifact 路径与 contract 不一致。

## 5.6 `REPRO_FAIL`

Shared layer: `REPRO`

定义：同一输入、同一代码、同一配置下，信号输出不一致或无法稳定复算。

典型表现：
- 多次运行结果不同；
- 并发 / 排序导致非确定性；
- 浮点聚合不稳定影响字段；
- 读写过程中记录丢失。

## 5.7 `SCOPE_FAIL`

Shared layer: `SCOPE`

定义：当前信号层已经引入新的研究问题，超出原谱系边界。

典型表现：
- 在 `02` 层加入新的 regime gate 并改变研究对象；
- 把结构诊断字段升格为交易主信号；
- 从双边线静默改成单边线；
- 在无新 mandate 的情况下增加新的 side contract。

---

# 6. 标准处置总原则

`02_signal_ready` 失败后，必须遵守下面六条原则：

1. **先冻结失败，再解释原因**；
2. **先修时间因果与语义正确性，再谈字段优雅度**；
3. **不允许用更复杂的字段掩盖实现不正确**；
4. **不允许因为 test / backtest 表现差而反向定义信号**；
5. **修复后必须保持字段可复现、可解释、可审计**；
6. **任何改变研究问题或策略身份的动作，都必须升级为 rollback 或 child lineage。**

---

# 7. 标准操作流程

## Step 0. 冻结失败

触发失败后，第一动作不是改代码，而是产出 failure freeze package。

必须产出：

- `failure_freeze.md`
- `signal_manifest.json`
- `field_snapshot.parquet`
- `field_dictionary.md`
- `artifact_catalog.md`
- `repro_manifest.json`
- `review_notes.md`

`failure_freeze.md` 至少记录：

- lineage id
- run id
- stage = `02_signal_ready`
- mandate version
- input artifact versions
- output field set
- failed checks
- suspected failure class
- reviewer
- timestamp

## Step 1. 先做 correctness triage

优先检查：

- lag / shift / rolling 的时间因果是否正确；
- 当前字段是否只使用 `t` 时点可见信息；
- 表达式、分母、窗口边界是否符合合同；
- 字段名、字段语义、field dictionary 是否一致。

若失败：

- 时间因果错误优先归类为 `TEMPORAL_LEAK_FAIL`
- 表达式实现错误优先归类为 `FORMULA_FAIL`
- 语义漂移优先归类为 `SEMANTIC_DRIFT_FAIL` 或 `SCOPE_FAIL`

## Step 2. 再做质量与 schema 审计

必须检查：

- `low_sample`
- `missing_rate_window`
- `pair_missing`
- 有效窗口计数
- field dictionary 完整性
- artifact catalog 与路径一致性

若失败：

- 质量门禁不足 -> `QUALITY_GATE_FAIL`
- schema / 路径 / 类型错误 -> `SCHEMA_FAIL`

## Step 3. 做复现审计

必须显式检查：

- 同配置重跑结果是否一致；
- 执行环境、排序规则、并发路径是否稳定；
- artifact 是否能从 manifest 追溯。

若失败：

- 归类为 `REPRO_FAIL`
- 禁止继续进入 `03_train_freeze`

## Step 4. 研究边界审计

检查当前物化是否偷偷改题：

- 是否把诊断字段升格为交易主信号；
- 是否引入新过滤器并改变主问题；
- 是否改变 side contract；
- 是否让字段名称继续承载新语义。

若发生上述行为：

- 归类为 `SCOPE_FAIL` 或 `SEMANTIC_DRIFT_FAIL`
- 停止原线推进

## Step 5. 映射 formal decision

完成审计后，只能映射到现有 formal vocabulary：

- `PASS FOR RETRY`
  仅限审计 sidecar 或字段字典不完整，但核心字段语义与时间因果已经正确
- `RETRY`
  适用于可在当前 stage 受控修复的实现、质量、schema、复现问题
- `NO-GO`
  适用于字段语义无法稳定定义，或所有实现都依赖泄漏 / 后验拼装
- `CHILD LINEAGE`
  适用于研究问题、策略身份、Universe、side contract 已实质变化

说明：

- `RESEARCH_AGAIN` 可以作为解释性 prose 出现
- 但正式输出必须翻译成 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE`

---

# 8. 回退与分流规则

## 8.1 标准回退阶段

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---:|---|
| `FORMULA_FAIL` | `02_signal_ready` | `RETRY` |
| `TEMPORAL_LEAK_FAIL` | 泄漏产生的最早阶段，通常 `01/02/03` | `RETRY` |
| `SEMANTIC_DRIFT_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |
| `QUALITY_GATE_FAIL` | `02_signal_ready` | `RETRY` |
| `SCHEMA_FAIL` | `02_signal_ready` | `RETRY` |
| `REPRO_FAIL` | `02_signal_ready` | `RETRY` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## 8.2 何时必须升级为 child lineage

出现以下任一情况，禁止在原线静默修复：

- 把结构证据字段改成交易主信号；
- 从双边线改成单边线；
- 新增未在 `00_mandate` 声明的策略侧 contract；
- 需要改变 Universe、时间频率、主机制定义。

---

# 9. 允许与禁止修改

## 9.1 允许修改

当且仅当问题属于 `02_signal_ready` 范围内的信号物化问题时，允许修改：

- 表达式实现
- lag / rolling / denominator / threshold 的边界实现
- 质量字段与状态字段
- schema、field dictionary、artifact catalog
- 排序、并发、数值稳定性与 reproducibility 机制
- 将已漂移字段拆分为主字段与审计字段

## 9.2 禁止修改

在 `02_signal_ready_failure_sop` 中，默认禁止：

- 因为回测或 test 不好看而反向修改信号定义；
- 在 `02` 层使用 `03/04/05` 才能出现的冻结对象；
- 通过增加例外规则让字段“看起来更合理”；
- 在原线静默改变研究问题；
- 一边说修 schema，一边重写策略语义；
- 跳过失败冻结，直接覆盖旧结果。

---

# 10. Retry 纪律

`02_signal_ready` 的 retry 必须是 **controlled retry**。

每次 retry 必须写明：

1. `failure_class`
2. `root_cause_hypothesis`
3. `rollback_stage`
4. `allowed_modifications`
5. `forbidden_modifications`
6. `expected_improvement`
7. `unchanged_contracts`

示例：

```yaml
failure_class: FORMULA_FAIL
root_cause_hypothesis: ResidualZ rolling std 的 closed boundary 写错，导致标准化失真
rollback_stage: 02_signal_ready
allowed_modifications:
  - fix_rolling_boundary
  - regenerate_signal_fields
  - rerun_field_spot_checks
forbidden_modifications:
  - change_mandate
  - change_universe
  - consume_test_evidence_objects
expected_improvement:
  - field-level unit checks pass
  - spot-check rows match manual calculation
  - no temporal leak flags
unchanged_contracts:
  - mandate
  - universe
  - time_split
  - downstream_freeze_inputs
```

纪律要求：

- 同一 failure class 连续 retry 不得超过 2 次；
- 超过 2 次仍未收敛，必须升级为 `NO-GO` 或 `CHILD LINEAGE`；
- 不允许长期停留在 `02` 通过不断小修隐性换题。

---

# 11. 标准产物

每次触发本 SOP，至少应产出以下标准件：

- `failure_freeze.md`
- `signal_manifest.json`
- `field_snapshot.parquet`
- `field_dictionary.md`
- `artifact_catalog.md`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若决定 `PASS FOR RETRY` 或 `RETRY`）

---

# 12. Reviewer / Referee 审核点

Reviewer 至少要审：

1. 失败是否已被完整冻结？
2. 公式、窗口、滞后是否能手工解释？
3. 是否存在未来函数或未来冻结对象提前消费？
4. 质量字段是否足以保护下游？
5. schema、field dictionary、artifact catalog 是否一致？
6. retry 修改范围是否被严格限制？

Referee 至少要审：

1. 当前物化的到底是不是原研究问题？
2. 是否已发生研究语义漂移？
3. 是否把过滤器、状态层、审计字段偷偷升格为主信号？
4. 是否已经达到必须开 child lineage 的条件？

---

# 13. 正式决策输出格式

本 SOP 执行完后，只允许输出下面四种 formal decision，外加一个 prose-only 提示：

## 13.1 `PASS FOR RETRY`

条件：

- 核心字段语义与时间因果正确；
- 仅缺 review sidecar、field dictionary 或 artifact catalog 闭环；
- 不需要改变研究身份。

## 13.2 `RETRY`

条件：

- 问题明确；
- 修复边界清晰；
- 不改变研究身份。

## 13.3 `NO-GO`

条件：

- 字段语义始终无法稳定定义；
- 所有物化版本都严重依赖泄漏或后验拼装；
- 当前线在 `02` 已暴露严重不可修复问题。

## 13.4 `CHILD LINEAGE`

条件：

- 修复动作实质改变主机制、Universe、frequency、side contract 或策略身份；
- 需要开新谱系来保持治理清洁。

## 13.5 Prose-only: “research again”

如果团队直觉上想写 “research again”，必须进一步翻译为：

- 回到当前或更早阶段做受控修复 -> `PASS FOR RETRY` 或 `RETRY`
- 原研究线不值得继续 -> `NO-GO`
- 修复已经变成新问题 -> `CHILD LINEAGE`

---

# 14. 与 Topic A / Topic C 的落地备注

若当前研究为 `BTC ↔ ALT` 的 Topic A / Topic C 线，`02_signal_ready` 额外必须检查：

- `DC_up` / `DC_down` 分母条件是否严格符合合同；
- `OC_*` 字段是否按四象限完整定义；
- `ResidualZ` 是否使用严格过去信息标准化；
- `OB/OS`、`OBRate/OSRate` 的窗口与质量门槛是否一致；
- `kappa` 的来源与回退条件是否已显式记录；
- `low_sample`、`missing_rate_window`、`pair_missing` 是否足以支撑下游消费；
- `topicA` 字段是否仍是结构证据，而不是被偷偷改造成在线交易 alpha。

若这些未通过，不得进入 `03_train_freeze`。

---

# 15. DoD（完成定义）

本 SOP 被视为完成，至少要满足：

- 已冻结失败版本；
- 已完成 failure classification；
- 已明确 rollback stage；
- 已写明 allowed / forbidden modifications；
- 已输出 formal decision；
- 若允许 retry，已提供受控 retry 计划；
- 所有审计 sidecar 已可以支撑 Reviewer / Referee 复核。

---

# 16. 一句话总结

`02_signal_ready` 失败后的标准动作，不是“继续把信号修复杂”，而是：

**先冻结失败，再判断它是公式错、时间泄漏、语义漂移、质量门禁不足、schema / 复现问题，还是已经换题；随后只在信号物化层受控修复，任何改变研究身份的动作都必须升级为 rollback 或 child lineage。**
