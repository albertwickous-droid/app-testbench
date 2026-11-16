from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app_testbench.config import Settings, build_settings
from app_testbench.errors import RunnerError
from app_testbench.flow import load_flow
from app_testbench.runner import FlowRunner


def test_runner_executes_flow_and_writes_report(
    fake_settings: Settings,
    fake_tools: dict[str, Path],
    apk_file: Path,
    tmp_path: Path,
) -> None:
    flow_path = tmp_path / "flow.yaml"
    flow_path.write_text(
        f"""
version: 1
name: smoke
device:
  package: com.example.app
report:
  capture_screenshots: all
  collect_logcat: true
setup:
  - action: install
    apk: {json.dumps(str(apk_file))}
steps:
  - action: launch
    description: Open <dashboard>
  - action: wait
    seconds: 0
  - action: tap
    x: 100
    y: 200
  - action: text
    text: hello world
  - action: screenshot
    label: login
  - action: dump_ui
    label: login-tree
  - action: assert_ui_contains
    text: Login
  - action: logcat
    label: step-log
teardown:
  - action: close
""".strip(),
        encoding="utf-8",
    )
    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()
    assert result.status == "passed"
    assert result.failed == 0
    launch = next(step for step in result.steps if step.action == "launch")
    assert launch.description == "Open <dashboard>"
    assert Path(result.report_path).is_file()
    report = Path(result.report_path).read_text(encoding="utf-8")
    result_json = Path(result.result_path).read_text(encoding="utf-8")
    assert "data:image/png;base64," in report
    assert "hello%sworld" in report or "hello world" in report
    assert "Open &lt;dashboard&gt;" in report
    assert '"description": "Open <dashboard>"' in result_json

    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any("install" in command for command in commands)
    assert any("shell" in command and "monkey" in command for command in commands)
    assert any(command[-4:] == ["input", "tap", "100", "200"] for command in commands)


def test_flow_device_instance_precedes_environment(
    fake_tools: dict[str, Path], tmp_path: Path
) -> None:
    flow_path = tmp_path / "precedence.yaml"
    flow_path.write_text(
        """
version: 1
name: precedence
device:
  instance: 2
steps:
  - action: back
""".strip(),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["APP_TESTBENCH_INSTANCE"] = "0"
    settings = build_settings(
        adb=str(fake_tools["adb"]),
        mumu_manager=str(fake_tools["manager"]),
        env=env,
    )
    result = FlowRunner(settings, load_flow(flow_path), output_base=tmp_path / "runs").run()
    assert result.status == "passed"
    assert result.environment["instance"] == 2
    commands = [
        json.loads(line)
        for line in (fake_tools["mumu_state"] / "mumu-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert ["info", "-v", "2"] in commands


def test_assert_ui_not_contains_uses_one_snapshot(
    fake_settings: Settings,
    fake_tools: dict[str, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flow_path = tmp_path / "assertion.yaml"
    flow_path.write_text(
        """
version: 1
name: assertion
steps:
  - action: assert_ui_not_contains
    text: Login
""".strip(),
        encoding="utf-8",
    )
    runner = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs")
    calls: list[int] = []

    def fake_dump(step, result) -> tuple[list[str], Path]:
        calls.append(1)
        return (["Login"] if len(calls) == 1 else []), Path("unused")

    monkeypatch.setattr(runner, "_dump_ui_for_result", fake_dump)
    monkeypatch.setattr("app_testbench.runner.time.monotonic", lambda: 0.0)
    monkeypatch.setattr("app_testbench.runner.time.sleep", lambda _: None)
    result = runner.run()
    assert result.status == "failed"
    assert len(calls) == 1
    assert "Unexpected UI text" in (result.steps[0].error or "")


def test_runner_failure_captures_diagnostics(
    fake_settings: Settings,
    fake_tools: dict[str, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAKE_ADB_UI_TEXT", "Home")
    flow_path = tmp_path / "fail.yaml"
    flow_path.write_text(
        """
version: 1
name: failure
device:
  package: com.example.app
report:
  capture_screenshots: failures
steps:
  - action: wait_for_text
    text: Login
    timeout: 1
    interval: 0.1
""".strip(),
        encoding="utf-8",
    )
    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()
    assert result.status == "failed"
    assert result.failed == 1
    assert result.logcat_paths == ["logs/logcat-final.txt"]
    report = Path(result.report_path).read_text(encoding="utf-8")
    assert "UI text was not found" in report
    assert "data:image/png;base64," in report
    assert "sample error" in report


def test_wait_for_text_retries_transient_ui_dump_errors(
    fake_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flow_path = tmp_path / "retry-wait.yaml"
    flow_path.write_text(
        """
version: 1
device:
  package: com.example.app
steps:
  - action: wait_for_text
    text: Login
    timeout: 1
    interval: 0.1
""".strip(),
        encoding="utf-8",
    )
    runner = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs")
    calls: list[int] = []

    def flaky_dump(step, result) -> tuple[list[str], Path]:
        calls.append(1)
        if len(calls) < 3:
            raise RunnerError("uiautomator dump failed.", hint="null root node")
        return ["Login"], Path("unused")

    monkeypatch.setattr(runner, "_dump_ui_for_result", flaky_dump)
    result = runner.run()

    assert result.status == "passed"
    assert len(calls) == 3
    assert result.steps[0].output["attempts"] == 3


def test_teardown_continues_after_a_teardown_failure(
    fake_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAKE_ADB_FAIL_FORCE_STOP", "1")
    flow_path = tmp_path / "teardown.yaml"
    flow_path.write_text(
        """
version: 1
name: teardown-failure
device:
  package: com.example.app
steps:
  - action: back
teardown:
  - action: close
  - action: logcat
    label: after-close
""".strip(),
        encoding="utf-8",
    )
    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()
    assert result.status == "failed"
    teardown = [step for step in result.steps if step.section == "teardown"]
    assert [step.status for step in teardown] == ["failed", "passed"]
    assert "logs/after-close.txt" in result.logcat_paths


def test_final_logcat_does_not_overwrite_teardown_logcat(
    fake_settings: Settings,
    tmp_path: Path,
) -> None:
    flow_path = tmp_path / "final-logcat.yaml"
    flow_path.write_text(
        """
version: 1
name: final-logcat
teardown:
  - action: logcat
    label: logcat-final
""".strip(),
        encoding="utf-8",
    )
    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()
    assert result.status == "passed"
    assert result.logcat_paths == ["logs/logcat-final.txt", "logs/logcat-final-2.txt"]
    output_dir = Path(result.output_dir)
    for relative in result.logcat_paths:
        assert (output_dir / relative).is_file()


def test_reused_artifact_labels_do_not_overwrite_evidence(
    fake_settings: Settings,
    tmp_path: Path,
) -> None:
    flow_path = tmp_path / "artifact-labels.yaml"
    flow_path.write_text(
        """
version: 1
name: artifact-labels
steps:
  - action: dump_ui
    label: evidence
  - action: dump_ui
    label: evidence
  - action: logcat
    label: evidence
  - action: logcat
    label: evidence
""".strip(),
        encoding="utf-8",
    )
    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()
    assert result.status == "passed"

    ui_steps = [step for step in result.steps if step.action == "dump_ui"]
    log_steps = [step for step in result.steps if step.action == "logcat"]
    assert ui_steps[0].ui_files == ["ui/evidence.xml"]
    assert ui_steps[1].ui_files == ["ui/evidence-2.xml"]
    assert log_steps[0].output["path"] == "logs/evidence.txt"
    assert log_steps[1].output["path"] == "logs/evidence-2.txt"
    assert len(set(result.logcat_paths)) == len(result.logcat_paths)

    output_dir = Path(result.output_dir)
    for relative in [*ui_steps[0].ui_files, *ui_steps[1].ui_files]:
        assert (output_dir / relative).is_file()
    for step in log_steps:
        assert (output_dir / step.output["path"]).is_file()


def test_aborted_main_steps_are_recorded_as_skipped(
    fake_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAKE_ADB_FAIL_FORCE_STOP", "1")
    flow_path = tmp_path / "aborted.yaml"
    flow_path.write_text(
        """
version: 1
name: aborted
device:
  package: com.example.app
steps:
  - action: close
  - action: back
  - action: home
""".strip(),
        encoding="utf-8",
    )
    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()
    assert result.status == "failed"
    assert [step.status for step in result.steps] == ["failed", "skipped", "skipped"]
    assert result.skipped == 2
    assert "Aborted after step steps-1 failed." in result.steps[1].output["reason"]


def test_runner_waits_for_android_boot(
    fake_settings: Settings, fake_tools: dict[str, Path], tmp_path: Path
) -> None:
    flow_path = tmp_path / "boot.yaml"
    flow_path.write_text(
        """
version: 1
name: boot-gate
device:
  wait_for_boot: true
  boot_timeout: 1
steps:
  - action: back
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()

    assert result.status == "passed"
    assert result.environment["boot"]["ready"] is True
    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(command[-3:] == ["shell", "getprop", "sys.boot_completed"] for command in commands)


def test_runner_records_boot_gate_timeout(
    fake_settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_BOOT_COMPLETED", "0")
    flow_path = tmp_path / "boot-timeout.yaml"
    flow_path.write_text(
        """
version: 1
name: boot-timeout
device:
  wait_for_boot: true
  boot_timeout: 0.02
steps:
  - action: back
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(
        fake_settings,
        load_flow(flow_path),
        output_base=tmp_path / "runs",
        boot_interval=0.01,
    ).run()

    assert result.status == "failed"
    assert result.environment["boot"]["ready"] is False
    assert [step.status for step in result.steps] == ["failed", "skipped"]
    assert "boot did not complete" in (result.steps[0].error or "")


def test_runner_verifies_install_identity(
    fake_settings: Settings,
    fake_tools: dict[str, Path],
    apk_file: Path,
    tmp_path: Path,
) -> None:
    flow_path = tmp_path / "verified-install.yaml"
    flow_path.write_text(
        f"""
version: 1
name: verified-install
device:
  package: com.example.app
setup:
  - action: install
    apk: {json.dumps(str(apk_file))}
    expected_version_code: 42
    expected_version_name: 1.2.3
steps:
  - action: back
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()

    assert result.status == "passed"
    install = next(step for step in result.steps if step.action == "install")
    assert install.output["package_identity"]["package"] == "com.example.app"
    assert install.output["package_identity"]["version_code"] == 42
    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(
        command[-4:] == ["shell", "dumpsys", "package", "com.example.app"] for command in commands
    )


def test_runner_fails_when_install_identity_does_not_match(
    fake_settings: Settings,
    apk_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAKE_ADB_VERSION_NAME", "9.9.9")
    flow_path = tmp_path / "verified-install-failure.yaml"
    flow_path.write_text(
        f"""
version: 1
name: verified-install-failure
device:
  package: com.example.app
setup:
  - action: install
    apk: {json.dumps(str(apk_file))}
    expected_version_name: 1.2.3
steps:
  - action: back
""".strip(),
        encoding="utf-8",
    )

    junit_path = tmp_path / "junit.xml"
    result = FlowRunner(
        fake_settings,
        load_flow(flow_path),
        output_base=tmp_path / "runs",
        junit_path=junit_path,
    ).run()

    assert result.status == "failed"
    install = next(step for step in result.steps if step.action == "install")
    assert "did not match expectations" in (install.error or "")
    assert "versionName" in (install.hint or "")
    assert "9.9.9" in (install.hint or "")
    assert junit_path.is_file()
    root = ET.parse(junit_path).getroot()
    assert root.attrib["failures"] == "1"
    assert root.find(".//failure") is not None


def test_runner_taps_selector_and_clears_focused_input(
    fake_settings: Settings,
    fake_tools: dict[str, Path],
    tmp_path: Path,
) -> None:
    flow_path = tmp_path / "selector.yaml"
    flow_path.write_text(
        """
version: 1
name: selector-actions
steps:
  - action: tap_text
    text: Search
    field: content-desc
    match: exact
  - action: clear_text
    count: 3
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()

    assert result.status == "passed"
    selector = result.steps[0]
    assert selector.output["matched_value"] == "Search"
    assert selector.output["tap"] == {"x": 400, "y": 250}
    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(command[-4:] == ["input", "tap", "400", "250"] for command in commands)
    delete_events = [
        command for command in commands if command[-3:] == ["input", "keyevent", "KEYCODE_DEL"]
    ]
    assert len(delete_events) == 3


def test_wait_for_text_recovers_from_visible_anr_dialog(
    fake_settings: Settings,
    fake_tools: dict[str, Path],
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("FAKE_ADB_UI_SEQUENCE", "anr,normal")
    flow_path = tmp_path / "anr-recovery.yaml"
    flow_path.write_text(
        """
version: 1
name: anr-recovery
steps:
  - action: wait_for_text
    text: Login
    timeout: 5
    interval: 0.1
    recover_anr: true
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()

    assert result.status == "passed"
    assert result.steps[0].output["anr_recoveries"] == 1
    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(command[-4:] == ["input", "tap", "300", "550"] for command in commands)


def test_optional_tap_text_returns_not_found_without_failing(
    fake_settings: Settings,
    fake_tools: dict[str, Path],
    tmp_path: Path,
) -> None:
    flow_path = tmp_path / "optional-tap.yaml"
    flow_path.write_text(
        """
version: 1
name: optional-tap
steps:
  - action: tap_text
    text: Already dismissed
    timeout: 1
    interval: 0.1
    optional: true
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()

    assert result.status == "passed"
    assert result.steps[0].output["found"] is False


def test_runner_waits_for_activity_and_asserts_logcat(
    fake_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "FAKE_ADB_ACTIVITY_SEQUENCE",
        "org.example/.SplashActivity,org.example/.PlayerActivity",
    )
    monkeypatch.setenv(
        "FAKE_ADB_LOGCAT_EXTRA",
        "11-05 12:00:00.500 I/VLC( 1000): Creating an input for 'demo.mp4'",
    )
    flow_path = tmp_path / "activity-logcat.yaml"
    flow_path.write_text(
        """
version: 1
name: activity-logcat
steps:
  - action: wait_for_activity
    activity: org.example/.PlayerActivity
    timeout: 5
    interval: 0.1
  - action: assert_logcat_contains
    text: "creating an input"
    lines: 100
    ignore_case: true
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()

    assert result.status == "passed"
    activity = result.steps[0]
    assert activity.output["observed_activity"] == "org.example/.PlayerActivity"
    assert activity.output["attempts"] == 2
    log_assertion = result.steps[1]
    assert log_assertion.output["match_count"] == 1
    assert "Creating an input" in log_assertion.output["matched_line"]


def test_wait_for_activity_failure_reports_last_observed_component(
    fake_settings: Settings,
    tmp_path: Path,
) -> None:
    flow_path = tmp_path / "activity-failure.yaml"
    flow_path.write_text(
        """
version: 1
name: activity-failure
steps:
  - action: wait_for_activity
    activity: org.example/.ExpectedActivity
    timeout: 1
    interval: 0.1
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()

    assert result.status == "failed"
    failed = result.steps[0]
    assert "did not match" in (failed.error or "")
    assert "com.example.app/.MainActivity" in (failed.hint or "")


def test_assert_logcat_contains_failure_includes_recent_tail(
    fake_settings: Settings,
    tmp_path: Path,
) -> None:
    flow_path = tmp_path / "logcat-failure.yaml"
    flow_path.write_text(
        """
version: 1
name: logcat-failure
steps:
  - action: assert_logcat_contains
    text: definitely-not-in-logcat
    lines: 100
""".strip(),
        encoding="utf-8",
    )

    result = FlowRunner(fake_settings, load_flow(flow_path), output_base=tmp_path / "runs").run()

    assert result.status == "failed"
    failed = result.steps[0]
    assert "did not contain" in (failed.error or "")
    assert "sample error" in (failed.hint or "")
