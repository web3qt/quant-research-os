# Paper-To-Spec XML Field Guides Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Chinese XML field guides for all paper-to-spec contracts so PaperSpec / `qros-paper-to-spec` can generate better YAML artifacts while YAML contracts remain canonical runtime truth.

**Architecture:** Keep `contracts/paper_to_spec/*.yaml` as the only validator input. Add one XML field guide per contract under `contracts/paper_to_spec/field_guides/`, then enforce guide/contract coverage with a standard-library XML parity test. Update the active paper-to-spec skill and user guide so agents read the stage-specific XML guide before writing the existing `paper_*_spec.yaml` artifact.

**Tech Stack:** Python 3, PyYAML already used by this repo, `xml.etree.ElementTree` from the Python standard library, pytest, Markdown docs, QROS skills.

---

## Source Material

- `openspec/changes/add-paper-to-spec-xml-field-guides/proposal.md`
- `openspec/changes/add-paper-to-spec-xml-field-guides/design.md`
- `openspec/changes/add-paper-to-spec-xml-field-guides/specs/paper-to-spec-field-guides/spec.md`
- `openspec/changes/add-paper-to-spec-xml-field-guides/tasks.md`

## Scope Check

This is one coherent capability: a paper-to-spec semantic guide layer. It touches contracts, tests, skill text, and docs, but it does not split into independent runtime features. Do not change stage flow, review routing, formal artifact format, or any paper-to-spec validator default YAML contract path.

## File Structure

- Create: `contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml`
  - Chinese field guide for `paper_data_spec.yaml`; covers data top-level fields, core data requirements, optional data blocks, blocking groups, and implementation handoff.
- Create: `contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml`
  - Chinese field guide for `paper_signal_spec.yaml`; covers signal reference, core signal fields, optional signal blocks, blocking groups, and handoff.
- Create: `contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml`
  - Chinese field guide for `paper_train_freeze_spec.yaml`; covers freeze reference, core train/freeze fields, optional train/freeze blocks, blocking groups, and handoff.
- Create: `contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml`
  - Chinese field guide for `paper_test_evidence_spec.yaml`; covers test evidence reference, core evidence fields, optional evidence blocks, blocking groups, and handoff.
- Create: `contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml`
  - Chinese field guide for `paper_backtest_spec.yaml`; covers backtest reference, market/portfolio/accounting/reproducibility fields, optional blocks, blocking groups, and handoff.
- Create: `contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml`
  - Chinese field guide for `paper_backtest_implementation_spec.yaml`; covers implementation boundary, entrypoint, inputs, outputs, manifest, controls, optional blocks, blocking groups, and handoff.
- Create: `tests/contracts/test_paper_to_spec_field_guides.py`
  - Contract/guide parity test using `yaml.safe_load` and `xml.etree.ElementTree`.
- Modify: `skills/core/qros-paper-to-spec/SKILL.md`
  - Adds XML field guide paths and stage protocols requiring agents to read only the matching guide before generating each YAML artifact.
- Modify: `tests/skills/test_paper_to_spec_assets.py`
  - Locks skill references to XML guide paths and canonical YAML wording.
- Modify: `docs/guides/qros-paper-to-spec-usage.md`
  - Explains XML guides are semantic/PaperSpec aids and formal outputs remain YAML.
- Modify: `tests/docs/test_paper_to_spec_docs.py`
  - Locks doc references to XML guide paths and canonical YAML wording.
- Modify if needed: `docs/README.codex.md`, `tests/docs/test_install_docs.py`
  - Only if README/install docs need a short mention to stay consistent.

## XML Vocabulary

Use this exact vocabulary. Keep tag names stable so tests can parse the guides without a schema dependency.

```xml
<paperSpecFieldGuide artifact="paper_data_spec.yaml" contract="paper_data_spec_contract.yaml">
  <field path="core_data_requirements.price_type" required="true" strictBlocking="true">
    <zhName>价格来源</zhName>
    <meaning>定义特征计算和收益标签使用哪一种价格源。</meaning>
    <whyItMatters>永续合约中 mark、last、index 价格口径不同，会影响收益、回测和防偷看判断。</whyItMatters>
    <fillRule>在 value 中明确 feature_price 和 return_price；如果论文没有明确说明，source 不能写 paper_stated。</fillRule>
    <examples>
      <example>value.feature_price=mark; value.return_price=mark</example>
    </examples>
    <commonMistakes>
      <mistake>只写 close price，但不说明是 mark close 还是 last close。</mistake>
    </commonMistakes>
    <blockingPrompt>如果价格源未知，先问研究员：特征和收益应该使用 mark、last 还是 index？</blockingPrompt>
  </field>
</paperSpecFieldGuide>
```

Guide entry rules:
- Use `<field path="...">` for top-level fields and core fields.
- Use `<block name="...">` for optional blocks.
- Use `<blockingGroup name="...">` for blocking question groups.
- Every `<field>`, `<block>`, and `<blockingGroup>` must include non-empty `zhName`, `meaning`, `whyItMatters`, `fillRule`, `examples`, and `commonMistakes`.
- Include `blockingPrompt` when the item can trigger a blocking research question.
- Chinese text must contain at least one CJK character.

Coverage paths:
- Required top-level fields use their plain field names, for example `source`.
- Core required fields use `core_data_requirements.<field>` or the stage-specific core container, for example `core_signal_requirements.signal_family`.
- Optional blocks use `<block name="derivatives_positioning">`.
- Blocking groups use `<blockingGroup name="market_scope">`.

---

### Task 1: Contract/Guide Parity Test

**Files:**
- Create: `tests/contracts/test_paper_to_spec_field_guides.py`
- Read: `contracts/paper_to_spec/*_contract.yaml`
- Read later: `contracts/paper_to_spec/field_guides/*.fields.xml`

- [ ] **Step 1: Write the failing parity test**

Create `tests/contracts/test_paper_to_spec_field_guides.py` with this complete content:

```python
from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIR = ROOT / "contracts" / "paper_to_spec"
GUIDE_DIR = CONTRACT_DIR / "field_guides"

GUIDE_MAP = {
    "paper_data_spec_contract.yaml": {
        "guide": "paper_data_spec.fields.xml",
        "artifact": "paper_data_spec.yaml",
        "core_container": "core_data_requirements",
    },
    "paper_signal_spec_contract.yaml": {
        "guide": "paper_signal_spec.fields.xml",
        "artifact": "paper_signal_spec.yaml",
        "core_container": "core_signal_requirements",
    },
    "paper_train_freeze_spec_contract.yaml": {
        "guide": "paper_train_freeze_spec.fields.xml",
        "artifact": "paper_train_freeze_spec.yaml",
        "core_container": "core_train_freeze_requirements",
    },
    "paper_test_evidence_spec_contract.yaml": {
        "guide": "paper_test_evidence_spec.fields.xml",
        "artifact": "paper_test_evidence_spec.yaml",
        "core_container": "core_test_evidence_requirements",
    },
    "paper_backtest_spec_contract.yaml": {
        "guide": "paper_backtest_spec.fields.xml",
        "artifact": "paper_backtest_spec.yaml",
        "core_container": "core_backtest_requirements",
    },
    "paper_backtest_implementation_spec_contract.yaml": {
        "guide": "paper_backtest_implementation_spec.fields.xml",
        "artifact": "paper_backtest_implementation_spec.yaml",
        "core_container": "core_implementation_requirements",
    },
}

REQUIRED_EXPLANATION_TAGS = [
    "zhName",
    "meaning",
    "whyItMatters",
    "fillRule",
    "examples",
    "commonMistakes",
]

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _load_contract(filename: str) -> dict:
    path = CONTRACT_DIR / filename
    assert path.exists(), f"missing contract: {path}"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), f"{path} must be a mapping"
    return payload


def _load_guide(filename: str) -> ET.Element:
    path = GUIDE_DIR / filename
    assert path.exists(), f"missing XML field guide: {path}"
    return ET.fromstring(path.read_text(encoding="utf-8"))


def _text_for(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    assert child is not None, f"{element.tag} {element.attrib} missing <{tag}>"
    text = "".join(child.itertext()).strip()
    assert text, f"{element.tag} {element.attrib} has empty <{tag}>"
    return text


def _assert_explanation_complete(element: ET.Element) -> None:
    combined = []
    for tag in REQUIRED_EXPLANATION_TAGS:
        combined.append(_text_for(element, tag))
    assert CJK_RE.search(" ".join(combined)), (
        f"{element.tag} {element.attrib} must include Chinese explanation text"
    )


def test_paper_to_spec_xml_field_guides_exist_and_reference_contracts() -> None:
    for contract_filename, expected in GUIDE_MAP.items():
        root = _load_guide(expected["guide"])
        assert root.tag == "paperSpecFieldGuide"
        assert root.attrib["artifact"] == expected["artifact"]
        assert root.attrib["contract"] == contract_filename


def test_paper_to_spec_xml_field_guides_cover_required_fields() -> None:
    for contract_filename, expected in GUIDE_MAP.items():
        contract = _load_contract(contract_filename)
        root = _load_guide(expected["guide"])
        fields = {field.attrib["path"]: field for field in root.findall("field")}

        for field_name in contract.get("required_top_level_fields", []):
            assert field_name in fields, (
                f"{expected['guide']} missing top-level field guide for {field_name}"
            )
            _assert_explanation_complete(fields[field_name])

        core_container = expected["core_container"]
        for field_name in contract.get("core_required_fields", []):
            path = f"{core_container}.{field_name}"
            assert path in fields, f"{expected['guide']} missing core field guide for {path}"
            _assert_explanation_complete(fields[path])


def test_paper_to_spec_xml_field_guides_cover_optional_blocks_and_blocking_groups() -> None:
    for contract_filename, expected in GUIDE_MAP.items():
        contract = _load_contract(contract_filename)
        root = _load_guide(expected["guide"])
        blocks = {block.attrib["name"]: block for block in root.findall("block")}
        blocking_groups = {
            group.attrib["name"]: group for group in root.findall("blockingGroup")
        }

        for block_name in contract.get("optional_blocks", []):
            assert block_name in blocks, (
                f"{expected['guide']} missing optional block guide for {block_name}"
            )
            _assert_explanation_complete(blocks[block_name])

        for group_name in contract.get("blocking_question_groups", {}):
            assert group_name in blocking_groups, (
                f"{expected['guide']} missing blocking group guide for {group_name}"
            )
            _assert_explanation_complete(blocking_groups[group_name])
```

- [ ] **Step 2: Run the new test and verify it fails because guides do not exist**

Run:

```bash
python -m pytest tests/contracts/test_paper_to_spec_field_guides.py -q
```

Expected: FAIL with a message like:

```text
missing XML field guide: .../contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml
```

- [ ] **Step 3: Commit test only if commits are explicitly authorized**

Do not commit unless the user explicitly authorizes commits. If authorized, run:

```bash
git add tests/contracts/test_paper_to_spec_field_guides.py
git commit -m "test: add paper-to-spec field guide parity checks"
```

Expected: commit succeeds and includes only the new parity test.

---

### Task 2: XML Field Guide Files

**Files:**
- Create: `contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml`
- Create: `contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml`
- Create: `contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml`
- Create: `contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml`
- Create: `contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml`
- Create: `contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml`
- Test: `tests/contracts/test_paper_to_spec_field_guides.py`

- [ ] **Step 1: Create the field guide directory**

Run:

```bash
mkdir -p contracts/paper_to_spec/field_guides
```

Expected: directory exists at `contracts/paper_to_spec/field_guides`.

- [ ] **Step 2: Add `paper_data_spec.fields.xml`**

Create `contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml`.

Required root:

```xml
<paperSpecFieldGuide artifact="paper_data_spec.yaml" contract="paper_data_spec_contract.yaml">
```

Required `<field path="...">` entries:

```text
spec_version
source
reading_coverage
target_market
core_data_requirements
triggered_optional_blocks
ambiguities
implementation_handoff
core_data_requirements.universe
core_data_requirements.price_bars
core_data_requirements.price_type
core_data_requirements.funding
core_data_requirements.fees_and_slippage
core_data_requirements.label_or_return_target
core_data_requirements.timestamp_alignment
core_data_requirements.data_availability
```

Required `<block name="...">` entries:

```text
derivatives_positioning
liquidity_microstructure
cross_exchange
external_or_onchain
sentiment_or_news
```

Required `<blockingGroup name="...">` entries:

```text
market_scope
bar_and_price
return_accounting
source_coverage
```

Use this complete entry pattern for every field, block, and blocking group, replacing only the path/name, Chinese name, and sentence content with the concrete concept:

```xml
  <field path="core_data_requirements.price_type" required="true" strictBlocking="true">
    <zhName>价格来源</zhName>
    <meaning>定义特征计算和收益标签使用哪一种价格源。</meaning>
    <whyItMatters>永续合约中 mark、last、index 价格口径不同，会影响收益、回测和防偷看判断。</whyItMatters>
    <fillRule>在 value 中明确 feature_price 和 return_price；如果论文没有明确说明，source 不能写 paper_stated。</fillRule>
    <examples>
      <example>value.feature_price=mark; value.return_price=mark</example>
    </examples>
    <commonMistakes>
      <mistake>只写 close price，但不说明是 mark close 还是 last close。</mistake>
    </commonMistakes>
    <blockingPrompt>如果价格源未知，先问研究员：特征和收益应该使用 mark、last 还是 index？</blockingPrompt>
  </field>
```

Concrete Chinese naming for the data guide:

```text
spec_version=规格版本
source=论文来源
reading_coverage=读取覆盖
target_market=目标市场
core_data_requirements=核心数据要求
triggered_optional_blocks=触发的可选数据块
ambiguities=待澄清问题
implementation_handoff=实现交接
universe=交易标的池
price_bars=价格K线
price_type=价格来源
funding=资金费率
fees_and_slippage=手续费与滑点
label_or_return_target=标签或收益目标
timestamp_alignment=时间戳对齐
data_availability=数据可用性
derivatives_positioning=衍生品持仓数据
liquidity_microstructure=流动性与微观结构
cross_exchange=跨交易所数据
external_or_onchain=外部或链上数据
sentiment_or_news=情绪或新闻数据
market_scope=市场范围阻断组
bar_and_price=K线与价格阻断组
return_accounting=收益核算阻断组
source_coverage=论文读取覆盖阻断组
```

- [ ] **Step 3: Add `paper_signal_spec.fields.xml`**

Create `contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml`.

Required root:

```xml
<paperSpecFieldGuide artifact="paper_signal_spec.yaml" contract="paper_signal_spec_contract.yaml">
```

Required field entries:

```text
spec_version
data_spec_reference
signal_research_intent
core_signal_requirements
triggered_optional_blocks
ambiguities
implementation_handoff
core_signal_requirements.signal_family
core_signal_requirements.prediction_target
core_signal_requirements.feature_inputs
core_signal_requirements.signal_definition
core_signal_requirements.signal_timing
core_signal_requirements.lookahead_controls
core_signal_requirements.train_test_policy
core_signal_requirements.portfolio_mapping
core_signal_requirements.diagnostics
```

Required block entries:

```text
cross_sectional_ranking
time_series_thresholds
parameter_search
machine_learning_model
regime_filter
risk_filter
```

Required blocking group entries:

```text
signal_identity
prediction_and_inputs
leakage_and_training
portfolio_and_diagnostics
```

Concrete Chinese naming:

```text
data_spec_reference=数据规格引用
signal_research_intent=信号研究意图
signal_family=信号家族
prediction_target=预测目标
feature_inputs=特征输入
signal_definition=信号定义
signal_timing=信号时点
lookahead_controls=防偷看控制
train_test_policy=训练测试政策
portfolio_mapping=组合映射
diagnostics=诊断要求
cross_sectional_ranking=截面排序
time_series_thresholds=时间序列阈值
parameter_search=参数搜索
machine_learning_model=机器学习模型
regime_filter=状态过滤
risk_filter=风险过滤
```

- [ ] **Step 4: Add `paper_train_freeze_spec.fields.xml`**

Create `contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml`.

Required root:

```xml
<paperSpecFieldGuide artifact="paper_train_freeze_spec.yaml" contract="paper_train_freeze_spec_contract.yaml">
```

Required field entries:

```text
spec_version
signal_spec_reference
train_freeze_intent
core_train_freeze_requirements
triggered_optional_blocks
ambiguities
implementation_handoff
core_train_freeze_requirements.train_test_mode
core_train_freeze_requirements.frozen_signal_definition
core_train_freeze_requirements.parameter_freeze
core_train_freeze_requirements.train_window
core_train_freeze_requirements.test_window
core_train_freeze_requirements.split_policy
core_train_freeze_requirements.selection_policy
core_train_freeze_requirements.model_training
core_train_freeze_requirements.refit_policy
core_train_freeze_requirements.leakage_controls
core_train_freeze_requirements.artifact_identity
```

Required block entries:

```text
rule_based_freeze
parameter_search_freeze
ml_training_freeze
walk_forward_freeze
regime_specific_freeze
```

Required blocking group entries:

```text
freeze_identity
split_and_selection
fit_and_refit
```

Concrete Chinese naming:

```text
signal_spec_reference=信号规格引用
train_freeze_intent=训练冻结意图
train_test_mode=训练测试模式
frozen_signal_definition=冻结信号定义
parameter_freeze=参数冻结
train_window=训练窗口
test_window=测试窗口
split_policy=切分政策
selection_policy=选择政策
model_training=模型训练
refit_policy=再训练政策
leakage_controls=泄漏控制
artifact_identity=产物身份
```

- [ ] **Step 5: Add `paper_test_evidence_spec.fields.xml`**

Create `contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml`.

Required root:

```xml
<paperSpecFieldGuide artifact="paper_test_evidence_spec.yaml" contract="paper_test_evidence_spec_contract.yaml">
```

Required field entries:

```text
spec_version
train_freeze_spec_reference
test_evidence_intent
core_test_evidence_requirements
triggered_optional_blocks
ambiguities
implementation_handoff
core_test_evidence_requirements.test_window
core_test_evidence_requirements.frozen_artifact_binding
core_test_evidence_requirements.signal_diagnostics
core_test_evidence_requirements.performance_diagnostics
core_test_evidence_requirements.rule_based_evidence
core_test_evidence_requirements.parameter_fit_evidence
core_test_evidence_requirements.ml_model_evidence
core_test_evidence_requirements.no_retune_attestation
core_test_evidence_requirements.test_result_usage_policy
core_test_evidence_requirements.provenance
core_test_evidence_requirements.evidence_identity
```

Use the optional block and blocking group names from `contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml`. Extract them with:

```bash
python - <<'PY'
from pathlib import Path
import yaml
payload = yaml.safe_load(Path("contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml").read_text())
print("optional_blocks:", payload.get("optional_blocks", []))
print("blocking_question_groups:", list(payload.get("blocking_question_groups", {})))
PY
```

Expected: command prints the exact names to include as `<block name="...">` and `<blockingGroup name="...">` entries.

- [ ] **Step 6: Add `paper_backtest_spec.fields.xml`**

Create `contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml`.

Required root:

```xml
<paperSpecFieldGuide artifact="paper_backtest_spec.yaml" contract="paper_backtest_spec_contract.yaml">
```

Required field entries:

```text
spec_version
test_evidence_spec_reference
backtest_intent
core_backtest_requirements
triggered_optional_blocks
ambiguities
implementation_handoff
core_backtest_requirements.backtest_scope
core_backtest_requirements.frozen_artifact_binding
core_backtest_requirements.market_assumptions
core_backtest_requirements.portfolio_construction
core_backtest_requirements.position_sizing
core_backtest_requirements.execution_assumptions
core_backtest_requirements.fees_slippage_funding
core_backtest_requirements.risk_controls
core_backtest_requirements.required_metrics
core_backtest_requirements.pass_fail_gate
core_backtest_requirements.reproducibility
core_backtest_requirements.provenance
core_backtest_requirements.implementation_handoff_plan
```

Use the optional block and blocking group names from `contracts/paper_to_spec/paper_backtest_spec_contract.yaml`. Extract them with:

```bash
python - <<'PY'
from pathlib import Path
import yaml
payload = yaml.safe_load(Path("contracts/paper_to_spec/paper_backtest_spec_contract.yaml").read_text())
print("optional_blocks:", payload.get("optional_blocks", []))
print("blocking_question_groups:", list(payload.get("blocking_question_groups", {})))
PY
```

- [ ] **Step 7: Add `paper_backtest_implementation_spec.fields.xml`**

Create `contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml`.

Required root:

```xml
<paperSpecFieldGuide artifact="paper_backtest_implementation_spec.yaml" contract="paper_backtest_implementation_spec_contract.yaml">
```

Required field entries:

```text
spec_version
backtest_spec_reference
implementation_intent
core_implementation_requirements
triggered_optional_blocks
ambiguities
implementation_handoff
core_implementation_requirements.active_research_repo_boundary
core_implementation_requirements.target_stage_program
core_implementation_requirements.backtest_entrypoint
core_implementation_requirements.input_artifacts
core_implementation_requirements.frozen_config_binding
core_implementation_requirements.data_access_plan
core_implementation_requirements.output_artifacts
core_implementation_requirements.execution_manifest
core_implementation_requirements.validation_checks
core_implementation_requirements.no_retune_controls
core_implementation_requirements.reproducibility_controls
```

Use the optional block and blocking group names from `contracts/paper_to_spec/paper_backtest_implementation_spec_contract.yaml`. Extract them with:

```bash
python - <<'PY'
from pathlib import Path
import yaml
payload = yaml.safe_load(Path("contracts/paper_to_spec/paper_backtest_implementation_spec_contract.yaml").read_text())
print("optional_blocks:", payload.get("optional_blocks", []))
print("blocking_question_groups:", list(payload.get("blocking_question_groups", {})))
PY
```

- [ ] **Step 8: Run parity tests and fix XML until they pass**

Run:

```bash
python -m pytest tests/contracts/test_paper_to_spec_field_guides.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 9: Commit XML guides if commits are explicitly authorized**

Do not commit unless the user explicitly authorizes commits. If authorized, run:

```bash
git add contracts/paper_to_spec/field_guides tests/contracts/test_paper_to_spec_field_guides.py
git commit -m "feat: add paper-to-spec XML field guides"
```

Expected: commit includes six XML guide files and the parity test.

---

### Task 3: Skill Integration

**Files:**
- Modify: `skills/core/qros-paper-to-spec/SKILL.md`
- Modify: `tests/skills/test_paper_to_spec_assets.py`
- Test: `tests/skills/test_paper_to_spec_assets.py`

- [ ] **Step 1: Extend the skill asset test before editing the skill**

In `tests/skills/test_paper_to_spec_assets.py`, add these strings to `required_strings`:

```python
        "contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml",
        "XML field guide",
        "YAML contract remains canonical",
        "正式 artifact 仍然是 `paper_*_spec.yaml`",
```

- [ ] **Step 2: Run the skill test and verify it fails**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py -q
```

Expected: FAIL because `SKILL.md` does not yet contain the XML guide paths and canonical YAML wording.

- [ ] **Step 3: Add the XML field guide section to the skill**

In `skills/core/qros-paper-to-spec/SKILL.md`, insert this section after the `Current outputs` section and before `Data Contract`:

```markdown
## XML Field Guides

PaperSpec generation must use the stage-specific XML field guide as semantic guidance before writing each YAML artifact:

```text
contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml
```

The XML field guide explains field meaning, examples, common mistakes, and blocking prompts in Chinese. YAML contract remains canonical for validation, and 正式 artifact 仍然是 `paper_*_spec.yaml`.

Load only the XML field guide for the stage currently being generated; do not load all guides into context unless comparing cross-stage inheritance.
```
```

- [ ] **Step 4: Add stage-specific read instructions**

For each execution protocol in `SKILL.md`, add one bullet before the stage's first field-filling step:

```markdown
0. `field guide`：先读取 `contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml`，只把它作为字段语义、示例、常见错误和阻断问题提示；正式校验仍以 `contracts/paper_to_spec/paper_data_spec_contract.yaml` 为准。
```

Use the matching guide and contract names for signal, train-freeze, test-evidence, backtest, and backtest implementation:

```text
paper_signal_spec.fields.xml -> paper_signal_spec_contract.yaml
paper_train_freeze_spec.fields.xml -> paper_train_freeze_spec_contract.yaml
paper_test_evidence_spec.fields.xml -> paper_test_evidence_spec_contract.yaml
paper_backtest_spec.fields.xml -> paper_backtest_spec_contract.yaml
paper_backtest_implementation_spec.fields.xml -> paper_backtest_implementation_spec_contract.yaml
```

- [ ] **Step 5: Run the skill test and verify it passes**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py -q
```

Expected:

```text
1 passed
```

- [ ] **Step 6: Commit skill integration if commits are explicitly authorized**

Do not commit unless the user explicitly authorizes commits. If authorized, run:

```bash
git add skills/core/qros-paper-to-spec/SKILL.md tests/skills/test_paper_to_spec_assets.py
git commit -m "docs: teach paper-to-spec skill about XML field guides"
```

Expected: commit includes only the skill and skill asset test changes.

---

### Task 4: User Documentation Integration

**Files:**
- Modify: `docs/guides/qros-paper-to-spec-usage.md`
- Modify: `tests/docs/test_paper_to_spec_docs.py`
- Modify if needed: `docs/README.codex.md`
- Modify if needed: `tests/docs/test_install_docs.py`
- Test: `tests/docs/test_paper_to_spec_docs.py`
- Test if README/install docs are touched: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Extend the paper-to-spec docs test before editing docs**

In `tests/docs/test_paper_to_spec_docs.py`, add these strings to `required_strings` inside `test_paper_to_spec_usage_guide_documents_first_paper_data_spec_version`:

```python
        "contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml",
        "XML field guide",
        "YAML contract remains canonical",
        "正式 artifact 仍然是 `paper_*_spec.yaml`",
```

- [ ] **Step 2: Run docs test and verify it fails**

Run:

```bash
python -m pytest tests/docs/test_paper_to_spec_docs.py -q
```

Expected: FAIL because `docs/guides/qros-paper-to-spec-usage.md` does not yet document XML field guides.

- [ ] **Step 3: Add XML guide explanation to usage docs**

In `docs/guides/qros-paper-to-spec-usage.md`, add this section near the contract overview before the per-stage contract sections:

```markdown
## XML Field Guides

PaperSpec / `qros-paper-to-spec` uses one XML field guide per stage as a semantic aid before writing the formal YAML artifact:

```text
contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml
contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml
```

The XML field guide contains Chinese field explanations, examples, common mistakes, and blocking prompts. YAML contract remains canonical for deterministic validation, and 正式 artifact 仍然是 `paper_*_spec.yaml`.

Agents should load only the guide for the stage they are generating. The guides are not formal research artifacts and are not validator outputs.
```
```

- [ ] **Step 4: Add stage protocol references in docs**

For each stage execution flow in `docs/guides/qros-paper-to-spec-usage.md`, add this as the first step, using matching stage names:

```markdown
0. 读取对应 XML field guide，仅用于字段语义、示例、常见错误和阻断问题提示；正式校验仍以对应 YAML contract 为准。
```

Then list the exact guide next to each stage:

```text
Data: contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml
Signal: contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml
Train-freeze: contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml
Test-evidence: contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml
Backtest: contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml
Backtest implementation: contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml
```

- [ ] **Step 5: Update README/install docs only if needed**

Check whether `docs/README.codex.md` has a paper-to-spec contract overview that would become misleading without XML guide mention:

```bash
rg -n "paper_to_spec|paper_data_spec|field guide|contract" docs/README.codex.md docs/guides/installation.md
```

Expected: if no text claims YAML contracts are the only thing agents read for generation, leave README/install docs unchanged. If there is a misleading sentence, add one sentence:

```markdown
PaperSpec generation may also consult `contracts/paper_to_spec/field_guides/*.fields.xml` for Chinese field explanations; YAML contracts and `paper_*_spec.yaml` artifacts remain canonical.
```

- [ ] **Step 6: Run docs tests and verify they pass**

Run:

```bash
python -m pytest tests/docs/test_paper_to_spec_docs.py -q
```

Expected:

```text
3 passed
```

If `docs/README.codex.md` or install docs were changed, also run:

```bash
python -m pytest tests/docs/test_install_docs.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit docs integration if commits are explicitly authorized**

Do not commit unless the user explicitly authorizes commits. If authorized, run:

```bash
git add docs/guides/qros-paper-to-spec-usage.md tests/docs/test_paper_to_spec_docs.py docs/README.codex.md tests/docs/test_install_docs.py
git commit -m "docs: document paper-to-spec XML field guides"
```

Expected: commit includes docs/test changes; if README/install docs were untouched, git will simply skip them.

---

### Task 5: Focused Contract Regression

**Files:**
- Read: `tests/contracts/test_paper_*_spec_contract.py`
- Read: `tests/contracts/test_paper_to_spec_field_guides.py`
- Read: `contracts/paper_to_spec/*.yaml`
- Read: `contracts/paper_to_spec/field_guides/*.fields.xml`

- [ ] **Step 1: Run focused contract tests**

Run:

```bash
python -m pytest \
  tests/contracts/test_paper_to_spec_field_guides.py \
  tests/contracts/test_paper_data_spec_contract.py \
  tests/contracts/test_paper_signal_spec_contract.py \
  tests/contracts/test_paper_train_freeze_spec_contract.py \
  tests/contracts/test_paper_test_evidence_spec_contract.py \
  tests/contracts/test_paper_backtest_spec_contract.py \
  tests/contracts/test_paper_backtest_implementation_spec_contract.py \
  -q
```

Expected: all listed contract tests pass.

- [ ] **Step 2: Verify validators still read YAML contract paths**

Run:

```bash
rg -n "DEFAULT_CONTRACT_PATH = ROOT / \"contracts\" / \"paper_to_spec\" / \"paper_.*_contract.yaml\"" runtime/tools/paper_*_spec_runtime.py
```

Expected: one `DEFAULT_CONTRACT_PATH` hit per paper spec runtime file, and all hits point to `.yaml` contract files.

- [ ] **Step 3: Run OpenSpec validation**

Run:

```bash
openspec validate add-paper-to-spec-xml-field-guides --strict --no-interactive
```

Expected:

```text
Change 'add-paper-to-spec-xml-field-guides' is valid
```

---

### Task 6: Full Focused Verification and Smoke

**Files:**
- No additional source changes in this task.

- [ ] **Step 1: Run focused implementation verification**

Run:

```bash
python -m pytest \
  tests/contracts/test_paper_to_spec_field_guides.py \
  tests/contracts/test_paper_data_spec_contract.py \
  tests/contracts/test_paper_signal_spec_contract.py \
  tests/contracts/test_paper_train_freeze_spec_contract.py \
  tests/contracts/test_paper_test_evidence_spec_contract.py \
  tests/contracts/test_paper_backtest_spec_contract.py \
  tests/contracts/test_paper_backtest_implementation_spec_contract.py \
  tests/skills/test_paper_to_spec_assets.py \
  tests/docs/test_paper_to_spec_docs.py \
  -q
```

Expected: all focused tests pass.

- [ ] **Step 2: Run bootstrap/install minimum check**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected: all bootstrap/install checks pass.

- [ ] **Step 3: Run QROS smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: smoke tier exits with code 0.

- [ ] **Step 4: Decide whether full-smoke is required**

Run full-smoke only if implementation changed any of these:

```text
qros-research-session stage flow / gate semantics
review / display / next-stage orchestration
route split / CSF routing
anti-drift snapshots or canonical session stage naming
stage-display supported stage contract
lineage-local stage-program auto-author seams
```

This plan should not touch those areas. If they were touched unexpectedly, run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: full-smoke exits with code 0.

- [ ] **Step 5: Review changed files**

Run:

```bash
git status --short
git diff --stat
```

Expected: changed files are limited to:

```text
contracts/paper_to_spec/field_guides/*.fields.xml
tests/contracts/test_paper_to_spec_field_guides.py
skills/core/qros-paper-to-spec/SKILL.md
tests/skills/test_paper_to_spec_assets.py
docs/guides/qros-paper-to-spec-usage.md
tests/docs/test_paper_to_spec_docs.py
docs/README.codex.md only if needed
tests/docs/test_install_docs.py only if needed
openspec/changes/add-paper-to-spec-xml-field-guides/tasks.md if apply marks tasks complete
```

- [ ] **Step 6: Final commit if commits are explicitly authorized**

Do not commit unless the user explicitly authorizes commits. If authorized, run:

```bash
git add \
  contracts/paper_to_spec/field_guides \
  tests/contracts/test_paper_to_spec_field_guides.py \
  skills/core/qros-paper-to-spec/SKILL.md \
  tests/skills/test_paper_to_spec_assets.py \
  docs/guides/qros-paper-to-spec-usage.md \
  tests/docs/test_paper_to_spec_docs.py \
  docs/README.codex.md \
  tests/docs/test_install_docs.py \
  openspec/changes/add-paper-to-spec-xml-field-guides/tasks.md
git commit -m "feat: add paper-to-spec XML field guides"
```

Expected: commit succeeds only after all required verification commands pass.

## Self-Review

Spec coverage:
- XML guide exists for every paper-to-spec contract: covered by Task 2 and Task 1 parity tests.
- YAML remains canonical: covered by Task 5 validator path check and skill/docs wording.
- Required top-level/core/optional/blocking coverage: covered by Task 1 test code and Task 2 guide creation.
- Chinese explanations for PaperSpec generation: covered by Task 1 non-empty CJK explanation checks and Task 2 content requirements.
- Formal artifacts remain YAML: covered by Task 3 skill wording and Task 4 docs wording.

Placeholder scan:
- No implementation step uses placeholder markers, delayed-work wording, or vague validation wording.
- Every code-changing task includes concrete file paths, code snippets, exact commands, and expected outcomes.

Type/name consistency:
- XML root is consistently `paperSpecFieldGuide`.
- XML entries are consistently `field path`, `block name`, and `blockingGroup name`.
- Contract/core container mapping matches the existing QROS naming: `core_data_requirements`, `core_signal_requirements`, `core_train_freeze_requirements`, `core_test_evidence_requirements`, `core_backtest_requirements`, and `core_implementation_requirements`.
