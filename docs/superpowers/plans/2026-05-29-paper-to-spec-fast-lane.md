# Paper-to-Spec Fast Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight `paper-to-spec` fast lane that turns a paper/PDF/URL into an implementable strategy spec bundle, without entering the heavy QROS governance workflow.

**Architecture:** Add a small machine-readable spec contract plus a runtime materializer that validates a structured spec draft, writes `strategy_spec.yaml`, renders `strategy_spec.md`, and records `source_manifest.yaml` under `outputs/paper_to_spec/<paper_slug>/`. Expose it through a repo-local wrapper and a Codex skill that tells the agent to read the source itself, separate `paper_stated` from `agent_inferred`, materialize the bundle, and only auto-implement when no blocking ambiguities remain.

**Tech Stack:** Python 3.12, `yaml`, repo-local `./.qros/bin` wrappers, Codex skill bundles, `pytest`

---

### Task 1: Add the paper-to-spec contract and runtime materializer

**Files:**
- Create: `contracts/paper_to_spec/strategy_spec_contract.yaml`
- Create: `runtime/tools/paper_to_spec.py`
- Test: `tests/paper_to_spec/test_paper_to_spec_runtime.py`

- [ ] **Step 1: Write the failing runtime tests**

```python
from pathlib import Path

import yaml

from runtime.tools.paper_to_spec import PaperToSpecError, materialize_strategy_spec_bundle, validate_strategy_spec


def _valid_spec() -> dict[str, object]:
    return {
        "spec_version": "v1",
        "strategy_identity": {
            "title": "Cross-Sectional Value Momentum",
            "summary": "Rank the universe by value and momentum, then long the top bucket and short the bottom bucket.",
            "strategy_type": "cross_sectional_factor",
        },
        "paper_stated": {
            "strategy_claim": ["Value and momentum jointly explain cross-sectional returns."],
            "market_scope": {"market": "crypto", "asset_type": "spot", "sample_period": "2021-01-01/2024-12-31"},
            "universe_rule": {"rule": "Top 50 assets by rolling dollar volume"},
            "data_requirements": {"required_fields": ["close", "volume", "market_cap"], "frequency": "1d"},
            "feature_definition": {"features": ["book_to_market_zscore", "momentum_126d"]},
            "label_or_target": {"target": "forward_return", "holding_horizon": "5d"},
            "portfolio_construction": {"method": "quintile_long_short", "rebalance_frequency": "5d"},
            "risk_controls": {"neutralization": ["market_cap"], "filters": ["min_volume"]},
            "cost_model": {"fee_bps": 10},
            "evaluation_protocol": {"metrics": ["mean_return", "sharpe", "max_drawdown"]},
        },
        "agent_inferred": {
            "inference_log": [
                {
                    "field": "implementation_choices.timestamp_semantics",
                    "decision": "Use close-to-next-open execution semantics.",
                    "reason": "The paper defines features on close prices and does not claim same-bar execution.",
                    "confidence": "medium",
                    "alternatives": ["close_to_close"],
                }
            ],
            "implementation_choices": {"timestamp_semantics": "close_to_next_open", "missing_value_policy": "drop_asset_for_bar"},
            "default_assumptions": {"winsorize": "none", "standardization": "cross_sectional_zscore"},
            "ambiguities": [],
            "fallback_plan": {"baseline_variant": "single_run", "alternate_variants": []},
        },
        "implementation_handoff": {
            "required_modules": ["data_loader.py", "signal_builder.py", "backtest.py"],
            "expected_inputs": ["daily_ohlcv.parquet"],
            "expected_outputs": ["signal.parquet", "portfolio_returns.parquet"],
            "validation_targets": ["quintile_spread_positive", "cost_adjusted_sharpe_positive"],
        },
    }


def test_validate_strategy_spec_rejects_missing_dual_layer_sections() -> None:
    with pytest.raises(PaperToSpecError, match="paper_stated"):
        validate_strategy_spec({"spec_version": "v1"})


def test_materialize_strategy_spec_bundle_writes_yaml_md_and_source_manifest(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = materialize_strategy_spec_bundle(
        outputs_root=outputs_root,
        source_locator="https://example.com/paper.pdf",
        source_kind="pdf_url",
        source_title="Cross-Sectional Value Momentum",
        spec_payload=_valid_spec(),
        requested_slug="cross_sectional_value_momentum",
    )

    bundle_root = outputs_root / "paper_to_spec" / "cross_sectional_value_momentum"
    assert result["bundle_root"] == str(bundle_root)
    assert (bundle_root / "strategy_spec.yaml").exists()
    assert (bundle_root / "strategy_spec.md").exists()
    assert (bundle_root / "source_manifest.yaml").exists()

    written_spec = yaml.safe_load((bundle_root / "strategy_spec.yaml").read_text(encoding="utf-8"))
    written_manifest = yaml.safe_load((bundle_root / "source_manifest.yaml").read_text(encoding="utf-8"))
    rendered_md = (bundle_root / "strategy_spec.md").read_text(encoding="utf-8")

    assert written_spec["strategy_identity"]["strategy_type"] == "cross_sectional_factor"
    assert written_manifest["source"]["kind"] == "pdf_url"
    assert written_manifest["source"]["locator"] == "https://example.com/paper.pdf"
    assert "paper_stated" in rendered_md
    assert "agent_inferred" in rendered_md
```

- [ ] **Step 2: Run the runtime test to verify it fails**

Run:

```bash
python -m pytest tests/paper_to_spec/test_paper_to_spec_runtime.py -q
```

Expected: FAIL with `ModuleNotFoundError` or import failure for `runtime.tools.paper_to_spec`.

- [ ] **Step 3: Add the contract and materializer implementation**

Create `contracts/paper_to_spec/strategy_spec_contract.yaml` with a stable field contract and enum set:

```yaml
schema_id: qros-paper-to-spec-contract-v1
spec_version: v1
required_top_level_fields:
  - spec_version
  - strategy_identity
  - paper_stated
  - agent_inferred
  - implementation_handoff
allowed_source_kinds:
  - pdf_url
  - webpage
  - local_pdf
  - local_doc
  - text_summary
allowed_strategy_types:
  - cross_sectional_factor
  - time_series_signal
  - event_driven
  - execution_rule
required_paper_stated_fields:
  - strategy_claim
  - market_scope
  - universe_rule
  - data_requirements
  - feature_definition
  - label_or_target
  - portfolio_construction
  - risk_controls
  - cost_model
  - evaluation_protocol
required_agent_inferred_fields:
  - inference_log
  - implementation_choices
  - default_assumptions
  - ambiguities
  - fallback_plan
required_implementation_handoff_fields:
  - required_modules
  - expected_inputs
  - expected_outputs
  - validation_targets
```

Create `runtime/tools/paper_to_spec.py` with a small validator + materializer:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import re
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "contracts" / "paper_to_spec" / "strategy_spec_contract.yaml"


class PaperToSpecError(RuntimeError):
    pass


@dataclass(frozen=True)
class MaterializedBundle:
    bundle_root: Path
    slug: str
    source_manifest_path: Path
    strategy_spec_path: Path
    strategy_markdown_path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "bundle_root": str(self.bundle_root),
            "slug": self.slug,
            "source_manifest_path": str(self.source_manifest_path),
            "strategy_spec_path": str(self.strategy_spec_path),
            "strategy_markdown_path": str(self.strategy_markdown_path),
        }


def validate_strategy_spec(spec_payload: dict[str, Any]) -> dict[str, Any]:
    contract = _load_yaml(CONTRACT_PATH)
    for field in contract["required_top_level_fields"]:
        if field not in spec_payload:
            raise PaperToSpecError(f"strategy spec missing required top-level field: {field}")
    strategy_identity = _require_map(spec_payload, "strategy_identity")
    strategy_type = str(strategy_identity.get("strategy_type", "")).strip()
    if strategy_type not in contract["allowed_strategy_types"]:
        raise PaperToSpecError(f"unsupported strategy_type: {strategy_type}")
    _require_fields(_require_map(spec_payload, "paper_stated"), contract["required_paper_stated_fields"], "paper_stated")
    _require_fields(_require_map(spec_payload, "agent_inferred"), contract["required_agent_inferred_fields"], "agent_inferred")
    _require_fields(_require_map(spec_payload, "implementation_handoff"), contract["required_implementation_handoff_fields"], "implementation_handoff")
    return spec_payload


def materialize_strategy_spec_bundle(
    *,
    outputs_root: Path,
    source_locator: str,
    source_kind: str,
    source_title: str,
    spec_payload: dict[str, Any],
    requested_slug: str | None = None,
) -> dict[str, str]:
    contract = _load_yaml(CONTRACT_PATH)
    if source_kind not in contract["allowed_source_kinds"]:
        raise PaperToSpecError(f"unsupported source kind: {source_kind}")
    validated = validate_strategy_spec(spec_payload)
    slug = requested_slug or slugify_name(source_title or validated["strategy_identity"]["title"])
    bundle_root = outputs_root / "paper_to_spec" / slug
    bundle_root.mkdir(parents=True, exist_ok=True)

    source_manifest = {
        "schema_id": "qros-paper-to-spec-source-manifest-v1",
        "source": {
            "kind": source_kind,
            "locator": source_locator,
            "title": source_title,
            "capture_time": datetime.now(UTC).isoformat(),
        },
    }

    strategy_spec_path = bundle_root / "strategy_spec.yaml"
    source_manifest_path = bundle_root / "source_manifest.yaml"
    strategy_markdown_path = bundle_root / "strategy_spec.md"

    _write_yaml(strategy_spec_path, validated)
    _write_yaml(source_manifest_path, source_manifest)
    strategy_markdown_path.write_text(render_strategy_spec_markdown(validated, source_manifest), encoding="utf-8")

    return MaterializedBundle(
        bundle_root=bundle_root,
        slug=slug,
        source_manifest_path=source_manifest_path,
        strategy_spec_path=strategy_spec_path,
        strategy_markdown_path=strategy_markdown_path,
    ).as_dict()


def render_strategy_spec_markdown(spec_payload: dict[str, Any], source_manifest: dict[str, Any]) -> str:
    strategy_identity = spec_payload["strategy_identity"]
    source = source_manifest["source"]
    lines = [
        f"# {strategy_identity['title']}",
        "",
        "## source",
        f"- kind: {source['kind']}",
        f"- locator: {source['locator']}",
        f"- title: {source['title']}",
        "",
        "## strategy_identity",
        f"- summary: {strategy_identity['summary']}",
        f"- strategy_type: {strategy_identity['strategy_type']}",
        "",
        "## paper_stated",
        yaml.safe_dump(spec_payload["paper_stated"], allow_unicode=True, sort_keys=False).strip(),
        "",
        "## agent_inferred",
        yaml.safe_dump(spec_payload["agent_inferred"], allow_unicode=True, sort_keys=False).strip(),
        "",
        "## implementation_handoff",
        yaml.safe_dump(spec_payload["implementation_handoff"], allow_unicode=True, sort_keys=False).strip(),
    ]
    return "\n".join(lines) + "\n"


def slugify_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "paper_to_spec"


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperToSpecError(f"{path} must contain a YAML mapping")
    return payload


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _require_map(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise PaperToSpecError(f"strategy spec field must be a map: {key}")
    return value


def _require_fields(payload: dict[str, Any], required_fields: list[str], section_name: str) -> None:
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise PaperToSpecError(f"{section_name} missing required fields: {', '.join(missing)}")
```

- [ ] **Step 4: Run the runtime test to verify it passes**

Run:

```bash
python -m pytest tests/paper_to_spec/test_paper_to_spec_runtime.py -q
```

Expected: PASS with 2 passing tests.

- [ ] **Step 5: Commit**

```bash
git add contracts/paper_to_spec/strategy_spec_contract.yaml runtime/tools/paper_to_spec.py tests/paper_to_spec/test_paper_to_spec_runtime.py
git commit -m "feat: add paper-to-spec materializer"
```

### Task 2: Add the CLI script and repo-local wrapper

**Files:**
- Create: `runtime/scripts/run_paper_to_spec.py`
- Create: `runtime/bin/qros-paper-to-spec`
- Test: `tests/paper_to_spec/test_run_paper_to_spec_script.py`

- [ ] **Step 1: Write the failing CLI test**

```python
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def _spec_payload() -> dict[str, object]:
    return {
        "spec_version": "v1",
        "strategy_identity": {
            "title": "Intraday Reversal",
            "summary": "Fade the largest same-day intraday move at the close.",
            "strategy_type": "time_series_signal",
        },
        "paper_stated": {
            "strategy_claim": ["Extreme intraday moves partially mean-revert overnight."],
            "market_scope": {"market": "equity", "asset_type": "stock", "sample_period": "2015-01-01/2024-12-31"},
            "universe_rule": {"rule": "Stocks above a rolling ADV threshold"},
            "data_requirements": {"required_fields": ["open", "close", "volume"], "frequency": "1d"},
            "feature_definition": {"features": ["intraday_return"]},
            "label_or_target": {"target": "overnight_return", "holding_horizon": "1d"},
            "portfolio_construction": {"method": "threshold_short_signal", "rebalance_frequency": "1d"},
            "risk_controls": {"neutralization": [], "filters": ["earnings_blackout"]},
            "cost_model": {"fee_bps": 5},
            "evaluation_protocol": {"metrics": ["hit_rate", "mean_return"]},
        },
        "agent_inferred": {
            "inference_log": [],
            "implementation_choices": {"timestamp_semantics": "close_to_next_open"},
            "default_assumptions": {"missing_value_policy": "drop_asset_for_bar"},
            "ambiguities": [],
            "fallback_plan": {"baseline_variant": "single_threshold", "alternate_variants": []},
        },
        "implementation_handoff": {
            "required_modules": ["loader.py", "signal.py", "portfolio.py"],
            "expected_inputs": ["daily_bars.parquet"],
            "expected_outputs": ["orders.parquet"],
            "validation_targets": ["overnight_mean_reversion_positive"],
        },
    }


def test_run_paper_to_spec_script_materializes_bundle_and_prints_json(tmp_path: Path) -> None:
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.safe_dump(_spec_payload(), allow_unicode=True, sort_keys=False), encoding="utf-8")
    outputs_root = tmp_path / "outputs"
    script_path = REPO_ROOT / "runtime" / "scripts" / "run_paper_to_spec.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--spec-file",
            str(spec_file),
            "--source",
            "https://example.com/reversal.pdf",
            "--source-kind",
            "pdf_url",
            "--title",
            "Intraday Reversal",
            "--slug",
            "intraday_reversal",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert '"slug": "intraday_reversal"' in result.stdout
    assert (outputs_root / "paper_to_spec" / "intraday_reversal" / "strategy_spec.yaml").exists()
```

- [ ] **Step 2: Run the CLI test to verify it fails**

Run:

```bash
python -m pytest tests/paper_to_spec/test_run_paper_to_spec_script.py -q
```

Expected: FAIL because `runtime/scripts/run_paper_to_spec.py` does not exist.

- [ ] **Step 3: Add the CLI script and wrapper**

Create `runtime/scripts/run_paper_to_spec.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.paper_to_spec import PaperToSpecError, materialize_strategy_spec_bundle  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize a QROS paper-to-spec bundle.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--spec-file", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-kind", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _load_spec_file(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperToSpecError(f"spec file must contain a YAML mapping: {path}")
    return payload


def _render_text(result: dict[str, str]) -> str:
    return "\n".join(
        [
            "QROS Paper-to-Spec",
            f"Slug: {result['slug']}",
            f"Bundle root: {result['bundle_root']}",
            f"Spec: {result['strategy_spec_path']}",
            f"Markdown: {result['strategy_markdown_path']}",
            f"Source manifest: {result['source_manifest_path']}",
        ]
    )


def main() -> int:
    args = _parse_args()
    try:
        result = materialize_strategy_spec_bundle(
            outputs_root=args.outputs_root.resolve(),
            source_locator=args.source,
            source_kind=args.source_kind,
            source_title=args.title,
            spec_payload=_load_spec_file(args.spec_file),
            requested_slug=args.slug,
        )
    except PaperToSpecError as exc:
        print(f"qros-paper-to-spec: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `runtime/bin/qros-paper-to-spec`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_CWD="$PWD"
ARGS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --cwd)
      TARGET_CWD="$2"
      shift 2
      ;;
    --outputs-root)
      echo "qros-paper-to-spec does not accept --outputs-root; it is derived from the project root" >&2
      exit 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

PROJECT_ROOT="$(cd "$TARGET_CWD" && pwd)"

source "$SCRIPT_DIR/qros-wrapper-lib"
PYTHON_BIN="$(qros_select_python_bin "$SCRIPT_DIR")"
qros_verify_runtime_lock "$SCRIPT_DIR" "$PYTHON_BIN"
RUNTIME_ROOT="$(qros_resolve_runtime_root "$SCRIPT_DIR" "$PYTHON_BIN" strict)"

cd "$PROJECT_ROOT"
exec "$PYTHON_BIN" "$RUNTIME_ROOT/scripts/run_paper_to_spec.py" --outputs-root "$PROJECT_ROOT/outputs" "${ARGS[@]}"
```

- [ ] **Step 4: Run the CLI test to verify it passes**

Run:

```bash
python -m pytest tests/paper_to_spec/test_run_paper_to_spec_script.py -q
```

Expected: PASS with 1 passing test and a materialized bundle under the temp `outputs/` tree.

- [ ] **Step 5: Commit**

```bash
git add runtime/scripts/run_paper_to_spec.py runtime/bin/qros-paper-to-spec tests/paper_to_spec/test_run_paper_to_spec_script.py
git commit -m "feat: add paper-to-spec wrapper"
```

### Task 3: Add the Codex skill and user-facing docs

**Files:**
- Create: `skills/core/qros-paper-to-spec/SKILL.md`
- Create: `docs/guides/qros-paper-to-spec-usage.md`
- Modify: `docs/README.codex.md`
- Test: `tests/skills/test_paper_to_spec_assets.py`
- Test: `tests/docs/test_paper_to_spec_docs.py`

- [ ] **Step 1: Write the failing skill/docs tests**

```python
from pathlib import Path

from tests.helpers.skill_test_utils import skill_path


def test_paper_to_spec_skill_exists_and_declares_fast_lane_boundaries() -> None:
    content = skill_path("qros-paper-to-spec").read_text(encoding="utf-8")

    assert "Use when the user wants to turn a paper, PDF, or URL into an implementable strategy spec" in content
    assert "paper_stated" in content
    assert "agent_inferred" in content
    assert "不得进入 mandate_admission" in content
    assert "./.qros/bin/qros-paper-to-spec" in content


def test_paper_to_spec_usage_docs_exist_and_are_linked() -> None:
    guide = Path("docs/guides/qros-paper-to-spec-usage.md")
    assert guide.exists()
    guide_text = guide.read_text(encoding="utf-8")
    codex_readme = Path("docs/README.codex.md").read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in guide_text
    assert "strategy_spec.yaml" in guide_text
    assert "$qros-paper-to-spec" in codex_readme
    assert "docs/guides/qros-paper-to-spec-usage.md" in codex_readme
```

- [ ] **Step 2: Run the skill/docs tests to verify they fail**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py -q
```

Expected: FAIL because the skill bundle and usage doc do not exist yet.

- [ ] **Step 3: Add the skill and docs**

Create `skills/core/qros-paper-to-spec/SKILL.md`:

```markdown
---
name: qros-paper-to-spec
description: Use when the user wants to turn a paper, PDF, or URL into an implementable strategy spec, optionally followed by automatic implementation.
---

# QROS Paper-to-Spec

## Purpose

这是独立于 `qros-research-session` 的轻量 fast lane。

它负责：

- 读取用户提供的论文、PDF、网页链接或长文本摘要
- 提炼 `paper_stated` 与 `agent_inferred`
- 生成可实现策略层 spec
- 在无高风险歧义且用户显式要求时继续自动实现

## Hard Boundaries

- 不得进入 `mandate_admission`。
- 不得进入 freeze / review / failure handling 主流程。
- 不得把 `agent_inferred` 冒充为论文原文。
- 不得在 `ambiguities` 包含高风险策略本体歧义时自动实现。

## Required Output Bundle

必须物化到：

- `outputs/paper_to_spec/<paper_slug>/strategy_spec.yaml`
- `outputs/paper_to_spec/<paper_slug>/strategy_spec.md`
- `outputs/paper_to_spec/<paper_slug>/source_manifest.yaml`

Repo-local materializer:

```bash
./.qros/bin/qros-paper-to-spec --spec-file /tmp/spec.yaml --source "https://example.com/paper.pdf" --source-kind pdf_url --title "Paper Title" --slug paper_title
```

## Working Rules

1. 先读取 source，再做 claim / formula / ambiguity inventory。
2. 只把 source 可归因的内容写入 `paper_stated`。
3. 论文未写清但实现必需的部分写入 `agent_inferred`。
4. `ambiguities` 必须显式列出阻断自动实现的高风险歧义。
5. 默认停在 spec；只有用户显式要求且 `ambiguities` 不阻断时，才继续实现。
```

Create `docs/guides/qros-paper-to-spec-usage.md`:

```markdown
# QROS Paper-to-Spec 使用说明

## 它是什么

`qros-paper-to-spec` 是一个独立 fast lane，用于把论文、PDF 或 URL 压成可实现策略层 spec。

它不进入 `qros-research-session` 主流程，也不要求 freeze / review / failure handling。

## 输出物

- `outputs/paper_to_spec/<paper_slug>/strategy_spec.yaml`
- `outputs/paper_to_spec/<paper_slug>/strategy_spec.md`
- `outputs/paper_to_spec/<paper_slug>/source_manifest.yaml`

`strategy_spec.yaml` 的核心要求是把论文原文支持的内容放到 `paper_stated`，把实现必需但论文未明确的补全放到 `agent_inferred`。

## 在 Codex 里怎么用

```text
$qros-paper-to-spec https://example.com/paper.pdf
$qros-paper-to-spec /abs/path/to/paper.pdf
$qros-paper-to-spec https://example.com/paper.pdf --auto-implement
```

## Runtime 调试入口

```bash
./.qros/bin/qros-paper-to-spec --spec-file /tmp/spec.yaml --source "https://example.com/paper.pdf" --source-kind pdf_url --title "Paper Title" --slug paper_title
```
```

Modify `docs/README.codex.md` to add the new entry to the usage table and wrapper examples:

```markdown
| 把论文 / PDF / URL 压成实现 spec | `$qros-paper-to-spec` |
```

and:

```bash
./.qros/bin/qros-paper-to-spec --spec-file /tmp/spec.yaml --source "https://example.com/paper.pdf" --source-kind pdf_url --title "Paper Title" --slug paper_title
```

- [ ] **Step 4: Run the skill/docs tests to verify they pass**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py -q
```

Expected: PASS with both tests green.

- [ ] **Step 5: Commit**

```bash
git add skills/core/qros-paper-to-spec/SKILL.md docs/guides/qros-paper-to-spec-usage.md docs/README.codex.md tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py
git commit -m "feat: add paper-to-spec skill and docs"
```

### Task 4: Wire bootstrap coverage and run focused verification + smoke

**Files:**
- Modify: `tests/bootstrap/test_project_bootstrap.py`
- Modify: `tests/docs/test_install_docs.py`
- Test: `tests/bootstrap/test_project_bootstrap.py`
- Test: `tests/docs/test_install_docs.py`
- Test: `tests/paper_to_spec/test_paper_to_spec_runtime.py`
- Test: `tests/paper_to_spec/test_run_paper_to_spec_script.py`
- Test: `tests/skills/test_paper_to_spec_assets.py`
- Test: `tests/docs/test_paper_to_spec_docs.py`

- [ ] **Step 1: Extend the bootstrap/doc regression tests**

Add these assertions to `tests/bootstrap/test_project_bootstrap.py`:

```python
assert Path("runtime/bin/qros-paper-to-spec").exists()
assert Path("runtime/scripts/run_paper_to_spec.py").exists()
assert Path("runtime/tools/paper_to_spec.py").exists()
assert Path("contracts/paper_to_spec/strategy_spec_contract.yaml").exists()
assert Path("docs/guides/qros-paper-to-spec-usage.md").exists()
assert skill_path("qros-paper-to-spec").exists()
```

Add these assertions to `tests/docs/test_install_docs.py`:

```python
def test_codex_readme_documents_paper_to_spec_entrypoint() -> None:
    content = Path("docs/README.codex.md").read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in content
    assert "./.qros/bin/qros-paper-to-spec" in content
    assert "docs/guides/qros-paper-to-spec-usage.md" in content
```

- [ ] **Step 2: Run the focused verification suite before smoke**

Run:

```bash
python -m pytest \
  tests/paper_to_spec/test_paper_to_spec_runtime.py \
  tests/paper_to_spec/test_run_paper_to_spec_script.py \
  tests/skills/test_paper_to_spec_assets.py \
  tests/docs/test_paper_to_spec_docs.py \
  tests/bootstrap/test_project_bootstrap.py \
  tests/docs/test_install_docs.py -q
```

Expected: PASS with all paper-to-spec tests, bootstrap assertions, and doc assertions green.

- [ ] **Step 3: Run smoke because this is a new user-facing runtime entrypoint**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS. This feature does not change `qros-research-session` stage flow, route split semantics, review orchestration, anti-drift stage naming, or stage-display contracts, so `full-smoke` is not required.

- [ ] **Step 4: Sanity-check the output bundle shape manually in the repo-local path**

Run:

```bash
python runtime/scripts/run_paper_to_spec.py \
  --outputs-root /tmp/qros-paper-to-spec-check/outputs \
  --spec-file /tmp/qros-paper-to-spec-check/spec.yaml \
  --source "https://example.com/paper.pdf" \
  --source-kind pdf_url \
  --title "Paper Title" \
  --slug paper_title \
  --json
```

Expected: JSON output containing `bundle_root`, `strategy_spec_path`, `strategy_markdown_path`, and `source_manifest_path`, with all three files present under `/tmp/qros-paper-to-spec-check/outputs/paper_to_spec/paper_title/`.

- [ ] **Step 5: Commit**

```bash
git add tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py
git commit -m "test: cover paper-to-spec bootstrap and docs"
```

## Self-Review Checklist

- Spec coverage:
  - Fast-lane boundary: Task 3 skill + docs.
  - `paper_stated` / `agent_inferred` split: Task 1 contract + runtime validator.
  - Output bundle shape: Task 1 materializer + Task 2 CLI.
  - Optional auto-implement gate: Task 3 skill boundaries and ambiguity rule.
  - Failure boundaries: Task 3 skill rules and Task 1 validation errors.
- Placeholder scan: no `TODO` / `TBD` / “similar to Task N” placeholders remain.
- Type consistency:
  - `strategy_type` enums stay aligned between contract, runtime, tests, and docs.
  - Output filenames stay aligned as `strategy_spec.yaml`, `strategy_spec.md`, and `source_manifest.yaml`.
  - CLI naming stays aligned as `qros-paper-to-spec` / `run_paper_to_spec.py`.
