---
name: qros-paper-to-spec
description: Turn a paper, PDF, or URL into an implementable strategy spec, optionally followed by automatic implementation when ambiguity is low enough.
---

# qros-paper-to-spec

## Purpose

这个 skill 用于把论文来源整理成 implementable strategy spec。普通用户入口可以直接给：

- `$qros-paper-to-spec <url>`
- 本地 PDF 路径
- 粘贴文本摘要

这个 skill 的默认合同是先接收 `URL / 本地 PDF 路径 / 粘贴文本摘要`，再把它们整理成实现级 spec；普通路径应当默认先产 spec，不先写代码。

这个入口独立于 `qros-research-session`，属于面向论文转规格的 fast-lane，不进入 heavy governance flow 或重治理主流程。

## Execution protocol

把这个 skill 当成真正可执行的 top-level orchestration，不只是合同说明。收到 `$qros-paper-to-spec <url|pdf|summary>` 后，必须按下面的协议执行：

1. 接收 ordinary inputs：
   - URL
   - 本地 PDF 路径
   - 用户直接粘贴的 summary / 摘要 / notes
2. detect `auto_implement`：
   - 如果用户显式说 `auto_implement`、`--auto-implement`、`自动实现`、`继续落 baseline`，视为启用
   - 否则默认关闭，走 `source -> spec -> materialize -> stop`
3. derive source metadata：
   - `source_kind`：至少区分 `url`、`pdf_url`、`local_pdf`、`pasted_summary`
   - `source`：保留原始 URL、PDF 路径或摘要来源标识
   - `title`：优先来自论文标题、PDF 标题或用户给定标题；拿不到时生成清晰占位标题
   - `slug`：基于 title 派生稳定 slug，必要时可由 wrapper 自动派生
   - `target repo`：必须明确当前 active research repo，正式产物只能写到该 repo 的 `outputs/paper_to_spec/<paper_slug>/`
4. read source itself：
   - agent 必须先 read source itself，再生成 spec，不能把读取责任推给 lower-level wrapper
   - URL / pdf_url：使用可用的网页读取工具获取正文、摘要或可见元信息
   - local PDF：使用可用的本地文件/PDF 提取工具读取正文
   - pasted summary：直接把用户粘贴内容当作输入源
   - 如果 local PDF cannot be extracted with available tooling，必须 cleanly degrade：明确要求用户 pasted text instead of inventing content，不能虚构论文内容
5. build internal inventories：
   - `claim inventory`：论文声称的 alpha、因果链、市场假设、限制条件
   - `formula inventory`：公式、指标定义、阈值、窗口、打分、排序、归一化、组合构造
   - `ambiguity inventory`：缺失参数、样本边界、交易实现口径、成本、rebalance、universe、label、evaluation 缺口
6. produce structured spec draft：
   - `paper_stated`：只能放论文或来源明确写出的内容
   - `agent_inferred`：只能放为了实现而补出的假设、默认值、推断口径
   - `implementation_handoff`：给后续实现者的任务拆解、待确认点、数据需求、工程落点
7. follow-up questions：
   - ask at most 1-3 follow-up questions only for blocking ambiguities
   - 非阻断 ambiguities 先写入 spec，不要因为次要缺口停住整个流程
   - 只有在 blocking ambiguities 会直接决定策略定义、收益归因或是否允许 auto_implement 时，才允许追问
8. materialize spec：
   - 先把 draft spec payload 写到 temp spec file
   - 然后调用：

```bash
./.qros/bin/qros-paper-to-spec --spec-file /tmp/paper_to_spec.strategy_spec.yaml --source "..." --source-kind "..." --title "..." [--slug paper-slug]
```

9. optional baseline continuation：
   - if `auto_implement` is enabled and ambiguities are not blocking，继续调用：

```bash
./.qros/bin/qros-paper-to-spec-baseline --spec-path ./outputs/paper_to_spec/<paper_slug>/strategy_spec.yaml
```

10. final report：
   - report where the spec bundle was written
   - 如果进入 auto_implement，report where the baseline files were written
   - 明确说明哪些内容来自 `paper_stated`，哪些来自 `agent_inferred`

## Hard boundaries

- 不得进入 `mandate_admission`
- 不得进入 freeze / review / failure handling main flow
- 不得把 `agent_inferred` 内容表述成论文原文已经明确给出
- 当 ambiguities 中仍存在高风险、会定义策略方向或收益归因的关键歧义时，不得 auto-implement
- 当输出目标需要落盘时，只能写入 active research repo，不能把正式产物写进 QROS framework repo

## Required output bundle

所有产物都必须落在 active research repo 本地 `outputs/` 树下，也就是 `outputs/paper_to_spec/<paper_slug>/` 下，而不是写到 QROS framework repo。repo-local wrapper 只是 lower-level materializer/debug surface，不负责替代 Codex 对 `URL / 本地 PDF 路径 / 粘贴文本摘要` 的读取与 spec 生成。按默认合同，目标落盘产物至少应包含：

- `outputs/paper_to_spec/<paper_slug>/strategy_spec.yaml`
- `outputs/paper_to_spec/<paper_slug>/strategy_spec.md`
- `outputs/paper_to_spec/<paper_slug>/source_manifest.yaml`

如果用户显式要求 `auto_implement`，并且不存在阻断自动实现的关键歧义，额外产物才可以继续写到：

- `outputs/paper_to_spec/<paper_slug>/auto_implement/`

## Ordinary Codex entrypoints

在 Codex 里，普通入口可以直接这样说：

```text
$qros-paper-to-spec <url>
$qros-paper-to-spec https://example.com/paper.pdf
$qros-paper-to-spec ./papers/momentum-reversal.pdf
$qros-paper-to-spec 下面是我整理的论文摘要，请先转成 spec：...
```

这些都表示 ordinary path 应先读取来源，再按默认合同走 `source -> spec -> materialize -> stop`。默认只产出 `strategy_spec.yaml`、`strategy_spec.md` 和 `source_manifest.yaml`，然后停止。

## auto_implement rule

`auto_implement` 是可选续步，不是默认动作。只有用户明确要求继续实现，并且已经没有阻断自动实现的歧义时，才应继续往下走。

- 可以继续时：继续把 spec materialize 后交给自动实现续步
- 不可以继续时：停在 spec，并明确列出 ambiguities
- 只有阻断自动实现的歧义才追问；非阻断项应先写进 spec，再把推断边界标到 `agent_inferred`

## Repo-local materializer/debug wrapper

只有在需要 repo-local runtime 调试、补物化或追踪 wrapper 行为时，才手动调用 lower-level materializer/debug surface；它要求输入预先构建好的 spec 文件，而不是直接吃 URL、PDF 或摘要。`--source` is provenance metadata only，用来记录来源定位；wrapper never fetches/parses paper body itself。`--source` 只作为 provenance metadata，wrapper 不会抓取或解析论文正文：

```bash
./.qros/bin/qros-paper-to-spec --spec-file ./tmp/strategy_spec.yaml --source "https://example.com/paper.pdf" --source-kind pdf_url --title "Example Paper" [--slug example-paper]
```

等价地，本地 PDF 也使用同一套真实 surface：

```bash
./.qros/bin/qros-paper-to-spec --spec-file ./tmp/strategy_spec.yaml --source "./papers/momentum.pdf" --source-kind local_pdf --title "Momentum Paper" [--slug momentum-paper]
```

## Working rules

按以下顺序工作，不要跳步：

1. `source`：锁定论文输入来源，记录 PDF、URL、标题、版本、`source_kind`、`target repo` 和可复现定位信息。
2. `read source itself`：先读取 URL、本地 PDF 或 pasted summary 的实际内容；不要把 source ingestion 推给 wrapper。
3. `inventory`：提取 claim inventory、formula inventory、ambiguity inventory，以及策略构件、数据要求、信号定义、约束、评估口径和实现前置条件。
4. `paper_stated vs agent_inferred`：把论文明确写出的内容放进 `paper_stated`，把模型根据上下文补出的实现假设放进 `agent_inferred`。
5. `implementation_handoff`：整理后续实现落点、数据依赖、阻断项和可自动推进的部分。
6. `temp spec file`：先把结构化 spec draft 写到 temp spec file，再调用 `./.qros/bin/qros-paper-to-spec --spec-file ...`
7. 默认停在 spec：除非用户明确要求 `auto_implement` 且不存在阻断歧义，否则默认只产出 `strategy_spec.yaml`、`strategy_spec.md` 和 `source_manifest.yaml`，然后停止。
8. `auto_implement`：只有在 ambiguities 不阻断时，才调用 `./.qros/bin/qros-paper-to-spec-baseline --spec-path ...`

## Output expectations

- `strategy_spec.yaml` 应该让后续实现者可以直接按字段落地，而不是再回到论文全文猜测
- `strategy_spec.md` 是对 YAML spec 的可读渲染，不应发明第二套字段语义
- `source_manifest.yaml` 记录 source kind、locator、title 和 capture time
- spec draft 至少应显式包含 `paper_stated`、`agent_inferred` 和 `implementation_handoff`
- 当 auto-implement 被拒绝时，要明确原因是高风险策略定义歧义，而不是把拒绝伪装成实现完成
