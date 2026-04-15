# QROS Stage Freeze Group Field Guide

## Purpose

这份文档按“字段一一对应”解释 QROS 主流程里的 freeze draft。

每个字段都回答 4 件事：

- 这个字段是什么意思
- 为什么这个字段必须在当前阶段出现
- 下游会怎么消费它
- 不该怎么填

这不是 schema 真值。schema 真值仍然以 stage SOP、skill 和 gate YAML 为准。

## How To Use

看到一份 freeze draft 时，按下面顺序读：

1. 找到当前 group
2. 用表格逐字段对照
3. 如果字段缺失，先判断是“补说明”还是“合同没冻结”
4. 如果字段内容变化，先判断是不是已经改变了研究合同

## Mandate

### `research_intent`

这组冻结“我们到底在研究什么”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `research_question` | 当前 research lineage 的唯一主问题 | 后面所有证据都要回答同一个问题；没有它就会变成每个阶段都在研究不同东西 | 写成宽泛主题，如“研究 BTC 和 ALT 关系” |
| `primary_hypothesis` | 你主张 edge 存在的主要机制解释 | 没有机制解释，后面很容易变成只追结果 | 写成“我感觉会涨/会跌” |
| `counter_hypothesis` | 能生成同样现象的最强对立解释 | 防止结果导向叙事，强迫研究员承认普通解释也可能成立 | 写成弱化版主假设，或空泛反对句 |
| `research_route` | 后续采用哪套证据体系推进，如 `time_series_signal` 或 `cross_sectional_factor` | 它决定后续 stage contract 和 review 逻辑 | 把它当流程标签随便改 |
| `factor_role` | 在 CSF 路线里，该因子在组合中的角色 | 后面组合表达必须和这里一致 | 没走 CSF 还硬填，或角色含糊不清 |
| `factor_structure` | 因子的结构身份，如单因子还是组合因子 | 后面 train/test/backtest 要知道研究对象是一个因子还是一个结构 | 用口语化描述代替结构定义 |
| `portfolio_expression` | 因子最终如何表达成组合或如何服务目标策略，如 `long_short_market_neutral`、`group_relative_long_short`、`target_strategy_filter` | 防止后面把同一因子换成不同组合表达或偷偷改成策略过滤器 | 不写表达方式，只说“后面再看” |
| `neutralization_policy` | 因子或组合用什么口径中性化 | 后面收益解释和风险暴露解释都依赖它 | 混合多个中性化口径 |
| `target_strategy_reference` | 如果研究是为某条目标策略服务，这里记录目标引用 | 防止后面把 exploratory 研究伪装成某策略验证 | 明明是 standalone idea 还硬挂策略名 |
| `group_taxonomy_reference` | 行业/分组/桶的正式分类引用 | 后续中性化、分组收益和 bucket 解释都要复用同一 taxonomy | 只写“按行业分组”而不给正式引用 |
| `excluded_routes` | 明确不允许走的研究路线 | 防止研究失败后静默切换路线继续讲故事 | 留空，或把当前 route 也排进去 |
| `route_rationale` | 为什么选当前路线、不选其他路线 | review 需要判断 route 选择是否有机制依据 | 写成“团队更熟悉”这种非研究理由 |
| `success_criteria` | 什么结果算支持 thesis | 没有它，后面通过标准会被事后改写 | 写成模糊表述，如“结果不错” |
| `failure_criteria` | 什么结果算 thesis 被破坏 | 明确失败边界，避免失败后继续硬讲 | 不写失败条件，只写成功条件 |
| `excluded_topics` | 当前研究线明确不研究的内容 | 防止 scope creep | 用“暂无”搪塞，实际啥都能往里塞 |

### `scope_contract`

这组冻结“研究边界在哪”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `market` | 研究发生在哪个市场制度里 | 不同市场的流动性、费用、撮合和风险都不同 | 写成泛泛的“crypto” |
| `universe` | 哪些对象有资格进入正式样本 | 没有正式 universe，后面很容易按结果增删样本 | 写成“流动性好的币”这类不可执行描述 |
| `target_task` | 本线研究的任务定义 | 决定后面 evidence 是方向预测、相对收益还是别的任务 | 把 thesis、任务和交易动作混写 |
| `excluded_scope` | 明确不研究的边界 | 防止看到机会就顺手扩大题目 | 留空或写“无” |
| `budget_days` | 允许消耗的研究时间预算 | 限制研究扩张 | 事后根据复杂度再补 |
| `max_iterations` | 在本线内允许试错的轮数 | 超过这个边界通常就该开 child lineage | 写成极大值，使它失去约束力 |

### `data_contract`

这组冻结“全链路使用什么数据语义”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `data_source` | 正式数据来源 | 防止不同供应商或不同抽数版本造成结果漂移 | 写成“交易所数据”这种不具体来源 |
| `bar_size` | 全链路基础 bar 粒度 | 后续所有时间对齐、标签和 horizon 都依赖它 | 把它当小参数后面随便改 |
| `holding_horizons` | 正式允许评估的 forward horizon 集合 | 防止后面无限扩 horizon 试结果 | 只写“多个 horizon” |
| `timestamp_semantics` | 一根 bar 何时算已知、收益从何时开始算 | 它是防未来函数的核心字段之一 | 只写“按 close 算”但不讲收益归属 |
| `no_lookahead_guardrail` | 明确禁止使用未来信息的边界 | 防止 signal、label 和事件检测偷看未来 | 写成口号，不说明边界 |

### `execution_contract`

这组冻结“后面允许动哪些自由度”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `time_split_note` | train/test/backtest/holdout 的正式切分原则 | 没有时间切分边界，后面所有结果都可能有污染 | 写成“后面再切” |
| `parameter_boundary_note` | 哪些参数允许调，范围到哪里 | 防止下游无限试参数 | 只写“可以优化参数” |
| `artifact_contract_note` | 每阶段必须交什么正式产物 | 没有这个，阶段完成会变成主观判断 | 只写“需要报告” |
| `crowding_capacity_note` | 后续容量和拥挤审计的基准说明 | backtest 阶段必须沿用同一基准 | 等到 backtest 才临时补 |

## Data Ready

### `extraction_contract`

这组冻结“抽数口径”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `data_source` | 当前 data_ready 实际抽取的数据源 | 与 mandate 的 data_source 对齐，防止实现换源 | 和 mandate 填得不一样却不解释 |
| `time_boundary` | 本次正式数据集覆盖的时间边界 | 后续 QC、coverage 和回放都依赖它 | 只写年份，不写完整边界 |
| `primary_time_key` | 这套数据的唯一主时间键，如 `close_time` | 防止 open/close 混用 | 两种时间键都想保留为主键 |
| `bar_size` | 实际抽取出来的基础粒度 | 需要与 mandate 对齐，否则整条线时间语义变了 | data_ready 里悄悄改粒度 |

### `quality_semantics`

这组冻结“坏数据怎么处理”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `missing_policy` | 遇到缺失值时是保留、标记还是删除 | 防止静默填补把坏样本洗掉 | 写成“按需要处理” |
| `stale_policy` | 遇到 stale bar 怎么定义和处置 | stale 数据会直接影响信号和收益解释 | 不定义 stale，只说“异常值处理” |
| `bad_price_policy` | 明显坏价如何被标记或排除 | 防止价格错误污染下游 | 静默修复，不留标记 |
| `outlier_policy` | 极端值如何被识别和处理 | 防止人为洗平极端样本 | 直接 winsorize 但不声明 |
| `dedupe_rule` | 同一 symbol 同一时间重复记录如何去重 | 没有去重规则就无法复现底表 | 只说“做去重”，不说按什么键 |

### `universe_admission`

这组冻结“谁能进入正式样本”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `benchmark_symbol` | 覆盖审计和残差计算依赖的基准对象 | 后续 benchmark coverage 和 residual 计算都要复用它 | 后面阶段换 benchmark |
| `coverage_floor` | 对象进入正式样本的最低覆盖要求 | 没有 coverage floor，样本准入会变得随意 | 只写“覆盖要足够” |
| `admission_rule` | 低于门槛时如何准入或排除 | 防止按结果手工挑对象 | 写成人工判断 |
| `exclusion_reporting` | 排除项必须怎样落盘和解释 | 防止坏样本静默消失 | 只在聊天里解释，不落正式文件 |

### `shared_derived_layer`

这组冻结“哪些共享派生层允许在 data_ready 生成”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `shared_outputs` | 当前阶段允许产出的共享派生层清单 | 防止在 data_ready 偷偷前移 signal 逻辑 | 把 thesis-specific signal 塞进来 |
| `layer_boundary_note` | 说明共享层的边界，哪些东西必须留给下游 | 防止职责边界变脏 | 不写边界，只列输出名 |

### `delivery_contract`

这组冻结“data_ready 真正要交什么”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | 本阶段必须真实落盘的机器可读产物 | 没有它，就会出现“文档写完了就算完成” | 把 placeholder 文件也算进去 |
| `consumer_stage` | 下一个正式消费这些产物的阶段 | 明确交付对象，防止多套输入并存 | 不写下游消费者 |
| `frozen_inputs_note` | 下游必须复用这一批冻结对象的说明 | 防止 signal_ready 重新造一套输入 | 写成泛泛备注，没约束力 |

## Signal Ready

### `signal_expression`

这组冻结“baseline signal 到底是什么”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `baseline_signal` | 这条 baseline signal 的正式名字 | 下游必须知道自己在消费哪条 signal | 名字和内容对不上 |
| `upstream_inputs` | 这条 signal 依赖哪些 data_ready 正式对象 | 防止下游偷偷加输入 | 写成“多种输入” |
| `state_fields` | 构成 signal 状态的正式字段 | 让 train/test 知道哪些列是 state 变量 | 不列字段，只写“状态特征” |
| `filter_fields` | 构成 signal 过滤条件的正式字段 | 过滤逻辑也是 signal 身份的一部分 | 后续阶段才补过滤字段 |

### `param_identity`

这组冻结“参数对象的身份”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `param_id` | 下游引用这组参数身份的唯一 ID | Train/Test/Review 必须确保讨论的是同一个对象 | 同名不同参数，或参数变了不换 ID |
| `parameter_values` | 这个 `param_id` 对应的具体参数实例 | 没有具体参数值，ID 失去意义 | 只写 ID 不写值 |
| `identity_note` | 对这组参数身份的边界说明，如 baseline-only | 防止后续把 search batch 混进 baseline 身份 | 不写边界说明 |

### `time_semantics`

这组冻结“signal 时间对齐”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `signal_timestamp` | signal 在哪一个时间点被记录为可见 | 后续 label 对齐必须严格依赖它 | 写成模糊的“bar close 附近” |
| `label_alignment` | forward label 从什么时点开始归属 | 防止 signal 和标签错位 | 不写起点，只写“预测未来收益” |
| `no_lookahead_guardrail` | signal 生成时禁止使用哪些未来信息 | 防止时间对齐看起来对、实际偷看未来 | 和 mandate/data_contract 语义不一致 |

### `signal_schema`

这组冻结“下游会看到哪些字段”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `timeseries_schema` | baseline signal 时序文件的正式列集合 | train/test 必须知道哪些列是正式 schema | 只说“有 signal 值” |
| `quality_fields` | 质量和覆盖率相关字段 | 防止下游把质量列误用成信号列 | 不区分正式值和质量辅助列 |
| `schema_note` | schema 边界说明 | 说明哪些列是强约束，哪些是辅助 | 完全不写说明 |

### `delivery_contract`

这组冻结“signal_ready 真正交什么”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | 必须真实物化的机器可读输出，如 `param_manifest.csv` | Train 只能消费正式 signal 产物 | 列了一堆未来计划文件 |
| `doc_artifacts` | companion 文档清单 | 下游需要字段和覆盖解释 | 只有机器文件，没有 companion doc |
| `consumer_stage` | 正式下游阶段 | 锁定交付对象 | 不写或写多个含混消费者 |

## Train Freeze

### `window_contract`

这组冻结“train 能看哪个窗”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `train_window_source` | train 窗来自哪个上游冻结对象 | 让所有人知道训练窗不是临时切的 | 不引用正式 source |
| `train_window_note` | 对 train 窗边界的说明 | 防止窗口理解不一致 | 只写“训练窗” |
| `leakage_guardrail` | 明确 train 阶段不能看的下游信息 | 防止 test/backtest 回写 train | 写成提醒语，无具体边界 |

### `threshold_contract`

这组冻结“哪些尺子是在 train 估出来的”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `threshold_targets` | 哪些对象要在 train 上估阈值 | 不清楚对象就无法解释 train 输出 | 写成“多个指标” |
| `threshold_rule` | 阈值的估计规则 | 后续 test 必须复用同一规则的结果 | 只写“自动估计” |
| `regime_cut_rule` | regime 切点如何在 train 中冻结 | 防止下游改 market regime 切法 | 在 test/backtest 再重切 |
| `frozen_outputs_note` | test 如何复用这些 train 输出 | 锁定 train/test 边界 | 不说明下游复用纪律 |

### `quality_filters`

这组冻结“因质量被淘汰谁”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `quality_metrics` | 用哪些质量指标评估候选对象 | 没有正式质量指标，筛选会变成拍脑袋 | 写收益指标进去 |
| `filter_rule` | 质量过滤规则 | 明确什么情况会被淘汰 | 用“人工判断”替代 |
| `symbol_param_admission_rule` | symbol/param 组合如何通过质量门槛 | 防止后续只保留看起来赚钱的对象 | 用结果表现定义准入 |
| `audit_note` | 哪些观察只记录不进 formal gate | 防止 audit 观察污染正式筛选 | 不区分 formal 与 audit |

### `param_governance`

这组冻结“参数选择轨迹”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `candidate_param_ids` | 正式候选参数身份集合 | 没有候选集合就无法判断筛选范围 | 只保留赢家，不写候选全集 |
| `kept_param_ids` | 当前保留给 test 的参数身份 | 明确 test 允许消费谁 | 不写保留结果 |
| `rejected_param_ids` | 被淘汰的参数身份 | 需要保留失败审计轨迹 | 失败对象直接消失 |
| `selection_rule` | 保留规则 | 让 reviewer 判断筛选逻辑是否正当 | 写成“综合考虑” |
| `reject_log_note` | reject 日志应该怎样记录 | 防止淘汰原因丢失 | 不要求 reject reason |
| `coarse_to_fine_note` | 是否允许后续扩大搜索空间 | 锁定第一版 train 的搜索边界 | 口头说 baseline-only，文档不写 |

### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | train 阶段必须产出的正式文件 | test 只能消费这些正式训练结果 | 只跑出来、不落盘 |
| `consumer_stage` | 正式消费者 | 明确这些输出给谁用 | 不写下游 |
| `reuse_constraints` | test 对 train 输出的复用边界 | 防止 test 重新估 train 尺子 | 只写“供下游参考” |

## Test Evidence

### `window_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `test_window_source` | test 窗来自哪个正式 source | 确保 test 不是临时切出来的 | 不引用正式 time split |
| `test_window_note` | test 窗边界说明 | 防止窗口理解歧义 | 只写“测试窗” |
| `train_reuse_note` | test 如何复用 train 结果 | 防止 test 重新训练 | 不说明复用纪律 |

### `formal_gate_contract`

这组冻结“正式通过标准”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `selected_param_ids` | test 正式通过的参数身份 | backtest 只能消费这些参数对象 | 到 backtest 再决定 |
| `candidate_best_h` | 允许被正式比较的 horizon 集合 | 防止无限试 horizon | 不列候选集，只写结果 |
| `best_h` | test 正式冻结的最佳 horizon | backtest 必须复用它，不能自己重选 | 到 backtest 再挑 |
| `formal_gate_note` | 正式裁决边界说明 | 防止 formal gate 混入 audit 项 | 只写“通过标准见报告” |
| `threshold_reuse_note` | train 阈值如何在 test 中复用 | 进一步防止 test 重估 train 尺子 | 不写 train/test 边界 |

### `admissibility_contract`

这组冻结“最终 whitelist”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `selected_symbols` | 正式通过 test 的 symbol 白名单 | backtest 和 holdout 只能复用它 | backtest 再重新加币 |
| `admissibility_rule` | symbol 进入 whitelist 的规则 | reviewer 需要知道为什么它们能进 | 写成“表现最好” |
| `rejection_rule` | symbol 被拒绝的规则 | 防止被拒对象静默消失 | 不写拒绝逻辑 |
| `summary_note` | 对 whitelist 边界的总结说明 | 告诉下游这是冻结对象，不是建议名单 | 不写冻结性质 |

### `audit_contract`

这组冻结“哪些证据只解释不裁决”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `audit_items` | 只做解释性审计的项目 | 明确哪些内容不进入 formal gate | 把 formal gate 指标塞进来 |
| `formal_vs_audit_boundary` | formal 与 audit 的边界说明 | 这是 test 阶段治理的核心护栏 | 完全不区分两者 |
| `crowding_scope` | 拥挤审计的边界 | 防止 crowding 发现被悄悄当成 formal veto | 写成 formal pass/fail 条件 |
| `condition_analysis_note` | 条件分析的解释用途说明 | 防止 explanatory analysis 反向决定结果 | 把它写成裁决逻辑 |

### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | test 阶段必须正式交付的机器文件 | backtest 只能消费已冻结的 test 结果 | 漏掉 `frozen_spec.json` 这类关键文件 |
| `consumer_stage` | 正式下游 | 锁定 backtest 是唯一消费者 | 写成多个含混下游 |
| `frozen_spec_note` | `selected_symbols` 和 `best_h` 的冻结说明 | 防止 backtest 自己重建 spec | 不强调“必须复用” |

## Backtest Ready

### `execution_policy`

这组冻结“交易语义”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `selected_symbols` | backtest 正式使用的对象集合 | 必须与 test 冻结 whitelist 对齐 | 回测时再补新对象 |
| `best_h` | 正式使用的 horizon | 必须复用 test 的冻结结果 | 自己重新挑更好 horizon |
| `entry_rule` | 正式进场语义 | 没有它就不知道 backtest 在模拟什么动作 | 写成“按信号进场” |
| `exit_rule` | 正式出场语义 | 和 `best_h`、风险控制共同定义交易合同 | 不写退出条件 |
| `cost_model_note` | 成本和滑点口径说明 | 异常好看的结果必须能追溯成本假设 | 只在代码里写，不进合同 |

### `portfolio_policy`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `position_sizing_rule` | 仓位规模规则 | 决定组合收益语义 | 写成“按情况定仓位” |
| `capital_base` | 回测资金基数 | 没有基数，组合结果不可比较 | 不写基数 |
| `max_concurrent_positions` | 同时持仓上限 | 控制组合表达边界 | 后面看到机会再加仓位数 |
| `combo_scope_note` | 组合层面的边界说明 | 防止回测阶段扩成另一套组合逻辑 | 不写组合边界 |

### `risk_overlay`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `risk_controls` | 风险控制清单 | 没有正式风险控制，异常表现无法治理 | 只写“注意风险” |
| `stop_or_kill_switch_rule` | 异常时如何停用或退出 | 防止异常条件下继续硬跑 | 不定义触发规则 |
| `abnormal_performance_sanity_check` | 结果异常时必须做的溯源检查 | 防止“太好看”也直接过 | 没有 sanity check |
| `reservation_note` | 尚未完全解决的保留说明 | 给 reviewer 识别 open risk 的入口 | 把硬问题伪装成保留项 |

### `engine_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `required_engines` | 必须一起运行的正式回测引擎 | 防止只挑对自己有利的引擎 | 跑一套后口头说另一套也差不多 |
| `semantic_compare_rule` | 双引擎何种程度算一致 | 没有一致性规则就无法解释差异 | 写成“结果差不多” |
| `repro_rule` | 同配置下如何定义可复现 | 防止回测不可重放 | 不写复现标准 |
| `engine_scope_note` | 双引擎共同消费什么冻结对象 | 防止两套引擎吃不同输入 | 不说明两引擎输入边界 |

### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | backtest 必须正式交付的机器文件 | holdout 和 reviewer 只能消费这些正式回测结果 | 只保留截图或 summary |
| `consumer_stage` | 正式下游 | 指明 holdout_validation 是下一消费者 | 不写下游 |
| `frozen_config_note` | holdout 如何复用 backtest 冻结配置 | 防止 holdout 自己再配置一套 | 只写“可供参考” |

## Holdout Validation

### `window_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `holdout_window_source` | holdout 窗来自哪个正式 source | 保证 holdout 是真正 untouched window | 临时再切一段出来 |
| `window_plan` | holdout 结果应包含哪些视图，如 single/merged | 明确验证展示口径 | 后面临时补视图 |
| `window_note` | holdout 窗边界说明 | 防止 holdout 被理解成另一次 backtest | 只写“最终验证窗” |
| `no_redefinition_guardrail` | holdout 阶段不得重定义研究问题 | 防止结果不好就改 thesis | 不写 guardrail |

### `reuse_contract`

这组冻结“holdout 绝不能改的东西”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `frozen_config_source` | holdout 复用的正式配置来源 | 没有 source 就无法证明没重配 | 写成“沿用上游配置”但不给来源 |
| `selected_combo_source` | holdout 复用的组合选择来源 | 防止 holdout 重新选组合 | 不写来源 |
| `selected_symbols` | holdout 必须原样复用的 symbol 集合 | 防止验证阶段增删对象 | 看到效果差就换名单 |
| `best_h` | holdout 必须原样复用的 horizon | 防止 holdout 再调持有窗 | 看到效果差就改 horizon |
| `no_reestimate_rule` | 明确禁止 holdout 重新估参数 | 这是 holdout 纯度的核心 | 写成“尽量不重估” |
| `no_whitelist_change_rule` | 明确禁止 holdout 改 whitelist | 防止验证阶段偷偷优化对象集合 | 写成“原则上不改” |

### `drift_audit`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `required_views` | holdout 必须提供哪些 drift 观察视角 | 防止只展示最好看的一个切面 | 只保留单一视图 |
| `direction_flip_rule` | 方向翻转何时必须升级处理 | drift 最严重的情况之一就是方向翻转 | 不定义翻转边界 |
| `sparse_activity_rule` | 交易稀疏时如何解释 | 防止低活动直接被包装成“更稳健” | 不解释稀疏活动 |
| `explanatory_note` | drift 解释的补充说明 | 给 reviewer 提供制度化解释入口 | 用它替代正式规则 |

### `failure_governance`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `retryable_conditions` | 哪些失败属于可重跑的技术或工艺问题 | 防止一失败就无限重试 | 把研究失败也写成可 retry |
| `no_go_conditions` | 哪些失败属于正式 NO-GO | 明确停线边界 | 写得过宽或完全不写 |
| `child_lineage_trigger` | 哪些变更已经需要开子谱系 | 防止在原线里偷偷改题 | 遇到结构性变化还继续原线 |
| `rollback_boundary` | 当前线最多能回改到哪 | 防止 holdout 失败后一路改到 mandate | 写成“视情况而定” |

### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | holdout 阶段必须正式交付的机器文件 | promotion decision 只能消费正式 holdout 产物 | 只写 markdown 总结 |
| `consumer_stage` | 正式下游 | 锁定谁来消费这些验证结果 | 不写消费者 |
| `field_doc_rule` | 每个机器文件都必须有 companion field doc 的规则 | 防止机器文件没人读得懂 | 只交 parquet/csv，不交字段说明 |

## `delivery_contract` 为什么每阶段都有

因为它不是重复字段，而是在每个阶段重复回答同一个问题：

`这一阶段到底怎样才算真的完成？`

它的存在就是为了禁止下面这些伪完成：

- 目录有了，所以算完成
- 文档写了，所以算完成
- 本地跑过了，所以算完成
- 有截图了，所以算完成

## CSF Route

下面这一段补的是 `research_route = cross_sectional_factor` 时，当前仓库实际 freeze draft 会出现的字段。

注意：

- 这里按 runtime / tests 中真实出现的字段来写，便于你直接对照磁盘产物
- 某些 CSF skill 文案和 runtime group 名有抽象层差异，但字段解释以当前实际 draft 为准

### CSF Data Ready

#### `panel_contract`

这组冻结“面板主键和面板时间语义”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `panel_primary_key` | 面板的联合主键，如 `date x asset` | 没有主键定义，后面 panel 就会退化成隐式时序表 | 只写一个维度，或者不写联合主键 |
| `cross_section_time_key` | 横截面切片使用的时间键 | 后续所有按日/按截面统计都依赖它 | 用时序主键口径混写 |
| `asset_key` | 资产维度的主键 | 防止 asset 标识在不同文件中不一致 | 同时混用 symbol、id、alias |
| `universe_membership_rule` | 每个日期点资产是否属于正式 universe 的规则 | 面板成员资格必须可回放，而不是靠结果后修 | 写成“按当时情况决定” |

#### `taxonomy_contract`

这组冻结“分组 taxonomy 的正式引用和映射规则”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `group_taxonomy_reference` | 下游 group-neutral 或 bucket 分析要复用的 taxonomy 版本 | 后续中性化和 group 分析必须复用同一版本 | 只写“行业分类” |
| `group_mapping_rule` | 每个资产如何被映射到组 | 防止不同阶段各自映射导致结果不可比 | 写成人工判断 |
| `taxonomy_note` | taxonomy 的冻结边界说明 | 让 reviewer 知道这里是研究 taxonomy，不是临时标签 | 把边界信息留在聊天里 |

#### `eligibility_contract`

这组冻结“基础可研究掩码”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `eligibility_base_rule` | 资产和日期进入 panel 的基础可研究规则 | 防止把因子缺失和基础准入混在一起 | 把 factor-specific 缺失也塞进来 |
| `coverage_floor_rule` | 截面覆盖率最低要求 | 后续 factor 计算必须建立在足够完整的截面上 | 只写“覆盖要高” |
| `mask_audit_note` | eligibility 掩码与因子缺失的边界说明 | 防止把基础准入问题伪装成因子问题 | 不写边界 |

#### `shared_feature_base`

这组冻结“CSF 共享特征底座”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `shared_feature_outputs` | 允许在 csf_data_ready 产出的共享 panel 特征 | 防止 signal_ready 之前偷做 factor 逻辑 | 把 thesis-specific factor 字段塞进来 |
| `shared_feature_note` | 共享底座的职责边界 | 防止 data_ready 和 factor definition 混层 | 不写边界，只列文件名 |

#### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | csf_data_ready 必须真实交付的机器文件 | csf_signal_ready 只能消费正式 panel 底座 | 只有文档没有 panel 文件 |
| `consumer_stage` | 正式下游阶段 | 锁定消费者为 `csf_signal_ready` | 不写消费者 |
| `frozen_inputs_note` | 下游 factor builder 必须复用这套 panel base 的说明 | 防止 signal_ready 自己重建底座 | 写成可选建议 |

### CSF Signal Ready

#### `factor_identity`

这组冻结“因子身份”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `factor_id` | 当前因子的正式身份 ID | train/test/backtest 必须知道自己在消费哪一个因子对象 | 名字和内容不一致，或内容变了 ID 不变 |
| `factor_version` | 因子版本号 | 因子定义有变更时要能区分 lineage 内版本 | 完全不做版本化 |
| `factor_direction` | 因子方向解释，如 `high_better` | 影响 rank IC、bucket spread 和方向翻转判断 | 到 test 阶段再解释方向 |
| `factor_structure` | 当前因子是 `single_factor` 还是其他结构 | 后续 train/test 需要知道对象结构 | 用口语描述代替结构字段 |

#### `panel_contract`

这组冻结“factor panel 的截面时间语义”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `panel_primary_key` | factor panel 的主键 | 下游所有 factor 统计都依赖一致主键 | 与 csf_data_ready 主键不一致 |
| `as_of_semantics` | 因子值在截面上何时算冻结可见 | 防止截面值的可见时间定义漂移 | 写成“收盘后可见”但不明确截面 close 语义 |
| `coverage_contract` | 每个截面最少需要多少 coverage | 没有 coverage 约束，因子解释会被稀疏样本污染 | 不给数值或规则 |

#### `factor_expression`

这组冻结“因子表达式本身”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `raw_factor_fields` | 因子直接依赖的原始字段 | 后面不能悄悄改因子输入源 | 只写“原始输入” |
| `derived_factor_fields` | 因子表达中间生成的派生字段 | 让下游知道因子值是怎么来的 | 派生字段不落正式合同 |
| `final_score_field` | 最终用于排序或组合的正式分数字段 | train/test 必须知道哪个字段才是正式因子值 | 让多个字段都像 final score |
| `missing_value_policy` | 因子层面的缺失值如何处理 | 防止把 factor 缺失和 eligibility 混在一起 | 静默填补或删除但不声明 |

#### `context_contract`

这组冻结“因子所依赖的上下文对象”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `group_context_fields` | 因子需要的上下文字段，如 group bucket | 下游中性化和组合表达需要复用这些上下文 | 不列上下文字段，只写“按组处理” |
| `component_factor_ids` | 若是多因子结构，这里列组件因子 ID | 防止 multi-factor 组合来源不透明 | 多因子却不列组件 |
| `score_combination_formula` | 多组件如何组合成最终分数 | 防止 train 阶段再学习新的权重或公式 | 写成“综合打分” |

#### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | csf_signal_ready 必须正式交付的机器文件 | csf_train_freeze 只能消费这些正式 factor 产物 | 只落文档，不落 factor panel |
| `consumer_stage` | 正式下游 | 锁定消费者为 `csf_train_freeze` | 不写下游 |
| `frozen_inputs_note` | train 可以动什么、不能动什么 | 防止 train 重新定义 factor | 写成“train 可继续优化 factor” |

### CSF Train Freeze

#### `preprocess_contract`

这组冻结“截面预处理尺子”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `winsorize_policy` | 如何做截面截尾/截断 | 防止 test/backtest 再发明另一套预处理 | 写成“按经验 winsorize” |
| `standardize_policy` | 如何标准化因子值 | 后续排名和中性化依赖它 | 不明确按截面还是全样本标准化 |
| `missing_fill_policy` | 因子缺失值如何处理 | 缺失处理会直接改变因子分布 | 静默 fill |
| `coverage_floor_rule` | 低 coverage 截面如何处理 | 防止在极稀疏截面上继续做排序 | 只说“coverage 要够” |

#### `neutralization_contract`

这组冻结“中性化尺子”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `neutralization_policy` | 正式中性化策略 | 后面组合表达必须复用这套中性化语义 | 与上游 `neutralization_policy` 不一致 |
| `beta_estimation_window` | 若涉及 beta 中性化，beta 的估计窗口 | 防止测试或回测换另一套 beta 估计 | 不写估计窗口 |
| `group_taxonomy_reference` | group-neutral 所依赖的 taxonomy 版本 | 防止换分组体系 | 只写“按行业中性化” |
| `residualization_formula` | 中性化残差的正式公式 | 防止不同阶段各自实现不同残差口径 | 只写“做中性化” |

#### `ranking_bucket_contract`

这组冻结“排序和分桶尺子”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `ranking_scope` | 在什么范围内做排序 | 决定截面比较对象是谁 | 不写范围，只说“按分数排序” |
| `bucket_schema` | 分桶方式，如 quintile | bucket returns 和 monotonicity 依赖它 | test 再换分桶制 |
| `quantile_count` | 桶数 | 防止后续随意改桶数 | 不写数量 |
| `min_names_per_bucket` | 每桶最低名字数 | 防止用过稀疏桶做出漂亮但不稳的结果 | 不写最低容量要求 |

#### `rebalance_contract`

这组冻结“调仓与持有尺子”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `rebalance_frequency` | 多久调仓一次 | 决定后续组合和成本语义 | 到回测才定频率 |
| `signal_lag_rule` | score freeze 后多久才允许交易 | 防止当期值即刻交易的隐性未来函数 | 写成“尽快交易” |
| `holding_period_rule` | 每次持有多久 | 后续组合收益解释依赖它 | 不写持有期 |
| `overlap_policy` | 相邻持仓是否允许重叠 | 影响组合构建和 turnover | 不写 overlap 规则 |

#### `search_governance_contract`

这组冻结“哪些轴在 train 阶段还能动，哪些绝对不能动”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `candidate_variant_ids` | 正式候选变体 ID 集合 | 没有候选集合，筛选轨迹不完整 | 只保留赢家 |
| `kept_variant_ids` | 保留进入 test 的变体 ID | test 必须知道自己能消费谁 | 不写 kept 结果 |
| `rejected_variant_ids` | 被拒绝的变体 ID | 需要 reject ledger 审计轨迹 | 拒绝对象直接消失 |
| `selection_rule` | 变体保留规则 | reviewer 需要判断 train 是否按规则筛选 | 写成“综合考虑” |
| `frozen_signal_contract_reference` | 当前 train 继承自哪一版 signal contract | 防止 train 变体脱离上游 factor 身份 | 不写引用 |
| `train_governable_axes` | 在 train 内允许继续治理的轴 | 明确 train 的合法自由度 | 把 signal expression 轴也塞进来 |
| `non_governable_axes_after_signal` | 在 signal_ready 之后绝对不能再动的轴 | 防止 train 偷改因子定义 | 留空或写不全 |
| `non_governable_axis_reject_rule` | 非法改动这些轴时的处置规则 | 防止非法变体继续伪装成 train variant | 不定义 reject 规则 |

#### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | csf_train_freeze 必须正式交付的机器文件 | csf_test_evidence 只能消费这些正式 train 结果 | 只留 yaml，不留 ledger |
| `consumer_stage` | 正式下游 | 锁定消费者为 `csf_test_evidence` | 不写消费者 |
| `reuse_constraints` | test 对 train 合同的复用边界 | 防止 test 再估 train 尺子 | 写成“供参考” |

### CSF Test Evidence

#### `window_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `test_window_source` | test 窗来源 | 保证 test 不是临时切窗 | 不引用正式 source |
| `train_reuse_note` | test 如何复用 train 规则 | 防止 test 重估预处理和分桶 | 不写复用纪律 |
| `subperiod_rule` | 子区间稳定性如何检查 | CSF 证据层需要看稳定性而不只是整体均值 | 不做 subperiod 规则 |

#### `variant_contract`

这组冻结“进入 test 的 factor 变体对象”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `selected_variant_ids` | test 正式评估的变体 ID | backtest 只能消费 test 准入的变体 | 到 backtest 再选变体 |
| `selection_rule` | test 对变体的准入规则 | 防止 test 再开新搜索 | 写成“挑最好看的” |
| `multiple_testing_note` | 禁止 test 阶段继续扩搜索的说明 | 防止 test 被用成第二轮 train | 不写多重检验边界 |

#### `evidence_contract`

这组冻结“当前 factor_role 应该看哪种证据”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `primary_evidence_contract` | 当前正式证据类型，如 `rank_ic_and_bucket_spread` | 不同 factor role 的正式证据不是一套东西 | 不写证据合同，只看通用收益 |
| `factor_role` | 当前因子角色 | `standalone_alpha` 和 filter/combo 的 gate 逻辑必须分开 | 与上游 role 不一致 |
| `role_specific_note` | 当前角色的特殊说明 | 给 reviewer 一个 role-aware 的判定边界 | 不写 role-specific 边界 |

#### `audit_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `breadth_rule` | 覆盖宽度要求 | 横截面因子如果可交易名字太少，证据不稳 | 不写 breadth 要求 |
| `flip_rule` | 方向翻转何时升级处理 | factor 方向翻转是重大风险 | 不定义翻转边界 |
| `coverage_note` | 覆盖失败的制度说明 | 明确 coverage 是 blocking，不是 audit-only | 把 coverage 问题降成说明项 |

#### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | csf_test_evidence 必须正式交付的机器文件 | csf_backtest_ready 只能消费 test 准入结果 | 只交 summary，不交 gate table |
| `consumer_stage` | 正式下游 | 锁定消费者为 `csf_backtest_ready` | 不写消费者 |
| `frozen_spec_note` | 下游只能消费 test-admitted variants 的说明 | 防止 backtest 再挑新变体 | 写成建议性语气 |

### CSF Backtest Ready

#### `portfolio_contract`

这组冻结“组合表达规则”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `portfolio_expression` | 正式组合表达或目标策略消费方式，如 `long_short_market_neutral`、`benchmark_relative_long_only`、`target_strategy_overlay` | backtest 必须复用上游冻结的表达方式，不能把独立组合和目标策略过滤混成一类 | 写成和上游不一致的表达 |
| `selection_rule` | 多空/选股的正式规则 | 决定组合到底如何从排序结果映射成持仓 | 不写选股规则 |
| `weight_mapping_rule` | 分数如何映射成权重 | 权重规则改变就不是同一组合合同 | 写成“按分数分配”但不具体 |
| `gross_exposure_rule` | 总敞口规则 | 组合收益、风险和容量解释依赖它 | 不写 gross 约束 |

#### `execution_contract`

这组冻结“组合执行口径”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `rebalance_execution_lag` | 调仓信号与实际执行之间的 lag | 防止组合层时间对齐漂移 | 写成“次日执行”但不对应 bar |
| `turnover_budget_rule` | turnover 预算规则 | 容量和成本解释依赖它 | 不写 turnover 上限 |
| `cost_model` | 正式成本模型 | 没有成本模型，净值解释不可信 | 只看 before-cost 结果 |
| `capacity_model` | 正式容量模型 | 回测必须说明容量约束 | 写成“后面再评估容量” |

#### `risk_contract`

这组冻结“组合风控边界”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `max_name_weight_rule` | 单名字权重上限 | 防止单名字主导结果 | 不写单名限制 |
| `net_exposure_rule` | 组合净敞口边界 | 维持组合表达的正式风险口径 | 净敞口不设边界 |
| `group_neutral_overlay` | 若启用 group-neutral，使用哪个 group overlay | 风险解释和行业暴露依赖它 | 不给 overlay 引用 |
| `target_strategy_reference` | 是否对照目标策略 | 保证 comparative backtest 有正式引用 | 明明没 target strategy 还随便挂名 |

#### `diagnostic_contract`

这组冻结“backtest 必须给出哪些诊断视角”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `required_diagnostics` | 必须生成的诊断项清单 | 防止只展示最好看的 summary | 只写收益，不写诊断 |
| `after_cost_rule` | 正式 gate 是否按净成本结果判定 | 防止 before-cost 看起来很好就通过 | 不说明 cost after/before |
| `name_level_rule` | 单名字主导时如何处理 | 防止组合结果其实只是一个名字的故事 | 完全不做 name-level 检查 |

#### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | csf_backtest_ready 必须正式交付的机器文件 | csf_holdout_validation 只能消费正式组合合同和权重输出 | 只留 summary，不留 contract/panel |
| `consumer_stage` | 正式下游 | 锁定消费者为 `csf_holdout_validation` | 不写消费者 |
| `frozen_config_note` | holdout 必须复用这套组合合同的说明 | 防止 holdout 再发明一套组合 | 写成“可参考” |

### CSF Holdout Validation

#### `window_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `holdout_window_source` | holdout 窗来源 | 保证 holdout 是正式 untouched window | 临时再切窗 |
| `reuse_rule` | holdout 只能复用哪些上游合同 | 防止验证阶段改规则 | 写成模糊复用说明 |
| `drift_scope` | drift 比较的范围说明 | 让 reviewer 知道 holdout 在和哪些 prior windows 比 | 不写比较范围 |

#### `reuse_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `backtest_contract_source` | holdout 复用的 backtest 合同来源 | 没有来源就无法证明没换组合合同 | 不引用正式 source |
| `test_contract_source` | holdout 复用的 test gate 来源 | 防止 holdout 脱离 test 准入对象 | 不引用 test source |
| `variant_reuse_rule` | holdout 是否允许改变 selected variants | 防止 holdout 再挑变体 | 写成“原则上不改” |
| `no_reestimate_rule` | holdout 是否允许重估参数 | holdout 纯度的核心字段 | 写成“尽量不重估” |

#### `stability_contract`

这组冻结“稳定性和 drift 的正式判定边界”。

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `direction_flip_rule` | 方向翻转何时升级处理 | factor holdout 里方向翻转是核心风险 | 不定义翻转 |
| `coverage_rule` | 覆盖塌缩时如何处理 | 防止 holdout 因样本塌缩而失真 | 把 coverage collapse 当普通备注 |
| `regime_shift_rule` | regime shift 如何审计 | 给 drift 解释一个正式入口 | 不写 regime 审计要求 |

#### `failure_governance`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `retryable_conditions` | 哪些失败可重跑 | 防止一切失败都被当成工程问题重来 | 把结构性失败也写成可 retry |
| `child_lineage_trigger` | 哪些情况需要开 child lineage | 防止在原线里偷偷重写因子或组合 | 不写 child lineage 触发条件 |
| `rollback_boundary` | 当前线能回改到哪 | 防止 holdout 失败后一路改回 signal/train | 写成“看情况” |

#### `delivery_contract`

| 字段 | 含义 | 为什么需要 | 不该怎么填 |
| --- | --- | --- | --- |
| `machine_artifacts` | csf_holdout_validation 必须正式交付的机器文件 | promotion decision 只能消费正式 holdout 产物 | 只写 narrative 结果 |
| `consumer_stage` | 正式下游或终点标记 | 锁定为终点或明确消费者 | 不写消费者 |
| `field_doc_rule` | 每个机器文件都必须带 companion field doc 的规则 | 防止输出机器文件没人能读懂 | 只交 parquet/json，不交字段说明 |
