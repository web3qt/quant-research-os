# 🛠 QROS | 阶段式研究治理框架

> 把“聊天里的想法”推进成一条**可审查、可复现、可追溯**的 research lineage。

QROS 是一个面向 agent 的阶段式研究治理框架。它不替你发明 alpha，也不替某条具体研究线代存真实业务代码。它负责把研究过程里的 freeze、review、formal artifacts、failure routing 和 lineage discipline 固定下来。

## ✨ 先记住这三件事

| 主题 | 结论 |
| --- | --- |
| 你现在看的是什么 | **框架仓**，不是策略实现仓 |
| 普通使用者怎么进入 | 统一入口是 **`qros-research-session`** |
| 真实研究产物写到哪里 | 当前 research repo 的 **`outputs/<lineage_id>/`** |

## 🚀 Codex 用户怎么开始

如果你本身就在 `Codex` 里工作，最短安装入口可以直接写成：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

安装完成后，在 Codex 里直接开始：

```text
$qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT ，横截面研究
$qros-research-session help
```

更新时，在 Codex 里直接运行：

```text
$qros-update
```

> 📌 推荐默认只记这一条主路径：安装好以后，先从 `$qros-research-session` 开始，不要先去背一堆 skill 名。

<details>
<summary><strong>手动安装、更新与验证</strong></summary>

手动安装：

```bash
git clone https://github.com/web3qt/quant-research-os.git ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
./setup --host codex --mode user-global
```

然后 **Restart Codex**，再在当前 research repo 根执行：

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

更新安装：

```bash
git pull && ./setup --host codex --mode user-global
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

如果你已经在 Codex 里，优先直接运行 `qros-update`，它会顺手刷新当前 repo 的 `./.qros/`。

最小验证：

```bash
./.qros/bin/qros-verify --tier smoke
```

手动诊断或恢复：

```bash
./.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
./.qros/bin/qros-review
```

</details>

## 🗺️ 当前主流程阶段图

```text
00_idea_intake -> 01_mandate
├─ time_series_signal
│  -> 02_data_ready
│  -> 03_signal_ready
│  -> 04_train_freeze
│  -> 05_test_evidence
│  -> 06_backtest_ready
│  -> 07_holdout_validation
└─ cross_sectional_factor
   -> 02_csf_data_ready
   -> 03_csf_signal_ready
   -> 04_csf_train_freeze
   -> 05_csf_test_evidence
   -> 06_csf_backtest_ready
   -> 07_csf_holdout_validation
```

QROS 负责固定阶段顺序、freeze/review gate、failure routing 和 lineage discipline。研究真正落地时，agent 必须在当前 research repo 中生成和维护正式产物。

当前 single-entry `qros-research-session` 的实际编排边界是：

- 一直推进到 `holdout_validation review`
- `holdout_validation review` 之后即停止

## 🧱 仓库结构

| 目录 | 作用 |
| --- | --- |
| `contracts/` | machine-readable truth，供 runtime、review engine、skill 生成直接读取 |
| `skills/` | author、failure handling、orchestrator 技能 |
| `runtime/bin/` | 稳定入口，例如 `qros-session`、`qros-review`、`qros-verify` |
| `runtime/scripts/` | 命令行 wrapper |
| `runtime/tools/` | stage runtime、gate 校验、program/provenance 处理 |
| `docs/` | 安装、SOP、字段说明、使用路径 |
| `tests/` | bootstrap、安装、workflow、runtime、anti-drift 回归 |
| `harness/` | 分层 `AGENTS.md` 的演示与验证子树，不是主流程 demo |

第一次接触 grouped freeze 字段，先看：

- `docs/guides/stage-freeze-group-field-guide.md`

如果要看验证分层，先看：

- `docs/guides/qros-verification-tiers.md`

## ⚠️ 当前关键约束

- 所有 `*_review` 阶段都要求独立的 adversarial reviewer
- reviewer 必须检查 stage artifact、provenance，以及 lineage-local `program/<stage>/` 源码
- 只有 `CLOSURE_READY_*` 才能继续运行 `./.qros/bin/qros-review` 写 closure artifacts
- `FIX_REQUIRED` 会把流程退回 author-fix loop，禁止直接写 `stage_completion_certificate.yaml`

## 📚 延伸阅读

- [文档导航](docs/README.md)
- [QROS 工作原理：两层运行时架构](docs/guides/how-qros-works.md) — 宿主 AI Runtime 与 QROS Python Runtime 如何协作
- [Codex 安装说明](docs/guides/installation.md)
- [QROS for Codex](docs/README.codex.md)
- [Codex 快速开始](docs/guides/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/guides/qros-research-session-usage.md)
- [阶段冻结字段说明](docs/guides/stage-freeze-group-field-guide.md)
