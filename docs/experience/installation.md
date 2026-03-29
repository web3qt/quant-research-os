# QROS Installation

## Supported Host

First version supports:

- `Codex`

Install entry point:

```bash
git clone <QROS_REPO_URL> ~/.qros
mkdir -p ~/.agents/skills
ln -s ~/.qros/skills ~/.agents/skills/qros
```

This keeps QROS as a cloned repo while exposing skills through Codex's native discovery path.

## Install Layout

What it writes:

- `~/.qros/skills/`
- `~/.agents/skills/qros -> ~/.qros/skills`

## Update

Update overwrites the cloned repo in place.

```bash
cd ~/.qros
git pull
```

Codex will immediately see the updated skills because `~/.agents/skills/qros` points at the repo skill tree.

## Check

Check is simple:

```bash
test -L ~/.agents/skills/qros
test -d ~/.qros/skills
```

It verifies:

- Codex can discover QROS skills through `~/.agents/skills/`
- the symlink points at the repo skill tree

## First Commands After Install

In Codex, start with:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

The recommended user path is still skill-first. The repo clone and symlink are only how Codex finds the skills.

## Troubleshooting

- `Codex` cannot see the skills: verify `~/.agents/skills/qros` points to `~/.qros/skills`
- Skill content looks stale: run `cd ~/.qros && git pull`
- Need workflow guidance: open `docs/experience/quickstart-codex.md`
- Need the unified entry docs: open `docs/experience/qros-research-session-usage.md`
