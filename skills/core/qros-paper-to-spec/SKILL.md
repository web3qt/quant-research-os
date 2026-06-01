---
name: qros-paper-to-spec
description: Prepare the next paper-to-spec v2 flow; the old strategy_spec materializer has been removed and the rebuilt path will be data-spec-first.
---

# qros-paper-to-spec

## Current status

`qros-paper-to-spec` 保留为 Codex skill 名称，但旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

当前不要把这个入口解释成“PDF 直接生成完整 strategy spec”或“PDF 直接生成回测代码”。旧的 `paper -> strategy_spec -> baseline` fast-lane 已经下线。

## Direction

下一版 `qros-paper-to-spec` 会采用 data-spec-first：

1. 读取论文来源。
2. 记录 PDF 读取覆盖和低置信区域。
3. 面向 crypto perpetual 场景生成 `paper_data_spec.yaml`。
4. 如果核心 data 口径不清楚，先停下来问研究员。
5. 等 data spec 稳定后，再设计 signal / train-freeze / test-evidence / backtest spec。

## Boundaries

- 不直接生成完整 strategy spec。
- 不直接生成回测代码。
- 独立于 `qros-research-session`，不进入主研究会话。
- 不进入 mandate / freeze / review / failure handling 的 heavy governance flow。
- 不把 agent 对 crypto perpetual 的迁移假设伪装成论文原文。

## Next implementation target

后续重建时，第一产物应是：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

该产物应包含 PDF 读取覆盖摘要、crypto perpetual 数据需求、严格阻断问题和 data implementation handoff。
