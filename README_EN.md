# 🛠 Quant Research OS | QROS

English | [中文](README.md)

QROS is a stage-gated research governance framework for AI coding agents. It turns raw trading ideas into **reviewable, reproducible, auditable** research lineages through freeze discipline, review discipline, formal artifacts, and workflow gates.

## Current Main Flow

```text
00_idea_intake -> 00_mandate
├─ time_series_signal
│  -> 01_data_ready
│  -> 02_signal_ready
│  -> 03_train_freeze
│  -> 04_test_evidence
│  -> 05_backtest_ready
│  -> 06_holdout_validation
└─ cross_sectional_factor
   -> 01_csf_data_ready
   -> 02_csf_signal_ready
   -> 03_csf_train_freeze
   -> 04_csf_test_evidence
   -> 05_csf_backtest_ready
   -> 06_csf_holdout_validation
```

QROS fixes the stage order, freeze/review gates, failure routing, and lineage discipline. The actual research implementation should be authored by the agent inside the active research repo.

## Repo Boundary

This repository is a **workflow/framework repo**, not the real artifact repo for a specific strategy lineage.

- It provides: workflow, skills, runtimes, gates, and review discipline
- It does not serve as: the real research implementation repo for one concrete strategy line
- Real research should advance under `outputs/<lineage_id>/` in the active research repo

With the lineage-local stage-program hard gate, every executable stage must also keep a route-aware stage program under `outputs/<lineage_id>/program/`, including `stage_program.yaml`, `README.md`, and the manifest-referenced entrypoint. The corresponding stage artifact directory must also contain `program_execution_manifest.json`. QROS runtime governs gates, contract validation, invocation, output verification, and provenance recording; framework-side shared builders no longer count as a completion path.

## Single-Entry Orchestrator

After installation, the recommended starting point is always the single entry orchestrator:

```text
qros-research-session Help me research this idea: BTC leads high-liquidity alts after shock events
qros-research-session help
```

That entry point will:

- create or resume the lineage
- detect the current stage
- resolve which skill should act now
- stop for governance confirmation when required
- write formal artifacts when deterministic progress is possible

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

When you begin actual work, keep using the same single-entry orchestrator above: `qros-research-session`.

## Why QROS

Most research ideas start as loose chat. Serious research does not. QROS exists to move a research team from vague idea discussion to explicit scope, frozen contracts, on-disk artifacts, and reviewable stage progression.

## Current Operating Shape

- All `*_review` stages now require an **independent adversarial reviewer**
- The reviewer must inspect stage artifacts, provenance, and the lineage-local `program/<stage>/` source implementation
- Only `CLOSURE_READY_*` outcomes may continue into deterministic closure via `~/.qros/bin/qros-review`
- `FIX_REQUIRED` returns the workflow to the author-fix loop and blocks closure artifacts
- Above the review loop, a **governance-candidate lane** records post-rollout repeated findings into `governance_signal.json`, `governance/review_findings_ledger.jsonl`, and `governance/candidates/*.yaml`
- Candidate priority is fixed as: `hard_gate -> template_constraint -> regression_test`
- Even an approved human governance decision does not activate policy directly; active changes still land through normal reviewed repo edits

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

If you want the deeper runtime behavior, state fields, and workflow semantics, continue with:

- `docs/experience/qros-research-session-usage.md`
- `docs/main-flow-sop/research_workflow_sop.md`

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
