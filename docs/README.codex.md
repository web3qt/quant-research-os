# QROS for Codex

Guide for using QROS with OpenAI Codex via native skill discovery.

## Quick Install

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

## Manual Installation

### Prerequisites

- OpenAI Codex CLI
- Git

### Steps

1. Clone the repo:

```bash
git clone https://github.com/web3qt/quant-research-os.git ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
```

2. Build the installed Codex skill tree and runtime:

```bash
./setup --host codex --mode user-global
```

3. Restart Codex.

## How It Works

Codex has native skill discovery. It scans `~/.codex/skills/` at startup, parses `SKILL.md` frontmatter, and loads matching skills on demand.

QROS keeps its authored source bundles in the cloned repo under `skills/`, then `./setup` flattens them into the installed Codex tree under `~/.codex/skills/`.

QROS skills become visible as flat installed directories:

```text
~/.codex/skills/qros-research-session/
~/.codex/skills/qros-mandate-review/
...
```

## Usage

Skills are the normal entrypoint:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-mandate-review`

If you need deterministic runtime debugging or manual recovery, use the repo-local wrappers:

```bash
~/.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
~/.qros/bin/qros-review
```

## Updating

```bash
cd ~/workspace/quant-research-os
git pull
./setup --host codex --mode user-global
```

If you installed an older QROS contract before the move to direct `~/.codex/skills` installs, rerun the same command and restart Codex so stale local skill directories are replaced.

## Uninstalling

```bash
rm -rf ~/.codex/skills/qros-*
```

Optionally remove the runtime and clone:

```bash
rm -rf ~/.qros
rm -rf ~/workspace/quant-research-os
```

## Troubleshooting

### Skills not showing up

1. Verify the installed Codex skills:

```bash
ls ~/.codex/skills | grep qros-
```

2. Check the runtime tree exists:

```bash
ls ~/.qros/bin
```

3. If you just updated the repo, rerun:

```bash
cd ~/workspace/quant-research-os
./setup --host codex --mode user-global
```

4. Restart Codex. Skills are discovered at startup.
