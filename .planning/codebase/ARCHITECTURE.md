<!-- refreshed: 2026-05-06 -->
# Architecture

**Analysis Date:** 2026-05-06

## System Overview

QROS (Quantitative Research Operating System) is an agentic stage-gated governance framework for quantitative research workflows. It is not a strategy implementation repository; it enforces a rigorous process for turning research ideas into auditable, reproducible, and traceable research lineages.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Agent Host Layer (Codex / Claude Code)               │
│  `.claude-plugin/agents/`  `.claude-plugin/skills/`  `.codex/INSTALL.md`  │
├──────────────┬──────────────────┬───────────────────┬───────────────────────┤
│   Skills     │    Runtime       │   Contracts       │   Templates           │
│  `skills/`   │  `runtime/`      │  `contracts/`     │  `templates/`         │
└──────┬───────┴──────┬───────────┴────────┬──────────┴──────────┬────────────┘
       │              │                    │                     │
       v              v                    v                     v
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Review Skillgen Engine                                   │
│          `runtime/tools/review_skillgen/`                                   │
│  (adversarial review, closure writing, protocol validation, gate checks)    │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    v
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Lineage Output (User Research Repo)                       │
│  `outputs/<lineage_id>/01_mandate/` .. `07_holdout_validation/`             │
│  `outputs/<lineage_id>/program/` (lineage-local stage programs)             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Contracts | Machine-readable truth: stage gates, artifact schemas, review checklists, diagnostic profiles | `contracts/` |
| Skills | Author, review, failure-handling, and orchestrator skill definitions (SKILL.md) for agent hosts | `skills/` |
| Runtime bin | Stable CLI entry points that resolve Python runtime and delegate to scripts | `runtime/bin/` |
| Runtime scripts | CLI wrappers and deterministic task runners invoked by bin | `runtime/scripts/` |
| Runtime tools | Core Python libraries: stage scaffolding, gate validation, review engine, anti-drift, install | `runtime/tools/` |
| Review Skillgen | Review engine: adversarial review contract, closure writer, protocol validator, scope builder | `runtime/tools/review_skillgen/` |
| Templates | Jinja-style skill templates for generated review skills | `templates/skills/` |
| Tests | Multi-layer test suite: contracts, runtime, session, review, anti-drift, e2e | `tests/` |
| Claude Plugin | Claude Code host configuration: reviewer agent definition, review skill bindings | `.claude-plugin/` |
| Docs | SOPs, guides, design specs, visuals | `docs/` |

## Pattern Overview

**Overall:** Contract-Driven Stage-Gated Pipeline with Adversarial Review

**Key Characteristics:**
- All stage definitions, gate rules, and artifact schemas are machine-readable YAML/JSON contracts
- The research pipeline is a directed acyclic graph of stages with explicit freeze/review/advance semantics
- Every stage requires an independent adversarial reviewer before advancing (no self-approval)
- Two parallel research routes exist (time_series_signal and cross_sectional_factor) with route-specific contracts
- Anti-drift regression testing enforces that contract changes are intentional and tracked
- The framework is host-agnostic: supports both Codex and Claude Code via separate but structurally identical skill/install paths

## Layers

**Contract Layer:**
- Purpose: Single source of truth for stage gates, artifact schemas, review checklists, and diagnostic profiles
- Location: `contracts/`
- Contains: YAML/JSON schema definitions for all stages, artifact contracts, intake schemas, review master checklist
- Depends on: Nothing (leaf layer)
- Used by: Runtime tools, review engine, anti-drift, skill generation, tests

**Skill Layer:**
- Purpose: Agent-readable instructions for authoring, reviewing, and handling failures at each stage
- Location: `skills/`
- Contains: SKILL.md files organized by stage domain (idea_intake, mandate, csf_*, tss_*, backtest_ready, etc.)
- Depends on: Contract layer (references contract paths in skill instructions)
- Used by: Agent hosts (Codex via `.codex/`, Claude Code via `.claude-plugin/`)

**Runtime Layer:**
- Purpose: Python tooling that enforces contracts, scaffolds stages, runs reviews, validates artifacts
- Location: `runtime/`
- Contains: bin (shell entry points), scripts (CLI wrappers), tools (Python libraries)
- Depends on: Contract layer (loads and validates YAML/JSON schemas)
- Used by: Agent hosts, CI/CD pipeline, CLI users

**Template Layer:**
- Purpose: Template files for generating stage-specific review skills
- Location: `templates/skills/`
- Contains: `SKILL.md.tmpl` with Jinja-style placeholders
- Depends on: Contract layer (templates reference stage contract data)
- Used by: `runtime/scripts/gen_stage_review_skills.py`

**Test Layer:**
- Purpose: Multi-layer test suite ensuring contract integrity, runtime correctness, and anti-drift
- Location: `tests/`
- Contains: Contract tests, runtime tests, session tests, review tests, anti-drift tests, e2e tests
- Depends on: All layers above
- Used by: CI/CD pipeline, developers

## Data Flow

### Primary Research Session Path

1. **Entry** -- User invokes `$qros-research-session` in their research repo (`runtime/bin/qros-session` shell script)
2. **Runtime resolution** -- Shell script locates Python >=3.11, resolves runtime root, invokes `runtime/scripts/run_research_session.py` (`runtime/bin/qros-session:85-88`)
3. **Session orchestration** -- `run_research_session.py` calls `runtime/tools/research_session.py` which manages the stage lifecycle, routing between TSS and CSF branches
4. **Stage scaffolding** -- For each stage, the research session calls stage-specific scaffold functions (e.g., `scaffold_csf_data_ready()` from `runtime/tools/csf_data_ready_runtime.py`)
5. **Artifact production** -- Agent produces formal artifacts in `outputs/<lineage_id>/<stage_dir>/author/formal/`
6. **Review invocation** -- `runtime/bin/qros-review` delegates to `runtime/scripts/run_stage_review.py` which calls `runtime/tools/review_skillgen/review_engine.py`
7. **Gate evaluation** -- `review_engine.py` loads contracts via `runtime/tools/review_skillgen/loaders.py`, validates protocol via `protocol_validator.py`, checks structural gates via `stage_content_gate.py`, validates upstream bindings via `upstream_binding_validator.py`
8. **Closure writing** -- `runtime/tools/review_skillgen/closure_writer.py` produces stage_evaluator.json and closure artifacts
9. **Stage advancement** -- `runtime/tools/stage_evaluator.py` reads the evaluator result and determines if the lineage can progress

### Review Cycle Path

1. **Prepare** -- `qros-review-cycle prepare` registers active review cycle, writes `review/request/*` and `reviewer_receipt.yaml`
2. **Handoff** -- Main thread spawns independent reviewer sub-agent and delivers handoff manifest
3. **Review execution** -- Reviewer reads `review/request/*` and `author/formal/*`, writes `review/result/reviewer_findings.raw.yaml`
4. **Closure** -- `qros-review` runs canonical result validation, audit, and closure artifact generation
5. **Result** -- Verdict (PASS, CONDITIONAL PASS, FIX_REQUIRED, etc.) written to `review/result/`

### Anti-Drift Path

1. **Snapshot export** -- `runtime/scripts/export_anti_drift_snapshots.py` captures current contract state
2. **Baseline compare** -- `runtime/scripts/anti_drift_baseline.py` compares against blessed snapshots in `tests/fixtures/anti_drift/`
3. **Generator freshness** -- `runtime/scripts/gen_stage_review_skills.py --dry-run` verifies generated skills match source
4. **Gate summary** -- `runtime/scripts/build_anti_drift_gate_summary.py` produces CI gate decision
5. **Release artifact** -- `runtime/scripts/build_anti_drift_release_artifact.py` produces release artifact for tagging

**State Management:**
- QROS is stateless between invocations. State lives in the user's research repo under `outputs/<lineage_id>/`
- Stage status is determined by file presence: `review/result/adversarial_review_result.yaml`, `stage_evaluator.json`, etc.
- Review cycle state is tracked in `review/request/` and `review/result/` directories within each stage
- No database, no daemon, no server. Pure filesystem-based state machine.

## Key Abstractions

**Stage Gate Contract:**
- Purpose: Machine-readable definition of every research stage including required inputs, required outputs, formal gate rules, verdict rules, rollback rules, and downstream permissions
- Examples: `contracts/stages/workflow_stage_gates.yaml`
- Pattern: YAML schema with `stages.<stage_id>` structure containing `formal_gate.pass_all_of`, `formal_gate.fail_any_of`, `verdict_rules`, `structural_gate_checks`, `metric_gate_checks`

**Artifact Contract:**
- Purpose: Schema definition for each stage's required artifacts with type, required sections, and field validation
- Examples: `contracts/artifacts/mandate_artifacts.yaml`, `contracts/artifacts/csf_data_ready_artifacts.yaml`
- Pattern: YAML with `artifacts.<filename>.type`, `artifacts.<filename>.required_sections`, `artifacts.<filename>.fields`

**Adversarial Review Contract:**
- Purpose: Defines the protocol for independent review including request/result schemas, verdict vocabulary, and write-scope isolation
- Examples: `runtime/tools/review_skillgen/adversarial_review_contract.py`
- Pattern: Python dataclasses and constants defining `FIX_REQUIRED`, `CLOSURE_READY_*` outcomes, allowed hosts, context isolation policies

**Stage Evaluator Result:**
- Purpose: JSON schema for the output of stage gate evaluation
- Examples: `contracts/stages/stage_evaluator.schema.json`
- Pattern: JSON Schema with `pass`, `can_progress`, `status`, `review_summary`, `required_outputs_checked`

**Lineage Program Contract:**
- Purpose: Defines the invariant that freeze approval must precede lineage-local program execution, which must precede artifact build, which must precede review closure
- Examples: `contracts/stages/workflow_stage_gates.yaml` (lineage_program_contract section)
- Pattern: Mapping of stage keys to program directories and provenance targets

## Entry Points

**`runtime/bin/qros-session` (primary user entry):**
- Location: `runtime/bin/qros-session`
- Triggers: User invokes `$qros-research-session` from within a research repo
- Responsibilities: Resolves Python runtime, locates framework source, delegates to `run_research_session.py`

**`runtime/bin/qros-review` (review execution):**
- Location: `runtime/bin/qros-review`
- Triggers: After adversarial reviewer completes findings
- Responsibilities: Validates protocol, writes closure artifacts, runs stage evaluator

**`runtime/bin/qros-update` (framework update):**
- Location: `runtime/bin/qros-update`
- Triggers: User invokes `$qros-update` to pull latest framework changes
- Responsibilities: Re-installs runtime assets, refreshes installed skills

**`runtime/bin/qros-progress` (read-only progress query):**
- Location: `runtime/bin/qros-progress`
- Triggers: User invokes `$qros-progress` to check current lineage status
- Responsibilities: Reads outputs, returns current stage, gate status, blocking reasons

**`runtime/bin/qros-validate-stage` (deterministic preflight):**
- Location: `runtime/bin/qros-validate-stage`
- Triggers: Before review entry
- Responsibilities: Validates artifact contract compliance, semantic validation, upstream bindings

**`runtime/bin/qros-factor-diagnostics` / `qros-signal-diagnostics` (optional diagnostics):**
- Location: `runtime/bin/qros-factor-diagnostics`, `runtime/bin/qros-signal-diagnostics`
- Triggers: User invokes for quality assessment without review
- Responsibilities: Reads stage outputs, produces diagnostic summaries

## Architectural Constraints

- **Threading:** Single-threaded Python execution. No async, no threading, no multiprocessing in the framework. Each CLI invocation is a single process.
- **Global state:** No module-level mutable singletons. `ROOT = Path(__file__).resolve().parents[N]` constants are used for path resolution but are immutable. Session state lives entirely in the user's filesystem under `outputs/<lineage_id>/`.
- **Circular imports:** The `review_skillgen/` package has an `__init__.py` that is intentionally minimal (empty or near-empty). Circular dependencies are avoided by having `review_engine.py` import from sibling modules, never the reverse. `stage_evaluator.py` imports from `review_skillgen/` but not vice versa.
- **Python version:** Requires Python >=3.11 (enforced by shell entry point selectors in `runtime/bin/` scripts)
- **Dependencies:** Minimal -- only `PyYAML` and `pyarrow` as runtime dependencies. `pytest` is dev-only.
- **Host compatibility:** Framework must work identically under Codex (OpenAI) and Claude Code (Anthropic). Host-specific behavior is isolated in `_HOST_CONFIG` dictionaries and `HOST_VARS` mappings.

## Anti-Patterns

### Self-Approval in Review

**What happens:** The author agent runs review on its own artifacts without spawning an independent reviewer sub-agent.
**Why it's wrong:** Violates the adversarial review invariant. The whole point of QROS is independent verification.
**Do this instead:** Always use `spawn_agent` (Codex) or task creation (Claude Code) to spawn an isolated reviewer. See `skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md:26-34`.

### Modifying Frozen Artifacts

**What happens:** Downstream stages re-compute or modify artifacts that were frozen by upstream stages.
**Why it's wrong:** Breaks the provenance chain and invalidates the review closure of upstream stages.
**Do this instead:** If a fundamental change is needed, open a child lineage. See `contracts/stages/workflow_stage_gates.yaml:54-56` (child_lineage_for_material_change rule).

### Bypassing Review for Completion

**What happens:** A stage is marked complete without running `qros-review` and obtaining closure artifacts.
**Why it's wrong:** QROS completion requires formal artifacts, provenance, review closure, and gate semantics all to be satisfied simultaneously.
**Do this instead:** Always run through the full review cycle. See `runtime/tools/stage_evaluator.py` for the canonical completion check.

## Error Handling

**Strategy:** Explicit error classes with actionable messages, not generic exceptions.

**Patterns:**
- `ReviewRuntimeConfigurationError(RuntimeError)` -- raised when review configuration is missing or invalid (`runtime/tools/review_skillgen/review_engine.py:46`)
- `StageEvaluatorConfigurationError(RuntimeError)` -- raised when stage evaluator cannot find required config (`runtime/tools/stage_evaluator.py:33`)
- `StageProgramRuntimeError(ValueError)` -- raised with a `reason_code` for programmatic handling (`runtime/tools/lineage_program_runtime.py:64-68`)
- `InstallError(RuntimeError)` -- raised for install-time failures (`runtime/tools/install_runtime.py:50`)
- `ParquetCheckTimeout(Exception)` -- raised when parquet gate checks exceed timeout (`runtime/tools/review_skillgen/stage_content_gate.py:17-18`)

## Cross-Cutting Concerns

**Logging:** No logging framework. CLI scripts use `print()` to stdout/stderr. Runtime tools return data structures; the calling script handles output formatting.

**Validation:** Multi-layer validation:
- Contract schema validation (YAML/JSON structure)
- Semantic validation (field values, enums, ranges)
- Structural gate checks (file existence, row counts, unique keys)
- Metric gate checks (numeric thresholds, e.g., mean_net_return > 0)
- Upstream binding validation (route inheritance, digest proofs)

**Authentication:** No authentication system. QROS is a local CLI framework. The "adversarial reviewer" is enforced by process isolation (separate agent context), not by authentication.

**Host Abstraction:** The framework abstracts over two agent hosts (Codex and Claude Code) via configuration dictionaries:
- `_HOST_CONFIG` in `install_runtime.py:22-25`
- `HOST_VARS` in `render.py:10-27`
- `HOST_REVIEWER_INVOCATION_KIND`, `HOST_CONTEXT_ISOLATION`, `HOST_HANDOFF_DELIVERY` in `adversarial_review_contract.py:56-67`

---

*Architecture analysis: 2026-05-06*
