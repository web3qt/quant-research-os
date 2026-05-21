# Mandate Admission Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the normal `idea_intake -> mandate` first-stage workflow with a single `mandate` stage that begins with `mandate_admission` and uses one user confirmation before authoring formal mandate artifacts.

**Architecture:** Introduce a compressed `mandate_admission.yaml` draft contract under `01_mandate/author/draft/`, move normal first-stage detection to `mandate_admission`, and update mandate authoring to consume mandate draft files instead of `00_idea_intake`. Keep `author/draft/` mutable and keep existing `author/formal/*` as the frozen downstream surface.

**Tech Stack:** Python runtime tools, YAML artifact contracts, pytest, QROS session CLI wrappers, existing `freeze_contract_runtime` digest helpers, existing stage program scaffold and review preflight.

---

## File Structure

- Create: `contracts/artifacts/mandate_admission_artifacts.yaml`
- Create: `runtime/tools/mandate_admission_runtime.py`
- Modify: `runtime/tools/artifact_contract_runtime.py`
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/scripts/run_research_session.py`
- Modify: `runtime/tools/idea_runtime.py`
- Modify: `runtime/tools/stage_program_scaffold.py`
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `skills/core/using-qros/SKILL.md`
- Modify: `skills/idea_intake/qros-idea-intake-author/SKILL.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/idea-intake-to-mandate-flow.md`
- Modify: `docs/guides/quickstart-codex.md`
- Modify: `tests/session/test_research_session_runtime.py`
- Modify: `tests/session/test_run_research_session_script.py`
- Modify: `tests/session/test_idea_runtime_scripts.py`
- Modify: `tests/runtime/test_artifact_contract_runtime.py`
- Modify: `tests/runtime/test_validate_stage_artifacts_script.py`
- Modify: `tests/bootstrap/test_project_bootstrap.py`
- Modify or delete: tests that assert normal-path `idea_intake` guidance, including `tests/session/test_idea_intake_artifact_shape.py`, `tests/contracts/test_idea_intake_artifact_contract.py`, `tests/skills/test_idea_intake_shape_contract_guidance.py`, and `tests/session/test_idea_intake_assets.py`

## Task 1: Add Mandate Admission Contract

**Files:**
- Create: `contracts/artifacts/mandate_admission_artifacts.yaml`
- Modify: `runtime/tools/artifact_contract_runtime.py`
- Modify: `tests/runtime/test_artifact_contract_runtime.py`
- Modify: `tests/bootstrap/test_project_bootstrap.py`

- [ ] **Step 1: Write failing contract load test**

Add this test to `tests/runtime/test_artifact_contract_runtime.py`:

```python
def test_load_artifact_contract_supports_mandate_admission() -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract

    contract = load_artifact_contract("mandate_admission")

    assert contract["schema_id"] == "mandate-admission-artifacts-v1"
    assert contract["stage"] == "mandate_admission"
    assert contract["stage_dir"] == "01_mandate/author/draft"
    assert "mandate_admission.yaml" in contract["artifacts"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py::test_load_artifact_contract_supports_mandate_admission -q
```

Expected: fail with `unsupported artifact contract stage: mandate_admission`.

- [ ] **Step 3: Create the contract file**

Create `contracts/artifacts/mandate_admission_artifacts.yaml` with this content:

```yaml
schema_id: mandate-admission-artifacts-v1
schema_version: v1
stage: mandate_admission
stage_dir: 01_mandate/author/draft
unknown_machine_top_level_fields: forbid

artifacts:
  mandate_admission.yaml:
    type: yaml
    unknown_top_level_fields: forbid
    fields:
      - path: lineage_id
        description: 标识当前研究 lineage，用于把 admission 判断绑定到唯一研究线。
        type: string
      - path: raw_idea
        description: 记录用户原始研究想法，用于审计 mandate 来源。
        type: string
      - path: observation
        description: 记录可观察市场现象，禁止直接把想法写成收益结论。
        type: string
      - path: primary_hypothesis
        description: 记录主假设，用于说明为什么该现象可能形成可研究边。
        type: string
      - path: counter_hypothesis
        description: 记录对立假设，用于防止只采纳支持性叙事。
        type: string
      - path: research_questions
        description: 记录主要研究问题和必要子问题。
        type: list[string]
        default: []
      - path: scope
        description: 记录 admission 批准范围。
        type: map
      - path: scope.market
        description: 声明研究市场。
        type: string
      - path: scope.instrument_type
        description: 声明交易品种类型。
        type: string
        default: ""
      - path: scope.universe
        description: 声明研究标的池。
        type: string
      - path: scope.data_source
        description: 声明数据来源。
        type: string
      - path: scope.bar_size
        description: 声明基础 K 线或采样粒度。
        type: string
      - path: scope.holding_horizons
        description: 列出研究持有周期。
        type: list[string]
        default: []
      - path: scope.target_task
        description: 声明目标研究任务。
        type: string
      - path: scope.excluded_scope
        description: 列出明确排除范围。
        type: list[string]
        default: []
      - path: scope.budget_days
        description: 声明研究预算天数。
        type: integer
        default: 0
      - path: scope.max_iterations
        description: 声明最大研究迭代次数。
        type: integer
        default: 0
      - path: qualification
        description: 记录想法资格评分。
        type: map
      - path: qualification.summary
        description: 记录资格评分摘要。
        type: string
        default: ""
      - path: qualification.dimensions
        description: 承载各资格评分维度。
        type: map
      - path: qualification.dimensions.observability.score
        description: 记录可观测性评分。
        type: integer
        default: 0
      - path: qualification.dimensions.observability.evidence
        description: 记录可观测性证据。
        type: list[string]
        default: []
      - path: qualification.dimensions.observability.uncertainty
        description: 记录可观测性不确定性。
        type: list[string]
        default: []
      - path: qualification.dimensions.observability.kill_reason
        description: 记录可观测性终止原因。
        type: list[string]
        default: []
      - path: qualification.dimensions.mechanism_plausibility.score
        description: 记录机制可信度评分。
        type: integer
        default: 0
      - path: qualification.dimensions.mechanism_plausibility.evidence
        description: 记录机制可信度证据。
        type: list[string]
        default: []
      - path: qualification.dimensions.mechanism_plausibility.uncertainty
        description: 记录机制可信度不确定性。
        type: list[string]
        default: []
      - path: qualification.dimensions.mechanism_plausibility.kill_reason
        description: 记录机制可信度终止原因。
        type: list[string]
        default: []
      - path: qualification.dimensions.tradeability.score
        description: 记录可交易性评分。
        type: integer
        default: 0
      - path: qualification.dimensions.tradeability.evidence
        description: 记录可交易性证据。
        type: list[string]
        default: []
      - path: qualification.dimensions.tradeability.uncertainty
        description: 记录可交易性不确定性。
        type: list[string]
        default: []
      - path: qualification.dimensions.tradeability.kill_reason
        description: 记录可交易性终止原因。
        type: list[string]
        default: []
      - path: qualification.dimensions.data_feasibility.score
        description: 记录数据可行性评分。
        type: integer
        default: 0
      - path: qualification.dimensions.data_feasibility.evidence
        description: 记录数据可行性证据。
        type: list[string]
        default: []
      - path: qualification.dimensions.data_feasibility.uncertainty
        description: 记录数据可行性不确定性。
        type: list[string]
        default: []
      - path: qualification.dimensions.data_feasibility.kill_reason
        description: 记录数据可行性终止原因。
        type: list[string]
        default: []
      - path: qualification.dimensions.scoping_clarity.score
        description: 记录范围清晰度评分。
        type: integer
        default: 0
      - path: qualification.dimensions.scoping_clarity.evidence
        description: 记录范围清晰度证据。
        type: list[string]
        default: []
      - path: qualification.dimensions.scoping_clarity.uncertainty
        description: 记录范围清晰度不确定性。
        type: list[string]
        default: []
      - path: qualification.dimensions.scoping_clarity.kill_reason
        description: 记录范围清晰度终止原因。
        type: list[string]
        default: []
      - path: qualification.dimensions.distinctiveness.score
        description: 记录差异化评分。
        type: integer
        default: 0
      - path: qualification.dimensions.distinctiveness.evidence
        description: 记录差异化证据。
        type: list[string]
        default: []
      - path: qualification.dimensions.distinctiveness.uncertainty
        description: 记录差异化不确定性。
        type: list[string]
        default: []
      - path: qualification.dimensions.distinctiveness.kill_reason
        description: 记录差异化终止原因。
        type: list[string]
        default: []
      - path: route_assessment
        description: 记录 route 判断。
        type: map
      - path: route_assessment.candidate_routes
        description: 列出候选研究路线。
        type: list[string]
        allowed_values_if_nonempty:
          - time_series_signal
          - cross_sectional_factor
      - path: route_assessment.recommended_route
        description: 声明推荐研究路线。
        type: string
        allowed_values_if_nonempty:
          - time_series_signal
          - cross_sectional_factor
      - path: route_assessment.why_recommended
        description: 记录路线推荐理由。
        type: list[string]
        default: []
      - path: route_assessment.why_not_other_routes
        description: 记录未选择其他路线的理由。
        type: map
        default: {}
      - path: route_assessment.route_risks
        description: 记录路线风险。
        type: list[string]
        default: []
      - path: route_assessment.route_decision_pending
        description: 记录路线决策是否待确认。
        type: boolean
        default: true
      - path: admission_decision
        description: 记录 mandate admission 结论。
        type: map
      - path: admission_decision.verdict
        description: 声明 admission 结论。
        type: enum
        values:
          - ACCEPT_FOR_MANDATE
          - NEEDS_REFRAME
          - DROP
        default: NEEDS_REFRAME
      - path: admission_decision.why
        description: 记录 admission 结论理由。
        type: list[string]
        default: []
      - path: admission_decision.kill_criteria
        description: 记录终止条件。
        type: list[string]
        default: []
      - path: admission_decision.required_reframe_actions
        description: 记录必须完成的重构动作。
        type: list[string]
        default: []
```

- [ ] **Step 4: Register the contract**

Add this entry to `ARTIFACT_CONTRACTS` in `runtime/tools/artifact_contract_runtime.py`:

```python
"mandate_admission": ROOT / "contracts" / "artifacts" / "mandate_admission_artifacts.yaml",
```

- [ ] **Step 5: Update bootstrap test**

In `tests/bootstrap/test_project_bootstrap.py`, add:

```python
assert Path("contracts/artifacts/mandate_admission_artifacts.yaml").exists()
```

- [ ] **Step 6: Run focused contract tests**

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py::test_load_artifact_contract_supports_mandate_admission tests/bootstrap/test_project_bootstrap.py -q
```

Expected: pass.

- [ ] **Step 7: Commit checkpoint**

If commit authorization is present for the implementation session:

```bash
git add contracts/artifacts/mandate_admission_artifacts.yaml runtime/tools/artifact_contract_runtime.py tests/runtime/test_artifact_contract_runtime.py tests/bootstrap/test_project_bootstrap.py
git commit -m "feat: add mandate admission artifact contract"
```

## Task 2: Add Mandate Admission Runtime Helpers

**Files:**
- Create: `runtime/tools/mandate_admission_runtime.py`
- Modify: `tests/session/test_research_session_runtime.py`

- [ ] **Step 1: Add failing tests for scaffold and admission readiness**

Add imports in `tests/session/test_research_session_runtime.py`:

```python
from runtime.tools.mandate_admission_runtime import (
    admission_ready_for_freeze,
    scaffold_mandate_admission,
)
```

Add tests:

```python
def test_scaffold_mandate_admission_creates_compressed_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "breakout_quality"

    artifacts = scaffold_mandate_admission(lineage_root, raw_idea="突破质量分数")

    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    assert "01_mandate/author/draft/mandate_admission.yaml" in artifacts
    assert "01_mandate/author/draft/mandate_freeze_draft.yaml" in artifacts
    payload = _read_yaml(draft_dir / "mandate_admission.yaml")
    assert payload["lineage_id"] == "breakout_quality"
    assert payload["raw_idea"] == "突破质量分数"
    assert payload["admission_decision"]["verdict"] == "NEEDS_REFRAME"


def test_admission_ready_for_freeze_requires_accept_verdict_and_route() -> None:
    payload = {
        "lineage_id": "breakout_quality",
        "raw_idea": "breakout quality",
        "observation": "Clean breakouts may continue.",
        "primary_hypothesis": "Volume-confirmed breakouts have relative strength.",
        "counter_hypothesis": "The effect is shared beta.",
        "research_questions": ["Does quality rank forecast forward returns?"],
        "scope": {
            "market": "crypto perpetual futures",
            "instrument_type": "perpetual",
            "universe": "top 30 Binance USD-M",
            "data_source": "/data/binance",
            "bar_size": "5m",
            "holding_horizons": ["30m", "2h"],
            "target_task": "cross-sectional ranking",
            "excluded_scope": ["spot"],
            "budget_days": 5,
            "max_iterations": 3,
        },
        "qualification": {
            "summary": "Researchable.",
            "dimensions": {
                name: {"score": 3, "evidence": ["present"], "uncertainty": [], "kill_reason": []}
                for name in [
                    "observability",
                    "mechanism_plausibility",
                    "tradeability",
                    "data_feasibility",
                    "scoping_clarity",
                    "distinctiveness",
                ]
            },
        },
        "route_assessment": {
            "candidate_routes": ["cross_sectional_factor", "time_series_signal"],
            "recommended_route": "cross_sectional_factor",
            "why_recommended": ["Ranking is the thesis."],
            "why_not_other_routes": {"time_series_signal": ["Single-asset direction is secondary."]},
            "route_risks": ["Short leg fragility."],
            "route_decision_pending": False,
        },
        "admission_decision": {
            "verdict": "ACCEPT_FOR_MANDATE",
            "why": ["Scope is concrete."],
            "kill_criteria": ["No monotonic buckets after costs."],
            "required_reframe_actions": [],
        },
    }

    assert admission_ready_for_freeze(payload) is None

    payload["route_assessment"]["recommended_route"] = ""
    assert admission_ready_for_freeze(payload) == "route_assessment.recommended_route is required"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_scaffold_mandate_admission_creates_compressed_draft tests/session/test_research_session_runtime.py::test_admission_ready_for_freeze_requires_accept_verdict_and_route -q
```

Expected: fail because `runtime.tools.mandate_admission_runtime` does not exist.

- [ ] **Step 3: Create helper module**

Create `runtime/tools/mandate_admission_runtime.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.idea_runtime import _blank_mandate_freeze_draft


QUALIFICATION_DIMENSIONS = (
    "observability",
    "mechanism_plausibility",
    "tradeability",
    "data_feasibility",
    "scoping_clarity",
    "distinctiveness",
)


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def blank_mandate_admission(lineage_id: str, raw_idea: str = "") -> dict[str, Any]:
    return {
        "lineage_id": lineage_id,
        "raw_idea": raw_idea,
        "observation": "",
        "primary_hypothesis": "",
        "counter_hypothesis": "",
        "research_questions": [],
        "scope": {
            "market": "",
            "instrument_type": "",
            "universe": "",
            "data_source": "",
            "bar_size": "",
            "holding_horizons": [],
            "target_task": "",
            "excluded_scope": [],
            "budget_days": 0,
            "max_iterations": 0,
        },
        "qualification": {
            "summary": "",
            "dimensions": {
                name: {"score": 0, "evidence": [], "uncertainty": [], "kill_reason": []}
                for name in QUALIFICATION_DIMENSIONS
            },
        },
        "route_assessment": {
            "candidate_routes": [],
            "recommended_route": "",
            "why_recommended": [],
            "why_not_other_routes": {},
            "route_risks": [],
            "route_decision_pending": True,
        },
        "admission_decision": {
            "verdict": "NEEDS_REFRAME",
            "why": [],
            "kill_criteria": [],
            "required_reframe_actions": [],
        },
    }


def scaffold_mandate_admission(lineage_root: Path, *, raw_idea: str = "") -> list[str]:
    lineage_root = lineage_root.resolve()
    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    admission_path = draft_dir / "mandate_admission.yaml"
    freeze_path = draft_dir / "mandate_freeze_draft.yaml"
    written: list[str] = []

    if not admission_path.exists():
        _dump_yaml(admission_path, blank_mandate_admission(lineage_root.name, raw_idea=raw_idea))
        written.append(str(admission_path.relative_to(lineage_root)))
    if not freeze_path.exists():
        _dump_yaml(freeze_path, _blank_mandate_freeze_draft())
        written.append(str(freeze_path.relative_to(lineage_root)))

    validation = validate_stage_artifacts(draft_dir, load_artifact_contract("mandate_admission"))
    if not validation.valid:
        joined_errors = "; ".join(validation.errors)
        raise ValueError(f"mandate_admission scaffold does not match artifact contract: {joined_errors}")
    return written


def load_mandate_admission(lineage_root: Path) -> dict[str, Any]:
    path = lineage_root / "01_mandate" / "author" / "draft" / "mandate_admission.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def admission_ready_for_freeze(payload: dict[str, Any]) -> str | None:
    required_strings = (
        "raw_idea",
        "observation",
        "primary_hypothesis",
        "counter_hypothesis",
        "scope.market",
        "scope.universe",
        "scope.data_source",
        "scope.bar_size",
        "scope.target_task",
        "route_assessment.recommended_route",
    )
    for path in required_strings:
        value = _get_path(payload, path)
        if not isinstance(value, str) or not value.strip():
            return f"{path} is required"

    candidate_routes = _get_path(payload, "route_assessment.candidate_routes")
    recommended_route = _get_path(payload, "route_assessment.recommended_route")
    if not isinstance(candidate_routes, list) or recommended_route not in candidate_routes:
        return "route_assessment.recommended_route must be in candidate_routes"

    kill_criteria = _get_path(payload, "admission_decision.kill_criteria")
    if not isinstance(kill_criteria, list) or not kill_criteria:
        return "admission_decision.kill_criteria is required"

    verdict = _get_path(payload, "admission_decision.verdict")
    if verdict != "ACCEPT_FOR_MANDATE":
        return "admission_decision.verdict must be ACCEPT_FOR_MANDATE"

    dimensions = _get_path(payload, "qualification.dimensions")
    if not isinstance(dimensions, dict):
        return "qualification.dimensions is required"
    for name in QUALIFICATION_DIMENSIONS:
        score = _get_path(payload, f"qualification.dimensions.{name}.score")
        if not isinstance(score, int) or score <= 0:
            return f"qualification.dimensions.{name}.score must be positive"
    return None


def _get_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
```

- [ ] **Step 4: Run helper tests**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_scaffold_mandate_admission_creates_compressed_draft tests/session/test_research_session_runtime.py::test_admission_ready_for_freeze_requires_accept_verdict_and_route -q
```

Expected: pass.

- [ ] **Step 5: Commit checkpoint**

If commit authorization is present:

```bash
git add runtime/tools/mandate_admission_runtime.py tests/session/test_research_session_runtime.py
git commit -m "feat: add mandate admission runtime helpers"
```

## Task 3: Replace First-Stage Detection

**Files:**
- Modify: `runtime/tools/research_session.py`
- Modify: `tests/session/test_research_session_runtime.py`

- [ ] **Step 1: Add failing stage detection tests**

In `tests/session/test_research_session_runtime.py`, replace the missing-lineage expectation with:

```python
def test_detect_session_stage_returns_mandate_admission_when_lineage_missing(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"

    assert detect_session_stage(lineage_root) == "mandate_admission"
```

Add:

```python
def test_detect_session_stage_returns_mandate_freeze_confirmation_when_admission_accepted(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "breakout_quality"
    scaffold_mandate_admission(lineage_root, raw_idea="breakout quality")
    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    payload = _read_yaml(draft_dir / "mandate_admission.yaml")
    payload.update(
        {
            "observation": "Clean breakouts may continue.",
            "primary_hypothesis": "Volume-confirmed breakouts have relative strength.",
            "counter_hypothesis": "The effect is shared beta.",
            "research_questions": ["Does quality rank forecast forward returns?"],
        }
    )
    payload["scope"].update(
        {
            "market": "crypto perpetual futures",
            "instrument_type": "perpetual",
            "universe": "top 30 Binance USD-M",
            "data_source": "/data/binance",
            "bar_size": "5m",
            "holding_horizons": ["30m"],
            "target_task": "cross-sectional ranking",
            "excluded_scope": ["spot"],
            "budget_days": 5,
            "max_iterations": 3,
        }
    )
    payload["qualification"]["summary"] = "Researchable."
    for dimension in payload["qualification"]["dimensions"].values():
        dimension["score"] = 3
        dimension["evidence"] = ["present"]
    payload["route_assessment"] = {
        "candidate_routes": ["cross_sectional_factor", "time_series_signal"],
        "recommended_route": "cross_sectional_factor",
        "why_recommended": ["Ranking is the thesis."],
        "why_not_other_routes": {"time_series_signal": ["Single-asset direction is secondary."]},
        "route_risks": ["Short leg fragility."],
        "route_decision_pending": False,
    }
    payload["admission_decision"] = {
        "verdict": "ACCEPT_FOR_MANDATE",
        "why": ["Scope is concrete."],
        "kill_criteria": ["No monotonic buckets after costs."],
        "required_reframe_actions": [],
    }
    _write_yaml(draft_dir / "mandate_admission.yaml", payload)
    _write_yaml(draft_dir / "mandate_freeze_draft.yaml", _freeze_draft(confirmed=False))

    assert detect_session_stage(lineage_root) == "mandate_freeze_confirmation_pending"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_detect_session_stage_returns_mandate_admission_when_lineage_missing tests/session/test_research_session_runtime.py::test_detect_session_stage_returns_mandate_freeze_confirmation_when_admission_accepted -q
```

Expected: fail because current stage names still use `idea_intake`.

- [ ] **Step 3: Update stage type and active skill maps**

In `runtime/tools/research_session.py`, add these stages to the session stage literal and active skill maps:

```python
"mandate_admission",
"mandate_freeze_confirmation_pending",
```

Map both stages to `qros-research-session` in ordinary orchestration. Do not map them to `qros-idea-intake-author`.

- [ ] **Step 4: Update `detect_session_stage()` first-stage logic**

Replace the old intake branch with logic equivalent to:

```python
mandate_draft_dir = mandate_dir / "author" / "draft"
mandate_admission_path = mandate_draft_dir / "mandate_admission.yaml"
mandate_freeze_path = mandate_draft_dir / "mandate_freeze_draft.yaml"
mandate_approval_path = mandate_draft_dir / "mandate_transition_approval.yaml"

if not mandate_admission_path.exists():
    return "mandate_admission"

admission_payload = _read_yaml(mandate_admission_path)
admission_error = admission_ready_for_freeze(admission_payload)
if admission_error is not None:
    return "mandate_admission"

if not mandate_freeze_path.exists() or next_mandate_freeze_group(lineage_root) is not None:
    return "mandate_freeze_confirmation_pending"

approval_decision = read_mandate_transition_decision(lineage_root)
if approval_decision == "CONFIRM_MANDATE":
    return "mandate_author"
if approval_decision == "REFRAME":
    return "mandate_admission"
return "mandate_freeze_confirmation_pending"
```

Also update `_approval_path()` so `read_mandate_transition_decision()` reads:

```python
return lineage_root / "01_mandate" / "author" / "draft" / MANDATE_TRANSITION_APPROVAL_FILE
```

- [ ] **Step 5: Run focused stage tests**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_detect_session_stage_returns_mandate_admission_when_lineage_missing tests/session/test_research_session_runtime.py::test_detect_session_stage_returns_mandate_freeze_confirmation_when_admission_accepted -q
```

Expected: pass.

- [ ] **Step 6: Commit checkpoint**

If commit authorization is present:

```bash
git add runtime/tools/research_session.py tests/session/test_research_session_runtime.py
git commit -m "feat: make mandate admission the first session stage"
```

## Task 4: Update Session Creation and Confirmation

**Files:**
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/scripts/run_research_session.py`
- Modify: `tests/session/test_run_research_session_script.py`

- [ ] **Step 1: Add failing CLI behavior tests**

In `tests/session/test_run_research_session_script.py`, add:

```python
def test_run_research_session_scaffolds_mandate_admission_for_raw_idea(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = run(
        [
            sys.executable,
            str(REPO_ROOT / "runtime" / "scripts" / "run_research_session.py"),
            "--outputs-root",
            str(outputs_root),
            "--raw-idea",
            "对全市场数字货币计算突破质量分数",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Current stage: mandate_admission" in result.stdout
    lineage_dirs = list(outputs_root.iterdir())
    assert len(lineage_dirs) == 1
    assert (lineage_dirs[0] / "01_mandate" / "author" / "draft" / "mandate_admission.yaml").exists()
    assert not (lineage_dirs[0] / "00_idea_intake").exists()
```

Add:

```python
def test_run_research_session_no_longer_accepts_confirm_intake(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = run(
        [
            sys.executable,
            str(REPO_ROOT / "runtime" / "scripts" / "run_research_session.py"),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "breakout_quality",
            "--confirm-intake",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "--confirm-intake has been retired" in result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/session/test_run_research_session_script.py::test_run_research_session_scaffolds_mandate_admission_for_raw_idea tests/session/test_run_research_session_script.py::test_run_research_session_no_longer_accepts_confirm_intake -q
```

Expected: fail because CLI still creates `00_idea_intake` and accepts `--confirm-intake`.

- [ ] **Step 3: Update raw idea slug fallback**

In `runtime/tools/research_session.py`, change `slugify_idea()` so Chinese-only ideas do not fail. Use a deterministic hash suffix:

```python
def slugify_idea(raw_idea: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", raw_idea.strip().lower())
    normalized = normalized.strip("_")
    if normalized:
        return normalized
    digest = hashlib.sha256(raw_idea.strip().encode("utf-8")).hexdigest()[:12]
    return f"idea_{digest}"
```

Add `import hashlib` near the existing imports.

- [ ] **Step 4: Scaffold mandate admission during `run_research_session()`**

In `run_research_session()`, replace `ensure_intake_scaffold()` use for new first-stage creation with:

```python
if current_stage == "mandate_admission":
    raw_idea_text = raw_idea or ""
    artifacts_written.extend(scaffold_mandate_admission(lineage_root, raw_idea=raw_idea_text))
    current_stage = detect_session_stage(lineage_root)
```

Keep existing behavior that re-detects after writes.

- [ ] **Step 5: Retire `--confirm-intake`**

In `runtime/scripts/run_research_session.py`, keep parser compatibility only long enough to emit a clear error. After parsing:

```python
if args.confirm_intake:
    raise SystemExit("--confirm-intake has been retired; mandate admission now uses --confirm-mandate after freeze review")
```

Remove `idea_intake_decision="CONFIRM_IDEA_INTAKE" if args.confirm_intake else None` from the runtime call and pass `idea_intake_decision=None`.

- [ ] **Step 6: Run focused CLI tests**

Run:

```bash
python -m pytest tests/session/test_run_research_session_script.py::test_run_research_session_scaffolds_mandate_admission_for_raw_idea tests/session/test_run_research_session_script.py::test_run_research_session_no_longer_accepts_confirm_intake -q
```

Expected: pass.

- [ ] **Step 7: Commit checkpoint**

If commit authorization is present:

```bash
git add runtime/tools/research_session.py runtime/scripts/run_research_session.py tests/session/test_run_research_session_script.py
git commit -m "feat: scaffold mandate admission from research session"
```

## Task 5: Update Mandate Builder Inputs

**Files:**
- Modify: `runtime/tools/idea_runtime.py`
- Modify: `runtime/tools/stage_program_scaffold.py`
- Modify: `tests/session/test_idea_runtime_scripts.py`

- [ ] **Step 1: Add failing mandate build test for new draft paths**

In `tests/session/test_idea_runtime_scripts.py`, add:

```python
def test_build_mandate_from_mandate_admission_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "breakout_quality"
    draft_dir = lineage_root / "01_mandate" / "author" / "draft"
    draft_dir.mkdir(parents=True)
    _write_yaml(
        draft_dir / "mandate_admission.yaml",
        {
            "lineage_id": "breakout_quality",
            "raw_idea": "breakout quality",
            "observation": "Clean breakouts may continue.",
            "primary_hypothesis": "Volume-confirmed breakouts have relative strength.",
            "counter_hypothesis": "The effect is shared beta.",
            "research_questions": ["Does quality rank forecast forward returns?"],
            "scope": {
                "market": "crypto perpetual futures",
                "instrument_type": "perpetual",
                "universe": "top 30 Binance USD-M",
                "data_source": "/data/binance",
                "bar_size": "5m",
                "holding_horizons": ["30m"],
                "target_task": "cross-sectional ranking",
                "excluded_scope": ["spot"],
                "budget_days": 5,
                "max_iterations": 3,
            },
            "qualification": {
                "summary": "Researchable.",
                "dimensions": {
                    name: {"score": 3, "evidence": ["present"], "uncertainty": [], "kill_reason": []}
                    for name in [
                        "observability",
                        "mechanism_plausibility",
                        "tradeability",
                        "data_feasibility",
                        "scoping_clarity",
                        "distinctiveness",
                    ]
                },
            },
            "route_assessment": _route_assessment(),
            "admission_decision": {
                "verdict": "ACCEPT_FOR_MANDATE",
                "why": ["Scope is concrete."],
                "kill_criteria": ["No monotonic buckets after costs."],
                "required_reframe_actions": [],
            },
        },
    )
    _write_yaml(draft_dir / "mandate_freeze_draft.yaml", _mandate_freeze_draft(confirmed=True))
    _write_yaml(
        draft_dir / "mandate_transition_approval.yaml",
        {
            "lineage_id": "breakout_quality",
            "decision": "CONFIRM_MANDATE",
            "approved_by": "tester",
            "approved_at": "2026-05-21T10:00:00Z",
            "source_stage": "mandate_freeze_confirmation_pending",
        },
    )

    ensure_stage_program(lineage_root, "mandate")
    result = run(
        [
            sys.executable,
            str(lineage_root / "program" / "mandate" / "run_stage.py"),
            "--lineage-root",
            str(lineage_root),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    assert (formal_dir / "mandate.md").exists()
    assert (formal_dir / "research_route.yaml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/session/test_idea_runtime_scripts.py::test_build_mandate_from_mandate_admission_draft -q
```

Expected: fail because `build_mandate_from_intake()` still reads `00_idea_intake`.

- [ ] **Step 3: Rename builder function internally**

In `runtime/tools/idea_runtime.py`, add a new function:

```python
def build_mandate_from_admission(lineage_root: Path) -> Path:
    ...
```

Move the current mandate build body into this function and change input paths:

```python
draft_dir = lineage_root / "01_mandate" / "author" / "draft"
admission = yaml.safe_load((draft_dir / "mandate_admission.yaml").read_text(encoding="utf-8"))
freeze_groups = require_confirmed_freeze_groups(draft_dir, draft_filename=MANDATE_FREEZE_DRAFT_FILE)
```

If `require_confirmed_freeze_groups()` does not accept `draft_filename`, add a small wrapper in `idea_runtime.py` that loads `draft_dir / MANDATE_FREEZE_DRAFT_FILE` and applies the same validation used by `freeze_contract_runtime`. Keep the old `build_mandate_from_intake()` as a thin alias during the same task only if existing tests still import it directly:

```python
def build_mandate_from_intake(lineage_root: Path) -> Path:
    return build_mandate_from_admission(lineage_root)
```

The alias is for code-level compatibility during the refactor, not a runtime path for `00_idea_intake`.

- [ ] **Step 4: Update gate data source**

Replace old gate decision reads:

```python
gate_decision = yaml.safe_load((intake_dir / "idea_gate_decision.yaml").read_text(encoding="utf-8"))
```

with:

```python
admission = yaml.safe_load((draft_dir / "mandate_admission.yaml").read_text(encoding="utf-8"))
if admission["admission_decision"]["verdict"] != "ACCEPT_FOR_MANDATE":
    raise ValueError("mandate_admission verdict must be ACCEPT_FOR_MANDATE before mandate build")
route_assessment = _require_route_assessment_from_admission(admission)
```

Implement `_require_route_assessment_from_admission()` with the same checks as the existing route assessment helper, using `admission["route_assessment"]`.

- [ ] **Step 5: Update stage program scaffold**

In `runtime/tools/stage_program_scaffold.py`, change the mandate spec:

```python
"inputs": [
    "01_mandate/author/draft/mandate_admission.yaml",
    "01_mandate/author/draft/mandate_freeze_draft.yaml",
    "01_mandate/author/draft/mandate_transition_approval.yaml",
],
"function": "build_mandate_from_admission",
```

- [ ] **Step 6: Run focused builder test**

Run:

```bash
python -m pytest tests/session/test_idea_runtime_scripts.py::test_build_mandate_from_mandate_admission_draft -q
```

Expected: pass.

- [ ] **Step 7: Commit checkpoint**

If commit authorization is present:

```bash
git add runtime/tools/idea_runtime.py runtime/tools/stage_program_scaffold.py tests/session/test_idea_runtime_scripts.py
git commit -m "feat: build mandate from admission draft"
```

## Task 6: Remove Normal-Path Idea Intake Surface

**Files:**
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `skills/core/using-qros/SKILL.md`
- Modify: `skills/idea_intake/qros-idea-intake-author/SKILL.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/idea-intake-to-mandate-flow.md`
- Modify: `docs/guides/quickstart-codex.md`
- Modify: docs and tests that assert active `idea_intake` first-stage wording

- [ ] **Step 1: Add failing doc expectation test**

In `tests/docs/test_install_docs.py` or a new doc test file, add:

```python
def test_research_session_docs_use_mandate_admission_first_stage() -> None:
    usage = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    quickstart = Path("docs/guides/quickstart-codex.md").read_text(encoding="utf-8")

    assert "mandate_admission" in usage
    assert "00_idea_intake" not in quickstart
    assert "idea_intake_confirmation_pending" not in usage
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py::test_research_session_docs_use_mandate_admission_first_stage -q
```

Expected: fail because docs still describe `idea_intake`.

- [ ] **Step 3: Update research-session skill**

In `skills/core/qros-research-session/SKILL.md`, replace normal first-stage rules with:

```markdown
- New lineages start in `mandate_admission`.
- `idea_intake` is retired from the ordinary user path.
- `mandate_admission` captures raw idea, observation, hypotheses, scope, qualification, route assessment, and admission decision in `01_mandate/author/draft/mandate_admission.yaml`.
- Only `ACCEPT_FOR_MANDATE` can move to `mandate_freeze_confirmation_pending`.
- The only pre-authoring user approval is final mandate freeze confirmation.
```

Remove instructions that require `CONFIRM_IDEA_INTAKE` or direct users to `qros-idea-intake-author`.

- [ ] **Step 4: Mark idea intake skill legacy**

At the top of `skills/idea_intake/qros-idea-intake-author/SKILL.md`, add:

```markdown
> Legacy note: `idea_intake` is retired from the normal QROS first-stage path. Do not recommend this skill from `qros-research-session`. Use only for manual inspection of old lineages created before the mandate-admission merge.
```

- [ ] **Step 5: Update active docs**

Rewrite the first-stage sections in:

```text
docs/guides/qros-research-session-usage.md
docs/guides/idea-intake-to-mandate-flow.md
docs/guides/quickstart-codex.md
```

Use these canonical statements:

```markdown
New QROS lineages start at `mandate_admission`.
QROS no longer creates `00_idea_intake/` for new lineages.
The old intake responsibilities are represented by `01_mandate/author/draft/mandate_admission.yaml`.
The first user approval freezes mandate and writes `mandate_transition_approval.yaml`.
```

- [ ] **Step 6: Run doc tests**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py tests/skills/test_idea_intake_shape_contract_guidance.py -q
```

Expected: install docs pass; idea-intake guidance tests either pass with legacy wording or are deleted if they only enforce retired normal-path behavior.

- [ ] **Step 7: Commit checkpoint**

If commit authorization is present:

```bash
git add skills/core/qros-research-session/SKILL.md skills/core/using-qros/SKILL.md skills/idea_intake/qros-idea-intake-author/SKILL.md docs/guides/qros-research-session-usage.md docs/guides/idea-intake-to-mandate-flow.md docs/guides/quickstart-codex.md tests/docs/test_install_docs.py tests/skills/test_idea_intake_shape_contract_guidance.py
git commit -m "docs: document mandate admission first-stage flow"
```

## Task 7: Update CLI and Runtime Test Suite Expectations

**Files:**
- Modify: `tests/session/test_research_session_runtime.py`
- Modify: `tests/session/test_run_research_session_script.py`
- Modify: `tests/runtime/test_validate_stage_artifacts_script.py`
- Modify or delete: retired normal-path idea-intake tests

- [ ] **Step 1: Replace first-stage expected names**

Across session tests, replace expected normal-path values:

```text
idea_intake -> mandate_admission
idea_intake_confirmation_pending -> mandate_admission or mandate_freeze_confirmation_pending, depending on admission completeness
mandate_confirmation_pending -> mandate_freeze_confirmation_pending
```

Use `mandate_admission` when admission evidence is missing or verdict is not `ACCEPT_FOR_MANDATE`.
Use `mandate_freeze_confirmation_pending` when admission is accepted but mandate freeze is not confirmed.

- [ ] **Step 2: Replace approval paths in tests**

Replace old approval path:

```text
00_idea_intake/mandate_transition_approval.yaml
```

with:

```text
01_mandate/author/draft/mandate_transition_approval.yaml
```

- [ ] **Step 3: Replace gate fixture writers**

Where tests write `idea_gate_decision.yaml`, write `mandate_admission.yaml` using the shape from Task 2. A minimal accepted fixture must include:

```python
{
    "lineage_id": "btc_leads_alts",
    "raw_idea": "BTC leads ALTs",
    "observation": "BTC shocks precede ALT reactions.",
    "primary_hypothesis": "BTC leads price discovery.",
    "counter_hypothesis": "Moves are shared beta.",
    "research_questions": ["Do ALTs follow BTC after shocks?"],
    "scope": {
        "market": "binance perp",
        "instrument_type": "perpetual",
        "universe": "high liquidity alts",
        "data_source": "binance um futures klines",
        "bar_size": "5m",
        "holding_horizons": ["15m", "30m"],
        "target_task": "event-driven relative return study",
        "excluded_scope": ["low liquidity tails"],
        "budget_days": 5,
        "max_iterations": 3,
    },
    "qualification": {
        "summary": "Researchable.",
        "dimensions": {
            name: {"score": 3, "evidence": ["present"], "uncertainty": [], "kill_reason": []}
            for name in [
                "observability",
                "mechanism_plausibility",
                "tradeability",
                "data_feasibility",
                "scoping_clarity",
                "distinctiveness",
            ]
        },
    },
    "route_assessment": _route_assessment(),
    "admission_decision": {
        "verdict": "ACCEPT_FOR_MANDATE",
        "why": ["Scope is concrete."],
        "kill_criteria": ["No edge after costs."],
        "required_reframe_actions": [],
    },
}
```

- [ ] **Step 4: Update validation script tests**

In `tests/runtime/test_validate_stage_artifacts_script.py`, add an acceptance test for:

```bash
python runtime/scripts/validate_stage_artifacts.py --stage mandate_admission --stage-dir <draft_dir>
```

Expected stdout should include:

```text
mandate_admission artifact shape valid
```

Update the script if it derives stage display text from the stage id.

- [ ] **Step 5: Run session/runtime suites**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py tests/session/test_run_research_session_script.py tests/runtime/test_validate_stage_artifacts_script.py -q
```

Expected: pass.

- [ ] **Step 6: Commit checkpoint**

If commit authorization is present:

```bash
git add tests/session/test_research_session_runtime.py tests/session/test_run_research_session_script.py tests/runtime/test_validate_stage_artifacts_script.py
git commit -m "test: update session tests for mandate admission"
```

## Task 8: Update Verification Tiers and Anti-Drift Fixtures

**Files:**
- Modify: `runtime/scripts/run_verification_tier.py`
- Modify: anti-drift snapshot fixtures under `tests/` if present
- Modify: session behavior tests referenced by smoke and full-smoke

- [ ] **Step 1: List current verification tier commands**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke --list
python runtime/scripts/run_verification_tier.py --tier full-smoke --list
```

Expected: command lists show tests that still include old first-stage naming.

- [ ] **Step 2: Update tier test membership only when needed**

If the listed tests point to deleted idea-intake-only files, replace them with mandate admission equivalents. Keep tests that still validate archived contracts only if they are not part of normal first-stage flow.

- [ ] **Step 3: Update anti-drift expectations**

Search:

```bash
rg -n "idea_intake|idea_intake_confirmation_pending|mandate_confirmation_pending|CONFIRM_IDEA_INTAKE|00_idea_intake" tests runtime docs skills
```

For normal-path fixtures, replace with:

```text
mandate_admission
mandate_freeze_confirmation_pending
CONFIRM_MANDATE
01_mandate/author/draft
```

For archived docs or legacy skill notes, keep references only when the surrounding text clearly says legacy or retired.

- [ ] **Step 4: Run smoke tier**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: pass.

- [ ] **Step 5: Commit checkpoint**

If commit authorization is present:

```bash
git add runtime/scripts/run_verification_tier.py tests runtime docs skills
git commit -m "test: refresh verification tiers for mandate admission"
```

## Task 9: Full Regression and Final Cleanup

**Files:**
- Review all files changed in Tasks 1-8

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py tests/session/test_research_session_runtime.py tests/session/test_run_research_session_script.py tests/session/test_idea_runtime_scripts.py tests/runtime/test_validate_stage_artifacts_script.py -q
```

Expected: pass.

- [ ] **Step 2: Run docs/bootstrap minimum**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected: pass.

- [ ] **Step 3: Run full smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: pass.

- [ ] **Step 4: Inspect remaining first-stage references**

Run:

```bash
rg -n "idea_intake|idea_intake_confirmation_pending|CONFIRM_IDEA_INTAKE|00_idea_intake" runtime skills docs tests contracts
```

Expected: remaining matches are limited to archived docs, legacy skill warnings, or explicit tests for retired behavior. No normal-path session output, recommended skill, quickstart, or active user guide should instruct users to enter `idea_intake`.

- [ ] **Step 5: Inspect git diff**

Run:

```bash
git diff --stat
git diff -- runtime/tools/research_session.py runtime/tools/idea_runtime.py runtime/tools/mandate_admission_runtime.py
```

Expected: diff shows one coherent first-stage workflow change and no unrelated refactors.

- [ ] **Step 6: Final commit checkpoint**

If commit authorization is present:

```bash
git add contracts runtime skills docs tests
git commit -m "feat: merge idea intake into mandate admission"
```

## Self-Review Notes

- Spec coverage: The plan covers the breaking stage model, compressed admission artifact, retained `draft/formal` boundary, no compatibility migration, docs updates, and required smoke/full-smoke verification.
- Placeholder scan: The plan contains no task that asks the implementer to invent missing behavior without a concrete file path, command, or code shape.
- Type consistency: The plan consistently uses `mandate_admission`, `mandate_freeze_confirmation_pending`, `mandate_admission.yaml`, `mandate_freeze_draft.yaml`, and `mandate_transition_approval.yaml`.
