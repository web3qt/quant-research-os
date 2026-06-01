# QROS paper-to-spec 使用说明

## 当前状态

`qros-paper-to-spec` 的旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

当前不要再把它当作“PDF 直接生成完整 strategy spec”或“PDF 直接生成回测代码”的入口。旧版 `paper -> strategy_spec -> baseline` fast-lane 已经下线。

## 新方向

下一版 `qros-paper-to-spec` 会采用 data-spec-first。第一产物将是：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

这个 `paper_data_spec.yaml` 会优先解决：

- PDF 读取覆盖：读了哪些页、哪些章节、哪些表格或公式低置信。
- crypto perpetual 数据需求：universe、bar、price type、funding、fees/slippage、label、timestamp alignment。
- 严格阻断问题：核心 data 口径不清楚时，先停下来问研究员。
- data implementation handoff：后续数据准备需要哪些 raw inputs、derived inputs 和 validation checks。

## 边界

- 不直接生成完整 strategy spec。
- 不直接生成回测代码。
- 不是 `qros-research-session` 的阶段入口。
- 不进入 heavy governance flow。
- 不把 crypto perpetual 迁移假设伪装成论文原文。

## 后续

`paper_data_spec.yaml` 稳定后，再继续设计 paper signal spec、train-freeze spec、test-evidence spec 和 backtest spec。
