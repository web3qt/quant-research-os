# 🛠 Quant Research OS | 量化研究操作系统

[English](README_EN.md) | 中文

QROS 是一个面向 Codex 的阶段式研究工作流。它通过交互式 mandate 冻结、正式产物和流程门禁，把原始交易想法转成可审查、可复现、可追溯的研究线。

## 为什么使用 QROS

大多数研究想法最开始只是聊天里的模糊表达，正式研究不能停留在这里。QROS 的目标是把研究流程从“口头讨论”推进到“明确边界、冻结合同、正式落盘、阶段可审查”。

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

## 快速开始

先把 QROS clone 到固定位置，再把 skills 链接给 Codex：

```bash
git clone <QROS_REPO_URL> ~/.codex/qros
mkdir -p ~/.agents/skills
ln -s ~/.codex/qros/skills ~/.agents/skills/qros
```

然后在你的研究仓里打开 Codex，从下面的统一入口开始：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

## 日常使用

正常使用时，直接在研究仓里通过 skill 名称进入：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-mandate-review
```

如果要做手动诊断或恢复，可以直接调用仓库里的稳定 wrapper：

```bash
~/.codex/qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
~/.codex/qros/bin/qros-review
```

## 安装后更新

更新只需要：

```bash
cd ~/.codex/qros
git pull
```

## 运行时布局

```text
~/.codex/qros/skills/
~/.agents/skills/qros -> ~/.codex/qros/skills
```

Codex 扫描 `~/.agents/skills/`，`qros` 入口通过 symlink 指向仓库里的 skill tree.

## 延伸阅读

- [安装说明](docs/experience/installation.md)
- [Codex 快速开始](docs/experience/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/experience/qros-research-session-usage.md)

## 常见问题

- 看不到技能：确认 `~/.agents/skills/qros` 指向 `~/.codex/qros/skills`
- 感觉安装内容过旧：进入 `~/.codex/qros` 执行 `git pull`
- 不确定安装是否正常：在 Codex 中查看 `qros-research-session` 是否可见
