# Codex Stage Review Skill System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first Codex-native stage review skill system for `Mandate`, `Data Ready`, and `Signal Ready`, generated from the existing gate and checklist YAML sources.

**Architecture:** Use a `shared prompt engine` approach instead of a runtime CLI. A small Python generator loads the existing YAML contracts, renders a shared review template plus stage-specific sections, and writes 3 Codex skills into `.agents/skills/`. The skills themselves perform the actual review at run time by reading stage artifacts and writing closure artifacts.

**Tech Stack:** Python 3.11, `PyYAML`, `pytest`, generated Codex `SKILL.md` files, existing YAML sources under `docs/`

---

### Task 1: Bootstrap The Minimal Skill Generator Toolchain

**Files:**
- Create: `pyproject.toml`
- Create: `tools/review_skillgen/__init__.py`
- Create: `tests/test_project_bootstrap.py`

**Step 1: Write the failing bootstrap test**

```python
from pathlib import Path


def test_project_bootstrap_files_exist() -> None:
    assert Path("pyproject.toml").exists()
    assert Path("tools/review_skillgen/__init__.py").exists()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_project_bootstrap.py -v
```

Expected: FAIL because the new files do not exist yet.

**Step 3: Write the minimal toolchain files**

Create `pyproject.toml`:

```toml
[project]
name = "quant-research-os"
version = "0.1.0"
description = "Codex skill generator for stage review workflows"
requires-python = ">=3.11"
dependencies = [
  "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

Create `tools/review_skillgen/__init__.py`:

```python
"""Skill generation helpers for Codex stage review skills."""
```

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_project_bootstrap.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml tools/review_skillgen/__init__.py tests/test_project_bootstrap.py
git commit -m "build: bootstrap codex skill generator toolchain"
```

### Task 2: Load And Validate The Gate + Checklist Schemas

**Files:**
- Create: `tools/review_skillgen/loaders.py`
- Create: `tools/review_skillgen/models.py`
- Test: `tests/test_schema_loaders.py`

**Step 1: Write the failing schema loader tests**

```python
from tools.review_skillgen.loaders import load_gate_schema, load_checklist_schema


def test_gate_schema_contains_first_wave_stages() -> None:
    gates = load_gate_schema("docs/gates/workflow_stage_gates.yaml")
    assert "mandate" in gates["stages"]
    assert "data_ready" in gates["stages"]
    assert "signal_ready" in gates["stages"]


def test_checklist_schema_contains_first_wave_stages() -> None:
    checklist = load_checklist_schema("docs/check-sop/review_checklist_master.yaml")
    assert "mandate" in checklist["stages"]
    assert "data_ready" in checklist["stages"]
    assert "signal_ready" in checklist["stages"]
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_schema_loaders.py -v
```

Expected: FAIL with import errors.

**Step 3: Implement the minimal schema loader**

Create `tools/review_skillgen/loaders.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must load to a mapping")
    return data


def load_gate_schema(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    if "stages" not in data:
        raise ValueError("gate schema missing stages")
    return data


def load_checklist_schema(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    if "stages" not in data:
        raise ValueError("checklist schema missing stages")
    return data
```

Create `tools/review_skillgen/models.py` with lightweight typed aliases only:

```python
from typing import Any

GateSchema = dict[str, Any]
ChecklistSchema = dict[str, Any]
```

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_schema_loaders.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tools/review_skillgen/loaders.py tools/review_skillgen/models.py tests/test_schema_loaders.py
git commit -m "feat: load stage gate and checklist schemas"
```

### Task 3: Implement The Shared Review Prompt Renderer

**Files:**
- Create: `templates/skills/review-stage/SKILL.md.tmpl`
- Create: `tools/review_skillgen/render.py`
- Test: `tests/test_render.py`

**Step 1: Write the failing renderer test**

```python
from tools.review_skillgen.render import render_stage_skill
from tools.review_skillgen.loaders import load_gate_schema, load_checklist_schema


def test_render_stage_skill_includes_stage_specific_contract() -> None:
    gates = load_gate_schema("docs/gates/workflow_stage_gates.yaml")
    checklist = load_checklist_schema("docs/check-sop/review_checklist_master.yaml")

    text = render_stage_skill(
        stage_key="mandate",
        skill_name="qros-mandate-review",
        gate_schema=gates,
        checklist_schema=checklist,
    )

    assert "Mandate" in text
    assert "formal gate" in text.lower()
    assert "latest_review_pack.yaml" in text
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_render.py -v
```

Expected: FAIL because the renderer does not exist yet.

**Step 3: Implement the shared renderer**

Template requirements for `templates/skills/review-stage/SKILL.md.tmpl`:

- frontmatter with generated `name` and `description`
- shared review protocol
- shared inputs section
- stage-specific formal gate summary
- stage-specific checklist summary
- verdict vocabulary
- closure artifact writing instructions

Minimal renderer shape for `tools/review_skillgen/render.py`:

```python
from __future__ import annotations

from pathlib import Path


def render_stage_skill(stage_key: str, skill_name: str, gate_schema: dict, checklist_schema: dict) -> str:
    stage_contract = gate_schema["stages"][stage_key]
    stage_checks = checklist_schema["stages"][stage_key]["checks"]
    template = Path("templates/skills/review-stage/SKILL.md.tmpl").read_text(encoding="utf-8")
    return (
        template
        .replace("{{SKILL_NAME}}", skill_name)
        .replace("{{STAGE_NAME}}", stage_contract["stage_name"])
        .replace("{{STAGE_PURPOSE}}", stage_contract["purpose"])
        .replace("{{FORMAL_GATE_BLOCK}}", _render_formal_gate(stage_contract))
        .replace("{{CHECKLIST_BLOCK}}", _render_checklist(stage_checks))
    )
```

The first version should stay simple: plain string replacement is fine.

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_render.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add templates/skills/review-stage/SKILL.md.tmpl tools/review_skillgen/render.py tests/test_render.py
git commit -m "feat: render shared codex review skill template"
```

### Task 4: Generate The 3 Codex Review Skills

**Files:**
- Create: `scripts/gen_codex_stage_review_skills.py`
- Create: `.agents/skills/qros-mandate-review/SKILL.md`
- Create: `.agents/skills/qros-data-ready-review/SKILL.md`
- Create: `.agents/skills/qros-signal-ready-review/SKILL.md`
- Create: `.agents/skills/qros-mandate-review/agents/openai.yaml`
- Create: `.agents/skills/qros-data-ready-review/agents/openai.yaml`
- Create: `.agents/skills/qros-signal-ready-review/agents/openai.yaml`
- Test: `tests/test_generation.py`

**Step 1: Write the failing generation test**

```python
from pathlib import Path
from subprocess import run


def test_generator_writes_first_wave_skills() -> None:
    result = run(
        ["python", "scripts/gen_codex_stage_review_skills.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert Path(".agents/skills/qros-mandate-review/SKILL.md").exists()
    assert Path(".agents/skills/qros-data-ready-review/SKILL.md").exists()
    assert Path(".agents/skills/qros-signal-ready-review/SKILL.md").exists()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_generation.py -v
```

Expected: FAIL because the generator script does not exist yet.

**Step 3: Implement the generator CLI**

Create `scripts/gen_codex_stage_review_skills.py`:

```python
from __future__ import annotations

from pathlib import Path

from tools.review_skillgen.loaders import load_gate_schema, load_checklist_schema
from tools.review_skillgen.render import render_stage_skill


FIRST_WAVE = {
    "mandate": "qros-mandate-review",
    "data_ready": "qros-data-ready-review",
    "signal_ready": "qros-signal-ready-review",
}


def main() -> int:
    gates = load_gate_schema("docs/gates/workflow_stage_gates.yaml")
    checklist = load_checklist_schema("docs/check-sop/review_checklist_master.yaml")

    for stage_key, skill_name in FIRST_WAVE.items():
        out_dir = Path(".agents/skills") / skill_name
        out_dir.mkdir(parents=True, exist_ok=True)
        text = render_stage_skill(stage_key, skill_name, gates, checklist)
        (out_dir / "SKILL.md").write_text(text, encoding="utf-8")

        agents_dir = out_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        (agents_dir / "openai.yaml").write_text(
            f"name: {skill_name}\ndescription: Stage review skill for {stage_key}\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_generation.py -v
python scripts/gen_codex_stage_review_skills.py
```

Expected: PASS and the 3 generated skill directories exist.

**Step 5: Commit**

```bash
git add scripts/gen_codex_stage_review_skills.py .agents/skills tests/test_generation.py
git commit -m "feat: generate first-wave codex stage review skills"
```

### Task 5: Add Freshness Validation And Stage-Specific Regression Tests

**Files:**
- Create: `tests/test_generated_skills_fresh.py`
- Modify: `scripts/gen_codex_stage_review_skills.py`

**Step 1: Write the failing freshness test**

```python
from pathlib import Path

from tools.review_skillgen.loaders import load_gate_schema, load_checklist_schema
from tools.review_skillgen.render import render_stage_skill


def test_generated_mandate_skill_is_fresh() -> None:
    gates = load_gate_schema("docs/gates/workflow_stage_gates.yaml")
    checklist = load_checklist_schema("docs/check-sop/review_checklist_master.yaml")
    rendered = render_stage_skill("mandate", "qros-mandate-review", gates, checklist)
    existing = Path(".agents/skills/qros-mandate-review/SKILL.md").read_text(encoding="utf-8")
    assert rendered == existing
```

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_generated_skills_fresh.py -v
```

Expected: FAIL until the generator output is stable and checked in.

**Step 3: Add dry-run support**

Extend `scripts/gen_codex_stage_review_skills.py` with:

- `--dry-run`
- non-zero exit code when generated output differs from checked-in files
- human-readable `FRESH:` / `STALE:` output

Expected CLI shape:

```bash
python scripts/gen_codex_stage_review_skills.py --dry-run
```

**Step 4: Run the full test suite**

Run:

```bash
python -m pytest tests -v
python scripts/gen_codex_stage_review_skills.py --dry-run
```

Expected: all PASS, all generated files reported as `FRESH`.

**Step 5: Commit**

```bash
git add scripts/gen_codex_stage_review_skills.py tests/test_generated_skills_fresh.py
git commit -m "test: validate generated codex review skills stay fresh"
```

### Task 6: Document Usage And Verification

**Files:**
- Create: `docs/experience/codex-stage-review-skill-usage.md`

**Step 1: Write the failing doc existence test**

```python
from pathlib import Path


def test_usage_doc_exists() -> None:
    assert Path("docs/experience/codex-stage-review-skill-usage.md").exists()
```

Add this test to `tests/test_project_bootstrap.py`.

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_project_bootstrap.py -v
```

Expected: FAIL because the usage doc does not exist yet.

**Step 3: Write the usage doc**

Create `docs/experience/codex-stage-review-skill-usage.md` covering:

- what the 3 first-wave skills do
- where they read rules from
- what evidence artifacts they expect
- what closure artifacts they write
- how to regenerate them with `python scripts/gen_codex_stage_review_skills.py`
- how to validate freshness with `--dry-run`

**Step 4: Run the targeted test**

Run:

```bash
python -m pytest tests/test_project_bootstrap.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add docs/experience/codex-stage-review-skill-usage.md tests/test_project_bootstrap.py
git commit -m "docs: add codex stage review skill usage guide"
```

### Verification Checklist

Run these before claiming the implementation is complete:

```bash
python -m pytest tests -v
python scripts/gen_codex_stage_review_skills.py
python scripts/gen_codex_stage_review_skills.py --dry-run
git status --short
```

Expected:

- tests all pass
- 3 generated skill directories exist
- dry-run reports everything as fresh
- git status only shows intentional changes

### Notes For The Implementer

- This plan intentionally uses Python instead of Rust for the first iteration.
- Reason: this is a text-generation bootstrap path for Codex skills, not a production trading runtime.
- Treat this as an explicit `non_rust_exception` for bootstrap tooling only.
- Keep the renderer simple in v1. Do not introduce Jinja, Click, Pydantic, or a larger framework unless the standard library approach becomes insufficient.

### Execution Order Summary

1. Bootstrap Python tooling
2. Load gate/checklist YAML
3. Render shared template
4. Generate first-wave skills
5. Add freshness validation
6. Document usage
