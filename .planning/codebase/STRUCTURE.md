# Codebase Structure

**Analysis Date:** 2026-05-06

## Directory Layout

```
quant-research-os/
├── contracts/          # Machine-readable stage gates, artifact schemas, review checklists
├── docs/               # SOPs, user guides, design specs, implementation plans, visuals
├── hooks/              # Empty directory (hooks live in runtime/hooks/)
├── runtime/            # Python runtime: bin entry points, scripts, tools library
├── skills/             # Author, review, failure, orchestrator SKILL.md definitions
├── templates/          # Jinja-style skill templates for generated review skills
├── tests/              # Multi-layer test suite
├── .claude-plugin/     # Claude Code host config: reviewer agent, review skill bindings
├── .codex/             # Codex host config: installation instructions
├── .github/            # CI/CD workflows (anti-drift gate)
├── .planning/          # GSD planning artifacts (this file lives here)
├── pyproject.toml      # Python project metadata (name=quant-research-os, v0.4.4)
├── uv.lock             # uv lockfile
├── AGENTS.md           # Top-level agent context document
├── README.md           # Project README (Chinese)
├── RELEASE_NOTES.md    # Release history
└── todo.md             # Project-level TODO
```

## Directory Purposes

**`contracts/`:**
- Purpose: Single source of machine-readable truth for the entire governance framework
- Contains: Stage gate definitions (YAML), artifact schemas (YAML), review checklists (YAML), JSON schemas, diagnostic profiles, agent eval cases, intake schemas
- Key files: `contracts/stages/workflow_stage_gates.yaml` (2318 lines, the central stage definition), `contracts/stages/stage_evaluator.schema.json`, `contracts/artifacts/*.yaml`, `contracts/review/review_checklist_master.yaml`

**`runtime/`:**
- Purpose: Executable Python code that enforces contracts, scaffolds stages, runs reviews, validates artifacts, and manages installation
- Contains: Shell entry points (bin/), CLI wrapper scripts (scripts/), Python library modules (tools/), hook definitions (hooks/)
- Key files: `runtime/bin/qros-session`, `runtime/bin/qros-review`, `runtime/bin/qros-update`, `runtime/tools/research_session.py`, `runtime/tools/review_skillgen/review_engine.py`

**`skills/`:**
- Purpose: Agent-readable SKILL.md instructions organized by stage domain
- Contains: ~30 skill directories, each containing a `SKILL.md` and optionally `agents/openai.yaml`
- Key files: `skills/core/qros-research-session/SKILL.md` (primary orchestrator skill), `skills/<stage>/qros-<stage>-review/SKILL.md` (review skills), `skills/<stage>/qros-<stage>-author/SKILL.md` (author skills)

**`templates/`:**
- Purpose: Template files for code generation (review skill generation)
- Contains: `templates/skills/review-stage/SKILL.md.tmpl`
- Generated: No (these are source templates)
- Committed: Yes

**`tests/`:**
- Purpose: Multi-layer test suite ensuring correctness across contracts, runtime, sessions, reviews, and anti-drift
- Contains: 10 test directories mirroring system layers
- Key files: `tests/helpers/repo_paths.py` (shared test constants), `tests/fixtures/anti_drift/*_snapshot.json` (blessed snapshots)

**`docs/`:**
- Purpose: Human-readable documentation including SOPs, guides, design specs, implementation plans, and visual diagrams
- Contains: `docs/sop/` (standard operating procedures per stage), `docs/guides/` (user guides), `docs/superpowers/specs/` (design specs), `docs/superpowers/plans/` (implementation plans), `docs/archive/plans/` (historical plans), `docs/visuals/` (diagrams)

**`.claude-plugin/`:**
- Purpose: Claude Code host configuration for running QROS review skills
- Contains: `agents/qros-reviewer.md` (reviewer agent definition), `skills/` (review skill bindings mirroring `skills/` review skills)
- Generated: Partially (review skills are generated from templates and installed here)
- Committed: Yes

**`.codex/`:**
- Purpose: Codex host configuration
- Contains: `INSTALL.md` (installation instructions fetched by users)

## Key File Locations

**Entry Points:**
- `runtime/bin/qros-session`: Primary research session entry (shell script, delegates to `run_research_session.py`)
- `runtime/bin/qros-review`: Review execution entry (shell script, delegates to `run_stage_review.py`)
- `runtime/bin/qros-update`: Framework update entry (shell script, delegates to `run_qros_update.py`)
- `runtime/bin/qros-progress`: Read-only progress query (shell script, delegates to `run_progress.py`)
- `runtime/bin/qros-validate-stage`: Deterministic preflight validation (shell script, delegates to `validate_stage_artifacts.py`)
- `runtime/bin/qros-factor-diagnostics`: CSF diagnostic entry (shell script, delegates to `run_factor_diagnostics.py`)
- `runtime/bin/qros-signal-diagnostics`: TSS diagnostic entry (shell script, delegates to `run_signal_diagnostics.py`)
- `runtime/bin/qros-review-cycle`: Review cycle management (shell script, delegates to `review_cycle.py`)
- `runtime/bin/qros-review-preflight`: Review preflight check (shell script, delegates to `qros_review_preflight.py`)
- `runtime/bin/qros-start-review`: Review session starter (shell script, delegates to `start_review_session.py`)
- `runtime/bin/qros-audit-reviewer`: Reviewer audit (shell script, delegates to `audit_reviewer_write_scope.py`)
- `runtime/bin/qros-agent-eval`: Agent behavior evaluation (shell script, delegates to `run_agent_behavior_eval.py`)

**Configuration:**
- `pyproject.toml`: Python project metadata (version 0.4.4, requires-python >=3.11, deps: PyYAML, pyarrow)
- `contracts/stages/workflow_stage_gates.yaml`: Central stage gate definition (all stages, verdicts, rules)
- `runtime/hooks/hooks.json`: Claude Code session-start hook configuration

**Core Logic:**
- `runtime/tools/research_session.py`: Main session orchestration (stage lifecycle, routing, scaffolding)
- `runtime/tools/review_skillgen/review_engine.py`: Review engine (loads contracts, validates protocol, runs gates)
- `runtime/tools/review_skillgen/closure_writer.py`: Writes closure artifacts and stage evaluator results
- `runtime/tools/review_skillgen/protocol_validator.py`: Validates review protocol compliance
- `runtime/tools/review_skillgen/stage_content_gate.py`: Structural and metric gate checks
- `runtime/tools/review_skillgen/upstream_binding_validator.py`: Route inheritance and upstream digest validation
- `runtime/tools/review_skillgen/adversarial_review_contract.py`: Review contract constants and validation
- `runtime/tools/stage_evaluator.py`: Stage completion evaluation
- `runtime/tools/lineage_program_runtime.py`: Lineage-local program identity and provenance
- `runtime/tools/install_runtime.py`: Framework installation logic
- `runtime/tools/anti_drift.py`: Anti-drift regression detection
- `runtime/tools/verification_tiers.py`: Test tier definitions (smoke, full-smoke)

**Testing:**
- `tests/contracts/`: Contract schema and artifact contract validation tests
- `tests/runtime/`: Runtime tool tests (stage runtimes, semantic validation, contract validators)
- `tests/session/`: Research session integration tests (artifact shapes, routing, reflection)
- `tests/review/`: Review engine tests (generation, engine, preflight, closure, evaluator)
- `tests/anti_drift/`: Anti-drift regression tests (baseline, replay, metamorphic, snapshots)
- `tests/bootstrap/`: Installation and setup tests
- `tests/pipeline/`: Full pipeline tests (CSF and TSS routes)
- `tests/e2e/`: End-to-end agent session tests
- `tests/agent_eval/`: Agent behavior evaluation case tests
- `tests/docs/`: Documentation hygiene tests
- `tests/helpers/`: Shared test utilities (repo_paths, fixtures, assertions, harness)
- `tests/fixtures/anti_drift/`: Blessed snapshot files for anti-drift comparison

## Naming Conventions

**Files:**
- Shell entry points: `qros-<verb>` (e.g., `qros-session`, `qros-review`, `qros-update`)
- Python scripts: `run_<action>.py` or `<action>.py` in `runtime/scripts/` (e.g., `run_research_session.py`, `review_cycle.py`)
- Python tools: `<domain>_runtime.py` for stage runtimes (e.g., `csf_data_ready_runtime.py`), `<feature>.py` for utilities (e.g., `anti_drift.py`)
- Review skillgen modules: `<concern>.py` in `runtime/tools/review_skillgen/` (e.g., `closure_writer.py`, `protocol_validator.py`)
- Skill directories: `qros-<stage>-<role>` (e.g., `qros-csf-data-ready-review`, `qros-mandate-author`)
- Contract files: `<stage>_artifacts.yaml`, `<domain>_schema.yaml`, `<domain>_library.yaml`
- Test files: `test_<subject>.py` in mirror directories (e.g., `tests/runtime/test_csf_data_ready_runtime.py`)

**Directories:**
- Stage domains: snake_case (e.g., `csf_data_ready`, `tss_holdout_validation`, `idea_intake`)
- Test directories: snake_case matching source layer (e.g., `anti_drift`, `agent_eval`, `bootstrap`)
- Documentation: snake_case (e.g., `docs/sop/main-flow/`, `docs/guides/`)

## Where to Add New Code

**New Stage (e.g., new CSF or TSS stage):**
- Contract definition: `contracts/stages/workflow_stage_gates.yaml` (add new stage entry)
- Artifact schema: `contracts/artifacts/<stage>_artifacts.yaml`
- Stage runtime: `runtime/tools/<stage>_runtime.py`
- Contract runtime: `runtime/tools/<stage>_contract_runtime.py`
- Author skill: `skills/<domain>/qros-<stage>-author/SKILL.md`
- Review skill: `skills/<domain>/qros-<stage>-review/SKILL.md`
- Failure skill: `skills/<domain>/qros-<stage>-failure/SKILL.md` (if applicable)
- SOP: `docs/sop/main-flow/<nn>_<stage>_sop_cn.md`
- Tests: `tests/runtime/test_<stage>_runtime.py`, `tests/contracts/test_<stage>_artifact_contract.py`, `tests/session/test_<stage>_artifact_shape.py`, `tests/review/test_review_preflight_<stage>_contract.py`
- Register in: `runtime/tools/research_session.py` (routing), `runtime/tools/stage_evaluator.py` (required outputs), `runtime/tools/anti_drift.py` (stage mapping)

**New Review Skillgen Feature:**
- Implementation: `runtime/tools/review_skillgen/<feature>.py`
- Tests: `tests/review/test_<feature>.py`
- Template integration: `templates/skills/review-stage/SKILL.md.tmpl` (if affects generated skills)

**New CLI Command:**
- Shell entry point: `runtime/bin/qros-<verb>`
- Python script: `runtime/scripts/<verb>.py` or `runtime/scripts/run_<verb>.py`
- Python tool: `runtime/tools/<feature>.py`

**New Diagnostic Profile:**
- Contract: `contracts/diagnostics/<profile>.yaml`
- Runtime: `runtime/tools/<profile>_diagnostics.py`
- Script: `runtime/scripts/run_<profile>_diagnostics.py`
- Bin: `runtime/bin/qros-<profile>-diagnostics`
- Skill: `skills/core/qros-<profile>-diagnostics/SKILL.md`
- Tests: `tests/runtime/test_<profile>_diagnostics.py`

**New Utility/Helper:**
- Shared helpers: `tests/helpers/<utility>.py`
- Runtime utility: `runtime/tools/<utility>.py`

## Special Directories

**`runtime/tools/review_skillgen/`:**
- Purpose: Review engine package -- the most complex subsystem in the framework
- Contains: 16 Python modules handling adversarial review contracts, closure writing, protocol validation, scope building, upstream binding, and gate checking
- Generated: No (all hand-written)
- Committed: Yes
- Key modules: `review_engine.py` (central orchestrator), `closure_writer.py` (artifact output), `protocol_validator.py` (compliance), `stage_content_gate.py` (structural/metric gates), `upstream_binding_validator.py` (route inheritance)

**`tests/fixtures/anti_drift/`:**
- Purpose: Blessed baseline snapshots for anti-drift regression testing
- Contains: `*_snapshot.json` files capturing contract state at known-good points
- Generated: Yes (by `runtime/scripts/export_anti_drift_snapshots.py`)
- Committed: Yes (updates require deliberate baseline promotion per `docs/anti_drift_baseline_promotion_protocol.md`)

**`.claude-plugin/`:**
- Purpose: Claude Code host-specific configuration
- Contains: Agent definition (`agents/qros-reviewer.md`) and skill bindings (`skills/`)
- Generated: Partially -- review skills are generated from templates by `gen_stage_review_skills.py` and installed here during `$qros-update`
- Committed: Yes

**`.codex/`:**
- Purpose: Codex host-specific configuration
- Contains: `INSTALL.md` (installation bootstrap instructions)
- Generated: No
- Committed: Yes

**`docs/visuals/`:**
- Purpose: Architecture diagrams and stage flow visuals
- Contains: `.drawio` and `.excalidraw` files with `.md` renderings
- Generated: No (hand-crafted diagrams)
- Committed: Yes

---

*Structure analysis: 2026-05-06*
