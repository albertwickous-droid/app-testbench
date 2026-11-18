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


def test_open_action_defaults_package_and_validates_mime(tmp_path: Path) -> None:
    path = tmp_path / "open.yaml"
    path.write_text(
        """
version: 1
device:
  package: com.example.app
steps:
  - action: open
    uri: http://127.0.0.1:18765/
    mime_type: Text/HTML
""".strip(),
        encoding="utf-8",
    )

    flow = load_flow(path)
    assert flow.steps[0].params == {
        "uri": "http://127.0.0.1:18765/",
        "package": "com.example.app",
        "mime_type": "text/html",
    }


def test_open_action_rejects_unsafe_uri(tmp_path: Path) -> None:
    path = tmp_path / "open.yaml"
    path.write_text(
        """
version: 1
steps:
  - action: open
    uri: javascript:alert(1)
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="Unsupported URI scheme"):
        load_flow(path)


def test_reverse_port_action_is_normalized(tmp_path: Path) -> None:
    path = tmp_path / "reverse.yaml"
    path.write_text(
        """
version: 1
setup:
  - action: reverse-port
    port: 18765
    local_port: 18766
teardown:
  - action: reverse_port
    port: 18765
    remove: true
""".strip(),
        encoding="utf-8",
    )
    flow = load_flow(path)
    assert flow.setup[0].action == "reverse_port"
    assert flow.setup[0].params == {
        "port": 18765,
        "local_port": 18766,
        "remove": False,
    }
    assert flow.teardown[0].params == {"port": 18765, "remove": True}


def test_clear_data_and_orientation_actions(tmp_path: Path) -> None:
    path = tmp_path / "device-state.yaml"
    path.write_text(
        """
version: 1
device:
  package: com.example.app
setup:
  - action: clear-data
  - action: orientation
    mode: Portrait
""".strip(),
        encoding="utf-8",
    )
    flow = load_flow(path)
    assert flow.setup[0].params == {"package": "com.example.app"}
    assert flow.setup[1].params == {"mode": "portrait"}


def test_orientation_action_rejects_unknown_mode(tmp_path: Path) -> None:
    path = tmp_path / "orientation.yaml"
    path.write_text(
        "version: 1\nsteps:\n  - action: orientation\n    mode: sideways\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="portrait, landscape, or auto"):
        load_flow(path)


def test_tap_text_and_clear_text_are_normalized(tmp_path: Path) -> None:
    path = tmp_path / "selector.yaml"
    path.write_text(
        """
version: 1
steps:
  - action: tap-text
    text: Search
    field: content-desc
    match: exact
    index: 1
    timeout: 5
    interval: 0.2
    optional: true
  - action: clear-text
    count: 12
""".strip(),
        encoding="utf-8",
    )

    flow = load_flow(path)

    assert flow.steps[0].action == "tap_text"
    assert flow.steps[0].params == {
        "text": "Search",
        "field": "content-desc",
        "match": "exact",
        "index": 1,
        "timeout": 5.0,
        "interval": 0.2,
        "ignore_case": False,
        "optional": True,
    }
    assert flow.steps[1].params == {"count": 12}


def test_tap_text_rejects_unknown_match_mode(tmp_path: Path) -> None:
    path = tmp_path / "selector.yaml"
    path.write_text(
        """
version: 1
steps:
  - action: tap_text
    text: Search
    match: fuzzy
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(FlowError, match="exact or contains"):
        load_flow(path)


def test_wait_for_text_normalizes_anr_recovery(tmp_path: Path) -> None:
    path = tmp_path / "wait-anr.yaml"
    path.write_text(
        """
version: 1
steps:
  - action: wait_for_text
    text: Ready
    recover_anr: true
""".strip(),
        encoding="utf-8",
    )

    flow = load_flow(path)

    assert flow.steps[0].params["recover_anr"] is True


def test_activity_wait_and_logcat_assertion_are_normalized(tmp_path: Path) -> None:
    path = tmp_path / "activity-logcat.yaml"
    path.write_text(
        """
version: 1
steps:
  - action: wait-for-activity
    activity: org.example/.PlayerActivity
    timeout: 20
    interval: 0.25
  - action: assert-logcat-contains
    text: "Creating an input"
    lines: 10000
    ignore_case: true
""".strip(),
        encoding="utf-8",
    )

    flow = load_flow(path)

    assert flow.steps[0].action == "wait_for_activity"
    assert flow.steps[0].params == {
        "activity": "org.example/.PlayerActivity",
        "timeout": 20.0,
        "interval": 0.25,
    }
    assert flow.steps[1].action == "assert_logcat_contains"
    assert flow.steps[1].params == {
        "text": "Creating an input",
        "lines": 10000,
        "ignore_case": True,
    }


def test_activity_wait_requires_a_full_component(tmp_path: Path) -> None:
    path = tmp_path / "activity-short.yaml"
    path.write_text(
        "version: 1\nsteps:\n  - action: wait_for_activity\n    activity: MainActivity\n",
        encoding="utf-8",
    )

    with pytest.raises(FlowError, match="must be a full component"):
        load_flow(path)


def test_variables_file_and_cli_overrides_resolve_typed_values(tmp_path: Path) -> None:
    flow_path = tmp_path / "flow.yaml"
    flow_path.write_text(
        """
version: 1
name: ${FLOW_NAME}
device:
  package: ${APP_PACKAGE}
steps:
  - action: launch
  - action: wait
    seconds: ${WAIT_SECONDS}
""".strip(),
        encoding="utf-8",
    )
    variables_path = tmp_path / "vars.yaml"
    variables_path.write_text(
        "FLOW_NAME: variable-smoke\nAPP_PACKAGE: com.example.fromfile\nWAIT_SECONDS: 1.25\n",
        encoding="utf-8",
    )
    from app_testbench.flow import resolve_variables

    variables = resolve_variables(
        vars_files=[variables_path],
        cli_vars=["APP_PACKAGE=com.example.cli"],
        environ={},
    )
    flow = load_flow(flow_path, variables=variables, environ={})
    assert flow.name == "variable-smoke"
    assert flow.device["package"] == "com.example.cli"
    assert flow.steps[1].params["seconds"] == 1.25
    assert flow.variable_names == ["APP_PACKAGE", "FLOW_NAME", "WAIT_SECONDS"]


def test_variable_file_rejects_nested_values(tmp_path: Path) -> None:
    from app_testbench.flow import load_variables_file

    path = tmp_path / "vars.json"
    path.write_text(json.dumps({"nested": {"value": 1}}), encoding="utf-8")
    with pytest.raises(FlowError, match="must be a string, number, or boolean"):
        load_variables_file(path)


def test_duplicate_cli_variable_is_rejected() -> None:
    from app_testbench.flow import parse_cli_variables

    with pytest.raises(FlowError, match="Duplicate --var"):
        parse_cli_variables(["NAME=first", "NAME=second"])


def test_flow_timeout_seconds_is_validated_and_serialized(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\ntimeout_seconds: 2.5\nsteps:\n  - action: back\n",
        encoding="utf-8",
    )
    flow = load_flow(path)
    assert flow.timeout_seconds == 2.5
    assert flow.to_dict()["timeout_seconds"] == 2.5


def test_flow_timeout_rejects_too_small_values(tmp_path: Path) -> None:
    path = tmp_path / "flow.yaml"
    path.write_text(
        "version: 1\ntimeout_seconds: 0.01\nsteps:\n  - action: back\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match=r"between 0\.1 and 86400"):
        load_flow(path)


def test_wait_for_text_gone_is_normalized(tmp_path: Path) -> None:
    path = tmp_path / "gone.yaml"
    path.write_text(
        """
version: 1
steps:
  - action: wait-for-text-gone
    text: Loading
    timeout: 3
    interval: 0.2
    ignore_case: true
""".strip(),
        encoding="utf-8",
    )
    flow = load_flow(path)
    assert flow.steps[0].action == "wait_for_text_gone"
    assert flow.steps[0].params == {
        "text": "Loading",
        "timeout": 3.0,
        "interval": 0.2,
        "ignore_case": True,
        "recover_anr": False,
    }


def test_install_sha256_is_validated(tmp_path: Path) -> None:
    path = tmp_path / "install.yaml"
    path.write_text(
        """
version: 1
setup:
  - action: install
    apk: app.apk
    sha256: ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789
""".strip(),
        encoding="utf-8",
    )
    flow = load_flow(path)
    assert (
        flow.setup[0].params["sha256"]
        == "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    )


def test_install_sha256_rejects_invalid_digest(tmp_path: Path) -> None:
    path = tmp_path / "install.yaml"
    path.write_text(
        "version: 1\nsetup:\n  - action: install\n    apk: app.apk\n    sha256: not-a-digest\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="SHA-256"):
        load_flow(path)


def test_report_redaction_patterns_are_validated_and_not_serialized(tmp_path: Path) -> None:
    path = tmp_path / "redact.yaml"
    path.write_text(
        """
version: 1
report:
  redact:
    - secret-value
  redact_replacement: "[MASKED]"
steps:
  - action: back
""".strip(),
        encoding="utf-8",
    )
    flow = load_flow(path)
    public = flow.to_dict()["report"]
    assert flow.report["redact"] == ["secret-value"]
    assert "redact" not in public
    assert public["redact_pattern_count"] == 1


def test_report_redaction_rejects_non_list_values(tmp_path: Path) -> None:
    path = tmp_path / "redact.yaml"
    path.write_text(
        "version: 1\nreport:\n  redact: secret-value\nsteps:\n  - action: back\n",
        encoding="utf-8",
    )
    with pytest.raises(FlowError, match="redact must be a list"):
        load_flow(path)
