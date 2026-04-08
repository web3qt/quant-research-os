# QROS Installation

## Supported Host

First version supports:

- `Codex`

Install entry point:

```bash
git clone <QROS_REPO_URL> ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
./setup --host codex --mode user-global
mkdir -p ~/.agents/skills
ln -sfn ~/.qros/skills ~/.agents/skills/qros
```

This keeps the repo clone as the authored source while exposing the flattened installed skills through Codex's native discovery path.

## Install Layout

What it writes:

- cloned repo source bundles under `~/workspace/quant-research-os/skills/`
- `~/.qros/skills/`
- `~/.agents/skills/qros -> ~/.qros/skills`

## Update

Update overwrites the cloned repo in place.

```bash
cd ~/workspace/quant-research-os
git pull
./setup --host codex --mode user-global
```

Codex will see the updated skills after `setup` refreshes the flattened install tree.

## Check

Check is simple:

```bash
test -L ~/.agents/skills/qros
test -d ~/.qros/skills
```

It verifies:

- Codex can discover QROS skills through `~/.agents/skills/`
- the symlink points at the installed flat skill tree

## First Commands After Install

In Codex, start with:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

The recommended user path is still skill-first. The repo clone and symlink are only how Codex finds the skills.

## Troubleshooting

- `Codex` cannot see the skills: verify `~/.agents/skills/qros` points to `~/.qros/skills`
- Skill content looks stale: run `cd ~/workspace/quant-research-os && git pull && ./setup --host codex --mode user-global`
- Need workflow guidance: open `docs/experience/quickstart-codex.md`
- Need the unified entry docs: open `docs/experience/qros-research-session-usage.md`
