# 01_data_ready_failure_sop

Doc ID: SOP-DATAREADY-FAILURE-v1.0  
Title: `01_data_ready_failure_sop` — Data Ready 阶段失败处置标准操作流程（机构级）  
Date: 2026-03-23  
Timezone: Asia/Tokyo  
Status: Active  
Owner: Strategy Research / Quant Dev / Data Platform  
Audience:

- Research
- Quant Dev
- Data Engineering
- Reviewer / Referee
Depends On:
- `research_workflow_master_spec`
- `00_mandate`
- `FS-LAYER0-DATA-BASE-v1.0`

---

# 1. 文档目的

本 SOP 只回答一件事：

**当一个 research lineage 在 `01_data_ready` 阶段未通过时，机构应如何冻结失败、分类问题、执行排查、决定回退、限制修改范围，并给出可审计结论。**

它不是 `01_data_ready` 的实现说明书，也不是数据平台开发文档。  
它是 `01_data_ready` **失败后的标准处置合同**。

---

# 2. 适用范围

本 SOP 适用于所有依赖标准化底表、对齐行情、标签、质量标记、pair 数据、特征母表的数据准备阶段，包括但不限于：

- 单资产时间序列研究
- pair / spread / relative value 研究
- 事件研究
- 多因子 / 截面研究
- Topic A / B / C / D 等谱系研究

只要某条线在 `01_data_ready` 需要回答下面这些问题，本 SOP 就适用：

- 数据是否完整、可追溯、可复现？
- 时间对齐是否正确？
- 缺失、异常、停牌、退市、stale、outlier 是否按合同处理？
- 是否存在未来函数、样本泄漏、幸存者偏差、单位错配？
- 下游 `02_signal_ready` 所需字段是否已按合同产出？

---

# 3. 阶段职责

`01_data_ready` 的职责不是“尽可能多准备数据”，而是：

1. 把 `00_mandate` 里声明的数据需求物化成**可复验输入**；
2. 确保下游 `02_signal_ready` 使用的数据满足**时间、单位、质量、覆盖率、可追溯性**合同；
3. 发现并隔离那些会污染研究结论的数据问题；
4. 给出 **PASS / FAIL / PASS_WITH_RESTRICTIONS** 的正式数据就绪结论。

因此，`01_data_ready` 失败时，不能把它当成一个普通工程 bug；  
它是**研究治理失败**的一部分，因为错误数据会直接污染后续统计证据与回测结论。

---

# 4. 失败触发条件

出现下列任一情形，即触发 `01_data_ready_failure_sop`：

## 4.1 硬性失败（自动 FAIL）

- 关键输入源缺失，无法完成最小研究样本；
- 时间戳错位，且影响主标签、收益、pair 对齐；
- 发现未来函数或未来信息泄漏；
- 数据单位不一致，且会改变研究结论；
- 退市、停牌、缺失、stale 处理不符合上游合同；
- 关键字段未产出，导致 `02_signal_ready` 无法消费；
- 无法复现同一底表版本；
- 数据质量问题已知会显著污染 test / backtest，但未能被 flag 隔离。

## 4.2 软性失败（需 Referee 判断）

- 覆盖率低于门槛，但尚可缩小 Universe 使用；
- 缺失率偏高，但主要集中于少数 symbol；
- 某些字段可回退默认值，但默认值可能引入偏差；
- 个别时间段质量差，但不确定是否足以影响全样本；
- 产物完整，但元数据、schema、version manifest 不完整；
- 研究方与数据方对字段定义理解不一致。

---

# 5. 失败分类

`01_data_ready` 的失败必须先分类，再处理。默认分类如下：

## 5.1 `DATA_MISSING`

定义：数据源或字段缺失，导致无法满足最小研究合同。

典型表现：

- 某些 symbol 无历史文件；
- `pair_stats` 缺失；
- 标签表不存在；
- 关键质量标记未生成。

## 5.2 `DATA_MISALIGNMENT`

定义：时间对齐、采样频率、session 边界、收益归属窗口不正确。

典型表现：

- `r_t` 实际对应 `t+1`；
- ALT 与 BTC 使用不同 bar close 定义；
- 事件标签与未来收益窗口重叠错位；
- train/test 时间边界穿越错误。

## 5.3 `LEAKAGE_FAIL`

定义：未来函数、标签泄漏、样本外信息混入研究窗口。

典型表现：

- 使用未来价格补缺；
- 用全样本统计量做 train 阶段标准化；
- 用 test 期信息定义 whitelist 或参数；
- 使用未来退市信息过滤样本。

## 5.4 `QUALITY_FAIL`

定义：缺失、stale、outlier、停牌、异常成交等质量问题超出门槛。

典型表现：

- 窗口有效样本严重不足；
- 极值未被标记或未被隔离；
- stale bar 连续出现但未处理；
- 低流动性时段污染收益与波动估计。

## 5.5 `SCHEMA_FAIL`

定义：字段名、类型、单位、语义不符合合同。

典型表现：

- `return` 与 `log_return` 混用；
- 百分比与小数混用；
- 布尔值、时间戳、float 类型不稳定；
- 文档写的是 `kappa`，实际产物是 `beta`。

## 5.6 `REPRO_FAIL`

定义：同一版本配置下无法稳定复现同一底表或统计摘要。

典型表现：

- 重跑文件 hash 变化；
- 随机处理未固化 seed；
- 输入源版本漂移；
- Manifest 不完整导致不可追踪。

## 5.7 `SCOPE_FAIL`

定义：数据准备已经偏离 `00_mandate` 声明的研究范围。

典型表现：

- Mandate 只允许 1m，Data Ready 却偷偷混入 5m；
- Universe 被临时扩池或缩池；
- 为了修复缺失，临时更换主腿或换指标口径；
- Data Ready 阶段擅自决定下游过滤规则。

---

# 6. 标准处置总原则

`01_data_ready` 失败后，必须遵守下面六条原则：

1. **先冻结失败，再解释原因**；
2. **先判断是否影响研究有效性，再讨论工程便利性**；
3. **先修时间与泄漏问题，再修覆盖率与质量问题**；
4. **不允许用临时补丁悄悄改研究定义**；
5. **修复后的数据必须可复现、可比较、可审计**；
6. **任何超出 `00_mandate` 的改动，必须升级为 change control 或 child lineage。**

---

# 7. 标准操作流程

## Step 0. 冻结失败

触发失败后，第一动作不是改代码，而是产出 failure freeze package。

必须产出：

- `failure_freeze.md`
- `data_ready_manifest.json`
- `schema_snapshot.json`
- `coverage_report.parquet`
- `quality_report.parquet`
- `lineage_input_inventory.csv`
- `review_notes.md`

`failure_freeze.md` 至少记录：

- lineage id
- run id
- stage = `01_data_ready`
- mandate version
- input source versions
- universe
- frequency
- time range
- failed checks
- suspected failure class
- reviewer
- timestamp

目的：**防止后面把不同数据版本混成一次失败讨论。**

---

## Step 1. 先做 correctness triage

### 1.1 时间与标签检查

检查：

- bar close 对齐是否一致；
- 收益 `r_t` 的归属窗口是否符合合同；
- 标签窗口是否严格位于特征之后；
- train / test / holdout 切分是否无穿越。

若失败：优先分类为 `DATA_MISALIGNMENT` 或 `LEAKAGE_FAIL`。

### 1.2 单位与 schema 检查

检查：

- 收益是简单收益还是对数收益；
- 价格是否为复权价 / 原始价；
- 百分比与小数是否统一；
- schema 与字段字典是否一致。

若失败：分类为 `SCHEMA_FAIL`。

### 1.3 输入可追溯检查

检查：

- 输入文件是否有 version / hash / source path；
- 重跑是否生成一致结果；
- 随机性是否已固定。

若失败：分类为 `REPRO_FAIL`。

---

## Step 2. 质量与覆盖率审计

### 2.1 Coverage 审计

必须按 symbol、按时间、按窗口统计：

- 总覆盖率
- 有效 bar 占比
- 缺失连续段长度
- 首尾截断情况
- 各 symbol 可用起止时间

### 2.2 Quality 审计

必须统计：

- `missing_rate`
- `stale_rate`
- `outlier_rate`
- `zero_return_rate`
- `valid_count_window`
- 低流动性时段占比

### 2.3 Pair / Relative Value 审计

若研究依赖 pair：

- ALT 与 BTC 时间戳是否严格对齐；
- pair missing 是否集中发生在某些时段；
- beta / kappa 来源是否一致；
- 主腿与副腿是否使用同一 bar 规则。

若失败：分类多为 `QUALITY_FAIL` 或 `DATA_MISALIGNMENT`。

---

## Step 3. 泄漏与样本偏差审计

必须显式检查：

- 是否使用全样本统计量做局部标准化；
- 是否使用未来已知信息过滤样本；
- 是否使用未来事件结果定义当前可交易 Universe；
- 是否存在幸存者偏差；
- 是否把 test / holdout 期信息提前用于 Data Ready。

一旦确认泄漏：

- 直接 `FAIL`
- 失败分类固定为 `LEAKAGE_FAIL`
- 禁止进入 `02_signal_ready`

---

## Step 4. 研究边界审计

检查 Data Ready 是否偷偷改题：

- 是否改变了 Universe；
- 是否改变了主腿 / 副腿角色；
- 是否改变了时间频率；
- 是否更换了研究字段定义；
- 是否在本阶段引入了下游 gate。

若发生上述行为，分类为 `SCOPE_FAIL`。

处理原则：

- 若只是实现失误，可回退修复；
- 若研究问题实质变化，必须走 change control；
- 若问题已经改变谱系身份，必须开 `child lineage`。

---

## Step 5. 判定失败等级

完成审计后，给出三档结论：

### 5.1 `FAIL-HARD`

条件：

- 存在时间错位；
- 存在未来函数；
- 关键字段缺失；
- schema/unit 错到足以改变结论；
- 数据无法复现。

动作：

- 当前 stage 终止；
- 不得进入 `02_signal_ready`；
- 必须修复并重跑完整 `01_data_ready`。

### 5.2 `FAIL-SOFT`

条件：

- 问题集中于部分 symbol 或部分时间段；
- 可通过收缩 Universe 或限制时间范围处理；
- 不影响主研究问题的可定义性，但影响覆盖率。

动作：

- 由 Referee 判定是否允许 `PASS_WITH_RESTRICTIONS`；
- 必须显式记录 restrictions；
- restrictions 不得由研究员口头继承，必须写入 contract。

### 5.3 `PASS_WITH_RESTRICTIONS`

仅当以下条件同时满足才允许：

- 无泄漏、无时间错位、无关键 schema 错误；
- 问题被清晰 flag 并可隔离；
- 缩小后的 Universe / 时间范围仍符合 `00_mandate` 主问题；
- Reviewer 接受限制条件。

典型限制：

- 只保留覆盖率达标的 symbol；
- 去除特定脏时段；
- 强制使用质量门槛字段进入下游。

---

# 8. 回退与分流规则

## 8.1 标准回退阶段

| failure_class | 默认回退阶段 | 说明 |
|---|---:|---|
| `DATA_MISSING` | `01_data_ready` | 补齐输入后重跑 |
| `DATA_MISALIGNMENT` | `01_data_ready` | 修对齐逻辑后重跑 |
| `LEAKAGE_FAIL` | `00_mandate` 或 `01_data_ready` | 先确认问题是否源于研究定义，再重做 |
| `QUALITY_FAIL` | `01_data_ready` | 修质量过滤、flag、覆盖范围 |
| `SCHEMA_FAIL` | `01_data_ready` | 修字段合同 |
| `REPRO_FAIL` | `01_data_ready` | 固化 manifest / seed / source version |
| `SCOPE_FAIL` | `00_mandate` 或 `change_control` | 视是否改题而定 |

## 8.2 何时必须升级为 child lineage

出现以下任一情况，禁止在原线静默修复：

- Universe 发生实质变化；
- 研究频率从 1m 改成 5m / 15m；
- 主腿从 BTC 改成 ETH；
- 研究问题从“全币池”改成“只做白名单”；
- 数据口径变化会改变后续信号定义。

此时必须：

- 冻结原线失败；
- 写明原线为何不再继续；
- 开 `child lineage` 重新提交 `00_mandate`。

---

# 9. 允许与禁止修改

## 9.1 允许修改

当且仅当问题被分类为 `01_data_ready` 范围内的数据准备问题时，允许修改：

- 数据抓取与清洗逻辑；
- 对齐逻辑；
- 缺失、stale、outlier 标记生成逻辑；
- schema 与字段字典；
- manifest / version / reproducibility 机制；
- 覆盖率过滤规则（前提是不改变 `00_mandate` 主问题）；
- 数据质量报告产物。

## 9.2 禁止修改

在 `01_data_ready_failure_sop` 中，默认禁止：

- 直接改信号公式来掩盖数据问题；
- 直接改 `03_train_freeze` 阈值来适配脏数据；
- 直接改 whitelist 结果来掩盖 coverage 问题；
- 用后验 test / backtest 结果反向决定 Data Ready 过滤；
- 临时缩短时间区间，只保留“好看”的年份；
- 在未走 change control 的情况下更换主研究对象；
- 口头声明“问题不大，先往下跑再说”。

---

# 10. Retry 纪律

`01_data_ready` 的 retry 必须是 **controlled retry**，而不是无限修补。

每次 retry 必须写明：

1. `failure_class`
2. `root_cause_hypothesis`
3. `rollback_stage`
4. `allowed_modifications`
5. `expected_improvement`
6. `unchanged_contracts`

示例：

```yaml
failure_class: DATA_MISALIGNMENT
root_cause_hypothesis: ALT bars 使用 exchange close，而 BTC bars 使用 local resample close，导致 pair returns 错位 1 bar
rollback_stage: 01_data_ready
allowed_modifications:
  - unify_bar_close_rule
  - regenerate_aligned_returns
  - refresh_pair_quality_flags
expected_improvement:
  - pair timestamp exact match rate > 99.9%
  - no lookahead in rfuture label windows
unchanged_contracts:
  - universe
  - frequency=1m
  - time_split
  - main_leg=BTCUSDT
```

纪律要求：

- 同一 failure class 连续 retry 不得超过 2 次；
- 超过 2 次仍未收敛，必须升级到 Reviewer / Referee；
- 若修复动作已经改变研究身份，则必须转 `child lineage`。

---

# 11. 标准产物

每次触发本 SOP，至少应产出以下标准件：

## 11.1 必产文件

- `failure_freeze.md`
- `data_ready_manifest.json`
- `coverage_report.parquet`
- `quality_report.parquet`
- `schema_snapshot.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若决定 retry）

## 11.2 建议附加文件

- `sample_row_checks.csv`
- `timestamp_alignment_audit.parquet`
- `label_leakage_audit.md`
- `input_hash_inventory.csv`
- `symbol_restriction_list.csv`

---

# 12. Reviewer / Referee 审核点

Reviewer 在 `01_data_ready` 失败时，至少要审下面这些问题：

1. 失败是否已被完整冻结？
2. 问题分类是否准确？
3. 是否存在未来函数或样本泄漏？
4. 是否有任何动作越权改变了 `00_mandate`？
5. retry 修改范围是否被严格限制？
6. 是否应当改为 `PASS_WITH_RESTRICTIONS`？
7. 是否已经达到必须开 `child lineage` 的条件？

Referee 的职责不是帮研究员想 patch，  
而是判断：**当前问题属于数据修复、研究回退，还是谱系变更。**

---

# 13. 决策输出格式

本 SOP 执行完后，只允许输出下面四种正式结论之一：

## 13.1 `RETRY`

条件：

- 问题明确；
- 修复边界清晰；
- 不改变研究身份。

## 13.2 `RESEARCH_AGAIN`

条件：

- 问题实际源于 `00_mandate` 或研究定义；
- Data Ready 阶段无法单独解决。

## 13.3 `NO_GO`

条件：

- 关键数据长期不可得；
- 研究所需最小样本不成立；
- 现有数据无法支撑主问题。

## 13.4 `CHILD_LINEAGE`

条件：

- 修复动作实质改变 Universe / frequency / main leg / field contract；
- 需要开新谱系来保持研究治理清洁。

---

# 14. 与后续阶段的边界

本 SOP 只处理 `01_data_ready` 失败。它明确不负责：

- `02_signal_ready` 的信号表达式正确性；
- `03_train_freeze` 的阈值冻结；
- `04_test_evidence` 的统计显著性；
- `05_backtest` 的交易经济性。

但它必须保证：

- 进入下游的数据不会因已知错误污染结论；
- 所有限制条件已明确写入 contract；
- 下游使用的数据边界清晰、稳定、可追溯。

---

# 15. 针对 Topic A / Topic C 的落地备注

若当前研究为 `BTC ↔ ALT` 的 Topic A / Topic C 线，`01_data_ready` 额外必须检查：

- `ALT` 与 `BTC` 是否严格同 ts 对齐；
- `pair_missing` 是否已标准化物化；
- `r_BTC`、`r_ALT` 的 0 收益处理是否符合 Topic A 合同；
- `pair_stats.beta_{N_reg}` 是否与信号窗口一致；
- `kappa` 回退为 `1.0` 的条件是否已显式记录；
- `low_sample` 与 `missing_rate_window` 是否足以支持后续 `ResidualZ` 标准化；
- 对于 `1m` 频率，stale / low-liquidity 时段是否会虚假放大 `ResidualZ`、`OB`、`OS`。

若这些未通过，不得进入 Topic C 的 `02_signal_ready`。

---

# 16. DoD（完成定义）

本 SOP 被视为完成，至少要满足：

- 已冻结失败版本；
- 已完成 failure classification；
- 已明确 rollback stage；
- 已写明 allowed / forbidden modifications；
- 已输出正式决策（`RETRY / RESEARCH_AGAIN / NO_GO / CHILD_LINEAGE`）；
- 若允许 retry，已提供受控 retry 计划；
- 若允许 pass with restrictions，已将 restrictions 写入正式 contract。

---

# 17. 一句话总结

`01_data_ready` 失败后的标准动作，不是“先修到能跑再说”，而是：

**先冻结失败，再判断它是缺失、错位、泄漏、质量、schema、复现还是越界问题；然后只在 Data Ready 层受控修复，任何改变研究身份的动作都必须升级为 change control 或 child lineage。**
