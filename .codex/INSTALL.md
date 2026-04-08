# Installing QROS for Codex

Enable QROS skills in Codex via native skill discovery.

## Prerequisites

- Git

## Installation

1. Clone the QROS repository somewhere outside the runtime target:

```bash
git clone https://github.com/web3qt/quant-research-os.git ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
```

2. Build the flat installed skill tree:

```bash
./setup --host codex --mode user-global
```

3. Create the Codex discovery symlink:

```bash
mkdir -p ~/.agents/skills
ln -sfn ~/.qros/skills ~/.agents/skills/qros
```

4. Restart Codex to discover the skills.

## Verify

```bash
ls -la ~/.agents/skills/qros
```

You should see a symlink pointing to `~/.qros/skills`.

```bash
ls ~/.qros/skills
```

You should see flat installed bundles such as `qros-research-session`.

## How it works

- repo source of truth: cloned repo `skills/`
- installed flat skill tree: `~/.qros/skills/`
- Codex discovery entry: `~/.agents/skills/qros -> ~/.qros/skills`

## Updating

```bash
cd ~/workspace/quant-research-os
git pull
./setup --host codex --mode user-global
```

The symlink stays stable; rerunning `setup` refreshes the flattened installed tree.

## Uninstalling

```bash
rm ~/.agents/skills/qros
```

Optionally delete the installed runtime and repo clone:

```bash
rm -rf ~/.qros
rm -rf ~/workspace/quant-research-os
```
