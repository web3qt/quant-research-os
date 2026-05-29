# Paper-to-Spec Fast Lane 设计

## 目标

新增一条独立于 `qros-research-session` 的轻量 fast lane：

`paper/pdf/url -> implementable strategy spec -> optional auto implementation`

它的目标不是把论文纳入 QROS 重治理流程，而是把论文、PDF 或网页中的策略描述压缩成一份“可实现策略层”的 spec，降低 agent 在实现阶段的语义漂移，并允许在用户显式要求时直接继续写复现代码。

## 非目标

本能力默认不做以下事情：

- 不进入 `mandate_admission`
- 不进入 freeze / review / failure handling 主流程
- 不宣称任何正式研究 stage 已完成
- 不把 QROS 框架仓当成 live lineage 正式研究产物仓
- 不要求为论文构造重治理 artifact package

## 设计结论

采用独立 fast lane，而不是把论文入口揉进现有主流程。

推荐新增独立 skill 或等价入口，暂定名 `paper-to-spec`。它接收 `PDF / 网页 URL / 本地文档 / 长文本摘要`，输出两份文件：

- `strategy_spec.yaml`：机器可读，实现 agent 的主输入
- `strategy_spec.md`：给人审阅的解释版摘要

默认停在 spec；当用户显式开启自动继续实现时，若 spec 满足自动实现条件，则继续进入实现阶段。

## 为什么不接入主流程

用户目标是“快速复现策略”，不是走完整治理闭环。现有 QROS 主流程擅长的是：

- 冻结研究合同
- 逐 stage 物化 formal artifacts
- 做 review closure 与 failure routing

而论文复现入口更需要的是：

- 从非结构化 source 中提炼实现约束
- 把论文原文与 agent 推断严格分开
- 为后续代码实现提供稳定 handoff

因此，最佳边界是：把这条能力设计成 QROS 体系旁边的一条轻量实现加速通道，而不是修改主 workflow 语义。

## 用户入口

建议支持以下入口形态：

- `$paper-to-spec <url>`
- `$paper-to-spec /path/to/paper.pdf`
- `$paper-to-spec "<paper summary>"`
- `$paper-to-spec <source> --auto-implement`

默认行为：

1. 读取并理解 source
2. 生成 `strategy_spec.yaml` 与 `strategy_spec.md`
3. 输出简短摘要并停止，等待用户审阅

显式 `--auto-implement` 行为：

1. 先生成 spec
2. 若存在高风险歧义，则拒绝自动实现并说明原因
3. 若满足自动实现条件，则把 spec 交给实现 agent 继续写代码

## 输出目录

建议统一落盘到：

- `outputs/paper_to_spec/<paper_slug>/strategy_spec.yaml`
- `outputs/paper_to_spec/<paper_slug>/strategy_spec.md`
- `outputs/paper_to_spec/<paper_slug>/source_manifest.yaml`

其中：

- `strategy_spec.yaml` 是实现主输入
- `strategy_spec.md` 是人类审阅摘要
- `source_manifest.yaml` 只记录 source 元信息与抓取上下文，不承担治理语义

## 核心设计：可实现策略层 spec

本能力的 spec 收敛到“可实现策略层”，而不是只做研究摘要，也不是直接逼近代码实现细节。

这个抽象层要求 spec 至少明确：

- 策略要做什么
- 需要哪些数据
- 信号或因子如何定义
- 标签或持有期如何定义
- 组合或触发逻辑如何执行
- 评估口径是什么
- 论文没写清的地方由哪些推断补全

这样可以避免两类问题：

- 抽象太高，agent 实现时重新发明关键细节
- 抽象太低，把论文未明确给出的细节伪装成确定事实

## 双层内容模型

`strategy_spec.yaml` 应固定为两层主语义：

- `paper_stated`
- `agent_inferred`

### `paper_stated`

只允许记录论文正文、附录、图表或 source 中可直接归因的内容，不做推断。

建议包含：

- `strategy_claim`
- `market_scope`
- `universe_rule`
- `data_requirements`
- `feature_definition`
- `label_or_target`
- `portfolio_construction`
- `risk_controls`
- `cost_model`
- `evaluation_protocol`

进入 `paper_stated` 的唯一门槛是：必须能在 source 中找到明确依据。

### `agent_inferred`

只记录论文未明确、但实现必须做出的补全决策，并显式标记这是 agent 推断，不是论文原意。

建议包含：

- `inference_log`
- `implementation_choices`
- `default_assumptions`
- `ambiguities`
- `fallback_plan`

每条推断都应尽量带上：

- 推断原因
- 依据来源
- 置信度
- 是否存在替代实现

## 为什么这些约束必须冻结

论文复现最容易漂移的通常不是代码风格，而是策略定义本身。需要被 spec 固定下来的点主要包括：

- 研究对象：市场、资产类型、universe
- 标签语义：收益从何时开始算、持有多久
- 信号定义：字段口径、公式符号、时间对齐
- 组合表达：rank、bucket、threshold、filter、long-short、long-only
- 评估口径：IC、分层、组合收益、成本前后、基准比较
- 缺省规则：缺失值处理、调仓时点、成本口径、异常样本处理

如果这些点不冻结，后续实现 agent 很容易在不同会话中生成不同版本的“同一策略”。

## 建议的 YAML 结构

建议 `strategy_spec.yaml` 采用如下顶层结构：

```yaml
spec_version: v1
source:
  kind: pdf_url | webpage | local_pdf | local_doc | text_summary
  locator: ...
  title: ...
  capture_time: ...
strategy_identity:
  title: ...
  summary: ...
  strategy_type: cross_sectional_factor | time_series_signal | event_driven | execution_rule
paper_stated:
  strategy_claim: ...
  market_scope: ...
  universe_rule: ...
  data_requirements: ...
  feature_definition: ...
  label_or_target: ...
  portfolio_construction: ...
  risk_controls: ...
  cost_model: ...
  evaluation_protocol: ...
agent_inferred:
  inference_log: ...
  implementation_choices: ...
  default_assumptions: ...
  ambiguities: ...
  fallback_plan: ...
implementation_handoff:
  required_modules: ...
  expected_inputs: ...
  expected_outputs: ...
  validation_targets: ...
```

## `strategy_spec.md` 的职责

`strategy_spec.md` 是 YAML 的解释版，用于快速人工确认。建议固定展示：

- 论文核心策略主张
- 已识别的策略类型
- `paper_stated` 中最关键的实现约束
- `agent_inferred` 中最关键的补全决策
- 仍未解决的歧义
- 如果继续实现，推荐先实现哪一版 baseline

它的职责是让用户快速判断“这份 spec 是否已经足够指导代码实现”，而不是复写整篇论文摘要。

## 执行流程

建议将 `paper-to-spec` fast lane 固定为 5 步。

### Step 1: 接收并标准化 source

支持：

- PDF 链接
- 网页链接
- 本地文档路径
- 粘贴的长文本摘要

产出基础 source 元信息：

- `source.kind`
- `source.locator`
- `source.title`
- `source.capture_time`

这里不设计硬编码文档解析器，默认依赖 agent 本身读取和理解内容的能力。

### Step 2: 先形成 evidence 视图

在写 spec 前，先把 source 中与实现有关的信息压成内部 evidence 视图，例如：

- `claim inventory`
- `formula inventory`
- `implementation clue inventory`
- `ambiguity inventory`

目标是先把“可实现相关信息”从论文叙述中剥离出来，再决定哪些能进入 `paper_stated`，哪些必须进 `agent_inferred`。

### Step 3: 生成 `paper_stated`

规则：

- 能归因到 source 的内容，才允许进入 `paper_stated`
- 图表若能清楚支持某个实现约束，也可进入 `paper_stated`
- 仅凭常识补全的内容，不得进入 `paper_stated`

### Step 4: 生成 `agent_inferred`

针对实现必需但 source 未写清的部分，输出：

- 推断结论
- 推断理由
- 置信度
- 备选实现

这样实现 agent 不必重新从零决定缺失项，而是直接消费这批补全决策。

### Step 5: 决定是否自动继续实现

- 默认：停在 spec，等待用户确认
- 显式 `--auto-implement`：若满足自动实现条件，则继续交给实现 agent

实现 agent 的首要输入应是 `strategy_spec.yaml`，而不是重新读 source。只有在 spec 缺关键字段时，才允许回看 source。

## 自动实现放行条件

只有满足以下条件时，`--auto-implement` 才应放行：

- `paper_stated.feature_definition` 足够明确，不是纯概念表述
- `portfolio_construction` 至少明确到排序、分组、打分或触发逻辑中的一种
- `label_or_target` 足够明确，知道预测对象或持有期结算方式
- `agent_inferred.ambiguities` 中没有会改变策略本体的高风险歧义
- `data_requirements` 不依赖当前环境明显不可得的数据

## 必须拒绝自动实现的高风险歧义

出现以下情况时，应停在 spec，而不是继续写代码：

- 论文只讲现象，没有给出可执行信号定义
- 核心公式缺变量定义，或符号复用导致含义不唯一
- 组合构建方式不清楚，long-short / long-only / filter 边界混乱
- 回测结论依赖特殊数据，但 source 没说明如何获取
- 关键结果可能依赖未来信息、幸存者偏差或其他不可复现处理
- 同一篇论文存在多种合理实现，且结果可能显著不同

## 轻量失败分类

本 fast lane 不引入 QROS 主流程式 failure handling，只做轻量分类：

- `SOURCE_UNREADABLE`
- `SPEC_UNDERDETERMINED`
- `IMPLEMENTATION_BLOCKED`
- `MULTI_VARIANT_REQUIRED`

### `SOURCE_UNREADABLE`

- 含义：链接失效、PDF 不可读、正文抓取失败或 source 无法访问
- 动作：停止，并要求用户替换 source

### `SPEC_UNDERDETERMINED`

- 含义：能读懂主题，但不足以生成可实现 spec
- 动作：输出当前已提取内容与 unresolved 清单，不继续实现

### `IMPLEMENTATION_BLOCKED`

- 含义：spec 已可形成，但实现被数据或环境前提阻断
- 动作：允许 spec 落盘，但不进入实现

### `MULTI_VARIANT_REQUIRED`

- 含义：存在多种合理实现，不能假装只有一个标准版本
- 动作：在 spec 中显式区分 baseline variant 与 alternate variants

## UX 原则

该入口的外部表达应尽量轻，不复用重治理术语。

对用户展示时应优先回答：

- 这篇论文是否足以形成可实现 spec
- 哪些约束是论文原文支持的
- 哪些实现细节是 agent 推断补全的
- 当前是否存在阻断自动实现的高风险歧义
- 是否建议继续自动实现

不应优先讲：

- stage
- freeze
- review closure
- governance completion

## 与 QROS 主流程的关系

这条能力应与当前主流程并存，而不是替代或污染主流程语义。

建议关系如下：

- `paper-to-spec`：轻量实现加速入口
- `qros-research-session`：正式治理与阶段推进入口

未来如果用户希望把 `paper-to-spec` 产出的 spec 升级为正式研究线输入，可以再设计单独的“spec import into QROS governance”桥接能力；首版不应把两者强绑在一起。

## 首版范围

首版只需要支持最小闭环：

1. 接收 source
2. 生成 `strategy_spec.yaml`
3. 生成 `strategy_spec.md`
4. 判断是否可自动继续实现
5. 在显式开启时继续进入实现

首版不要求：

- 通用 PDF parser framework
- 多论文合并
- 论文之间冲突裁决
- 自动 benchmark against paper results
- 主流程级别的 formal review artifacts

## 推荐的一句话定义

`paper-to-spec` 是一条独立 fast lane，用来把论文、PDF 或 URL 中的策略描述压缩成可实现策略 spec，并在用户显式允许时继续自动实现。
