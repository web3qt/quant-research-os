<!-- refreshed: 2026-05-20 -->
# Architecture

**Analysis Date:** 2026-05-20

## System Overview

QROS (Quant Research OS) is a stage-gated governance framework for quantitative research workflows. It is a **framework repository** -- not a strategy implementation repository. It provides contracts, runtime tools, agent skills, and verification infrastructure that consumer research repos use to enforce disciplined freeze/review/advance workflows.

The system operates across two AI agent hosts (Codex CLI and Claude Code), with a Python runtime providing deterministic state machines, contract validation, and orchestration.

```text
┌─────────────────────────────────────────────────────────────────────┐
│                     Agent Host Layer                                 │
│   (Codex CLI / Claude Code)                                         │
│   Skills loaded from: skills/  or  ~/.codex/skills/ or plugin       │
├──────────┬──────────────────┬────────────────┬───────────────────────┤
│  Author  │    Review        │   Failure      │    Core               │
│  Skills  │    Skills        │   Handling     │    Utilities          │
│ skills/  │    skills/       │   skills/      │    skills/core/       │
│ <stage>/ │    <stage>/      │   failure_     │                       │
│ *author/ │    *-review/     │   handling/    │                       │
├──────────┴──────────────────┴────────────────┴───────────────────────┤
│                     Runtime Layer (Python)                           │
├──────────┬──────────────────┬────────────────┬───────────────────────┤
│  bin/    │   scripts/       │   tools/       │    hooks/             │
│  CLI     │   wrappers &     │   engine &     │    session-start      │
│  entries │   task runners   │   scaffolds    │    hook               │
├──────────┴──────────────────┴────────────────┴───────────────────────┤
│                     Contract Layer (YAML/JSON)                       │
├──────────┬──────────────────┬────────────────┬───────────────────────┤
│  stages/ │   artifacts/     │   review/      │   diagnostics/        │
│  gates   │   schemas        │   checklists   │   profiles & metrics  │
├──────────┴──────────────────┴────────────────┴───────────────────────┤
│                     Consumer Research Repo                           │
│   outputs/<lineage_id>/  -- disk truth for stage artifacts           │
│   program/               -- lineage-local stage programs             │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | Key Files |
|-----------|----------------|-----------|
| `contracts/` | Machine-readable truth: gate definitions, artifact schemas, review checklists, diagnostic profiles | `contracts/stages/workflow_stage_gates.yaml`, `contracts/artifacts/*.yaml`, `contracts/review/review_checklist_master.yaml` |
| `runtime/bin/` | Stable CLI entry points exposed to agents and users | `runtime/bin/qros-session`, `runtime/bin/qros-review`, `runtime/bin/qros-update`, `runtime/bin/qros-progress` |
| `runtime/scripts/` | Command wrappers and deterministic task runners invoked by bin entries | `runtime/scripts/run_research_session.py`, `runtime/scripts/run_verification_tier.py` |
| `runtime/tools/` | Core engine: freeze contracts, stage evaluation, review engine, scaffolding, anti-drift | `runtime/tools/research_session.py`, `runtime/tools/stage_evaluator.py`, `runtime/tools/freeze_contract_runtime.py` |
| `runtime/tools/review_skillgen/` | Review engine subsystem: adversarial review, closure writing, upstream binding, preflight checks | `runtime/tools/review_skillgen/review_engine.py`, `runtime/tools/review_skillgen/closure_writer.py` |
| `skills/` | Agent behavior bundles: 56+ skill bundles for author, review, and failure handling per stage | `skills/core/qros-research-session/SKILL.md`, `skills/<stage>/qros-*-author/SKILL.md` |
| `templates/` | Host-agnostic review skill template generator | `templates/skills/review-stage/SKILL.md.tmpl` |
| `tests/` | 999 pytest tests across 12 test directories | `tests/session/`, `tests/review/`, `tests/contracts/`, `tests/anti_drift/` |
| `docs/` | SOPs, guides, visuals, governance documentation | `docs/guides/`, `docs/sop/`, `docs/governance/` |
| `.claude-plugin/` | Claude Code plugin distribution: skills + reviewer agent | `.claude-plugin/agents/qros-reviewer.md`, `.claude-plugin/skills/` |
| `.codex/` | Codex CLI installation instructions | `.codex/INSTALL.md` |

## Pattern Overview

**Overall:** Contract-first, stage-gated pipeline with freeze/review/advance semantics.

**Key Characteristics:**
- **Contract-first**: All stage gates, freeze groups, artifact expectations, and review checklists are defined as machine-readable YAML/JSON before implementation
- **Disk is truth**: Stage completion is verified by actual files on disk in `outputs/<lineage_id>/`, not by agent claims
- **Freeze before build**: Each stage freezes inputs before producing outputs; frozen artifacts get SHA256 digests recorded in the lineage lock ledger
- **Review before advance**: Independent adversarial review is required; author cannot self-review
- **Failure is a route**: Non-normal review verdicts (FIX_REQUIRED, RETRY, NO-GO, CHILD LINEAGE) route to failure handling rather than continuing the pipeline
- **Dual-host**: Skills are installed into either Codex (`~/.codex/skills/`) or Claude Code (`.claude-plugin/skills/`) with the same source

## Layers

### Contract Layer

- **Purpose**: Define the machine-readable truth for stage gates, artifact schemas, verdict vocabularies, and review checklists
- **Location**: `contracts/`
- **Contains**: YAML gate definitions, JSON schemas, YAML artifact manifests, diagnostic profiles
- **Depends on**: Nothing (this is the source of truth)
- **Used by**: Runtime tools, review engine, stage evaluator, skills, tests

### Runtime Layer

- **Purpose**: Deterministic state machine, contract validation, freeze management, review orchestration, and CLI entry points
- **Location**: `runtime/`
- **Contains**: Python modules (`tools/*.py`), CLI scripts (`bin/*`), command wrappers (`scripts/*.py`), session hooks (`hooks/`)
- **Depends on**: `contracts/` (reads gate definitions, schemas), `pyyaml`, `pyarrow`
- **Used by**: Agent skills invoke runtime scripts and tools; tests verify runtime behavior

### Skills Layer

- **Purpose**: Agent behavior definitions organized by stage and role (author, review, failure)
- **Location**: `skills/`
- **Contains**: SKILL.md files with YAML frontmatter, organized in `<stage>/qros-<role>-<stage>/` directories
- **Depends on**: `contracts/` (references gate definitions), `runtime/` (invokes scripts/tools)
- **Used by**: Codex and Claude Code load skills to determine agent behavior during research sessions

### Test Layer

- **Purpose**: Verification of all runtime behavior, contract compliance, skill tree integrity, and anti-drift regression
- **Location**: `tests/`
- **Contains**: pytest test modules organized by concern (session, review, contracts, anti_drift, skills, docs, etc.)
- **Depends on**: All layers
- **Used by**: CI, developers running `python -m pytest` or `python runtime/scripts/run_verification_tier.py --tier smoke`

## Data Flow

### Primary Research Session Flow

1. User invokes `qros-research-session` via agent host (`runtime/bin/qros-session`)
2. `runtime/scripts/run_research_session.py` detects or creates a lineage in the active research repo
3. `runtime/tools/research_session.py` (`detect_session_stage`) identifies the current stage and active skill
4. Agent executes the stage-specific author skill (e.g., `skills/tss_data_ready/qros-tss-data-ready-author/SKILL.md`)
5. Author produces artifacts in `outputs/<lineage_id>/<stage_dir>/`
6. Review preflight runs: `runtime/tools/review_skillgen/review_preflight.py` validates structural gates, metric gates, upstream bindings, and lineage locks
7. Adversarial review skill executes: `runtime/tools/review_skillgen/review_engine.py` drives the review process
8. Review closure writes verdict: `runtime/tools/review_skillgen/closure_writer.py` outputs review pack and completion certificate
9. If verdict is normal (PASS/CONDITIONAL PASS), `runtime/tools/research_session.py` advances to next stage
10. If verdict is non-normal, failure handling skill activates (`skills/failure_handling/qros-stage-failure-handler/SKILL.md`)

### Freeze Group Flow

1. Stage scaffold generates freeze draft (`runtime/tools/<stage>_runtime.py` -- e.g., `scaffold_tss_data_ready()`)
2. Freeze draft written to `<stage_dir>/<stage>_freeze_draft.yaml`
3. Agent confirms each freeze group interactively
4. `runtime/tools/freeze_contract_runtime.py` validates completeness and computes SHA256 digest
5. Upon review PASS, frozen artifacts are recorded in `lineage_lock_ledger.yaml`
6. `runtime/tools/lineage_lock_ledger.py` (`assert_lineage_locks_intact`) prevents downstream mutation of locked artifacts

### Review Preflight Flow

1. `runtime/tools/review_skillgen/review_preflight.py` called before review starts
2. Loads gate schema from `contracts/stages/workflow_stage_gates.yaml`
3. Loads checklist from `contracts/review/review_checklist_master.yaml`
4. Checks required outputs exist on disk
5. Checks structural gates (field non-empty, enum values, unique keys)
6. Checks metric gates (threshold comparisons on artifact data)
7. Validates upstream bindings (route inheritance, frozen artifact digestion)
8. Validates lineage-local stage program existence and provenance
9. Asserts lineage locks intact (no mutated frozen artifacts)
10. Returns preflight result; review proceeds only if all blocking checks pass

**State Management:**
- Stage state tracked in `outputs/<lineage_id>/` directory structure on disk
- Lineage lock ledger (`lineage_lock_ledger.yaml`) records SHA256 digests of frozen artifacts
- Review runtime state written to `review_runtime_state.yaml` during active review
- Session stage detection reads disk state, not in-memory state

## Key Abstractions

### Stage Gate Contract

- **Purpose**: Defines what a stage requires (inputs, outputs, formal gate rules, verdict vocabulary, rollback rules, downstream permissions)
- **Examples**: `contracts/stages/workflow_stage_gates.yaml` (lines 198-2326 define all 20 stages)
- **Pattern**: Each stage has `pass_all_of`, `fail_any_of`, `verdict_rules`, `rollback_rules`, `downstream_permissions`, and optional `structural_gate_checks` / `metric_gate_checks`

### Freeze Group

- **Purpose**: Groups of fields that must be frozen (confirmed + SHA256 digest) before proceeding
- **Examples**: `runtime/tools/freeze_contract_runtime.py`, `runtime/tools/tss_data_ready_runtime.py` (`TSS_DATA_READY_FREEZE_GROUP_ORDER`)
- **Pattern**: Each stage defines a tuple of freeze group names and a draft file name; scaffold writes draft, agent confirms, runtime validates digest

### Skill Bundle

- **Purpose**: A single agent behavior definition for one stage-role combination
- **Examples**: `skills/tss_test_evidence/qros-tss-test-evidence-author/SKILL.md`
- **Pattern**: SKILL.md with YAML frontmatter (`name`, `description`) followed by markdown instructions for the agent

### Lineage Lock Ledger

- **Purpose**: Records SHA256 digests of all frozen artifacts to detect unauthorized mutation
- **Examples**: `runtime/tools/lineage_lock_ledger.py`
- **Pattern**: `lineage_lock_ledger.yaml` stores `{lineage_id, stage, path, sha256, lock_reason}` entries; `assert_lineage_locks_intact()` checks current files against recorded digests

### Stage Evaluator

- **Purpose**: Validates that a stage's required outputs exist on disk and meet quality thresholds
- **Examples**: `runtime/tools/stage_evaluator.py`
- **Pattern**: `StageEvaluatorSpec` dataclass defines `required_outputs` per stage; evaluator writes results to `stage_evaluator_results.jsonl`

### Anti-Drift System

- **Purpose**: Metamorphic testing and snapshot-based regression detection across the skill tree
- **Examples**: `runtime/tools/anti_drift.py`, `runtime/tools/anti_drift_scenarios.py`
- **Pattern**: Scenarios defined per route family (mainline, CSF, failure, support); baseline snapshots compared against current output

## Entry Points

### `qros-session` (Unified Research Session)

- **Location**: `runtime/bin/qros-session`
- **Triggers**: User or agent invokes `qros-research-session` skill
- **Responsibilities**: Orchestrates the full research session from idea_intake through holdout_validation review, detecting current stage, loading appropriate skill, and managing stage transitions

### `qros-review` (Stage Review)

- **Location**: `runtime/bin/qros-review`
- **Triggers**: User invokes review explicitly or as part of session flow
- **Responsibilities**: Runs adversarial review preflight, loads checklist and gate schema, validates artifacts, and produces review closure

### `qros-progress` (Progress Viewer)

- **Location**: `runtime/bin/qros-progress`
- **Triggers**: User asks for current lineage status
- **Responsibilities**: Read-only display of current stage, lineage state, and review history

### `qros-update` (Version Update)

- **Location**: `runtime/bin/qros-update`
- **Triggers**: User runs `qros-update` in an active research repo
- **Responsibilities**: Detects current host (Codex or Claude Code), refreshes global QROS installation, rebuilds repo-local `./.qros/` runtime

### `qros-validate-stage` (Stage Validation)

- **Location**: `runtime/bin/qros-validate-stage`
- **Triggers**: Agent or user validates current stage artifacts
- **Responsibilities**: Runs stage evaluator, checks required outputs, structural gates, and metric gates

### `qros-factor-diagnostics` / `qros-signal-diagnostics`

- **Location**: `runtime/bin/qros-factor-diagnostics`, `runtime/bin/qros-signal-diagnostics`
- **Triggers**: User asks for factor/signal quality diagnostics
- **Responsibilities**: Reads diagnostic profiles from `contracts/diagnostics/`, evaluates metrics against thresholds

## Architectural Constraints

- **Threading**: Single-threaded Python execution. No concurrency primitives. All state is on disk.
- **Global state**: `runtime/tools/research_session.py` (5346 lines) is the largest module and holds the central session orchestration logic. Module-level constants define stage mappings.
- **Circular imports**: Avoided by having tools import from each other linearly. The review_skillgen package imports from tools but tools do not import from review_skillgen except through the scripts layer.
- **Language**: Python 3.11+ runtime with no async. All I/O is synchronous file reads/writes.
- **Agent- Runtime split**: AI agents (Codex/Claude Code) handle understanding, dialogue, and tool dispatch. Python runtime handles deterministic state machines, contract validation, and file I/O. Neither layer subsumes the other.
- **Host portability**: Skills must work on both Codex CLI and Claude Code. Host-specific adaptations live in `.codex/` and `.claude-plugin/`.

## Anti-Patterns

### Using empty directories or placeholder files as stage completion

**What happens:** An agent creates an empty directory or a file with only a header/title but no actual content, then claims the stage is complete.
**Why it's wrong:** QROS requires actual machine-readable artifacts with real data. The `no_gate_doc_no_completion` and `frozen_inputs_only` global rules explicitly prohibit this.
**Do this instead:** Use `runtime/tools/stage_evaluator.py` to verify required outputs exist with real content, and run `run_verification_tier.py --tier smoke` before claiming completion. Reference: `contracts/stages/workflow_stage_gates.yaml` lines 44-55.

### Skipping the freeze confirmation step

**What happens:** An agent proceeds to artifact generation without confirming freeze groups.
**Why it's wrong:** The freeze-before-build principle requires all inputs to be locked with SHA256 digests before downstream consumption. `runtime/tools/freeze_contract_runtime.py` will reject unconfirmed drafts.
**Do this instead:** Follow the freeze group confirmation flow in `runtime/tools/<stage>_runtime.py` scaffold functions, ensuring each group has `confirmed: true` and a valid `freeze_digest_sha256`.

### Author self-reviewing

**What happens:** The same agent that authored artifacts also performs the review.
**Why it's wrong:** The adversarial review system requires independent reviewers. `runtime/tools/review_skillgen/adversarial_review_contract.py` tracks reviewer identity separately from author identity.
**Do this instead:** Use the review skill bundle (e.g., `skills/<stage>/qros-<stage>-review/SKILL.md`) with a separate agent context, or spawn a review sub-agent via `runtime/bin/qros-review`.

### Using shared builder as completion path

**What happens:** An agent uses the framework's shared scaffold helpers as the sole evidence of stage completion.
**Why it's wrong:** The `no_shared_builder_completion_path` global rule (line 58 of workflow_stage_gates.yaml) explicitly forbids this. Stage completion requires lineage-local stage programs with their own `stage_program.yaml`, entrypoint, README, and `program_execution_manifest.json`.
**Do this instead:** Generate lineage-local programs in `outputs/<lineage_id>/program/<stage>/` using `runtime/tools/stage_program_scaffold.py` specs.

## Error Handling

**Strategy:** Errors are categorized as configuration errors (missing setup), validation errors (contract violations), and mutation errors (frozen artifact changes). Each has a distinct error type and recovery path.

**Patterns:**
- `StageEvaluatorConfigurationError` -- missing or misconfigured stage evaluator setup; user-facing CLI message with actionable fix
- `FrozenArtifactMutationError` -- a locked artifact was modified; includes expected/observed SHA256 and recovery command to restore or open child lineage (`runtime/tools/lineage_lock_ledger.py`)
- `ProtectedStateError` -- review state was corrupted or tampered with during active review (`runtime/tools/review_skillgen/protected_state_guard.py`)
- `StageProgramRuntimeError` -- lineage-local stage program missing or invalid (`runtime/tools/lineage_program_runtime.py`)
- `ArtifactContractError` -- artifact schema mismatch (`runtime/tools/artifact_contract_runtime.py`)
- Review verdicts that are not normal PASS route to failure handling skills rather than raising exceptions

## Cross-Cutting Concerns

**Logging:** Python standard library only. No structured logging framework. Runtime tools print to stdout/stderr for CLI consumption. Chinese-language comments preferred for maintainer-facing documentation in `runtime/tools/` and `runtime/scripts/`.

**Validation:** Multi-layered: (1) freeze contract validation on draft confirmation, (2) structural gate checks on field presence/enums/uniqueness, (3) metric gate checks on numeric thresholds, (4) upstream binding validation on route inheritance, (5) anti-drift metamorphic testing for regression.

**Authentication:** Not applicable within the framework. QROS operates on local filesystem state in consumer research repos. Agent host identity (Codex vs Claude Code) is detected by installer and hook scripts.

---

*Architecture analysis: 2026-05-20*
