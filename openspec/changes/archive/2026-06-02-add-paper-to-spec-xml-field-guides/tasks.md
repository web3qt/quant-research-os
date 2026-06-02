## 1. XML Field Guide Structure

- [x] 1.1 Create `contracts/paper_to_spec/field_guides/` and add one `.fields.xml` guide per existing `paper_*_spec_contract.yaml`; verify with `find contracts/paper_to_spec/field_guides -maxdepth 1 -name '*.fields.xml' -print`.
- [x] 1.2 Define the stable XML vocabulary using `paperSpecFieldGuide`, `field`, `block`, `blockingGroup`, `zhName`, `meaning`, `whyItMatters`, `fillRule`, `examples`, `commonMistakes`, and `blockingPrompt`; verify XML parseability with the new parity test.
- [x] 1.3 Populate the guides with Chinese explanations for required top-level fields, core required fields, optional blocks, blocking question groups, and implementation handoff fields; verify coverage with `python -m pytest tests/contracts/test_paper_to_spec_field_guides.py`.

## 2. Contract/Guide Parity Tests

- [x] 2.1 Add `tests/contracts/test_paper_to_spec_field_guides.py` using `yaml.safe_load` for YAML contracts and `xml.etree.ElementTree` for XML guides; verify it fails if a guide is missing or invalid.
- [x] 2.2 Assert every YAML contract's `required_top_level_fields`, `core_required_fields`, `optional_blocks`, and `blocking_question_groups` are covered by the matching XML guide; verify with `python -m pytest tests/contracts/test_paper_to_spec_field_guides.py`.
- [x] 2.3 Assert required explanation nodes are non-empty and contain Chinese text for covered guide entries; verify with `python -m pytest tests/contracts/test_paper_to_spec_field_guides.py`.

## 3. PaperSpec Skill and Documentation Integration

- [x] 3.1 Update `skills/core/qros-paper-to-spec/SKILL.md` so each stage protocol tells the agent to read only the matching XML field guide before generating the YAML artifact; verify with `python -m pytest tests/skills/test_paper_to_spec_assets.py`.
- [x] 3.2 Update `docs/guides/qros-paper-to-spec-usage.md` to explain that XML field guides are semantic/PaperSpec aids while YAML contracts and `paper_*_spec.yaml` artifacts remain canonical; verify with `python -m pytest tests/docs/test_paper_to_spec_docs.py`.
- [x] 3.3 If install docs or README mention paper-to-spec contract usage, update them only as needed without changing QROS install semantics; verify with `python -m pytest tests/docs/test_install_docs.py`.

## 4. Verification

- [x] 4.1 Run focused contract/skill/docs tests: `python -m pytest tests/contracts/test_paper_to_spec_field_guides.py tests/contracts/test_paper_data_spec_contract.py tests/contracts/test_paper_signal_spec_contract.py tests/contracts/test_paper_train_freeze_spec_contract.py tests/contracts/test_paper_test_evidence_spec_contract.py tests/contracts/test_paper_backtest_spec_contract.py tests/contracts/test_paper_backtest_implementation_spec_contract.py tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py`.
- [x] 4.2 Run bootstrap/install doc regression if touched: `python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py`.
- [x] 4.3 Run QROS smoke: `python runtime/scripts/run_verification_tier.py --tier smoke`.
- [x] 4.4 Run full-smoke only if implementation unexpectedly changes stage flow, gate semantics, route split, review/display orchestration, anti-drift snapshots, canonical session stage naming, stage-display support, or lineage-local stage-program authoring: `python runtime/scripts/run_verification_tier.py --tier full-smoke`. Not run because this implementation did not touch those areas.
