from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app_testbench.errors import FlowError
from app_testbench.flow import load_flow, starter_document


def test_load_yaml_flow_with_defaults(tmp_path: Path) -> None:
    flow_path = tmp_path / "flow.yaml"
    flow_path.write_text(
        """
version: 1
name: smoke
device:
  package: com.example.app
steps:
  - action: launch
  - action: tap
    x: 10
    y: 20
""".strip(),
        encoding="utf-8",
    )
    flow = load_flow(flow_path)
    assert flow.name == "smoke"
    assert flow.steps[0].params["package"] == "com.example.app"
    assert flow.steps[1].params == {"x": 10, "y": 20}
    assert flow.report["capture_screenshots"] == "failures"


def test_json_flow_expands_environment_and_resolves_apk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_PACKAGE", "com.example.demo")
    flow_path = tmp_path / "flow.json"
    flow_path.write_text(
        json.dumps(
            {
                "version": 1,
                "name": "install",
                "device": {"package": "${APP_PACKAGE}", "instance": 2},
                "setup": [{"action": "install", "apk": "demo.apk"}],
                "steps": [{"action": "launch"}],
            }
        ),
        encoding="utf-8",
    )
    flow = load_flow(flow_path)
    assert flow.device["package"] == "com.example.demo"
    assert flow.setup[0].params["apk"] == str((tmp_path / "demo.apk").resolve())


def test_unknown_action_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text("version: 1\nsteps:\n  - action: explode\n", encoding="utf-8")
    with pytest.raises(FlowError, match="Unknown action"):
        load_flow(path)


def test_unknown_step_field_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\nsteps:\n  - action: tap\n    x: 1\n    y: 2\n    typo: true\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="Unknown field"):
        load_flow(path)


def test_invalid_activity_component_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\ndevice:\n  package: com.example.app\n"
        "steps:\n  - action: launch\n    activity: '.MainActivity; id'\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="Invalid activity component"):
        load_flow(path)


def test_fractional_integer_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\nsteps:\n  - action: tap\n    x: 1.5\n    y: 2\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="x must be an integer"):
        load_flow(path)


def test_non_finite_number_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\nsteps:\n  - action: wait\n    seconds: .nan\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="seconds must be a finite number"):
        load_flow(path)


def test_capture_screenshots_rejects_non_string_values(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\nreport:\n  capture_screenshots: []\nsteps:\n  - action: back\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="capture_screenshots must be one of"):
        load_flow(path)


def test_missing_environment_variable_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DOES_NOT_EXIST", raising=False)
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\nsteps:\n  - action: text\n    text: ${DOES_NOT_EXIST}\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="Missing environment"):
        load_flow(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [("id", 123), ("name", False)],
)
def test_step_id_and_name_must_be_strings(tmp_path: Path, field: str, value: object) -> None:
    path = tmp_path / "flow.json"
    path.write_text(
        json.dumps({"version": 1, "steps": [{"action": "back", field: value}]}),
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match=rf"steps\[0\]\.{field} must be a string"):
        load_flow(path)


def test_duplicate_step_ids_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\nsteps:\n  - {id: same, action: back}\n  - {id: same, action: home}\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="Duplicate step id"):
        load_flow(path)


def test_starter_documents_are_valid(tmp_path: Path) -> None:
    for suffix, content in (
        (".yaml", starter_document()),
        (".json", starter_document(json_format=True)),
    ):
        path = tmp_path / f"starter{suffix}"
        path.write_text(content, encoding="utf-8")
        flow = load_flow(path)
        assert flow.name == "login-smoke"
        assert flow.step_count >= 4


def test_repository_examples_are_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = [*sorted((root / "examples").glob("smoke.*")), root / "examples" / "login-search.yaml"]
    for path in paths:
        flow = load_flow(path)
        assert flow.step_count > 0


def test_packaged_skill_matches_canonical_skill() -> None:
    root = Path(__file__).resolve().parents[1]
    canonical = (root / "skills" / "app-testbench" / "SKILL.md").read_text(encoding="utf-8")
    packaged = (root / "src" / "app_testbench" / "skills" / "SKILL.md").read_text(encoding="utf-8")
    assert packaged == canonical


def test_text_action_preserves_surrounding_whitespace(tmp_path: Path) -> None:
    path = tmp_path / "whitespace.yaml"
    path.write_text(
        'version: 1\nsteps:\n  - action: text\n    text: "  hello world  "\n', encoding="utf-8"
    )
    flow = load_flow(path)
    assert flow.steps[0].params["text"] == "  hello world  "


def test_keyevent_is_normalized_and_invalid_keyevent_rejected(tmp_path: Path) -> None:
    path = tmp_path / "keyevent.yaml"
    path.write_text("version: 1\nsteps:\n  - action: keyevent\n    key: enter\n", encoding="utf-8")
    flow = load_flow(path)
    assert flow.steps[0].params["key"] == "KEYCODE_ENTER"

    path.write_text(
        "version: 1\nsteps:\n  - action: keyevent\n    key: 'bad key'\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="Invalid keyevent"):
        load_flow(path)


@pytest.mark.parametrize(
    ("suffix", "content"),
    [
        (".json", '{"version": 1, "steps": [], "steps": []}'),
        (".yaml", "version: 1\nsteps: []\nsteps: []\n"),
    ],
)
def test_duplicate_mapping_keys_are_rejected(tmp_path: Path, suffix: str, content: str) -> None:
    path = tmp_path / f"duplicate{suffix}"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(FlowError, match=r"(?i)duplicate"):
        load_flow(path)


@pytest.mark.parametrize(
    ("field_name", "content"),
    [
        ("$", "version: 1\n1: unknown\nsteps:\n  - action: back\n"),
        (
            "device",
            "version: 1\ndevice:\n  1: unknown\nsteps:\n  - action: back\n",
        ),
        (
            "steps[0]",
            "version: 1\nsteps:\n  - action: back\n    1: unknown\n",
        ),
        (
            "report",
            "version: 1\nreport:\n  1: unknown\nsteps:\n  - action: back\n",
        ),
    ],
)
def test_mapping_field_names_must_be_strings(tmp_path: Path, field_name: str, content: str) -> None:
    path = tmp_path / "numeric-key.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(FlowError, match=rf"{re.escape(field_name)} field names must be strings"):
        load_flow(path)


def test_install_expected_identity_defaults_package_from_device(tmp_path: Path) -> None:
    path = tmp_path / "install.yaml"
    path.write_text(
        """
version: 1
device:
  package: com.example.app
setup:
  - action: install
    apk: ./app.apk
    expected_version_code: 42
    expected_version_name: 1.2.3
""".strip(),
        encoding="utf-8",
    )

    flow = load_flow(path)
    params = flow.setup[0].params
    assert params["expected_package"] == "com.example.app"
    assert params["expected_version_code"] == 42
    assert params["expected_version_name"] == "1.2.3"


def test_install_version_expectation_requires_a_package(tmp_path: Path) -> None:
    path = tmp_path / "install.yaml"
    path.write_text(
        "version: 1\nsetup:\n  - action: install\n    apk: ./app.apk\n"
        "    expected_version_code: 42\n",
        encoding="utf-8",
    )

    with pytest.raises(FlowError, match="expected_package is required"):
        load_flow(path)


def test_install_expected_package_is_validated(tmp_path: Path) -> None:
    path = tmp_path / "install.yaml"
    path.write_text(
        "version: 1\nsetup:\n  - action: install\n    apk: ./app.apk\n"
        "    expected_package: not a package\n",
        encoding="utf-8",
    )

    with pytest.raises(FlowError, match="Invalid Android package"):
        load_flow(path)


def test_device_boot_gate_configuration(tmp_path: Path) -> None:
    path = tmp_path / "boot.yaml"
    path.write_text(
        "version: 1\ndevice:\n  wait_for_boot: true\n  boot_timeout: 2.5\n"
        "steps:\n  - action: back\n",
        encoding="utf-8",
    )

    flow = load_flow(path)
    assert flow.device["wait_for_boot"] is True
    assert flow.device["boot_timeout"] == 2.5
