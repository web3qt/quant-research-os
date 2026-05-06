# Technology Stack

**Analysis Date:** 2026-05-06

## Languages

**Primary:**
- Python 3.11+ - Entire codebase is Python. ~656 `.py` files, ~58,381 lines of code (excluding `.venv`, `.worktrees`, `__pycache__`). All runtime tools, scripts, tests, and contract validators are Python.
- Markdown - ~368 `.md` files. SKILL.md definitions, SOP documentation, CLAUDE.md agent instructions, contract companion docs, README files. This is the "configuration language" of the framework.
- YAML - ~66 `.yaml` files. Machine-readable contracts (stage gates, artifact schemas, review checklists, diagnostic profiles), anti-drift snapshots, test fixtures, AGENTS.md agent prompts.

**Secondary:**
- Bash - Shell wrapper `setup` script at project root (`/Users/mac08/workspace/web3qt/quant-research-os/setup`). No other standalone shell scripts; all CLI entry points are Python scripts.
- JSON - Machine-readable state files (manifests, anti-drift snapshots, stage evaluator results, hooks config). Not hand-authored; generated programmatically.
- TOML - Used as an output artifact format (`run_config.toml`), read back via `tomllib` stdlib in `artifact_contract_runtime.py`. `pyproject.toml` for project metadata.
- CSV - Output artifact format for tabular research data (param manifests, signal coverage, rebalance ledgers). Written via `csv` stdlib.
- Parquet - Output artifact format for quantitative research data (factor panels, backtest results, portfolio metrics). Written via `pyarrow.parquet`.
- DrawIO - Architecture diagrams in `docs/visuals/`. Not code-executed.

## Runtime

**Environment:**
- Python 3.11+ (minimum; CI uses 3.13)
- No Node.js, no Rust, no Go, no JVM -- pure Python project

**Package Manager:**
- `uv` (Astral) -- lockfile at `uv.lock` (version 1, revision 3)
- Lockfile present and committed

**Virtual Environment:**
- `.venv/` directory at project root (standard Python venv)
- `.venv/pyvenv.cfg` present

## Frameworks

**Core:**
- No web framework (no Flask, Django, FastAPI, etc.)
- No data science framework at runtime (no pandas, numpy, scipy, sklearn, torch, tensorflow)
- The project is a governance/workflow framework, not a computation engine

**Testing:**
- pytest >= 8.0 (dev dependency)
- pluggy, iniconfig, packaging -- pytest transitive dependencies
- colorama -- terminal color support (likely for pytest output)

**Build/Dev:**
- pyarrow >= 20.0 -- used for writing Parquet artifacts in scaffold/runtime code
- PyYAML >= 6.0 -- YAML contract loading and generation throughout

## Key Dependencies

**Critical (runtime):**
- `PyYAML >= 6.0` -- Loads and validates all YAML contracts (stage gates, artifact schemas, review checklists, diagnostic profiles). The most-used third-party import after stdlib (140 import sites).
- `pyarrow >= 20.0` -- Writes Parquet research artifacts (factor panels, backtest comparison tables, portfolio metrics). Used in scaffold builders and runtime validators (34 import sites for `pq`, 17 for `pa`).

**Dev:**
- `pytest >= 8.0` -- Test runner. Config at `[tool.pytest.ini_options]` in `pyproject.toml`.

**Stdlib-Heavy:**
- `pathlib` -- 284 import sites. Ubiquitous path manipulation.
- `json` -- 101 import sites. Manifest generation, anti-drift snapshots, stage evaluator results.
- `subprocess` -- Used for git operations (update_runtime, install_runtime, lineage_program_runtime) and data pipeline execution.
- `csv` -- 24 import sites. Research data output format.
- `hashlib` -- SHA-256 digests for upstream binding verification in TSS stages.
- `tomllib` -- Python 3.11+ stdlib for reading TOML artifacts.
- `dataclasses`, `typing` -- Extensive use of frozen dataclasses and type annotations.
- `argparse` -- CLI argument parsing for all scripts and bin wrappers.

**Infrastructure:**
- No database drivers, no ORM, no cache layer
- No HTTP client libraries (no requests, httpx, aiohttp)
- No cloud SDKs (no boto3, google-cloud, azure)

## Configuration

**Project Metadata:**
- `pyproject.toml` at `/Users/mac08/workspace/web3qt/quant-research-os/pyproject.toml`
  - Project name: `quant-research-os`
  - Version: `0.4.4`
  - Description: "Agentic stage-gated governance framework for quantitative research workflows"
  - requires-python: `>=3.11`

**Build:**
- No build system beyond `pyproject.toml` (no setuptools, no hatchling, no poetry)
- `setup` is a bash script, not a Python package config
- No Dockerfile, no docker-compose, no containerization

**Lockfile:**
- `uv.lock` at `/Users/mac08/workspace/web3qt/quant-research-os/uv.lock`
- 9 packages total (including transitive): colorama, iniconfig, packaging, pluggy, pyarrow, pygments, pytest, pyyaml, quant-research-os

**Python Test Config:**
```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

**Git:**
- `.gitignore` at `/Users/mac08/workspace/web3qt/quant-research-os/.gitignore`
- Main branch: `main`; development branch: `dev`

## Platform Requirements

**Development:**
- Python 3.11+ (3.13 in CI)
- `uv` package manager (for lockfile fidelity)
- Git
- No other system dependencies

**Supported AI Hosts:**
- OpenAI Codex -- primary host; skills installed to `~/.codex/skills/`
- Claude Code -- secondary host; skills installed to `~/.claude/skills/` or `.claude-plugin/skills/`

**Production/Deployment:**
- No server deployment. This is a framework repository, not a running service.
- Installed into research repos via `setup` script or `install_runtime.py`
- Runtime assets copied to `.qros/` (repo-local) or host skill directories (global)

## CI/CD

**Pipeline:**
- GitHub Actions -- single workflow at `.github/workflows/anti-drift.yml`
- Runs on: PRs, pushes to main, nightly schedule (cron 03:00 UTC), manual dispatch
- Runner: `ubuntu-latest`, Python 3.13

**Jobs:**
1. `pr-gate` (PRs and pushes): Runs anti-drift tests, generator freshness check, snapshot baseline comparison
2. `nightly-release-gate` (schedule/dispatch): Full nightly pipeline including research session snapshot verification

**Test Commands (from CI):**
```bash
python -m pip install PyYAML pytest pyarrow
python -m pytest tests/anti_drift/ tests/session/ tests/contracts/ tests/review/ ...
python runtime/scripts/gen_stage_review_skills.py --dry-run
python runtime/scripts/export_anti_drift_snapshots.py --output-dir /tmp/current_snapshots
python runtime/scripts/anti_drift_baseline.py compare --baseline ... --current ...
```

**Artifacts:**
- Uploaded via `actions/upload-artifact@v4`
- Anti-drift snapshots, comparison JSON, nightly reports, gate summaries, release artifacts

---

*Stack analysis: 2026-05-06*
