"""Device-free execution planning for dry runs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app_testbench import SCHEMA_VERSION
from app_testbench.config import Settings
from app_testbench.flow import Flow, FlowStep
from app_testbench.utils import now_iso, slugify

_SENSITIVE_PARTS = ("password", "passwd", "secret", "token", "cookie", "authorization", "api_key")


def _mask(value: Any, *, key: str = "") -> Any:
    lowered = key.casefold()
    if any(part in lowered for part in _SENSITIVE_PARTS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(item_key): _mask(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_mask(item) for item in value]
    return value


def _adb_prefix(settings: Settings, serial: str | None) -> list[str]:
    prefix = [str(settings.adb) if settings.adb else "adb"]
    if serial:
        prefix.extend(["-s", serial])
    return prefix


def _step_command(step: FlowStep, *, settings: Settings, serial: str | None) -> list[str]:
    prefix = _adb_prefix(settings, serial)
    params = step.params
    action = step.action
    if action == "install":
        command = [*prefix, "install"]
        if params.get("reinstall", True):
            command.append("-r")
        if params.get("grant_permissions"):
            command.append("-g")
        command.append(str(params.get("apk", "<apk>")))
        return command
    if action == "launch":
        package = str(params.get("package", "<package>"))
        activity = params.get("activity")
        if activity:
            return [*prefix, "shell", "am", "start", "-W", "-n", str(activity)]
        return [
            *prefix,
            "shell",
            "monkey",
            "-p",
            package,
            "-c",
            "android.intent.category.LAUNCHER",
            "1",
        ]
    if action == "open":
        return [
            *prefix,
            "shell",
            "am",
            "start",
            "-W",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            str(params.get("uri", "<uri>")),
        ]
    if action == "close":
        return [*prefix, "shell", "am", "force-stop", str(params.get("package", "<package>"))]
    if action == "clear_app_data":
        return [*prefix, "shell", "pm", "clear", str(params.get("package", "<package>"))]
    if action == "orientation":
        return [
            *prefix,
            "shell",
            "wm",
            "user-rotation",
            "lock",
            "0" if params.get("mode") == "portrait" else "1",
        ]
    if action == "reverse_port":
        if params.get("remove"):
            return [*prefix, "reverse", "--remove", f"tcp:{params.get('port')}"]
        local = params.get("local_port", params.get("port"))
        return [*prefix, "reverse", f"tcp:{params.get('port')}", f"tcp:{local}"]
    if action == "tap":
        return [*prefix, "shell", "input", "tap", str(params.get("x")), str(params.get("y"))]
    if action == "swipe":
        return [
            *prefix,
            "shell",
            "input",
            "swipe",
            *(str(params.get(key)) for key in ("x1", "y1", "x2", "y2")),
            str(params.get("duration_ms", 300)),
        ]
    if action == "text":
        return [*prefix, "shell", "input", "text", str(params.get("text", "<text>"))]
    if action == "keyevent":
        return [*prefix, "shell", "input", "keyevent", str(params.get("key"))]
    if action == "back":
        return [*prefix, "shell", "input", "keyevent", "KEYCODE_BACK"]
    if action == "home":
        return [*prefix, "shell", "input", "keyevent", "KEYCODE_HOME"]
    if action == "screenshot":
        return [*prefix, "exec-out", "screencap", "-p"]
    if action == "dump_ui" or action in {
        "wait_for_text",
        "wait_for_text_gone",
        "wait_for_activity",
        "assert_ui_contains",
        "assert_ui_not_contains",
        "tap_text",
    }:
        return [*prefix, "shell", "uiautomator", "dump", "/sdcard/app_testbench_window.xml"]
    if action == "logcat" or action == "assert_logcat_contains":
        return [*prefix, "logcat", "-d", "-v", "threadtime", "-t", str(params.get("lines", 1000))]
    if action == "wait":
        return ["wait", f"{float(params.get('seconds', 0)):g}s"]
    return [*prefix, "shell", step.action]


def build_execution_plan(
    flow: Flow,
    settings: Settings,
    *,
    output_base: Path,
    wait_for_boot: bool | None = None,
    boot_timeout: float | None = None,
    flow_timeout: float | None = None,
) -> dict[str, Any]:
    """Return a resolved, side-effect-free description of a flow run."""

    instance = (
        settings.instance
        if settings.instance_explicit
        else int(flow.device.get("instance", settings.instance or 0))
    )
    serial = (
        settings.serial
        if settings.serial_explicit
        else flow.device.get("serial") or settings.serial
    )
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    expected_dir = output_base / f"{stamp}-{slugify(flow.name, fallback='run')}"
    steps: list[dict[str, Any]] = []
    for step in flow.all_steps:
        steps.append(
            {
                "id": step.id,
                "name": step.name,
                "section": step.section,
                "action": step.action,
                "command": _step_command(step, settings=settings, serial=serial),
                "params": _mask(step.params),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "dry_run": True,
        "generated_at": now_iso(),
        "flow": _mask(flow.to_dict()),
        "variables": {"names": flow.variable_names},
        "device": {
            "instance": instance,
            "serial": serial,
            "package": flow.device.get("package"),
            "wait_for_boot": bool(
                wait_for_boot
                if wait_for_boot is not None
                else flow.device.get("wait_for_boot", False)
            ),
            "boot_timeout_seconds": boot_timeout
            if boot_timeout is not None
            else flow.device.get("boot_timeout", 60),
        },
        "output_base": str(output_base.resolve()),
        "expected_run_dir": str(expected_dir.resolve()),
        "flow_timeout_seconds": (
            flow_timeout if flow_timeout is not None else flow.timeout_seconds
        ),
        "step_count": len(steps),
        "steps": steps,
    }
