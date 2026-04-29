# QROS 安装指南

## 支持的宿主

当前版本支持：

- `Codex`

## Codex 用户推荐路径

先在你要研究的 active research repo 根目录打开 Codex。

如果你本身就是在 Codex 里工作，推荐像 `superpowers` 那样走“让 Codex 自己读取安装说明”的路径：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

这条路径更接近 Codex 的 skill-first 使用方式，也更适合第一次安装。

Codex 会克隆或刷新 QROS 源码仓，把扁平化安装后的 skills 直接写入 Codex 原生 discovery path，并初始化当前 research repo 的本地 runtime。

首次安装或刷新 skills 后需要 Restart Codex。重启后，从同一个 active research repo 运行 `qros-research-session`。

## 安装布局

安装会写入：

- `~/workspace/quant-research-os/skills/` 下的源码版 source bundles
- `~/.codex/skills/qros-*/`
- `~/.codex/qros/install-manifest.json`
- `<research-repo>/.qros/`

当前 `<research-repo>/.qros/` 默认只保留：

- `bin/`
- `install-manifest.json`

它是项目本地 wrapper 层，不再复制整套 runtime 源码镜像。

## 更新

更新会就地刷新已克隆的 QROS 源码仓。

如果你已经在 Codex 里，推荐输入：

```text
qros-update
```

它会同时刷新全局安装和当前 repo 的 `./.qros/` runtime。

请从 active research repo 根目录运行 `qros-update`，这样它会刷新全局 skills，同时刷新该 repo 的 `./.qros/`。

如果你之前装的是旧版（例如还走 `~/.agents/skills` 或保留了旧 display 相关安装产物），直接运行 `qros-update`，然后 **Restart Codex**，不要只更新源码仓。

## 检查

最小检查命令：

```bash
ls ~/.codex/skills | grep qros-
test -f ~/.codex/qros/install-manifest.json
test -d ./.qros
```

如果需要检查当前 repo-local runtime 是否和 QROS source repo 对齐，可以从 active research repo 运行 `setup --check` 形式的安装检查：

```bash
<source_repo>/setup --host codex --mode repo-local --check
```

当 `install-manifest.json` 里的 `source_git_commit drift` 被检测到时，检查会提示当前安装记录的 revision 和 source repo 当前 revision。处理方式是从 active research repo 运行 `qros-update`，然后 Restart Codex。

它会验证：

- Codex 能通过 `~/.codex/skills/` 发现 QROS skills
- 安装元数据存在于 `~/.codex/qros/`
- runtime assets 存在于 `./.qros/`
- `source_git_commit` 没有相对 QROS source repo 发生 drift

## 安装后的第一批命令

在 Codex 里，从这些命令开始：

| 你想做什么 | 在 Codex 里输入 |
| --- | --- |
| 开始或继续一条研究线 | `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT` |
| 查看 QROS 使用帮助 | `qros-research-session help` |
| 查看当前研究进度 | `qros-progress` |
| 更新 QROS 到远程最新版本，并刷新当前 repo 的 `./.qros/` | `qros-update` |

推荐用户路径是 skill-first。源码克隆只是 authored source；`user-global` 让 Codex 看见已安装 skills，`repo-local` 让当前 research repo 拥有自己的 runtime。

正常使用时，不需要从 `./.qros/bin/qros-session` 开始。

`./.qros/bin/qros-session`、`./.qros/bin/qros-review` 和 `./.qros/bin/qros-verify` 主要用于：

- deterministic debugging
- 手工恢复
- 直接验证运行

## 排查问题

- `Codex` 看不到 skills：确认 `~/.codex/skills/` 包含 `qros-*`
- Skill 内容看起来过旧：从 active research repo 根目录运行 `qros-update`，然后重启 Codex
- 需要工作流指导：打开 `docs/guides/quickstart-codex.md`
- 需要统一入口说明：打开 `docs/guides/qros-research-session-usage.md`
