# CSF Backtest Real Return Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `csf_backtest_ready` reject formal backtest metrics derived from proxy returns such as `mom_ret` and require explicit tradable return provenance.

**Architecture:** Add a new `return_accounting_provenance.yaml` formal artifact, generate it from the CSF backtest runtime builder, and enforce it in the CSF backtest semantic validator. Keep proxy PnL as diagnostic-only by blocking forbidden formal source types, forbidden return fields, signal/factor-panel-only input paths, and obvious `weight * mom_ret` stage-local code patterns.

**Tech Stack:** Python 3, PyYAML, pyarrow/parquet, pytest, existing QROS artifact contract runtime and review preflight.

---

## File Structure

- Modify `contracts/artifacts/csf_backtest_ready_artifacts.yaml`
  - Declare `return_accounting_provenance.yaml` as a required formal YAML artifact.
- Modify `runtime/tools/csf_backtest_runtime.py`
  - Add `return_accounting_provenance.yaml` to `CSF_BACKTEST_READY_STAGE_OUTPUTS`.
  - Write a valid provenance artifact during runtime-built CSF backtest scaffolding.
  - Mention the artifact in `artifact_catalog.md` and `field_dictionary.md`.
- Modify `runtime/tools/csf_backtest_ready_contract_runtime.py`
  - Validate return provenance semantics.
  - Reject proxy return source types, forbidden return fields, signal/factor-only paths, and obvious proxy PnL program code.
- Modify `tests/contracts/test_csf_backtest_ready_artifact_contract.py`
  - Lock the new contract artifact and fields.
- Modify `tests/runtime/test_csf_backtest_runtime.py`
  - Assert the runtime builder writes the new artifact and lists it in `run_manifest.json`.
- Modify `tests/session/test_csf_backtest_ready_artifact_shape.py`
  - Assert artifact validation accepts the new required artifact and its field shape is stable.
- Modify `tests/runtime/test_csf_backtest_ready_semantic_validation.py`
  - Add negative tests for missing provenance, forbidden source types, `mom_ret`, signal-only paths, and code scan.
  - Add a positive assertion that runtime-built outputs remain valid.
- Modify `tests/review/test_review_preflight_csf_backtest_ready_contract.py`
  - Ensure review preflight blocks missing or illegal return provenance.
- Modify `skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md`
  - Instruct author flow to require tradable return provenance and not use `mom_ret` for formal PnL.
- Modify `skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md`
  - Instruct review flow to treat proxy PnL as blocking.
- Modify `tests/skills/test_csf_backtest_ready_contract_first_guidance.py`
  - Lock the skill guidance text for the new artifact and proxy-PnL prohibition.
- Modify `docs/guides/qros-research-session-usage.md`, `docs/guides/qros-review-shared-protocol.md`, `docs/guides/stage-freeze-group-field-guide.md`, and `docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md`
  - Document that CSF backtest formal metrics require tradable return provenance.
- Modify `tests/docs/test_csf_backtest_ready_contract_first_docs.py`
  - Lock documentation mentions.

---

### Task 1: Lock The New Artifact Contract

**Files:**
- Modify: `tests/contracts/test_csf_backtest_ready_artifact_contract.py`
- Modify: `contracts/artifacts/csf_backtest_ready_artifacts.yaml`

- [ ] **Step 1: Write failing contract tests**

Add these assertions to `tests/contracts/test_csf_backtest_ready_artifact_contract.py`.

```python
def test_csf_backtest_ready_contract_declares_all_formal_outputs() -> None:
    contract = _load_contract()

    assert set(contract["artifacts"]) == {
        "portfolio_contract.yaml",
        "portfolio_weight_panel.parquet",
        "rebalance_ledger.csv",
        "turnover_capacity_report.parquet",
        "cost_assumption_report.md",
        "portfolio_summary.parquet",
        "name_level_metrics.parquet",
        "drawdown_report.json",
        "target_strategy_compare.parquet",
        "csf_backtest_gate_table.csv",
        "return_accounting_provenance.yaml",
        "csf_backtest_contract.md",
        "csf_backtest_gate_decision.md",
        "run_manifest.json",
        "artifact_catalog.md",
        "field_dictionary.md",
    }
```

Add this new test near the other contract field tests.

```python
def test_csf_backtest_ready_contract_locks_return_accounting_provenance_fields() -> None:
    contract = _load_contract()
    artifact = _artifact(contract, "return_accounting_provenance.yaml")

    assert artifact["type"] == "yaml"
    assert artifact["unknown_top_level_fields"] == "forbid"
    assert _field_paths(artifact) == {
        "stage",
        "lineage_id",
        "return_source.source_type",
        "return_source.input_paths",
        "return_source.price_field",
        "return_source.return_field",
        "return_source.source_stage",
        "return_source.is_signal_derived",
        "accounting.rebalance_timing",
        "accounting.holding_period",
        "accounting.fee_model",
        "accounting.slippage_model",
        "accounting.funding_model",
        "accounting.missing_price_policy",
        "accounting.gross_return_formula",
        "accounting.net_return_formula",
        "formal_outputs.portfolio_summary",
        "formal_outputs.gate_table",
    }

    source_type = next(field for field in artifact["fields"] if field["path"] == "return_source.source_type")
    assert source_type["type"] == "enum"
    assert source_type["values"] == [
        "market_price",
        "execution_ledger",
        "mark_price",
        "ohlcv",
        "funding_adjusted_price",
        "tradable_return_panel",
    ]

    source_stage = next(field for field in artifact["fields"] if field["path"] == "return_source.source_stage")
    assert source_stage["type"] == "enum"
    assert source_stage["values"] == ["csf_data_ready", "execution"]
```

- [ ] **Step 2: Run contract test and verify it fails**

Run:

```bash
python -m pytest tests/contracts/test_csf_backtest_ready_artifact_contract.py -q
```

Expected: FAIL because `return_accounting_provenance.yaml` is not declared yet.

- [ ] **Step 3: Add `return_accounting_provenance.yaml` to the artifact contract**

Insert this artifact block in `contracts/artifacts/csf_backtest_ready_artifacts.yaml` between `csf_backtest_gate_table.csv` and `csf_backtest_contract.md`.

```yaml
  return_accounting_provenance.yaml:
    type: yaml
    unknown_top_level_fields: forbid
    fields:
      - path: stage
        description: 标识该 artifact 所属的 QROS 阶段，用于阻止跨阶段产物混用。
        type: enum
        values:
          - csf_backtest_ready
      - path: lineage_id
        description: 标识当前研究 lineage，用于把收益来源与唯一研究线绑定。
        type: string
      - path: return_source.source_type
        description: 声明 formal PnL 使用的真实收益来源类型，用于禁止 signal/factor proxy return 进入 backtest gate。
        type: enum
        values:
          - market_price
          - execution_ledger
          - mark_price
          - ohlcv
          - funding_adjusted_price
          - tradable_return_panel
      - path: return_source.input_paths
        description: 列出 formal return accounting 使用的输入路径，用于审计收益来源是否独立于 signal/factor panel。
        type: list[string]
      - path: return_source.price_field
        description: 记录价格字段；若使用已计算 tradable return panel，可写入空字符串。
        type: string
      - path: return_source.return_field
        description: 记录正式收益字段，用于阻止 mom_ret 等 proxy 字段进入 formal PnL。
        type: string
      - path: return_source.source_stage
        description: 记录收益来源所属阶段，用于确认 formal PnL 来自 data_ready 或 execution accounting。
        type: enum
        values:
          - csf_data_ready
          - execution
      - path: return_source.is_signal_derived
        description: 声明正式收益字段是否由 signal/factor panel 派生；formal backtest 必须为 false。
        type: boolean
      - path: accounting.rebalance_timing
        description: 记录再平衡成交时点，用于审计信号与收益窗口是否错配。
        type: string
      - path: accounting.holding_period
        description: 记录持仓收益窗口，用于解释 formal return field 的时间跨度。
        type: string
      - path: accounting.fee_model
        description: 记录手续费模型，用于解释 net return 的扣减口径。
        type: string
      - path: accounting.slippage_model
        description: 记录滑点模型，用于解释 net return 的执行成本口径。
        type: string
      - path: accounting.funding_model
        description: 记录资金费率模型，用于解释永续合约 PnL 的资金成本口径。
        type: string
      - path: accounting.missing_price_policy
        description: 记录缺失价格处理策略，用于审计不可交易样本如何进入或退出组合。
        type: string
      - path: accounting.gross_return_formula
        description: 记录 gross return 公式，用于审计组合收益是否来自 tradable return 而非 proxy return。
        type: string
      - path: accounting.net_return_formula
        description: 记录 net return 公式，用于审计成本、滑点和资金费率如何扣减。
        type: string
      - path: formal_outputs.portfolio_summary
        description: 记录该 provenance 支撑的 portfolio summary 产物名。
        type: string
      - path: formal_outputs.gate_table
        description: 记录该 provenance 支撑的 gate table 产物名。
        type: string
```

- [ ] **Step 4: Run contract test and verify it passes**

Run:

```bash
python -m pytest tests/contracts/test_csf_backtest_ready_artifact_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit only if explicit commit permission exists**

If the user has explicitly approved commits on the current branch, run:

```bash
git add contracts/artifacts/csf_backtest_ready_artifacts.yaml tests/contracts/test_csf_backtest_ready_artifact_contract.py
git commit -m "feat: require csf backtest return provenance contract"
```

If commit permission has not been granted, do not commit.

---

### Task 2: Generate Valid Provenance From The CSF Backtest Runtime Builder

**Files:**
- Modify: `tests/runtime/test_csf_backtest_runtime.py`
- Modify: `tests/session/test_csf_backtest_ready_artifact_shape.py`
- Modify: `runtime/tools/csf_backtest_runtime.py`

- [ ] **Step 1: Write failing builder tests**

In `tests/runtime/test_csf_backtest_runtime.py`, extend `test_build_csf_backtest_ready_writes_required_outputs`.

```python
    assert (formal_dir / "return_accounting_provenance.yaml").exists()

    provenance = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))
    assert provenance["stage"] == "csf_backtest_ready"
    assert provenance["lineage_id"] == lineage_root.name
    assert provenance["return_source"]["source_type"] == "tradable_return_panel"
    assert provenance["return_source"]["return_field"] == "return_1d"
    assert provenance["return_source"]["source_stage"] == "csf_data_ready"
    assert provenance["return_source"]["is_signal_derived"] is False
    assert provenance["formal_outputs"] == {
        "portfolio_summary": "portfolio_summary.parquet",
        "gate_table": "csf_backtest_gate_table.csv",
    }

    assert "return_accounting_provenance.yaml" in run_manifest["stage_outputs"]
```

In `tests/session/test_csf_backtest_ready_artifact_shape.py`, add this test.

```python
def test_csf_backtest_ready_return_accounting_provenance_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_backtest_ready(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    payload = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))

    assert set(payload) == {"stage", "lineage_id", "return_source", "accounting", "formal_outputs"}
    assert set(payload["return_source"]) == {
        "source_type",
        "input_paths",
        "price_field",
        "return_field",
        "source_stage",
        "is_signal_derived",
    }
    assert set(payload["accounting"]) == {
        "rebalance_timing",
        "holding_period",
        "fee_model",
        "slippage_model",
        "funding_model",
        "missing_price_policy",
        "gross_return_formula",
        "net_return_formula",
    }
    assert payload["return_source"]["is_signal_derived"] is False
```

- [ ] **Step 2: Run builder and session shape tests and verify they fail**

Run:

```bash
python -m pytest tests/runtime/test_csf_backtest_runtime.py::test_build_csf_backtest_ready_writes_required_outputs tests/session/test_csf_backtest_ready_artifact_shape.py -q
```

Expected: FAIL because the runtime builder does not write `return_accounting_provenance.yaml`.

- [ ] **Step 3: Update runtime output list**

In `runtime/tools/csf_backtest_runtime.py`, add `"return_accounting_provenance.yaml"` to `CSF_BACKTEST_READY_STAGE_OUTPUTS` immediately after `"csf_backtest_gate_table.csv"`.

```python
CSF_BACKTEST_READY_STAGE_OUTPUTS = [
    "portfolio_contract.yaml",
    "portfolio_weight_panel.parquet",
    "rebalance_ledger.csv",
    "turnover_capacity_report.parquet",
    "cost_assumption_report.md",
    "portfolio_summary.parquet",
    "name_level_metrics.parquet",
    "drawdown_report.json",
    "target_strategy_compare.parquet",
    "csf_backtest_gate_table.csv",
    "return_accounting_provenance.yaml",
    "csf_backtest_contract.md",
    "csf_backtest_gate_decision.md",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
]
```

- [ ] **Step 4: Write provenance in the builder**

In `build_csf_backtest_ready_from_test_evidence`, after writing `csf_backtest_gate_table.csv` and before writing `csf_backtest_contract.md`, add:

```python
    _dump_yaml(
        stage_formal_dir / "return_accounting_provenance.yaml",
        {
            "stage": "csf_backtest_ready",
            "lineage_id": lineage_root.name,
            "return_source": {
                "source_type": "tradable_return_panel",
                "input_paths": [
                    "../02_csf_data_ready/author/formal/shared_feature_base/returns_panel.parquet",
                ],
                "price_field": "",
                "return_field": "return_1d",
                "source_stage": "csf_data_ready",
                "is_signal_derived": False,
            },
            "accounting": {
                "rebalance_timing": rebalance_execution_lag,
                "holding_period": "1d",
                "fee_model": cost_model,
                "slippage_model": cost_model,
                "funding_model": "zero_or_external_to_fixture",
                "missing_price_policy": "fail_closed",
                "gross_return_formula": "sum(weight * return_1d)",
                "net_return_formula": "gross_return - fees - slippage - funding",
            },
            "formal_outputs": {
                "portfolio_summary": "portfolio_summary.parquet",
                "gate_table": "csf_backtest_gate_table.csv",
            },
        },
    )
```

- [ ] **Step 5: Add provenance to catalog and field dictionary**

In the artifact catalog list in `runtime/tools/csf_backtest_runtime.py`, add:

```python
                "- return_accounting_provenance.yaml",
```

In the field dictionary text, add:

```python
                "- `return_accounting_provenance.yaml`: 记录 formal backtest metrics 使用的真实收益来源、accounting 口径和输出绑定。",
```

- [ ] **Step 6: Run builder and session shape tests and verify they pass**

Run:

```bash
python -m pytest tests/runtime/test_csf_backtest_runtime.py tests/session/test_csf_backtest_ready_artifact_shape.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit only if explicit commit permission exists**

If the user has explicitly approved commits on the current branch, run:

```bash
git add runtime/tools/csf_backtest_runtime.py tests/runtime/test_csf_backtest_runtime.py tests/session/test_csf_backtest_ready_artifact_shape.py
git commit -m "feat: emit csf backtest return provenance"
```

If commit permission has not been granted, do not commit.

---

### Task 3: Enforce Return Provenance In The Semantic Validator

**Files:**
- Modify: `tests/runtime/test_csf_backtest_ready_semantic_validation.py`
- Modify: `runtime/tools/csf_backtest_ready_contract_runtime.py`

- [ ] **Step 1: Add failing semantic validation tests**

Append these tests to `tests/runtime/test_csf_backtest_ready_semantic_validation.py`.

```python
def test_csf_backtest_ready_semantics_rejects_missing_return_accounting_provenance(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    (formal_dir / "return_accounting_provenance.yaml").unlink()

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert "return_accounting_provenance.yaml: missing required return accounting provenance" in result.errors


def test_csf_backtest_ready_semantics_rejects_signal_panel_return_source(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))
    payload["return_source"]["source_type"] = "signal_panel"
    _write_yaml(formal_dir / "return_accounting_provenance.yaml", payload)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert "return_accounting_provenance.yaml: return_source.source_type signal_panel is forbidden for formal backtest PnL" in result.errors


def test_csf_backtest_ready_semantics_rejects_mom_ret_as_formal_return_field(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))
    payload["return_source"]["return_field"] = "mom_ret"
    payload["accounting"]["gross_return_formula"] = "sum(weight * mom_ret)"
    _write_yaml(formal_dir / "return_accounting_provenance.yaml", payload)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert "return_accounting_provenance.yaml: formal return field/formula must not use proxy token mom_ret" in result.errors


def test_csf_backtest_ready_semantics_rejects_signal_ready_only_return_paths(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = yaml.safe_load((formal_dir / "return_accounting_provenance.yaml").read_text(encoding="utf-8"))
    payload["return_source"]["input_paths"] = [
        "../03_csf_signal_ready/author/formal/factor_panel.parquet",
    ]
    _write_yaml(formal_dir / "return_accounting_provenance.yaml", payload)

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert "return_accounting_provenance.yaml: formal return input_paths must include an independent market/execution source, not only signal/train factor outputs" in result.errors


def test_csf_backtest_ready_semantics_rejects_stage_program_weight_times_mom_ret(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_backtest_ready_contract_runtime import validate_csf_backtest_ready_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    program_path = lineage_root / "program" / "cross_sectional_factor" / "backtest_ready" / "run_stage.py"
    program_path.parent.mkdir(parents=True)
    program_path.write_text(
        "gross_ret = (merged['weight'] * merged['mom_ret']).sum()\n",
        encoding="utf-8",
    )

    result = validate_csf_backtest_ready_semantics(formal_dir, lineage_root)

    assert "run_stage.py: formal backtest program appears to compute PnL from weight * mom_ret proxy returns" in result.errors
```

- [ ] **Step 2: Run semantic tests and verify they fail**

Run:

```bash
python -m pytest tests/runtime/test_csf_backtest_ready_semantic_validation.py -q
```

Expected: FAIL on the new tests because semantic validator does not inspect return provenance or stage-local code yet.

- [ ] **Step 3: Add constants and provenance loading**

In `runtime/tools/csf_backtest_ready_contract_runtime.py`, add `import re` near the top and update constants.

```python
import re
```

Add these constants after `EXPECTED_TEST_GATE_REFERENCE`.

```python
EXPECTED_RETURN_PROVENANCE_OUTPUT = "return_accounting_provenance.yaml"
ALLOWED_RETURN_SOURCE_TYPES = {
    "market_price",
    "execution_ledger",
    "mark_price",
    "ohlcv",
    "funding_adjusted_price",
    "tradable_return_panel",
}
FORBIDDEN_RETURN_SOURCE_TYPES = {
    "signal_panel",
    "factor_panel",
    "diagnostic_proxy",
    "proxy_return",
}
FORBIDDEN_FORMAL_RETURN_TOKENS = {
    "mom_ret",
    "factor_score",
    "rank_score",
    "neutralized",
    "signal",
}
MARKET_OR_EXECUTION_PATH_HINTS = {
    "02_csf_data_ready",
    "shared_feature_base/returns_panel.parquet",
    "shared_feature_base/market_panel.parquet",
    "execution_ledger",
    "execution",
}
SIGNAL_OR_FACTOR_PATH_HINTS = {
    "03_csf_signal_ready",
    "04_csf_train_freeze",
    "factor_panel.parquet",
    "signal_panel.parquet",
}
```

Add `"return_accounting_provenance.yaml"` to `REQUIRED_STAGE_OUTPUTS`.

- [ ] **Step 4: Wire provenance validation into the public validator**

In `validate_csf_backtest_ready_semantics`, load provenance and call the new helpers.

```python
    return_provenance = _load_return_accounting_provenance(
        stage_formal_dir / "return_accounting_provenance.yaml",
        errors,
    )
    if portfolio_contract is None or run_manifest is None or return_provenance is None:
        return ArtifactValidationResult(errors=errors)

    selected_variant_ids = _read_test_selected_variant_ids(lineage_root, errors)
    errors.extend(_validate_portfolio_expression(portfolio_contract, lineage_root))
    errors.extend(_validate_gate_rows(gate_rows, selected_variant_ids))
    errors.extend(_validate_return_accounting_provenance(return_provenance))
    errors.extend(_validate_stage_program_for_proxy_pnl(lineage_root))
```

Keep the existing parquet and run manifest checks after these calls.

- [ ] **Step 5: Add the provenance helper functions**

Add these functions below `_load_yaml_mapping`.

```python
def _load_return_accounting_provenance(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        errors.append(f"{path.name}: missing required return accounting provenance")
        return None
    return _load_yaml_mapping(path, errors)


def _mapping_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _validate_return_accounting_provenance(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    return_source = _mapping_value(payload, "return_source")
    accounting = _mapping_value(payload, "accounting")
    formal_outputs = _mapping_value(payload, "formal_outputs")

    source_type = str(return_source.get("source_type", "")).strip()
    if source_type in FORBIDDEN_RETURN_SOURCE_TYPES:
        errors.append(
            "return_accounting_provenance.yaml: "
            f"return_source.source_type {source_type} is forbidden for formal backtest PnL"
        )
    elif source_type not in ALLOWED_RETURN_SOURCE_TYPES:
        errors.append(
            "return_accounting_provenance.yaml: "
            f"return_source.source_type must be one of {sorted(ALLOWED_RETURN_SOURCE_TYPES)!r}"
        )

    if return_source.get("is_signal_derived") is not False:
        errors.append("return_accounting_provenance.yaml: return_source.is_signal_derived must be false")

    input_paths = _string_list(return_source.get("input_paths"))
    if not input_paths:
        errors.append("return_accounting_provenance.yaml: return_source.input_paths must not be empty")
    elif not _has_independent_market_or_execution_path(input_paths):
        errors.append(
            "return_accounting_provenance.yaml: formal return input_paths must include an independent "
            "market/execution source, not only signal/train factor outputs"
        )

    formal_return_values = [
        str(return_source.get("return_field", "")),
        str(return_source.get("price_field", "")),
        str(accounting.get("gross_return_formula", "")),
        str(accounting.get("net_return_formula", "")),
    ]
    for token in sorted(FORBIDDEN_FORMAL_RETURN_TOKENS):
        if any(_contains_forbidden_token(value, token) for value in formal_return_values):
            errors.append(
                "return_accounting_provenance.yaml: "
                f"formal return field/formula must not use proxy token {token}"
            )

    if str(formal_outputs.get("portfolio_summary", "")).strip() != "portfolio_summary.parquet":
        errors.append("return_accounting_provenance.yaml: formal_outputs.portfolio_summary must be portfolio_summary.parquet")
    if str(formal_outputs.get("gate_table", "")).strip() != "csf_backtest_gate_table.csv":
        errors.append("return_accounting_provenance.yaml: formal_outputs.gate_table must be csf_backtest_gate_table.csv")

    return errors


def _has_independent_market_or_execution_path(input_paths: list[str]) -> bool:
    normalized_paths = [path.replace("\\", "/") for path in input_paths]
    has_market_or_execution = any(
        hint in path
        for path in normalized_paths
        for hint in MARKET_OR_EXECUTION_PATH_HINTS
    )
    has_only_signal_or_factor = all(
        any(hint in path for hint in SIGNAL_OR_FACTOR_PATH_HINTS)
        for path in normalized_paths
    )
    return has_market_or_execution and not has_only_signal_or_factor


def _contains_forbidden_token(value: str, token: str) -> bool:
    if not value:
        return False
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", value) is not None
```

- [ ] **Step 6: Add stage-local code scan**

Add this helper near the other validation helpers.

```python
def _validate_stage_program_for_proxy_pnl(lineage_root: Path | None) -> list[str]:
    if lineage_root is None:
        return []
    program_path = lineage_root / "program" / "cross_sectional_factor" / "backtest_ready" / "run_stage.py"
    if not program_path.exists():
        return []
    try:
        content = program_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"run_stage.py: program read failed during proxy PnL scan: {exc}"]

    compact = re.sub(r"\s+", " ", content)
    weight_mom_ret_patterns = [
        r"weight['\"]?\]\s*\*\s*[^\\n;]*mom_ret['\"]?\]",
        r"mom_ret['\"]?\]\s*\*\s*[^\\n;]*weight['\"]?\]",
        r"\bweight\b\s*\*\s*\bmom_ret\b",
        r"\bmom_ret\b\s*\*\s*\bweight\b",
    ]
    if any(re.search(pattern, compact) for pattern in weight_mom_ret_patterns):
        return ["run_stage.py: formal backtest program appears to compute PnL from weight * mom_ret proxy returns"]
    if re.search(r"select\(\s*\[[^\]]*['\"]mom_ret['\"][^\]]*\]", compact):
        return ["run_stage.py: formal backtest program selects mom_ret for backtest return accounting"]
    return []
```

- [ ] **Step 7: Run semantic tests and verify they pass**

Run:

```bash
python -m pytest tests/runtime/test_csf_backtest_ready_semantic_validation.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit only if explicit commit permission exists**

If the user has explicitly approved commits on the current branch, run:

```bash
git add runtime/tools/csf_backtest_ready_contract_runtime.py tests/runtime/test_csf_backtest_ready_semantic_validation.py
git commit -m "fix: block proxy returns in csf backtest validation"
```

If commit permission has not been granted, do not commit.

---

### Task 4: Verify Review Preflight Blocks Illegal Provenance

**Files:**
- Modify: `tests/review/test_review_preflight_csf_backtest_ready_contract.py`

- [ ] **Step 1: Add preflight regression tests**

Append these tests to `tests/review/test_review_preflight_csf_backtest_ready_contract.py`.

```python
def test_review_preflight_blocks_csf_backtest_ready_missing_return_provenance(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_backtest_ready_stage(tmp_path)
    (stage_dir / "author" / "formal" / "return_accounting_provenance.yaml").unlink()

    payload = _run_csf_backtest_ready_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("return_accounting_provenance.yaml" in item for item in payload["content_findings"])


def test_review_preflight_blocks_csf_backtest_ready_mom_ret_return_provenance(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_backtest_ready_stage(tmp_path)
    provenance_path = stage_dir / "author" / "formal" / "return_accounting_provenance.yaml"
    payload = yaml.safe_load(provenance_path.read_text(encoding="utf-8"))
    payload["return_source"]["return_field"] = "mom_ret"
    payload["accounting"]["gross_return_formula"] = "sum(weight * mom_ret)"
    provenance_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    result = _run_csf_backtest_ready_preflight(stage_dir)

    assert result["status"] == "FAIL"
    assert any("CSF-BACKTEST-SEMANTIC-001" in item and "mom_ret" in item for item in result["content_findings"])
```

Also add this import at the top:

```python
import yaml
```

- [ ] **Step 2: Run preflight tests and verify they pass**

Run:

```bash
python -m pytest tests/review/test_review_preflight_csf_backtest_ready_contract.py -q
```

Expected: PASS. If the first new test fails with only `ARTIFACT-CONTRACT-001` and not semantic findings, keep the assertion broad as written because either contract or semantic preflight is acceptable blocking behavior.

- [ ] **Step 3: Commit only if explicit commit permission exists**

If the user has explicitly approved commits on the current branch, run:

```bash
git add tests/review/test_review_preflight_csf_backtest_ready_contract.py
git commit -m "test: cover csf backtest return provenance preflight"
```

If commit permission has not been granted, do not commit.

---

### Task 5: Update Author And Review Skill Guidance

**Files:**
- Modify: `tests/skills/test_csf_backtest_ready_contract_first_guidance.py`
- Modify: `skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md`
- Modify: `skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md`

- [ ] **Step 1: Write failing skill guidance tests**

Extend `tests/skills/test_csf_backtest_ready_contract_first_guidance.py`.

```python
def test_csf_backtest_ready_author_skill_requires_return_accounting_provenance() -> None:
    content = AUTHOR_SKILL.read_text(encoding="utf-8")

    assert "return_accounting_provenance.yaml" in content
    assert "不得使用 mom_ret 作为 formal PnL" in content
    assert "signal/factor panel proxy return 只能作为 diagnostic" in content
    assert "缺少 tradable return source 时不得伪造 backtest" in content


def test_csf_backtest_ready_review_skill_blocks_proxy_pnl() -> None:
    content = REVIEW_SKILL.read_text(encoding="utf-8")

    assert "return_accounting_provenance.yaml" in content
    assert "mom_ret" in content
    assert "proxy PnL" in content
    assert "不得进入 csf_holdout_validation" in content
```

- [ ] **Step 2: Run skill tests and verify they fail**

Run:

```bash
python -m pytest tests/skills/test_csf_backtest_ready_contract_first_guidance.py -q
```

Expected: FAIL because the skill files do not mention the new provenance/proxy-PnL requirements.

- [ ] **Step 3: Update author skill**

In `skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md`, add a short required block near the artifact/output requirements:

```markdown
## Formal Return Accounting 要求

- 必须产出 `return_accounting_provenance.yaml`，并让 `portfolio_summary.parquet` 与 `csf_backtest_gate_table.csv` 可追溯到该 provenance。
- Formal PnL 必须来自 `csf_data_ready` 的 tradable return/market price source，或来自明确 execution ledger；不得使用 `mom_ret` 作为 formal PnL。
- signal/factor panel proxy return 只能作为 diagnostic，不得进入 `portfolio_summary.parquet`、`csf_backtest_gate_table.csv` 或 review pass 口径。
- 缺少 tradable return source 时不得伪造 backtest；应停止普通推进并写出 blocking handoff，说明缺少真实可交易收益来源。
```

- [ ] **Step 4: Update review skill**

In `skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md`, add a blocking checklist block near deterministic preflight or blocking rules:

```markdown
## Formal Return Accounting Blocking Rules

- 必须检查 `return_accounting_provenance.yaml` 是否存在，并确认 `portfolio_summary.parquet` 与 `csf_backtest_gate_table.csv` 的 formal metrics 受该 provenance 支撑。
- 如果 formal return field、formula 或 stage-local program 使用 `mom_ret`、signal/factor score、rank score、neutralized factor 或其他 proxy PnL，必须判为 blocking。
- proxy PnL 只能作为 diagnostic evidence；一旦进入 formal gate metrics，不得进入 `csf_holdout_validation`。
- 如果缺少 tradable return source，应要求修复当前 `csf_backtest_ready` stage 或进入 failure handling；除非需要改变 mandate 路线或已有下游 freeze 依赖，否则不要默认开 child lineage。
```

- [ ] **Step 5: Run skill tests and verify they pass**

Run:

```bash
python -m pytest tests/skills/test_csf_backtest_ready_contract_first_guidance.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit only if explicit commit permission exists**

If the user has explicitly approved commits on the current branch, run:

```bash
git add skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md tests/skills/test_csf_backtest_ready_contract_first_guidance.py
git commit -m "docs: require tradable return provenance in csf backtest skills"
```

If commit permission has not been granted, do not commit.

---

### Task 6: Update User-Facing Docs

**Files:**
- Modify: `tests/docs/test_csf_backtest_ready_contract_first_docs.py`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `docs/guides/stage-freeze-group-field-guide.md`
- Modify: `docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md`

- [ ] **Step 1: Write failing docs tests**

Extend `tests/docs/test_csf_backtest_ready_contract_first_docs.py`.

```python
def test_csf_backtest_ready_docs_explain_return_accounting_provenance() -> None:
    paths = [
        Path("docs/guides/qros-research-session-usage.md"),
        Path("docs/guides/qros-review-shared-protocol.md"),
        Path("docs/guides/stage-freeze-group-field-guide.md"),
        Path("docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md"),
    ]

    for path in paths:
        content = path.read_text(encoding="utf-8")
        assert "return_accounting_provenance.yaml" in content, path
        assert "mom_ret" in content, path
        assert "formal" in content, path
```

- [ ] **Step 2: Run docs tests and verify they fail**

Run:

```bash
python -m pytest tests/docs/test_csf_backtest_ready_contract_first_docs.py -q
```

Expected: FAIL until each document mentions the new artifact and the `mom_ret` formal-PnL prohibition.

- [ ] **Step 3: Update `docs/guides/qros-research-session-usage.md`**

In the CSF backtest ready paragraph, add:

```markdown
`csf_backtest_ready` 的 formal metrics 还必须绑定 `return_accounting_provenance.yaml`。`portfolio_summary.parquet` 与 `csf_backtest_gate_table.csv` 只能使用来自 `csf_data_ready` tradable return / market price source 或 execution ledger 的收益口径；`mom_ret`、factor score、rank score、neutralized factor 或 signal/factor panel proxy PnL 只能作为 diagnostic，不能作为 formal gate metric。
```

- [ ] **Step 4: Update `docs/guides/qros-review-shared-protocol.md`**

In the CSF backtest preflight section, add:

```markdown
- return accounting provenance validation：读取 `return_accounting_provenance.yaml`，确认 `portfolio_summary.parquet` 与 `csf_backtest_gate_table.csv` 的 formal metrics 来自独立 tradable return / market price source 或 execution ledger；如果使用 `mom_ret` 或 signal/factor panel proxy PnL，必须 blocking。
```

- [ ] **Step 5: Update `docs/guides/stage-freeze-group-field-guide.md`**

In the `csf_backtest_ready` artifact description, add:

```markdown
`return_accounting_provenance.yaml` 是 formal PnL 的收益来源合同。它必须声明 `return_source.source_type`、`return_source.input_paths`、`return_source.return_field`、`return_source.is_signal_derived=false`、accounting 口径和 formal output 绑定。`mom_ret` 或 signal/factor panel proxy return 不得作为 formal `portfolio_summary.parquet` / `csf_backtest_gate_table.csv` 来源。
```

- [ ] **Step 6: Update `docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md`**

In the formal outputs or review checklist section, add:

```markdown
- 必须检查 `return_accounting_provenance.yaml`：formal PnL 应来自 `csf_data_ready` 的 tradable return / market price source 或 execution ledger。`mom_ret`、signal/factor score、rank score、neutralized factor 或其他 proxy PnL 只能放在 diagnostic 中，不能进入 `portfolio_summary.parquet`、`csf_backtest_gate_table.csv` 或 review pass。
```

- [ ] **Step 7: Run docs tests and verify they pass**

Run:

```bash
python -m pytest tests/docs/test_csf_backtest_ready_contract_first_docs.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit only if explicit commit permission exists**

If the user has explicitly approved commits on the current branch, run:

```bash
git add docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md docs/guides/stage-freeze-group-field-guide.md docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md tests/docs/test_csf_backtest_ready_contract_first_docs.py
git commit -m "docs: document csf backtest real return provenance"
```

If commit permission has not been granted, do not commit.

---

### Task 7: Focused Integration Verification

**Files:**
- No source edits expected in this task.

- [ ] **Step 1: Run focused contract/runtime/skill/doc tests**

Run:

```bash
python -m pytest \
  tests/contracts/test_csf_backtest_ready_artifact_contract.py \
  tests/runtime/test_csf_backtest_runtime.py \
  tests/session/test_csf_backtest_ready_artifact_shape.py \
  tests/runtime/test_csf_backtest_ready_semantic_validation.py \
  tests/review/test_review_preflight_csf_backtest_ready_contract.py \
  tests/skills/test_csf_backtest_ready_contract_first_guidance.py \
  tests/docs/test_csf_backtest_ready_contract_first_docs.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run smoke verification**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 3: Run full-smoke verification**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS. This is required because the change touches `csf_backtest_ready` stage gate semantics.

- [ ] **Step 4: Inspect final diff**

Run:

```bash
git diff --stat
git diff -- contracts/artifacts/csf_backtest_ready_artifacts.yaml runtime/tools/csf_backtest_runtime.py runtime/tools/csf_backtest_ready_contract_runtime.py
```

Expected: diff shows only CSF backtest provenance contract/runtime/validator changes plus matching tests/docs/skills.

- [ ] **Step 5: Commit only if explicit commit permission exists**

If the user has explicitly approved commits on the current branch, run:

```bash
git add contracts/artifacts/csf_backtest_ready_artifacts.yaml runtime/tools/csf_backtest_runtime.py runtime/tools/csf_backtest_ready_contract_runtime.py tests/contracts/test_csf_backtest_ready_artifact_contract.py tests/runtime/test_csf_backtest_runtime.py tests/session/test_csf_backtest_ready_artifact_shape.py tests/runtime/test_csf_backtest_ready_semantic_validation.py tests/review/test_review_preflight_csf_backtest_ready_contract.py tests/skills/test_csf_backtest_ready_contract_first_guidance.py tests/docs/test_csf_backtest_ready_contract_first_docs.py skills/csf_backtest_ready/qros-csf-backtest-ready-author/SKILL.md skills/csf_backtest_ready/qros-csf-backtest-ready-review/SKILL.md docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md docs/guides/stage-freeze-group-field-guide.md docs/sop/main-flow/06_csf_backtest_ready_sop_cn.md
git commit -m "feat: block proxy pnl in csf backtest ready"
```

If commit permission has not been granted, do not commit.

---

## Self-Review

- Spec coverage:
  - Contract artifact is covered by Task 1.
  - Runtime generation is covered by Task 2.
  - Semantic provenance gate and proxy-PnL code scan are covered by Task 3.
  - Review preflight blocking is covered by Task 4.
  - Author/review skill behavior is covered by Task 5.
  - User-facing docs are covered by Task 6.
  - Focused tests, smoke, and full-smoke are covered by Task 7.
- Placeholder scan:
  - The plan uses exact files, exact test functions, exact commands, and concrete code snippets.
  - It avoids deferred implementation language and does not rely on unspecified follow-up steps.
- Type and naming consistency:
  - The new artifact is consistently named `return_accounting_provenance.yaml`.
  - The formal output names stay `portfolio_summary.parquet` and `csf_backtest_gate_table.csv`.
  - The semantic validator error messages are matched by tests exactly.
