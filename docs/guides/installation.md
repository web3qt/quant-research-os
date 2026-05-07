# QROS 安装指南

<p align="center"><i>量化研究操作系统 -- 安装与配置指南</i></p>

---

<br>

## 支持的宿主

当前版本支持：

- `Codex`：完整支持
- `Claude Code`：完整支持，通过 `.claude-plugin/` 提供 skill discovery 和 adversarial reviewer agent

---

<br>

## Codex 用户推荐路径

先在你要研究的 active research repo 根目录打开 Codex。

如果你本身就是在 Codex 里工作，推荐像 `superpowers` 那样走"让 Codex 自己读取安装说明"的路径：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

> 这条路径更接近 Codex 的 skill-first 使用方式，也更适合第一次安装。

Codex 会克隆或刷新 QROS 源码仓，把扁平化安装后的 skills 直接写入 Codex 原生 discovery path，并初始化当前 research repo 的本地 runtime。

首次安装或刷新 skills 后需要 Restart Codex。重启后，从同一个 active research repo 运行 `qros-research-session`。

---

<br>

## Claude Code

Claude Code 通过 `.claude-plugin/` 目录提供完整的 QROS skill discovery 和 adversarial reviewer agent。

在 Claude Code 中可以先添加 marketplace：

```text
/plugin marketplace add web3qt/quant-research-os
```

然后安装 plugin：

```text
/plugin install qros@quant-research-os
```

> Plugin install 不等于 QROS workflow ready：当前 active research repo 仍然需要 `./.qros/bin` repo-local runtime 才能运行 `qros-session`、`qros-progress` 和 `qros-review`。

安装后，Claude Code 会以 plugin namespace 暴露 QROS skills，包括 13 个 stage-specific review skills 和独立的 adversarial reviewer agent（`.claude-plugin/agents/qros-reviewer.md`）。

**Review workflow 支持情况：**

- `.claude-plugin/agents/qros-reviewer.md` 定义了独立的 adversarial reviewer agent，确保 reviewer 与 author 身份隔离
- review skill template 已支持 host-agnostic 生成：`{{HOST_SPAWN_TOOL}}` 在 Codex 下为 `spawn_agent`，在 Claude Code 下为通过 `.claude-plugin/agents/qros-reviewer.md` 创建 task
- review skill 生成器支持 `--host claude-code`，将 skills 写入 `.claude-plugin/skills/`
- `qros-review-cycle prepare` 已支持 `--host claude-code`，自动生成对应的 reviewer handoff prompt 和 closer command

---

<br>

## Claude Code repo bootstrap

Claude Code 安装 plugin 之后，还需要初始化 active research repo 的 `./.qros` runtime 才能运行 `qros-session`、`qros-progress` 和 `qros-review`。

在 active research repo 根目录运行 repo bootstrap：

```bash
<source_repo>/setup --host claude-code --mode repo-local
```

这会写入：
- `./.qros/bin/*` (wrapper 脚本)
- `./.qros/install-manifest.json` (记录 `host = claude-code`)

Claude Code 的 global skills 存储在 `~/.claude/skills/`，global install manifest 在 `~/.claude/qros/install-manifest.json`。

<br>

### 更新

Claude Code 用户更新 QROS runtime：

```bash
<source_repo>/runtime/bin/qros-update --host claude-code --cwd "$PWD"
```

> 注意：如果 QROS skills 是通过 `/plugin install qros@quant-research-os` 安装的，plugin-managed skills 优先于 `~/.claude/skills/` 下的文件。需要同时运行：
> - `/plugin update qros@quant-research-os` (刷新 plugin-managed skills)
> - `qros-update --host claude-code` (刷新 repo-local `./.qros/` runtime)

<br>

### 检查

检查 Claude Code 安装状态：

```bash
ls ~/.claude/skills | grep qros-
test -f ~/.claude/qros/install-manifest.json
test -d ./.qros
```

或使用 setup 检查：

```bash
<source_repo>/setup --host claude-code --mode repo-local --check
```

---

<br>

## 安装布局

安装会写入：

- `~/workspace/quant-research-os/skills/` 下的源码版 source bundles
- Codex: `~/.codex/skills/qros-*/`，`~/.codex/qros/install-manifest.json`
- Claude Code: `.claude-plugin/skills/qros-*/`（repo-local plugin skills），`~/.claude/qros/install-manifest.json`
- `<research-repo>/.qros/`

当前 `<research-repo>/.qros/` 默认只保留：

- `bin/`
- `install-manifest.json`

> 它是项目本地 wrapper 层，不再复制整套 runtime 源码镜像。

`install-manifest.json` 是 repo-local runtime 的来源证明。关键字段包括：

| 字段 | 含义 |
| --- | --- |
| `source_repo_path` | 安装时使用的 QROS source checkout 绝对路径 |
| `source_git_commit` | 安装时 source checkout 的 Git commit |
| `source_git_dirty` | 安装时 source checkout 是否有未提交改动 |
| `source_git_status_short` | 安装时 `git status --short` 的逐行快照 |
| `python_executable` | 安装时运行 setup 的 Python interpreter 绝对路径 |
| `python_version` | 安装时运行 setup 的 Python 版本 |

当前阶段里，`python_executable` 和 `python_version` 只作为审计 provenance 记录；wrapper 优先使用安装时 interpreter 的执行策略由后续 Python wrapper 阶段处理。

### wrapper provenance guard

Repo-local `./.qros/bin/qros-*` wrappers 会在运行 session、review、validation、progress 或 diagnostics 脚本前读取 `./.qros/install-manifest.json`，并检查来源约束：

- `source_repo_path` 必须指向仍然存在且包含 `runtime/scripts` 的 QROS source checkout
- 如果设置了 `QROS_EXPECTED_SOURCE_REPO=/abs/path/to/quant-research-os`，manifest 里的 `source_repo_path` 必须与它解析到同一个 checkout
- 如果 manifest 记录 `source_git_dirty: false`，当前 source checkout 不能变成 dirty state

普通 wrapper 遇到这些 drift 会停止并打印 `QROS source repo path drift detected:` 或 `QROS source_git_dirty drift detected:`。恢复命令是 `qros-update`；它会继续进入 recovery diagnostics，便于从 active research repo 刷新 repo-local runtime。

`QROS_ALLOW_PROVENANCE_DRIFT=1` 只用于 emergency/manual recovery。它会让 wrapper 打印显式 override 警告后继续，不应作为正常研究流程使用。

---

<br>

## 更新

更新会就地刷新已克隆的 QROS 源码仓。

如果你已经在 Codex 里，推荐输入：

```text
qros-update
```

它会同时刷新全局安装和当前 repo 的 `./.qros/` runtime。

请从 active research repo 根目录运行 `qros-update`，这样它会刷新全局 skills，同时刷新该 repo 的 `./.qros/`。

> 如果你之前装的是旧版（例如还走 `~/.agents/skills` 或保留了旧 display 相关安装产物），直接运行 `qros-update`，然后 **Restart Codex**，不要只更新源码仓。

---

<br>

## 检查

最小检查命令（Codex）：

```bash
ls ~/.codex/skills | grep qros-
test -f ~/.codex/qros/install-manifest.json
test -d ./.qros
```

最小检查命令（Claude Code）：

```bash
ls ~/.claude/skills | grep qros-
test -f ~/.claude/qros/install-manifest.json
test -d ./.qros
```

如果需要检查当前 repo-local runtime 是否和 QROS source repo 对齐，可以从 active research repo 运行 `setup --check` 形式的安装检查：

```bash
<source_repo>/setup --host codex --mode repo-local --check
```

> 当 `install-manifest.json` 里的 `source_repo_path drift`、`source_git_commit drift` 或 `source_git_dirty drift` 被检测到时，检查会提示当前安装记录的 source path、revision 或 dirty-state 与 source repo 当前状态的差异。处理方式是从 active research repo 运行 `qros-update`，必要时先 commit 或 stash QROS source checkout 的本地改动，然后 Restart Codex。

它会验证：

- Codex 能通过 `~/.codex/skills/` 发现 QROS skills
- 安装元数据存在于 `~/.codex/qros/`
- runtime assets 存在于 `./.qros/`
- `source_repo_path` 指向当前检查的 QROS source repo
- `source_git_commit` 没有相对 QROS source repo 发生 drift
- `source_git_dirty` 没有从安装时的 clean state 漂移到当前 dirty state

---

<br>

## 安装后的第一批命令

在 Codex 或 Claude Code 里，从这些命令开始：

| 你想做什么 | 在 Codex 里输入 |
| --- | --- |
| 开始或继续一条研究线 | `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT` |
| 查看 QROS 使用帮助 | `qros-research-session help` |
| 查看当前研究进度 | `qros-progress` |
| 更新 QROS 到远程最新版本，并刷新当前 repo 的 `./.qros/` | `qros-update` |

> 推荐用户路径是 skill-first。源码克隆只是 authored source；`user-global` 让 Codex 看见已安装 skills，`repo-local` 让当前 research repo 拥有自己的 runtime。

正常使用时，不需要从 `./.qros/bin/qros-session` 开始。

`./.qros/bin/qros-session`、`./.qros/bin/qros-review` 和 `./.qros/bin/qros-verify` 主要用于：

- deterministic debugging
- 手工恢复
- 直接验证运行

---

<br>

## 排查问题

- `Codex` 看不到 skills：确认 `~/.codex/skills/` 包含 `qros-*`
- `Claude Code` 看不到 skills：确认 `.claude-plugin/skills/` 包含 `qros-*` 或 plugin 已安装
- Skill 内容看起来过旧：从 active research repo 根目录运行 `qros-update`，然后重启 host
- 需要工作流指导：打开 `docs/guides/quickstart-codex.md`（Codex）或确认 `.claude-plugin/` 已就位（Claude Code）
- 需要统一入口说明：打开 `docs/guides/qros-research-session-usage.md`
