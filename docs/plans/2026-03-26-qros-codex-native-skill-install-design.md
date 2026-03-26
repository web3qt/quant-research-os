# QROS Codex Native Skill Install Design

**Date:** 2026-03-26  
**Status:** Approved for replacement direction  
**Scope:** `Codex-only`, `clone + symlink install`, `skill-first entry`, `no pipx distribution`

## Goal

把 QROS 的 Codex 安装与使用模型收敛到更接近 `obra/superpowers` 的轻量方案：

- QROS 继续作为独立工具仓存在
- 用户通过 `git clone` 安装工具仓
- 用户通过一个 symlink 让 Codex 发现 QROS skills
- 用户日常仍以 `qros-*` skill 名称作为第一入口
- 研究产物写当前研究仓
- 不再引入 `pipx install qros`、包级全局 CLI、`~/.qros` runtime 镜像这类重分发层

这次改动的目标不是“把 QROS 产品化成通用 Python CLI 包”，而是“顺着 Codex 已有的原生 skill 发现机制，把安装和更新压到最轻”。

## Why Replace The Heavier Direction

前一版方向的问题已经很清楚：

- `pipx` / `uv tool` 安装链路太重
- 为了支撑全局 CLI，不得不补 `manifest`、`doctor`、资源打包、运行时定位、cwd 协议
- `qros --help` 都可能被 runtime 依赖拖累
- `--cwd "$PWD"` 这种抽象会把“研究仓根目录”问题重新发明一遍

这些问题本质上都来自同一个源头：

- 我们在为 Codex skill 系统额外建一套分发和运行时框架

而 `superpowers` 的做法证明：

- 对 Codex 来说，很多时候并不需要这层额外框架

## Reference Pattern From `superpowers`

参考 `obra/superpowers`，Codex 安装只做两件事：

1. clone 仓库到用户目录
2. 把 skill 目录 symlink 到 Codex 发现路径

典型路径：

```bash
git clone https://github.com/obra/superpowers.git ~/.codex/superpowers
mkdir -p ~/.agents/skills
ln -s ~/.codex/superpowers/skills ~/.agents/skills/superpowers
```

然后：

- Codex 启动时扫描 `~/.agents/skills/`
- skills 通过 symlink 被发现
- 更新只需在 clone 下 `git pull`

这条路径的关键优势是：

- 安装极轻
- 更新极轻
- 不需要重新发明技能注册协议
- 不需要把工具仓打成另一种分发产物

## Recommended QROS Model

QROS 采用同类模型：

### Install

```bash
git clone <QROS_REPO_URL> ~/.codex/qros
mkdir -p ~/.agents/skills
ln -s ~/.codex/qros/skills ~/.agents/skills/qros
```

或等价地把仓库直接 clone 到别的固定路径，再把 `skills/` 链进 `~/.agents/skills/qros`。

### Update

```bash
cd ~/.codex/qros
git pull
```

因为 skills 通过 symlink 暴露，更新会自然生效，不需要 `refresh` 安装器。

### Usage

用户在任意研究仓里打开 Codex，直接使用：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
```

## Install Layout

推荐布局：

```text
~/.codex/qros/
  skills/
    qros-research-session/
    qros-mandate-review/
    ...
  scripts/
  tools/
  docs/
  templates/

~/.agents/skills/
  qros -> ~/.codex/qros/skills
```

重点：

- `~/.codex/qros/` 是 QROS 工具仓本体
- `~/.agents/skills/qros` 只是一个 symlink 入口
- 不再复制 skills 到另一个安装目录
- 不再复制 runtime 到 `~/.qros`

## Skill Discovery Model

QROS 不需要额外发明 skill 注册协议。

只要满足：

- `skills/` 下是 Codex 可发现的 skill 目录
- 每个 skill 都有 `SKILL.md`
- `~/.agents/skills/qros` 指向它们

Codex 就能按原生机制发现并加载。

## Runtime Model

保留“skill-first，runtime-second”的体验：

- 用户入口仍是 skill 名称
- 运行时命令可以是 repo 内稳定脚本
- 但这些命令不需要伪装成一个全局包安装的 `qros` CLI

建议两种可接受形式：

### Option A: Skill 调用 repo 内绝对路径脚本

例如：

```bash
python ~/.codex/qros/scripts/run_research_session.py --outputs-root outputs ...
```

优点：

- 最直接
- 不需要再造 wrapper

缺点：

- skill 文本会显式暴露绝对路径

### Option B: 仓库内提供极薄 wrapper

例如在 `~/.codex/qros/bin/` 下提供：

- `qros-session`
- `qros-review`

skill 调用：

```bash
~/.codex/qros/bin/qros-session --cwd "$PWD" ...
```

优点：

- skill 文本更整洁
- 入口名称稳定

缺点：

- 仍然需要一个很薄的执行层

推荐 **Option B**，但这个 wrapper 必须保持极薄，不得再次膨胀成完整全局 CLI 产品。

## What To Remove

在这个新方向里，前一版重方案中的这些概念都应下线或降级：

- `pipx install qros`
- `uv tool install qros`
- `project.scripts.qros`
- `qros codex install`
- `qros codex refresh`
- `qros doctor`
- `~/.qros/manifest.json` 作为主安装状态
- 包资源分发作为主路径

如果确实保留，也只能作为开发辅助，而不是用户主路径。

## Docs Model

文档应该完全按 `superpowers` 风格改写：

- 顶层 README 给出 clone + symlink 安装
- 新增 `.codex/INSTALL.md`
- 增加 `docs/experience/installation-codex-native.md` 或直接重写现有 installation 文档
- 明确说明：
  - Codex 扫描 `~/.agents/skills/`
  - `~/.agents/skills/qros` 只是一个 symlink
  - 更新只需 `git pull`

## Testing Strategy

测试也应从“包安装器”转成“repo + symlink”模型：

### 1. Skill Tree Shape

- `skills/` 目录存在
- 所有 `qros-*` skills 有 `SKILL.md`

### 2. Install Script / Manual Install Helper

如果提供一个轻量 install helper，应测试：

- clone 目标路径检查
- symlink 创建
- 已存在 symlink 的幂等更新

### 3. Runtime Entry Stability

- skills 中引用的 repo 内路径或 wrapper 路径稳定
- 从研究仓执行时产物写到当前仓，而不是工具仓

## Non-Goals

这次不做：

- Python 包分发
- `pipx` / `uv tool` 安装
- 全局 `qros` 命令作为主入口
- package data 资源分发体系
- `~/.qros` 完整 runtime 镜像

## Success Criteria

新方案完成后，应满足：

- 用户只需 clone 一次 QROS 仓库
- 用户只需创建一个 symlink 就能让 Codex 发现 skills
- 更新只需 `git pull`
- 用户日常始终在研究仓里使用 `qros-*` skills
- 不再需要维护一套厚重的全局 CLI 安装层
