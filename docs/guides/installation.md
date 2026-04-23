# QROS Installation

## Supported Host

First version supports:

- `Codex`

## Recommended For Codex Users

先在你要研究的 active research repo 根目录打开 Codex。

如果你本身就是在 Codex 里工作，推荐像 `superpowers` 那样走“让 Codex 自己读取安装说明”的路径：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

这条路径更接近 Codex 的 skill-first 使用方式，也更适合第一次安装。

Codex will clone or refresh the QROS source repo, write flat installed skills directly into Codex's native discovery path, and bootstrap the current research repo's local runtime.

首次安装或刷新 skills 后需要 Restart Codex。重启后，从同一个 active research repo 运行 `qros-research-session`。

## Install Layout

What it writes:

- cloned repo source bundles under `~/workspace/quant-research-os/skills/`
- `~/.codex/skills/qros-*/`
- `~/.codex/qros/install-manifest.json`
- `<research-repo>/.qros/`

当前 `<research-repo>/.qros/` 默认只保留：

- `bin/`
- `install-manifest.json`

它是项目本地 wrapper 层，不再复制整套 runtime 源码镜像。

## Update

Update overwrites the cloned repo in place.

If you are already inside Codex, the preferred path is:

```text
qros-update
```

It refreshes both the global install and the current repo's `./.qros/` runtime.

请从 active research repo 根目录运行 `qros-update`，这样它会刷新全局 skills，同时刷新该 repo 的 `./.qros/`。

如果你之前装的是旧版（例如还走 `~/.agents/skills` 或保留了旧 display 相关安装产物），直接运行 `qros-update`，然后 **Restart Codex**，不要只更新源码仓。

## Check

Check is simple:

```bash
ls ~/.codex/skills | grep qros-
test -f ~/.codex/qros/install-manifest.json
test -d ./.qros
```

It verifies:

- Codex can discover QROS skills through `~/.codex/skills/`
- the install metadata exists under `~/.codex/qros/`
- the runtime assets exist under `./.qros/`

## First Commands After Install

In Codex, start with:

| 你想做什么 | 在 Codex 里输入 |
| --- | --- |
| 开始或继续一条研究线 | `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT` |
| 查看 QROS 使用帮助 | `qros-research-session help` |
| 查看当前研究进度 | `qros-progress` |
| 更新 QROS 到远程最新版本，并刷新当前 repo 的 `./.qros/` | `qros-update` |

The recommended user path is skill-first. The repo clone is the authored source; `user-global` makes Codex see the installed skills, and `repo-local` makes the current research repo get its own runtime.

For normal use, you do not need to start from `./.qros/bin/qros-session`.

Use `./.qros/bin/qros-session`, `./.qros/bin/qros-review`, and `./.qros/bin/qros-verify` mainly for:

- deterministic debugging
- manual recovery
- direct verification runs

## Troubleshooting

- `Codex` cannot see the skills: verify `~/.codex/skills/` contains `qros-*`
- Skill content looks stale: run `qros-update` from the active research repo root, then Restart Codex
- Need workflow guidance: open `docs/guides/quickstart-codex.md`
- Need the unified entry docs: open `docs/guides/qros-research-session-usage.md`
