from __future__ import annotations

from pathlib import Path
import tomllib


def test_project_version_is_0600_in_pyproject_and_uv_lock() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    uv_lock = Path("uv.lock").read_text(encoding="utf-8")

    assert pyproject["project"]["version"] == "0.6.0"
    assert 'name = "quant-research-os"' in uv_lock
    assert 'version = "0.6.0"' in uv_lock


def test_release_notes_cover_all_public_versions() -> None:
    notes = Path("RELEASE_NOTES.md").read_text(encoding="utf-8")

    for version in ["0.6.0", "0.5.0", "0.4.11", "0.4.10", "0.4.9", "0.4.8", "0.4.7", "0.4.6", "0.4.5", "0.4.4", "0.4.3", "0.4.2", "0.4.1", "0.4.0", "0.3.0", "0.2.0", "0.1.0"]:
        assert f"## {version}" in notes

    assert "qros-check-stage-entry" in notes
    assert "time_series_signal" in notes
    assert "qros-signal-diagnostics" in notes
    assert "tss_data_ready" in notes
    assert "qros-factor-diagnostics" in notes
    assert "中文解释" in notes
    assert "Rank IC" in notes
    assert "uv.lock" in notes
    assert "Codex 和 Claude Code 的统一用户更新入口" in notes
    assert "Python 3.12" in notes
    assert "repo-local runtime" in notes
    assert "稳定 tag 发布路径" in notes
