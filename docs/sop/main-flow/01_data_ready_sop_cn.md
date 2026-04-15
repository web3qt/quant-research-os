# 01_data_ready_sop — Data Ready 阶段标准操作流程（机构级）

Doc ID: SOP-DATAREADY-v1.0
Title: `01_data_ready_sop` — Data Ready 阶段标准操作流程（机构级）
Date: 2026-03-27
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research / Quant Dev / Data Platform
Audience:
- Research
- Quant Dev
- Data Engineering
- Reviewer / Referee

Depends On:
- `research_workflow_master_spec`（`docs/sop/main-flow/research_workflow_sop.md`）
- `workflow_stage_gates.yaml`（`contracts/stages/workflow_stage_gates.yaml`）
- `00_mandate`（上游阶段冻结产物）

---

# 1. 文档目的

本 SOP 只回答一件事：

**一条 research lineage 进入 `01_data_ready` 阶段后，执行者应如何从 Mandate 冻结产物出发，完成数据抽取、对齐、清洗、审计、缓存生成和元数据归档，最终产出可共享、可审计、strategy-agnostic 的 Layer 0 数据基础层。**

它不是数据平台的开发文档，也不是某条谱系的专项操作手册。
它是 `01_data_ready` 阶段的**执行合同和交付规范**。

如果你需要了解本阶段**失败后**的处置流程，请参阅 `../failures/01_data_ready_failure_sop_cn.md`。

---

# 2. 阶段定位

## 2.1 核心问题

> 原始数据能否被转换为共享、可审计、可复用的数据基础层？

具体而言：能否在统一时间栅格、统一质量语义和可复用统计缓存三个维度上，把原始市场数据转化为下游所有阶段都可信赖的 Layer 0。

## 2.2 为什么独立

团队最常见的伪发现之一，就是把数据问题误当成 alpha。

以下问题都足以制造假信号：

- 缺失值被静默补齐（forward-fill），实际引入了前视信息；
- open_time 和 close_time 标签混用，导致收益计算偏移一根 bar；
- 去重规则不清晰，同一根 bar 出现两次导致统计量膨胀；
- 补值语义不清，下游信号无法区分"真实零值"和"缺失被填零"；
- 覆盖率审计缺失，某些标的只有半截数据却被当成完整样本。

把数据准备独立成一个正式阶段并设置 formal gate，目的就是在研究开始之前隔离这些风险。

## 2.3 上下游关系

| 方向 | 阶段 | 关系说明 |
|------|------|----------|
| 上游 | `00_mandate` | 消费 mandate frozen outputs：universe、时间边界、time_split.json |
| 下游 | `02_signal_ready` | 产出 aligned_bars/、rolling_stats/、qc_report、dataset_manifest 供下游消费 |

**冻结约束**：下游 `02_signal_ready` 不得重新估算本阶段冻结的时间边界和 universe admission rules。

---

# 3. 适用范围

本 SOP 适用于所有依赖标准化底表、对齐行情、质量标记的数据准备阶段，包括但不限于：

- 单资产时间序列研究
- pair / spread / relative value 研究
- 事件驱动研究
- 多因子 / 截面研究
- 各谱系研究（Topic A / B / C / D 等）

只要某条线在 `01_data_ready` 需要回答以下问题，本 SOP 就适用：

- 时间对齐是否正确且统一？
- 缺失、异常、停牌、退市、stale、outlier 是否按合同处理？
- 基准腿（benchmark leg）覆盖是否审计通过？
- 去重规则是否显式记录？
- 下游 `02_signal_ready` 所需字段是否已按合同产出？

---

# 4. 执行步骤

以下 12 个步骤构成本阶段的完整执行流程。每个步骤给出"输入 → 动作 → 输出 → 验证点"四元组。

## 步骤 1：确认 Mandate 冻结产物完整

| 项 | 内容 |
|----|------|
| **输入** | `00_mandate` gate decision = PASS 的产物目录 |
| **动作** | 逐项核对 mandate frozen outputs 是否存在且版本一致：research_question.md、time_split.json、universe_declaration.md、mandate_gate_decision.md、artifact_catalog.md |
| **输出** | mandate_completeness_check（记录在自审文档中） |
| **验证点** | 所有 mandate required_outputs 均存在；time_split.json 内容与 mandate_gate_decision.md 声明一致；如有缺失则不得启动后续步骤 |

## 步骤 2：数据抽取与版本锁定

| 项 | 内容 |
|----|------|
| **输入** | mandate 声明的 universe、时间边界、数据源标识 |
| **动作** | 从数据平台或上游共享源拉取原始 OHLCV / 事件数据；锁定数据版本（snapshot ID 或 hash） |
| **输出** | raw_data/（原始数据目录）、data_source_version.json（含 snapshot ID、拉取时间、源标识） |
| **验证点** | 原始数据文件数量与 universe 声明一致；时间范围覆盖 mandate 声明的 train + test + backtest + holdout 全部窗口；同一 snapshot ID 可复现同一数据 |

## 步骤 3：统一时间栅格对齐

| 项 | 内容 |
|----|------|
| **输入** | raw_data/、time_split.json（定义 bar size 和时间边界） |
| **动作** | 将所有标的对齐到统一时间栅格（如 1h bar、UTC+0）；所有 bar 统一使用 close_time 或 open_time 中的**一种**作为主键，全局一致 |
| **输出** | aligned_bars/（对齐后的底表目录） |
| **验证点** | 所有标的时间轴长度一致（dense axis）；主键列名和语义全局统一；不存在因对齐产生的重复行或间隙行（除显式标记的缺失外） |

## 步骤 4：缺失 / 脏数据语义标记

| 项 | 内容 |
|----|------|
| **输入** | aligned_bars/ |
| **动作** | 对每根 bar 标注缺失原因标签（missing、stale、delisted、halted、outlier、bad_price）；**不得**静默 forward-fill、不得静默删除、不得用 0 替代 NaN |
| **输出** | aligned_bars/ 中增加 quality flag 列（如 `bar_quality`、`missing_reason`） |
| **验证点** | NaN 行均有对应 missing_reason 标签；不存在连续 N 根以上 stale bar 而未被标记；forward-fill 仅在显式声明且记录在 data_contract.md 中时才允许 |

## 步骤 5：去重与 dedupe 规则记录

| 项 | 内容 |
|----|------|
| **输入** | aligned_bars/ |
| **动作** | 检测并处理同一主键下的重复行；记录去重规则（保留哪一条、为什么） |
| **输出** | dedupe_rule.md（去重规则文档）；aligned_bars/ 已去重 |
| **验证点** | aligned_bars/ 中不存在主键重复行；dedupe_rule.md 中写明了重复来源、处理策略和影响范围 |

## 步骤 6：基准腿覆盖审计

| 项 | 内容 |
|----|------|
| **输入** | aligned_bars/、mandate 中声明的 benchmark 资产 |
| **动作** | 审计 benchmark leg（如 BTC、ETH 或指数）的数据完整性：覆盖率、缺失率、stale 率；确认 benchmark 数据质量不低于研究对象 |
| **输出** | benchmark_audit 记录（写入 qc_report 或 validation_report.md） |
| **验证点** | benchmark 覆盖率 >= 研究窗口 95%（或按 data_contract 声明的阈值）；覆盖缺口已显式记录并解释 |

## 步骤 7：Universe admissibility 筛选与排除记录

| 项 | 内容 |
|----|------|
| **输入** | aligned_bars/、mandate universe 声明、质量标记结果 |
| **动作** | 根据质量阈值（覆盖率、stale 率、流动性）决定哪些标的进入正式 universe，哪些被排除；被排除标的**必须**记录排除原因 |
| **输出** | universe_summary.md、universe_exclusions.csv、universe_exclusions.md |
| **验证点** | universe_exclusions.csv 中每行都有 exclusion_reason 字段；排除后的正式 universe 与 universe_summary.md 中的声明一致；不存在"静默删币"（删除标的但不留排除记录） |

## 步骤 8：QC 报告生成

| 项 | 内容 |
|----|------|
| **输入** | aligned_bars/、质量标记结果、universe admissibility 结果 |
| **动作** | 汇总全局和逐标的质量指标，生成 machine-readable QC 报告 |
| **输出** | qc_report.parquet |
| **验证点** | qc_report 至少包含：symbol、total_bars、missing_bars、missing_pct、stale_bars、stale_pct、outlier_bars、bad_price_bars、coverage_start、coverage_end、admitted（是否进入正式 universe）；文件可被 pandas 正常读取且无 schema 异常 |

## 步骤 9：Rolling statistics / 缓存生成

| 项 | 内容 |
|----|------|
| **输入** | aligned_bars/ |
| **动作** | 计算并缓存下游常用的 rolling statistics（如 rolling mean、rolling std、rolling volume）；**只使用 train 窗口内数据估算**，不得用全样本 |
| **输出** | rolling_stats/（缓存目录） |
| **验证点** | rolling statistics 的计算窗口与 time_split.json 中 train 窗口一致；不存在使用 test / backtest / holdout 数据估算的情况；缓存文件有 field_dictionary 对应条目 |

## 步骤 10：数据合同、元数据与重放程序生成

| 项 | 内容 |
|----|------|
| **输入** | 以上所有步骤的产出 |
| **动作** | 撰写 data_contract.md（定义下游可消费的字段、语义、质量承诺）；生成 dataset_manifest.json（数据集元数据：版本、时间范围、行数、列数、hash）；生成 run_manifest.json（记录 runtime 版本、输入根目录、program_artifacts、replay_command）；保存 stage-local rebuild 程序（如 `rebuild_data_ready.py`） |
| **输出** | data_contract.md、dataset_manifest.json、run_manifest.json、`rebuild_data_ready.py` 或等价程序快照 |
| **验证点** | data_contract.md 中列出的字段与 aligned_bars/ 实际列名一一对应；dataset_manifest.json 中的 row_count 与实际文件行数一致；hash 可复现；run_manifest.json 可追到 runtime 版本和 replay_command；rebuild 程序可以在冻结输入上重放 |

## 步骤 11：artifact_catalog 和 field_dictionary 生成

| 项 | 内容 |
|----|------|
| **输入** | 以上所有 artifact |
| **动作** | 生成 artifact_catalog.md（列出本阶段所有产出文件、路径、用途、格式）；生成 field_dictionary.md（列出所有 machine-readable 文件中每个字段的名称、类型、语义、单位、示例值） |
| **输出** | artifact_catalog.md、field_dictionary.md |
| **验证点** | artifact_catalog 中列出的每个文件确实存在于产出目录中；field_dictionary 覆盖 qc_report.parquet、dataset_manifest.json、aligned_bars/ 和 rolling_stats/ 中的所有字段 |

## 步骤 12：自审与 gate 文档

| 项 | 内容 |
|----|------|
| **输入** | 以上所有产出 + `workflow_stage_gates.yaml` 中 data_ready 合同 |
| **动作** | 逐项核对 formal gate 的 pass_all_of 和 fail_any_of；记录 audit-only 发现；撰写 validation_report.md 和 data_ready_gate_decision.md |
| **输出** | validation_report.md、data_ready_gate_decision.md |
| **验证点** | gate decision 中明确写出 verdict（PASS / CONDITIONAL PASS / RETRY / CHILD LINEAGE 等）；所有 formal gate 条目逐条有"满足 / 不满足"的判断和证据引用；audit-only 发现与 formal gate 分开列出 |

---

# 5. 必备输出与 Artifact 规范

## 5.1 完整产出清单

| 文件 / 目录 | 类型 | 格式 | 说明 |
|-------------|------|------|------|
| `aligned_bars/` | machine | parquet / csv | 统一时间栅格对齐后的底表 |
| `rolling_stats/` | machine | parquet / csv | 可复用的 rolling statistics 缓存 |
| `qc_report.parquet` | machine | parquet | 全局和逐标的质量指标汇总 |
| `dataset_manifest.json` | machine | json | 数据集元数据（版本、范围、hash） |
| `universe_exclusions.csv` | machine | csv | 被排除标的列表及排除原因 |
| `run_manifest.json` | machine | json | 运行账本，记录 runtime 版本、输入根目录、program_artifacts、replay_command |
| `rebuild_data_ready.py` | machine | python | stage-local 重放程序；若使用别的语言，需提供等价程序快照 |
| `validation_report.md` | human | markdown | 数据质量验证报告 |
| `data_contract.md` | human | markdown | 下游字段与语义合同 |
| `dedupe_rule.md` | human | markdown | 去重规则说明 |
| `universe_summary.md` | human | markdown | 正式 universe 汇总 |
| `universe_exclusions.md` | human | markdown | 排除项的详细说明 |
| `data_ready_gate_decision.md` | human | markdown | 阶段 gate 判定文档 |
| `artifact_catalog.md` | human | markdown | 本阶段全部产出目录 |
| `field_dictionary.md` | human | markdown | 字段名、类型、语义、单位 |

## 5.2 qc_report.parquet 示例 schema

```
symbol              : string    # 标的代码
total_bars          : int64     # 总 bar 数
missing_bars        : int64     # 缺失 bar 数
missing_pct         : float64   # 缺失率
stale_bars          : int64     # stale bar 数
stale_pct           : float64   # stale 率
outlier_bars        : int64     # outlier bar 数
bad_price_bars      : int64     # 坏价 bar 数
coverage_start      : datetime  # 覆盖起始时间
coverage_end        : datetime  # 覆盖结束时间
admitted            : bool      # 是否进入正式 universe
exclusion_reason    : string    # 排除原因（admitted=True 时为空）
```

## 5.3 dataset_manifest.json 示例结构

```json
{
  "manifest_version": "1.0",
  "lineage_id": "topic_a_v3",
  "stage": "data_ready",
  "created_at": "2026-03-27T10:00:00+09:00",
  "data_source": {
    "provider": "exchange_api",
    "snapshot_id": "snap_20260327_001",
    "pull_timestamp": "2026-03-27T09:30:00+09:00"
  },
  "time_range": {
    "start": "2023-01-01T00:00:00Z",
    "end": "2026-01-01T00:00:00Z",
    "bar_size": "1h",
    "timezone": "UTC"
  },
  "universe": {
    "total_symbols": 150,
    "admitted_symbols": 132,
    "excluded_symbols": 18
  },
  "aligned_bars": {
    "row_count": 3960000,
    "column_count": 12,
    "file_hash_sha256": "a1b2c3..."
  },
  "qc_summary": {
    "global_missing_pct": 0.023,
    "global_stale_pct": 0.005,
    "benchmark_coverage_pct": 0.998
  }
}
```

---

# 6. Formal Gate 规则

## 6.1 必须全部满足（pass_all_of）

| # | Gate 条件 | 判定方法 |
|---|----------|----------|
| G1 | 基准腿覆盖审计已完成 | qc_report 中 benchmark 标的的 coverage_pct >= 阈值，且审计结论写入 validation_report.md |
| G2 | dense 时间轴已生成，正式对象时间轴长度一致 | aligned_bars/ 中所有 admitted 标的的行数相同 |
| G3 | 缺失、坏价、stale 和 outlier 语义已显式保留 | aligned_bars/ 中存在 quality flag 列；NaN 不被静默填充 |
| G4 | qc_report 与 dataset_manifest 已生成 | 文件存在且 schema 合规 |
| G5 | 排除项和准入结果已显式记录 | universe_exclusions.csv 和 universe_exclusions.md 存在且非空（如无排除则显式声明） |
| G6 | required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation | artifact_catalog.md 中列出的每个文件确实存在；field_dictionary.md 覆盖所有 machine artifact 字段 |

## 6.2 触发任一即失败（fail_any_of）

| # | 失败条件 | 说明 |
|---|---------|------|
| F1 | 没有统一时间栅格 | 不同标的使用不同 bar size 或不同对齐方式 |
| F2 | 混用 open_time 和 close_time 作为主键 | 部分文件用 open_time、部分用 close_time |
| F3 | 静默吞掉缺失或静默 forward-fill | NaN 被填充但未在 data_contract.md 中声明 |
| F4 | 基准腿覆盖或 universe 审计无法解释 | benchmark 覆盖率异常但无文档说明 |

## 6.3 Verdict 映射

| Verdict | 条件 |
|---------|------|
| **PASS** | pass_all_of 全部满足，fail_any_of 全部未触发 |
| **CONDITIONAL PASS** | pass_all_of 基本满足，存在显式 reservations（如边缘质量对象保留、个别 cache 缺口不阻断下一阶段） |
| **PASS FOR RETRY** | processing 或 validation 结果可通过当前阶段修复后重跑 |
| **RETRY** | 时间对齐、QC 或 dataset manifest 存在可修复缺陷 |
| **CHILD LINEAGE** | 正式时间窗或 universe 需要实质改写，必须回退到 mandate 开子谱系 |

---

# 7. Audit-Only 检查项

以下检查项不构成 formal gate，但应记录在 validation_report.md 中，供 reviewer 参考：

| # | 检查项 | 说明 |
|---|--------|------|
| A1 | 个别对象质量偏弱但未触发正式排除 | 例如某标的 stale 率 3%，低于排除阈值但高于平均水平 |
| A2 | rolling cache 选择是否足够经济 | rolling window 是否过大导致计算浪费；是否有冗余 cache |
| A3 | 数据抽取延迟或不稳定 | 源数据 API 响应异常，虽然最终拉到数据但存在重试 |
| A4 | 跨标的质量方差 | 部分标的质量显著好于其他标的，可能影响截面分析 |

Audit-only 发现**不得**被用作 formal gate 失败的理由，也不得被偷换成 fail_any_of 条目。

---

# 8. 常见陷阱与误区

## 8.1 明确禁止

| # | 禁止行为 | 风险 |
|---|---------|------|
| P1 | 在原始层静默 forward-fill 缺失 | 引入前视信息，下游信号看到了未来数据 |
| P2 | 混用 open_time 和 close_time 作为主键 | 收益计算偏移一根 bar，所有 alpha 结论失效 |
| P3 | 发现覆盖问题后直接静默删币不留排除报告 | 构成幸存者偏差，下游回测无法还原真实 universe |

## 8.2 常见误区

| # | 误区 | 正确做法 |
|---|------|---------|
| M1 | 用全样本统计量（mean、std）标准化 train 数据 | 只用 train 窗口内数据估算统计量；全样本 = 前视 |
| M2 | 补值时引入前视信息 | 补值只能用当前及以前时间点的数据；不得用未来 bar 插值 |
| M3 | 忽略基准腿（benchmark leg）质量 | benchmark 数据质量不低于研究对象是底线；benchmark 有洞则所有相对收益计算失效 |
| M4 | 把对齐后的数据当成"干净数据" | 对齐只解决时间栅格问题，不解决质量问题；quality flag 仍需保留 |
| M5 | 去重后不记录规则 | 后续复现时无法确认去重逻辑是否一致 |
| M6 | 把 volume = 0 当成缺失 | 零成交量可能是真实市场状态（假期、低流动性），不应默认标记为 missing |
| M7 | 只检查整体覆盖率而不检查尾部 | 头部标的可能拉高整体指标，但尾部标的严重缺失；需逐标的检查 |
| M8 | 将 data_ready 输出视为 thesis-specific | Data Ready 产出的是 strategy-agnostic 的共享基础层，不嵌入 thesis-specific 标签或特征 |

---

# 9. 失败与回退

## 9.1 回退规则

| 项 | 说明 |
|----|------|
| 默认回退阶段 | `data_ready`（在本阶段内修复） |
| 允许修改范围 | 数据抽取、时间对齐、QC 规则、admissibility 审计 |
| 必须开子谱系 | 想修改 mandate 冻结的时间边界 或 想修改 mandate 冻结的 universe 口径 |

## 9.2 失败处置流程

当本阶段 gate verdict 为 RETRY / PASS FOR RETRY / CHILD LINEAGE 时，按以下文档执行：

> **参阅**: `../failures/01_data_ready_failure_sop_cn.md`

该文档覆盖：失败冻结、问题分类、排查步骤、修改限制、回退决策和审计闭环。

## 9.3 关键约束

- 在本阶段内修复（RETRY / PASS FOR RETRY）时，**不得**修改 mandate 冻结产物；
- 如果修复涉及改时间窗或 universe 口径，必须回退到 mandate 开 CHILD LINEAGE；
- 修复后必须重新执行步骤 8-12（QC 报告、rolling stats、元数据、自审），不得只修局部不更新全局产出。

---

# 10. 阶段专属要求

## 10.1 QC 标准细节

| 指标 | 默认阈值 | 说明 |
|------|---------|------|
| 单标的缺失率 | <= 5% | 超过则标记为 audit-only 关注或触发排除 |
| 单标的 stale 率 | <= 3% | 连续 stale >= 24 bars 需显式标记 |
| benchmark 覆盖率 | >= 95% | 低于则 formal gate 失败 |
| 全局缺失率 | <= 2% | 超过需在 validation_report.md 中解释 |
| 坏价检测 | OHLC 关系违规 | H < L、C < 0、O = 0 等视为坏价 |

以上阈值为默认值。如果 mandate 或 data_contract 中声明了不同阈值，以声明值为准，但必须在 data_contract.md 中写明依据。

## 10.2 对齐方法论

1. **时间主键统一**：全局使用 close_time 或 open_time 中的**一种**，在 data_contract.md 中声明。
2. **bar 边界定义**：明确 bar 的 [start, end) 语义，避免 off-by-one。
3. **时区统一**：所有时间戳转换为 UTC（或 data_contract 中声明的统一时区）。
4. **dense axis 生成**：生成覆盖全研究窗口的完整时间轴；缺失 bar 用 NaN + quality flag 填充，不得跳过。
5. **跨标的对齐验证**：所有 admitted 标的的时间轴行数必须相同。

## 10.3 缺失语义处理规范

| 缺失类型 | 标签 | 处理方式 |
|---------|------|---------|
| 数据源未返回 | `missing` | 保留 NaN，不填充 |
| 价格未变化超过 N 根 bar | `stale` | 保留原值，标记 stale flag |
| 标的已退市 | `delisted` | 从退市时间点起标记，保留 NaN |
| 标的停牌 | `halted` | 保留 NaN，标记 halted |
| 统计异常值 | `outlier` | 保留原值，标记 outlier flag（不自动修正） |
| 价格逻辑违规 | `bad_price` | 保留原值，标记 bad_price flag |

**核心原则**：保留语义，不静默吞掉。下游阶段自行决定如何处理各类标签，Data Ready 只负责标记。

---

# 11. Checklist 速查表

执行者和 reviewer 可使用以下 checklist 快速核对：

## 11.1 执行者 Checklist

- [ ] Mandate 冻结产物完整性已确认（time_split.json、universe_declaration.md 等）
- [ ] 数据已从声明的数据源拉取并锁定版本
- [ ] 统一时间栅格已生成，主键类型（open_time / close_time）全局一致
- [ ] 缺失值已标记语义标签，未进行静默 forward-fill
- [ ] 去重已完成，dedupe_rule.md 已撰写
- [ ] 基准腿覆盖审计已通过
- [ ] Universe admissibility 筛选已完成，排除项已记录
- [ ] qc_report.parquet 已生成且 schema 合规
- [ ] rolling_stats/ 已生成，仅使用 train 窗口数据估算
- [ ] data_contract.md 和 dataset_manifest.json 已生成
- [ ] artifact_catalog.md 已生成，所有文件均存在
- [ ] field_dictionary.md 覆盖所有 machine-readable 字段
- [ ] data_ready_gate_decision.md 已撰写，verdict 明确

## 11.2 Reviewer Checklist

- [ ] formal gate pass_all_of 逐条核对（G1-G6）
- [ ] formal gate fail_any_of 逐条排除（F1-F4）
- [ ] audit-only 发现已记录且与 formal gate 分开
- [ ] verdict 与证据一致，未出现"audit-only 偷换 formal gate"
- [ ] required_outputs 13 项全部存在
- [ ] field_dictionary 覆盖 qc_report、dataset_manifest、aligned_bars、rolling_stats 全部字段
- [ ] data_contract.md 中字段与 aligned_bars/ 实际列名一致
- [ ] rolling statistics 未使用 test / backtest / holdout 数据

---

# 12. 关联文档

| 文档 | 路径 | 关系 |
|------|------|------|
| 研究 Workflow 总指南 | `docs/sop/main-flow/research_workflow_sop.md` | 上层方法论 |
| 阶段 Gate 合同 | `contracts/stages/workflow_stage_gates.yaml` | formal gate 真值 |
| Data Ready 失败处置 SOP | `docs/sop/failures/01_data_ready_failure_sop_cn.md` | 失败时的标准流程 |
| Mandate 阶段 | `00_mandate` 阶段产物 | 上游冻结产物 |
| Signal Ready SOP | `02_signal_ready`（如有） | 下游消费方 |

**文档优先级**（冲突时）：

1. `workflow_stage_gates.yaml` 是 gate contract 真值。
2. 本 SOP 是执行层和解释层。
3. 谱系自身的 gate 文档必须同时满足以上两者。

---

*End of SOP-DATAREADY-v1.0*
