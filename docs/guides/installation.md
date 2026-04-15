# QROS Installation

## Supported Host

First version supports:

- `Codex`

## Recommended For Codex Users

如果你本身就是在 Codex 里工作，推荐像 `superpowers` 那样走“让 Codex 自己读取安装说明”的路径：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

这条路径更接近 Codex 的 skill-first 使用方式，也更适合第一次安装。

Install entry point:

```bash
git clone <QROS_REPO_URL> ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
./setup --host codex --mode user-global
```

This keeps the repo clone as the authored source while writing flat installed skills directly into Codex's native discovery path.

Then, from each research repo root, bootstrap a local runtime:

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

## Install Layout

What it writes:

- cloned repo source bundles under `~/workspace/quant-research-os/skills/`
- `~/.codex/skills/qros-*/`
- `~/.codex/qros/install-manifest.json`
- `<research-repo>/.qros/`

## Update

Update overwrites the cloned repo in place.

```bash
cd ~/workspace/quant-research-os
git pull
./setup --host codex --mode user-global
```

Codex will see the updated skills after `setup` refreshes `~/.codex/skills`.

如果你之前装的是旧版（例如还走 `~/.agents/skills` 或保留了旧 display 相关安装产物），这里也要完整重新跑一遍，然后**重启 Codex**，不要只 `git pull`。

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

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

The recommended user path is skill-first. The repo clone is the authored source; `user-global` makes Codex see the installed skills, and `repo-local` makes the current research repo get its own runtime.

For normal use, you do not need to start from `./.qros/bin/qros-session`.

Use `./.qros/bin/qros-session`, `./.qros/bin/qros-review`, and `./.qros/bin/qros-verify` mainly for:

- deterministic debugging
- manual recovery
- direct verification runs

## Troubleshooting

- `Codex` cannot see the skills: verify `~/.codex/skills/` contains `qros-*`
- Skill content looks stale: run `cd ~/workspace/quant-research-os && git pull && ./setup --host codex --mode user-global`，然后在当前 research repo 根再跑一次 `~/workspace/quant-research-os/setup --host codex --mode repo-local`，最后重启 Codex
- Need workflow guidance: open `docs/guides/quickstart-codex.md`
- Need the unified entry docs: open `docs/guides/qros-research-session-usage.md`
