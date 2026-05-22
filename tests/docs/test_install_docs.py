from pathlib import Path


def test_install_docs_reference_supported_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    installation = Path("docs/guides/installation.md").read_text(encoding="utf-8")
    quickstart = Path("docs/guides/quickstart-codex.md").read_text(encoding="utf-8")
    session_usage = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    codex_guide = Path("docs/README.codex.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, installation, quickstart, session_usage, codex_guide])

    assert "./.qros" in combined
    assert "~/.codex/skills" in combined
    assert "pipx install qros" not in combined
    assert "uv tool install qros" not in combined
    assert "Manual Installation" not in combined
    assert "Manual fallback" not in combined
    assert "手动安装" not in combined
    assert "qros-research-session" in combined
    assert "qros-research-session help" in combined
    assert "qros-progress" in combined
    assert "direct skill handoff" in combined
    assert "开始或继续一条研究线" in combined
    assert "查看当前研究进度" in combined
    assert "查看 QROS 使用帮助" in combined
    assert "更新 QROS 到最新稳定版本" in combined
    assert "./.qros/bin/qros-progress" in combined
    assert "./.qros/bin/qros-resume" in combined
    assert "qros-update" in combined
    assert "./.qros/bin/qros-session" in combined
    assert "./.qros/bin/qros-review-cycle" in combined
    assert "./.qros/bin/qros-review" in combined
    assert "./.qros/bin/qros-verify" in combined
    assert "setup --check" in combined
    assert "source_git_commit drift" in combined
    assert "Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md" in combined
    assert "Restart Codex" in combined
    assert "卸载" in combined


def test_install_docs_describe_research_repo_first_fetch_flow() -> None:
    install_doc = Path(".codex/INSTALL.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("docs/guides/quickstart-codex.md").read_text(encoding="utf-8")
    installation = Path("docs/guides/installation.md").read_text(encoding="utf-8")
    update_skill = Path("skills/core/qros-update/SKILL.md").read_text(encoding="utf-8")

    combined = "\n".join([install_doc, readme, quickstart, installation, update_skill])

    assert "active research repo" in combined
    assert "Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md" in combined
    assert "Restart Codex" in combined
    assert "qros-research-session" in combined
    assert "qros-update" in combined
    assert "current repo's `./.qros/`" in update_skill
    assert "For ordinary users, the update command is always" in update_skill
    assert "--host codex` and `--host claude-code` are manual recovery/debug overrides" in update_skill


def test_install_docs_describe_stable_default_and_main_developer_path() -> None:
    combined = "\n".join(
        [
            Path(".codex/INSTALL.md").read_text(encoding="utf-8"),
            Path(".claude/INSTALL.md").read_text(encoding="utf-8"),
            Path("docs/guides/installation.md").read_text(encoding="utf-8"),
            Path("docs/README.codex.md").read_text(encoding="utf-8"),
            Path("skills/core/qros-update/SKILL.md").read_text(encoding="utf-8"),
        ]
    )

    assert "latest stable" in combined or "最新稳定版本" in combined
    assert "qros-update main" in combined


def test_install_docs_describe_uv_python312_repo_local_runtime() -> None:
    installation = Path("docs/guides/installation.md").read_text(encoding="utf-8")

    assert "./.qros/.venv/bin/python" in installation
    assert "Python 3.12" in installation
    assert "./.qros/uv.lock" in installation
    assert "runtime_lock_digest" in installation
    assert ".qros.install.lock" in installation
    assert ".qros.tmp-*" in installation
    assert "自动清理这些陈旧 staging 目录" in installation
    assert "do not install dependencies as a side effect" in installation
    assert "QROS_PYTHON" in installation
    assert "uv python find 3.12" in installation


def test_codex_readme_describes_python312_wrapper_runtime() -> None:
    codex_guide = Path("docs/README.codex.md").read_text(encoding="utf-8")

    assert "QROS repo-local commands require Python 3.12" in codex_guide
    assert "`qros-update`" in codex_guide
    assert "`uv` 创建或刷新 `./.qros/.venv`" in codex_guide
    assert "不要为了绕过 Python 版本问题而跳过 `./.qros/bin/qros-*` wrapper" in codex_guide
    assert "直接调用 `runtime/scripts/*`" in codex_guide


def test_install_docs_reference_stage_field_guide() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("docs/guides/quickstart-codex.md").read_text(encoding="utf-8")
    session_usage = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    guide = Path("docs/guides/stage-freeze-group-field-guide.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, quickstart, session_usage])

    assert "stage-freeze-group-field-guide.md" in combined
    assert "qros-verification-tiers.md" in combined
    assert "research_intent" in guide
    assert "scope_contract" in guide
    assert "delivery_contract" in guide
    assert "| 字段 | 含义 | 为什么需要 | 不该怎么填 |" in guide
    assert "为什么需要" in guide
    assert "不该怎么填" in guide
    assert "param_identity" in guide
    assert "reuse_contract" in guide
    assert "best_h" in guide
    assert "selected_symbols" in guide
    assert "panel_primary_key" in guide
    assert "factor_id" in guide
    assert "search_governance_contract" in guide
    assert "portfolio_contract" in guide
    assert "stability_contract" in guide
    assert "data_viability_contract" in guide
    assert "time_coverage_contract" in guide
    assert "route_viability_contract" in guide
    assert "expression_identity_contract" in guide
    assert "provenance_viability_contract" in guide
    assert "reviewer 不是这些基础事实的第一发现点" in guide


def test_stage_author_skills_lock_preflight_and_reviewer_not_first_discovery_wording() -> None:
    mandate_author = Path("skills/mandate/qros-mandate-author/SKILL.md").read_text(encoding="utf-8")
    data_ready_author = Path("skills/data_ready/qros-data-ready-author/SKILL.md").read_text(
        encoding="utf-8"
    )
    csf_data_ready_author = Path("skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "作为 mandate freeze 前的 preflight 事实先锁定" in mandate_author
    assert "reviewer 不是这些基础事实的第一发现点" in mandate_author

    assert "作为进入 reviewer 之前的 preflight 事实先锁定" in data_ready_author
    assert "reviewer 不是第一次发现" in data_ready_author
    assert "这批数据是否真实可用、覆盖到哪、来自哪里" in data_ready_author

    assert "作为进入 reviewer 之前的 preflight 事实先锁定" in csf_data_ready_author
    assert "reviewer 不是第一次发现" in csf_data_ready_author
    assert "这包是否还服务 CSF 路线、面板身份是否漂移、输入来源是否真实" in csf_data_ready_author
    assert "deterministic preflight" in csf_data_ready_author


def test_claude_code_bootstrap_docs_present() -> None:
    installation = Path("docs/guides/installation.md").read_text(encoding="utf-8")

    assert "Claude Code repo bootstrap" in installation
    assert "--host claude-code --mode repo-local" in installation
    assert "~/.claude/skills" in installation
    assert "~/.claude/qros/install-manifest.json" in installation
    assert 'qros-update` 默认会自动识别当前 host' in installation
    assert 'qros-update --cwd "$PWD"' in installation
    assert "`--host claude-code` 只作为 manual recovery/debug override" in installation
    assert "普通路径也是在 active research repo 根目录直接输入" in installation
    assert "host = claude-code" in installation
    assert "## Claude Code" in installation
    assert ".claude-plugin/agents/qros-reviewer.md" in installation
    # Codex paths still present
    assert "~/.codex/skills" in installation
    assert "Restart Codex" in installation


def test_review_protocol_documents_fail_closed_boundaries() -> None:
    protocol = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")
    csf_review_skill = Path("skills/csf_test_evidence/qros-csf-test-evidence-review/SKILL.md").read_text(
        encoding="utf-8"
    )
    combined = protocol + "\n" + csf_review_skill

    assert "REVIEWER_IDENTITY_COLLISION" in protocol
    assert "REVIEW_CONTEXT_ROOT_MISMATCH" in protocol
    assert "HARD_GATE_DOWNGRADED" in protocol
    assert "REVIEW_RESULT_PROJECTION_DRIFT" in protocol
    assert "review/final_review.yaml" in combined
    assert "reviewer_findings.raw.yaml" not in combined
    assert "reviewed_artifact_paths" in combined
    assert "reviewed_program_path" in combined
    assert "reviewed_artifact_digest" in combined
    assert "reviewed_program_digest" in combined
    assert "recommended_next_action" in combined
    assert "stage_contract_context.yaml" in csf_review_skill
    assert "stage_contract_context.md" in csf_review_skill


def test_qros_research_session_usage_documents_stage_author_context() -> None:
    content = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    assert "stage_author_context.yaml" in content
    assert "stage_author_context.md" in content
    assert "author truth entrypoint" in content
    assert "author orchestration" in content
