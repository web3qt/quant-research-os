from runtime.scripts.build_anti_drift_release_artifact import build_release_artifact


def test_build_release_artifact_passes_when_all_inputs_green() -> None:
    artifact = build_release_artifact(
        nightly_gate_summary={"status": "PASS"},
        generator_fresh=True,
        classification_baseline_matches=True,
        snapshot_cli_ok=True,
    )

    assert artifact["status"] == "PASS"
    assert artifact["failure_reasons"] == []


def test_build_release_artifact_fails_on_any_blocker() -> None:
    artifact = build_release_artifact(
        nightly_gate_summary={"status": "FAIL"},
        generator_fresh=False,
        classification_baseline_matches=True,
        snapshot_cli_ok=False,
    )

    assert artifact["status"] == "FAIL"
    assert artifact["failure_reasons"] == [
        "nightly_gate_failed",
        "generated_skills_stale",
        "snapshot_cli_failed",
    ]
