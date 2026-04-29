from pathlib import Path

from runtime.tools.review_skillgen.review_engine import _check_global_evidence


def test_global_evidence_accepts_route_specific_run_manifest(tmp_path: Path) -> None:
    author_formal_dir = tmp_path / "author" / "formal"
    author_formal_dir.mkdir(parents=True)
    (author_formal_dir / "artifact_catalog.md").write_text("catalog\n", encoding="utf-8")
    (author_formal_dir / "field_dictionary.md").write_text("fields\n", encoding="utf-8")
    (author_formal_dir / "tss_holdout_run_manifest.json").write_text("{}\n", encoding="utf-8")

    findings = _check_global_evidence(author_formal_dir, {})

    assert findings == []
