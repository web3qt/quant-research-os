# Paper-To-Spec Auto Implementation Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in post-PaperSpec implementation handoff that first explains required data, asks whether the researcher can provide it, and only allows agent data acquisition after explicit approval.

**Architecture:** Add a contract-backed `paper_auto_implementation_handoff.yaml` artifact beside the existing staged PaperSpec artifacts. The new validator enforces valid upstream specs, explicit implementation decision, data readiness state, active repo boundary, and controlled data acquisition approval; the skill/docs explain the interactive handoff behavior.

**Tech Stack:** YAML contracts, XML field guides, Python validators using `yaml.safe_load`, pytest, OpenSpec.

---

## File Structure

- Create `contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml`: machine-readable truth for the new post-spec handoff artifact.
- Create `contracts/paper_to_spec/field_guides/paper_auto_implementation_handoff.fields.xml`: Chinese field guide for the new artifact.
- Modify `tests/contracts/test_paper_to_spec_field_guides.py`: add the new contract/guide pair to XML coverage.
- Create `tests/contracts/test_paper_auto_implementation_handoff_contract.py`: lock the new contract shape.
- Create `tests/fixtures/paper_to_spec/valid_paper_auto_implementation_handoff.yaml`: valid fixture for runtime tests.
- Create `runtime/tools/paper_auto_implementation_handoff_runtime.py`: deterministic validator for the handoff artifact.
- Create `runtime/scripts/validate_paper_auto_implementation_handoff.py`: CLI wrapper.
- Create `tests/runtime/test_paper_auto_implementation_handoff_runtime.py`: validator behavior tests for opt-in, decline, data response, acquisition approval, and active repo boundary.
- Modify `skills/core/qros-paper-to-spec/SKILL.md`: add post-spec prompt and data readiness protocol.
- Modify `docs/guides/qros-paper-to-spec-usage.md`: document the handoff and data acquisition consent rules.
- Modify `tests/skills/test_paper_to_spec_assets.py`: lock skill wording.
- Modify `tests/docs/test_paper_to_spec_docs.py`: lock user docs wording.

Do not add data download code in this change. The contract allows an approved acquisition plan and provenance records; actual exchange/API-specific acquisition should remain a later active-repo implementation concern.

### Task 1: Contract And XML Field Guide

**Files:**
- Create: `contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml`
- Create: `contracts/paper_to_spec/field_guides/paper_auto_implementation_handoff.fields.xml`
- Modify: `tests/contracts/test_paper_to_spec_field_guides.py`
- Test: `tests/contracts/test_paper_auto_implementation_handoff_contract.py`

- [ ] **Step 1: Write the failing contract test**

Create `tests/contracts/test_paper_auto_implementation_handoff_contract.py`:

```python
from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml")


def _load_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"missing contract: {CONTRACT_PATH}"
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_auto_implementation_handoff_contract_declares_required_shape() -> None:
    contract = _load_contract()

    assert contract["schema_id"] == "qros-paper-auto-implementation-handoff-contract-v1"
    assert contract["spec_version"] == "v1"
    assert contract["depends_on"] == {
        "artifact": "paper_backtest_implementation_spec.yaml",
        "schema_id": "qros-paper-backtest-implementation-spec-contract-v1",
        "validator": "runtime/scripts/validate_paper_backtest_implementation_spec.py",
    }
    assert contract["required_top_level_fields"] == [
        "spec_version",
        "source",
        "paper_spec_chain",
        "implementation_decision",
        "data_readiness_brief",
        "researcher_data_response",
        "agent_acquisition_plan",
        "acquisition_provenance",
        "active_repo_boundary",
        "allowed_next_action",
        "ambiguities",
        "implementation_handoff",
    ]


def test_paper_auto_implementation_handoff_contract_locks_enums() -> None:
    contract = _load_contract()

    assert contract["allowed_spec_validation_statuses"] == ["valid", "blocked", "unknown"]
    assert contract["allowed_implementation_decisions"] == ["pending", "accepted", "declined"]
    assert contract["allowed_researcher_data_statuses"] == ["pending", "provided", "cannot_provide"]
    assert contract["allowed_acquisition_plan_statuses"] == ["not_needed", "pending_approval", "approved", "rejected"]
    assert contract["allowed_acquisition_run_statuses"] == ["not_run", "succeeded", "failed", "partial"]
    assert contract["allowed_next_actions"] == [
        "stop_after_specs",
        "ask_researcher",
        "validate_researcher_data",
        "run_agent_data_acquisition",
        "generate_active_repo_backtest_scaffold",
    ]


def test_paper_auto_implementation_handoff_contract_locks_data_item_shape() -> None:
    contract = _load_contract()

    assert contract["required_data_item_fields"] == [
        "name",
        "requirement",
        "required",
        "fields",
        "cadence",
        "time_range",
        "source_constraints",
        "expected_format",
        "missing_data_policy",
        "blocking",
    ]
    assert contract["required_acquisition_source_fields"] == [
        "dataset",
        "source",
        "command",
        "storage_target",
        "approval_required",
    ]


def test_paper_auto_implementation_handoff_contract_declares_blocking_groups() -> None:
    contract = _load_contract()

    assert contract["blocking_question_groups"] == {
        "implementation_consent": ["implementation_decision"],
        "data_readiness": ["data_readiness_brief", "researcher_data_response"],
        "agent_acquisition": ["agent_acquisition_plan", "acquisition_provenance"],
        "repo_boundary": ["active_repo_boundary"],
        "next_action": ["allowed_next_action"],
    }
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python -m pytest tests/contracts/test_paper_auto_implementation_handoff_contract.py -q
```

Expected: FAIL with `missing contract: contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml`.

- [ ] **Step 3: Add the handoff contract**

Create `contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml`:

```yaml
schema_id: qros-paper-auto-implementation-handoff-contract-v1
spec_version: v1

depends_on:
  artifact: paper_backtest_implementation_spec.yaml
  schema_id: qros-paper-backtest-implementation-spec-contract-v1
  validator: runtime/scripts/validate_paper_backtest_implementation_spec.py

required_top_level_fields:
  - spec_version
  - source
  - paper_spec_chain
  - implementation_decision
  - data_readiness_brief
  - researcher_data_response
  - agent_acquisition_plan
  - acquisition_provenance
  - active_repo_boundary
  - allowed_next_action
  - ambiguities
  - implementation_handoff

required_source_fields:
  - title
  - locator
  - source_kind
  - paper_slug

allowed_source_kinds:
  - pdf_url
  - webpage
  - local_pdf
  - local_doc
  - text_summary

required_paper_spec_chain_fields:
  - paper_data_spec
  - paper_signal_spec
  - paper_train_freeze_spec
  - paper_test_evidence_spec
  - paper_backtest_spec
  - paper_backtest_implementation_spec

required_spec_reference_fields:
  - path
  - validation_status
  - digest

allowed_spec_validation_statuses:
  - valid
  - blocked
  - unknown

required_implementation_decision_fields:
  - decision
  - prompt
  - answered_by
  - answered_at
  - evidence

allowed_implementation_decisions:
  - pending
  - accepted
  - declined

required_data_readiness_brief_fields:
  - required_datasets
  - optional_datasets
  - blocking_gaps
  - summary

required_data_item_fields:
  - name
  - requirement
  - required
  - fields
  - cadence
  - time_range
  - source_constraints
  - expected_format
  - missing_data_policy
  - blocking

required_researcher_data_response_fields:
  - status
  - provided_paths
  - access_instructions
  - missing_datasets
  - evidence

allowed_researcher_data_statuses:
  - pending
  - provided
  - cannot_provide

required_agent_acquisition_plan_fields:
  - status
  - sources
  - approval
  - limitations

allowed_acquisition_plan_statuses:
  - not_needed
  - pending_approval
  - approved
  - rejected

required_acquisition_source_fields:
  - dataset
  - source
  - command
  - storage_target
  - approval_required

required_acquisition_provenance_fields:
  - run_status
  - source_records
  - snapshot_identity
  - coverage
  - validation_result
  - failure_reason

allowed_acquisition_run_statuses:
  - not_run
  - succeeded
  - failed
  - partial

required_active_repo_boundary_fields:
  - repo_role
  - target_root
  - forbidden_root

allowed_next_actions:
  - stop_after_specs
  - ask_researcher
  - validate_researcher_data
  - run_agent_data_acquisition
  - generate_active_repo_backtest_scaffold

required_ambiguity_fields:
  - field
  - question
  - blocking

required_implementation_handoff_fields:
  - implementation_inputs
  - implementation_outputs
  - validation_checks
  - next_stage_recommendation

blocking_question_groups:
  implementation_consent:
    - implementation_decision
  data_readiness:
    - data_readiness_brief
    - researcher_data_response
  agent_acquisition:
    - agent_acquisition_plan
    - acquisition_provenance
  repo_boundary:
    - active_repo_boundary
  next_action:
    - allowed_next_action
```

- [ ] **Step 4: Add the XML field guide and coverage map test**

Create `contracts/paper_to_spec/field_guides/paper_auto_implementation_handoff.fields.xml`:

```xml
<paperSpecFieldGuide artifact="paper_auto_implementation_handoff.yaml" contract="paper_auto_implementation_handoff_contract.yaml">
  <field path="spec_version"><zhName>规格版本</zhName><meaning>声明 auto implementation handoff 合同版本。</meaning><whyItMatters>版本决定运行时校验口径。</whyItMatters><fillRule>填写 v1。</fillRule><examples><example>v1</example></examples><commonMistakes><mistake>版本缺失。</mistake></commonMistakes><blockingPrompt>请确认合同版本。</blockingPrompt></field>
  <field path="source"><zhName>论文来源</zhName><meaning>记录论文来源和 paper_slug。</meaning><whyItMatters>handoff 必须追溯到同一篇论文。</whyItMatters><fillRule>与上游 PaperSpec source 保持一致。</fillRule><examples><example>paper_slug=momentum_perp_paper</example></examples><commonMistakes><mistake>使用不同 paper_slug。</mistake></commonMistakes><blockingPrompt>请确认 source。</blockingPrompt></field>
  <field path="paper_spec_chain"><zhName>PaperSpec 链路</zhName><meaning>记录六个上游 PaperSpec artifact 的路径、校验状态和 digest。</meaning><whyItMatters>只有 valid spec 链路才允许进入实现询问。</whyItMatters><fillRule>逐项填写 paper_data_spec 到 paper_backtest_implementation_spec。</fillRule><examples><example>paper_backtest_implementation_spec.validation_status=valid</example></examples><commonMistakes><mistake>缺少某个上游 spec。</mistake></commonMistakes><blockingPrompt>请确认所有上游 spec 均 valid。</blockingPrompt></field>
  <field path="implementation_decision"><zhName>实现决策</zhName><meaning>记录用户是否同意从 specs 自动实现。</meaning><whyItMatters>实现、下载数据或生成 scaffold 必须用户显式同意。</whyItMatters><fillRule>decision 使用 pending、accepted 或 declined。</fillRule><examples><example>decision=accepted</example></examples><commonMistakes><mistake>没有用户答复就继续实现。</mistake></commonMistakes><blockingPrompt>请确认是否自动实现。</blockingPrompt></field>
  <field path="data_readiness_brief"><zhName>数据准备说明</zhName><meaning>列出实现前需要的数据、字段、周期、范围和缺口。</meaning><whyItMatters>数据是实现前最早的阻塞项。</whyItMatters><fillRule>拆分 required_datasets、optional_datasets、blocking_gaps 和 summary。</fillRule><examples><example>required_datasets=price_bars,funding_rates</example></examples><commonMistakes><mistake>只写需要行情，不列字段和范围。</mistake></commonMistakes><blockingPrompt>请确认数据清单。</blockingPrompt></field>
  <field path="researcher_data_response"><zhName>研究员数据回应</zhName><meaning>记录研究员能否提供数据、路径或缺失项。</meaning><whyItMatters>用户数据优先于 agent 自行获取。</whyItMatters><fillRule>status 使用 pending、provided 或 cannot_provide。</fillRule><examples><example>status=provided</example></examples><commonMistakes><mistake>未询问用户就下载数据。</mistake></commonMistakes><blockingPrompt>请确认是否能提供数据。</blockingPrompt></field>
  <field path="agent_acquisition_plan"><zhName>Agent 数据获取计划</zhName><meaning>记录用户不能供数时的获取来源、命令、目标路径和审批状态。</meaning><whyItMatters>agent 获取必须可审计且先获批。</whyItMatters><fillRule>status 使用 not_needed、pending_approval、approved 或 rejected。</fillRule><examples><example>status=pending_approval</example></examples><commonMistakes><mistake>未获批就下载。</mistake></commonMistakes><blockingPrompt>请确认数据获取计划。</blockingPrompt></field>
  <field path="acquisition_provenance"><zhName>获取来源链路</zhName><meaning>记录获取运行状态、来源记录、snapshot、覆盖和失败原因。</meaning><whyItMatters>下载数据不能冒充已验证正式数据。</whyItMatters><fillRule>未运行时 run_status=not_run，并保留空 source_records。</fillRule><examples><example>run_status=not_run</example></examples><commonMistakes><mistake>数据下载失败但不记录失败原因。</mistake></commonMistakes><blockingPrompt>请确认数据获取 provenance。</blockingPrompt></field>
  <field path="active_repo_boundary"><zhName>Active Repo 边界</zhName><meaning>定义 handoff、数据和实现输出属于 active research repo。</meaning><whyItMatters>QROS 框架仓不能保存 live lineage 产物。</whyItMatters><fillRule>repo_role 必须是 active_research_repo，并填写 target_root。</fillRule><examples><example>target_root=outputs/paper_to_spec/example</example></examples><commonMistakes><mistake>写入 QROS framework repo。</mistake></commonMistakes><blockingPrompt>请确认 active repo 路径。</blockingPrompt></field>
  <field path="allowed_next_action"><zhName>允许下一动作</zhName><meaning>记录 handoff 之后唯一允许的下一步。</meaning><whyItMatters>防止跳过数据门槛或用户同意。</whyItMatters><fillRule>使用合同 allowed_next_actions。</fillRule><examples><example>validate_researcher_data</example></examples><commonMistakes><mistake>pending 状态下直接生成 scaffold。</mistake></commonMistakes><blockingPrompt>请确认下一步。</blockingPrompt></field>
  <field path="ambiguities"><zhName>歧义问题</zhName><meaning>记录 handoff 阶段阻塞问题。</meaning><whyItMatters>阻塞问题不能由 agent 猜测绕过。</whyItMatters><fillRule>填写 field、question、blocking。</fillRule><examples><example>field=data_readiness_brief.required_datasets</example></examples><commonMistakes><mistake>数据范围不清仍继续实现。</mistake></commonMistakes><blockingPrompt>blocking=true 时暂停。</blockingPrompt></field>
  <field path="implementation_handoff"><zhName>实现交接</zhName><meaning>记录输入、输出、验证检查和下一阶段建议。</meaning><whyItMatters>后续 active repo 实现必须消费明确 handoff。</whyItMatters><fillRule>填写 implementation_inputs、implementation_outputs、validation_checks、next_stage_recommendation。</fillRule><examples><example>next_stage_recommendation=validate_researcher_data</example></examples><commonMistakes><mistake>没有列出验证检查。</mistake></commonMistakes><blockingPrompt>请确认实现交接。</blockingPrompt></field>
  <blockingGroup name="implementation_consent"><zhName>实现同意</zhName><meaning>覆盖 implementation_decision。</meaning><whyItMatters>没有同意不能实现。</whyItMatters><fillRule>确认用户回答。</fillRule><examples><example>decision=accepted</example></examples><commonMistakes><mistake>把 valid specs 当成实现同意。</mistake></commonMistakes><blockingPrompt>请确认实现同意。</blockingPrompt></blockingGroup>
  <blockingGroup name="data_readiness"><zhName>数据准备</zhName><meaning>覆盖 data_readiness_brief 和 researcher_data_response。</meaning><whyItMatters>数据不清不能实现。</whyItMatters><fillRule>确认数据需求和用户回应。</fillRule><examples><example>required bars and funding provided</example></examples><commonMistakes><mistake>未列数据缺口。</mistake></commonMistakes><blockingPrompt>请确认数据准备。</blockingPrompt></blockingGroup>
  <blockingGroup name="agent_acquisition"><zhName>Agent 获取</zhName><meaning>覆盖 agent_acquisition_plan 和 acquisition_provenance。</meaning><whyItMatters>自动获取必须审批和留痕。</whyItMatters><fillRule>确认计划、审批和 provenance。</fillRule><examples><example>plan approved and provenance recorded</example></examples><commonMistakes><mistake>下载后没有 snapshot identity。</mistake></commonMistakes><blockingPrompt>请确认获取计划。</blockingPrompt></blockingGroup>
  <blockingGroup name="repo_boundary"><zhName>仓库边界</zhName><meaning>覆盖 active_repo_boundary。</meaning><whyItMatters>产物必须在 active repo。</whyItMatters><fillRule>确认 target_root 不是 QROS framework repo。</fillRule><examples><example>repo_role=active_research_repo</example></examples><commonMistakes><mistake>写入 contracts/。</mistake></commonMistakes><blockingPrompt>请确认仓库边界。</blockingPrompt></blockingGroup>
  <blockingGroup name="next_action"><zhName>下一动作</zhName><meaning>覆盖 allowed_next_action。</meaning><whyItMatters>只能执行当前状态允许的动作。</whyItMatters><fillRule>按 decision、data response 和 plan status 选择。</fillRule><examples><example>ask_researcher</example></examples><commonMistakes><mistake>未获批就 acquisition。</mistake></commonMistakes><blockingPrompt>请确认下一动作。</blockingPrompt></blockingGroup>
</paperSpecFieldGuide>
```

Modify `tests/contracts/test_paper_to_spec_field_guides.py` by adding this entry to `GUIDE_MAP`:

```python
    "paper_auto_implementation_handoff_contract.yaml": {
        "guide": "paper_auto_implementation_handoff.fields.xml",
        "artifact": "paper_auto_implementation_handoff.yaml",
        "core_container": "",
    },
```

Then update `test_paper_to_spec_xml_field_guides_cover_required_fields` so contracts without `core_required_fields` skip core path checks:

```python
        core_container = expected["core_container"]
        for field_name in contract.get("core_required_fields", []):
            path = f"{core_container}.{field_name}"
            assert path in fields, f"{expected['guide']} missing core field guide for {path}"
```

The existing loop already does nothing when `core_required_fields` is absent; no extra branch is needed.

- [ ] **Step 5: Run contract and XML tests**

Run:

```bash
python -m pytest tests/contracts/test_paper_auto_implementation_handoff_contract.py tests/contracts/test_paper_to_spec_field_guides.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit contract layer**

```bash
git add contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml \
  contracts/paper_to_spec/field_guides/paper_auto_implementation_handoff.fields.xml \
  tests/contracts/test_paper_auto_implementation_handoff_contract.py \
  tests/contracts/test_paper_to_spec_field_guides.py
git commit -m "feat: add paper auto implementation handoff contract"
```

### Task 2: Runtime Validator And Fixture

**Files:**
- Create: `tests/fixtures/paper_to_spec/valid_paper_auto_implementation_handoff.yaml`
- Create: `runtime/tools/paper_auto_implementation_handoff_runtime.py`
- Create: `runtime/scripts/validate_paper_auto_implementation_handoff.py`
- Test: `tests/runtime/test_paper_auto_implementation_handoff_runtime.py`

- [ ] **Step 1: Write the valid fixture**

Create `tests/fixtures/paper_to_spec/valid_paper_auto_implementation_handoff.yaml`:

```yaml
spec_version: v1
source:
  title: Example Crypto Perpetual Momentum Paper
  locator: tests/fixtures/paper_to_spec/example_summary.md
  source_kind: text_summary
  paper_slug: example_crypto_perp_momentum
paper_spec_chain:
  paper_data_spec:
    path: tests/fixtures/paper_to_spec/valid_paper_data_spec.yaml
    validation_status: valid
    digest: example_paper_data_spec_digest
  paper_signal_spec:
    path: tests/fixtures/paper_to_spec/valid_paper_signal_spec.yaml
    validation_status: valid
    digest: example_paper_signal_spec_digest
  paper_train_freeze_spec:
    path: tests/fixtures/paper_to_spec/valid_paper_train_freeze_spec.yaml
    validation_status: valid
    digest: example_paper_train_freeze_spec_digest
  paper_test_evidence_spec:
    path: tests/fixtures/paper_to_spec/valid_paper_test_evidence_spec.yaml
    validation_status: valid
    digest: example_paper_test_evidence_spec_digest
  paper_backtest_spec:
    path: tests/fixtures/paper_to_spec/valid_paper_backtest_spec.yaml
    validation_status: valid
    digest: example_paper_backtest_spec_digest
  paper_backtest_implementation_spec:
    path: tests/fixtures/paper_to_spec/valid_paper_backtest_implementation_spec.yaml
    validation_status: valid
    digest: example_paper_backtest_implementation_spec_digest
implementation_decision:
  decision: accepted
  prompt: Do you want QROS to automatically implement from these specs in the active research repo?
  answered_by: researcher
  answered_at: 2026-06-02T00:00:00Z
  evidence:
    - user_confirmed_auto_implementation
data_readiness_brief:
  required_datasets:
    - name: price_bars
      requirement: 1h OHLCV bars for selected crypto perpetual universe
      required: true
      fields:
        - timestamp
        - symbol
        - open
        - high
        - low
        - close
        - volume
      cadence: 1h
      time_range: 2023-01-01_to_2025-06-30
      source_constraints:
        - exchange_profile=generic_crypto_perp_or_user_selected
        - timestamps_utc
      expected_format: parquet
      missing_data_policy: fail_if_required_window_missing
      blocking: true
    - name: funding_rates
      requirement: funding rate observations aligned to exchange timestamps
      required: true
      fields:
        - timestamp
        - symbol
        - funding_rate
      cadence: exchange_funding_interval
      time_range: 2023-01-01_to_2025-06-30
      source_constraints:
        - same_exchange_profile_as_price_bars
        - timestamps_utc
      expected_format: parquet
      missing_data_policy: fail_if_required_window_missing
      blocking: true
  optional_datasets: []
  blocking_gaps: []
  summary: Required price bars and funding rates must exist before scaffold generation.
researcher_data_response:
  status: provided
  provided_paths:
    price_bars: /active-repo/data/asset_time_index.parquet
    funding_rates: /active-repo/data/funding_rates.parquet
  access_instructions: Use the active repo local data snapshot paths.
  missing_datasets: []
  evidence:
    - researcher_provided_paths
agent_acquisition_plan:
  status: not_needed
  sources: []
  approval:
    approved: false
    approved_by: ""
    approved_at: ""
  limitations: []
acquisition_provenance:
  run_status: not_run
  source_records: []
  snapshot_identity: ""
  coverage: {}
  validation_result: not_run
  failure_reason: ""
active_repo_boundary:
  repo_role: active_research_repo
  target_root: /active-repo/outputs/paper_to_spec/example_crypto_perp_momentum
  forbidden_root: qros_framework_repo
allowed_next_action: validate_researcher_data
ambiguities: []
implementation_handoff:
  implementation_inputs:
    - paper_backtest_implementation_spec.yaml
    - paper_auto_implementation_handoff.yaml
    - /active-repo/data/asset_time_index.parquet
    - /active-repo/data/funding_rates.parquet
  implementation_outputs:
    - data_readiness_report.yaml
    - active_repo_backtest_scaffold
  validation_checks:
    - all_paper_specs_valid
    - implementation_decision_accepted
    - required_data_paths_present
    - active_repo_boundary_not_qros_framework
  next_stage_recommendation: validate_researcher_data
```

- [ ] **Step 2: Write failing runtime tests**

Create `tests/runtime/test_paper_auto_implementation_handoff_runtime.py`:

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from runtime.tools.paper_auto_implementation_handoff_runtime import (
    validate_paper_auto_implementation_handoff,
)


ROOT = Path(__file__).resolve().parents[2]
VALID_SPEC = ROOT / "tests" / "fixtures" / "paper_to_spec" / "valid_paper_auto_implementation_handoff.yaml"
SCRIPT = ROOT / "runtime" / "scripts" / "validate_paper_auto_implementation_handoff.py"


def _load_valid_spec() -> dict:
    return yaml.safe_load(VALID_SPEC.read_text(encoding="utf-8"))


def test_valid_paper_auto_implementation_handoff_fixture_passes_contract_validation() -> None:
    result = validate_paper_auto_implementation_handoff(VALID_SPEC)

    assert result.valid
    assert result.findings == []


def test_validator_fails_when_required_top_level_field_missing(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload.pop("implementation_decision")
    spec_path = tmp_path / "paper_auto_implementation_handoff.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_auto_implementation_handoff(spec_path)

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_MISSING_FIELD",
        "missing top-level field: implementation_decision",
    ) in result.findings


def test_validator_blocks_when_any_paper_spec_is_not_valid(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["paper_spec_chain"]["paper_backtest_spec"]["validation_status"] = "blocked"
    spec_path = tmp_path / "paper_auto_implementation_handoff.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_auto_implementation_handoff(spec_path)

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_SPEC_CHAIN_NOT_VALID",
        "paper_spec_chain.paper_backtest_spec.validation_status must be valid before implementation handoff",
    ) in result.findings


def test_validator_allows_declined_decision_only_with_stop_action(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_decision"]["decision"] = "declined"
    payload["researcher_data_response"]["status"] = "pending"
    payload["allowed_next_action"] = "stop_after_specs"
    payload["implementation_handoff"]["next_stage_recommendation"] = "stop_after_specs"
    spec_path = tmp_path / "paper_auto_implementation_handoff.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_auto_implementation_handoff(spec_path)

    assert result.valid
    assert result.findings == []


def test_validator_blocks_pending_decision_with_implementation_action(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["implementation_decision"]["decision"] = "pending"
    payload["allowed_next_action"] = "generate_active_repo_backtest_scaffold"
    spec_path = tmp_path / "paper_auto_implementation_handoff.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_auto_implementation_handoff(spec_path)

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_CONSENT_REQUIRED",
        "implementation_decision.decision must be accepted before implementation actions",
    ) in result.findings


def test_validator_blocks_agent_acquisition_without_approval(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["researcher_data_response"]["status"] = "cannot_provide"
    payload["agent_acquisition_plan"]["status"] = "pending_approval"
    payload["agent_acquisition_plan"]["sources"] = [
        {
            "dataset": "price_bars",
            "source": "exchange_api",
            "command": "python acquire_price_bars.py",
            "storage_target": "/active-repo/data/asset_time_index.parquet",
            "approval_required": True,
        }
    ]
    payload["allowed_next_action"] = "run_agent_data_acquisition"
    spec_path = tmp_path / "paper_auto_implementation_handoff.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_auto_implementation_handoff(spec_path)

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_ACQUISITION_NOT_APPROVED",
        "agent_acquisition_plan.status must be approved before run_agent_data_acquisition",
    ) in result.findings


def test_validator_blocks_framework_repo_target(tmp_path: Path) -> None:
    payload = _load_valid_spec()
    payload["active_repo_boundary"]["repo_role"] = "qros_framework_repo"
    spec_path = tmp_path / "paper_auto_implementation_handoff.yaml"
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_paper_auto_implementation_handoff(spec_path)

    assert not result.valid
    assert (
        "PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET",
        "active_repo_boundary must target active research repo, not QROS framework repo",
    ) in result.findings


def test_validate_paper_auto_implementation_handoff_script_reports_success() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec-path", str(VALID_SPEC)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "paper_auto_implementation_handoff valid" in completed.stdout
    assert completed.stderr == ""
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```bash
python -m pytest tests/runtime/test_paper_auto_implementation_handoff_runtime.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'runtime.tools.paper_auto_implementation_handoff_runtime'`.

- [ ] **Step 4: Implement validator module**

Create `runtime/tools/paper_auto_implementation_handoff_runtime.py` using the existing paper validator style:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_PATH = ROOT / "contracts" / "paper_to_spec" / "paper_auto_implementation_handoff_contract.yaml"
FRAMEWORK_REPO_TOKENS = ("qros_framework_repo", "quant-research-os/framework", "qros framework repo")
IMPLEMENTATION_ACTIONS = {
    "validate_researcher_data",
    "run_agent_data_acquisition",
    "generate_active_repo_backtest_scaffold",
}


@dataclass(frozen=True)
class PaperAutoImplementationHandoffValidationResult:
    spec_path: Path
    contract_path: Path
    findings: list[tuple[str, str]]

    @property
    def valid(self) -> bool:
        return not self.findings

    @property
    def reason_codes(self) -> list[str]:
        observed: list[str] = []
        for code, _ in self.findings:
            if code not in observed:
                observed.append(code)
        return observed


def validate_paper_auto_implementation_handoff(
    spec_path: Path,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> PaperAutoImplementationHandoffValidationResult:
    spec_path = spec_path.resolve()
    contract_path = contract_path.resolve()
    findings: list[tuple[str, str]] = []

    contract = _load_yaml_map(contract_path, "PAPER_AUTO_IMPLEMENTATION_HANDOFF_CONTRACT_INVALID", findings)
    payload = _load_yaml_map(spec_path, "PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_YAML", findings)
    if not isinstance(contract, dict) or not isinstance(payload, dict):
        return PaperAutoImplementationHandoffValidationResult(spec_path, contract_path, findings)

    findings.extend(_validate_top_level(payload, contract))
    findings.extend(_validate_source(payload.get("source"), contract))
    findings.extend(_validate_paper_spec_chain(payload.get("paper_spec_chain"), contract))
    findings.extend(_validate_implementation_decision(payload.get("implementation_decision"), contract))
    findings.extend(_validate_data_readiness_brief(payload.get("data_readiness_brief"), contract))
    findings.extend(_validate_researcher_data_response(payload.get("researcher_data_response"), contract))
    findings.extend(_validate_agent_acquisition_plan(payload.get("agent_acquisition_plan"), contract))
    findings.extend(_validate_acquisition_provenance(payload.get("acquisition_provenance"), contract))
    findings.extend(_validate_active_repo_boundary(payload.get("active_repo_boundary"), contract))
    findings.extend(_validate_allowed_next_action(payload, contract))
    findings.extend(_validate_ambiguities(payload.get("ambiguities"), contract))
    findings.extend(_validate_implementation_handoff(payload.get("implementation_handoff"), contract))
    return PaperAutoImplementationHandoffValidationResult(spec_path, contract_path, findings)


def _load_yaml_map(path: Path, code: str, findings: list[tuple[str, str]]) -> dict[str, Any] | None:
    if not path.exists():
        findings.append((code, f"missing yaml file: {path}"))
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        findings.append((code, f"{path}: invalid yaml: {exc}"))
        return None
    if not isinstance(payload, dict):
        findings.append((code, f"{path}: yaml root must be a mapping"))
        return None
    return payload


def _validate_top_level(payload: dict[str, Any], contract: dict[str, Any]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for field in contract.get("required_top_level_fields", []):
        if field not in payload:
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_MISSING_FIELD", f"missing top-level field: {field}"))
    if payload.get("spec_version") != contract.get("spec_version"):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_VERSION", f"spec_version must be {contract.get('spec_version')!r}"))
    return findings


def _validate_source(source: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(source, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "source must be a mapping")]
    findings = _require_fields("source", source, contract.get("required_source_fields", []))
    findings.extend(_validate_enum("source.source_kind", source.get("source_kind"), contract.get("allowed_source_kinds", [])))
    return findings


def _validate_paper_spec_chain(chain: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(chain, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "paper_spec_chain must be a mapping")]
    findings: list[tuple[str, str]] = []
    for spec_name in contract.get("required_paper_spec_chain_fields", []):
        if spec_name not in chain:
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_MISSING_FIELD", f"paper_spec_chain.{spec_name}: missing required spec reference"))
            continue
        reference = chain[spec_name]
        if not isinstance(reference, dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"paper_spec_chain.{spec_name} must be a mapping"))
            continue
        path = f"paper_spec_chain.{spec_name}"
        findings.extend(_require_fields(path, reference, contract.get("required_spec_reference_fields", [])))
        findings.extend(_validate_enum(f"{path}.validation_status", reference.get("validation_status"), contract.get("allowed_spec_validation_statuses", [])))
        if reference.get("validation_status") != "valid":
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_SPEC_CHAIN_NOT_VALID", f"{path}.validation_status must be valid before implementation handoff"))
    return findings


def _validate_implementation_decision(decision: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(decision, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "implementation_decision must be a mapping")]
    findings = _require_fields("implementation_decision", decision, contract.get("required_implementation_decision_fields", []))
    findings.extend(_validate_enum("implementation_decision.decision", decision.get("decision"), contract.get("allowed_implementation_decisions", [])))
    return findings


def _validate_data_readiness_brief(brief: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(brief, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "data_readiness_brief must be a mapping")]
    findings = _require_fields("data_readiness_brief", brief, contract.get("required_data_readiness_brief_fields", []))
    for list_field in ["required_datasets", "optional_datasets", "blocking_gaps"]:
        if list_field in brief and not isinstance(brief.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"data_readiness_brief.{list_field} must be a list"))
    for list_field in ["required_datasets", "optional_datasets"]:
        for index, item in enumerate(brief.get(list_field, [])):
            path = f"data_readiness_brief.{list_field}[{index}]"
            if not isinstance(item, dict):
                findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"{path} must be a mapping"))
                continue
            findings.extend(_require_fields(path, item, contract.get("required_data_item_fields", [])))
            if "fields" in item and not isinstance(item.get("fields"), list):
                findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.fields must be a list"))
            if "blocking" in item and not isinstance(item.get("blocking"), bool):
                findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.blocking must be a boolean"))
    return findings


def _validate_researcher_data_response(response: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(response, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "researcher_data_response must be a mapping")]
    findings = _require_fields("researcher_data_response", response, contract.get("required_researcher_data_response_fields", []))
    findings.extend(_validate_enum("researcher_data_response.status", response.get("status"), contract.get("allowed_researcher_data_statuses", [])))
    for list_field in ["missing_datasets", "evidence"]:
        if list_field in response and not isinstance(response.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"researcher_data_response.{list_field} must be a list"))
    if "provided_paths" in response and not isinstance(response.get("provided_paths"), dict):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", "researcher_data_response.provided_paths must be a mapping"))
    return findings


def _validate_agent_acquisition_plan(plan: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(plan, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "agent_acquisition_plan must be a mapping")]
    findings = _require_fields("agent_acquisition_plan", plan, contract.get("required_agent_acquisition_plan_fields", []))
    findings.extend(_validate_enum("agent_acquisition_plan.status", plan.get("status"), contract.get("allowed_acquisition_plan_statuses", [])))
    if "sources" in plan and not isinstance(plan.get("sources"), list):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", "agent_acquisition_plan.sources must be a list"))
    for index, source in enumerate(plan.get("sources", [])):
        path = f"agent_acquisition_plan.sources[{index}]"
        if not isinstance(source, dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"{path} must be a mapping"))
            continue
        findings.extend(_require_fields(path, source, contract.get("required_acquisition_source_fields", [])))
        if "approval_required" in source and not isinstance(source.get("approval_required"), bool):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.approval_required must be a boolean"))
    if "limitations" in plan and not isinstance(plan.get("limitations"), list):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", "agent_acquisition_plan.limitations must be a list"))
    return findings


def _validate_acquisition_provenance(provenance: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(provenance, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "acquisition_provenance must be a mapping")]
    findings = _require_fields("acquisition_provenance", provenance, contract.get("required_acquisition_provenance_fields", []))
    findings.extend(_validate_enum("acquisition_provenance.run_status", provenance.get("run_status"), contract.get("allowed_acquisition_run_statuses", [])))
    if "source_records" in provenance and not isinstance(provenance.get("source_records"), list):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", "acquisition_provenance.source_records must be a list"))
    return findings


def _validate_active_repo_boundary(boundary: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(boundary, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "active_repo_boundary must be a mapping")]
    findings = _require_fields("active_repo_boundary", boundary, contract.get("required_active_repo_boundary_fields", []))
    combined = f"{boundary.get('repo_role', '')} {boundary.get('target_root', '')}".lower()
    if any(token in combined for token in FRAMEWORK_REPO_TOKENS):
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_FRAMEWORK_REPO_TARGET", "active_repo_boundary must target active research repo, not QROS framework repo"))
    return findings


def _validate_allowed_next_action(payload: dict[str, Any], contract: dict[str, Any]) -> list[tuple[str, str]]:
    action = payload.get("allowed_next_action")
    findings = _validate_enum("allowed_next_action", action, contract.get("allowed_next_actions", []))
    decision = payload.get("implementation_decision", {})
    decision_value = decision.get("decision") if isinstance(decision, dict) else None
    if action in IMPLEMENTATION_ACTIONS and decision_value != "accepted":
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_CONSENT_REQUIRED", "implementation_decision.decision must be accepted before implementation actions"))
    plan = payload.get("agent_acquisition_plan", {})
    plan_status = plan.get("status") if isinstance(plan, dict) else None
    if action == "run_agent_data_acquisition" and plan_status != "approved":
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_ACQUISITION_NOT_APPROVED", "agent_acquisition_plan.status must be approved before run_agent_data_acquisition"))
    if decision_value == "declined" and action != "stop_after_specs":
        findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_DECLINED_ACTION_INVALID", "declined implementation_decision requires allowed_next_action stop_after_specs"))
    return findings


def _validate_ambiguities(ambiguities: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(ambiguities, list):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "ambiguities must be a list")]
    findings: list[tuple[str, str]] = []
    for index, ambiguity in enumerate(ambiguities):
        path = f"ambiguities[{index}]"
        if not isinstance(ambiguity, dict):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", f"{path} must be a mapping"))
            continue
        findings.extend(_require_fields(path, ambiguity, contract.get("required_ambiguity_fields", [])))
        if "blocking" in ambiguity and not isinstance(ambiguity.get("blocking"), bool):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"{path}.blocking must be a boolean"))
    return findings


def _validate_implementation_handoff(handoff: Any, contract: dict[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(handoff, dict):
        return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_SECTION", "implementation_handoff must be a mapping")]
    findings = _require_fields("implementation_handoff", handoff, contract.get("required_implementation_handoff_fields", []))
    for list_field in ["implementation_inputs", "implementation_outputs", "validation_checks"]:
        if list_field in handoff and not isinstance(handoff.get(list_field), list):
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_TYPE", f"implementation_handoff.{list_field} must be a list"))
    findings.extend(_validate_enum("implementation_handoff.next_stage_recommendation", handoff.get("next_stage_recommendation"), contract.get("allowed_next_actions", [])))
    return findings


def _require_fields(path: str, payload: dict[str, Any], fields: list[str]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for field in fields:
        if field not in payload:
            findings.append(("PAPER_AUTO_IMPLEMENTATION_HANDOFF_MISSING_FIELD", f"{path}.{field}: missing required field"))
    return findings


def _validate_enum(path: str, value: Any, allowed_values: list[str]) -> list[tuple[str, str]]:
    if value in allowed_values:
        return []
    return [("PAPER_AUTO_IMPLEMENTATION_HANDOFF_INVALID_ENUM", f"{path} must be one of {allowed_values}")]
```

- [ ] **Step 5: Add the CLI wrapper**

Create `runtime/scripts/validate_paper_auto_implementation_handoff.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.paper_auto_implementation_handoff_runtime import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    validate_paper_auto_implementation_handoff,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a QROS paper_auto_implementation_handoff.yaml artifact.")
    parser.add_argument("--spec-path", type=Path, required=True)
    parser.add_argument("--contract-path", type=Path, default=DEFAULT_CONTRACT_PATH)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = validate_paper_auto_implementation_handoff(args.spec_path, args.contract_path)
    if not result.valid:
        for reason_code, message in result.findings:
            print(f"{reason_code}: {message}", file=sys.stderr)
        return 1

    print(f"paper_auto_implementation_handoff valid: {result.spec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Run runtime tests**

Run:

```bash
python -m pytest tests/runtime/test_paper_auto_implementation_handoff_runtime.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit runtime layer**

```bash
git add tests/fixtures/paper_to_spec/valid_paper_auto_implementation_handoff.yaml \
  runtime/tools/paper_auto_implementation_handoff_runtime.py \
  runtime/scripts/validate_paper_auto_implementation_handoff.py \
  tests/runtime/test_paper_auto_implementation_handoff_runtime.py
git commit -m "feat: validate paper auto implementation handoff"
```

### Task 3: Skill And User Documentation

**Files:**
- Modify: `skills/core/qros-paper-to-spec/SKILL.md`
- Modify: `docs/guides/qros-paper-to-spec-usage.md`
- Test: `tests/skills/test_paper_to_spec_assets.py`
- Test: `tests/docs/test_paper_to_spec_docs.py`

- [ ] **Step 1: Update failing skill/doc tests first**

Modify the required string arrays in `tests/skills/test_paper_to_spec_assets.py` and `tests/docs/test_paper_to_spec_docs.py` to include these exact strings:

```python
        "paper_auto_implementation_handoff.yaml",
        "post-spec implementation prompt",
        "Data Readiness Brief",
        "Do you want QROS to automatically implement from these specs in the active research repo?",
        "researcher can provide required data",
        "agent acquisition plan",
        "agent-driven data acquisition",
        "must not download, materialize, or claim availability",
        "active research repo",
        "not QROS framework repo",
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py -q
```

Expected: FAIL because the skill and docs do not yet contain the new handoff wording.

- [ ] **Step 3: Update skill instructions**

Add this section to `skills/core/qros-paper-to-spec/SKILL.md` after the Backtest Implementation Execution Protocol:

```markdown
## Post-Spec Auto Implementation Handoff

After the requested PaperSpec chain is generated and validators pass, do not silently stop and do not silently implement. Present this post-spec implementation prompt:

```text
All requested PaperSpec artifacts are valid.
Do you want QROS to automatically implement from these specs in the active research repo?
```

If the researcher declines or does not answer, preserve the generated specs and stop. Do not generate implementation code, download data, create scaffold files, or write live lineage artifacts.

If the researcher accepts, create or update `paper_auto_implementation_handoff.yaml` in the active research repo. The handoff must first include a Data Readiness Brief derived from `paper_data_spec.yaml`, downstream specs, and `paper_backtest_implementation_spec.yaml`.

The Data Readiness Brief must list:

- required datasets
- optional datasets
- market and venue scope
- symbol universe
- bar cadence and time range
- required fields
- expected formats
- source constraints
- provenance requirements
- missing-data policy
- blocking data gaps

Ask whether the researcher can provide required data before any agent-driven data acquisition.

If the researcher can provide required data, collect paths, snapshots, credentials, or access instructions and validate those inputs against the Data Readiness Brief.

If the researcher cannot provide required data, present an agent acquisition plan before taking action. The plan must list source, symbols, time range, fields, command or tool, active repo storage target, expected artifacts, and limitations. The system must not download, materialize, or claim availability of required data until the researcher approves the agent acquisition plan.

All handoff artifacts, downloaded data, snapshots, implementation code, and live lineage outputs must be written to the active research repo, not QROS framework repo.
```
```

- [ ] **Step 4: Update user guide**

Add the matching section to `docs/guides/qros-paper-to-spec-usage.md` after the Backtest Implementation validator section:

```markdown
## Auto Implementation Handoff

When all requested PaperSpec artifacts are valid, `qros-paper-to-spec` must ask:

```text
All requested PaperSpec artifacts are valid.
Do you want QROS to automatically implement from these specs in the active research repo?
```

This is a post-spec implementation prompt. A valid `paper_backtest_implementation_spec.yaml` does not itself authorize implementation, scaffold generation, data download, or active repo writes.

If the researcher opts in, QROS must first produce a Data Readiness Brief and record the decision in `paper_auto_implementation_handoff.yaml` in the active research repo.

The Data Readiness Brief must tell the researcher which data is required, including datasets, fields, cadence, time range, market scope, expected format, source constraints, provenance requirements, and missing-data policy.

QROS must ask whether the researcher can provide required data. If the researcher can provide it, QROS records paths, snapshots, credentials, or access instructions and validates them before implementation proceeds.

If the researcher cannot provide required data, QROS may prepare an agent acquisition plan. The plan must be approved before agent-driven data acquisition. QROS must not download, materialize, or claim availability of required data before that approval.

Downloaded data, snapshots, implementation code, scaffold output, and live lineage artifacts belong in the active research repo, not QROS framework repo.
```
```

- [ ] **Step 5: Run skill/doc tests**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit skill and docs**

```bash
git add skills/core/qros-paper-to-spec/SKILL.md \
  docs/guides/qros-paper-to-spec-usage.md \
  tests/skills/test_paper_to_spec_assets.py \
  tests/docs/test_paper_to_spec_docs.py
git commit -m "docs: describe paper auto implementation handoff"
```

### Task 4: OpenSpec And Verification Integration

**Files:**
- Modify: `openspec/changes/add-paper-to-spec-auto-implementation-handoff/tasks.md`
- Optionally modify: `openspec/changes/add-paper-to-spec-auto-implementation-handoff/specs/paper-to-spec-implementation-handoff/spec.md` if implementation reveals wording drift

- [ ] **Step 1: Mark completed OpenSpec tasks during implementation**

After Tasks 1-3 pass, update `openspec/changes/add-paper-to-spec-auto-implementation-handoff/tasks.md` by changing completed task checkboxes to checked. Use exact checkbox syntax:

```markdown
- [x] 1.1 Decide whether to add a new `paper_auto_implementation_handoff.yaml` contract under `contracts/paper_to_spec/` or reuse an existing implementation handoff section.
```

Expected: every completed implementation item has `[x]`; incomplete verification items remain `[ ]` until run.

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest \
  tests/contracts/test_paper_auto_implementation_handoff_contract.py \
  tests/contracts/test_paper_to_spec_field_guides.py \
  tests/runtime/test_paper_auto_implementation_handoff_runtime.py \
  tests/skills/test_paper_to_spec_assets.py \
  tests/docs/test_paper_to_spec_docs.py \
  -q
```

Expected: PASS.

- [ ] **Step 3: Run docs/bootstrap minimum**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [ ] **Step 4: Run OpenSpec strict validation**

Run:

```bash
openspec validate --all --strict --no-interactive
```

Expected: PASS with all specs and active changes valid.

- [ ] **Step 5: Run smoke tier**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 6: Decide whether full-smoke is required**

Run full-smoke only if implementation touched `qros-research-session` stage flow, gate semantics, review orchestration, route split, anti-drift snapshots, stage-display supported stage contracts, or lineage-local stage-program auto-author behavior.

If full-smoke is not required, record this in the final report:

```text
full-smoke not run: change is scoped to paper-to-spec handoff contract, validator, skill, docs, and tests; it does not change qros-research-session stage flow/gate/review/route/stage-display/auto-author behavior.
```

If full-smoke is required, run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS.

- [ ] **Step 7: Commit verification/task updates**

```bash
git add openspec/changes/add-paper-to-spec-auto-implementation-handoff/tasks.md
git commit -m "chore: mark paper implementation handoff tasks"
```

### Task 5: Archive The OpenSpec Change After Implementation

**Files:**
- Modify via OpenSpec archive: `openspec/changes/archive/<date>-add-paper-to-spec-auto-implementation-handoff/`
- Modify via OpenSpec archive: `openspec/specs/paper-to-spec-implementation-handoff/spec.md`

- [ ] **Step 1: Confirm implementation is complete**

Run:

```bash
openspec status --change add-paper-to-spec-auto-implementation-handoff
```

Expected: all artifacts complete and implementation tasks marked done.

- [ ] **Step 2: Archive the change**

Run:

```bash
openspec archive add-paper-to-spec-auto-implementation-handoff --yes
```

Expected: the change moves under `openspec/changes/archive/` and the live spec is created or updated under `openspec/specs/paper-to-spec-implementation-handoff/spec.md`.

- [ ] **Step 3: Validate archived spec**

Run:

```bash
openspec validate --all --strict --no-interactive
```

Expected: PASS.

- [ ] **Step 4: Commit archive**

```bash
git add openspec
git commit -m "chore: archive paper implementation handoff spec"
```

## Self-Review

Spec coverage:

- Post-spec implementation prompt is covered by Task 3 skill/docs and Task 2 validator decision tests.
- Opt-in behavior is covered by Task 2 pending/declined/accepted tests.
- Data Readiness Brief is covered by Task 1 contract fields, Task 2 fixture, and Task 3 docs/skill.
- Researcher-provided data preference is covered by `researcher_data_response` contract fields and Task 2 valid fixture.
- Agent acquisition control is covered by `agent_acquisition_plan`, `acquisition_provenance`, and the no-approval runtime test.
- Machine-readable handoff state is covered by the new contract, fixture, validator, XML guide, and CLI wrapper.
- PaperSpec boundaries are covered by active repo boundary validator and docs/skill wording.

Placeholder scan:

- The plan contains no unresolved placeholders, deferred implementation notes, cross-task shorthand, or unspecified test requests.
- Every code-changing task includes concrete file paths, code blocks, commands, and expected outcomes.

Type consistency:

- Contract, fixture, validator, tests, CLI, docs, and skill all use `paper_auto_implementation_handoff`.
- Validator class is `PaperAutoImplementationHandoffValidationResult`.
- Validator function is `validate_paper_auto_implementation_handoff`.
- CLI script is `validate_paper_auto_implementation_handoff.py`.
