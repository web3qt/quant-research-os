from pathlib import Path

import yaml

from runtime.tools import review_session_runtime
from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff
from tests.helpers.skill_test_utils import skill_path
from tests.review.test_start_review_session import _prepare_mandate_stage


def test_research_session_skill_exists_and_covers_first_wave_flow() -> None:
    skill_file = skill_path("qros-research-session")
    content = skill_file.read_text(encoding="utf-8")

    assert skill_file.exists()
    assert "mandate_admission" in content
    assert "mandate_freeze_confirmation_pending" in content
    assert "mandate" in content
    assert "mandate review" in content.lower()
    assert "mandate_freeze_confirmation_pending" in content
    assert "CONFIRM_MANDATE" in content
    assert "是否确认进入 mandate" in content
    assert "observation" in content
    assert "counter-hypothesis" in content or "counter_hypothesis" in content
    assert "kill criteria" in content
    assert "ACCEPT_FOR_MANDATE" in content
    assert "data source" in content.lower() or "数据来源" in content
    assert "bar_size" in content or "1m" in content
    assert "research_intent" in content
    assert "scope_contract" in content
    assert "data_contract" in content
    assert "execution_contract" in content
    assert "data_ready_confirmation_pending" in content
    assert "extraction_contract" in content
    assert "shared_derived_layer" in content
    assert "是否按以上内容冻结 data_ready" in content
    assert "signal_ready_confirmation_pending" in content
    assert "signal_expression" in content
    assert "param_identity" in content
    assert "是否按以上内容冻结 signal_ready" in content
    assert "train_freeze_confirmation_pending" in content
    assert "window_contract" in content
    assert "threshold_contract" in content
    assert "quality_filters" in content
    assert "param_governance" in content
    assert "是否按以上内容冻结 train_freeze" in content
    assert "test_evidence_confirmation_pending" in content
    assert "formal_gate_contract" in content
    assert "admissibility_contract" in content
    assert "audit_contract" in content
    assert "是否按以上内容冻结 test_evidence" in content
    assert "backtest_ready_confirmation_pending" in content
    assert "execution_policy" in content
    assert "portfolio_policy" in content
    assert "risk_overlay" in content
    assert "engine_contract" in content
    assert "是否按以上内容冻结 backtest_ready" in content
    assert "holdout_validation_confirmation_pending" in content
    assert "reuse_contract" in content
    assert "drift_audit" in content
    assert "failure_governance" in content
    assert "是否按以上内容冻结 holdout_validation" in content
    assert "governance/pending_decisions" not in content
    assert "GOVERNANCE_DECISION_RECORD_REQUIRED" not in content
    assert "docs/guides/qros-authoring-language-discipline.md" in content
    assert "独立 reviewer 子代理" in content
    assert "spawn_agent" in content
    assert "./.qros/bin/qros-review-cycle prepare" in content
    assert "不得自己撰写 `review/final_review.yaml`" in content
    assert "./.qros/bin/qros-review" in content
    assert "Main-Agent Review Loop" in content
    assert "review-ready" in content
    assert "review/final_review.yaml" in content
    assert "launcher_review_ready_status" in content
    assert "./.qros/bin/qros-session" in content
    assert "./.qros/bin/qros-session <lineage_id> --continue" not in content
    assert "runtime status 报告当前需要 author、review、failure handling 或 next-stage confirmation" in content
    assert "stage-specific author/review skill 默认只作为高级/debug/manual recovery 入口" in content
    assert "CONFIRM_REVIEW" in content
    assert "freeze_groups" in content
    assert "--confirm-all-freeze-groups" in content
    assert "freeze_digest_sha256" in content
    assert "empty scaffold" in content
    assert "确认全部" in content
    assert "每组回显当前 freeze draft，并单独确认" not in content


def test_research_session_usage_doc_mentions_single_entry_flow() -> None:
    usage_path = Path("docs/guides/qros-research-session-usage.md")
    content = usage_path.read_text(encoding="utf-8")

    assert usage_path.exists()
    assert "./.qros/bin/qros-session" in content
    assert "qros-research-session" in content
    assert "data_ready" in content
    assert "mandate_freeze_confirmation_pending" in content
    assert "mandate_admission" in content
    assert "用户不需要记住内部命令" in content
    assert "reviewer 子代理" in content
    assert "spawn_agent" in content
    assert "qros-mandate-review" in content or "qros-*-review" in content
    assert "qros-session <lineage_id> --continue" not in content
    assert "继续 `$qros-research-session`" in content
    assert "自动识别当前 stage" in content
    assert "高级/debug/manual recovery" in content
    assert "CONFIRM_REVIEW" in content
    assert "awaiting_author_fix" in content
    assert "./.qros/bin/qros-review" in content
    assert "./.qros/bin/qros-review-cycle prepare" in content
    assert "review-ready" in content
    assert "review/result/review_findings.yaml" in content
    assert "launcher_review_ready_status" in content
    assert "review/review_cycle_trace.jsonl" in content
    assert "route_inheritance_contract.yaml" in content
    assert "admission" in content.lower()
    assert "kill criteria" in content
    assert "第一道用户确认是 mandate freeze approval" in content
    assert "--confirm-all-freeze-groups" in content
    assert "freeze_digest_sha256" in content
    assert "missing_items" in content
    assert "确认全部" in content
    assert "不会替代最终 stage approval" in content
    assert "是否确认进入 mandate" in content
    assert "数据来源" in content
    assert "1m" in content or "5m" in content or "15m" in content
    assert "research_intent" in content
    assert "scope_contract" in content
    assert "tss_data_ready_confirmation_pending" in content
    assert "shared_derived_layer" in content
    assert "是否按以上内容冻结 tss_data_ready" in content
    assert "tss_signal_ready_confirmation_pending" in content
    assert "signal_expression" in content
    assert "是否按以上内容冻结 tss_signal_ready" in content
    assert "tss_train_freeze_confirmation_pending" in content
    assert "window_contract" in content
    assert "是否按以上内容冻结 tss_train_freeze" in content
    assert "tss_test_evidence_confirmation_pending" in content
    assert "formal_gate_contract" in content
    assert "是否按以上内容冻结 tss_test_evidence" in content
    assert "tss_backtest_ready_confirmation_pending" in content
    assert "execution_policy" in content
    assert "是否按以上内容冻结 tss_backtest_ready" in content
    assert "tss_holdout_validation_confirmation_pending" in content
    assert "reuse_contract" in content
    assert "是否按以上内容冻结 tss_holdout_validation" in content


def test_review_handoff_instructs_reviewer_to_write_final_review_yaml(monkeypatch) -> None:
    content = Path("docs/guides/qros-review-shared-protocol.md").read_text(encoding="utf-8")
    skill_content = Path("skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md").read_text(
        encoding="utf-8"
    )
    payload = {
        "lineage_id": "lineage_a",
        "stage": "csf_data_ready",
        "stage_dir": "/tmp/repo/outputs/lineage_a/02_csf_data_ready",
        "lineage_root": "/tmp/repo/outputs/lineage_a",
        "review_cycle_id": "cycle-123",
        "request_payload": {
            "project_root": "/tmp/repo",
            "lineage_root": "/tmp/repo/outputs/lineage_a",
            "stage_dir": "/tmp/repo/outputs/lineage_a/02_csf_data_ready",
        },
        "receipt_payload": {
            "launcher_session_id": "launcher-session",
            "launcher_thread_id": "launcher-thread",
            "reviewer_agent_id": "reviewer-agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "execution_mode": "spawned_agent",
            "reviewer_invocation_kind": "codex_spawn_agent",
            "context_isolation_policy": "fork_context_false",
            "handoff_delivery_method": "send_input",
        },
    }

    monkeypatch.setattr(review_session_runtime, "start_review_cycle", lambda **_: payload)
    handoff = review_session_runtime.prepare_review_cycle_for_handoff(
        cwd=Path("/tmp/repo"),
        explicit_context={
            "stage_dir": Path(payload["stage_dir"]),
            "lineage_root": Path(payload["lineage_root"]),
        },
        reviewer_identity="qros-csf-data-ready-reviewer",
        reviewer_session_id="reviewer-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-agent",
    )
    handoff_prompt = handoff["reviewer_handoff_prompt"]

    assert "review/final_review.yaml" in content
    assert "review/result/reviewer_findings.raw.yaml" not in content
    assert "./.qros/bin/qros-review" not in content
    assert "active `reviewer_receipt.yaml` 必须绑定" in content

    assert "review/final_review.yaml" in skill_content

    assert "closer_command" not in handoff
    assert "review/final_review.yaml" in handoff_prompt
    assert "Do not run qros-review or any closer step." in handoff_prompt
    assert "reviewer_findings.raw.yaml" not in handoff_prompt
    assert "reviewed_artifact_paths: [<relative paths under author/formal>]" in handoff_prompt
    assert "The QROS governance repo is not the active research repo unless the canonical paths in this handoff point there." in handoff_prompt


def test_review_handoff_lists_exact_expected_final_review_bindings(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    payload = prepare_review_cycle_for_handoff(
        cwd=tmp_path,
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="launcher-session-1",
        launcher_thread_id="launcher-thread-1",
        reviewer_agent_id="reviewer-child-1",
        host="codex",
    )

    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    prompt = payload["reviewer_handoff_prompt"]

    assert "Do not infer review truth from prior chat" in prompt
    assert f"reviewed_artifact_digest: {request_payload['bound_author_materialization_digest']}" in prompt
    assert f"reviewed_program_digest: {request_payload['author_program_hash']}" in prompt
    assert "review/request/stage_contract_context.yaml" in prompt
    assert "review/request/stage_contract_context.md" in prompt
    assert "review/final_review.yaml" in prompt
    assert "- outputs/topic_a/01_mandate/review/final_review.yaml" in prompt.splitlines()
    assert "- 01_mandate/review/final_review.yaml" not in prompt.splitlines()
    assert "review/result/adversarial_review_result.yaml" not in prompt


def test_session_skill_documents_stage_author_context_as_author_truth_entrypoint() -> None:
    content = Path("skills/core/qros-research-session/SKILL.md").read_text(encoding="utf-8")

    assert "stage_author_context.yaml" in content
    assert "stage_author_context.md" in content
    assert "current-stage author truth entrypoint" in content
    assert "Use the CSF-specific grouped confirmations and ask for these frozen contract groups in order:" not in content
    assert "Use the TSS-specific grouped confirmations and ask for these frozen contract groups in order:" not in content


def test_author_skills_allow_bulk_freeze_group_confirmation() -> None:
    for skill_name in [
        "qros-mandate-author",
        "qros-data-ready-author",
        "qros-csf-data-ready-author",
        "qros-signal-ready-author",
        "qros-csf-signal-ready-author",
        "qros-train-freeze-author",
        "qros-csf-train-freeze-author",
        "qros-test-evidence-author",
        "qros-csf-test-evidence-author",
        "qros-backtest-ready-author",
        "qros-csf-backtest-ready-author",
        "qros-holdout-validation-author",
        "qros-csf-holdout-validation-author",
    ]:
        content = skill_path(skill_name).read_text(encoding="utf-8")

        assert "一次展示全部 groups" in content
        assert "确认全部" in content
        assert "每一组都要先回显 freeze draft，再确认该组" not in content


def test_data_ready_author_skill_exists() -> None:
    skill_file = skill_path("qros-data-ready-author")
    content = skill_file.read_text(encoding="utf-8")

    assert skill_file.exists()
    assert "data_ready" in content.lower()
    assert "extraction_contract" in content
    assert "quality_semantics" in content
    assert "universe_admission" in content
    assert "shared_derived_layer" in content
    assert "delivery_contract" in content


def test_research_session_mandate_admission_requires_interview() -> None:
    skill_file = skill_path("qros-research-session")
    content = skill_file.read_text(encoding="utf-8")

    assert skill_file.exists()
    assert "mandate_admission" in content
    assert "observation" in content
    assert "counter-hypothesis" in content or "counter_hypothesis" in content
    assert "kill criteria" in content
    assert "Do not treat the user's first raw-idea sentence as if all of these were already confirmed" in content


def test_signal_ready_author_skill_exists() -> None:
    skill_file = skill_path("qros-signal-ready-author")
    content = skill_file.read_text(encoding="utf-8")

    assert skill_file.exists()
    assert "signal_ready" in content.lower()
    assert "signal_expression" in content
    assert "param_identity" in content
    assert "time_semantics" in content
    assert "signal_schema" in content
    assert "delivery_contract" in content


def test_train_freeze_author_skill_exists() -> None:
    skill_file = skill_path("qros-train-freeze-author")
    content = skill_file.read_text(encoding="utf-8")

    assert skill_file.exists()
    assert "train_freeze" in content.lower()
    assert "window_contract" in content
    assert "threshold_contract" in content
    assert "quality_filters" in content
    assert "param_governance" in content
    assert "delivery_contract" in content


def test_test_evidence_author_skill_exists() -> None:
    skill_file = skill_path("qros-test-evidence-author")
    content = skill_file.read_text(encoding="utf-8")

    assert skill_file.exists()
    assert "test_evidence" in content.lower()
    assert "window_contract" in content
    assert "formal_gate_contract" in content
    assert "admissibility_contract" in content
    assert "audit_contract" in content
    assert "delivery_contract" in content


def test_backtest_ready_author_skill_exists() -> None:
    skill_file = skill_path("qros-backtest-ready-author")
    content = skill_file.read_text(encoding="utf-8")

    assert skill_file.exists()
    assert "backtest_ready" in content.lower()
    assert "execution_policy" in content
    assert "portfolio_policy" in content
    assert "risk_overlay" in content
    assert "engine_contract" in content
    assert "delivery_contract" in content


def test_holdout_validation_author_skill_exists() -> None:
    skill_file = skill_path("qros-holdout-validation-author")
    content = skill_file.read_text(encoding="utf-8")

    assert skill_file.exists()
    assert "holdout_validation" in content.lower()
    assert "window_contract" in content
    assert "reuse_contract" in content
    assert "drift_audit" in content
    assert "failure_governance" in content
    assert "delivery_contract" in content
