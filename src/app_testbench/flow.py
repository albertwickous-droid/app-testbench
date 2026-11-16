"""JSON/YAML flow loading, environment expansion, and strict validation."""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app_testbench.device import (
    normalize_keyevent,
    validate_activity,
    validate_mime_type,
    validate_open_uri,
    validate_package,
    validate_port,
)
from app_testbench.errors import FlowError, RunnerError

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_ACTION_ALIASES = {
    "dump-ui": "dump_ui",
    "key-event": "keyevent",
    "assert-ui-contains": "assert_ui_contains",
    "assert-ui-not-contains": "assert_ui_not_contains",
    "wait-for-text": "wait_for_text",
    "open-url": "open",
    "reverse-port": "reverse_port",
    "clear-data": "clear_app_data",
    "clear-app-data": "clear_app_data",
    "tap-text": "tap_text",
    "clear-text": "clear_text",
}
_ACTION_SPECS: dict[str, frozenset[str]] = {
    "install": frozenset(
        {
            "apk",
            "reinstall",
            "grant_permissions",
            "expected_package",
            "expected_version_code",
            "expected_version_name",
        }
    ),
    "launch": frozenset({"package", "activity"}),
    "open": frozenset({"uri", "package", "mime_type"}),
    "close": frozenset({"package"}),
    "clear_app_data": frozenset({"package"}),
    "orientation": frozenset({"mode"}),
    "reverse_port": frozenset({"port", "local_port", "remove"}),
    "tap": frozenset({"x", "y"}),
    "tap_text": frozenset(
        {"text", "field", "match", "index", "timeout", "interval", "ignore_case", "optional"}
    ),
    "clear_text": frozenset({"count"}),
    "swipe": frozenset({"x1", "y1", "x2", "y2", "duration_ms"}),
    "text": frozenset({"text"}),
    "keyevent": frozenset({"key"}),
    "back": frozenset(),
    "home": frozenset(),
    "wait": frozenset({"seconds"}),
    "screenshot": frozenset({"label"}),
    "dump_ui": frozenset({"label"}),
    "logcat": frozenset({"label", "lines"}),
    "assert_ui_contains": frozenset({"text", "ignore_case"}),
    "assert_ui_not_contains": frozenset({"text", "ignore_case"}),
    "wait_for_text": frozenset({"text", "timeout", "interval", "ignore_case", "recover_anr"}),
}
_STEP_KEYS = frozenset({"action", "id", "name", "description", "continue_on_error", "screenshot"})
_DEFAULT_NAMES = {
    "install": "Install APK",
    "launch": "Launch app",
    "open": "Open URI",
    "close": "Close app",
    "clear_app_data": "Clear app data",
    "orientation": "Set screen orientation",
    "reverse_port": "Configure ADB reverse port",
    "tap": "Tap",
    "tap_text": "Tap visible UI text",
    "clear_text": "Clear text input",
    "swipe": "Swipe",
    "text": "Enter text",
    "keyevent": "Press key",
    "back": "Press back",
    "home": "Press home",
    "wait": "Wait",
    "screenshot": "Capture screenshot",
    "dump_ui": "Dump UI hierarchy",
    "logcat": "Capture logcat",
    "assert_ui_contains": "Assert UI contains text",
    "assert_ui_not_contains": "Assert UI does not contain text",
    "wait_for_text": "Wait for UI text",
}
_REPORT_DEFAULTS: dict[str, Any] = {
    "title": None,
    "capture_screenshots": "failures",
    "collect_logcat": True,
    "clear_logcat": False,
    "include_ui_xml": True,
    "max_log_chars": 200_000,
}


@dataclass(slots=True)
class FlowStep:
    id: str
    name: str
    action: str
    section: str
    params: dict[str, Any] = field(default_factory=dict)
    continue_on_error: bool = False
    screenshot: bool = False
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "action": self.action,
            "section": self.section,
            "params": self.params,
            "continue_on_error": self.continue_on_error,
            "screenshot": self.screenshot,
            "description": self.description,
        }


@dataclass(slots=True)
class Flow:
    path: Path
    name: str
    description: str = ""
    device: dict[str, Any] = field(default_factory=dict)
    setup: list[FlowStep] = field(default_factory=list)
    steps: list[FlowStep] = field(default_factory=list)
    teardown: list[FlowStep] = field(default_factory=list)
    report: dict[str, Any] = field(default_factory=dict)

    @property
    def all_steps(self) -> list[FlowStep]:
        return [*self.setup, *self.steps, *self.teardown]

    @property
    def step_count(self) -> int:
        return len(self.setup) + len(self.steps) + len(self.teardown)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "name": self.name,
            "description": self.description,
            "device": self.device,
            "setup": [step.to_dict() for step in self.setup],
            "steps": [step.to_dict() for step in self.steps],
            "teardown": [step.to_dict() for step in self.teardown],
            "report": self.report,
            "step_count": self.step_count,
        }


def _expand_environment(value: Any, *, path: str, missing: set[str]) -> Any:
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in os.environ:
                missing.add(name)
                return match.group(0)
            return os.environ[name]

        return _ENV_PATTERN.sub(replace, value)
    if isinstance(value, list):
        return [
            _expand_environment(item, path=f"{path}[{index}]", missing=missing)
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        return {
            key: _expand_environment(item, path=f"{path}.{key}", missing=missing)
            for key, item in value.items()
        }
    return value


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _read_document(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise FlowError(f"Could not read flow: {path}") from exc
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            return json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
        except ValueError as exc:
            raise FlowError(f"Could not parse flow: {path}", hint=str(exc)) from exc
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise FlowError(
                "PyYAML is required for YAML flows.",
                hint='Install with `pip install "app-testbench"`.',
            ) from exc

        class UniqueKeyLoader(yaml.SafeLoader):
            def construct_mapping(self, node, deep=False):
                seen = set()
                for key_node, _ in node.value:
                    if key_node.tag == "tag:yaml.org,2002:merge":
                        continue
                    key = self.construct_object(key_node, deep=deep)
                    try:
                        duplicate = key in seen
                    except TypeError:
                        continue
                    if duplicate:
                        raise yaml.constructor.ConstructorError(
                            "while constructing a mapping",
                            node.start_mark,
                            f"found duplicate key {key!r}",
                            key_node.start_mark,
                        )
                    seen.add(key)
                return super().construct_mapping(node, deep=deep)

        loader = UniqueKeyLoader(text)
        try:
            return loader.get_single_data()
        except yaml.YAMLError as exc:
            raise FlowError(f"Could not parse flow: {path}", hint=str(exc)) from exc
        finally:
            loader.dispose()
    raise FlowError(
        f"Unsupported flow extension: {suffix or '<none>'}",
        hint="Use a .yaml, .yml, or .json file.",
    )


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FlowError(f"{field_name} must be a mapping/object")
    non_string_keys = [key for key in value if not isinstance(key, str)]
    if non_string_keys:
        rendered = ", ".join(sorted(repr(key) for key in non_string_keys))
        raise FlowError(f"{field_name} field names must be strings; found: {rendered}")
    return value


def _sequence(value: Any, *, field_name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise FlowError(f"{field_name} must be a list")
    return value


def _string(value: Any, *, field_name: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise FlowError(f"{field_name} must be a string")
    result = value.strip()
    if not result and not allow_empty:
        raise FlowError(f"{field_name} cannot be empty")
    return result


def _preserve_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise FlowError(f"{field_name} must be a string")
    if not value:
        raise FlowError(f"{field_name} cannot be empty")
    return value


def _bool(value: Any, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise FlowError(f"{field_name} must be a boolean")


def _integer(value: Any, *, field_name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise FlowError(f"{field_name} must be an integer")
    if isinstance(value, float) and not value.is_integer():
        raise FlowError(f"{field_name} must be an integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise FlowError(f"{field_name} must be an integer") from exc
    if result < minimum or result > maximum:
        raise FlowError(f"{field_name} must be between {minimum} and {maximum}")
    return result


def _number(value: Any, *, field_name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise FlowError(f"{field_name} must be a number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise FlowError(f"{field_name} must be a number") from exc
    if not math.isfinite(result):
        raise FlowError(f"{field_name} must be a finite number")
    if result < minimum or result > maximum:
        raise FlowError(f"{field_name} must be between {minimum:g} and {maximum:g}")
    return result


def _normalize_step(
    raw_value: Any,
    *,
    section: str,
    index: int,
    base_dir: Path,
    default_package: str | None,
    seen_ids: set[str],
) -> FlowStep:
    location = f"{section}[{index}]"
    raw = _mapping(raw_value, field_name=location)
    if "action" not in raw:
        raise FlowError(f"{location}.action is required")
    action_raw = _string(raw["action"], field_name=f"{location}.action").lower()
    action = _ACTION_ALIASES.get(action_raw, action_raw.replace("-", "_"))
    if action not in _ACTION_SPECS:
        supported = ", ".join(sorted(_ACTION_SPECS))
        raise FlowError(
            f"Unknown action {action_raw!r} at {location}.",
            hint=f"Supported actions: {supported}",
        )

    allowed = _STEP_KEYS | _ACTION_SPECS[action]
    unknown = set(raw) - allowed
    if unknown:
        raise FlowError(
            f"Unknown field(s) at {location}: {', '.join(sorted(unknown))}",
            hint="Check the flow reference for the fields accepted by this action.",
        )

    step_id_raw = raw.get("id")
    step_id = (
        f"{section}-{index + 1}"
        if step_id_raw is None
        else _string(step_id_raw, field_name=f"{location}.id")
    )
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", step_id):
        raise FlowError(f"{location}.id may only contain letters, numbers, '.', '_' and '-'")
    if step_id in seen_ids:
        raise FlowError(f"Duplicate step id: {step_id}")
    seen_ids.add(step_id)

    name_raw = raw.get("name")
    name = (
        _DEFAULT_NAMES[action]
        if name_raw is None
        else _string(name_raw, field_name=f"{location}.name")
    )
    description = raw.get("description")
    if description is not None:
        description = _string(description, field_name=f"{location}.description")

    params = {key: value for key, value in raw.items() if key in _ACTION_SPECS[action]}
    required = {
        "install": {"apk"},
        "launch": set() if default_package else {"package"},
        "open": {"uri"},
        "close": set() if default_package else {"package"},
        "clear_app_data": set() if default_package else {"package"},
        "orientation": {"mode"},
        "reverse_port": {"port"},
        "tap": {"x", "y"},
        "tap_text": {"text"},
        "swipe": {"x1", "y1", "x2", "y2"},
        "text": {"text"},
        "keyevent": {"key"},
        "wait": {"seconds"},
        "assert_ui_contains": {"text"},
        "assert_ui_not_contains": {"text"},
        "wait_for_text": {"text"},
    }.get(action, set())
    missing = required - set(params)
    if missing:
        raise FlowError(f"{location} is missing: {', '.join(sorted(missing))}")

    if action == "install":
        apk_value = _string(params["apk"], field_name=f"{location}.apk")
        apk = Path(os.path.expandvars(os.path.expanduser(apk_value)))
        params["apk"] = str(apk if apk.is_absolute() else (base_dir / apk).resolve())
        params["reinstall"] = _bool(
            params.get("reinstall", True), field_name=f"{location}.reinstall"
        )
        params["grant_permissions"] = _bool(
            params.get("grant_permissions", False),
            field_name=f"{location}.grant_permissions",
        )
        if params.get("expected_package") is not None:
            try:
                params["expected_package"] = validate_package(
                    _string(
                        params["expected_package"],
                        field_name=f"{location}.expected_package",
                    )
                )
            except RunnerError as exc:
                raise FlowError(str(exc)) from exc
        if params.get("expected_version_code") is not None:
            params["expected_version_code"] = _integer(
                params["expected_version_code"],
                field_name=f"{location}.expected_version_code",
                minimum=1,
                maximum=2_147_483_647,
            )
        if params.get("expected_version_name") is not None:
            params["expected_version_name"] = _string(
                params["expected_version_name"],
                field_name=f"{location}.expected_version_name",
            )
        has_version_expectation = (
            params.get("expected_version_code") is not None
            or params.get("expected_version_name") is not None
        )
        if params.get("expected_package") is None and has_version_expectation:
            if default_package is None:
                raise FlowError(
                    f"{location}.expected_package is required when version expectations are set",
                    hint="Add expected_package or a device.package default.",
                )
            params["expected_package"] = default_package
    elif action in {"launch", "open", "close", "clear_app_data"}:
        package = params.get("package", default_package)
        if action == "open" and package is None:
            params.pop("package", None)
        else:
            try:
                params["package"] = validate_package(
                    _string(package, field_name=f"{location}.package")
                )
            except RunnerError as exc:
                raise FlowError(str(exc)) from exc
        if action == "launch" and params.get("activity") is not None:
            try:
                params["activity"] = validate_activity(
                    _string(params["activity"], field_name=f"{location}.activity")
                )
            except RunnerError as exc:
                raise FlowError(str(exc), hint=exc.hint) from exc
        if action == "open":
            try:
                params["uri"] = validate_open_uri(
                    _string(params["uri"], field_name=f"{location}.uri")
                )
                if params.get("mime_type") is not None:
                    params["mime_type"] = validate_mime_type(
                        _string(params["mime_type"], field_name=f"{location}.mime_type")
                    )
            except RunnerError as exc:
                raise FlowError(str(exc), hint=exc.hint) from exc
    elif action == "orientation":
        mode = _string(params["mode"], field_name=f"{location}.mode").lower()
        if mode not in {"portrait", "landscape", "auto"}:
            raise FlowError(f"{location}.mode must be portrait, landscape, or auto")
        params["mode"] = mode
    elif action == "reverse_port":
        try:
            params["port"] = validate_port(
                _integer(
                    params["port"],
                    field_name=f"{location}.port",
                    minimum=1,
                    maximum=65_535,
                ),
                name=f"{location}.port",
            )
            if params.get("local_port") is not None:
                params["local_port"] = validate_port(
                    _integer(
                        params["local_port"],
                        field_name=f"{location}.local_port",
                        minimum=1,
                        maximum=65_535,
                    ),
                    name=f"{location}.local_port",
                )
        except RunnerError as exc:
            raise FlowError(str(exc)) from exc
        params["remove"] = _bool(params.get("remove", False), field_name=f"{location}.remove")
        if params["remove"] and "local_port" in params:
            raise FlowError(f"{location}.local_port cannot be used when remove is true")
    elif action == "tap":
        params["x"] = _integer(params["x"], field_name=f"{location}.x", minimum=0, maximum=100_000)
        params["y"] = _integer(params["y"], field_name=f"{location}.y", minimum=0, maximum=100_000)
    elif action == "tap_text":
        params["text"] = _string(params["text"], field_name=f"{location}.text")
        field = _string(params.get("field", "any"), field_name=f"{location}.field").lower()
        if field not in {"any", "text", "content-desc"}:
            raise FlowError(f"{location}.field must be any, text, or content-desc")
        params["field"] = field
        match = _string(params.get("match", "contains"), field_name=f"{location}.match").lower()
        if match not in {"exact", "contains"}:
            raise FlowError(f"{location}.match must be exact or contains")
        params["match"] = match
        params["index"] = _integer(
            params.get("index", 0), field_name=f"{location}.index", minimum=0, maximum=100
        )
        params["timeout"] = _number(
            params.get("timeout", 10),
            field_name=f"{location}.timeout",
            minimum=1,
            maximum=600,
        )
        params["interval"] = _number(
            params.get("interval", 0.5),
            field_name=f"{location}.interval",
            minimum=0.1,
            maximum=30,
        )
        params["ignore_case"] = _bool(
            params.get("ignore_case", False),
            field_name=f"{location}.ignore_case",
        )
        params["optional"] = _bool(
            params.get("optional", False),
            field_name=f"{location}.optional",
        )
    elif action == "clear_text":
        params["count"] = _integer(
            params.get("count", 40),
            field_name=f"{location}.count",
            minimum=1,
            maximum=500,
        )
    elif action == "swipe":
        for key in ("x1", "y1", "x2", "y2"):
            params[key] = _integer(
                params[key], field_name=f"{location}.{key}", minimum=0, maximum=100_000
            )
        params["duration_ms"] = _integer(
            params.get("duration_ms", 300),
            field_name=f"{location}.duration_ms",
            minimum=1,
            maximum=600_000,
        )
    elif action == "text":
        params["text"] = _preserve_string(params["text"], field_name=f"{location}.text")
    elif action == "keyevent":
        try:
            params["key"] = normalize_keyevent(_string(params["key"], field_name=f"{location}.key"))
        except RunnerError as exc:
            raise FlowError(str(exc)) from exc
    elif action == "wait":
        params["seconds"] = _number(
            params["seconds"],
            field_name=f"{location}.seconds",
            minimum=0,
            maximum=3600,
        )
    elif action in {"screenshot", "dump_ui"}:
        if params.get("label") is not None:
            params["label"] = _string(params["label"], field_name=f"{location}.label")
    elif action == "logcat":
        params["lines"] = _integer(
            params.get("lines", 1000),
            field_name=f"{location}.lines",
            minimum=1,
            maximum=100_000,
        )
        if params.get("label") is not None:
            params["label"] = _string(params["label"], field_name=f"{location}.label")
    elif action in {"assert_ui_contains", "assert_ui_not_contains"}:
        params["text"] = _string(params["text"], field_name=f"{location}.text")
        params["ignore_case"] = _bool(
            params.get("ignore_case", False),
            field_name=f"{location}.ignore_case",
        )
    elif action == "wait_for_text":
        params["text"] = _string(params["text"], field_name=f"{location}.text")
        params["timeout"] = _number(
            params.get("timeout", 10),
            field_name=f"{location}.timeout",
            minimum=1,
            maximum=600,
        )
        params["interval"] = _number(
            params.get("interval", 0.5),
            field_name=f"{location}.interval",
            minimum=0.1,
            maximum=30,
        )
        params["ignore_case"] = _bool(
            params.get("ignore_case", False),
            field_name=f"{location}.ignore_case",
        )
        params["recover_anr"] = _bool(
            params.get("recover_anr", False),
            field_name=f"{location}.recover_anr",
        )

    return FlowStep(
        id=step_id,
        name=name,
        action=action,
        section=section,
        params=params,
        continue_on_error=_bool(
            raw.get("continue_on_error", False),
            field_name=f"{location}.continue_on_error",
        ),
        screenshot=_bool(raw.get("screenshot", False), field_name=f"{location}.screenshot"),
        description=description,
    )


def load_flow(path_value: str | Path) -> Flow:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise FlowError(f"Flow file does not exist: {path}")
    raw = _read_document(path)
    missing: set[str] = set()
    raw = _expand_environment(raw, path="$", missing=missing)
    if missing:
        raise FlowError(
            f"Missing environment variable(s): {', '.join(sorted(missing))}",
            hint="Set them before running, for example `$env:APP_PACKAGE='com.example.app'`.",
        )
    root = _mapping(raw, field_name="$")
    allowed_root = {
        "version",
        "name",
        "description",
        "device",
        "setup",
        "steps",
        "teardown",
        "report",
    }
    unknown_root = set(root) - allowed_root
    if unknown_root:
        raise FlowError(f"Unknown top-level field(s): {', '.join(sorted(unknown_root))}")

    version = root.get("version", 1)
    if str(version) != "1":
        raise FlowError(f"Unsupported flow version: {version!r}", hint="Use version: 1")

    name = root.get("name")
    if name is None:
        name = path.stem
    name = _string(name, field_name="name")
    description = _string(root.get("description", ""), field_name="description", allow_empty=True)

    device_raw = _mapping(root.get("device", {}), field_name="device")
    allowed_device = {"instance", "serial", "package", "wait_for_boot", "boot_timeout"}
    unknown_device = set(device_raw) - allowed_device
    if unknown_device:
        raise FlowError(f"Unknown device field(s): {', '.join(sorted(unknown_device))}")
    device: dict[str, Any] = {}
    if device_raw.get("instance") is not None:
        device["instance"] = _integer(
            device_raw["instance"], field_name="device.instance", minimum=0, maximum=999
        )
    if device_raw.get("serial") is not None:
        serial = _string(device_raw["serial"], field_name="device.serial")
        if any(character.isspace() for character in serial):
            raise FlowError("device.serial cannot contain whitespace")
        device["serial"] = serial
    if device_raw.get("package") is not None:
        try:
            device["package"] = validate_package(
                _string(device_raw["package"], field_name="device.package")
            )
        except RunnerError as exc:
            raise FlowError(str(exc)) from exc
    if device_raw.get("wait_for_boot") is not None:
        device["wait_for_boot"] = _bool(
            device_raw["wait_for_boot"], field_name="device.wait_for_boot"
        )
    if device_raw.get("boot_timeout") is not None:
        device["boot_timeout"] = _number(
            device_raw["boot_timeout"],
            field_name="device.boot_timeout",
            minimum=0.01,
            maximum=600,
        )

    seen_ids: set[str] = set()
    sections: dict[str, list[FlowStep]] = {}
    for section in ("setup", "steps", "teardown"):
        raw_steps = _sequence(root.get(section, []), field_name=section)
        normalized: list[FlowStep] = []
        for index, item in enumerate(raw_steps):
            normalized.append(
                _normalize_step(
                    item,
                    section=section,
                    index=index,
                    base_dir=path.parent,
                    default_package=device.get("package"),
                    seen_ids=seen_ids,
                )
            )
        sections[section] = normalized

    if not any(sections.values()):
        raise FlowError("Flow must contain at least one setup, steps, or teardown action")

    report_raw = _mapping(root.get("report", {}), field_name="report")
    unknown_report = set(report_raw) - set(_REPORT_DEFAULTS)
    if unknown_report:
        raise FlowError(f"Unknown report field(s): {', '.join(sorted(unknown_report))}")
    report = dict(_REPORT_DEFAULTS)
    report.update(report_raw)
    capture_screenshots = report["capture_screenshots"]
    if not isinstance(capture_screenshots, str) or capture_screenshots not in {
        "all",
        "failures",
        "manual",
    }:
        raise FlowError("report.capture_screenshots must be one of: all, failures, manual")
    for key in ("collect_logcat", "clear_logcat", "include_ui_xml"):
        report[key] = _bool(report[key], field_name=f"report.{key}")
    report["max_log_chars"] = _integer(
        report["max_log_chars"],
        field_name="report.max_log_chars",
        minimum=1_000,
        maximum=10_000_000,
    )
    if report["title"] is not None:
        report["title"] = _string(report["title"], field_name="report.title")
    else:
        report["title"] = name

    return Flow(
        path=path,
        name=name,
        description=description,
        device=device,
        setup=sections["setup"],
        steps=sections["steps"],
        teardown=sections["teardown"],
        report=report,
    )


STARTER_YAML = """\
version: 1
name: login-smoke
description: Install, launch, and verify the first screen.
device:
  instance: 0
  package: com.example.app

report:
  capture_screenshots: all
  collect_logcat: true

setup:
  - name: Install APK
    action: install
    apk: ./app.apk

steps:
  - name: Launch app
    action: launch
  - name: Wait for first screen
    action: wait_for_text
    text: Login
    timeout: 20
  - name: Screenshot first screen
    action: screenshot
    label: first-screen
  - name: Dump UI hierarchy
    action: dump_ui
    label: first-screen

teardown:
  - name: Capture final logcat
    action: logcat
    label: final
    lines: 2000
"""


def starter_document(*, json_format: bool = False) -> str:
    if not json_format:
        return STARTER_YAML
    flow = {
        "version": 1,
        "name": "login-smoke",
        "device": {"instance": 0, "package": "com.example.app"},
        "report": {"capture_screenshots": "all", "collect_logcat": True},
        "setup": [{"name": "Install APK", "action": "install", "apk": "./app.apk"}],
        "steps": [
            {"name": "Launch app", "action": "launch"},
            {
                "name": "Wait for first screen",
                "action": "wait_for_text",
                "text": "Login",
                "timeout": 20,
            },
            {
                "name": "Screenshot first screen",
                "action": "screenshot",
                "label": "first-screen",
            },
        ],
        "teardown": [{"name": "Capture final logcat", "action": "logcat", "lines": 2000}],
    }
    return json.dumps(flow, ensure_ascii=False, indent=2) + "\n"
