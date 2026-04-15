# Stage Artifact Map Draw.io Design

## Goal

在 `docs/show/` 下新增一个 draw.io 展示图，用于回答三个问题：

1. 每个阶段先看什么
2. 每个阶段生成什么文件
3. 每个文件大致是干什么的

## Scope

只覆盖当前 first-wave 已落地编排：

- `idea_intake`
- `mandate`
- mainline: `data_ready -> signal_ready -> train_freeze -> test_evidence -> backtest_ready -> holdout_validation`
- CSF: `csf_data_ready -> csf_signal_ready -> csf_train_freeze -> csf_test_evidence -> csf_backtest_ready -> csf_holdout_validation`

不覆盖当前终点之后的任何治理阶段。

## Recommended Format

新增一个 draw.io 文件：

- `docs/show/qros-stage-artifact-map.drawio`

采用 **一个文件、两页图**：

1. `Mainline`
2. `CSF`

原因：

- 一个页面同时塞下 mainline + CSF 的所有阶段会过于拥挤
- 两页仍然属于一个 draw.io 文件，用户易于打开和分享
- `idea_intake` 和 `mandate` 是共享前置，可以在两页中用相同的“共用说明框”表达

## Visual Structure

每一页都包含三层：

### 1. 顶部说明框

说明统一目录合同：

- `author/draft/`
- `author/formal/`
- `review/request/`
- `review/result/`
- `review/closure/`
- `review/governance/`

同时给出统一阅读顺序：

1. `author/formal/artifact_catalog.md`
2. `author/formal/field_dictionary.md`
3. `author/formal/*gate_decision.md` 或 `*contract.md`
4. 核心 machine artifacts
5. `review/closure/stage_completion_certificate.yaml`

### 2. 阶段卡片

每个阶段一个卡片，每张卡片固定包含：

- 阶段名
- 对应目录
- `先看`
- `生成`
- `用途`

### 3. 阶段顺序箭头

用简洁箭头表达阶段推进顺序，但不把 `display` 画成强制门。

## Content Rules

### Common Rules

- 每个阶段只列最重要的 formal artifacts，不把所有辅助文件都塞进去
- 文件名必须真实存在于当前 repo 合同或 runtime 中
- 用途描述控制在一句话内
- 优先使用 `artifact_catalog.md` 和 `field_dictionary.md` 作为阅读入口

### Mainline Page

包含：

- `idea_intake`
- `mandate`
- `data_ready`
- `signal_ready`
- `train_freeze`
- `test_evidence`
- `backtest_ready`
- `holdout_validation`

### CSF Page

顶部说明：

- `idea_intake` 和 `mandate` 与 mainline 共用
- route split 后进入 CSF 独立链

包含：

- `csf_data_ready`
- `csf_signal_ready`
- `csf_train_freeze`
- `csf_test_evidence`
- `csf_backtest_ready`
- `csf_holdout_validation`

## README Integration

更新 `docs/show/README.md`，增加一个简短 section：

- 图文件路径
- 两页分别看什么
- 建议阅读方式

## Rejected Alternatives

### 1. 只在 README 里写表格

拒绝原因：

- 用户明确要 draw.io 图
- 阶段顺序、阅读顺序、文件用途在图里更容易讲解

### 2. 一个页面放下全部 mainline + CSF

拒绝原因：

- 信息量过大
- 阶段卡片会过小，不利于读文件名和用途

### 3. 每个阶段单独一张 draw.io

拒绝原因：

- 文件太碎
- 不适合 `docs/show` 的展示入口定位

## Decision

采用：

- `docs/show/qros-stage-artifact-map.drawio`
- 两页：
  - `Mainline`
  - `CSF`
- `docs/show/README.md` 增加入口说明
