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
git clone https://github.com/web3qt/quant-research-os.git ~/.codex/qros
```

2. Create the skills symlink:

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/qros/skills ~/.agents/skills/qros
```

3. Restart Codex.

## How It Works

Codex has native skill discovery. It scans `~/.agents/skills/` at startup, parses `SKILL.md` frontmatter, and loads matching skills on demand.

QROS skills become visible through a single symlink:

```text
~/.agents/skills/qros/ -> ~/.codex/qros/skills/
```

## Usage

Skills are the normal entrypoint:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-mandate-review`

If you need deterministic runtime debugging or manual recovery, use the repo-local wrappers:

```bash
~/.codex/qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
~/.codex/qros/bin/qros-review
```

## Updating

```bash
cd ~/.codex/qros
git pull
```

## Uninstalling

```bash
rm ~/.agents/skills/qros
```

Optionally remove the clone:

```bash
rm -rf ~/.codex/qros
```

## Troubleshooting

### Skills not showing up

1. Verify the symlink:

```bash
ls -la ~/.agents/skills/qros
```

2. Check the skill tree exists:

```bash
ls ~/.codex/qros/skills
```

3. Restart Codex. Skills are discovered at startup.
