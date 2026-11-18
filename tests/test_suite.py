from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from importlib.resources import files
from pathlib import Path

import pytest

from app_testbench.cli import main
from app_testbench.config import Settings
from app_testbench.errors import ConfigError
from app_testbench.flow import load_flow
from app_testbench.runner import FlowRunner
from app_testbench.suite import load_data_cases, load_suite_definition, run_collection


def _flow(path: Path, name: str, *, tag: str | None = None) -> None:
    tags = f"tags: [{tag}]\n" if tag else ""
    path.write_text(
        f"version: 1\nname: {name}\n{tags}steps:\n  - action: back\n",
        encoding="utf-8",
    )


def test_suite_tag_filter_and_aggregate_artifacts(fake_settings: Settings, tmp_path: Path) -> None:
    smoke = tmp_path / "smoke.yaml"
    full = tmp_path / "full.yaml"
    _flow(smoke, "smoke", tag="smoke")
    _flow(full, "full", tag="full")
    suite = tmp_path / "suite.yaml"
    suite.write_text(
        """
version: 1
name: quick-suite
description: quick local checks
flows:
  - smoke.yaml
  - full.yaml
""".strip(),
        encoding="utf-8",
    )

    definition = load_suite_definition(suite, tags=["SMOKE"])
    assert [case.flow.name for case in definition.cases] == ["smoke"]

    collection = run_collection(
        definition.cases,
        fake_settings,
        output_base=tmp_path / "runs",
        name=definition.name,
        kind="suite",
        description=definition.description,
        tags=["SMOKE"],
    )

    assert collection.status == "passed"
    assert collection.payload["summary"]["total"] == 1
    assert collection.payload["cases"][0]["flow"] == "smoke"
    for path in (
        collection.result_path,
        collection.report_path,
        collection.junit_path,
        collection.manifest_path,
    ):
        assert path.is_file()
    junit = ET.parse(collection.junit_path).getroot()
    assert junit.attrib["tests"] == "1"
    assert junit.attrib["failures"] == "0"
    manifest = json.loads(collection.manifest_path.read_text(encoding="utf-8"))
    paths = {item["path"] for item in manifest["files"]}
    assert {"suite-result.json", "suite-report.html", "junit.xml"} <= paths
    assert "manifest.json" not in paths

    jsonschema = pytest.importorskip("jsonschema")
    collection_schema = json.loads(
        files("app_testbench.schemas")
        .joinpath("collection-result-v1.schema.json")
        .read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(collection_schema).validate(collection.payload)


def test_suite_no_matching_tag_is_a_configuration_error(tmp_path: Path) -> None:
    flow = tmp_path / "smoke.yaml"
    _flow(flow, "smoke", tag="smoke")
    suite = tmp_path / "suite.yaml"
    suite.write_text("flows: [smoke.yaml]\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="No suite flows matched"):
        load_suite_definition(suite, tags=["release"])


def test_suite_inline_variables_are_available_to_flow(
    fake_settings: Settings, tmp_path: Path
) -> None:
    flow = tmp_path / "named.yaml"
    flow.write_text(
        "version: 1\nname: ${CASE_NAME}\nsteps:\n  - action: back\n",
        encoding="utf-8",
    )
    suite = tmp_path / "suite.yaml"
    suite.write_text(
        """
version: 1
flows:
  - path: named.yaml
    variables:
      CASE_NAME: checkout
""".strip(),
        encoding="utf-8",
    )

    definition = load_suite_definition(suite)

    assert definition.cases[0].flow.name == "checkout"


def test_data_csv_creates_independent_cases_and_reuses_variables(
    fake_settings: Settings, tmp_path: Path
) -> None:
    flow = tmp_path / "data.yaml"
    flow.write_text(
        "version: 1\nname: data-flow\nsteps:\n  - action: text\n    text: ${VALUE}\n",
        encoding="utf-8",
    )
    data = tmp_path / "cases.csv"
    data.write_text("VALUE\nfirst\nsecond\n", encoding="utf-8")

    cases = load_data_cases(flow, data)
    assert [case.flow.steps[0].params["text"] for case in cases] == ["first", "second"]
    assert [case.flow.variable_names for case in cases] == [["VALUE"], ["VALUE"]]

    collection = run_collection(
        cases,
        fake_settings,
        output_base=tmp_path / "runs",
        name="data-flow-data",
        kind="data",
    )

    assert collection.status == "passed"
    assert collection.payload["summary"]["total"] == 2
    assert [case["data_index"] for case in collection.payload["cases"]] == [1, 2]
    assert collection.junit_path.is_file()


def test_data_json_preserves_typed_values(tmp_path: Path) -> None:
    flow = tmp_path / "wait.yaml"
    flow.write_text(
        "version: 1\nname: wait-flow\nsteps:\n  - action: wait\n    seconds: ${WAIT}\n",
        encoding="utf-8",
    )
    data = tmp_path / "cases.json"
    data.write_text(json.dumps([{"WAIT": 0}, {"WAIT": 1.5}]), encoding="utf-8")

    cases = load_data_cases(flow, data)

    assert [case.flow.steps[0].params["seconds"] for case in cases] == [0.0, 1.5]


def test_data_rejects_duplicate_or_empty_csv_headers(tmp_path: Path) -> None:
    flow = tmp_path / "flow.yaml"
    _flow(flow, "flow")
    for name, content, message in (
        ("duplicate.csv", "A,A\n1,2\n", "unique"),
        ("empty.csv", ",B\n1,2\n", "cannot be empty"),
    ):
        data = tmp_path / name
        data.write_text(content, encoding="utf-8")
        with pytest.raises(ConfigError, match=message):
            load_data_cases(flow, data)


def test_events_jsonl_contains_start_and_end_events(
    fake_settings: Settings, tmp_path: Path
) -> None:
    flow_path = tmp_path / "events.yaml"
    flow_path.write_text(
        "version: 1\nname: events\nsteps:\n  - action: back\n  - action: wait\n    seconds: 0\n",
        encoding="utf-8",
    )
    events = tmp_path / "events.ndjson"

    result = FlowRunner(
        fake_settings,
        load_flow(flow_path),
        output_base=tmp_path / "runs",
        events_path=events,
    ).run()

    assert result.status == "passed"
    records = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in records] == [
        "flow_start",
        "step_start",
        "step_end",
        "step_start",
        "step_end",
        "flow_end",
    ]
    assert all(record["schema_version"] == "1.0" for record in records)
    assert records[2]["step"]["id"] == "steps-1"
    assert records[-1]["summary"]["passed"] == 2

    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        files("app_testbench.schemas").joinpath("events-v1.schema.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    for record in records:
        validator.validate(record)


def test_cli_suite_returns_aggregate_json(
    fake_tools: dict[str, Path], tmp_path: Path, capsys
) -> None:
    flow = tmp_path / "smoke.yaml"
    _flow(flow, "smoke", tag="smoke")
    suite = tmp_path / "suite.yaml"
    suite.write_text("version: 1\nname: cli-suite\nflows: [smoke.yaml]\n", encoding="utf-8")

    code = main(
        [
            "suite",
            str(suite),
            "--tag",
            "smoke",
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

    assert code == 0, payload
    assert payload["ok"] is True
    assert payload["command"] == "suite"
    assert payload["data"]["summary"]["total"] == 1
    assert payload["data"]["cases"][0]["status"] == "passed"


def test_cli_data_run_returns_aggregate_json(
    fake_tools: dict[str, Path], tmp_path: Path, capsys
) -> None:
    flow = tmp_path / "data.yaml"
    flow.write_text(
        "version: 1\nname: cli-data\nsteps:\n  - action: text\n    text: ${VALUE}\n",
        encoding="utf-8",
    )
    data = tmp_path / "cases.csv"
    data.write_text("VALUE\none\ntwo\n", encoding="utf-8")

    code = main(
        [
            "run",
            str(flow),
            "--data",
            str(data),
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
    assert payload["command"] == "run"
    assert payload["data"]["summary"]["total"] == 2
    assert [case["data_index"] for case in payload["data"]["cases"]] == [1, 2]


def test_events_jsonl_marks_failed_steps(fake_settings: Settings, tmp_path: Path) -> None:
    flow_path = tmp_path / "failure-events.yaml"
    flow_path.write_text(
        "version: 1\nname: failure-events\nsteps:\n"
        "  - action: assert_ui_contains\n    text: MISSING_EVENT_TEXT\n",
        encoding="utf-8",
    )
    events = tmp_path / "failure-events.ndjson"

    result = FlowRunner(
        fake_settings,
        load_flow(flow_path),
        output_base=tmp_path / "runs",
        events_path=events,
    ).run()

    assert result.status == "failed"
    records = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    failed = next(record for record in records if record["event"] == "step_end")
    assert failed["status"] == "failed"
    assert failed["error_type"] == "step_failure"
    assert "MISSING_EVENT_TEXT" in failed["error"]
