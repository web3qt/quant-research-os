# Installing QROS for Claude Code

Enable QROS skills in Claude Code via `.claude-plugin/` skill discovery and adversarial reviewer agent.

## Recommended Claude Code Flow

Start Claude Code from the active research repo root, then ask Claude Code:

```
请阅读并按照 https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.claude/INSTALL.md 的指示安装 QROS
```

Claude Code should install QROS globally, bootstrap the current research repo's `./.qros/`, then you should restart Claude Code. After restart, begin with:

```
qros-research-session 帮我研究这个想法：<your idea>
```

## Prerequisites

- Git

## Claude Code Execution Steps

1. Clone the QROS repository somewhere outside the runtime target:

```bash
git clone https://github.com/web3qt/quant-research-os.git ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
```

2. Build the installed Claude Code skill tree:

```bash
./setup --host claude-code --mode user-global
```

3. From the active research repo root, bootstrap a project-local runtime:

```bash
~/workspace/quant-research-os/setup --host claude-code --mode repo-local
```

4. Restart Claude Code to discover the skills.

5. Start the workflow from the active research repo:

```
qros-research-session 帮我研究这个想法：<your idea>
```

## Verify

```bash
ls ~/.claude/skills | grep qros-
```

You should see installed skill directories such as `qros-research-session`.

```bash
test -f ~/.claude/qros/install-manifest.json
test -d ./.qros/bin
```

You should see a global install manifest under `~/.claude/qros/` and project-local runtime wrappers under `./.qros/bin/`.

## How it works

- repo source of truth: cloned repo `skills/`
- installed flat Claude Code skill tree: `~/.claude/skills/`
- global install metadata: `~/.claude/qros/install-manifest.json`
- project-local runtime helpers: `<research-repo>/.qros/`

## Updating

Inside Claude Code, the preferred path is:

```
qros-update
```

It refreshes both the global install and the current repo's `./.qros/` runtime.

Run `qros-update` from the active research repo root so the refreshed repo-local runtime is written to that repo.

If update state looks stale, run `qros-update` from the active research repo root and then restart Claude Code.

## Uninstalling

Optionally delete the installed skills, install metadata, project-local runtime, and repo clone:

```bash
rm -rf ~/.claude/skills/qros-*
rm -rf ~/.claude/qros
rm -rf ./.qros
rm -rf ~/workspace/quant-research-os
```
