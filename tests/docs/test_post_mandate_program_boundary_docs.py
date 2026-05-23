from pathlib import Path


def test_qros_research_session_usage_explains_codex_authored_stage_program_boundary() -> None:
    content = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")

    assert "Codex" in content
    assert "显式生成或刷新" in content
    assert "lineage-local stage program" in content
    assert "program_hash" in content
    assert "整个 `program_dir`" in content
    assert "preflight" in content
    assert "`mandate_review_confirmation_pending`" in content
    assert "mandate-first / mandate-only" in content
    assert "artifact contract validation" in content
    assert "mandate semantic validation" in content
    assert "optional hygiene check" in content
    assert "继续覆盖所有 post-mandate `*_review_confirmation_pending`" not in content
    assert "当前 runtime 只在 `mandate_review_confirmation_pending` 强制跑 deterministic review-entry preflight" in content


def test_research_workflow_sop_tracks_post_mandate_program_boundary() -> None:
    content = Path("docs/sop/main-flow/research_workflow_sop.md").read_text(encoding="utf-8")

    assert "Codex" in content
    assert "lineage-local stage program" in content
    assert "thin wrapper" in content
    assert "program/common/" in content


def test_review_shared_protocol_requires_preflight_to_block_fake_programs_and_artifacts() -> None:
    content = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")

    assert "preflight" in content
    assert "thin wrapper" in content
    assert "placeholder" in content
    assert "fake" in content
    assert "reviewer lane" in content
    assert "artifact contract validation" in content
    assert "mandate semantic validation" in content


def test_qros_verification_tiers_marks_stage_program_boundary_change_as_full_smoke() -> None:
    content = Path("docs/guides/qros-verification-tiers.md").read_text(encoding="utf-8")

    assert "stage-program authoring contract" in content
    assert "full-smoke" in content


def test_qros_authoring_language_discipline_carries_shared_comment_rule() -> None:
    content = Path("docs/guides/qros-authoring-language-discipline.md").read_text(encoding="utf-8")

    assert "关键步骤" in content
    assert "中文注释" in content
    assert "run_stage.py" in content
    assert "关键 helper" in content


def test_qros_research_session_skill_removes_post_mandate_auto_materialize_path() -> None:
    content = Path("skills/core/qros-research-session/SKILL.md").read_text(encoding="utf-8")

    assert "auto-materialize the first-pass runnable program and continue" not in content
    assert "explicitly author or refresh the lineage-local stage program" in content
    assert "no silent auto-materialize path" in content
    assert "`mandate_review_confirmation_pending`" in content
    assert "mandate-first / mandate-only" in content
    assert "mandatory reviewer-lane gate" in content
    assert "artifact contract validation" in content
    assert "mandate semantic validation" in content
    assert "如需要 deterministic 预检" not in content
    assert "继续向所有 post-mandate `*_review_confirmation_pending` 扩展" not in content
