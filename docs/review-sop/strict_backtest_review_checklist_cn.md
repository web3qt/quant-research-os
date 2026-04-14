# Strict Backtest Review Checklist（机构级中文版）

- doc_id: SOP-STRICT-BACKTEST-REVIEW-CHECK-v1.0
- title: Strict Backtest Review Checklist — 严格回测可信性复核清单
- date: 2026-03-24
- timezone: Asia/Shanghai
- status: Active
- owner: Strategy Research / Reviewer / Referee / Portfolio Review
- audience:
  - Research
  - Reviewer
  - Referee
  - Portfolio Review
- depends_on:
  - contracts/stages/workflow_stage_gates.yaml
  - contracts/review/review_checklist_master.yaml
  - docs/review-sop/stage_completion_standard_cn.md
  - docs/fail-sop/05_backtest_failure_sop_cn.md
  - docs/fail-sop/lineage_change_control_sop_cn.md

---

## 1. 文档目的

本清单用于回答一个更严格的问题：

**某份回测结果，到底只是“看起来不错”，还是已经达到“可信可采纳”的程度。**

它主要用于两类场景：

1. 正式 `05_backtest` 阶段的高强度复核
2. 历史遗留或非 formal lineage 回测的只读审计

这份清单不是为了重新设计策略，而是为了判断：

- 研究问题有没有被偷偷换掉
- 样本与 OOS 口径是否真实
- 执行与成本假设是否足够严肃
- 引擎与资金记账口径是否能撑得住正式结论
- 这份回测结论是否值得被下游相信

一句话：

**这不是“结果解释清单”，而是“结果可信门槛清单”。**

---

## 2. 适用范围

适用于：

- `05_backtest` formal closure review
- 从旧研究迁移到正式 stage-gated workflow 之前的回测审计
- 收益显著偏强、执行假设偏敏感、或机制演进频繁的策略

不适用于：

- 仅为快速探索写的 notebook 草稿
- 未冻结研究主问题的灵感试验
- 还没形成最小 artifact 链的临时分析

---

## 3. 必读顺序

1. `contracts/stages/workflow_stage_gates.yaml`
2. `contracts/review/review_checklist_master.yaml`
3. `docs/review-sop/stage_completion_standard_cn.md`
4. 当前 backtest 的 gate 文档、review 文档、关键脚本与关键输出
5. 若当前 backtest 已失败或存在治理问题，再读：
   - `05_backtest_failure_sop_cn.md`
   - `lineage_change_control_sop_cn.md`

---

## 4. 总体判定规则

严格复核只做三类结论：

- `RETRY`
  当前结果有研究价值，但未达到正式可信门槛，可在当前阶段受控补证据、补引擎、补执行模型后重审。
- `CHILD LINEAGE`
  当前有效结果已经不再回答原研究问题，必须新开谱系。
- `NO-GO`
  当前回测既不可信，也没有明确受控修复空间，不应继续推进。

如果 blocking checks 里任何一项不通过，就**不得**把这份回测写成可正式采信的 `PASS`。

---

## 5. Blocking Checks

以下项目全部是 blocking。

### 5.1 研究身份与谱系控制

检查：
- 当前有效策略是否仍在回答原始 mandate / thesis
- 是否发生机制切换、时间框架切换、执行语义切换、Universe 身份切换

通过标准：
- 当前回测仍然沿用原主问题与冻结边界

失败含义：
- 如果已经换题，默认结论为 `CHILD LINEAGE`

### 5.2 冻结输入与上游 handoff

检查：
- whitelist、best_h、信号字段、执行规则是否来自上游冻结产物
- 是否在 backtest 中重新选币、重估 horizon、重写阈值

通过标准：
- 仅使用上游冻结对象；没有看完结果再改输入

失败含义：
- 默认 `RETRY`
- 若实质改变 alpha 机制或上游冻结身份，升级为 `CHILD LINEAGE`

### 5.3 样本窗口与时间口径一致性

检查：
- 脚本实际使用的 IS / OOS / holdout 时间窗
- review 文档和 gate 文档写的时间窗
- 年化口径与样本长度是否一致

通过标准：
- 脚本、artifact、review、gate 文本完全一致

失败含义：
- 默认 `RETRY`
- 在修正前，不得相信年化收益、OOS 稳定性或衰减结论

### 5.4 OOS 独立性

检查：
- OOS 是否只使用 IS 冻结参数
- OOS 是否被用于回写参数、白名单、执行规则

通过标准：
- OOS 仅作为独立检验，不参与回写

失败含义：
- 默认 `RETRY`

### 5.5 双引擎完成度

检查：
- `vectorbt/`
- `backtrader/`
- `engine_compare.csv`

通过标准：
- 两套正式回测均完成

失败含义：
- 默认 `RETRY`
- 单引擎结果不得被写成 formal `Backtest Ready`

### 5.6 双引擎语义一致性

检查：
- 关键收益、回撤、交易数和资金曲线是否一致
- 是否存在 `semantic_gap`

通过标准：
- `semantic_gap = false`
- 差异有明确解释且不影响 formal verdict

失败含义：
- 默认 `RETRY`
- 若无法解释语义冲突，升级为 `NO-GO`

### 5.7 执行与成本模型严肃性

检查：
- fee、slippage、funding、maker/taker、capacity 是否明确
- maker 成交逻辑是否有严肃执行假设，而不是仅用随即抽样替代微观执行语义

通过标准：
- 成本与执行模型可解释，且与策略实现语义匹配

失败含义：
- 默认 `RETRY`
- 如果收益对单一宽松执行假设高度敏感，结果不得被正式采信

### 5.8 正式资金记账与 artifact 链

检查：
- `portfolio_summary.parquet`
- `summary.txt`
- `field_dictionary.md`
- 必要的 trade / symbol / portfolio artifact

通过标准：
- 收益、回撤、交易与费用都能被正式资金记账口径解释

失败含义：
- 默认 `RETRY`

### 5.9 异常收益 sanity review

检查：
- 当收益偏强、回撤异常小、或执行假设过理想时，是否做过 sanity review
- 是否检查时间对齐、坏 bar、成本口径、收益集中度

通过标准：
- sanity review 已完成，且无 blocking issue

失败含义：
- 默认 `RETRY`

### 5.10 搜索预算与负结果保留

检查：
- 参数搜索是否留痕
- reject ledger / failed variants / 失败原因是否保留

通过标准：
- 失败结果未被抹掉
- 选择当前组合的理由清晰

失败含义：
- 默认 `RETRY`

### 5.11 独立审查与治理闭环

检查：
- reviewer 是否独立于 builder
- gate decision 是否与 review evidence 对齐
- rollback_stage、allowed_modifications、forbidden_modifications 是否写清

通过标准：
- 独立审查成立，治理边界完整

失败含义：
- 默认 `RETRY`
- 若存在明显自我批准或角色混用，不得写成正式可信关闭

---

## 6. Reservation Checks

以下项目通常不是单独 blocking，但必须明确记录：

- 容量与冲击模型仍偏粗
- 只做了部分 stress test
- turnover / close reason 拆解仍不够细
- combo ledger 仍需补强
- OOS 衰减已经出现但尚未构成机制失效

Reservation 不能被伪装成 `PASS`，只能支持：

- `CONDITIONAL PASS`
- 或 `PASS FOR RETRY`

前提是所有 blocking checks 已通过。

---

## 7. 默认 verdict 映射

| 发现 | 默认 verdict |
|---|---|
| 当前有效结果已经换题 | `CHILD LINEAGE` |
| 样本窗口、OOS 口径或年化口径不一致 | `RETRY` |
| 只跑单引擎 | `RETRY` |
| 双引擎 semantic gap 无法解释 | `NO-GO` |
| 执行/成本模型过宽、但可受控补强 | `RETRY` |
| 自我 review / 自我批准 | `RETRY` |
| 负结果被丢弃 | `RETRY` 或 `NO-GO` |

---

## 8. 最低输出要求

做完严格复核后，至少要写清：

- `audit_target`
- `original_lineage_verdict`
- `current_backtest_trust_verdict`
- `shadow_or_promotion_readiness`
- `blocking_checks_failed`
- `reservation_checks_triggered`
- `rollback_stage`
- `allowed_modifications`
- `forbidden_modifications`
- `critical_artifacts_used`
- `decision_basis`
- `residual_risks`

---

## 9. 使用纪律

- 复核是只读的，不在审计过程中改策略。
- 不允许因为“结果看起来很好”就跳过 blocking checks。
- 不允许把 legacy 回测的 narrative 质量等同于 formal backtest quality。
- 不允许把新机制包成原机制的研究成功。
- 针对某个具体研究分支的审计记录，必须写在对应的
  `research/<family>/<lineage_or_strategy>/...` 目录下，不进入项目级
  `docs/review-sop/`。

---

## 10. 一句话标准

**只有当研究身份、样本口径、执行语义、引擎一致性、资金记账和治理闭环都经得起复核时，这份回测结果才值得被相信。**
