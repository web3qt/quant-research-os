# Installing QROS for Codex

Enable QROS skills in Codex via native skill discovery. Just clone and symlink.

## Prerequisites

- Git

## Installation

1. Clone the QROS repository:

```bash
git clone https://github.com/web3qt/quant-research-os.git ~/.codex/qros
```

2. Create the skills symlink:

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/qros/skills ~/.agents/skills/qros
```

3. Restart Codex to discover the skills.

## Verify

```bash
ls -la ~/.agents/skills/qros
```

You should see a symlink pointing to `~/.codex/qros/skills`.

## Updating

```bash
cd ~/.codex/qros
git pull
```

Skills update instantly through the symlink.

## Uninstalling

```bash
rm ~/.agents/skills/qros
```

Optionally delete the clone:

```bash
rm -rf ~/.codex/qros
```
