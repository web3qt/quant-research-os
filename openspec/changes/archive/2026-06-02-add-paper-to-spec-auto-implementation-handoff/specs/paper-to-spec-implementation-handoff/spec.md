## ADDED Requirements

### Requirement: Post-spec implementation prompt
The `qros-paper-to-spec` skill SHALL present an explicit implementation prompt after the requested PaperSpec chain has been generated and validated.

#### Scenario: All requested specs are valid
- **WHEN** `qros-paper-to-spec` completes the requested PaperSpec chain with valid artifacts
- **THEN** the skill SHALL ask whether the researcher wants QROS to automatically implement from the specs in the active research repo

#### Scenario: Specs are not valid
- **WHEN** any requested PaperSpec artifact is missing, invalid, or blocked by strict unknown fields
- **THEN** the skill MUST NOT ask to auto-implement and SHALL surface the blocking spec issues first

### Requirement: Implementation remains opt-in
The system MUST NOT generate implementation code, download data, create active repo scaffolds, or write live lineage artifacts unless the researcher explicitly confirms the post-spec implementation prompt.

#### Scenario: Researcher declines implementation
- **WHEN** the researcher answers no to the implementation prompt
- **THEN** the system SHALL stop after preserving the generated PaperSpec artifacts and SHALL NOT perform implementation or data acquisition actions

#### Scenario: Researcher has not answered
- **WHEN** the implementation prompt has been shown but the researcher has not answered
- **THEN** the system MUST wait for researcher input and MUST NOT infer consent from the existence of valid specs

### Requirement: Data readiness brief precedes implementation
Before implementation begins, the system SHALL produce a data readiness brief derived from the validated PaperSpec artifacts.

#### Scenario: Researcher opts into implementation
- **WHEN** the researcher confirms automatic implementation
- **THEN** the system SHALL first list required data, optional data, market scope, symbol universe, time range, cadence, fields, expected formats, source constraints, provenance needs, and missing-data policy

#### Scenario: Data requirement is ambiguous
- **WHEN** required data scope, fields, time range, source semantics, or missing-data policy are unknown
- **THEN** the system SHALL mark the data readiness item as blocking and ask the researcher for clarification before implementation

### Requirement: Researcher-provided data is preferred
The system SHALL ask whether the researcher can provide the required datasets before attempting agent-driven acquisition.

#### Scenario: Researcher can provide data
- **WHEN** the researcher confirms they can provide required data
- **THEN** the system SHALL collect paths, snapshots, credentials, or access instructions and validate them against the data readiness brief before implementation proceeds

#### Scenario: Provided data is incomplete
- **WHEN** researcher-provided data does not satisfy required fields, coverage, cadence, market scope, or provenance constraints
- **THEN** the system SHALL report the gaps and MUST NOT silently substitute another dataset

### Requirement: Agent data acquisition is controlled and auditable
The system SHALL allow agent-driven data acquisition only after the researcher confirms they cannot provide the required data and approves an acquisition plan.

#### Scenario: Researcher cannot provide data
- **WHEN** the researcher confirms they cannot provide required data
- **THEN** the system SHALL present an acquisition plan including source, symbols, time range, fields, commands or tools, active repo storage target, expected artifacts, and known limitations

#### Scenario: Acquisition plan is not approved
- **WHEN** the acquisition plan has not been approved by the researcher
- **THEN** the system MUST NOT download, materialize, or claim availability of the required data

#### Scenario: Agent acquisition runs
- **WHEN** agent-driven acquisition is approved and executed
- **THEN** the system SHALL record source, command, timestamp, snapshot identity, coverage, validation result, and any failure reason

### Requirement: Handoff state is machine-readable
The system SHALL persist the post-spec implementation decision and data readiness state in a machine-readable artifact in the active research repo.

#### Scenario: Implementation handoff is created
- **WHEN** the post-spec implementation prompt is answered
- **THEN** the system SHALL record the decision, data readiness brief, researcher data response, acquisition plan status, provenance requirements, and allowed next action in an active-repo `paper_auto_implementation_handoff.yaml` or equivalent contract-backed artifact

#### Scenario: Running in the QROS framework repo
- **WHEN** the handoff artifact or data acquisition output would be written under the QROS framework repo
- **THEN** the system MUST block and ask for an active research repo target

### Requirement: PaperSpec boundaries are preserved
The implementation handoff MUST NOT claim review closure, stage advancement, or valid live research outputs merely because specs are valid or data has been acquired.

#### Scenario: Specs are valid and data is available
- **WHEN** PaperSpec artifacts are valid and data readiness is satisfied
- **THEN** the system MAY proceed to active repo implementation only within the explicit handoff boundary and MUST NOT mark QROS governance stages as complete
