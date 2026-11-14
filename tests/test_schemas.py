from __future__ import annotations

import json
from importlib.resources import files

import pytest

from app_testbench.cli import _error_payload, _payload
from app_testbench.errors import DeviceError
from app_testbench.models import RunResult, StepResult
from app_testbench.utils import now_iso


def _load_schema(name: str) -> dict:
    return json.loads(files("app_testbench.schemas").joinpath(name).read_text(encoding="utf-8"))


def _result() -> RunResult:
    return RunResult(
        name="schema-smoke",
        status="passed",
        started_at=now_iso(),
        finished_at=now_iso(),
        duration_ms=12,
        environment={"serial": "127.0.0.1:16384"},
        config={},
        steps=[
            StepResult(
                id="steps-1",
                name="Back",
                action="back",
                section="steps",
                status="passed",
                started_at=now_iso(),
                duration_ms=12,
            )
        ],
    )


def test_schema_files_are_valid_draft_2020_12() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    for name in ("result-v1.schema.json", "cli-v1.schema.json"):
        schema = _load_schema(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        jsonschema.Draft202012Validator.check_schema(schema)


def test_result_json_matches_result_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema("result-v1.schema.json")
    validator = jsonschema.Draft202012Validator(schema)

    validator.validate(_result().to_dict())
    legacy = _result().to_dict()
    legacy.pop("junit_path")
    validator.validate(legacy)

    invalid = _result().to_dict()
    invalid["status"] = "unknown"
    assert list(validator.iter_errors(invalid))


def test_cli_success_and_error_envelopes_match_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema("cli-v1.schema.json")
    validator = jsonschema.Draft202012Validator(schema)

    validator.validate(_payload("run", {"status": "passed"}))
    validator.validate(_error_payload("run", DeviceError("boom", hint="retry")))


def test_schemas_are_packaged_resources() -> None:
    package_files = files("app_testbench.schemas")
    assert package_files.joinpath("result-v1.schema.json").is_file()
    assert package_files.joinpath("cli-v1.schema.json").is_file()
