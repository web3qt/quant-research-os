# QROS Installation

## Supported Host

First version supports:

- `Codex`

Install entry point:

```bash
./setup --host codex --mode repo-local
./setup --host codex --mode user-global
```

## Repo-Local Install

Use this when QROS should live inside the current project.

```bash
./setup --host codex --mode repo-local
```

What it writes:

- `.agents/skills/qros-*`
- `.qros/scripts/`
- `.qros/tools/`
- `.qros/templates/`
- `.qros/docs/`
- `.qros/install-manifest.json`

## User-Global Install

Use this when you want one installation shared across local projects.

```bash
./setup --host codex --mode user-global
```

What it writes:

- `~/.codex/skills/qros-*`
- `~/.qros/scripts/`
- `~/.qros/tools/`
- `~/.qros/templates/`
- `~/.qros/docs/`
- `~/.qros/install-manifest.json`

## Auto Mode

`auto` resolves to:

- `repo-local` when the current directory already looks like a project with `.agents/`
- otherwise `user-global`

```bash
./setup --host codex --mode auto
```

## Refresh

Refresh overwrites the managed QROS assets from the current source repo.

```bash
./setup --host codex --refresh
```

## Check

Check validates the install without writing files.

```bash
./setup --host codex --check
```

It verifies:

- expected `qros-*` skills exist
- runtime assets exist
- `install-manifest.json` exists
- manifest contains the expected install metadata

## First Commands After Install

In Codex, start with:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

The recommended user path is skill-first. The runtime scripts still exist, but they are internal plumbing and manual recovery tools, not the main workflow.

## Troubleshooting

- `--check` reports missing manifest: run `./setup --host codex --mode repo-local` or `user-global`
- Skill content looks stale: run `./setup --host codex --refresh`
- Need workflow guidance: open `docs/experience/quickstart-codex.md`
- Need the unified entry docs: open `docs/experience/qros-research-session-usage.md`
