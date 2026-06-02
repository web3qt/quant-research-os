## Context

The paper-to-spec fast lane is currently driven by six YAML contracts under `contracts/paper_to_spec/`. Each contract is loaded by a matching deterministic validator in `runtime/tools/paper_*_spec_runtime.py`, and the `qros-paper-to-spec` skill instructs agents to produce staged `paper_*_spec.yaml` artifacts.

The contracts are good machine-readable truth, but they are sparse as user-facing guidance. They define required fields, enums, core fields, optional blocks, field libraries, and blocking groups, but they do not carry rich Chinese field explanations, examples, or common mistakes. That makes PaperSpec-style generation harder for both researcher and agent.

## Goals / Non-Goals

**Goals:**

- Add XML field guides for all six paper-to-spec contracts.
- Keep YAML contracts as canonical runtime truth for validators and artifact shape.
- Give PaperSpec / `qros-paper-to-spec` a structured Chinese explanation layer for field meaning, examples, common mistakes, and blocking guidance.
- Add parity tests so XML guide coverage stays aligned with YAML contracts.
- Update user-facing guide and skill text to describe how the XML guide is used.

**Non-Goals:**

- Do not replace `contracts/paper_to_spec/*.yaml` with XML.
- Do not change the formal artifact format; outputs remain `paper_*_spec.yaml`.
- Do not change stage flow, gate semantics, route split, review orchestration, failure handling, or validators' default contract paths.
- Do not introduce an XML schema dependency or third-party parser.

## Decisions

### Decision: YAML remains canonical, XML is semantic guidance

The YAML contracts remain the only machine-readable validation source consumed by runtime validators. XML field guides live beside them as a PaperSpec-facing semantic layer.

Alternative considered: replace YAML contracts with XML. This was rejected because all six validators, contract tests, runtime tests, fixtures, skill docs, and usage docs currently depend on YAML contract paths and `yaml.safe_load`. Full replacement would increase blast radius without improving deterministic validation.

### Decision: Store guides under `contracts/paper_to_spec/field_guides/`

Each contract gets one guide:

```text
contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml
```

This keeps guides close to the contracts they explain while preserving the distinction between runtime contracts and human/agent guidance.

Alternative considered: put guides only in `docs/`. This was rejected because docs-only placement makes parity testing and skill discovery less direct.

### Decision: Use a small stable XML vocabulary

The guide vocabulary should be intentionally small:

```xml
<paperSpecFieldGuide artifact="paper_data_spec.yaml" contract="paper_data_spec_contract.yaml">
  <field path="core_data_requirements.price_type" required="true" strictBlocking="true">
    <zhName>价格来源</zhName>
    <meaning>...</meaning>
    <whyItMatters>...</whyItMatters>
    <fillRule>...</fillRule>
    <examples>
      <example>...</example>
    </examples>
    <commonMistakes>
      <mistake>...</mistake>
    </commonMistakes>
    <blockingPrompt>...</blockingPrompt>
  </field>
</paperSpecFieldGuide>
```

Tests should parse this with `xml.etree.ElementTree`, so no dependency is added.

### Decision: Parity tests enforce coverage, not full semantic correctness

Tests should verify that each XML guide exists, is parseable, references the expected artifact/contract, and covers the YAML contract's required top-level fields, core required fields, optional blocks, and blocking question groups. Tests should also require non-empty Chinese explanation elements for each covered field.

The tests should not try to prove the explanation is financially or scientifically correct. That remains review responsibility.

### Decision: Skill consumes XML as pre-generation context

`qros-paper-to-spec` should instruct agents to inspect the matching XML field guide before generating each stage artifact. The agent still writes YAML artifacts and validates them with existing scripts.

This integrates PaperSpec without creating a second artifact contract or making reviewers write runtime-owned closure/projection/audit artifacts.

## Risks / Trade-offs

- XML guide drift from YAML contract -> Mitigation: add parity tests that fail when required fields, core fields, optional blocks, or blocking groups are missing from guides.
- Guides become too verbose for agent context -> Mitigation: keep one guide per artifact and instruct agents to load only the stage guide currently being generated.
- Chinese explanation accidentally changes contract semantics -> Mitigation: docs and skill must state YAML contract is canonical and XML guide is explanatory.
- Users may expect XML output artifacts -> Mitigation: usage docs must explicitly say formal outputs remain `paper_*_spec.yaml`.
- Future full XML migration becomes harder if guide vocabulary is informal -> Mitigation: keep XML vocabulary stable, narrow, and parseable from the first implementation.

## Migration Plan

1. Add XML field guide files without changing YAML contracts.
2. Add parity tests for guide presence and coverage.
3. Update `qros-paper-to-spec` and usage docs to reference the guides.
4. Run focused contract/skill/docs tests and smoke.

Rollback is straightforward: remove the XML guide files, parity tests, and skill/docs references. Runtime validators and formal artifacts remain unchanged.
