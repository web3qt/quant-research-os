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

推荐的使用方式是 skill-first：

- 从一个统一 skill 入口开始
- 让 agent 创建或恢复 research lineage
- 让工作流驱动下一步必须发生的交互
- 让正式产物落盘并成为唯一事实来源

## 快速开始

在当前仓库里为 Codex 安装 QROS：

```bash
./setup --host codex --mode repo-local
```

然后在这个仓库里打开 Codex，从下面的统一入口开始：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

## 安装模式

- `repo-local`
  技能写入 `.agents/skills/`，运行时资产写入 `.qros/`
- `user-global`
  技能写入 `~/.codex/skills/`，运行时资产写入 `~/.qros/`

常用命令：

```bash
./setup --host codex --mode repo-local
./setup --host codex --mode user-global
./setup --host codex --mode auto
./setup --host codex --check
./setup --host codex --refresh
```

## 已安装用户如何更新

- `repo-local`
  先执行 `git pull`。如果你希望受管资产按最新仓库状态重写，再执行 `./setup --host codex --refresh`。
- `user-global`
  只执行 `git pull` 不够。还需要执行 `./setup --host codex --refresh`，刷新 `~/.codex/skills/` 和 `~/.qros/`。

## 运行时布局

Repo-local 安装：

```text
.agents/skills/qros-*/
.qros/scripts/
.qros/tools/
.qros/templates/
.qros/docs/
.qros/install-manifest.json
```

User-global 安装：

```text
~/.codex/skills/qros-*/
~/.qros/scripts/
~/.qros/tools/
~/.qros/templates/
~/.qros/docs/
~/.qros/install-manifest.json
```

## 延伸阅读

- [安装说明](docs/experience/installation.md)
- [Codex 快速开始](docs/experience/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/experience/qros-research-session-usage.md)

## 常见问题

- 看不到技能：重新执行 `./setup --host codex --refresh`
- 感觉安装内容过旧：`repo-local` 用户先执行 `git pull`；`user-global` 用户重新执行 `./setup --host codex --refresh`
- 不确定安装是否正常：执行 `./setup --host codex --check`
