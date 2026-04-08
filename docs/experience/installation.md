# QROS Installation

## Supported Host

First version supports:

- `Codex`

Install entry point:

```bash
git clone <QROS_REPO_URL> ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
./setup --host codex --mode user-global
```

This keeps the repo clone as the authored source while writing flat installed skills directly into Codex's native discovery path.

## Install Layout

What it writes:

- cloned repo source bundles under `~/workspace/quant-research-os/skills/`
- `~/.codex/skills/qros-*/`
- `~/.qros/`

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
test -d ~/.qros
```

It verifies:

- Codex can discover QROS skills through `~/.codex/skills/`
- the runtime assets exist under `~/.qros/`

## First Commands After Install

In Codex, start with:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

The recommended user path is still skill-first. The repo clone is the authored source; `setup` is what makes Codex see the installed skills.

## Troubleshooting

- `Codex` cannot see the skills: verify `~/.codex/skills/` contains `qros-*`
- Skill content looks stale: run `cd ~/workspace/quant-research-os && git pull && ./setup --host codex --mode user-global`，然后重启 Codex
- Need workflow guidance: open `docs/experience/quickstart-codex.md`
- Need the unified entry docs: open `docs/experience/qros-research-session-usage.md`
