# Quant Research OS

QROS is a stage-gated research workflow for Codex. It turns raw trading ideas into reviewable, reproducible research lineages instead of loose chat notes and ad-hoc experiments.

It is built for one core job: take an idea, qualify whether it deserves research budget, freeze a formal mandate through interaction, and keep the workflow auditable as it moves toward later stages.

## First-Wave Flow

Current unified flow:

- `idea_intake`
- `mandate`
- `mandate review`

The intended experience is skill-first:

- start from one entry point
- let the agent create or resume the lineage
- let the workflow drive the next required interaction
- keep formal artifacts on disk as the source of truth

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

- qualify the idea in `idea_intake`
- freeze the mandate interactively
- close the first wave at `mandate review`

## Install

QROS currently supports Codex installs in two modes:

- `repo-local`
  Copies skills into `.agents/skills/` and runtime assets into `.qros/`
- `user-global`
  Copies skills into `~/.codex/skills/` and runtime assets into `~/.qros/`

Common commands:

```bash
./setup --host codex --mode repo-local
./setup --host codex --mode user-global
./setup --host codex --mode auto
./setup --host codex --check
./setup --host codex --refresh
```

Use `repo-local` when the project should carry skills and runtime with it. Use `user-global` when you want one installation shared across projects on your machine.

## Start In Codex

Recommended prompts:

- `qros-research-session 帮我从这个想法开始：BTC 领动高流动性 ALT`
- `qros-research-session help`

## Update Existing Install

- `repo-local`
  Run `git pull` first. If you want the managed assets rewritten from the latest repo state, run `./setup --host codex --refresh`.
- `user-global`
  `git pull` alone is not enough. Rerun `./setup --host codex --refresh` to refresh `~/.codex/skills/` and `~/.qros/`.

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

## Learn More

Core docs:

- [installation.md](docs/experience/installation.md)
- [quickstart-codex.md](docs/experience/quickstart-codex.md)
- [qros-research-session-usage.md](docs/experience/qros-research-session-usage.md)

## Troubleshooting

- Skills not visible: rerun `./setup --host codex --refresh`
- Existing install feels out of date: `repo-local` users should `git pull` first; `user-global` users should rerun `./setup --host codex --refresh`
- Unsure whether install is healthy: run `./setup --host codex --check`
- Need the first-run walkthrough: open `docs/experience/quickstart-codex.md`
- Need the single-entry workflow details: open `docs/experience/qros-research-session-usage.md`
