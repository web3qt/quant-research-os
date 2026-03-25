# Quant Research OS

Stage-gated research workflow assets for Codex, focused on turning trading ideas into reviewable, reproducible research lineages.

## Quick Start

1. Clone this repository.
2. Install QROS for Codex:

```bash
./setup --host codex --mode user-global
```

Or install into the current repo so teammates get the same skills and runtime:

```bash
./setup --host codex --mode repo-local
```

3. Start a new lineage:

```bash
python scripts/scaffold_idea_intake.py --lineage-root outputs/<lineage_id>
```

4. Use these skills in order:

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`

5. Build mandate artifacts after the intake gate passes:

```bash
python scripts/build_mandate_from_intake.py --lineage-root outputs/<lineage_id>
```

6. Run the stage review from the relevant stage directory:

```bash
python scripts/run_stage_review.py
```

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

The smallest supported flow today is:

`idea_intake -> mandate -> mandate_review`

Typical path:

```bash
python scripts/scaffold_idea_intake.py --lineage-root outputs/<lineage_id>
python scripts/build_mandate_from_intake.py --lineage-root outputs/<lineage_id>
python scripts/run_stage_review.py
```

See:

- [installation.md](docs/experience/installation.md)
- [quickstart-codex.md](docs/experience/quickstart-codex.md)
- [idea-intake-to-mandate-flow.md](docs/experience/idea-intake-to-mandate-flow.md)

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
