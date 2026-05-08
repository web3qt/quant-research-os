from pathlib import Path

import pytest
import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from runtime.tools.lineage_program_runtime import StageProgramRuntimeError, validate_stage_program


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_validate_stage_program_rejects_post_mandate_thin_wrapper(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (lineage_root / "01_mandate" / "author" / "formal").mkdir(parents=True, exist_ok=True)
    (lineage_root / "01_mandate" / "author" / "formal" / "mandate.md").write_text(
        "# Mandate\n",
        encoding="utf-8",
    )
    (lineage_root / "02_csf_data_ready" / "author" / "draft").mkdir(parents=True, exist_ok=True)
    (lineage_root / "02_csf_data_ready" / "author" / "draft" / "csf_data_ready_freeze_draft.yaml").write_text(
        "groups:\n  contract:\n    confirmed: true\n",
        encoding="utf-8",
    )
    (lineage_root / "02_csf_data_ready" / "author" / "formal").mkdir(parents=True, exist_ok=True)
    (lineage_root / "02_csf_data_ready" / "author" / "formal" / "panel_manifest.json").write_text(
        "{\n  \"status\": \"ready\"\n}\n",
        encoding="utf-8",
    )
    (lineage_root / "02_csf_data_ready" / "author" / "formal" / "panel_manifest.md").write_text(
        "# Panel Manifest\n",
        encoding="utf-8",
    )
    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "# 读取冻结合同并生成正式产物\n"
        "from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate\n"
        "def main():\n"
        "    build_csf_data_ready_from_mandate(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "csf_data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [
                {"kind": "artifact", "path": "01_mandate/author/formal/mandate.md", "required": True},
                {"kind": "artifact", "path": "02_csf_data_ready/author/draft/csf_data_ready_freeze_draft.yaml", "required": True},
            ],
            "outputs": [
                {"kind": "human", "path": "02_csf_data_ready/author/formal/panel_manifest.md", "required": False},
                {"kind": "machine", "path": "02_csf_data_ready/author/formal/panel_manifest.json", "required": True},
            ],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-1"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="thin wrapper") as excinfo:
        validate_stage_program(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"


def test_validate_stage_program_rejects_local_shim_forwarding_to_builder(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "# 本地 shim 只负责转发，不应绕过身份门禁\n"
        "from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate\n"
        "\n"
        "def _dispatch(lineage_root):\n"
        "    return build_csf_data_ready_from_mandate(lineage_root)\n"
        "\n"
        "def main():\n"
        "    return _dispatch(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "csf_data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-1"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="thin wrapper") as excinfo:
        validate_stage_program(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"


def test_validate_stage_program_rejects_sibling_helper_forwarding_to_builder(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "helpers.py").write_text(
        "from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate\n"
        "\n"
        "def dispatch(lineage_root):\n"
        "    return build_csf_data_ready_from_mandate(lineage_root)\n",
        encoding="utf-8",
    )
    (program_dir / "run_stage.py").write_text(
        "# 入口只负责转发到 sibling helper\n"
        "from helpers import dispatch\n"
        "\n"
        "def main():\n"
        "    return dispatch(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "csf_data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-4"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="thin wrapper") as excinfo:
        validate_stage_program(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"


def test_validate_stage_program_rejects_parent_package_import_forwarding_to_builder(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "# 通过 parent-package import 间接调用 forbidden builder\n"
        "from runtime.tools import csf_data_ready_runtime\n"
        "\n"
        "def main():\n"
        "    return csf_data_ready_runtime.build_csf_data_ready_from_mandate(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "csf_data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-5"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="thin wrapper") as excinfo:
        validate_stage_program(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"


def test_validate_stage_program_rejects_star_import_forwarding_to_builder(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "# 通过 star import 绕过显式 builder 导入\n"
        "from runtime.tools.csf_data_ready_runtime import *\n"
        "\n"
        "def main():\n"
        "    return build_csf_data_ready_from_mandate(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "csf_data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-6"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="thin wrapper") as excinfo:
        validate_stage_program(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"


def test_validate_stage_program_rejects_top_level_runtime_import_forwarding_to_builder(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "# 通过顶层 runtime 导入间接调用 forbidden builder\n"
        "import runtime\n"
        "\n"
        "def main():\n"
        "    return runtime.tools.csf_data_ready_runtime.build_csf_data_ready_from_mandate(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "csf_data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-7"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="thin wrapper") as excinfo:
        validate_stage_program(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"


def test_validate_stage_program_rejects_local_alias_forwarding_to_builder_name(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "# 通过局部别名转发危险 builder 名称\n"
        "from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate\n"
        "forward = build_csf_data_ready_from_mandate\n"
        "\n"
        "def main():\n"
        "    return forward(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "csf_data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-8"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="thin wrapper") as excinfo:
        validate_stage_program(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"


def test_validate_stage_program_rejects_local_alias_forwarding_to_builder_module(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "cross_sectional_factor" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "# 通过局部别名转发危险模块别名\n"
        "import runtime.tools.csf_data_ready_runtime as mod\n"
        "forward = mod\n"
        "\n"
        "def main():\n"
        "    return forward.build_csf_data_ready_from_mandate(None)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "csf_data_ready",
            "route": "cross_sectional_factor",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-9"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="thin wrapper") as excinfo:
        validate_stage_program(lineage_root, "csf_data_ready", "cross_sectional_factor")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"


def test_validate_stage_program_allows_non_builder_runtime_tools_utility_import(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "time_series" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "README.md").write_text("# data_ready\n", encoding="utf-8")
    (program_dir / "run_stage.py").write_text(
        "# 调用非 builder 工具，不应被误判为薄包装\n"
        "from pathlib import Path\n"
        "from runtime.tools.review_skillgen.context_inference import build_stage_context\n"
        "\n"
        "def main():\n"
        "    return build_stage_context(Path(__file__).resolve().parent)\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "data_ready",
            "route": "time_series_signal",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-3"},
        },
    )

    validated = validate_stage_program(lineage_root, "data_ready", "time_series_signal")

    assert validated.entrypoint == "run_stage.py"
    assert validated.stage_id == "data_ready"


def test_validate_stage_program_rejects_missing_chinese_comments_for_helper(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_k"
    program_dir = lineage_root / "program" / "time_series" / "data_ready"
    program_dir.mkdir(parents=True, exist_ok=True)

    (program_dir / "helpers.py").write_text(
        "def build_dataset():\n"
        "    return {'status': 'ok'}\n",
        encoding="utf-8",
    )
    (program_dir / "run_stage.py").write_text(
        "# 读取冻结合同并生成正式数据产物\n"
        "from helpers import build_dataset\n"
        "def main():\n"
        "    build_dataset()\n",
        encoding="utf-8",
    )
    _write_yaml(
        program_dir / "stage_program.yaml",
        {
            "stage_id": "data_ready",
            "route": "time_series_signal",
            "lineage_id": "btc_alt_k",
            "entrypoint": "run_stage.py",
            "entry_type": "python",
            "inputs": [],
            "outputs": [],
            "depends_on_programs": ["mandate"],
            "shared_libs": [],
            "authored_by": {"agent_id": "codex", "agent_role": "executor", "session_id": "sess-2"},
        },
    )

    with pytest.raises(StageProgramRuntimeError, match="Chinese comments") as excinfo:
        validate_stage_program(lineage_root, "data_ready", "time_series_signal")

    assert excinfo.value.reason_code == "STAGE_PROGRAM_INVALID"
