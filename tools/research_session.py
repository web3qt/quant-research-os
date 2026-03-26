from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml

from tools.data_ready_runtime import (
    DATA_READY_FREEZE_DRAFT_FILE,
    DATA_READY_FREEZE_GROUP_ORDER,
    build_data_ready_from_mandate,
    scaffold_data_ready,
)
from tools.idea_runtime import (
    MANDATE_FREEZE_DRAFT_FILE,
    MANDATE_FREEZE_GROUP_ORDER,
    build_mandate_from_intake,
    scaffold_idea_intake,
)
from tools.review_skillgen.review_engine import run_stage_review
from tools.signal_ready_runtime import (
    SIGNAL_READY_FREEZE_DRAFT_FILE,
    SIGNAL_READY_FREEZE_GROUP_ORDER,
    build_signal_ready_from_data_ready,
    scaffold_signal_ready,
)
from tools.backtest_runtime import (
    BACKTEST_READY_DRAFT_FILE,
    BACKTEST_READY_GROUP_ORDER,
    build_backtest_ready_from_test_evidence,
    scaffold_backtest_ready,
)
from tools.holdout_runtime import (
    HOLDOUT_VALIDATION_DRAFT_FILE,
    HOLDOUT_VALIDATION_GROUP_ORDER,
    build_holdout_validation_from_backtest,
    scaffold_holdout_validation,
)
from tools.test_evidence_runtime import (
    TEST_EVIDENCE_DRAFT_FILE,
    TEST_EVIDENCE_GROUP_ORDER,
    build_test_evidence_from_train_freeze,
    scaffold_test_evidence,
)
from tools.train_runtime import (
    TRAIN_FREEZE_DRAFT_FILE,
    TRAIN_FREEZE_GROUP_ORDER,
    build_train_freeze_from_signal_ready,
    scaffold_train_freeze,
)


SessionStage = Literal[
    "idea_intake",
    "idea_intake_confirmation_pending",
    "mandate_confirmation_pending",
    "mandate_author",
    "mandate_review",
    "data_ready_confirmation_pending",
    "data_ready_author",
    "data_ready_review",
    "signal_ready_confirmation_pending",
    "signal_ready_author",
    "signal_ready_review",
    "train_freeze_confirmation_pending",
    "train_freeze_author",
    "train_freeze_review",
    "test_evidence_confirmation_pending",
    "test_evidence_author",
    "test_evidence_review",
    "backtest_ready_confirmation_pending",
    "backtest_ready_author",
    "backtest_ready_review",
    "holdout_validation_confirmation_pending",
    "holdout_validation_author",
    "holdout_validation_review",
    "holdout_validation_review_complete",
]
IdeaIntakeTransitionDecision = Literal["CONFIRM_IDEA_INTAKE", "HOLD", "REFRAME"]
MandateTransitionDecision = Literal["CONFIRM_MANDATE", "HOLD", "REFRAME"]
DataReadyTransitionDecision = Literal["CONFIRM_DATA_READY", "HOLD", "REFRAME"]
SignalReadyTransitionDecision = Literal["CONFIRM_SIGNAL_READY", "HOLD", "REFRAME"]
TrainFreezeTransitionDecision = Literal["CONFIRM_TRAIN_FREEZE", "HOLD", "REFRAME"]
TestEvidenceTransitionDecision = Literal["CONFIRM_TEST_EVIDENCE", "HOLD", "REFRAME"]
BacktestReadyTransitionDecision = Literal["CONFIRM_BACKTEST_READY", "HOLD", "REFRAME"]
HoldoutValidationTransitionDecision = Literal["CONFIRM_HOLDOUT_VALIDATION", "HOLD", "REFRAME"]
MANDATE_REQUIRED_OUTPUTS = [
    "mandate.md",
    "research_scope.md",
    "time_split.json",
    "parameter_grid.yaml",
    "run_config.toml",
    "artifact_catalog.md",
    "field_dictionary.md",
]
MANDATE_CLOSURE_OUTPUTS = [
    "latest_review_pack.yaml",
    "stage_gate_review.yaml",
    "stage_completion_certificate.yaml",
]
DATA_READY_REQUIRED_OUTPUTS = [
    "aligned_bars",
    "rolling_stats",
    "pair_stats",
    "benchmark_residual",
    "topic_basket_state",
    "qc_report.parquet",
    "dataset_manifest.json",
    "validation_report.md",
    "data_contract.md",
    "dedupe_rule.md",
    "universe_summary.md",
    "universe_exclusions.csv",
    "universe_exclusions.md",
    "data_ready_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
SIGNAL_READY_REQUIRED_OUTPUTS = [
    "param_manifest.csv",
    "params",
    "signal_coverage.csv",
    "signal_coverage.md",
    "signal_coverage_summary.md",
    "signal_contract.md",
    "signal_fields_contract.md",
    "signal_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
TRAIN_FREEZE_REQUIRED_OUTPUTS = [
    "train_thresholds.json",
    "train_quality.parquet",
    "train_param_ledger.csv",
    "train_rejects.csv",
    "train_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
TEST_EVIDENCE_REQUIRED_OUTPUTS = [
    "report_by_h.parquet",
    "symbol_summary.parquet",
    "admissibility_report.parquet",
    "test_gate_table.csv",
    "crowding_review.md",
    "selected_symbols_test.csv",
    "selected_symbols_test.parquet",
    "frozen_spec.json",
    "test_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
BACKTEST_READY_REQUIRED_OUTPUTS = [
    "engine_compare.csv",
    "vectorbt",
    "backtrader",
    "strategy_combo_ledger.csv",
    "capacity_review.md",
    "backtest_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
HOLDOUT_VALIDATION_REQUIRED_OUTPUTS = [
    "holdout_run_manifest.json",
    "holdout_backtest_compare.csv",
    "window_results",
    "holdout_gate_decision.md",
    "artifact_catalog.md",
    "field_dictionary.md",
]
ADVANCING_COMPLETION_STATUSES = {"PASS", "CONDITIONAL PASS", "GO"}
NON_ADVANCING_COMPLETION_STATUSES = {"PASS FOR RETRY", "RETRY", "NO-GO", "CHILD LINEAGE"}
IDEA_INTAKE_TRANSITION_APPROVAL_FILE = "idea_intake_transition_approval.yaml"
MANDATE_TRANSITION_APPROVAL_FILE = "mandate_transition_approval.yaml"
DATA_READY_TRANSITION_APPROVAL_FILE = "data_ready_transition_approval.yaml"
SIGNAL_READY_TRANSITION_APPROVAL_FILE = "signal_ready_transition_approval.yaml"
TRAIN_FREEZE_TRANSITION_APPROVAL_FILE = "train_transition_approval.yaml"
TEST_EVIDENCE_TRANSITION_APPROVAL_FILE = "test_evidence_transition_approval.yaml"
BACKTEST_READY_TRANSITION_APPROVAL_FILE = "backtest_ready_transition_approval.yaml"
HOLDOUT_VALIDATION_TRANSITION_APPROVAL_FILE = "holdout_validation_transition_approval.yaml"


@dataclass(frozen=True)
class SessionContext:
    lineage_id: str
    lineage_root: Path
    current_stage: SessionStage
    artifacts_written: list[str]
    gate_status: str
    next_action: str
    why_now: list[str]
    open_risks: list[str]
    review_verdict: str | None = None
    requires_failure_handling: bool = False
    failure_stage: str | None = None
    failure_reason_summary: str | None = None


def slugify_idea(raw_idea: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", raw_idea.strip().lower())
    normalized = normalized.strip("_")
    if not normalized:
        raise ValueError("raw_idea must contain at least one alphanumeric character")
    return normalized


def resolve_lineage_root(outputs_root: Path, lineage_id: str | None, raw_idea: str | None) -> Path:
    if lineage_id:
        return outputs_root / lineage_id
    if raw_idea:
        return outputs_root / slugify_idea(raw_idea)
    raise ValueError("Either lineage_id or raw_idea must be provided")


def detect_session_stage(lineage_root: Path) -> SessionStage:
    intake_dir = lineage_root / "00_idea_intake"
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = lineage_root / "02_data_ready"
    signal_ready_dir = lineage_root / "03_signal_ready"
    train_dir = lineage_root / "04_train_freeze"
    test_evidence_dir = lineage_root / "05_test_evidence"
    backtest_dir = lineage_root / "06_backtest"
    holdout_dir = lineage_root / "07_holdout"

    if _holdout_validation_outputs_complete(holdout_dir):
        if _holdout_validation_closure_complete(holdout_dir):
            return "holdout_validation_review_complete"
        return "holdout_validation_review"

    if _backtest_ready_outputs_complete(backtest_dir):
        if not _backtest_ready_closure_complete(backtest_dir):
            return "backtest_ready_review"
        approval_decision = read_holdout_validation_transition_decision(lineage_root)
        if (
            approval_decision == "CONFIRM_HOLDOUT_VALIDATION"
            and next_holdout_validation_group(lineage_root) is None
        ):
            return "holdout_validation_author"
        return "holdout_validation_confirmation_pending"

    if _test_evidence_outputs_complete(test_evidence_dir):
        if not _test_evidence_closure_complete(test_evidence_dir):
            return "test_evidence_review"
        approval_decision = read_backtest_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_BACKTEST_READY" and next_backtest_ready_group(lineage_root) is None:
            return "backtest_ready_author"
        return "backtest_ready_confirmation_pending"

    if _train_freeze_outputs_complete(train_dir):
        if not _train_freeze_closure_complete(train_dir):
            return "train_freeze_review"
        approval_decision = read_test_evidence_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_TEST_EVIDENCE" and next_test_evidence_group(lineage_root) is None:
            return "test_evidence_author"
        return "test_evidence_confirmation_pending"

    if _signal_ready_outputs_complete(signal_ready_dir):
        if not _signal_ready_closure_complete(signal_ready_dir):
            return "signal_ready_review"
        approval_decision = read_train_freeze_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_TRAIN_FREEZE" and next_train_freeze_group(lineage_root) is None:
            return "train_freeze_author"
        return "train_freeze_confirmation_pending"

    if _data_ready_outputs_complete(data_ready_dir):
        if not _data_ready_closure_complete(data_ready_dir):
            return "data_ready_review"
        approval_decision = read_signal_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_SIGNAL_READY" and next_signal_ready_freeze_group(lineage_root) is None:
            return "signal_ready_author"
        return "signal_ready_confirmation_pending"

    if _mandate_outputs_complete(mandate_dir):
        if not _mandate_closure_complete(mandate_dir):
            return "mandate_review"
        approval_decision = read_data_ready_transition_decision(lineage_root)
        if approval_decision == "CONFIRM_DATA_READY" and next_data_ready_freeze_group(lineage_root) is None:
            return "data_ready_author"
        return "data_ready_confirmation_pending"

    if not intake_dir.exists():
        return "idea_intake"

    intake_approval = read_idea_intake_transition_decision(lineage_root)
    if intake_approval != "CONFIRM_IDEA_INTAKE":
        return "idea_intake_confirmation_pending"

    gate_path = intake_dir / "idea_gate_decision.yaml"
    if not gate_path.exists():
        return "idea_intake"

    gate_decision = _read_yaml(gate_path)
    if gate_decision.get("verdict") != "GO_TO_MANDATE":
        return "idea_intake"

    approval_decision = read_mandate_transition_decision(lineage_root)
    if approval_decision == "CONFIRM_MANDATE" and next_mandate_freeze_group(lineage_root) is None:
        return "mandate_author"
    if approval_decision == "REFRAME":
        return "idea_intake"

    return "mandate_confirmation_pending"


def ensure_intake_scaffold(lineage_root: Path) -> list[str]:
    intake_dir = lineage_root / "00_idea_intake"
    if intake_dir.exists():
        return []

    scaffold_idea_intake(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in intake_dir.iterdir())


def build_mandate_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "mandate_author":
        return []

    mandate_dir = build_mandate_from_intake(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in mandate_dir.iterdir())


def ensure_data_ready_scaffold(lineage_root: Path) -> list[str]:
    data_ready_dir = lineage_root / "02_data_ready"
    if data_ready_dir.exists() and (data_ready_dir / DATA_READY_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_data_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in data_ready_dir.iterdir())


def build_data_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "data_ready_author":
        return []

    data_ready_dir = build_data_ready_from_mandate(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in data_ready_dir.iterdir())


def ensure_signal_ready_scaffold(lineage_root: Path) -> list[str]:
    signal_ready_dir = lineage_root / "03_signal_ready"
    if signal_ready_dir.exists() and (signal_ready_dir / SIGNAL_READY_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_signal_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in signal_ready_dir.iterdir())


def build_signal_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "signal_ready_author":
        return []

    signal_ready_dir = build_signal_ready_from_data_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in signal_ready_dir.iterdir())


def ensure_train_freeze_scaffold(lineage_root: Path) -> list[str]:
    train_dir = lineage_root / "04_train_freeze"
    if train_dir.exists() and (train_dir / TRAIN_FREEZE_DRAFT_FILE).exists():
        return []

    scaffold_train_freeze(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in train_dir.iterdir())


def build_train_freeze_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "train_freeze_author":
        return []

    train_dir = build_train_freeze_from_signal_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in train_dir.iterdir())


def ensure_test_evidence_scaffold(lineage_root: Path) -> list[str]:
    test_dir = lineage_root / "05_test_evidence"
    if test_dir.exists() and (test_dir / TEST_EVIDENCE_DRAFT_FILE).exists():
        return []

    scaffold_test_evidence(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in test_dir.iterdir())


def build_test_evidence_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "test_evidence_author":
        return []

    test_dir = build_test_evidence_from_train_freeze(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in test_dir.iterdir())


def ensure_backtest_ready_scaffold(lineage_root: Path) -> list[str]:
    backtest_dir = lineage_root / "06_backtest"
    if backtest_dir.exists() and (backtest_dir / BACKTEST_READY_DRAFT_FILE).exists():
        return []

    scaffold_backtest_ready(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in backtest_dir.iterdir())


def build_backtest_ready_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "backtest_ready_author":
        return []

    backtest_dir = build_backtest_ready_from_test_evidence(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in backtest_dir.iterdir())


def ensure_holdout_validation_scaffold(lineage_root: Path) -> list[str]:
    holdout_dir = lineage_root / "07_holdout"
    if holdout_dir.exists() and (holdout_dir / HOLDOUT_VALIDATION_DRAFT_FILE).exists():
        return []

    scaffold_holdout_validation(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in holdout_dir.iterdir())


def build_holdout_validation_if_admitted(lineage_root: Path) -> list[str]:
    if detect_session_stage(lineage_root) != "holdout_validation_author":
        return []

    holdout_dir = build_holdout_validation_from_backtest(lineage_root)
    return sorted(str(path.relative_to(lineage_root)) for path in holdout_dir.iterdir())


def run_mandate_review_if_ready(lineage_root: Path) -> dict[str, object] | None:
    if detect_session_stage(lineage_root) != "mandate_review":
        return None

    mandate_dir = lineage_root / "01_mandate"
    if not (mandate_dir / "review_findings.yaml").exists():
        return None

    return run_stage_review(
        explicit_context={
            "lineage_id": lineage_root.name,
            "lineage_root": lineage_root,
            "stage": "mandate",
            "stage_dir": mandate_dir,
        }
    )


def write_mandate_transition_decision(
    lineage_root: Path,
    *,
    decision: MandateTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    gate_decision = _read_yaml(approval_path.parent / "idea_gate_decision.yaml")
    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_gate_verdict": gate_decision.get("verdict", ""),
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_idea_intake_transition_decision(
    lineage_root: Path,
    *,
    decision: IdeaIntakeTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _idea_intake_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "idea_intake_interview",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_data_ready_transition_decision(
    lineage_root: Path,
    *,
    decision: DataReadyTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _data_ready_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "mandate_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_signal_ready_transition_decision(
    lineage_root: Path,
    *,
    decision: SignalReadyTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _signal_ready_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "data_ready_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_train_freeze_transition_decision(
    lineage_root: Path,
    *,
    decision: TrainFreezeTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _train_freeze_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "signal_ready_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_test_evidence_transition_decision(
    lineage_root: Path,
    *,
    decision: TestEvidenceTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _test_evidence_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "train_freeze_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_backtest_ready_transition_decision(
    lineage_root: Path,
    *,
    decision: BacktestReadyTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _backtest_ready_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "test_evidence_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def write_holdout_validation_transition_decision(
    lineage_root: Path,
    *,
    decision: HoldoutValidationTransitionDecision,
    approved_by: str = "codex",
) -> str:
    approval_path = _holdout_validation_approval_path(lineage_root)
    approval_path.parent.mkdir(parents=True, exist_ok=True)

    approval_path.write_text(
        yaml.safe_dump(
            {
                "lineage_id": lineage_root.name,
                "decision": decision,
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "source_stage": "backtest_ready_review_complete",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(approval_path.relative_to(lineage_root))


def read_mandate_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_MANDATE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_idea_intake_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _idea_intake_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_IDEA_INTAKE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_data_ready_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _data_ready_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_DATA_READY", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_signal_ready_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _signal_ready_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_SIGNAL_READY", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_train_freeze_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _train_freeze_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_TRAIN_FREEZE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_test_evidence_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _test_evidence_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_TEST_EVIDENCE", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_backtest_ready_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _backtest_ready_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_BACKTEST_READY", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def read_holdout_validation_transition_decision(lineage_root: Path) -> str | None:
    approval_path = _holdout_validation_approval_path(lineage_root)
    if not approval_path.exists():
        return None

    decision = _read_yaml(approval_path).get("decision")
    if decision in {"CONFIRM_HOLDOUT_VALIDATION", "HOLD", "REFRAME"}:
        return str(decision)
    return None


def session_transition_summary(lineage_root: Path) -> tuple[list[str], list[str]]:
    gate_path = lineage_root / "00_idea_intake" / "idea_gate_decision.yaml"
    if not gate_path.exists():
        return [], []

    gate_decision = _read_yaml(gate_path)
    why_now = [str(item) for item in gate_decision.get("why", []) if item]
    open_risks = [str(item) for item in gate_decision.get("required_reframe_actions", []) if item]
    if not open_risks and gate_decision.get("rollback_target"):
        open_risks = [f"rollback_target remains {gate_decision['rollback_target']}"]
    return why_now, open_risks


def next_mandate_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "00_idea_intake" / MANDATE_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return MANDATE_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in MANDATE_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_data_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "02_data_ready" / DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return DATA_READY_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in DATA_READY_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_signal_ready_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "03_signal_ready" / SIGNAL_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return SIGNAL_READY_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in SIGNAL_READY_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_train_freeze_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "04_train_freeze" / TRAIN_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        return TRAIN_FREEZE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in TRAIN_FREEZE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_test_evidence_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "05_test_evidence" / TEST_EVIDENCE_DRAFT_FILE
    if not draft_path.exists():
        return TEST_EVIDENCE_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in TEST_EVIDENCE_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_backtest_ready_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "06_backtest" / BACKTEST_READY_DRAFT_FILE
    if not draft_path.exists():
        return BACKTEST_READY_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in BACKTEST_READY_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def next_holdout_validation_group(lineage_root: Path) -> str | None:
    draft_path = lineage_root / "07_holdout" / HOLDOUT_VALIDATION_DRAFT_FILE
    if not draft_path.exists():
        return HOLDOUT_VALIDATION_GROUP_ORDER[0]

    draft_payload = _read_yaml(draft_path)
    groups = draft_payload.get("groups", {})
    for name in HOLDOUT_VALIDATION_GROUP_ORDER:
        if not bool(groups.get(name, {}).get("confirmed")):
            return name
    return None


def summarize_session_status(
    *,
    lineage_id: str,
    lineage_root: Path,
    current_stage: SessionStage,
    artifacts_written: list[str],
    gate_status: str,
    next_action: str,
    why_now: list[str] | None = None,
    open_risks: list[str] | None = None,
    review_verdict: str | None = None,
    requires_failure_handling: bool = False,
    failure_stage: str | None = None,
    failure_reason_summary: str | None = None,
) -> SessionContext:
    return SessionContext(
        lineage_id=lineage_id,
        lineage_root=lineage_root,
        current_stage=current_stage,
        artifacts_written=artifacts_written,
        gate_status=gate_status,
        next_action=next_action,
        why_now=why_now or [],
        open_risks=open_risks or [],
        review_verdict=review_verdict,
        requires_failure_handling=requires_failure_handling,
        failure_stage=failure_stage,
        failure_reason_summary=failure_reason_summary,
    )


def run_research_session(
    *,
    outputs_root: Path,
    lineage_id: str | None = None,
    raw_idea: str | None = None,
    idea_intake_decision: IdeaIntakeTransitionDecision | None = None,
    mandate_decision: MandateTransitionDecision | None = None,
    data_ready_decision: DataReadyTransitionDecision | None = None,
    signal_ready_decision: SignalReadyTransitionDecision | None = None,
    train_freeze_decision: TrainFreezeTransitionDecision | None = None,
    test_evidence_decision: TestEvidenceTransitionDecision | None = None,
    backtest_ready_decision: BacktestReadyTransitionDecision | None = None,
    holdout_validation_decision: HoldoutValidationTransitionDecision | None = None,
) -> SessionContext:
    lineage_root = resolve_lineage_root(outputs_root, lineage_id=lineage_id, raw_idea=raw_idea)
    lineage_root.mkdir(parents=True, exist_ok=True)

    artifacts_written: list[str] = []
    if idea_intake_decision is not None:
        artifacts_written.append(
            write_idea_intake_transition_decision(lineage_root, decision=idea_intake_decision)
        )
    if mandate_decision is not None:
        artifacts_written.append(
            write_mandate_transition_decision(lineage_root, decision=mandate_decision)
        )
    if data_ready_decision is not None:
        artifacts_written.append(
            write_data_ready_transition_decision(lineage_root, decision=data_ready_decision)
        )
    if signal_ready_decision is not None:
        artifacts_written.append(
            write_signal_ready_transition_decision(lineage_root, decision=signal_ready_decision)
        )
    if train_freeze_decision is not None:
        artifacts_written.append(
            write_train_freeze_transition_decision(lineage_root, decision=train_freeze_decision)
        )
    if test_evidence_decision is not None:
        artifacts_written.append(
            write_test_evidence_transition_decision(lineage_root, decision=test_evidence_decision)
        )
    if backtest_ready_decision is not None:
        artifacts_written.append(
            write_backtest_ready_transition_decision(lineage_root, decision=backtest_ready_decision)
        )
    if holdout_validation_decision is not None:
        artifacts_written.append(
            write_holdout_validation_transition_decision(
                lineage_root, decision=holdout_validation_decision
            )
        )

    current_stage = detect_session_stage(lineage_root)

    if current_stage == "idea_intake":
        artifacts_written.extend(ensure_intake_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "mandate_author":
        artifacts_written.extend(build_mandate_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "data_ready_confirmation_pending":
        artifacts_written.extend(ensure_data_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "data_ready_author":
        artifacts_written.extend(build_data_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "signal_ready_confirmation_pending":
        artifacts_written.extend(ensure_signal_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "signal_ready_author":
        artifacts_written.extend(build_signal_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "train_freeze_confirmation_pending":
        artifacts_written.extend(ensure_train_freeze_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "train_freeze_author":
        artifacts_written.extend(build_train_freeze_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "test_evidence_confirmation_pending":
        artifacts_written.extend(ensure_test_evidence_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "test_evidence_author":
        artifacts_written.extend(build_test_evidence_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "backtest_ready_confirmation_pending":
        artifacts_written.extend(ensure_backtest_ready_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "backtest_ready_author":
        artifacts_written.extend(build_backtest_ready_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "holdout_validation_confirmation_pending":
        artifacts_written.extend(ensure_holdout_validation_scaffold(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    if current_stage == "holdout_validation_author":
        artifacts_written.extend(build_holdout_validation_if_admitted(lineage_root))
        current_stage = detect_session_stage(lineage_root)

    gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
    review_verdict, requires_failure_handling, failure_stage, failure_reason_summary = (
        _latest_review_failure_status(lineage_root)
    )
    if requires_failure_handling and failure_stage is not None:
        gate_status = "FAILURE_HANDLING_REQUIRED"
        next_action = f"Enter failure handling for {failure_stage} via qros-stage-failure-handler"
    why_now, open_risks = session_transition_summary(lineage_root)
    return summarize_session_status(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        current_stage=current_stage,
        artifacts_written=artifacts_written,
        gate_status=gate_status,
        next_action=next_action,
        why_now=why_now,
        open_risks=open_risks,
        review_verdict=review_verdict,
        requires_failure_handling=requires_failure_handling,
        failure_stage=failure_stage,
        failure_reason_summary=failure_reason_summary,
    )


def _mandate_outputs_complete(mandate_dir: Path) -> bool:
    return all((mandate_dir / name).exists() for name in MANDATE_REQUIRED_OUTPUTS)


def _data_ready_outputs_complete(data_ready_dir: Path) -> bool:
    return all((data_ready_dir / name).exists() for name in DATA_READY_REQUIRED_OUTPUTS)


def _signal_ready_outputs_complete(signal_ready_dir: Path) -> bool:
    return all((signal_ready_dir / name).exists() for name in SIGNAL_READY_REQUIRED_OUTPUTS)


def _train_freeze_outputs_complete(train_dir: Path) -> bool:
    return all((train_dir / name).exists() for name in TRAIN_FREEZE_REQUIRED_OUTPUTS)


def _test_evidence_outputs_complete(test_dir: Path) -> bool:
    return all((test_dir / name).exists() for name in TEST_EVIDENCE_REQUIRED_OUTPUTS)


def _backtest_ready_outputs_complete(backtest_dir: Path) -> bool:
    return all((backtest_dir / name).exists() for name in BACKTEST_READY_REQUIRED_OUTPUTS)


def _holdout_validation_outputs_complete(holdout_dir: Path) -> bool:
    return all((holdout_dir / name).exists() for name in HOLDOUT_VALIDATION_REQUIRED_OUTPUTS)


def _completion_certificate_allows_progress(stage_dir: Path) -> bool:
    payload = _read_yaml(stage_dir / "stage_completion_certificate.yaml")
    if not payload:
        return True

    stage_status = payload.get("stage_status") or payload.get("final_verdict")
    if stage_status in ADVANCING_COMPLETION_STATUSES:
        return True
    if stage_status in NON_ADVANCING_COMPLETION_STATUSES:
        return False
    return True


def _review_verdict_from_stage_dir(stage_dir: Path) -> str | None:
    certificate_path = stage_dir / "stage_completion_certificate.yaml"
    if not certificate_path.exists():
        return None

    payload = _read_yaml(certificate_path)
    if not payload:
        return None

    verdict = payload.get("stage_status") or payload.get("final_verdict")
    if isinstance(verdict, str) and verdict.strip():
        return verdict
    return None


def _latest_review_failure_status(
    lineage_root: Path,
) -> tuple[str | None, bool, str | None, str | None]:
    review_stage_dirs = [
        ("holdout_validation_review", lineage_root / "07_holdout"),
        ("backtest_ready_review", lineage_root / "06_backtest"),
        ("test_evidence_review", lineage_root / "05_test_evidence"),
        ("train_freeze_review", lineage_root / "04_train_freeze"),
        ("signal_ready_review", lineage_root / "03_signal_ready"),
        ("data_ready_review", lineage_root / "02_data_ready"),
        ("mandate_review", lineage_root / "01_mandate"),
    ]

    for review_stage, stage_dir in review_stage_dirs:
        verdict = _review_verdict_from_stage_dir(stage_dir)
        if verdict is None:
            continue
        if verdict in NON_ADVANCING_COMPLETION_STATUSES:
            return (
                verdict,
                True,
                review_stage,
                f"{review_stage} requires failure handling because review verdict is {verdict}.",
            )
        return verdict, False, None, None

    return None, False, None, None


def _mandate_closure_complete(mandate_dir: Path) -> bool:
    if (mandate_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(mandate_dir)
    return all((mandate_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _data_ready_closure_complete(data_ready_dir: Path) -> bool:
    if (data_ready_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(data_ready_dir)
    return all((data_ready_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _signal_ready_closure_complete(signal_ready_dir: Path) -> bool:
    if (signal_ready_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(signal_ready_dir)
    return all((signal_ready_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _train_freeze_closure_complete(train_dir: Path) -> bool:
    if (train_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(train_dir)
    return all((train_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _test_evidence_closure_complete(test_dir: Path) -> bool:
    if (test_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(test_dir)
    return all((test_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _backtest_ready_closure_complete(backtest_dir: Path) -> bool:
    if (backtest_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(backtest_dir)
    return all((backtest_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _holdout_validation_closure_complete(holdout_dir: Path) -> bool:
    if (holdout_dir / "stage_completion_certificate.yaml").exists():
        return _completion_certificate_allows_progress(holdout_dir)
    return all((holdout_dir / name).exists() for name in MANDATE_CLOSURE_OUTPUTS)


def _gate_status_and_next_action(lineage_root: Path, current_stage: SessionStage) -> tuple[str, str]:
    intake_gate = lineage_root / "00_idea_intake" / "idea_gate_decision.yaml"
    if current_stage == "idea_intake":
        if intake_gate.exists():
            verdict = _read_yaml(intake_gate).get("verdict", "")
            if verdict == "GO_TO_MANDATE":
                return "GO_TO_MANDATE_PENDING_CONFIRMATION", "Await explicit CONFIRM_MANDATE"
            if verdict == "DROP":
                return "DROP", "Reframe or terminate the idea"
        return (
            "IN_PROGRESS",
            "Finalize qualification artifacts only after intake interview approval",
        )

    if current_stage == "idea_intake_confirmation_pending":
        decision = read_idea_intake_transition_decision(lineage_root)
        if decision == "HOLD":
            return "IDEA_INTAKE_ON_HOLD", "Wait for explicit CONFIRM_IDEA_INTAKE"
        return (
            "IDEA_INTAKE_PENDING_CONFIRMATION",
            "Run with --confirm-intake or reply CONFIRM_IDEA_INTAKE <lineage_id> after finishing the intake interview",
        )

    if current_stage == "mandate_confirmation_pending":
        next_group = next_mandate_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_MANDATE_PENDING_CONFIRMATION", f"Complete mandate freeze group: {next_group}"
        decision = read_mandate_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_MANDATE_ON_HOLD", "Wait for explicit CONFIRM_MANDATE"
        return "GO_TO_MANDATE_PENDING_CONFIRMATION", "Run with --confirm-mandate or reply CONFIRM_MANDATE <lineage_id>"

    if current_stage == "mandate_author":
        return "GO_TO_MANDATE_CONFIRMED", "Freeze mandate artifacts"

    if current_stage == "mandate_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run mandate review"

    if current_stage == "data_ready_confirmation_pending":
        next_group = next_data_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_DATA_READY_PENDING_CONFIRMATION", f"Complete data_ready freeze group: {next_group}"
        decision = read_data_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_DATA_READY_ON_HOLD", "Wait for explicit CONFIRM_DATA_READY"
        return "GO_TO_DATA_READY_PENDING_CONFIRMATION", "Run with --confirm-data-ready or reply CONFIRM_DATA_READY <lineage_id>"

    if current_stage == "data_ready_author":
        return "GO_TO_DATA_READY_CONFIRMED", "Freeze data_ready artifacts"

    if current_stage == "data_ready_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run data_ready review"

    if current_stage == "signal_ready_confirmation_pending":
        next_group = next_signal_ready_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_SIGNAL_READY_PENDING_CONFIRMATION", f"Complete signal_ready freeze group: {next_group}"
        decision = read_signal_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_SIGNAL_READY_ON_HOLD", "Wait for explicit CONFIRM_SIGNAL_READY"
        return "GO_TO_SIGNAL_READY_PENDING_CONFIRMATION", "Run with --confirm-signal-ready or reply CONFIRM_SIGNAL_READY <lineage_id>"

    if current_stage == "signal_ready_author":
        return "GO_TO_SIGNAL_READY_CONFIRMED", "Freeze signal_ready artifacts"

    if current_stage == "signal_ready_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run signal_ready review"

    if current_stage == "train_freeze_confirmation_pending":
        next_group = next_train_freeze_group(lineage_root)
        if next_group is not None:
            return "GO_TO_TRAIN_FREEZE_PENDING_CONFIRMATION", f"Complete train_freeze group: {next_group}"
        decision = read_train_freeze_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_TRAIN_FREEZE_ON_HOLD", "Wait for explicit CONFIRM_TRAIN_FREEZE"
        return "GO_TO_TRAIN_FREEZE_PENDING_CONFIRMATION", "Run with --confirm-train-freeze or reply CONFIRM_TRAIN_FREEZE <lineage_id>"

    if current_stage == "train_freeze_author":
        return "GO_TO_TRAIN_FREEZE_CONFIRMED", "Freeze train_freeze artifacts"

    if current_stage == "train_freeze_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run train_freeze review"

    if current_stage == "test_evidence_confirmation_pending":
        next_group = next_test_evidence_group(lineage_root)
        if next_group is not None:
            return "GO_TO_TEST_EVIDENCE_PENDING_CONFIRMATION", f"Complete test_evidence group: {next_group}"
        decision = read_test_evidence_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_TEST_EVIDENCE_ON_HOLD", "Wait for explicit CONFIRM_TEST_EVIDENCE"
        return "GO_TO_TEST_EVIDENCE_PENDING_CONFIRMATION", "Run with --confirm-test-evidence or reply CONFIRM_TEST_EVIDENCE <lineage_id>"

    if current_stage == "test_evidence_author":
        return "GO_TO_TEST_EVIDENCE_CONFIRMED", "Freeze test_evidence artifacts"

    if current_stage == "test_evidence_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run test_evidence review"

    if current_stage == "backtest_ready_confirmation_pending":
        next_group = next_backtest_ready_group(lineage_root)
        if next_group is not None:
            return "GO_TO_BACKTEST_READY_PENDING_CONFIRMATION", f"Complete backtest_ready group: {next_group}"
        decision = read_backtest_ready_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_BACKTEST_READY_ON_HOLD", "Wait for explicit CONFIRM_BACKTEST_READY"
        return "GO_TO_BACKTEST_READY_PENDING_CONFIRMATION", "Run with --confirm-backtest-ready or reply CONFIRM_BACKTEST_READY <lineage_id>"

    if current_stage == "backtest_ready_author":
        return "GO_TO_BACKTEST_READY_CONFIRMED", "Freeze backtest_ready artifacts"

    if current_stage == "backtest_ready_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run backtest_ready review"

    if current_stage == "holdout_validation_confirmation_pending":
        next_group = next_holdout_validation_group(lineage_root)
        if next_group is not None:
            return (
                "GO_TO_HOLDOUT_VALIDATION_PENDING_CONFIRMATION",
                f"Complete holdout_validation group: {next_group}",
            )
        decision = read_holdout_validation_transition_decision(lineage_root)
        if decision == "HOLD":
            return "GO_TO_HOLDOUT_VALIDATION_ON_HOLD", "Wait for explicit CONFIRM_HOLDOUT_VALIDATION"
        return (
            "GO_TO_HOLDOUT_VALIDATION_PENDING_CONFIRMATION",
            "Run with --confirm-holdout-validation or reply CONFIRM_HOLDOUT_VALIDATION <lineage_id>",
        )

    if current_stage == "holdout_validation_author":
        return "GO_TO_HOLDOUT_VALIDATION_CONFIRMED", "Freeze holdout_validation artifacts"

    if current_stage == "holdout_validation_review":
        return "REVIEW_PENDING", "Write review_findings.yaml and run holdout_validation review"

    return "REVIEW_COMPLETE", "Stop here until promotion_decision orchestration exists"


def _read_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    return {}


def _idea_intake_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "00_idea_intake" / IDEA_INTAKE_TRANSITION_APPROVAL_FILE


def _approval_path(lineage_root: Path) -> Path:
    return lineage_root / "00_idea_intake" / MANDATE_TRANSITION_APPROVAL_FILE


def _data_ready_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "02_data_ready" / DATA_READY_TRANSITION_APPROVAL_FILE


def _signal_ready_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "03_signal_ready" / SIGNAL_READY_TRANSITION_APPROVAL_FILE


def _train_freeze_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "04_train_freeze" / TRAIN_FREEZE_TRANSITION_APPROVAL_FILE


def _test_evidence_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "05_test_evidence" / TEST_EVIDENCE_TRANSITION_APPROVAL_FILE


def _backtest_ready_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "06_backtest" / BACKTEST_READY_TRANSITION_APPROVAL_FILE


def _holdout_validation_approval_path(lineage_root: Path) -> Path:
    return lineage_root / "07_holdout" / HOLDOUT_VALIDATION_TRANSITION_APPROVAL_FILE
