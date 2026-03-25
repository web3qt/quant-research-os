# Quant Research OS

Stage-gated research workflow assets for Codex, focused on turning trading ideas into reviewable, reproducible research lineages.

## Quick Start

1. Clone this repository.
2. Install QROS for Codex:

```bash
./setup --host codex --mode repo-local
```

3. Open Codex in this repo and start from the unified skill entry:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

4. Let the agent drive the first-wave flow:

- `idea_intake`
- `mandate`
- `mandate review`

## Install

QROS currently supports Codex installs in two modes:

- `repo-local`: copies skills into `.agents/skills/` and runtime assets into `.qros/`
- `user-global`: copies skills into `~/.codex/skills/` and runtime assets into `~/.qros/`

Common commands:

```bash
./setup --host codex --mode repo-local
./setup --host codex --mode user-global
./setup --host codex --mode auto
./setup --host codex --check
./setup --host codex --refresh
```

## First Workflow

The latest supported user flow is skill-first:

- install the repo with `./setup --host codex --mode repo-local`
- start from `qros-research-session`
- let the agent create or resume the lineage
- let the agent drive `idea_intake -> mandate -> mandate review`

Example prompts:

- `qros-research-session 帮我从这个想法开始：BTC 领动高流动性 ALT`
- `qros-research-session help`

See:

- [installation.md](docs/experience/installation.md)
- [quickstart-codex.md](docs/experience/quickstart-codex.md)
- [qros-research-session-usage.md](docs/experience/qros-research-session-usage.md)

## Install Modes

Use `repo-local` when the project should carry skills and runtime with it. Use `user-global` when you want one installation shared across projects on your machine.

## Runtime Layout

Repo-local install:

```text
.agents/skills/qros-*/
.qros/scripts/
.qros/tools/
.qros/templates/
.qros/docs/
.qros/install-manifest.json
```

User-global install:

```text
~/.codex/skills/qros-*/
~/.qros/scripts/
~/.qros/tools/
~/.qros/templates/
~/.qros/docs/
~/.qros/install-manifest.json
```

## Troubleshooting

- Skills not visible: rerun `./setup --host codex --refresh`
- Unsure whether install is healthy: run `./setup --host codex --check`
- Need the first-run walkthrough: open `docs/experience/quickstart-codex.md`
- Need the single-entry workflow details: open `docs/experience/qros-research-session-usage.md`
