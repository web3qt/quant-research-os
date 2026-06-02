## 1. Contract And Artifact Shape

- [x] 1.1 Decide whether to add a new `paper_auto_implementation_handoff.yaml` contract under `contracts/paper_to_spec/` or reuse an existing implementation handoff section.
- [x] 1.2 If adding the artifact, define required top-level fields for implementation decision, data readiness brief, researcher data response, acquisition plan, acquisition provenance, active repo boundary, and allowed next action.
- [x] 1.3 Add or update XML field guide coverage for any new handoff fields with Chinese explanations.
- [x] 1.4 Add contract tests for required fields, enums, blocking groups, and XML guide coverage.

## 2. Runtime And Skill Behavior

- [x] 2.1 Update `qros-paper-to-spec` skill instructions so valid specs end with an explicit implementation prompt instead of silently stopping or implementing.
- [x] 2.2 Add runtime/helper behavior, if needed, to derive the Data Readiness Brief from validated PaperSpec artifacts.
- [x] 2.3 Ensure the flow asks whether the researcher can provide required data before any agent-driven acquisition plan is created.
- [x] 2.4 Ensure agent acquisition is only described or executed after explicit researcher approval and records source, command, snapshot identity, coverage, validation result, and failure reason.
- [x] 2.5 Enforce active research repo boundaries for handoff artifacts, downloaded data, and implementation outputs.

## 3. Documentation And Tests

- [x] 3.1 Update `docs/guides/qros-paper-to-spec-usage.md` with the post-spec implementation prompt, data readiness brief, and data acquisition consent rules.
- [x] 3.2 Update skill asset tests to lock the new prompt and data readiness wording.
- [x] 3.3 Add runtime tests for decline, opt-in with researcher-provided data, opt-in with missing data, and agent acquisition plan approval states.
- [x] 3.4 Add fixture coverage for valid and blocking implementation handoff artifacts if a new contract is introduced.
- [x] 3.5 Add regression tests proving no implementation or data acquisition happens when specs are invalid or the researcher has not opted in.

## 4. Verification

- [x] 4.1 Run focused tests for paper-to-spec contracts, XML field guides, runtime helpers, docs, and skill assets.
- [x] 4.2 Run `python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q`.
- [x] 4.3 Run `openspec validate --all --strict --no-interactive`.
- [x] 4.4 Run `python runtime/scripts/run_verification_tier.py --tier smoke`.
- [x] 4.5 Run full-smoke only if implementation changes touch `qros-research-session` stage flow, gate semantics, review orchestration, route split, anti-drift snapshots, stage-display supported stage contracts, or lineage-local stage-program auto-author behavior.
