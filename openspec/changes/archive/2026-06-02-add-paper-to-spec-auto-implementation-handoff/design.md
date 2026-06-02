## Context

`qros-paper-to-spec` is currently a data-spec-first PaperSpec authoring entrypoint. It generates staged `paper_*_spec.yaml` artifacts and stops at `paper_backtest_implementation_spec.yaml`, which is still an implementation plan rather than live research code.

The requested behavior adds a post-spec decision point: once the staged specs are valid, the skill should ask whether to automatically implement from those specs. If the researcher chooses implementation, the data layer must be handled first: QROS must list required datasets and ask whether the researcher can provide them before any agent-driven acquisition.

## Goals / Non-Goals

**Goals:**

- Add an explicit end-of-run implementation prompt after the requested PaperSpec chain is valid.
- Make implementation opt-in; no implementation, scaffold generation, data download, or active repo write happens silently.
- Add a data readiness brief before implementation that tells the researcher exactly which data is required and optional.
- Allow agent-driven data acquisition only after the researcher confirms they cannot provide required data.
- Keep implementation artifacts, data snapshots, downloaded files, and live lineage work in the active research repo.
- Make the handoff testable through deterministic docs, skill rules, and preferably a machine-readable handoff artifact contract.

**Non-Goals:**

- Do not change `qros-research-session` stage flow, review orchestration, route split, or failure handling.
- Do not make the QROS framework repo store live strategy programs or formal research outputs.
- Do not bypass PaperSpec validators.
- Do not guarantee external data availability or silently substitute data sources.
- Do not generate implementation code during OpenSpec proposal work.

## Decisions

### Decision 1: Add a post-spec implementation gate, not implicit implementation

After all requested `paper_*_spec.yaml` artifacts are generated and validated, `qros-paper-to-spec` should present a clear prompt:

```text
All requested PaperSpec artifacts are valid.
Do you want QROS to automatically implement from these specs in the active research repo?
```

Rationale: The current skill is intentionally specification-focused. An explicit gate preserves that boundary while giving the researcher a natural next step.

Alternative considered: Automatically implement whenever `paper_backtest_implementation_spec.yaml` recommends `generate_active_repo_backtest_scaffold`. Rejected because it would turn a planning artifact into side-effectful execution without researcher consent.

### Decision 2: Require a data readiness brief before implementation

If the researcher opts in, the next output should be a Data Readiness Brief derived from `paper_data_spec.yaml`, downstream specs, and `paper_backtest_implementation_spec.yaml`. The brief should list:

- required datasets
- optional datasets
- market and venue scope
- symbols/universe
- bar cadence and time range
- required fields
- expected formats
- provenance requirements
- missing-data policy
- whether the researcher can provide each dataset

Rationale: Data availability is the earliest practical implementation blocker. Surfacing it first prevents the agent from writing implementation plans around unavailable inputs.

Alternative considered: Let the implementation scaffold discover missing data later. Rejected because it pushes a known data dependency into runtime failure and encourages ad hoc substitutions.

### Decision 3: Make researcher-provided data the first path

The handoff should ask whether the researcher can provide the listed datasets. If yes, QROS should collect paths, snapshots, credentials, or access instructions and validate that the provided data matches the spec requirements before implementation.

Rationale: In quant research, local curated data is often more authoritative than newly downloaded public data. User-provided data must be preferred when available.

Alternative considered: Always let the agent download data. Rejected because it may fetch the wrong exchange, settlement, symbol universe, time range, or adjusted field semantics.

### Decision 4: Permit agent acquisition only with an acquisition plan and provenance

If the researcher cannot provide data, QROS may attempt acquisition only after presenting a plan that includes source, requested time range, symbols, expected fields, commands/tools, storage target in the active repo, and known limitations. The acquisition result must record provenance and failures.

Rationale: Agent acquisition can be useful, but it must remain auditable and must not masquerade as verified user-provided data.

Alternative considered: Treat downloaded data as equivalent to researcher-provided data. Rejected because downloaded data needs source and coverage evidence.

### Decision 5: Prefer a machine-readable handoff artifact

The implementation should consider adding a contract-backed artifact such as:

```text
outputs/paper_to_spec/<paper_slug>/paper_auto_implementation_handoff.yaml
```

This artifact would record the implementation decision, data readiness brief, researcher data response, agent acquisition plan, acquisition provenance, and allowed next action.

Rationale: QROS already treats machine-readable artifacts as the truth layer. A handoff artifact makes the prompt auditable and testable instead of depending on chat history.

Alternative considered: Only update the skill text. Rejected as insufficiently testable for a workflow boundary with data acquisition side effects.

## Risks / Trade-offs

- Data acquisition may require network access, credentials, or paid APIs -> require explicit researcher confirmation and record failures without fabricating data.
- A new handoff artifact adds schema and validator work -> keep the artifact narrow and focused on the post-spec decision plus data readiness state.
- Users may expect full strategy implementation after saying yes -> wording must clarify this begins active repo implementation/scaffold work and still respects data readiness, no-retune, and repo boundary rules.
- Downloaded data may not match paper assumptions -> validate against `paper_data_spec.yaml` and record coverage gaps as blocking.
- This can overlap with `qros-research-session` governance -> keep this capability scoped to PaperSpec fast-lane handoff and do not claim review closure or stage advancement.
