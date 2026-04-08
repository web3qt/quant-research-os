# 🛠 Quant Research OS | 量化研究操作系统

[English](README_EN.md) | 中文

QROS 是一个面向 agent 的阶段式研究治理框架。它把原始交易想法推进为**可审查、可复现、可追溯**的 research lineage，并通过 freeze、review、formal artifacts 与 workflow gates 约束研究如何被定义、推进和否决。

## 当前主流程阶段图

```text
00_idea_intake -> 00_mandate
├─ time_series_signal
│  -> 01_data_ready
│  -> 02_signal_ready
│  -> 03_train_freeze
│  -> 04_test_evidence
│  -> 05_backtest_ready
│  -> 06_holdout_validation
└─ cross_sectional_factor
   -> 01_csf_data_ready
   -> 02_csf_signal_ready
   -> 03_csf_train_freeze
   -> 04_csf_test_evidence
   -> 05_csf_backtest_ready
   -> 06_csf_holdout_validation
```

QROS 负责把阶段顺序、freeze/review gate、failure routing 和 lineage discipline 固定下来；研究真正落地时，agent 应在当前 research repo 中生成和维护该条研究线的正式产物。

## Repo 边界

这个仓库是 **研究流程框架仓**，不是某条具体策略线的真实研究产物仓。

- 这里提供：workflow、skills、runtime、gate discipline、review discipline
- 这里不承载：某条具体研究线的真实业务实现、因子研究代码、回测实现本体
- 实际研究应在当前 research repo 的 `outputs/<lineage_id>/` 下推进

从 lineage-local stage program hard gate 起，每个可执行阶段都必须在当前 research repo 的 `outputs/<lineage_id>/program/` 下保留 route-aware stage program（至少包含 `stage_program.yaml`、`README.md` 和被 manifest 引用的 entrypoint），并在对应阶段产物目录写出 `program_execution_manifest.json`。QROS runtime 只负责 gate、合同校验、调用、产物验证和 provenance 记账，不再把 framework-side shared builder 当作完成来源。

## 单入口 orchestrator

安装完成后，推荐始终从统一入口开始：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

这个入口会：

- 创建或恢复 lineage
- 判断当前真实阶段
- 推导当前该由哪个 skill 接手
- 在需要治理确认时停下来交互
- 在可以确定性落盘时写出 formal artifacts

## 快速开始

### Claude Code

```text
/plugin marketplace add web3qt/quant-research-os
/plugin install quant-research-os@qros
```

安装后在新会话中提及量化研究想法，QROS 会自动激活。

### Codex

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

## 开始研究

开始研究时，继续使用上面的单入口 orchestrator：`qros-research-session`。

## 为什么使用 QROS

大多数研究想法最开始只是聊天里的模糊表达，正式研究不能停留在这里。QROS 的目标是把研究流程从“口头讨论”推进到“明确边界、冻结合同、正式落盘、阶段可审查”。

## 当前关键制度变化

- 所有 `*_review` 阶段都要求**独立的 adversarial reviewer**
- reviewer 必须检查 stage artifact、provenance，以及 lineage-local `program/<stage>/` 源码
- 只有 `CLOSURE_READY_*` 结果才能继续运行 `~/.qros/bin/qros-review` 写 closure artifacts
- `FIX_REQUIRED` 会把流程退回 author-fix loop，禁止直接写 `stage_completion_certificate.yaml`
- review 闭环之上还有 **governance-candidate lane**：post-rollout review findings 会写成 `governance_signal.json`，再聚合到 `governance/review_findings_ledger.jsonl` 与 `governance/candidates/*.yaml`
- 候选优先级固定为：`hard_gate -> template_constraint -> regression_test`
- human governance decision 也不会直接激活 policy；真正生效仍要走正常 repo 变更

## 日常使用

正常使用时，直接在研究仓里通过 skill 名称进入：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-mandate-review
```

如果要做手动诊断或恢复，可以直接调用仓库里的稳定 wrapper：

```bash
~/.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
~/.qros/bin/qros-review
```

如果你想看更细的实际运行行为、状态字段、stage gate 语义和恢复方式，可以继续读：

- `docs/experience/qros-research-session-usage.md`
- `docs/experience/qros-verification-tiers.md`
- `docs/main-flow-sop/research_workflow_sop.md`

## 验证分层

QROS 现在把流程级验证分成：

- `smoke`
- `full-smoke`

例如：

```bash
python scripts/run_verification_tier.py --tier smoke
python scripts/run_verification_tier.py --tier full-smoke
```

如果已经按安装文档落好稳定 wrapper，也可以用：

```bash
~/.qros/bin/qros-verify --tier smoke
```

## 安装后更新

**Claude Code:**

```text
/plugin update quant-research-os
```

**手动安装:**

```bash
git pull && ./setup --host codex --mode user-global
```

如果你之前装的是旧版（例如还在用 `~/.agents/skills`，或还保留 display 相关旧 skill/runtime），也按上面这条重新执行一次，然后**重启 Codex**，让本地安装树刷新到当前合同。

## 用户如何开始使用（Codex）

安装完成后，按这 4 步走即可：

1. 克隆仓库并运行：

```bash
./setup --host codex --mode user-global
```

2. 重启 Codex
3. 在新会话里直接输入第一条命令：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
```

也可以先看帮助：

```text
qros-research-session help
```

如果你想直接验证安装是否正常，也可以运行：

```bash
~/.qros/bin/qros-verify --tier smoke
```

## 运行时布局

**插件安装（Claude Code）:**

插件系统自动管理 skill 发现和 hook 注入。

**手动安装（Codex / 通用）:**

```text
~/.codex/skills/qros-*
~/.qros/
```

Codex 扫描 `~/.codex/skills/`，`./setup --mode user-global` 会把扁平 `qros-*` skills 直接写进去。

## 延伸阅读

- [Claude Code 安装说明](.claude/INSTALL.md)
- [Codex 安装说明](docs/experience/installation.md)
- [QROS for Codex](docs/README.codex.md)
- [Codex 快速开始](docs/experience/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/experience/qros-research-session-usage.md)
- [阶段冻结字段说明](docs/experience/stage-freeze-group-field-guide.md)

## 常见问题

- Claude Code 看不到技能：确认已执行 `/plugin install web3qt/quant-research-os`，重启会话
- Codex 看不到技能：确认 `~/.codex/skills/` 里存在 `qros-*`
- 感觉安装内容过旧：Claude Code 执行 `/plugin update quant-research-os`；手动安装执行 `git pull && ./setup --host codex --mode user-global`，然后重启 Codex
- 不确定安装是否正常：新开会话，输入 “帮我研究一个量化策略” 测试自动触发
