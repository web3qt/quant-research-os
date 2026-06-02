## ADDED Requirements

### Requirement: XML field guides explain paper-to-spec contracts

The system SHALL provide an XML field guide for each YAML contract under `contracts/paper_to_spec/`, and each guide MUST explain the corresponding paper-to-spec artifact fields in Chinese without replacing the YAML contract as canonical runtime truth.

#### Scenario: Guide exists for every paper-to-spec contract
- **WHEN** a maintainer inspects `contracts/paper_to_spec/field_guides/`
- **THEN** there is one parseable `.fields.xml` guide for each `paper_*_spec_contract.yaml`

#### Scenario: YAML remains canonical
- **WHEN** a paper-to-spec validator runs
- **THEN** it continues to read the matching `contracts/paper_to_spec/*.yaml` contract as the validation source

### Requirement: XML guides cover contract-defined fields

Each XML field guide SHALL cover the matching YAML contract's required top-level fields, core required fields, optional blocks, and blocking question groups with stable field paths or block identifiers.

#### Scenario: Required fields have guide entries
- **WHEN** parity tests compare a YAML contract with its XML field guide
- **THEN** every required top-level field and every core required field declared by the YAML contract has a corresponding XML guide entry

#### Scenario: Optional blocks and blocking groups have guide entries
- **WHEN** parity tests compare a YAML contract with its XML field guide
- **THEN** every declared optional block and blocking question group has a corresponding XML guide entry

### Requirement: Field explanations are useful to PaperSpec generation

Each XML field guide entry SHALL include non-empty Chinese explanation content for field meaning, why the field matters, fill rules, examples or accepted shapes, common mistakes, and blocking prompts where applicable.

#### Scenario: Agent prepares a data spec
- **WHEN** PaperSpec or `qros-paper-to-spec` prepares to generate `paper_data_spec.yaml`
- **THEN** it can load `paper_data_spec.fields.xml` to understand field meaning, evidence expectations, examples, and blocking questions before writing YAML

#### Scenario: Guide entries prevent source confusion
- **WHEN** a field explanation describes evidence or source requirements
- **THEN** it distinguishes `paper_stated`, `agent_inferred`, `researcher_required`, and `exchange_profile_default` according to the YAML contract enums

### Requirement: Formal paper-to-spec artifacts remain YAML

The system SHALL continue producing formal paper-to-spec outputs as `paper_*_spec.yaml` artifacts, and XML guides MUST NOT be treated as formal research artifacts or validator outputs.

#### Scenario: PaperSpec completes a stage artifact
- **WHEN** PaperSpec or `qros-paper-to-spec` materializes a stage output
- **THEN** the output is the existing `paper_*_spec.yaml` format and can be checked by the existing deterministic validator

#### Scenario: User reads paper-to-spec documentation
- **WHEN** the usage guide describes XML field guides
- **THEN** it explicitly states that XML guides are explanatory generation aids and YAML contracts/artifacts remain canonical
