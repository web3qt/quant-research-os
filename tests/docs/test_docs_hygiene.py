from pathlib import Path


LEGACY_DOC_TOKENS = (
    "docs/all-sops",
    "docs/gates/",
    "docs/check-sop/",
    "第一层-主流程sop",
    "第二层-阶段失败 sop",
    "第四层-check",
)

LIVE_DOC_FILES = (
    Path("README.md"),
    Path("docs/README.md"),
    Path("docs/README.codex.md"),
    *sorted(Path("docs/guides").glob("*.md")),
    *sorted(Path("docs/sop/main-flow").glob("*.md")),
    *sorted(Path("docs/sop/failures").glob("*.md")),
    *sorted(Path("docs/sop/review").glob("*.md")),
)

LEGACY_RUNTIME_TOKENS = (
    "03_train_calibration",
    "train_calibration",
    "05_backtest",
    "06_holdout",
    "stage-failure-harness",
    "shadow",
    "Shadow",
    "git clone",
    "git pull",
    "tools/research_session.py",
    "scripts/run_research_session.py",
)


def test_live_docs_do_not_reference_legacy_doc_layout() -> None:
    offenders: list[str] = []

    for path in LIVE_DOC_FILES:
        text = path.read_text(encoding="utf-8")
        matches = [token for token in LEGACY_DOC_TOKENS if token in text]
        if matches:
            offenders.append(f"{path}: {', '.join(matches)}")

    assert not offenders, "Legacy doc-layout references remain in live docs:\n" + "\n".join(offenders)


def test_live_docs_do_not_reference_legacy_runtime_stage_or_install_terms() -> None:
    offenders: list[str] = []

    for path in LIVE_DOC_FILES:
        text = path.read_text(encoding="utf-8")
        matches = [token for token in LEGACY_RUNTIME_TOKENS if token in text]
        if matches:
            offenders.append(f"{path}: {', '.join(matches)}")

    assert not offenders, "Legacy runtime/install terms remain in live docs:\n" + "\n".join(offenders)


def test_docs_index_exists_and_points_to_current_truth_layers() -> None:
    content = Path("docs/README.md").read_text(encoding="utf-8")

    assert "contracts/stages/workflow_stage_gates.yaml" in content
    assert "contracts/review/review_checklist_master.yaml" in content
    assert "docs/archive/plans/" in content
    assert "不是当前运行时真值" in content
