from pathlib import Path

import pytest

from tools.review_skillgen.review_findings import load_review_findings


def test_load_review_findings_normalizes_defaults(tmp_path: Path) -> None:
    findings_path = tmp_path / "review_findings.yaml"
    findings_path.write_text("reviewer_identity: codex\nrecommended_verdict: PASS\n", encoding="utf-8")

    findings = load_review_findings(findings_path)

    assert findings["reviewer_identity"] == "codex"
    assert findings["recommended_verdict"] == "PASS"
    assert findings["blocking_findings"] == []
    assert findings["reservation_findings"] == []
    assert findings["info_findings"] == []
    assert findings["residual_risks"] == []
    assert findings["allowed_modifications"] == []
    assert findings["downstream_permissions"] == []


def test_load_review_findings_rejects_unsupported_verdict(tmp_path: Path) -> None:
    findings_path = tmp_path / "review_findings.yaml"
    findings_path.write_text("recommended_verdict: MAYBE\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported verdict"):
        load_review_findings(findings_path)


def test_load_review_findings_requires_mapping(tmp_path: Path) -> None:
    findings_path = tmp_path / "review_findings.yaml"
    findings_path.write_text("- nope\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must load to a mapping"):
        load_review_findings(findings_path)
