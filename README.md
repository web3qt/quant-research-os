# 🧭 QROS

> 把研究想法推进成一条**可审查、可复现、可追溯**的 research lineage。

`治理框架` `Codex 技能` `阶段门禁` `正式产物` `失败处置`

QROS 是面向 agent 的量化研究治理框架。它不替你发明 alpha，也不替某条具体研究线保存真实策略代码；它负责把研究过程里的 freeze、review、formal artifacts、failure routing 和 provenance 固定下来。

> [!IMPORTANT]
> QROS 是 **框架仓**，不是策略实现仓。
> 真实研究程序和正式研究产物应写在 active research repo 的 `outputs/<lineage_id>/` 下。

## 先从这里开始

在你的 active research repo 根目录打开 Codex，然后输入：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

安装或刷新完成后，Restart Codex，再从同一个 research repo 继续。

| 你想做什么 | 输入什么 |
| --- | --- |
| 开始或继续一条研究线 | `$qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT，横截面研究` |
| 查看 QROS 使用帮助 | `$qros-research-session help` |
| 查看当前研究进度 | `$qros-progress` |
| 查看横截面因子阶段质量诊断 | `$qros-factor-diagnostics` |
| 更新 QROS 到远程最新版本，并刷新当前 repo 的 `./.qros/` | `$qros-update` |

> [!TIP]
> 普通使用者默认只需要记住一条主路径：安装好以后，先从 `$qros-research-session` 开始。

`$qros-progress` 是只读进度查询入口。它默认读取当前 repo 的 `outputs/`，选择最近修改的 lineage，返回当前 stage、active skill、gate 状态、blocking reason 和 next action；它不写 artifact，也不推进 stage。

`$qros-factor-diagnostics` 是可选 diagnostics 入口。它查看 CSF 阶段的数据质量、因子质量、回测结果和 holdout 稳定性；它不是 review，不是 gate，不写 review closure，也不替代 `$qros-review`。

在 Codex 里可以这样问：

```text
$qros-factor-diagnostics 看下当前 lineage 的因子诊断
$qros-factor-diagnostics 看下 csf_test_evidence 阶段的 Rank IC、分层和稳定性
$qros-factor-diagnostics 看下 csf_backtest_ready 阶段的成本后收益、回撤、换手和容量
$qros-factor-diagnostics 看下 csf_holdout_validation 阶段有没有退化或 regime shift
$qros-factor-diagnostics mean IC 为负说明什么，跟当前策略方向有没有冲突
$qros-factor-diagnostics 不要只给数字，用中文解释这些指标说明什么
```

## QROS 负责什么

| 领域 | QROS 做什么 | QROS 不做什么 |
| --- | --- | --- |
| 流程 | 固定 stage flow、freeze group、review gate、failure routing | 代替研究员判断 alpha 是否成立 |
| 产物 | 定义 formal artifact shape 和 machine-readable contract | 把 placeholder 文件当作 stage 完成 |
| 运行时 | 校验并调用 lineage-local stage program | 偷偷生成框架侧 completion fallback |
| 审查 | 要求独立 adversarial reviewer 和 closure evidence | 让 author 自己给自己放行 |

> [!NOTE]
> QROS 的重点不是“多生成几个文件”，而是让每个阶段的输入、输出、审查和失败处置都有可追溯的证据链。

## 主流程

`qros-research-session` 是当前普通研究工作的统一入口。

当前 single-entry 编排会推进到 `holdout_validation review` closure。closure 后先进入 `holdout_validation_next_stage_confirmation_pending`；显式执行 `CONFIRM_NEXT_STAGE` 后进入 `holdout_validation_review_complete` 终态，不再继续更后面的治理阶段。

```text
idea_intake
  -> mandate
  -> route selection
     -> time_series_signal
     -> cross_sectional_factor
  -> holdout_validation review closure
  -> holdout_validation_review_complete
```

<details>
<summary>展开完整阶段图</summary>

```text
00_idea_intake -> 01_mandate
├─ time_series_signal
│  -> 02_data_ready
│  -> 03_signal_ready
│  -> 04_train_freeze
│  -> 05_test_evidence
│  -> 06_backtest
│  -> 07_holdout
└─ cross_sectional_factor
   -> 02_csf_data_ready
   -> 03_csf_signal_ready
   -> 04_csf_train_freeze
   -> 05_csf_test_evidence
   -> 06_csf_backtest_ready
   -> 07_csf_holdout_validation
```

</details>

## 仓库地图

| 目录 | 作用 |
| --- | --- |
| `contracts/` | machine-readable truth，供 runtime、review engine 和 skill generation 读取 |
| `skills/` | author、review、failure handling、orchestrator skill source |
| `runtime/bin/` | 稳定用户入口，例如 `qros-session`、`qros-review`、`qros-verify` |
| `runtime/scripts/` | command-line wrappers 和 deterministic task runner |
| `runtime/tools/` | stage runtime、gate 校验、program/provenance 处理 |
| `docs/` | 安装、SOP、字段说明、使用路径 |
| `tests/` | bootstrap、安装、workflow、runtime、anti-drift regression |

## Review 规则

- 每个 `*_review` 阶段都要求独立 adversarial reviewer。
- reviewer 必须检查 stage artifact、provenance，以及对应的 lineage-local route-aware stage program 源码。
- 只有 `CLOSURE_READY_*` 才能继续运行 `./.qros/bin/qros-review` 写 closure artifacts。
- `FIX_REQUIRED` 会把流程退回 author-fix loop，禁止直接写 `stage_completion_certificate.yaml`。

> [!WARNING]
> 不要因为目录存在、文件占位或只有合同说明文档，就宣称某个 stage 已完成。
> QROS 的完成标准是 formal artifacts、provenance、review closure 和 gate 语义同时成立。

## 常用文档

| 想了解 | 去哪里 |
| --- | --- |
| 文档导航 | [docs/README.md](docs/README.md) |
| QROS 工作原理 | [docs/guides/how-qros-works.md](docs/guides/how-qros-works.md) |
| Codex 安装说明 | [docs/guides/installation.md](docs/guides/installation.md) |
| QROS for Codex | [docs/README.codex.md](docs/README.codex.md) |
| Codex 快速开始 | [docs/guides/quickstart-codex.md](docs/guides/quickstart-codex.md) |
| 统一研究会话说明 | [docs/guides/qros-research-session-usage.md](docs/guides/qros-research-session-usage.md) |
| 因子阶段 diagnostics | [docs/guides/qros-factor-diagnostics.md](docs/guides/qros-factor-diagnostics.md) |
| 阶段冻结字段说明 | [docs/guides/stage-freeze-group-field-guide.md](docs/guides/stage-freeze-group-field-guide.md) |
| 验证分层 | [docs/guides/qros-verification-tiers.md](docs/guides/qros-verification-tiers.md) |
