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

2. Build the installed Codex skill tree:

```bash
./setup --host codex --mode user-global
```

3. Restart Codex to discover the skills.

4. For each research repo, bootstrap a project-local runtime from that repo's root:

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

## Verify

```bash
ls ~/.codex/skills | grep qros-
```

You should see installed skill directories such as `qros-research-session`.

```bash
test -f ~/.codex/qros/install-manifest.json
test -d ./.qros/bin
```

You should see a global install manifest under `~/.codex/qros/` and project-local runtime wrappers under `./.qros/bin/`.

## How it works

- repo source of truth: cloned repo `skills/`
- installed flat Codex skill tree: `~/.codex/skills/`
- global install metadata: `~/.codex/qros/install-manifest.json`
- project-local runtime helpers: `<research-repo>/.qros/`

## Updating

Inside Codex, the preferred path is:

```text
qros-update
```

It refreshes both the global install and the current repo's `./.qros/` runtime.

Manual fallback:

```bash
cd ~/workspace/quant-research-os
git pull
./setup --host codex --mode user-global
```

Then rerun project-local bootstrap inside each research repo that should pick up the updated runtime:

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

Rerunning `setup` refreshes the flat installed skill tree under `~/.codex/skills` and the local runtime under `./.qros/`.

## Uninstalling

Optionally delete the installed skills, install metadata, project-local runtime, and repo clone:

```bash
rm -rf ~/.codex/skills/qros-*
rm -rf ~/.codex/qros
rm -rf ./.qros
rm -rf ~/workspace/quant-research-os
```
