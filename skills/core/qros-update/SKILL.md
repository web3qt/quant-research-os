---
name: qros-update
description: Update QROS to the latest published main and refresh the current repo-local runtime for the active Codex workspace
---

# QROS Update

Use this skill when the user asks to update QROS, refresh to the latest released version, sync the latest main branch, or rebuild the current repo's `./.qros/` runtime.

## Goal

Bring the user to the latest published `origin/main` version of QROS and leave the current working repo ready to use immediately.

## Required behavior

- Treat published `origin/main` as the source of truth.
- Refresh both surfaces:
  - global Codex install state under `~/.codex/skills/` and `~/.codex/qros/`
  - the current repo's local runtime under `./.qros/`
- Prefer the stable update entry instead of replaying ad hoc shell steps:

```bash
<source_repo>/runtime/bin/qros-update --cwd "$PWD"
```

## Self-heal expectations

This skill is for the agent, not the user. Do not surface common update errors immediately.

Before telling the user anything failed, automatically repair and retry these cases:

- missing `~/.codex/qros/install-manifest.json`
- stale or missing `source_repo_path`
- missing managed source repo clone
- dirty or drifted managed source repo
- outdated global skills
- missing or stale `./.qros/`
- failed install checks caused by stale install state

Default recovery order:

1. Read `~/.codex/qros/install-manifest.json` and use `source_repo_path` when it exists.
2. If manifest is missing or stale, try `~/workspace/quant-research-os`.
3. If the managed source repo still does not exist, clone the official QROS repo.
4. Update the managed source repo to `origin/main`.
5. Refresh `user-global`.
6. Refresh the current repo's `repo-local`.
7. Run install checks.

## When to stop and surface a blocker

Only stop and tell the user when there is no safe recovery path, for example:

- network access is unavailable
- Git remote access is unavailable
- filesystem permissions block writes
- the current working directory cannot safely host a repo-local runtime

## Success response

After success, keep the user-facing message short:

- confirm QROS was updated
- include the installed commit
- confirm the current repo's `./.qros/` runtime was refreshed

Do not dump the full repair log unless the user asks.
