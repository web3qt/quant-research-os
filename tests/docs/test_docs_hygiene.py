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


def test_active_docs_and_skills_use_mandate_admission_first_stage_terms() -> None:
    checked_paths = [
        Path("README.md"),
        Path("docs/SUMMARY.md"),
        Path("docs/README.md"),
        Path("docs/README.codex.md"),
        *sorted(Path("docs/guides").glob("*.md")),
        *sorted(Path("docs/sop/main-flow").glob("*.md")),
        *sorted(Path("docs/visuals").glob("*.drawio")),
        *sorted(Path("docs/visuals/csf/image").glob("*.drawio")),
        *sorted(Path("docs/visuals/csf/image").glob("*.excalidraw")),
        *sorted(Path("docs/visuals/csf/image").glob("*.excalidraw.md")),
        *sorted(Path("skills").glob("**/SKILL.md")),
    ]
    stale_tokens = [
        "00_" + "idea" + "_intake",
        "GO_TO_" + "MANDATE",
        "mandate_" + "confirmation_pending",
        "idea" + "_intake_confirmation_pending",
        "CONFIRM_" + "IDEA_INTAKE",
        "--confirm-" + "intake",
        "qros-" + "idea" + "-intake-author",
        "idea" + "_intake",
        "Idea " + "Intake",
        "00_" + "mandate",
        "00 " + "mandate",
    ]
    offenders: list[str] = []

    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        matches = [token for token in stale_tokens if token in text]
        if matches:
            offenders.append(f"{path}: {', '.join(matches)}")

    assert not offenders, "Stale first-stage terms remain in active docs/skills:\n" + "\n".join(offenders)
