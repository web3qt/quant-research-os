# 🛠 Quant Research OS | QROS

English | [中文](README.md)

QROS is a stage-gated research workflow for Codex. It turns raw trading ideas into reviewable, reproducible, and auditable research lineages through interactive mandate freezing, formal artifacts, and workflow gates.

## Why QROS

Most research ideas start as loose chat. Serious research does not. QROS exists to move a research team from vague idea discussion to explicit scope, frozen contracts, on-disk artifacts, and reviewable stage progression.

## First-Wave Flow

Current unified flow:

- `idea_intake`
- `mandate`
- `mandate review`
- `data_ready`
- `data_ready review`
- `signal_ready`
- `signal_ready review`

The intended experience is skill-first:

- start from one skill entry
- let the agent create or resume the lineage
- let the workflow drive the next required interaction
- keep formal artifacts on disk as the source of truth

## Quick Start

Install QROS for Codex inside this repository:

```bash
./setup --host codex --mode repo-local
```

Then open Codex in this repo and start with:

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

## Install Modes

- `repo-local`
  Skills are written into `.agents/skills/` and runtime assets into `.qros/`
- `user-global`
  Skills are written into `~/.codex/skills/` and runtime assets into `~/.qros/`

Common commands:

```bash
./setup --host codex --mode repo-local
./setup --host codex --mode user-global
./setup --host codex --mode auto
./setup --host codex --check
./setup --host codex --refresh
```

## Update Existing Install

- `repo-local`
  Run `git pull` first. If you want managed assets rewritten from the latest repo state, run `./setup --host codex --refresh`.
- `user-global`
  `git pull` alone is not enough. Run `./setup --host codex --refresh` to refresh `~/.codex/skills/` and `~/.qros/`.

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

- [Installation](docs/experience/installation.md)
- [Quickstart For Codex](docs/experience/quickstart-codex.md)
- [QROS Research Session Usage](docs/experience/qros-research-session-usage.md)

## Troubleshooting

- Skills not visible: rerun `./setup --host codex --refresh`
- Existing install feels out of date: `repo-local` users should `git pull` first; `user-global` users should rerun `./setup --host codex --refresh`
- Unsure whether install is healthy: run `./setup --host codex --check`
