# 🛠 QROS | 阶段式研究治理框架

QROS是一个面向 agent 的阶段式研究治理框架。它不替你发明 alpha，也不替某条具体研究线代存真实业务代码。它做的事是把研究从“聊天里的想法”推进成一条**可审查、可复现、可追溯**的 research lineage，并用 freeze、review、formal artifacts、failure routing 和 lineage discipline 约束这条线如何被定义、推进、否决和重开。

它：

- **不是策略实现仓，这是研究流程框架仓。**
- **普通使用者的入口不是几十个 skill，而是一个：`qros-research-session`。**
- **真实研究产物不写在这个仓库里，而写在当前 active research repo 的 `outputs/<lineage_id>/` 下。**

## Codex 用户怎么开始

如果你本身就在 `Codex` 里工作，最短安装入口可以直接写成：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

安装完成后，在 Codex 里直接开始：

```text
$qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT ，横截面研究
$qros-research-session help
```

## 当前主流程阶段图

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

## 项目边界

先抓住三件事：

1. **框架仓**，也就是这个 repo。这里放 workflow、skills、runtime、schema、SOP 和测试。
2. **安装产物**。Codex 从 `~/.codex/skills/qros-*` 发现技能，每个 research repo 有自己的 `./.qros/` 本地 runtime。
3. **真实研究仓**。formal artifacts、review closure、lineage-local stage program 都应写到当前 research repo 的 `outputs/<lineage_id>/` 下。

这也是 README 最重要的判断边界：QROS 提供制度，不代存某条具体研究线的真实业务代码。

从 `mandate` 开始，每个可执行阶段都必须在 `outputs/<lineage_id>/program/` 下保留 route-aware stage program，至少包含：

- `stage_program.yaml`
- `README.md`
- 被 manifest 引用的 entrypoint

对应阶段产物目录还必须写出 `program_execution_manifest.json`。整个不变量是 `freeze approval -> lineage-local program -> artifact build -> review closure`，不能再回退到 `framework-side shared builder` 充当完成来源。

空目录、placeholder 文件、只有合同语义的说明文档，都不能被当作阶段完成。

## 仓库结构

- `contracts/`：machine-readable truth，供 runtime、review engine、skill 生成直接读取
- `skills/`：author、failure handling、orchestrator 技能
- `runtime/bin/`：稳定入口，例如 `qros-session`、`qros-review`、`qros-verify`
- `runtime/scripts/`：命令行 wrapper
- `runtime/tools/`：stage runtime、gate 校验、program/provenance 处理
- `docs/`：安装、SOP、字段说明、使用路径
- `tests/`：bootstrap、安装、workflow、runtime、anti-drift 回归
- `harness/`：分层 `AGENTS.md` 的演示与验证子树，不是主流程 demo

如果是第一次接触 grouped freeze 字段，先看：

- `docs/guides/stage-freeze-group-field-guide.md`

如果要看验证分层，先看：

- `docs/guides/qros-verification-tiers.md`

## 当前关键约束

- 所有 `*_review` 阶段都要求独立的 adversarial reviewer
- reviewer 必须检查 stage artifact、provenance，以及 lineage-local `program/<stage>/` 源码
- 只有 `CLOSURE_READY_*` 才能继续运行 `./.qros/bin/qros-review` 写 closure artifacts
- `FIX_REQUIRED` 会把流程退回 author-fix loop，禁止直接写 `stage_completion_certificate.yaml`
- review findings 会继续汇入 governance-candidate lane，但 human governance decision 仍然不能直接替代正常 repo 变更

## 延伸阅读

- [文档导航](docs/README.md)
- [QROS 工作原理：两层运行时架构](docs/guides/how-qros-works.md) — 宿主 AI Runtime 与 QROS Python Runtime 如何协作
- [Codex 安装说明](docs/guides/installation.md)
- [QROS for Codex](docs/README.codex.md)
- [Codex 快速开始](docs/guides/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/guides/qros-research-session-usage.md)
- [阶段冻结字段说明](docs/guides/stage-freeze-group-field-guide.md)

## 常见问题

- Codex 看不到技能：确认 `~/.codex/skills/` 里存在 `qros-*`
- 感觉安装内容过旧：执行 `git pull && ./setup --host codex --mode user-global`，再在当前 research repo 根执行 `~/workspace/quant-research-os/setup --host codex --mode repo-local`，然后重启 Codex
- 不确定安装是否正常：新开会话，输入 “帮我研究一个量化策略” 测试自动触发
