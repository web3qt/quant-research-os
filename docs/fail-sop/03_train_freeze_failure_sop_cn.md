# 03_train_freeze_failure_sop

Doc ID: SOP-TRAINFREEZE-FAILURE-v1.0
Title: `03_train_freeze_failure_sop` — Train Freeze 阶段失败处置标准操作流程（机构级）
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
- `02_signal_ready`
- `stage-failure-harness`

---

# 1. 文档目的

本 SOP 只回答一件事：

**当 research lineage 在 `03_train_freeze` 阶段未通过时，团队应如何冻结失败、识别 freeze 治理违规、决定回退层级、限制修改范围，并给出可审计结论。**

它不是“尽快把 freeze 做出来”的操作手册。
它是 `03_train_freeze` **失败后的标准处置合同**。

---

# 2. 适用范围

本 SOP 适用于所有在 `03_train_freeze` 需要冻结正式研究合同的谱系，包括但不限于：

- 时间切分：`train / test / holdout`
- Universe 或白名单：`selected_symbols_train`
- 阈值对象：`q20/q40/q60/q80`、`entry_z` 候选集合、质量门槛
- 参数边界：允许进入后续阶段的 param grid
- 规则合同：`entry_mode`、`signal_side`、`conditioning_mode`、`risk_role`
- 审计口径：哪些字段在线消费，哪些字段只用于离线评估

只要本阶段需要回答“后续阶段消费的到底是哪一份冻结合同”，本 SOP 就适用。

---

# 3. 阶段职责

`03_train_freeze` 的职责不是继续研究，而是：

1. 把后续 `04_test_evidence` / `05_backtest` 会消费的对象正式冻结；
2. 确保冻结对象来自允许的信息边界，而不是 test/backtest 结果；
3. 记录候选空间、搜索纪律与最终冻结版本；
4. 防止 `03` 变成隐性调参层或后验写回层。

因此，`03_train_freeze` 失败属于**治理失败**，而不是单纯的文档遗漏。
freeze 合同一旦不清楚，后续所有证据都可能被污染。

---

# 4. 失败触发条件

出现下列任一情形，即触发 `03_train_freeze_failure_sop`：

## 4.1 硬性失败（自动 FAIL）

- 冻结对象缺失、不完整或定义模糊；
- 无法根据文档与产物重建同一份 freeze 结果；
- 发现 freeze 对象依赖了 test / backtest / holdout 结果；
- 发现白名单、阈值、`best_h`、参数集合在 freeze 后被静默改写；
- 发现 train/test 边界被后验移动；
- 发现多个候选版本中只保留“最好看的一个”，却没有 trial log；
- 无法确认后续阶段消费的到底是哪一版合同。

## 4.2 软性失败（需 Referee 判断）

- 冻结对象存在，但 freeze manifest、field dictionary、trial log 不完整；
- freeze 语义基本清楚，但 artifact sidecar 未闭环；
- reviewer 认为合同大体成立，但 referee 无法确认是否仍是原题。

软性失败仍必须进入 harness，先冻结，再决定是：

- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

---

# 5. 失败分类

`03_train_freeze` 的失败必须先映射 shared harness，再落到 stage-specific failure class。

## 5.1 `FREEZE_MISSING`

Shared layer: `IMPLEMENTATION`

定义：应该冻结的对象没有被冻结，或只有口头说明没有正式产物。

典型表现：
- 没有 `time_split.json`；
- 没有 `parameter_grid.yaml`；
- 没有 `selected_symbols_train.csv`；
- 没有明确的 `freeze_manifest`。

## 5.2 `FREEZE_AMBIGUOUS`

Shared layer: `IMPLEMENTATION`

定义：冻结对象看似存在，但语义不明确，无法判断后续是否消费同一对象。

典型表现：
- “高波过滤已冻结”但未说明是 train 统计还是全样本统计；
- “白名单已冻结”但未说明路径、版本与生成时间；
- 文档声明某种 `entry_mode`，代码却仍接受其他模式。

## 5.3 `LEAKED_FREEZE_FAIL`

Shared layer: `INTEGRITY`

定义：冻结对象直接或间接使用了 test / backtest / holdout 信息。

典型表现：
- 用全样本 `ResidualZ` 估分位阈值；
- 用 test 期结果重排 `selected_symbols`；
- 用 backtest 表现选 `best_h` 再回写 `03`；
- 先看 OOS 再决定 train 门槛。

## 5.4 `MULTIPLE_TESTING_FAIL`

Shared layer: `INTEGRITY`

定义：freeze 前进行了大量搜索，但没有记录候选空间、试验次数与选择纪律。

典型表现：
- 扫了很多窗口、阈值、过滤器，只留下一个最优组合；
- 没有 trial log；
- 无法区分哪些参数是预先声明，哪些是探索后提案。

## 5.5 `POST_FREEZE_DRIFT`

Shared layer: `SCOPE`

定义：freeze 之后对冻结对象进行了静默改写，但未新开 child lineage，也未重新审批。

典型表现：
- `selected_symbols_train.csv` 被覆盖；
- `q20/q40/q60/q80` 被重算但路径不变；
- `signal_side` 从双边变单边却仍沿用原 lineage；
- `best_h` 从 `04` 回写进 `03`。

## 5.6 `REPRO_FAIL`

Shared layer: `REPRO`

定义：在相同输入、相同版本下，freeze 结果无法稳定复现。

典型表现：
- 两次运行白名单不一致；
- 参数集顺序依赖随机种子但未记录；
- 数据抽样或排序非确定性；
- train 统计量重跑后不同。

## 5.7 `SCOPE_FAIL`

Shared layer: `SCOPE`

定义：借 `03_train_freeze` 之名，实质上改变了研究问题。

典型表现：
- 原题是双边 `OB/OS`，freeze 时变成 `OB only`；
- 原题是结构审计，freeze 时变成收益最优化；
- 原题只定义 Universe，freeze 时静默增加主 gate。

---

# 6. 标准处置总原则

`03_train_freeze` 失败后，必须遵守下面六条原则：

1. **先冻结失败现场，再讨论修复方案**；
2. **先判断 freeze 是否干净，再讨论参数是否合理**；
3. **先隔离结果污染，再讨论搜索效率**；
4. **不允许用后验结果写回上游冻结对象**；
5. **修复后的 freeze 必须可复现、可比较、可审计**；
6. **任何改变研究身份的动作，都必须升级为 rollback 或 child lineage。**

---

# 7. 标准操作流程

## Step 0. 冻结失败

触发失败后，必须冻结：

- 当前 freeze 产物
- 代码版本
- 数据版本
- 时间切分
- trial log
- 参数候选空间
- 当前 reviewer / referee 意见
- 已知违规点或异常现象

至少产出：

- `failure_freeze.md`
- `freeze_manifest_snapshot.json`
- `trial_log_snapshot.csv`
- `time_split_snapshot.json`
- `repro_manifest.json`
- `review_notes.md`

## Step 1. 先做 freeze correctness triage

优先检查：

- 后续阶段消费的对象是否都已显式冻结；
- freeze 语义是否与文档一致；
- freeze 对象是否只使用 train 期可用信息；
- 候选空间与最终版本是否能追溯。

若失败：

- 对象缺失 -> `FREEZE_MISSING`
- 语义不清 -> `FREEZE_AMBIGUOUS`
- 使用未来信息 -> `LEAKED_FREEZE_FAIL`

## Step 2. 再做 search-discipline 审计

必须检查：

- 是否记录了候选参数空间；
- 是否记录了试验次数与筛选逻辑；
- 是否只保留“最好看”的冻结版本；
- 是否存在 `04/05` 结果回写 `03` 的迹象。

若失败：

- 搜索纪律失守 -> `MULTIPLE_TESTING_FAIL`
- freeze 后静默改写 -> `POST_FREEZE_DRIFT`

## Step 3. 做复现审计

必须显式检查：

- 同一版本下 freeze 结果能否重建；
- 数据版本、排序、种子是否已固定；
- manifest 能否追溯到同一份输入。

若失败：

- 归类为 `REPRO_FAIL`
- 禁止进入 `04_test_evidence`

## Step 4. 研究边界审计

检查当前 freeze 是否偷偷改题：

- 是否从结构线变成交易线；
- 是否从双边线变成单边线；
- 是否新增了未在 mandate 声明的主 gate；
- 是否改变了 Universe、frequency 或策略角色。

若发生上述行为：

- 归类为 `SCOPE_FAIL`
- 停止原线推进

## Step 5. 映射 formal decision

完成审计后，只能映射到现有 formal vocabulary：

- `PASS FOR RETRY`
  仅限 freeze 对象已经成立，但 audit sidecar 或 trial log 不完整
- `RETRY`
  适用于当前或更早阶段可受控修复的 freeze 缺口、复现问题或搜索纪律问题
- `NO-GO`
  适用于冻结合同始终无法稳定成立，或当前线已不值得继续
- `CHILD LINEAGE`
  适用于研究问题、Universe、frequency、策略身份已经实质变化

说明：

- `RESEARCH_AGAIN` 可以作为解释性 prose 出现
- 但正式输出必须翻译成 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE`

---

# 8. 回退与分流规则

## 8.1 标准回退阶段

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---:|---|
| `FREEZE_MISSING` | `03_train_freeze` | `RETRY` |
| `FREEZE_AMBIGUOUS` | `03_train_freeze` | `PASS FOR RETRY` 或 `RETRY` |
| `LEAKED_FREEZE_FAIL` | `02_signal_ready` 或更早 | `RETRY` |
| `MULTIPLE_TESTING_FAIL` | `02_signal_ready` 或 `00_mandate` | `RETRY` 或 `CHILD LINEAGE` |
| `POST_FREEZE_DRIFT` | 最近一个合法 freeze checkpoint | `RETRY` |
| `REPRO_FAIL` | `01_data_ready`、`02_signal_ready` 或 `03_train_freeze` | `RETRY` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## 8.2 何时必须升级为 child lineage

出现以下任一情况，禁止在原线静默修复：

- 从双边研究变成单边研究；
- 从结构审计变成收益最优化；
- 需要改变 Universe、frequency、signal_side 或 risk_role；
- 需要让 `03` 接管本不属于 freeze 层的研究问题。

---

# 9. 允许与禁止修改

## 9.1 允许修改

当且仅当问题属于 freeze 治理范围内时，允许修改：

- freeze manifest
- trial log 与候选空间记录
- 时间切分物化
- 白名单与阈值对象的生成实现
- reproducibility 与版本固定机制
- downstream contract 所需的审计 sidecar

## 9.2 禁止修改

在 `03_train_freeze_failure_sop` 中，默认禁止：

- 用 test / backtest 结果反向重估冻结对象；
- 覆盖原冻结文件而不留痕；
- 因结果不好而静默缩小 Universe；
- 在未走 change control 的情况下改变策略身份；
- 跳过失败冻结，直接写新版本覆盖旧版本。

---

# 10. Retry 纪律

`03_train_freeze` 的 retry 必须是 **controlled retry**。

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
failure_class: LEAKED_FREEZE_FAIL
root_cause_hypothesis: best_h 来源错误，使用了 test evidence 的结果回写 03_train_freeze
rollback_stage: 02_signal_ready
allowed_modifications:
  - regenerate_train_only_quantiles
  - rebuild_freeze_manifest
  - rerun_freeze_review
forbidden_modifications:
  - overwrite_existing_freeze_artifacts_in_place
  - use_test_results_to_select_best_h
  - change_strategy_identity
expected_improvement:
  - no downstream-derived objects appear in freeze manifest
  - whitelist and thresholds are reproducible from train-only inputs
unchanged_contracts:
  - mandate
  - universe_definition
  - signal_family
  - downstream_stage_order
```

纪律要求：

- 同一 failure class 连续 retry 不得超过 2 次；
- `03` 不得成为无限期调参层；
- 若修复动作已经改变研究身份，必须转 `CHILD LINEAGE`。

---

# 11. 标准产物

每次触发本 SOP，至少应产出以下标准件：

- `failure_freeze.md`
- `freeze_manifest_snapshot.json`
- `trial_log_snapshot.csv`
- `time_split_snapshot.json`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若决定 `PASS FOR RETRY` 或 `RETRY`）

---

# 12. Reviewer / Referee 审核点

Reviewer 至少要审：

1. 失败是否已被完整冻结？
2. 后续阶段消费的到底是哪一份 freeze 合同？
3. trial log 与候选空间是否可追溯？
4. 是否存在 `04/05` 结果回写 `03`？
5. retry 修改范围是否被严格限制？

Referee 至少要审：

1. 当前 freeze 是否仍然服务于原研究问题？
2. 是否发生 multiple testing 或 post-freeze drift？
3. 是否已经达到必须开 child lineage 的条件？
4. formal decision 是否符合治理纪律？

---

# 13. 正式决策输出格式

本 SOP 执行完后，只允许输出下面四种 formal decision，外加一个 prose-only 提示：

## 13.1 `PASS FOR RETRY`

条件：

- 冻结对象已成立；
- 仅缺 trial log、manifest 或审计 sidecar 闭环；
- 不需要改变研究身份。

## 13.2 `RETRY`

条件：

- 问题明确；
- 回退层级清晰；
- 修复不改变研究身份。

## 13.3 `NO-GO`

条件：

- 冻结合同始终无法稳定成立；
- 多轮修复后仍无法形成可审计 freeze；
- 当前线不值得继续投入。

## 13.4 `CHILD LINEAGE`

条件：

- 修复动作实质改变 Universe、frequency、signal_side、策略身份或研究主问题；
- 需要开新谱系来保持治理清洁。

## 13.5 Prose-only: “research again”

如果团队直觉上想写 “research again”，必须进一步翻译为：

- 回到当前或更早阶段重做 freeze / freeze input -> `PASS FOR RETRY` 或 `RETRY`
- 原研究线不值得继续 -> `NO-GO`
- 修复已经变成新问题 -> `CHILD LINEAGE`

---

# 14. 与 Topic A / Topic C 的落地备注

若当前研究为 Topic A / Topic C 线，`03_train_freeze` 额外必须检查：

- `selected_symbols_train` 是否仅来源于 train 期结构 / 信号证据；
- `best_h` 是否尚未在 `03` 被后验选出；
- `ResidualZ`、`OB/OS`、质量门槛的冻结对象是否只来自允许输入；
- `topicA` 结构白名单是否没有被偷偷升级成交易最优名单；
- `topicC-3A` 是否仍保持原先单边 / 双边合同，不被静默改写。

若这些未通过，不得进入 `04_test_evidence`。

---

# 15. DoD（完成定义）

本 SOP 被视为完成，至少要满足：

- 已冻结失败版本；
- 已完成 failure classification；
- 已明确 rollback stage；
- 已写明 allowed / forbidden modifications；
- 已输出 formal decision；
- 若允许 retry，已提供受控 retry 计划；
- reviewer / referee 可以依据产物复建同一份 freeze 结论。

---

# 16. 一句话总结

`03_train_freeze` 失败后的标准动作，不是“先把 freeze 文件补齐再说”，而是：

**先冻结失败，再判断它是 freeze 缺失、freeze 语义模糊、后验冻结、multiple testing、post-freeze drift、复现失败还是已经换题；随后只在合法回退边界内受控修复，任何改变研究身份的动作都必须升级为 rollback 或 child lineage。**
