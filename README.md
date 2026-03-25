# 🛠 Quant Research OS | 量化研究操作系统

English | 中文

QROS is a stage-gated research workflow for Codex. It turns raw trading ideas into reviewable, reproducible, and auditable research lineages through interactive mandate freezing, formal artifacts, and workflow gates.

QROS 是一个面向 Codex 的阶段式研究工作流。它通过交互式 mandate 冻结、正式产物和流程门禁，把原始交易想法转成可审查、可复现、可追溯的研究线。

## Why QROS | 为什么使用 QROS

Most research ideas start as loose chat. Serious research does not. QROS exists to move a research team from vague idea discussion to explicit scope, frozen contracts, on-disk artifacts, and reviewable stage progression.

大多数研究想法最开始只是聊天里的模糊表达，正式研究不能停留在这里。QROS 的目标是把研究流程从“口头讨论”推进到“明确边界、冻结合同、正式落盘、阶段可审查”。

## First-Wave Flow | 第一阶段工作流

Current unified flow:

- `idea_intake`
- `mandate`
- `mandate review`

当前统一入口覆盖：

- `idea_intake`
- `mandate`
- `mandate review`

## Core Experience | 核心体验

- Start from one skill entry
- Let the agent qualify whether the idea deserves research budget
- Freeze mandate content interactively instead of silently generating documents
- Keep formal artifacts on disk as the source of truth

- 从一个统一 skill 入口开始
- 让 agent 先判断这个想法是否值得进入正式研究
- 通过交互式流程冻结 mandate，而不是静默生成文档
- 让正式产物落盘并成为唯一事实来源

## Quick Start | 快速开始

Install QROS for Codex inside this repository:

在当前仓库里安装 QROS：

```bash
./setup --host codex --mode repo-local
```

Then open Codex in this repo and start with:

然后在这个仓库里打开 Codex，从下面的统一入口开始：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

## Install Modes | 安装模式

- `repo-local`
  Skills are written into `.agents/skills/` and runtime assets into `.qros/`
- `user-global`
  Skills are written into `~/.codex/skills/` and runtime assets into `~/.qros/`

- `repo-local`
  技能写入 `.agents/skills/`，运行时资产写入 `.qros/`
- `user-global`
  技能写入 `~/.codex/skills/`，运行时资产写入 `~/.qros/`

Common commands:

常用命令：

```bash
./setup --host codex --mode repo-local
./setup --host codex --mode user-global
./setup --host codex --mode auto
./setup --host codex --check
./setup --host codex --refresh
```

## Update Existing Install | 已安装用户如何更新

- `repo-local`
  Run `git pull` first. If you want managed assets rewritten from the latest repo state, run `./setup --host codex --refresh`.
- `user-global`
  `git pull` alone is not enough. Run `./setup --host codex --refresh` to refresh `~/.codex/skills/` and `~/.qros/`.

- `repo-local`
  先执行 `git pull`。如果你希望受管资产按最新仓库状态重写，再执行 `./setup --host codex --refresh`。
- `user-global`
  只执行 `git pull` 不够。还需要执行 `./setup --host codex --refresh`，刷新 `~/.codex/skills/` 和 `~/.qros/`。

## Runtime Layout | 运行时布局

Repo-local install:

```text
.agents/skills/qros-*/
.qros/scripts/
.qros/tools/
.qros/templates/
.qros/docs/
.qros/install-manifest.json
```

User-global install:

```text
~/.codex/skills/qros-*/
~/.qros/scripts/
~/.qros/tools/
~/.qros/templates/
~/.qros/docs/
~/.qros/install-manifest.json
```

## Learn More | 延伸阅读

- [Installation](docs/experience/installation.md)
- [Quickstart For Codex](docs/experience/quickstart-codex.md)
- [QROS Research Session Usage](docs/experience/qros-research-session-usage.md)

- [安装说明](docs/experience/installation.md)
- [Codex 快速开始](docs/experience/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/experience/qros-research-session-usage.md)

## Troubleshooting | 常见问题

- Skills not visible: rerun `./setup --host codex --refresh`
- Existing install feels out of date: `repo-local` users should `git pull` first; `user-global` users should rerun `./setup --host codex --refresh`
- Unsure whether install is healthy: run `./setup --host codex --check`

- 看不到技能：重新执行 `./setup --host codex --refresh`
- 感觉安装内容过旧：`repo-local` 用户先执行 `git pull`；`user-global` 用户重新执行 `./setup --host codex --refresh`
- 不确定安装是否正常：执行 `./setup --host codex --check`
