# Codebase Structure

**Analysis Date:** 2026-05-20

## Directory Layout

```
quant-research-os/
├── contracts/                # Machine-readable truth layer
│   ├── stages/               # Stage gate definitions (YAML/JSON)
│   ├── artifacts/            # Per-stage artifact schemas (YAML)
│   ├── review/               # Review checklists
│   ├── diagnostics/          # Diagnostic profiles and metric libraries
│   ├── intake/               # Idea intake schemas
│   ├── agent_eval/           # Agent behavior eval cases
│   ├── governance/           # Governance contracts
│   └── AGENTS.md             # Contract editing rules
├── runtime/                  # Python runtime engine
│   ├── bin/                  # CLI entry points (16 commands)
│   ├── scripts/              # Command wrappers and task runners
│   ├── tools/                # Core engine modules (~60 .py files)
│   │   └── review_skillgen/  # Review engine subsystem (~20 .py files)
│   ├── hooks/                # Session hooks (hooks.json + session-start)
│   └── AGENTS.md             # Runtime editing rules
├── skills/                   # Agent behavior bundles (~56 skills)
│   ├── core/                 # Cross-cutting utilities (7 skills)
│   ├── idea_intake/          # Idea intake skill
│   ├── mandate/              # Mandate skills (author, review)
│   ├── <stage>/              # Per-stage skills (author, review, failure)
│   ├── tss_<stage>/          # Time-series signal route skills
│   ├── csf_<stage>/          # Cross-sectional factor route skills
│   ├── failure_handling/     # Failure and lineage change skills
│   └── AGENTS.md             # Skills editing rules
├── templates/                # Skill template generator
│   └── skills/
│       └── review-stage/
│           └── SKILL.md.tmpl
├── tests/                    # Test suite (999 tests, 12 directories)
│   ├── session/              # Session orchestration tests
│   ├── review/               # Review engine tests
│   ├── contracts/            # Contract compliance tests
│   ├── anti_drift/           # Anti-drift regression tests
│   ├── skills/               # Skill tree integrity tests
│   ├── runtime/              # Runtime tool tests
│   ├── pipeline/             # End-to-end pipeline tests
│   ├── bootstrap/            # Project bootstrap tests
│   ├── docs/                 # Documentation regression tests
│   ├── e2e/                  # End-to-end integration tests
│   ├── agent_eval/           # Agent behavior eval tests
│   ├── fixtures/             # Test fixtures and shared data
│   ├── helpers/              # Test helper utilities
│   └── AGENTS.md             # Test directory rules
├── docs/                     # Documentation
│   ├── guides/               # User guides
│   ├── sop/                  # Standard operating procedures
│   ├── governance/           # Governance documentation
│   ├── visuals/              # Diagrams and visual assets
│   ├── plans/                # Planning documents
│   ├── archive/              # Archived documents
│   ├── superpowers/          # Superpower specs and plans
│   └── AGENTS.md             # Documentation editing rules
├── .claude/                  # Claude Code installation
│   ├── INSTALL.md            # Claude Code install instructions
│   └── settings.local.json   # Local Claude Code settings
├── .claude-plugin/           # Claude Code plugin distribution
│   ├── agents/               # Reviewer agent definition
│   └── skills/               # Plugin-specific review skills
├── .codex/                   # Codex CLI installation
│   └── INSTALL.md            # Codex install instructions
├── .planning/                # Project planning (not committed to release)
├── AGENTS.md                 # Root agent rules and conventions
├── README.md                 # Project overview and quick start
├── RELEASE_NOTES.md          # Version release notes
├── pyproject.toml            # Python project configuration
├── uv.lock                   # UV lockfile
├── setup                     # Installation bootstrap script
├── todo.md                   # Development task tracking
└── .gitignore                # Git ignore rules
```

## Directory Purposes

### `contracts/`

- **Purpose**: Machine-readable truth layer. All stage gates, artifact schemas, verdict vocabularies, and review checklists.
- **Contains**: YAML gate definitions, JSON schemas, YAML artifact manifests, diagnostic metric libraries
- **Key files**:
  - `contracts/stages/workflow_stage_gates.yaml` -- The central contract: all 20 stage definitions with gates, verdicts, rollback rules, downstream permissions, structural and metric gate checks
  - `contracts/stages/stage_evaluator.schema.json` -- JSON schema for stage evaluator configuration
  - `contracts/artifacts/<stage>_artifacts.yaml` -- 14 artifact manifest files (one per non-idea-intake stage)
  - `contracts/review/review_checklist_master.yaml` -- Master review checklist loaded by review engine
  - `contracts/diagnostics/factor_metric_library.yaml`, `tss_metric_library.yaml` -- Metric definitions for diagnostics
  - `contracts/intake/idea_gate_decision_schema.yaml`, `qualification_scorecard_schema.yaml` -- Idea intake schemas

### `runtime/`

- **Purpose**: Python runtime engine providing deterministic state machines, contract validation, review orchestration, and CLI entry points
- **Contains**: CLI scripts (`bin/`), command wrappers (`scripts/`), core engine modules (`tools/`), session hooks (`hooks/`)
- **Key files**:
  - `runtime/bin/qros-session` -- Unified research session entry point
  - `runtime/bin/qros-review` -- Stage review entry point
  - `runtime/bin/qros-progress` -- Read-only progress viewer
  - `runtime/bin/qros-update` -- Version update command
  - `runtime/bin/qros-factor-diagnostics` -- CSF factor diagnostics
  - `runtime/bin/qros-signal-diagnostics` -- TSS signal diagnostics
  - `runtime/bin/qros-validate-stage` -- Stage artifact validation
  - `runtime/bin/qros-wrapper-lib` -- Shared wrapper library
  - `runtime/tools/research_session.py` -- Central session orchestrator (5346 lines), stage detection, skill dispatch
  - `runtime/tools/stage_evaluator.py` -- Stage artifact validation engine (902 lines)
  - `runtime/tools/freeze_contract_runtime.py` -- Freeze group validation and SHA256 digest management
  - `runtime/tools/lineage_lock_ledger.py` -- Frozen artifact mutation detection
  - `runtime/tools/stage_entry_guard.py` -- Stage entry authorization (author vs review lane)
  - `runtime/tools/review_skillgen/review_engine.py` -- Core review engine
  - `runtime/tools/review_skillgen/closure_writer.py` -- Review closure artifact writer
  - `runtime/tools/review_skillgen/review_preflight.py` -- Pre-review validation orchestrator
  - `runtime/tools/review_skillgen/upstream_binding_validator.py` -- Route inheritance validation
  - `runtime/tools/review_skillgen/protected_state_guard.py` -- Review state integrity guard
  - `runtime/tools/verification_tiers.py` -- Smoke/full-smoke test tier definitions
  - `runtime/tools/anti_drift.py` -- Anti-drift baseline comparison engine
  - `runtime/tools/anti_drift_scenarios.py` -- Anti-drift scenario definitions
  - `runtime/tools/<stage>_runtime.py` -- Per-stage scaffold functions (18 stage-specific runtimes)
  - `runtime/tools/<stage>_contract_runtime.py` -- Per-stage semantic validation (11 contract runtimes)

### `skills/`

- **Purpose**: Agent behavior bundles that define how AI agents should act during each stage-role combination
- **Contains**: SKILL.md files organized in `<stage>/qros-<role>-<stage>/` directories
- **Key files**:
  - `skills/AGENTS.md` -- Skill editing rules
  - `skills/core/qros-research-session/SKILL.md` -- Unified session entry skill
  - `skills/core/qros-progress/SKILL.md` -- Progress viewing skill
  - `skills/core/qros-update/SKILL.md` -- Version update skill
  - `skills/core/qros-factor-diagnostics/SKILL.md` -- CSF diagnostics skill
  - `skills/core/qros-signal-diagnostics/SKILL.md` -- TSS diagnostics skill
  - `skills/core/qros-stage-display/SKILL.md` -- Stage display skill
  - `skills/core/using-qros/SKILL.md` -- General QROS usage guide (loaded by session-start hook)
  - `skills/failure_handling/qros-stage-failure-handler/SKILL.md` -- Failure handling dispatch
  - `skills/failure_handling/qros-lineage-change-control/SKILL.md` -- Child lineage creation
  - `skills/failure_handling/qros-shadow-failure/SKILL.md` -- Shadow failure analysis

### `tests/`

- **Purpose**: 999 pytest tests covering all runtime behavior, contract compliance, and anti-drift regression
- **Contains**: pytest modules organized by concern
- **Key files**:
  - `tests/session/test_research_session_runtime.py` -- Session orchestration tests
  - `tests/review/test_stage_evaluator.py` -- Review engine tests
  - `tests/contracts/test_stage_evaluator_contract.py` -- Contract compliance tests
  - `tests/anti_drift/test_anti_drift.py` -- Anti-drift baseline tests
  - `tests/anti_drift/test_anti_drift_metamorphic.py` -- Metamorphic regression tests
  - `tests/bootstrap/test_project_bootstrap.py` -- Project bootstrap tests
  - `tests/skills/test_skill_tree.py` -- Skill tree integrity tests

### `docs/`

- **Purpose**: User-facing documentation, SOPs, guides, and governance docs
- **Contains**: Markdown documents organized by type
- **Key files**:
  - `docs/README.md` -- Documentation navigation hub
  - `docs/guides/installation.md` -- Installation guide
  - `docs/guides/qros-research-session-usage.md` -- Session usage guide
  - `docs/guides/qros-review-constraint-map.md` -- Review constraint reference
  - `docs/guides/stage-freeze-group-field-guide.md` -- Freeze group field reference
  - `docs/guides/qros-factor-diagnostics.md` -- CSF diagnostics guide
  - `docs/guides/qros-signal-diagnostics.md` -- TSS diagnostics guide
  - `docs/sop/main-flow/` -- Research workflow SOP

### `templates/`

- **Purpose**: Host-agnostic skill templates for generating review skills at install time
- **Contains**: Jinja-like template files
- **Key files**: `templates/skills/review-stage/SKILL.md.tmpl`

### `.claude-plugin/`

- **Purpose**: Claude Code plugin distribution. Contains review skills that are loaded into the Claude Code plugin system.
- **Contains**: Agent definitions and host-specific skill copies
- **Key files**: `.claude-plugin/agents/qros-reviewer.md`

### `.codex/`

- **Purpose**: Codex CLI installation instructions
- **Key files**: `.codex/INSTALL.md`

## Key File Locations

### Entry Points

- `runtime/bin/qros-session`: Unified research session CLI
- `runtime/bin/qros-review`: Stage review CLI
- `runtime/bin/qros-progress`: Read-only progress viewer
- `runtime/bin/qros-update`: Version update CLI
- `runtime/bin/qros-validate-stage`: Stage validation CLI
- `runtime/bin/qros-factor-diagnostics`: CSF factor diagnostics CLI
- `runtime/bin/qros-signal-diagnostics`: TSS signal diagnostics CLI
- `runtime/bin/qros-review-cycle`: Review cycle management
- `runtime/bin/qros-start-review`: Review initiation
- `runtime/bin/qros-review-preflight`: Pre-review validation
- `runtime/bin/qros-check-stage-entry`: Stage entry guard
- `runtime/bin/qros-audit-reviewer`: Reviewer audit
- `runtime/bin/qros-agent-eval`: Agent behavior evaluation
- `runtime/bin/qros-resume`: Session resume
- `runtime/bin/qros-verify`: Verification runner
- `runtime/bin/qros-wrapper-lib`: Shared wrapper library

### Configuration

- `pyproject.toml`: Python project metadata, dependencies (PyYAML>=6.0, pyarrow>=20.0), pytest config
- `contracts/stages/workflow_stage_gates.yaml`: Central stage gate definitions
- `contracts/review/review_checklist_master.yaml`: Master review checklist
- `runtime/hooks/hooks.json`: Claude Code session hook configuration
- `runtime/tools/verification_tiers.py`: Smoke/full-smoke test tier definitions

### Core Logic

- `runtime/tools/research_session.py`: Central session orchestrator (5346 lines)
- `runtime/tools/stage_evaluator.py`: Stage artifact validation (902 lines)
- `runtime/tools/freeze_contract_runtime.py`: Freeze group management
- `runtime/tools/lineage_lock_ledger.py`: Frozen artifact mutation detection
- `runtime/tools/stage_entry_guard.py`: Stage entry authorization
- `runtime/tools/review_skillgen/review_engine.py`: Review engine core
- `runtime/tools/review_skillgen/closure_writer.py`: Review closure writer
- `runtime/tools/review_skillgen/review_preflight.py`: Pre-review validation
- `runtime/tools/lineage_program_runtime.py`: Lineage-local program validation
- `runtime/tools/artifact_contract_runtime.py`: Artifact contract validation
- `runtime/tools/author_context_runtime.py`: Author context building
- `runtime/tools/install_runtime.py`: Installation logic
- `runtime/tools/update_runtime.py`: Version update logic
- `runtime/tools/progress_runtime.py`: Progress display logic

### Testing

- `tests/session/`: Session orchestration tests
- `tests/review/`: Review engine tests
- `tests/contracts/`: Contract compliance tests
- `tests/anti_drift/`: Anti-drift regression tests
- `tests/skills/`: Skill tree integrity tests
- `tests/runtime/`: Runtime tool tests
- `tests/pipeline/`: End-to-end pipeline tests
- `tests/e2e/`: End-to-end integration tests
- `tests/bootstrap/`: Project bootstrap tests
- `tests/docs/`: Documentation regression tests
- `tests/agent_eval/`: Agent behavior evaluation tests

## Naming Conventions

### Files

- **Stage-specific runtimes**: `<stage>_runtime.py` (e.g., `tss_data_ready_runtime.py`, `csf_signal_ready_runtime.py`)
- **Stage-specific contract runtimes**: `<stage>_contract_runtime.py` (e.g., `tss_test_evidence_contract_runtime.py`)
- **Artifact schemas**: `<stage>_artifacts.yaml` (e.g., `csf_backtest_ready_artifacts.yaml`)
- **Skill directories**: `qros-<stage>-<role>` (e.g., `qros-tss-test-evidence-author`, `qros-csf-signal-ready-review`)
- **CLI entry points**: `qros-<command>` (e.g., `qros-session`, `qros-review`, `qros-update`)
- **Script wrappers**: `run_<command>.py` or `<action>_<noun>.py` (e.g., `run_research_session.py`, `build_anti_drift_gate_summary.py`)

### Directories

- **Stage directories in consumer repos**: `<nn>_<stage>` with zero-padded number (e.g., `02_tss_data_ready`, `05_csf_test_evidence`)
- **Skill bundles**: `<stage>/qros-<stage>-<role>/` where role is `author`, `review`, or `failure`
- **Route prefixes**: `tss_` for time_series_signal, `csf_` for cross_sectional_factor
- **Test directories**: lowercase snake_case matching the concern area (e.g., `anti_drift`, `agent_eval`)

### Stage Keys

- `idea_intake` -- no prefix, no route
- `mandate` -- no prefix, route-neutral
- `tss_data_ready`, `tss_signal_ready`, `tss_train_freeze`, `tss_test_evidence`, `tss_backtest_ready`, `tss_holdout_validation` -- time_series_signal route
- `csf_data_ready`, `csf_signal_ready`, `csf_train_freeze`, `csf_test_evidence`, `csf_backtest_ready`, `csf_holdout_validation` -- cross_sectional_factor route
- Legacy unprefixed stages (`data_ready`, `signal_ready`, `train_calibration`, `test_evidence`, `backtest_ready`, `holdout_validation`) -- original time_series_signal route

## Where to Add New Code

### New Stage (e.g., adding `regime_filter` stage)

1. **Contract definition**: Add stage entry to `contracts/stages/workflow_stage_gates.yaml`
2. **Artifact schema**: Create `contracts/artifacts/<stage>_artifacts.yaml`
3. **Runtime scaffold**: Create `runtime/tools/<stage>_runtime.py` with `scaffold_<stage>()` and freeze group constants
4. **Runtime contract validation**: Create `runtime/tools/<stage>_contract_runtime.py` with `validate_<stage>_semantics()`
5. **Session integration**: Update `runtime/tools/research_session.py` stage mappings and `STAGE_ACTIVE_SKILLS`
6. **Stage evaluator**: Update `runtime/tools/stage_evaluator.py` required outputs
7. **Skills**: Create `skills/<stage>/qros-<stage>-author/SKILL.md`, `skills/<stage>/qros-<stage>-review/SKILL.md`, optionally `skills/<stage>/qros-<stage>-failure/SKILL.md`
8. **Template**: Update `templates/skills/review-stage/SKILL.md.tmpl` if review behavior changes
9. **Tests**: Add tests in `tests/session/`, `tests/review/`, `tests/contracts/`, `tests/anti_drift/`

### New Route (e.g., adding `portfolio_optimization` route)

1. **Contract**: Add route entries to `contracts/stages/workflow_stage_gates.yaml` with new prefix (e.g., `po_`)
2. **Artifact schemas**: Create `contracts/artifacts/po_<stage>_artifacts.yaml` for each stage
3. **Diagnostic profiles**: Create `contracts/diagnostics/po_stage_diagnostic_profiles.yaml` and `po_metric_library.yaml`
4. **Runtime**: Create `runtime/tools/po_<stage>_runtime.py` and `runtime/tools/po_<stage>_contract_runtime.py` for each stage
5. **Skills**: Create `skills/po_<stage>/` directories with author, review, and failure skills
6. **Session routing**: Update `runtime/tools/research_session.py` route dispatch logic
7. **Tests**: Comprehensive new test directories mirroring existing route tests

### New CLI Command

1. **Script**: Create `runtime/scripts/run_<command>.py`
2. **Bin entry**: Create `runtime/bin/qros-<command>` that delegates to the script
3. **Core skill** (if agent-facing): Create `skills/core/qros-<command>/SKILL.md`
4. **Tests**: Add tests in appropriate `tests/` subdirectory

### New Diagnostic Profile

1. **Metric library**: Add metrics to `contracts/diagnostics/<route>_metric_library.yaml`
2. **Diagnostic profile**: Add stage profile to `contracts/diagnostics/<route>_stage_diagnostic_profiles.yaml`
3. **Runtime**: Update `runtime/tools/factor_diagnostics.py` or `runtime/tools/signal_diagnostics.py`
4. **Tests**: Add tests in `tests/runtime/`

### New Utility / Shared Helper

- **Runtime helpers**: Place in `runtime/tools/` as `<descriptive_name>.py`
- **Test helpers**: Place in `tests/helpers/`
- **Test fixtures**: Place in `tests/fixtures/`

## Special Directories

### `.claude-plugin/`

- **Purpose**: Claude Code plugin distribution with host-specific review skills and agent definitions
- **Generated**: Partially -- review skill SKILL.md files are generated from templates during `qros-update`
- **Committed**: Yes

### `.codex/`

- **Purpose**: Codex CLI installation instructions
- **Generated**: No
- **Committed**: Yes

### `.planning/`

- **Purpose**: Project planning documents, phases, and codebase analysis
- **Generated**: By GSD tooling
- **Committed**: Varies by content

### `.venv/`

- **Purpose**: Python virtual environment
- **Generated**: Yes, by `uv sync`
- **Committed**: No (gitignored)

### `runtime/tools/review_skillgen/`

- **Purpose**: Self-contained review engine subsystem with its own models, validators, and writers
- **Generated**: No
- **Committed**: Yes
- **Note**: This is a package within `runtime/tools/`, not a separate top-level directory

---

*Structure analysis: 2026-05-20*
