# Technology Stack

**Analysis Date:** 2026-05-20

## Languages

**Primary:**
- Python 3.11+ (requires `>=3.11` per `pyproject.toml`) — All runtime tools, scripts, tests, and skill generators. Python 3.12 preferred for `uv` runtime (`runtime/tools/uv_runtime_env.py` sets `PYTHON_RUNTIME = "3.12"`).

**Secondary:**
- Bash — CLI entry points in `runtime/bin/` (e.g., `qros-session`, `qros-review`, `qros-update`, `qros-progress`). Shell wrappers that locate Python and invoke runtime scripts.
- YAML — Machine-readable contracts in `contracts/` (stage gates, artifact schemas, diagnostic profiles, review checklists).
- JSON — Stage evaluator schemas (`contracts/stages/stage_evaluator.schema.json`), run manifests, provenance files, diagnostic outputs.
- TOML — Project config (`pyproject.toml`), research run configs (`run_config.toml` in research outputs).
- Markdown — Human-readable artifacts, skill definitions (`SKILL.md`), gate decisions, documentation.

## Runtime

**Environment:**
- Python `>=3.11` (CI uses Python 3.13 per `.github/workflows/anti-drift.yml`)
- `tomllib` used for TOML parsing (stdlib in Python 3.11+)

**Package Manager:**
- uv — Fast Python package manager used for dependency resolution and virtual environment management
- Lockfile: `uv.lock` present (191 lines, v1 format)
- Config: `pyproject.toml`

## Frameworks

**Core:**
- No web framework — QROS is a CLI-based governance framework, not a server application
- Custom stage-gated state machine built from scratch in `runtime/tools/research_session.py` (229K+ lines)

**Testing:**
- pytest >=8.0 — Test runner with config in `pyproject.toml` (`[tool.pytest.ini_options]`)
- 999 collected tests across multiple test directories

**Build/Dev:**
- uv — Package management and virtual environment provisioning
- `./setup` — Bootstrap script that calls `runtime/tools/install_runtime.py`
- `runtime/tools/uv_runtime_env.py` — Ensures repo-local uv runtime with correct Python version

## Key Dependencies

**Critical:**
- PyYAML >=6.0 — YAML parsing for contracts, stage gates, artifact schemas, freeze groups, review checklists. Used pervasively across `runtime/tools/` and `runtime/scripts/`.
- pyarrow >=20.0 (locked to 24.0.0) — Parquet file I/O for research artifacts (factor panels, signal panels, quality flags, diagnostics, coverage reports). Used in `runtime/tools/artifact_contract_runtime.py`, `csf_*_runtime.py`, `tss_*_runtime.py`, `factor_diagnostics.py`, `signal_diagnostics.py`.

**Standard Library (Heavy Usage):**
- `json` — Run manifests, provenance files, diagnostic summaries, evaluator results
- `pathlib` — File system operations throughout all runtime tools
- `dataclasses` — Data structures for session context, freeze groups, stage evaluation
- `subprocess` — Git operations in `install_runtime.py` and `update_runtime.py`
- `hashlib` — Content hashing for anti-drift snapshots and provenance
- `argparse` — CLI argument parsing in scripts
- `tomllib` — TOML config reading (Python 3.11+ stdlib)
- `csv` — Ledger and variant file I/O
- `re` — Pattern matching in session parsing, anti-drift
- `shutil`, `tempfile` — File operations in install/update tooling

**Dev Dependencies:**
- pytest >=8.0 — Test framework (`[project.optional-dependencies] dev`)

## Configuration

**Environment:**
- No `.env` files in repo — configuration is contract-file-driven
- `QROS_PYTHON` env var — Override Python binary selection in `runtime/bin/qros-wrapper-lib`
- `CLAUDE_PLUGIN_ROOT` env var — Set by Claude Code plugin system for hook resolution
- Settings: `.claude/settings.local.json` present (local Claude Code settings)

**Build:**
- `pyproject.toml` — Project metadata, dependencies, pytest config
- `uv.lock` — Deterministic dependency lockfile
- `.gitignore` — Excludes `.venv/`, `__pycache__/`, `.omc/`, `.omx/`, `.qros/`, `outputs/`, `governance/`

**Contracts:**
- `contracts/stages/workflow_stage_gates.yaml` — Master stage gate definitions (2326 lines)
- `contracts/stages/stage_evaluator.schema.json` — JSON Schema for evaluator output
- `contracts/artifacts/*.yaml` — Per-stage artifact expectations (14 files)
- `contracts/review/review_checklist_master.yaml` — Review checklist definitions
- `contracts/intake/*.yaml` — Idea gate and qualification scorecard schemas
- `contracts/diagnostics/*.yaml` — Diagnostic metric libraries and stage profiles

## Platform Requirements

**Development:**
- Python >=3.11 (3.12+ recommended)
- uv package manager
- Git
- Supported AI host: Codex CLI (>=0.130.0) or Claude Code (>=2.1.128)

**Production:**
- Active research repo consuming QROS as a governance layer
- QROS installed via `./setup --host codex|claude-code --mode user-global|repo-local`
- Research repo bootstrapped with `./.qros/` runtime directory
- Deployment is agent-driven: no traditional server deployment

## Host Agent Integration

**Codex:**
- Skill discovery via `~/.codex/skills/qros-*/`
- Install instructions: `.codex/INSTALL.md`
- AGENTS.md instruction chain for directory-scoped rules

**Claude Code:**
- Plugin system via `.claude-plugin/` (skills + agents)
- Session start hook: `runtime/hooks/hooks.json` + `runtime/hooks/session-start`
- Reviewer agent: `.claude-plugin/agents/qros-reviewer.md`
- Install instructions: `.claude/INSTALL.md`

---

*Stack analysis: 2026-05-20*
