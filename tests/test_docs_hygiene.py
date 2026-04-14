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
    *sorted(Path("docs/governance").glob("*.md")),
    *sorted(Path("docs/main-flow-sop").glob("*.md")),
    *sorted(Path("docs/review-sop").glob("*.md")),
)


def test_live_docs_do_not_reference_legacy_doc_layout() -> None:
    offenders: list[str] = []

    for path in LIVE_DOC_FILES:
        text = path.read_text(encoding="utf-8")
        matches = [token for token in LEGACY_DOC_TOKENS if token in text]
        if matches:
            offenders.append(f"{path}: {', '.join(matches)}")

    assert not offenders, "Legacy doc-layout references remain in live docs:\n" + "\n".join(offenders)


def test_docs_index_exists_and_points_to_current_truth_layers() -> None:
    content = Path("docs/README.md").read_text(encoding="utf-8")

    assert "contracts/stages/workflow_stage_gates.yaml" in content
    assert "contracts/review/review_checklist_master.yaml" in content
    assert "contracts/governance/review_governance_policy.yaml" in content
    assert "docs/plans/" in content
    assert "不是当前运行时真值" in content
