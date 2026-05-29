# QROS paper-to-spec 使用说明

## 它是什么

`qros-paper-to-spec` 是一个把论文来源转成实现级策略规格说明的 Codex skill。它适合先把研究论文拆成结构化 spec，再决定是否继续自动实现。

这个 skill 的默认合同是接收 `URL / 本地 PDF 路径 / 粘贴文本摘要`，默认先产 spec，不先写代码。

这是独立 fast-lane，不是 `qros-research-session` 的阶段入口，也不进入 heavy governance flow。

## 实际执行流程

顶层 skill 现在是可操作的 source-ingestion orchestration，不是抽象占位。收到 `$qros-paper-to-spec <url|pdf|summary>` 后，Codex 会按这条顺序工作：

1. 接收普通输入：URL、本地 PDF 路径，或你直接 pasted summary。
2. detect `auto_implement`：只有你显式写了 `auto_implement`、`--auto-implement`、`自动实现` 之类的意思，才会尝试继续。
3. derive `source_kind`、`source`、`title`、`slug` 和 `target repo`：
   - `source_kind` 至少区分 `url`、`pdf_url`、`local_pdf`、`pasted_summary`
   - `target repo` 指当前 active research repo；正式产物只能落到这个 repo
4. read source itself：
   - URL 或 PDF URL：skill 自己读取网页/PDF 可见内容
   - 本地 PDF：skill 自己尝试读取本地 PDF 内容
   - pasted summary：直接以你粘贴的内容为准
   - 如果本地 PDF 用当前可用工具无法提取文字，会 cleanly degrade 成让你 pasted text，而不是 invent 内容
5. build internal inventories：
   - `claim inventory`
   - `formula inventory`
   - `ambiguity inventory`
6. 生成结构化 spec draft，至少拆成：
   - `paper_stated`
   - `agent_inferred`
   - `implementation_handoff`
7. ask at most 1-3 follow-up questions only for blocking ambiguities。
8. 先把 spec draft 写到 temp spec file，再调用 lower-level wrapper 物化正式产物。
9. 如果 `auto_implement` 已启用，而且 ambiguities 不阻断自动实现，再继续调用 baseline helper。

默认合同仍然是 `source -> spec -> materialize -> stop`。

## 它不做什么

- 不进入 `qros-research-session`
- 不进入 `mandate_admission`
- 不进入 freeze / review / failure handling 的 heavy governance flow
- 不会把 `agent_inferred` 伪装成论文已经明确写出的 `paper_stated`
- 当仍有高风险、会改变策略定义的歧义时，不会自动实现

## 输出产物

所有产物都应写入 active research repo 本地 `outputs/` 树下的 `outputs/paper_to_spec/<paper_slug>/`，而不是写到 QROS framework repo。Codex skill 负责普通入口上的 source-to-spec 编排；repo-local wrapper 只是 lower-level materializer/debug surface。按默认合同，目标产物为：

- `outputs/paper_to_spec/<paper_slug>/strategy_spec.yaml`
- `outputs/paper_to_spec/<paper_slug>/strategy_spec.md`
- `outputs/paper_to_spec/<paper_slug>/source_manifest.yaml`

如果用户显式开启 `--auto-implement`，还可以继续写入：

- `outputs/paper_to_spec/<paper_slug>/auto_implement/`

## 在 Codex 里怎么用

普通 skill 入口支持 URL、本地 PDF 路径和粘贴摘要。可以直接把 `$qros-paper-to-spec <url>` 当成最短入口理解。

默认合同是 `source -> spec -> materialize -> stop`，也就是默认先停在 spec，不先写代码。

URL 入口：

```text
$qros-paper-to-spec <url>
$qros-paper-to-spec https://example.com/paper.pdf
```

除非你显式要求自动实现，否则默认停在 `strategy_spec.yaml`、`strategy_spec.md` 和 `source_manifest.yaml`，不继续进入实现。

本地 PDF 路径入口：

```text
$qros-paper-to-spec ./papers/momentum-reversal.pdf
```

粘贴文本摘要入口：

```text
$qros-paper-to-spec 下面是我整理的论文摘要，请输出 spec，并把 paper_stated / agent_inferred 分开写：...
```

只有在你明确要求 `--auto-implement`，并且不存在阻断自动实现的歧义时，才允许继续实现：

```text
$qros-paper-to-spec https://example.com/paper.pdf --auto-implement
```

## Repo-local runtime 调试

正常入口仍然是 Codex skill。top-level skill 负责 source ingestion，也就是自己先 read source itself、整理 `source_kind`、确定 `target repo`、产出 claim inventory / formula inventory / ambiguity inventory，并把 draft 写到 temp spec file。只有在需要 deterministic wrapper 调试、补物化或追踪 runtime 行为时，才手动调用 repo-local wrapper。`./.qros/bin/qros-paper-to-spec` 是 lower-level materializer/debug surface，需要预先准备好的 spec 文件；`--source` is provenance metadata only，wrapper never fetches/parses paper body itself。`--source` 只作为 provenance metadata，wrapper 不会抓取或解析论文正文：

```bash
./.qros/bin/qros-paper-to-spec --spec-file ./tmp/strategy_spec.yaml --source "https://example.com/paper.pdf" --source-kind pdf_url --title "Momentum Paper" [--slug momentum-paper]
```

如果你只是想让 runtime 自动派生 slug，也应使用同一套真实参数：

```bash
./.qros/bin/qros-paper-to-spec --spec-file ./tmp/strategy_spec.yaml --source "./papers/momentum.pdf" --source-kind local_pdf --title "Momentum Paper" [--slug momentum-paper]
```

如果你已经有现成的 `strategy_spec.yaml`，只是想基于这个已有 spec 生成或排查 baseline scaffold，可以改用 `./.qros/bin/qros-paper-to-spec-baseline`。它是更低层的 lower-level deterministic scaffold/debug surface，消费的是现有 `--spec-path`，不会在没有 spec 的情况下替你先生成 baseline spec；普通用户入口仍然应该先走 `$qros-paper-to-spec`，而不是跳过 skill 直接从 baseline helper 开始。

如果 spec 已经生成，但你仍在判断是否继续实现，默认仍然停在 spec。只有阻断自动实现的歧义才追问，而且 ask at most 1-3 follow-up questions only for blocking ambiguities；没有阻断时，先把 spec 物化完整，再决定是否进入 `auto_implement`。

当 `auto_implement` 启用且没有阻断歧义时，top-level skill 会继续调用：

```bash
./.qros/bin/qros-paper-to-spec-baseline --spec-path ./outputs/paper_to_spec/<paper_slug>/strategy_spec.yaml
```

最终回复应明确报告 spec bundle 写到了哪里；如果继续 auto_implement，也要报告 baseline files 写到了哪里。
