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

2. Build the installed Codex skill tree and runtime:

```bash
./setup --host codex --mode user-global
```

3. Restart Codex to discover the skills.

## Verify

```bash
ls ~/.codex/skills | grep qros-
```

You should see installed skill directories such as `qros-research-session`.

```bash
ls ~/.qros/bin
```

You should see runtime wrappers such as `qros-session`.

## How it works

- repo source of truth: cloned repo `skills/`
- installed flat Codex skill tree: `~/.codex/skills/`
- installed runtime helpers: `~/.qros/`

## Updating

```bash
cd ~/workspace/quant-research-os
git pull
./setup --host codex --mode user-global
```

Rerunning `setup` refreshes the flat installed skill tree under `~/.codex/skills`.

## Uninstalling

Optionally delete the installed skills, runtime, and repo clone:

```bash
rm -rf ~/.codex/skills/qros-*
rm -rf ~/.qros
rm -rf ~/workspace/quant-research-os
```
