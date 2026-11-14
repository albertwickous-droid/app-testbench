from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app_testbench.cli import build_parser, main
from app_testbench.config import build_settings
from app_testbench.errors import ConfigError
from app_testbench.flow import load_flow


def test_doctor_json_accepts_options_after_subcommand(fake_tools: dict[str, Path], capsys) -> None:
    code = main(
        [
            "doctor",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert payload["command"] == "doctor"
    assert payload["data"]["status"] == "pass"


def test_global_options_before_subcommand_are_preserved() -> None:
    args = build_parser().parse_args(
        [
            "--adb",
            "adb.exe",
            "--mumumanager",
            "MuMuManager.exe",
            "--instance",
            "2",
            "--serial",
            "127.0.0.1:16416",
            "--timeout",
            "5",
            "--json",
            "doctor",
        ]
    )
    assert args.adb == "adb.exe"
    assert args.mumumanager == "MuMuManager.exe"
    assert args.instance == 2
    assert args.serial == "127.0.0.1:16416"
    assert args.timeout == 5.0
    assert args.json_output is True


def test_debug_option_is_available_after_subcommand(fake_tools: dict[str, Path], capsys) -> None:
    code = main(
        [
            "doctor",
            "--debug",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True


def test_json_environment_is_honored(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setenv("APP_TESTBENCH_JSON", "1")
    code = main(
        [
            "doctor",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert payload["command"] == "doctor"


def test_json_environment_is_honored_for_errors(
    fake_tools: dict[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setenv("APP_TESTBENCH_JSON", "1")
    code = main(
        [
            "validate",
            str(tmp_path / "missing.yaml"),
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["ok"] is False
    assert payload["error"]["type"] == "flow_error"


@pytest.mark.parametrize(
    "argv",
    [
        ["doctor", "--timeout", "nan"],
        ["doctor", "--timeout", "0"],
    ],
)
def test_json_mode_covers_argument_and_configuration_errors(
    argv: list[str], monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setenv("APP_TESTBENCH_JSON", "1")
    code = main(argv)
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == 2
    assert captured.err == ""
    assert payload["ok"] is False
    assert payload["command"] == "doctor"
    assert payload["error"]["type"] == "config_error"


def test_instance_start_rejects_negative_wait(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setenv("APP_TESTBENCH_JSON", "1")
    code = main(["instance", "start", "--wait", "-1"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == 2
    assert captured.err == ""
    assert payload["error"]["type"] == "config_error"
    assert "must be >= 0" in payload["error"]["message"]


def test_invalid_device_argument_fails_before_device_connection(
    fake_tools: dict[str, Path], capsys
) -> None:
    code = main(
        [
            "tap",
            "-1",
            "1",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["error"]["type"] == "config_error"
    assert not (fake_tools["adb_state"] / "adb-commands.jsonl").exists()
    assert not (fake_tools["mumu_state"] / "mumu-commands.jsonl").exists()


def test_non_finite_timeout_setting_is_rejected() -> None:
    with pytest.raises(ConfigError, match="finite number"):
        build_settings(timeout=float("nan"))


@pytest.mark.parametrize("keyword", ["adb", "mumu_manager"])
def test_explicit_tool_paths_must_be_files(tmp_path: Path, keyword: str) -> None:
    with pytest.raises(ConfigError, match="does not exist or is not executable"):
        build_settings(**{keyword: str(tmp_path)}, env={})


def test_instance_list_json(fake_tools: dict[str, Path], capsys) -> None:
    code = main(
        [
            "instance",
            "list",
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["data"]["instances"][0]["serial"] == "127.0.0.1:16384"


def test_validate_flow(fake_tools: dict[str, Path], tmp_path: Path, capsys) -> None:
    flow = tmp_path / "flow.json"
    flow.write_text(
        json.dumps({"version": 1, "name": "valid", "steps": [{"action": "back"}]}),
        encoding="utf-8",
    )
    code = main(
        [
            "validate",
            str(flow),
            "--adb",
            str(fake_tools["adb"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["data"]["name"] == "valid"
    assert payload["data"]["step_count"] == 1


def test_init_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "flow.yaml"
    output.write_text("existing", encoding="utf-8")
    code = main(["init", "--output", str(output)])
    assert code == 2
    assert output.read_text(encoding="utf-8") == "existing"


def test_init_rejects_directory_output_with_force(tmp_path: Path, capsys) -> None:
    output = tmp_path / "flow-output"
    output.mkdir()
    code = main(["init", "--output", str(output), "--force"])
    captured = capsys.readouterr()
    assert code == 2
    assert "directory" in captured.err.lower()


def test_json_after_separator_is_text(fake_tools: dict[str, Path], capsys) -> None:
    code = main(
        [
            "text",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "schema_version" not in captured.out
    commands = [
        json.loads(line)
        for line in (fake_tools["adb_state"] / "adb-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(command[-1] == "input text --json" for command in commands)


def test_screenshot_rejects_directory_output(
    fake_tools: dict[str, Path], tmp_path: Path, capsys
) -> None:
    output = tmp_path / "screenshots"
    output.mkdir()
    code = main(
        [
            "screenshot",
            "--output",
            str(output),
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["error"]["type"] == "config_error"
    assert "directory" in payload["error"]["message"].lower()
    assert not (fake_tools["adb_state"] / "adb-commands.jsonl").exists()
    assert not (fake_tools["mumu_state"] / "mumu-commands.jsonl").exists()


def test_module_entrypoint_subprocess(fake_tools: dict[str, Path]) -> None:
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app_testbench",
            "doctor",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0, completed.stderr
    assert payload["ok"] is True


def test_run_rejects_file_output(fake_tools: dict[str, Path], tmp_path: Path, capsys) -> None:
    flow = tmp_path / "flow.json"
    flow.write_text(
        json.dumps({"version": 1, "steps": [{"action": "back"}]}),
        encoding="utf-8",
    )
    output = tmp_path / "runs"
    output.write_text("not a directory", encoding="utf-8")
    code = main(
        [
            "run",
            str(flow),
            "--output",
            str(output),
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["error"]["type"] == "config_error"
    assert "not a directory" in payload["error"]["message"].lower()


def test_run_flow_from_cli(fake_tools: dict[str, Path], tmp_path: Path, capsys) -> None:
    flow = tmp_path / "flow.yaml"
    flow.write_text(
        """
version: 1
name: cli-run
device:
  package: com.example.app
report:
  capture_screenshots: failures
steps:
  - action: launch
  - action: assert_ui_contains
    text: Login
""".strip(),
        encoding="utf-8",
    )
    code = main(
        [
            "run",
            str(flow),
            "--output",
            str(tmp_path / "runs"),
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["status"] == "passed"
    assert Path(payload["data"]["report_path"]).is_file()


def test_init_uses_default_extension_for_selected_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    assert load_flow(tmp_path / "mumu-flow.yaml").name == "login-smoke"

    assert main(["init", "--format", "json"]) == 0
    assert load_flow(tmp_path / "mumu-flow.json").name == "login-smoke"
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "mumu-flow.json",
        "mumu-flow.yaml",
    ]


def test_run_cli_exports_junit_and_waits_for_boot(
    fake_tools: dict[str, Path], tmp_path: Path, capsys
) -> None:
    flow = tmp_path / "flow.yaml"
    flow.write_text(
        """
version: 1
name: cli-boot-junit
device:
  wait_for_boot: true
steps:
  - action: back
""".strip(),
        encoding="utf-8",
    )
    junit = tmp_path / "artifacts" / "junit.xml"

    code = main(
        [
            "run",
            str(flow),
            "--output",
            str(tmp_path / "runs"),
            "--junit-xml",
            str(junit),
            "--boot-timeout",
            "1",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["data"]["junit_path"] == str(junit.resolve())
    assert payload["data"]["environment"]["boot"]["ready"] is True
    assert ET.parse(junit).getroot().tag == "testsuites"


def test_install_cli_verifies_package_identity(
    fake_tools: dict[str, Path], apk_file: Path, capsys
) -> None:
    code = main(
        [
            "install",
            str(apk_file),
            "--expected-package",
            "com.example.app",
            "--expected-version-code",
            "42",
            "--expected-version-name",
            "1.2.3",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["data"]["package_identity"]["package"] == "com.example.app"
    assert payload["data"]["package_identity"]["version_code"] == 42
    assert payload["data"]["package_identity"]["version_name"] == "1.2.3"


def test_install_cli_rejects_version_expectation_without_package(
    fake_tools: dict[str, Path], apk_file: Path, capsys
) -> None:
    code = main(
        [
            "install",
            str(apk_file),
            "--expected-version-code",
            "42",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 2
    assert payload["error"]["type"] == "config_error"
    assert "expected-package" in payload["error"]["message"]
    assert not (fake_tools["adb_state"] / "adb-commands.jsonl").exists()
    assert not (fake_tools["mumu_state"] / "mumu-commands.jsonl").exists()


def test_install_cli_mismatch_returns_device_error(
    fake_tools: dict[str, Path],
    apk_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    monkeypatch.setenv("FAKE_ADB_VERSION_CODE", "43")
    code = main(
        [
            "install",
            str(apk_file),
            "--expected-package",
            "com.example.app",
            "--expected-version-code",
            "42",
            "--adb",
            str(fake_tools["adb"]),
            "--mumumanager",
            str(fake_tools["manager"]),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert payload["error"]["type"] == "device_error"
    assert "versionCode" in payload["error"]["hint"]
