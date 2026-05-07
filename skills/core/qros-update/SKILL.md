---
name: qros-update
description: Update QROS to the latest published main and refresh the current repo-local runtime for the active host workspace
---

# QROS Update

Use this skill when the user asks to update QROS, refresh to the latest released version, sync the latest main branch, or rebuild the current repo's `./.qros/` runtime.

Run this skill from the active research repo root. The current working directory determines which repo-local `./.qros/` runtime is refreshed.

## Goal

Bring the user to the latest published `origin/main` version of QROS and leave the current working repo ready to use immediately.

## Host awareness

This skill is host-aware. By default `qros-update` uses `--host auto` and resolves the host in this order:

1. explicit `--host codex` or `--host claude-code` from the current wrapper
2. `QROS_HOST`
3. current agent environment markers (`CLAUDE_CODE` / `CLAUDECODE_*` or `CODEX_*`)
4. the current repo's `./.qros/install-manifest.json.host`
5. fallback to Codex

Compatibility note: old repo-local `qros-update` wrappers always passed `--host codex` as their default. The latest updater treats that unmarked legacy default as `auto`, so a Claude Code repo with `QROS_HOST=claude-code`, Claude Code environment markers, or `./.qros/install-manifest.json.host = claude-code` still refreshes the Claude Code surface once the source checkout is on the latest updater.

The update behavior differs by resolved host:

- **Codex** (`--host codex`): Refreshes `~/.codex/skills/` and the current repo's `./.qros/` runtime.
- **Claude Code** (`--host claude-code`): Refreshes `~/.claude/skills/` and the current repo's `./.qros/` runtime.

Note: if QROS skills were installed via `/plugin install qros@quant-research-os`, the plugin-managed skill copy takes precedence over `~/.claude/skills/`. Run `/plugin update qros@quant-research-os` to refresh plugin-managed skills, then run this update for repo-local runtime refresh.

## Required behavior

- Treat published `origin/main` as the source of truth.
- Refresh both surfaces:
  - global install state (Codex: `~/.codex/skills/` and `~/.codex/qros/`; Claude Code: `~/.claude/skills/` and `~/.claude/qros/`)
  - the current repo's local runtime under `./.qros/`
- Prefer the stable update entry instead of replaying ad hoc shell steps:

Auto-detect current host:
```bash
<source_repo>/runtime/bin/qros-update --cwd "$PWD"
```

Explicit Codex override:
```bash
<source_repo>/runtime/bin/qros-update --host codex --cwd "$PWD"
```

Explicit Claude Code override:
```bash
<source_repo>/runtime/bin/qros-update --host claude-code --cwd "$PWD"
```

## Self-heal expectations

This skill is for the agent, not the user. Do not surface common update errors immediately.

Before telling the user anything failed, automatically repair and retry these cases:

- missing host-specific install manifest (`~/.codex/qros/install-manifest.json` or `~/.claude/qros/install-manifest.json`)
- stale or missing `source_repo_path`
- missing managed source repo clone
- dirty or drifted managed source repo
- outdated global skills
- missing or stale `./.qros/`
- failed install checks caused by stale install state

Default recovery order:

1. Resolve host with `--host auto` unless the user explicitly requested a host.
2. Read the host-specific global manifest and use `source_repo_path` when it exists.
3. If manifest is missing or stale, try `~/workspace/quant-research-os`.
4. If the managed source repo still does not exist, clone the official QROS repo.
5. Update the managed source repo to `origin/main`.
6. Refresh `user-global`.
7. Refresh the current repo's `repo-local`.
8. Run install checks.

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
- include the host name (Codex or Claude Code)
- confirm the current repo's `./.qros/` runtime was refreshed

Do not dump the full repair log unless the user asks.
