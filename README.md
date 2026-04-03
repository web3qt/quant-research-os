# 🛠 Quant Research OS | 量化研究操作系统

[English](README_EN.md) | 中文

QROS 是一个面向 agent 的阶段式研究工作流。它通过交互式 mandate 冻结、正式产物和流程门禁，把原始交易想法转成可审查、可复现、可追溯的研究线。

QROS 是一个指导 agent 辅助研究员开展正式策略研究的治理框架。本仓库提供研究流程、阶段门禁、skills、runtime、lineage 与 review discipline，用来约束研究如何被定义、冻结、审查和推进。

本仓库不负责沉淀某条具体策略线的真实业务研究代码，也不要求研究员在这里手写因子、回测或验证实现。具体研究代码应由 agent 在当前研究仓中生成，并按 QROS 合同产出正式 artifact，供研究员审查、确认和推进。空目录、占位文件和只有语义说明的文档不能被当作阶段完成。

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

安装完成后，从统一入口开始研究流程：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

## 为什么使用 QROS

大多数研究想法最开始只是聊天里的模糊表达，正式研究不能停留在这里。QROS 的目标是把研究流程从"口头讨论"推进到"明确边界、冻结合同、正式落盘、阶段可审查"。

## 第一阶段工作流

当前统一入口覆盖：

- `idea_intake`
- `mandate`
- `mandate review`
- `data_ready`
- `data_ready review`
- `signal_ready`
- `signal_ready review`
- `train_freeze`
- `train_freeze review`
- `test_evidence`
- `test_evidence review`
- `backtest_ready`
- `backtest_ready review`
- `holdout_validation`
- `holdout_validation review`

推荐的使用方式是 skill-first：

- 从一个统一 skill 入口开始
- 让 agent 创建或恢复 research lineage
- 让工作流驱动下一步必须发生的交互
- 让正式产物落盘并成为唯一事实来源

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

## 安装后更新

**Claude Code:**

```text
/plugin update quant-research-os
```

**手动安装:**

```bash
cd ~/.qros && git pull
```

## 运行时布局

**插件安装（Claude Code）:**

插件系统自动管理 skill 发现和 hook 注入。

**手动安装（Codex / 通用）:**

```text
~/.qros/skills/
~/.agents/skills/qros -> ~/.qros/skills
```

Codex 扫描 `~/.agents/skills/`，`qros` 入口通过 symlink 指向仓库里的 skill tree.

## 延伸阅读

- [Claude Code 安装说明](.claude/INSTALL.md)
- [Codex 安装说明](docs/experience/installation.md)
- [QROS for Codex](docs/README.codex.md)
- [Codex 快速开始](docs/experience/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/experience/qros-research-session-usage.md)
- [阶段冻结字段说明](docs/experience/stage-freeze-group-field-guide.md)

## 常见问题

- Claude Code 看不到技能：确认已执行 `/plugin install web3qt/quant-research-os`，重启会话
- Codex 看不到技能：确认 `~/.agents/skills/qros` 指向 `~/.qros/skills`
- 感觉安装内容过旧：Claude Code 执行 `/plugin update quant-research-os`；手动安装执行 `cd ~/.qros && git pull`
- 不确定安装是否正常：新开会话，输入 "帮我研究一个量化策略" 测试自动触发
