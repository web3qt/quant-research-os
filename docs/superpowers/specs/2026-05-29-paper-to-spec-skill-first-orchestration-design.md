# Paper-to-Spec Skill-First Orchestration 设计

## 目标

把当前 `paper-to-spec` 的低层 materializer-only fast lane，升级成一条真正的 skill-first orchestration lane：

`paper/pdf/url -> source understanding -> implementable strategy spec -> materialize bundle -> optional baseline implementation`

它的首要目标不是扩张治理，而是让用户可以直接把论文、PDF、网页链接或文本摘要交给 `$qros-paper-to-spec`，由 agent 在 skill 层完成 source 阅读、spec 提炼、必要追问，并在需要时继续自动实现 baseline。

## 当前基础

当前仓库已经有：

- `runtime/tools/paper_to_spec.py`
- `runtime/scripts/run_paper_to_spec.py`
- `runtime/bin/qros-paper-to-spec`
- `contracts/paper_to_spec/strategy_spec_contract.yaml`
- `skills/core/qros-paper-to-spec/SKILL.md`

这套基础设施目前更接近一个 deterministic materializer：它消费结构化 spec payload，把结果物化为：

- `strategy_spec.yaml`
- `strategy_spec.md`
- `source_manifest.yaml`

下一阶段不应推倒这层，而应在它之上增加真正的 source ingestion / orchestration 层。

## 非目标

首版 orchestration 不做以下事情：

- 不把论文入口并入 `qros-research-session`
- 不进入 `mandate_admission` / `mandate` / freeze / review / failure handling 主流程
- 不在 runtime 层实现硬编码网页解析器或 PDF 解析器
- 不保证直接复现论文最终收益结果
- 不强行统一所有 target repo 的研究代码模板
- 不把 QROS 框架仓当成 active research repo

## 核心结论

采用 skill-first 单入口编排：

- `$qros-paper-to-spec` 是唯一普通入口
- skill 层负责：
  - 读取 `URL / 本地 PDF 路径 / 粘贴文本摘要`
  - 提炼 `paper_stated` / `agent_inferred`
  - 识别阻断自动实现的高风险 `ambiguities`
  - 必要时追问 1-3 个关键问题
  - 生成 draft spec
  - 调现有 materializer 落盘
  - 在满足条件时继续自动实现 baseline
- runtime 层继续保持 deterministic：
  - 不读论文
  - 不做网页/PDF 解析
  - 只负责校验、slug/路径安全、bundle 物化

## 为什么选 skill-first

用户已经明确不想为 source 阅读写硬编码解析器，并且预期 agent 自身能够：

- 读网页
- 读 PDF
- 理解论文
- 提炼实现约束

因此最合理的边界是：

- skill / agent 层负责不确定性工作
- runtime 层负责确定性工作

这比 runtime-first 方案更稳：

- 避免在 runtime 里堆积脆弱的内容解析逻辑
- 保留 agent 在 source 理解上的灵活性
- 保持 runtime 测试边界清晰

## 输入范围

首版正式支持三类输入：

- URL
- 本地 PDF 路径
- 粘贴文本摘要

不把聊天附件接入放进首版范围。

理由：

- 这三类已经覆盖大多数真实使用场景
- 附件接入会引入额外的 connector / session surface 集成
- 首版应先把 skill-first 主链打通

## 交互模式

普通模式与自动实现模式共存。

### 普通模式

默认行为：

1. 读取 source
2. 提炼 spec
3. 调 materializer 落盘
4. 停在 spec，不自动写代码

### 自动实现模式

当用户显式要求 `auto_implement` 时：

1. 读取 source
2. 提炼 spec
3. 若存在阻断型歧义，则先追问
4. 调 materializer 落盘
5. 在目标 repo 中生成 baseline
6. 执行最小验证

## 歧义处理策略

采用双模式：

- 默认 best-effort 落盘
- 只有当歧义会阻断自动实现时，才追问

### 阻断型歧义

以下情况会阻断自动实现：

- 核心信号公式不完整
- 组合表达不清楚，无法区分 `long_short` / `filter` / `ranking`
- `label_or_target` 或 `holding_horizon` 缺失
- 关键数据依赖是否存在无法判断
- 同一论文存在两种以上会显著改变 baseline 结果的合理实现

### 非阻断型歧义

以下情况允许直接落盘：

- 成本口径未完全写死
- 次要 preprocessing 规则未说明
- 存在可接受的默认缺省策略

这类信息进入 `agent_inferred.ambiguities` 或 `agent_inferred.default_assumptions`，而不是阻断 spec 生成。

### 追问策略

当 `auto_implement=true` 且命中阻断型歧义时：

- 最多追问 1-3 个关键问题
- 只问会改变 baseline 实现形态的缺口
- 不问装饰性问题

如果 `auto_implement=false`，则即使有阻断型歧义，也允许先落盘 best-effort spec，只是明确标记 `ambiguities`。

## 统一执行流

建议固定为 7 步。

### Step 1: 标准化输入

统一形成 source descriptor：

- `source_kind`
- `source_locator`
- `source_title`
- `target_repo`
- `auto_implement`

### Step 2: 阅读并提炼 evidence

在 skill 内部形成工作级 evidence 视图：

- `claim inventory`
- `formula inventory`
- `implementation clue inventory`
- `ambiguity inventory`

这一步不要求 runtime 落盘。

### Step 3: 生成 draft spec

生成与现有 contract 对齐的 draft：

- `strategy_identity`
- `paper_stated`
- `agent_inferred`
- `implementation_handoff`

### Step 4: 判断是否需要追问

只有当自动实现会被高风险歧义阻断时才进入追问。

### Step 5: 追问关键缺口

若需要，则在 skill 中向用户追问 1-3 个关键问题，再刷新 draft spec。

### Step 6: 调 materializer 落盘

把 draft payload 交给现有 materializer，生成正式 bundle：

- `strategy_spec.yaml`
- `strategy_spec.md`
- `source_manifest.yaml`

### Step 7: 条件性进入 baseline implementation

仅当以下条件全部满足时才继续：

- 用户显式要求自动实现
- spec 已成功落盘
- 不存在阻断型歧义
- target repo 已明确且有效

## repo 选择规则

自动实现支持双模式：

- 默认：当前 active research repo
- 显式：用户指定 target repo

若指定 repo 无效：

- spec 仍可落盘到当前目标上下文
- 自动实现应停止，不应假装成功

## 输出位置规则

无论是否自动实现，spec bundle 都必须写在目标 active research repo 的本地输出树：

- `outputs/paper_to_spec/<paper_slug>/strategy_spec.yaml`
- `outputs/paper_to_spec/<paper_slug>/strategy_spec.md`
- `outputs/paper_to_spec/<paper_slug>/source_manifest.yaml`

必须反复明确：

- 这些文件属于 active research repo
- 不属于 QROS 框架仓的正式研究产物

## baseline 输出策略

采用双模式：

### 模式 A: repo-native

若 target repo 已有明确研究代码组织方式，则复用现有模式，不另发明模板。

例如可能已有：

- `research/`
- `strategies/`
- `src/`
- 既有 loader / signal / backtest 组织方式

### 模式 B: template fallback

若 target repo 不存在明确研究模式，则生成最小 fallback 结构，例如：

- `paper_specs/<paper_slug>/README.md`
- `paper_specs/<paper_slug>/strategy_config.yaml`
- `paper_specs/<paper_slug>/build_dataset.py`
- `paper_specs/<paper_slug>/build_signal.py`
- `paper_specs/<paper_slug>/run_backtest.py`
- `paper_specs/<paper_slug>/tests/test_smoke.py`

这里的原则不是美观，而是：

- 可运行
- 可读
- 可继续人工修改

## baseline 最低交付

无论 repo-native 还是 fallback，自动实现至少产出：

- spec 绑定说明
- 最小数据入口
- baseline signal / feature logic
- 最小 portfolio / trigger logic
- run entrypoint
- minimal verification entrypoint

## 最小验证定义

首版自动实现的最小验证只覆盖 4 类。

### 1. spec binding check

验证实现明确绑定到某份 `strategy_spec.yaml`，避免实现与 spec 漂移成两套东西。

### 2. data contract smoke

验证最小数据入口可运行：

- 需要哪些字段
- 缺字段如何报错
- 给定样例输入能否走通

### 3. strategy pipeline smoke

验证最小 pipeline 闭环：

- 数据读取
- 特征 / 信号计算
- 组合 / 触发逻辑
- 结果输出

这里不要求收益正确，只要求流程能跑通。

### 4. artifact existence check

验证 baseline 运行后能生成最小结果物，如：

- signal output
- backtest output
- summary / report file

### 最小验证不包含

以下内容不属于首版 fast lane baseline：

- 对齐论文表格结果
- 全参数搜索
- 多 variant 比较
- 样本外稳定性分析
- 容量 / 成本深度建模
- 大规模回归测试

## 验证失败时的处理

若最小验证失败：

- spec 保留
- baseline 实现保留
- 状态标记为 `implementation_blocked`
- 返回明确失败点

不要因为 baseline 验证失败就回退成“什么都没生成”。

## 分层职责

### Skill 层

负责：

- source ingestion
- evidence 提炼
- `paper_stated` / `agent_inferred` 区分
- ambiguity 判断
- 必要追问
- 调 materializer
- 条件性启动 baseline implementation

### Runtime 层

负责：

- spec shape 校验
- slug / path 安全
- bundle 物化
- deterministic error surface

### Implementation 层

负责：

- 根据已落盘 spec 在目标 repo 中生成 baseline
- 选择 repo-native 或 fallback 模式
- 执行最小验证

## 与当前 materializer 的关系

当前 low-level surface 保持不变：

- `./.qros/bin/qros-paper-to-spec` 仍然是 lower-level materializer / debug surface
- 它继续要求 `--spec-file --source --source-kind --title [--slug]`

普通用户入口仍然应该是：

- `$qros-paper-to-spec <url>`
- `$qros-paper-to-spec /abs/path/to/paper.pdf`
- `$qros-paper-to-spec "<paper summary>"`

也就是说：

- skill surface 负责“从 source 到 spec”
- wrapper surface 负责“把已有 spec payload 物化”

## 实现拆分

建议拆成 4 个实现块。

### Block 1: skill orchestration 升级

改造 `$qros-paper-to-spec` 的真实工作流，使其支持：

- `URL / 本地 PDF 路径 / 粘贴文本摘要`
- source 阅读
- spec draft 生成
- ambiguity 决策
- 必要追问

### Block 2: draft-to-materializer bridge

定义 skill 产出的 draft payload 如何交给现有 materializer，保持 runtime 只消费结构化 spec，不自己解析论文。

### Block 3: auto-implement orchestration

在 `auto_implement=true` 且无阻断歧义时：

- 选择 target repo
- 识别 repo-native 模式或 fallback 模式
- 生成 baseline
- 执行最小验证

### Block 4: cross-layer regression coverage

锁住：

- skill / docs / runtime / wrapper 之间的一致性
- active research repo 输出边界
- best-effort vs blocking ambiguity 行为
- auto-implement 的最小验证口径

## 推荐实现顺序

建议顺序：

1. Block 1
2. Block 2
3. Block 4
4. Block 3

理由：

- 先打通 source -> spec 主链
- 再把 draft 和 materializer 接稳
- 先补回归，锁住接口
- 最后再接自动实现，避免入口未稳时就放大复杂度

## 风险与边界

### 风险 1: source 理解错误

由于首版不做 deterministic source parser，source 理解质量依赖 agent 本身。因此必须继续坚持：

- `paper_stated` 与 `agent_inferred` 严格分层
- 有歧义就显式进入 `ambiguities`

### 风险 2: target repo 风格不一致

repo-native 模式会面临代码结构差异，因此 fallback template 必须始终保留。

### 风险 3: 用户误把 skill 当 wrapper

文档必须明确区分：

- `$qros-paper-to-spec`：普通用户入口
- `./.qros/bin/qros-paper-to-spec`：低层 materializer / debug 入口

## 推荐的一句话定义

把当前 materializer-only fast lane，升级成一个真正的 skill-first paper ingestion + spec generation + optional baseline implementation orchestration lane。
