# QROS Review 约束地图

## 目的

这篇文档只回答三个问题：

- review agent 有没有固定 skill
- 每个阶段“必须检查什么”写在哪里
- 这些检查里，哪些已经是 runtime 强约束，哪些还主要靠 reviewer skill 执行

这不是 review 操作手册。  
如果你要看 reviewer / launcher / raw findings / closure 的执行协议，优先看：

- [QROS 共享 Review 协议](qros-review-shared-protocol.md)

如果你要看 review skill 的调用方式，再看：

- [Codex 阶段 Review Skill 使用说明](codex-stage-review-skill-usage.md)

## 一句话结论

QROS 当前的 review 不是“reviewer 自由发挥”。

固定约束来自 4 层：

1. 共享 review 协议
2. stage gate 真值合同
3. stage review checklist 真值
4. stage-specific review skill

其中：

- `qros-session` 决定当前阶段绑定哪个固定 review skill
- `workflow_stage_gates.yaml` 决定 formal gate / required outputs / rollback / downstream permissions
- `review_checklist_master.yaml` 决定 reviewer 需要检查的 blocking / reservation / audit-only 项
- `SKILL.md` 只是把这些真值渲染成 reviewer 可执行文本，不应发明第二套规则

## 约束来源

### 1. 共享协议

共享协议文件：

- [docs/guides/qros-review-shared-protocol.md](/Users/mac08/workspace/web3qt/quant-research-os/docs/guides/qros-review-shared-protocol.md:1)

它统一规定：

- reviewer 子代理与 launcher 主线程的职责边界
- `adversarial_review_request.yaml` / `spawned_reviewer_receipt.yaml` / `reviewer_findings.raw.yaml` / closure artifacts 的协议
- `FIX_REQUIRED` 与 closure-ready outcome 的语义
- `qros-review` 作为 deterministic closer 的行为

### 2. Stage Gate 真值

stage gate 真值文件：

- [contracts/stages/workflow_stage_gates.yaml](/Users/mac08/workspace/web3qt/quant-research-os/contracts/stages/workflow_stage_gates.yaml:1)

它定义每个 stage 的：

- `required_inputs`
- `required_outputs`
- `formal_gate`
- `verdict_rules`
- `rollback_rules`
- `downstream_permissions`
- 部分 `structural_gate_checks`
- 部分 `metric_gate_checks`

### 3. Review Checklist 真值

review checklist 真值文件：

- [contracts/review/review_checklist_master.yaml](/Users/mac08/workspace/web3qt/quant-research-os/contracts/review/review_checklist_master.yaml:1)

它定义每个 stage 的 reviewer 检查项：

- `blocking`
- `reservation`
- `audit-only`

### 4. Stage-Specific Review Skill

review skill source bundle 在 repo 内：

- `skills/<stage>/qros-*-review/SKILL.md`

Codex 安装副本在本机：

- `~/.codex/skills/qros-*-review/`

这些 skill 由生成器维护：

- [runtime/scripts/gen_codex_stage_review_skills.py](/Users/mac08/workspace/web3qt/quant-research-os/runtime/scripts/gen_codex_stage_review_skills.py:1)

## 固定 Skill 映射

`qros-session` 对 review stage 的 skill 映射由 runtime 的 research session 模块维护，并由测试锁定。

当前第一波固定映射如下：

| Session Stage | 固定 Review Skill | Source Bundle |
| --- | --- | --- |
| `mandate_review_confirmation_pending` / `mandate_review` | `qros-mandate-review` | `skills/mandate/qros-mandate-review/` |
| `data_ready_review_confirmation_pending` / `data_ready_review` | `qros-data-ready-review` | `skills/data_ready/qros-data-ready-review/` |
| `signal_ready_review_confirmation_pending` / `signal_ready_review` | `qros-signal-ready-review` | `skills/signal_ready/qros-signal-ready-review/` |
| `train_freeze_review_confirmation_pending` / `train_freeze_review` | `qros-train-freeze-review` | `skills/train_freeze/qros-train-freeze-review/` |
| `test_evidence_review_confirmation_pending` / `test_evidence_review` | `qros-test-evidence-review` | `skills/test_evidence/qros-test-evidence-review/` |
| `backtest_ready_review_confirmation_pending` / `backtest_ready_review` | `qros-backtest-ready-review` | `skills/backtest_ready/qros-backtest-ready-review/` |
| `holdout_validation_review_confirmation_pending` / `holdout_validation_review` | `qros-holdout-validation-review` | `skills/holdout_validation/qros-holdout-validation-review/` |
| `csf_data_ready_review_confirmation_pending` / `csf_data_ready_review` | `qros-csf-data-ready-review` | `skills/csf_data_ready/qros-csf-data-ready-review/` |
| `csf_signal_ready_review_confirmation_pending` / `csf_signal_ready_review` | `qros-csf-signal-ready-review` | `skills/csf_signal_ready/qros-csf-signal-ready-review/` |
| `csf_train_freeze_review_confirmation_pending` / `csf_train_freeze_review` | `qros-csf-train-freeze-review` | `skills/csf_train_freeze/qros-csf-train-freeze-review/` |
| `csf_test_evidence_review_confirmation_pending` / `csf_test_evidence_review` | `qros-csf-test-evidence-review` | `skills/csf_test_evidence/qros-csf-test-evidence-review/` |
| `csf_backtest_ready_review_confirmation_pending` / `csf_backtest_ready_review` | `qros-csf-backtest-ready-review` | `skills/csf_backtest_ready/qros-csf-backtest-ready-review/` |
| `csf_holdout_validation_review_confirmation_pending` / `csf_holdout_validation_review` | `qros-csf-holdout-validation-review` | `skills/csf_holdout_validation/qros-csf-holdout-validation-review/` |

结论很简单：

- review agent 有固定 skill
- 不同阶段不能混用 review skill
- reviewer 不应该自己发明“我这轮想怎么审”

## 目标治理方向：Review 由人显式发起

这一节描述的是**目标约束方向**，不是说当前 runtime 已经全部实现。

目标是把 review 的职责边界收得更硬：

- `author` 会话只负责 freeze / build / author 修复
- `review` lane 由人显式进入对应 `qros-*-review` skill 发起
- `author` resume 也由人显式发起
- runtime 不再替主 author 会话偷偷编排 reviewer，而是只负责强记录当前 review state

### 为什么这样设计

这样做有 4 个直接好处：

- lane 更清楚：author 与 review 不再混在一个线程里来回切换
- 独立性更自然：review 不再依赖“主线程内部再 spawn 一个 reviewer”来模拟独立审查
- 人的控制感更强：是否发起 review、是否回 author lane，都是显式治理动作
- 调试更简单：review 出问题时，看 spawned reviewer cycle 即可，不必在 author 主线程里扒开混合日志

### 不是“runtime 只记录当前阶段”

如果 review 改成人主动单独发起，runtime 也不能只记录“当前 stage 名”。

至少还必须强记录：

- 当前 stage 是否 `author_ready`
- 是否已 `review_requested`
- 当前 active `review_cycle_id`
- 当前 request 绑定的 author outputs digest
- 当前 review 是否 `in_progress`
- 当前 review verdict
- closure 是否已经写盘
- author outputs 是否在 request 之后变化，从而使当前 cycle stale

也就是说，目标形态是：

- `stage` 仍存在
- 但还必须有明确的 `review_state`

### Author / Review / Resume 的责任边界

建议的责任边界如下：

| 动作 | 谁显式发起 | runtime 负责什么 | 不允许什么 |
| --- | --- | --- | --- |
| 进入 review | 人显式进入对应 `qros-*-review` | 生成 request、绑定 active cycle、拒绝并发 review | author 线程静默自己切进 review |
| reviewer 执行审查 | spawned reviewer 子代理 | 校验 request / receipt / result / audit / closure 协议 | reviewer 自己改 author outputs |
| review 结束后回 author lane | 人显式恢复 author session | 给出 `awaiting_author_fix`、`resume_hint`、stale 判定 | runtime 自动无声切回 author |
| review 通过后进入下游 | 人显式确认 next-stage handoff | closure 判真、推进 stage state | 旧 review result 在 author outputs 更新后继续被视为有效 |

### 建议的最小模型

如果按这个方向收口，一个最小且强约束的模型应该是：

1. `qros-session` 只推进到 `*_review_confirmation_pending`
2. 人在当前会话中显式启动 `qros-*-review`
3. 该 review skill 用 `spawn_agent` 拉起 reviewer 子代理，并向 runtime 注册 active review cycle
4. reviewer 子代理完成 raw findings，随后当前会话完成 deterministic closure
5. author 会话只重新读取 runtime 状态，不负责 reviewer 编排

### 这里的关键原则

关键点不是“以后 review 完全人工化”，而是：

- **人决定 lane 切换**
- **runtime 强约束 lane 状态**
- **AI 只按当前 lane 和 runtime contract 执行**

这和本文其它约束是一致的：

- 合理约束必须做成强约束
- 不依赖 AI 自我发挥来保持 author / review 边界

## 每个阶段必须检查什么

下面这张表不是完整 checklist，而是“每个阶段最核心的 must-check 面”。

| Stage | Formal Gate 主面 | Checklist 主面 |
| --- | --- | --- |
| `mandate` | 研究问题、time split、universe、参数边界、执行栈、CSF route identity 冻结 | 文档解释是否闭合、关键字段和参数是否只是列名未解释 |
| `data_ready` | 数据完整性、QC 语义、dedupe、缺失 / stale / bad price 处理、可复现性 | QC 报告、aligned bars、benchmark leg、上游 mandate 对齐 |
| `signal_ready` | 信号表达、参数身份、时间语义、字段合同、交付合同 | 参数表、timeseries、signal fields 合同、人类可读说明 |
| `train_freeze` | 训练窗、阈值、过滤规则、候选淘汰账本、冻结后不可重调 | reject ledger、threshold contract、参数与 train window 一致性 |
| `test_evidence` | 独立测试窗统计、admissibility、audit trail、best-h / whitelist | rank IC / monotonicity / breadth / robustness / crowding 解释 |
| `backtest_ready` | 双引擎回放、after-cost 组合结果、容量与参与率、风险覆盖 | engine compare、一致性、name-level concentration、组合合同 |
| `holdout_validation` | holdout 不翻向、drift audit、reuse contract、failure governance | out-of-sample 稳定性、窗口比较、regime drift 说明 |
| `csf_data_ready` | `date x asset` 面板合同、membership、eligibility、coverage、shared feature base | 面板主键、taxonomy、shared feature 语义、replay command |
| `csf_signal_ready` | 因子面板合同、因子身份、方向、neutralization、route inheritance | `factor_panel.parquet`、`factor_manifest.yaml`、contract 一致性 |
| `csf_train_freeze` | bucket / neutralization / rebalance / search governance 冻结 | variant ledger、rejects、bucket diagnostics、neutralization diagnostics |
| `csf_test_evidence` | rank IC、bucket spread、breadth、stability、admissibility | summary / timeseries / monotonicity / gated vs ungated 解释 |
| `csf_backtest_ready` | portfolio expression、after-cost、capacity、execution/risk overlay | portfolio summary、name-level spread、turnover / participation / engine consistency |
| `csf_holdout_validation` | direction match、holdout return、reuse contract、drift audit | holdout compare、rolling stability、regime shift audit |

如果你想看某个 stage 的完整必检项，优先看：

1. `workflow_stage_gates.yaml` 中该 stage 的 `formal_gate`
2. `review_checklist_master.yaml` 中该 stage 的 `checks`
3. 对应 `skills/<stage>/qros-*-review/SKILL.md`

## 已经是强约束的，和还没完全前移的

当前 review 相关约束可以粗分成两类。

### 已经是 runtime 强约束

这些项已经能被 deterministic 判定，不依赖 reviewer 自由发挥：

- review stage 到 fixed skill 的映射
- request / receipt / result / audit / closure 的协议字段
- self-review / reviewer binding mismatch
- required outputs 是否存在
- 部分 structural gates
- 部分 metric gates
- stale review cycle 判定
- reviewer write scope audit

### 仍主要靠 reviewer skill 执行

这些项往往已经写在 checklist / skill 里，但还没全部 machine-enforced：

- formal package 跨文件口径一致性
- 某些 package-level semantic drift
- 某些说明是否足够闭合
- 某些“字段存在了，但解释仍然不可信”的问题

当前方向不是再给 reviewer 更多自由度，而是把这些已经写明的合理约束继续前移成 deterministic checker。

## 判断一个约束应不应该做强

如果某条规则满足下面 3 个条件，就应该优先前移成强约束：

- 机器可读：能落到 YAML / JSON / TOML / parquet schema 或 deterministic checker
- 本地可判定：只看当前 stage formal package、request/receipt/result、provenance 就能判断
- 失败可行动：一旦失败，系统能明确把 agent 打回 author lane，并指出修什么

不满足这 3 条的，才暂时留在 reviewer judgement。

## 维护规则

如果你修改 review 约束，优先按这个顺序改：

1. 先改 `contracts/stages/workflow_stage_gates.yaml`
2. 再改 `contracts/review/review_checklist_master.yaml`
3. 再重新生成 `skills/*/qros-*-review/SKILL.md`
4. 最后更新解释层文档

不要只改 `SKILL.md` 而不改真值层。

## 相关文档

- [QROS 共享 Review 协议](qros-review-shared-protocol.md)
- [Codex 阶段 Review Skill 使用说明](codex-stage-review-skill-usage.md)
- [QROS 统一研究会话使用说明](qros-research-session-usage.md)
