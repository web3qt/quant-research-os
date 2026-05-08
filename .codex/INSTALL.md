# Installing QROS for Codex

Enable QROS skills in Codex via native skill discovery.

## Recommended Codex Flow

Start Codex from the active research repo root, then ask Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

Codex should install QROS globally, bootstrap the current research repo's `./.qros/`, then you should Restart Codex. After restart, begin with:

```text
qros-research-session 帮我研究这个想法：<your idea>
```

## Prerequisites

- Git

## Codex Execution Steps

1. Clone the QROS repository somewhere outside the runtime target:

```bash
git clone https://github.com/web3qt/quant-research-os.git ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
```

2. Build the installed Codex skill tree:

```bash
./setup --host codex --mode user-global
```

3. From the active research repo root, bootstrap a project-local runtime:

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

4. Restart Codex to discover the skills.

5. Start the workflow from the active research repo:

```text
qros-research-session 帮我研究这个想法：<your idea>
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

It auto-detects the active host and refreshes both the global install and the current repo's `./.qros/` runtime. For Codex this means `~/.codex/skills/`, `~/.codex/qros/`, and the active repo's `./.qros/`.

Run `qros-update` from the active research repo root so the refreshed repo-local runtime is written to that repo.

If update state looks stale, run `qros-update` from the active research repo root and then Restart Codex.

## Uninstalling

Optionally delete the installed skills, install metadata, project-local runtime, and repo clone:

```bash
rm -rf ~/.codex/skills/qros-*
rm -rf ~/.codex/qros
rm -rf ./.qros
rm -rf ~/workspace/quant-research-os
```
