# 🛠 Quant Research OS | QROS

English | [中文](README.md)

QROS is a stage-gated research workflow for AI coding agents. It turns raw trading ideas into reviewable, reproducible, and auditable research lineages through interactive mandate freezing, formal artifacts, and workflow gates.

With the lineage-local stage-program hard gate, every executable stage must also keep a route-aware stage program under `outputs/<lineage_id>/program/` in the active research repo, including `stage_program.yaml`, `README.md`, and the manifest-referenced entrypoint. The corresponding stage artifact directory must also contain `program_execution_manifest.json`. QROS runtime now governs freeze/review gates, validates and invokes the local program, verifies outputs, and records provenance; framework-side shared builders no longer count as a completion path.

## Quick Start

### Claude Code

```text
/plugin marketplace add web3qt/quant-research-os
/plugin install quant-research-os@qros
```

After installation, mention a quantitative research idea in a new session and QROS will activate automatically.

### Codex

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

## Start Research

```text
qros-research-session Help me research this idea: BTC leads high-liquidity alts after shock events
qros-research-session help
```

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
- `train_freeze`
- `train_freeze review`
- `test_evidence`
- `test_evidence review`
- `backtest_ready`
- `backtest_ready review`
- `holdout_validation`
- `holdout_validation review`

The intended experience is skill-first:

- start from one skill entry
- let the agent create or resume the lineage
- let the workflow drive the next required interaction
- keep formal artifacts on disk as the source of truth

## Updating

**Claude Code:**

```text
/plugin update quant-research-os
```

**Codex / manual install:**

```bash
cd ~/.qros && git pull
```

## Runtime Layout

**Plugin install (Claude Code):**

The plugin system manages skill discovery and hook injection automatically.

**Manual install (Codex / generic):**

```text
~/.qros/skills/
~/.agents/skills/qros -> ~/.qros/skills
```

## Learn More

- [Claude Code Installation](.claude/INSTALL.md)
- [Codex Installation](docs/experience/installation.md)
- [Quickstart For Codex](docs/experience/quickstart-codex.md)
- [QROS Research Session Usage](docs/experience/qros-research-session-usage.md)
- [Stage Freeze Group Field Guide (CN)](docs/experience/stage-freeze-group-field-guide.md)

## Troubleshooting

- Claude Code: skills not visible after install — restart session or run `/plugin update quant-research-os`
- Codex: skills not visible — verify `~/.agents/skills/qros` points to `~/.qros/skills`
- Stale install: Claude Code `/plugin update quant-research-os`; Codex `cd ~/.qros && git pull`
- Unsure if install is healthy: start a new session and mention a quant research idea to test auto-trigger
