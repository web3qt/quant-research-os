from tests.helpers.skill_test_utils import skill_path, skill_text


TSS_FAILURE_SKILLS = [
    ("tss_train_freeze", "qros-tss-train-freeze-failure"),
    ("tss_test_evidence", "qros-tss-test-evidence-failure"),
]


def test_tss_failure_skills_exist_and_are_route_specific() -> None:
    for stage, skill_name in TSS_FAILURE_SKILLS:
        path = skill_path(skill_name)
        content = path.read_text(encoding="utf-8")
        assert f"name: {skill_name}" in content
        assert stage in content
        assert "time_series_signal" in content
        assert "不得把 TSS 失败路由到 legacy unprefixed failure skill" in content
        assert "qros-lineage-change-control" in content


def test_stage_failure_handler_routes_tss_failures_to_tss_specific_skills() -> None:
    content = skill_text("qros-stage-failure-handler")

    assert "`tss_train_freeze` → `qros-tss-train-freeze-failure`" in content
    assert "`tss_test_evidence` → `qros-tss-test-evidence-failure`" in content
    assert "| `tss_train_freeze` | `qros-tss-train-freeze-failure` |" in content
    assert "| `tss_test_evidence` | `qros-tss-test-evidence-failure` |" in content


def test_using_qros_lists_tss_failure_skills() -> None:
    content = skill_text("using-qros")

    assert "qros-tss-train-freeze-failure" in content
    assert "qros-tss-test-evidence-failure" in content
