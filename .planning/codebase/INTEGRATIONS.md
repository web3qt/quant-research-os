# External Integrations

**Analysis Date:** 2026-05-20

## APIs & External Services

**GitHub:**
- Used for framework distribution and version updates
- Repository: `https://github.com/web3qt/quant-research-os.git`
- Integration: `git clone` / `git pull` / `git fetch` via `subprocess` in `runtime/tools/install_runtime.py` and `runtime/tools/update_runtime.py`
- SDK/Client: Git CLI via `subprocess.run`
- Auth: SSH key or HTTPS credential (user-configured, not in repo)

**AI Agent Hosts (Codex / Claude Code):**
- Codex CLI — Skill discovery at `~/.codex/skills/qros-*/`, agent sub-spawning with `spawn_agent (fork_context=false)`
- Claude Code — Plugin system at `.claude-plugin/`, session hooks at `runtime/hooks/`, adversarial reviewer agent at `.claude-plugin/agents/qros-reviewer.md`
- Integration: File-system-based skill discovery, AGENTS.md instruction chaining, shell entry points
- Auth: Host-provided (user's existing Codex/Claude Code session)

## Data Storage

**Databases:**
- None — QROS does not use a database. All state is file-based.

**File Storage:**
- Local filesystem only — Stage state, artifacts, freeze groups, and provenance stored as files in active research repo's `outputs/<lineage_id>/` directory
- Artifact formats: YAML, JSON, Parquet, CSV, Markdown
- Provenance tracking: `program_execution_manifest.json` per stage
- Lineage lock ledger: `runtime/tools/lineage_lock_ledger.py` tracks frozen artifact integrity

**Caching:**
- Python bytecode cache (`__pycache__/`) — Standard Python caching
- Anti-drift snapshot cache: `tests/fixtures/anti_drift/*_snapshot.json` — Blessed baseline snapshots for regression detection

## Authentication & Identity

**Auth Provider:**
- Not applicable — QROS has no user authentication system
- Identity is implicitly tied to the AI agent host session (Codex or Claude Code)
- Author vs Reviewer separation enforced by governance contracts, not by technical auth:
  - Author lane produces artifacts
  - Reviewer lane performs adversarial review via `.claude-plugin/agents/qros-reviewer.md`
  - `contracts/stages/workflow_stage_gates.yaml` mandates independent reviewer

## Monitoring & Observability

**Error Tracking:**
- None — No external error tracking service

**Logs:**
- `runtime/tools/research_session.py` outputs session state to stdout as structured JSON
- `runtime/scripts/run_progress.py` provides read-only progress display
- Anti-drift nightly reports: `runtime/scripts/render_anti_drift_nightly_report.py`
- Stage evaluator output: JSON files following `contracts/stages/stage_evaluator.schema.json`

## CI/CD & Deployment

**Hosting:**
- GitHub repository hosting: `https://github.com/web3qt/quant-research-os`
- No server hosting — QROS runs locally in the user's research environment

**CI Pipeline:**
- GitHub Actions — `.github/workflows/anti-drift.yml`
- Triggers: PR, push to main, nightly cron (03:00 UTC), manual dispatch
- Jobs:
  - `pr-gate`: Anti-drift regression tests on PRs and pushes
  - `nightly-release-gate`: Full nightly pipeline with snapshot comparison and release artifact generation
- CI Dependencies: Python 3.13, PyYAML, pytest, pyarrow
- Actions used: `actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`

## Environment Configuration

**Required env vars:**
- `QROS_PYTHON` (optional) — Override Python binary for runtime wrappers
- `CLAUDE_PLUGIN_ROOT` (set by Claude Code) — Plugin root for hook resolution

**Secrets location:**
- No secrets stored in repository
- Git credentials managed externally by user's SSH/HTTPS setup

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Formats & Interchange

**Parquet (pyarrow):**
- Primary binary format for research data artifacts
- Used for factor panels, signal panels, quality flags, coverage reports, diagnostic outputs
- Read/write via `pyarrow.parquet` in `runtime/tools/artifact_contract_runtime.py`, `csf_*_runtime.py`, `tss_*_runtime.py`, `factor_diagnostics.py`, `signal_diagnostics.py`

**YAML (PyYAML):**
- Machine-readable contracts, stage gates, freeze groups, manifests
- Used throughout `contracts/` and `runtime/tools/`

**JSON:**
- Run manifests, provenance files, evaluator results, diagnostic summaries
- Schema validation via `contracts/stages/stage_evaluator.schema.json` (JSON Schema draft 2020-12)

**CSV:**
- Ledger files, variant tracking, gate tables

**Markdown:**
- Human-readable artifacts (gate decisions, contracts, field dictionaries, catalogs)
- Skill definitions (`SKILL.md` files in `skills/`)

## Agent Skill System Integration

**Skill Discovery:**
- Codex: `~/.codex/skills/qros-<skill-name>/SKILL.md`
- Claude Code: `.claude-plugin/skills/<skill-name>/SKILL.md`
- Built from `skills/` source via `runtime/scripts/gen_stage_review_skills.py`
- Templates: `templates/skills/review-stage/`

**Skill Types:**
- Core skills: `qros-research-session`, `qros-progress`, `qros-update`, `qros-factor-diagnostics`, `qros-signal-diagnostics`, `qros-stage-display`, `using-qros`
- Stage-specific author skills: Per-stage skill bundles in `skills/<stage>/` (22 stage directories)
- Review skills: Generated per-stage from templates
- Failure handling skills: `skills/failure_handling/`

**Review Agent:**
- Claude Code: `.claude-plugin/agents/qros-reviewer.md` — Independent adversarial reviewer
- Review protocol: `runtime/tools/review_session_runtime.py`, `runtime/scripts/review_cycle.py`
- Review skill generation: `runtime/tools/review_skillgen/` (24 files in dedicated subpackage)

---

*Integration audit: 2026-05-20*
