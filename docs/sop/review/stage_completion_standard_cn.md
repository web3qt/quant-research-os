
# Stage Completion Standard（机构级中文版）

- doc_id: SOP-STAGE-COMPLETION-STANDARD-v1.0
- title: Stage Completion Standard — 阶段可信完成标准规范
- date: 2026-03-23
- timezone: Asia/Tokyo
- status: Active
- owner: Strategy Research / Quant Dev / Reviewer / Referee
- audience:
  - Research
  - Quant Dev
  - Reviewer
  - Referee
  - Portfolio Review
- depends_on:
  - docs/sop/main-flow/research_workflow_sop.md
  - contracts/stages/workflow_stage_gates.yaml
  - 01_data_ready_failure_sop
  - 02_signal_ready_failure_sop
  - 03_train_freeze_failure_sop
  - 04_test_evidence_failure_sop
  - 05_backtest_failure_sop
  - 06_holdout_failure_sop
  - 07_shadow_failure_sop
  - lineage_change_control_sop

---

## 1. 文档目的

本规范定义：

**在团队正式研究 workflow 中，一个阶段何时才可以被认为“已完成且可信”。**

这里的“完成”不等于：

- 程序跑完了；
- 目录里有文件了；
- 研究员觉得结果差不多；
- 文档里写了 `PASS`。

本规范要解决的是更严格的问题：

1. 这个阶段是否真的交齐了 contract 要求的内容？
2. 这个阶段的关键结果能否被重复运行与复核？
3. 阶段结论能否追溯到具体 artifact、字段与 gate rule？
4. 是否经过了有效质疑，而不是自我确认？
5. 是否排除了明显异常、口径冲突或结果失真？
6. 是否已经完成正式治理记录，可以被下游安全消费？

一句话：

**阶段完成不等于“做完”，而等于“经得起复核并允许被下游正式消费”。**

---

## 1.1 关闭工件三件套

正式 review 关闭依赖三类工件，各自职责不同，不得混用：

- `latest_review_pack.yaml`
  reviewer findings 的聚合件，记录 reviewer 看到了什么、反对了什么、还缺什么。
- `stage_gate_review.yaml`
  独立 reviewer agent review 已发生的 proof artifact。
- `stage_completion_certificate.yaml`
  machine-readable closure certificate，回答“为什么这一步已经可信关闭”。

这些 closure artifacts 的 canonical 位置是：

- `<stage>/review/closure/latest_review_pack.yaml`
- `<stage>/review/closure/stage_gate_review.yaml`
- `<stage>/review/closure/stage_completion_certificate.yaml`

其中：

- `review pack` 不是 formal gate decision
- `stage_gate_review.yaml` 不是 completion certificate
- `stage_completion_certificate.yaml` 不是替代 `gate_decision.yaml` 的第二套审批系统

---

## 2. 适用范围

本规范适用于所有正式研究阶段：

1. `Mandate`
2. `Data Ready`
3. `Signal Ready`
4. `Train Calibration`
5. `Test Evidence`
6. `Backtest Ready`
7. `Holdout Validation`
8. `Promotion Decision`
9. `Shadow Admission`
10. `Canary / Production`（研究侧能覆盖的部分）

本规范不适用于：

- 一次性 notebook 草稿
- 临时探索性分析
- 未冻结研究问题的灵感试验
- 仅供个人快速查看分布的中间脚本

---

## 3. 核心原则

### 3.1 Contract first
先检查该阶段按 contract 应交什么，再讨论结果是否好看。

### 3.2 Reproducibility before persuasion
先证明别人可以复跑，再允许研究员说服别人。

### 3.3 Traceable evidence over verbal explanation
正式结论必须依赖 artifact 与字段证据链，而不是依赖口头解释。

### 3.4 Effective challenge is mandatory
没有经过有效质疑的阶段结论，不算可信完成。

### 3.5 Sanity before promotion
结果异常地好或异常地差，都必须经过合理性检查。

### 3.6 Governance closes the stage
阶段只有在 gate verdict、回退范围、允许修改范围与下游权限都被正式记录后，才算真正关闭。

---

## 4. 阶段可信完成的六联标准

一个阶段只有在下面六项全部通过时，才可以被写成：

- `PASS`
- 或 `CONDITIONAL PASS`

六项标准分别是：

1. `Contract Pass`
2. `Reproducibility Pass`
3. `Traceability Pass`
4. `Challenge Pass`
5. `Sanity Pass`
6. `Governance Pass`

若任意一项不通过，则不得写无保留的 `PASS`。

---

## 5. 六联标准定义

## 5.1 `Contract Pass`

### 定义
该阶段在 `contracts/stages/workflow_stage_gates.yaml` 和对应 stage guide 中要求的 formal 输入、formal 输出、formal 文档、formal gate 产物均已完整交付。

### 最低检查项
- `required_inputs` 完整
- `required_outputs` 完整
- `artifact_catalog.md` 已生成
- `field_dictionary.md` 或 `*_fields.md` 已生成
- 阶段 gate 文档已生成
- 若本阶段要求冻结 handoff，则 `frozen_spec.*` 已生成

### 常见失败模式
- 只有结果表，没有字段说明
- 只有文档，没有机器可读 artifact
- 缺少 gate 文档
- 缺少 reject ledger / param ledger / selected list
- 只生成了目录，没有正式登记到 `artifact_catalog.md`

### 结论规则
- 若任一 formal output 缺失：`Contract Pass = false`
- 若仅有 audit-only 产物缺失：可记录 reservation，但不得伪装成 पूर्ण formal pass

---

## 5.2 `Reproducibility Pass`

### 定义
在冻结输入、冻结配置和冻结代码版本下，本阶段关键结果可被重复执行并得到一致结论。

### 最低检查项
- 存在 `run_manifest.json` 或等价文件
- 存在 `git_revision` / 代码版本标识
- 输入 artifact 路径可追溯
- 参数身份可追溯
- 关键执行命令或入口已记录
- stage-local rebuild 程序或等价 program snapshot 已登记到 `program_artifacts`
- 关键输出可重跑
- 重跑后关键汇总值与 gate verdict 一致

### 推荐检查方式
- 同环境重跑
- 独立环境重跑
- spot recomputation（抽 symbol、抽 param_id、抽日期）
- 双引擎/双实现对照（适用于 `Backtest`、`Shadow`）

### 常见失败模式
- 只能“作者自己跑出来”
- 代码版本不清楚
- 输入路径漂移
- 依赖临时 notebook 状态
- 重跑后结果与原结论不一致

### 结论规则
- 若关键结论无法复现：`Reproducibility Pass = false`

---

## 5.3 `Traceability Pass`

### 定义
阶段结论、gate verdict、reject/selected 结果、冻结对象和回退结论都能追溯到具体 artifact、具体字段和具体规则。

### 最低检查项
- 关键结论能指向具体 artifact
- 关键 gate verdict 能指向具体 formal gate rule
- reject / selected 有 ledger
- whitelist / thresholds / best_h / trade rules 有 frozen spec
- 文档中出现的关键字段都能在字段说明里找到
- `rollback_stage / allowed_modifications / downstream_permissions` 可追溯

### 推荐附加字段
- `decision_evidence_links`
- `critical_artifacts_used`
- `critical_fields_used`

### 常见失败模式
- 文档说“结构成立”，但找不到对应统计表
- 文档说“某币被拒绝”，但没有 reject ledger
- gate 结论和 YAML contract 对不上
- 白名单或规则来源不明
- 字段名称在 prose 中出现，但字段字典里不存在

### 结论规则
- 若关键结论无法定位到证据链：`Traceability Pass = false`

---

## 5.4 `Challenge Pass`

### 定义
本阶段结论已接受来自独立职责视角的有效质疑，并且主要质疑点已被回应或记录为 residual risks。

### 最低检查项
- `Builder` 已提交阶段产物
- `Critic / Reviewer` 已执行书面挑战
- `Auditor / Referee` 已基于 artifact 给出结论
- 主要风险与反例已被检查
- 未被解决的风险已写入 `residual_risks`

### 推荐 challenge 问题
1. 是否存在前视或时间泄漏？
2. 是否存在字段越层？
3. 是否把 audit-only 偷换成 formal gate？
4. 是否把结果异常解释成机制成立？
5. 是否发生研究主问题漂移？
6. 是否静默修改了冻结对象？
7. 是否只保留赢家，丢掉失败轨迹？

### 常见失败模式
- 只有作者本人“确认没问题”
- reviewer 只是签字，没有实质质疑
- 没有 challenge memo / self review
- 只记录支持证据，不记录反驳检查

### 结论规则
- 若没有独立挑战记录：`Challenge Pass = false`
- 单人研究时，至少需要 `self_challenge.md`，否则不得视为通过

---

## 5.5 `Sanity Pass`

### 定义
本阶段关键结果已经过合理性检查，没有存在未解释的异常好、异常差、口径冲突或分布失真。

### 最低检查项
- 关键汇总指标在常识范围内
- 没有明显未解释的异常集中度
- 没有明显未解释的单位冲突
- 没有明显未解释的样本崩塌
- 若结果异常地好，已触发异常结果复核
- 若结果异常地差，已判断是否属于数据/实现/机制问题

### 分阶段典型检查示例

#### `Mandate`
- 主问题是否过宽或自相矛盾
- 参数空间是否过大到不可审计

#### `Data Ready`
- 覆盖率是否异常
- 缺失率是否异常低到可疑
- 排除比例是否异常高

#### `Signal Ready`
- 覆盖是否接近零
- 低样本比例是否极高
- 某些参数是否几乎无有效信号

#### `Train Calibration`
- 拒绝率是否异常高
- 阈值分位是否异常不稳定
- 是否出现利用训练收益选参数的迹象

#### `Test Evidence`
- 是否只有极少数 symbol 或单一 horizon 支撑
- 是否只在单一 regime 成立
- 是否只有 audit evidence 漂亮，formal gate 很弱

#### `Backtest Ready`
- 是否异常高收益
- 收益是否过度集中
- 双引擎是否一致
- 成本口径是否合理

#### `Holdout Validation`
- 是否断崖式退化
- 是否暴露孤峰参数
- 是否疑似 selection bias

#### `Shadow Admission`
- 实际滑点是否远高于假设
- 实际成交分布是否严重偏离
- API/监控/运营异常是否改变结论

### 结论规则
- 若存在未解释的重大异常：`Sanity Pass = false`

---

## 5.6 `Governance Pass`

### 定义
本阶段正式 gate 结论、冻结范围、保留风险、回退规则、允许修改范围和下游消费权限都已被明确记录，并完成签发。

### 最低检查项
- `stage_status` 已明确
- `decision_date_utc` 已记录
- `lineage_id` 已记录
- `frozen_scope` 已记录
- `decision_basis` 已记录
- `residual_risks` 已记录
- `rollback_stage` 已记录（若适用）
- `allowed_modifications` 已记录（若适用）
- `next_stage / downstream_permissions` 已记录
- 必要签发人已完成 sign-off

### 常见失败模式
- 文档说“基本通过”，但没有正式状态词
- 有 PASS/RETRY，但没有 rollback stage
- 有 `CONDITIONAL PASS`，但 reservations 没写清
- 允许修改范围为空白
- 下游不知道自己到底能消费什么

### 结论规则
- 若 governance 信息不完整：`Governance Pass = false`

---

## 6. 阶段完成判定规则

### 6.1 `PASS`
必须同时满足：
- `Contract Pass = true`
- `Reproducibility Pass = true`
- `Traceability Pass = true`
- `Challenge Pass = true`
- `Sanity Pass = true`
- `Governance Pass = true`

且无阻断性 reservation。

### 6.2 `CONDITIONAL PASS`
必须满足：
- 六联标准中不存在阻断性失败
- 允许存在非阻断性 reservation
- reservations 已在 gate 文档中明确写出
- 下游消费权限已明确限制

### 6.3 `PASS FOR RETRY`
适用于：
- 当前阶段不能直接晋级
- 但存在明确的受控回退与 retry 方案
- `rollback_stage` 与 `allowed_modifications` 已明确
- 未完成 retry 前不得视为正式通过

### 6.4 `RETRY`
适用于：
- 六联标准中至少有一项阻断性失败
- 但失败仍属于当前谱系可修复问题
- 必须进入失败 SOP 流程

### 6.5 `NO-GO`
适用于：
- 当前阶段已足以否定继续推进的合理性
- 或失败不具备经济修复意义
- 或继续投入不符合研究治理纪律

### 6.6 `CHILD LINEAGE`
适用于：
- 当前阶段问题要修复必须改变研究主问题、冻结对象身份、交易语义或 portfolio role
- 不应继续在原线内修补

---

## 7. 阶段可信完成的推荐检查方式

## 7.1 Checklist review
逐项核对 stage contract，不依赖主观印象。

## 7.2 Spot recomputation
随机抽取 symbol / param_id / 日期，对关键字段重算。

## 7.3 Cross-engine / cross-implementation check
适用于：
- `Backtest`
- `Holdout`
- `Shadow`

至少验证：
- 核心方向一致
- 成本解释一致
- 关键 close reason 一致
- 无明显 semantic gap

## 7.4 Ledger audit
检查：
- reject ledger
- retry record
- selected ledger
- strategy combo ledger
- child lineage relation

防止：
- 只保留赢家
- 静默删除失败版本
- 下游偷偷扩参数

## 7.5 Freeze audit
检查：
- 本阶段是否消费了上游冻结对象
- 是否重估阈值
- 是否重估 whitelist
- 是否重估 best_h
- 是否有 holdout/backtest 信息反向污染

## 7.6 Effective challenge memo
要求 reviewer 或 self-review 至少回答：
- 我最怀疑哪里可能错
- 我怎么排查的
- 哪些风险仍未排除

---

## 8. 单人研究与团队研究的区别要求

## 8.1 团队研究
推荐职责分离：
- `Builder`
- `Reviewer / Critic`
- `Auditor / Referee`

正式 `PASS / CONDITIONAL PASS / GO` 尽量不由同一人单独完成。

## 8.2 单人研究
允许 self-gate，但必须显式留下：
- `self_review.md`
- `self_challenge.md`
- `stage_completion_certificate.yaml`

并在结论中明确：
- 当前结论属于“个人流程内通过”
- 尚未经过外部独立复核（若确实没有）

---

## 9. 阶段完成证书要求

每个正式阶段关闭时，建议生成统一文件：

- `stage_completion_certificate.yaml`

最低字段包括：

- `stage`
- `lineage_id`
- `run_id`
- `review_scope`
- `reviewed_by_builder`
- `reviewed_by_reviewer`
- `reviewed_by_auditor`
- `final_verdict`
- `contract_pass`
- `reproducibility_pass`
- `traceability_pass`
- `challenge_pass`
- `sanity_pass`
- `governance_pass`
- `blocking_checks_failed`
- `reservation_checks_triggered`
- `residual_risks`
- `rollback_stage`
- `allowed_modifications`
- `forbidden_modifications`
- `downstream_permissions`
- `critical_artifacts_used`
- `critical_fields_used`
- `decision_basis`

该文件的职责是：

**回答“为什么我们相信这一步真的完成了”。**

---

## 10. 与现有 workflow 的对接方式

本规范不替代：

- `contracts/stages/workflow_stage_gates.yaml`
- 各阶段 failure SOP
- `lineage_change_control_sop`

本规范的角色是：

- 为所有阶段提供统一的可信完成标准
- 为 reviewer/auditor 提供统一的完成判定框架
- 为 `PASS / CONDITIONAL PASS / RETRY / NO-GO / CHILD LINEAGE` 提供可信支撑

推荐使用顺序：

1. 先读 `contracts/stages/workflow_stage_gates.yaml`
2. 再检查阶段 artifacts 与 gate 文档
3. 再按本规范做六联检查
4. 若失败，进入对应 failure SOP
5. 若变更研究身份，进入 `lineage_change_control_sop`

---

## 11. 对 Topic A / Topic C 的落地说明

### 11.1 对 `topicA`
`topicA` 常见风险是：
- 结构证据与执行证据混淆
- 把结构白名单误当执行白名单

因此其阶段完成尤其要强调：
- `Traceability Pass`
- `Challenge Pass`
- `Governance Pass`

### 11.2 对 `topicC / topicC-3A`
`topicC` 常见风险是：
- 研究主问题与执行语义漂移
- 在 `Backtest` 结果不好后反向改写信号或上游冻结对象
- 把 `gross > 0, net < 0` 混淆成“研究不成立”

因此其阶段完成尤其要强调：
- `Sanity Pass`
- `Freeze audit`
- `lineage change control`

---

## 12. 一句话总结

**机构级 workflow 中，一个阶段只有在 contract、复现、追溯、质疑、合理性和治理六个方面都站得住，才算“可信完成”；否则最多只能算“程序跑完了”，还不能算正式通过。**
