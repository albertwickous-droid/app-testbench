from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app_testbench.device import (
    AndroidDevice,
    encode_input_text,
    normalize_keyevent,
    parse_adb_devices,
    parse_package_identity,
    parse_surface_orientation,
    parse_top_activity,
    validate_activity,
    validate_mime_type,
    validate_open_uri,
    validate_port,
)
from app_testbench.errors import DeviceError
from app_testbench.utils import ProcessRunner


def test_parse_adb_devices() -> None:
    output = """List of devices attached
127.0.0.1:5555\tdevice product:fake model:FakeMuMu device:fake
emulator-5554\toffline
"""
    assert parse_adb_devices(output) == [
        {
            "serial": "127.0.0.1:5555",
            "state": "device",
            "product": "fake",
            "model": "FakeMuMu",
            "device": "fake",
        },
        {"serial": "emulator-5554", "state": "offline"},
    ]


def test_input_text_encoding_and_unicode_guard() -> None:
    assert encode_input_text("hello world!") == "hello%sworld!"
    with pytest.raises(DeviceError, match="ASCII"):
        encode_input_text("你好")


def test_activity_component_validation() -> None:
    assert validate_activity(" com.example/.MainActivity ") == "com.example/.MainActivity"
    assert validate_activity("com.example/com.example.MainActivity") == (
        "com.example/com.example.MainActivity"
    )
    assert validate_activity("MainActivity") == "MainActivity"
    for value in ("", "   ", "com.example/.MainActivity; id", "com.example//MainActivity"):
        with pytest.raises(DeviceError, match="Invalid activity component"):
            validate_activity(value)


def test_normalize_keyevent() -> None:
    assert normalize_keyevent("enter") == "KEYCODE_ENTER"
    assert normalize_keyevent("KEYCODE_BACK") == "KEYCODE_BACK"
    assert normalize_keyevent("66") == "66"
    with pytest.raises(DeviceError):
        normalize_keyevent("bad key")


def test_parse_surface_orientation() -> None:
    assert parse_surface_orientation("  SurfaceOrientation: 1\n") == 1
    assert parse_surface_orientation("no orientation here") is None


def test_parse_top_activity_supports_common_dumpsys_shapes() -> None:
    top_resumed = "  topResumedActivity=ActivityRecord{123 u0 com.example.app/.MainActivity t42}"
    assert parse_top_activity(top_resumed) == {
        "component": "com.example.app/.MainActivity",
        "package": "com.example.app",
        "activity": ".MainActivity",
        "source_line": top_resumed.strip(),
    }

    focused = (
        "  mFocusedApp=ActivityRecord{abc u0 org.mozilla.fennec_fdroid/"
        "org.mozilla.fenix.HomeActivity t9}"
    )
    assert parse_top_activity(focused)["component"] == (
        "org.mozilla.fennec_fdroid/org.mozilla.fenix.HomeActivity"
    )
    assert parse_top_activity("ACTIVITY MANAGER ACTIVITIES") is None


def test_android_device_fixture_workflow(fake_tools: dict[str, Path], tmp_path: Path) -> None:
    runner = ProcessRunner(10)
    device = AndroidDevice(fake_tools["adb"], runner)
    assert device.connect() == "127.0.0.1:5555"
    assert device.get_state() == "device"

    device.tap(10, 20)
    device.swipe(10, 20, 30, 40, 500)
    device.input_text("hello world")
    device.keyevent("ENTER")
    device.launch("com.example.app")
    device.close("com.example.app")

    screenshot = device.screenshot(tmp_path / "shot.png")
    assert screenshot.read_bytes().startswith(b"\x89PNG")
    ui = device.dump_ui(tmp_path / "ui.xml")
    assert "Login" in device.ui_text(ui)
    assert device.ui_node_count(ui) >= 3
    assert device.top_activity()["component"] == "com.example.app/.MainActivity"
    assert "sample error" in device.logcat_text(lines=100)
    logcat = device.logcat(tmp_path / "log.txt")
    assert "sample error" in logcat.read_text(encoding="utf-8")

    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(command[-4:] == ["input", "tap", "10", "20"] for command in commands)
    assert any("shell" in command and "monkey" in command for command in commands)
    assert any(
        "shell" in command and "am" in command and "force-stop" in command for command in commands
    )


def test_dump_ui_cleans_remote_file_after_read_failure(
    fake_tools: dict[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_INVALID_UI", "1")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))
    with pytest.raises(DeviceError, match="UI hierarchy"):
        device.dump_ui(tmp_path / "ui.xml")

    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert commands[-1][-4:] == ["shell", "rm", "-f", "/sdcard/app_testbench_window.xml"]


def test_launch_activity_rejects_zero_exit_error_output(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_FAIL_AM_START", "1")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))
    with pytest.raises(DeviceError, match="Activity could not be launched"):
        device.launch("com.example.app", "com.example.app.MissingActivity")

    monkeypatch.delenv("FAKE_ADB_FAIL_AM_START")
    assert device.launch("com.example.app", ".MainActivity") == "Status: ok"
    with pytest.raises(DeviceError, match="Invalid activity component"):
        device.launch("com.example.app", "")


def test_launch_normalizes_plain_activity_class(fake_tools: dict[str, Path]) -> None:
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))
    assert device.launch("com.example.app", "MainActivity") == "Status: ok"
    assert device.launch("com.example.app", "com.other.feature.MainActivity") == "Status: ok"

    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    components = [command[-1] for command in commands if command[-5:-2] == ["am", "start", "-W"]]
    assert components == [
        "com.example.app/com.example.app.MainActivity",
        "com.example.app/com.other.feature.MainActivity",
    ]


def test_get_state_ignores_adb_stderr_diagnostics(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_GET_STATE_STDERR", "1")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10), "127.0.0.1:5555")
    assert device.get_state() == "device"
    assert device.connect() == "127.0.0.1:5555"


def test_wait_until_boot_complete_polls_until_ready(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_BOOT_SEQUENCE", "0,1")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))

    info = device.wait_until_boot_complete(timeout=1, interval=0.01)

    assert info["ready"] is True
    assert info["attempts"] == 2
    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert commands.count(["shell", "getprop", "sys.boot_completed"]) == 2


def test_wait_until_boot_complete_times_out(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_BOOT_COMPLETED", "0")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))

    with pytest.raises(DeviceError, match="boot did not complete") as caught:
        device.wait_until_boot_complete(timeout=0.02, interval=0.01)

    assert "Polled sys.boot_completed" in (caught.value.hint or "")


def test_parse_package_identity_reads_dumpsys_fields() -> None:
    output = """Packages:
  Package [com.example.app] (fake):
    versionCode=42 minSdk=23
    versionName="1.2.3"
"""
    assert parse_package_identity(output) == {
        "package": "com.example.app",
        "version_code": 42,
        "version_name": "1.2.3",
    }


def test_install_verifies_expected_package_identity(
    fake_tools: dict[str, Path], apk_file: Path
) -> None:
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))

    assert (
        device.install(
            apk_file,
            expected_package="com.example.app",
            expected_version_code=42,
            expected_version_name="1.2.3",
        )
        == "Success"
    )
    assert device.last_package_identity is not None
    assert device.last_package_identity["package"] == "com.example.app"
    assert device.last_package_identity["version_code"] == 42
    assert device.last_package_identity["version_name"] == "1.2.3"

    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(
        command[-4:] == ["shell", "dumpsys", "package", "com.example.app"] for command in commands
    )


def test_install_rejects_version_mismatch(
    fake_tools: dict[str, Path], apk_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_VERSION_CODE", "43")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))

    with pytest.raises(DeviceError, match="did not match") as caught:
        device.install(
            apk_file,
            expected_package="com.example.app",
            expected_version_code=42,
        )

    assert "versionCode" in (caught.value.hint or "")
    assert "43" in (caught.value.hint or "")
    assert device.last_package_identity is None


def test_install_without_expectations_does_not_query_package(
    fake_tools: dict[str, Path], apk_file: Path
) -> None:
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))

    assert device.install(apk_file) == "Success"
    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert not any("dumpsys" in command for command in commands)


def test_install_requires_package_for_version_expectations(
    fake_tools: dict[str, Path], apk_file: Path
) -> None:
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))

    with pytest.raises(DeviceError, match="expected_package is required"):
        device.install(apk_file, expected_version_code=42)


def test_install_reports_dumpsys_failure(
    fake_tools: dict[str, Path], apk_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_DUMPSYS_FAIL", "1")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))

    with pytest.raises(DeviceError, match="ADB command failed"):
        device.install(apk_file, expected_package="com.example.app")

    assert device.last_package_identity is None


def test_install_rejects_package_mismatch(
    fake_tools: dict[str, Path], apk_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_DUMPSYS_PACKAGE", "com.other.app")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))

    with pytest.raises(DeviceError, match="did not match") as caught:
        device.install(apk_file, expected_package="com.example.app")

    assert "package" in (caught.value.hint or "")
    assert "com.other.app" in (caught.value.hint or "")


def test_open_uri_and_port_validation() -> None:
    assert validate_open_uri("http://127.0.0.1:18765/path?q=1") == (
        "http://127.0.0.1:18765/path?q=1"
    )
    assert validate_open_uri("file:///sdcard/Movies/demo.mp4") == ("file:///sdcard/Movies/demo.mp4")
    assert validate_mime_type(" Video/MP4 ") == "video/mp4"
    assert validate_port(18_765, name="port") == 18_765

    for value in (
        "javascript:alert(1)",
        "file:///data/local/tmp/demo.mp4",
        "https://user:secret@example.test/",
        "http://example.test/a b",
        "",
    ):
        with pytest.raises(DeviceError):
            validate_open_uri(value)
    with pytest.raises(DeviceError, match="MIME"):
        validate_mime_type("video")
    with pytest.raises(DeviceError, match="between 1 and 65535"):
        validate_port(0, name="port")


def test_open_uri_builds_a_quoted_view_intent(fake_tools: dict[str, Path]) -> None:
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10), "127.0.0.1:5555")

    device.open_uri(
        "http://127.0.0.1:18765/?mode=qa",
        package="com.example.app",
        mime_type="text/html",
    )

    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    shell_commands = [command for command in commands if "shell" in command]
    assert any(
        "am start -W -a android.intent.action.VIEW" in command[command.index("shell") + 1]
        and "http://127.0.0.1:18765/?mode=qa" in command[command.index("shell") + 1]
        and "-p com.example.app" in command[command.index("shell") + 1]
        for command in shell_commands
    )


def test_reverse_port_builds_and_removes_mapping(fake_tools: dict[str, Path]) -> None:
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10), "127.0.0.1:5555")

    device.reverse_port(18_765, local_port=18_766)
    device.reverse_port(18_765, remove=True)

    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    reverse_commands = [
        command[command.index("reverse") :] for command in commands if "reverse" in command
    ]
    assert ["reverse", "tcp:18765", "tcp:18766"] in reverse_commands
    assert ["reverse", "--remove", "tcp:18765"] in reverse_commands


def test_clear_data_and_orientation_command_shape(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_ADB_SURFACE_ORIENTATION_SEQUENCE", "1,0")
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10), "127.0.0.1:5555")

    assert device.clear_app_data("com.example.app") == "Success"
    message = device.set_orientation("portrait")
    device.set_orientation("auto")
    assert "SurfaceOrientation 0" in message

    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    shell_commands = [
        command[command.index("shell") :] for command in commands if "shell" in command
    ]
    assert ["shell", "pm", "clear", "com.example.app"] in shell_commands
    assert ["shell", "wm", "fixed-to-user-rotation", "enabled"] in shell_commands
    assert ["shell", "wm", "user-rotation", "lock", "0"] in shell_commands
    assert ["shell", "wm", "fixed-to-user-rotation", "default"] in shell_commands
    assert ["shell", "wm", "user-rotation", "free"] in shell_commands
    assert ["shell", "dumpsys", "input"] in shell_commands


def test_install_verifies_apk_sha256_before_adb(
    fake_tools: dict[str, Path], apk_file: Path
) -> None:
    expected = hashlib.sha256(apk_file.read_bytes()).hexdigest()
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))
    assert device.install(apk_file, expected_sha256=expected) == "Success"
    assert device.last_apk_sha256 == expected


def test_install_sha256_mismatch_never_invokes_adb(
    fake_tools: dict[str, Path], apk_file: Path
) -> None:
    device = AndroidDevice(fake_tools["adb"], ProcessRunner(10))
    with pytest.raises(DeviceError, match="installation was not attempted"):
        device.install(apk_file, expected_sha256="0" * 64)
    command_log = fake_tools["adb_state"] / "adb-commands.jsonl"
    if command_log.exists():
        commands = [
            json.loads(line) for line in command_log.read_text(encoding="utf-8").splitlines()
        ]
        assert not any("install" in command for command in commands)
    assert device.last_apk_sha256 is None
