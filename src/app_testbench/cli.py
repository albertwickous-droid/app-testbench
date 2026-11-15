"""Command-line interface for app-testbench."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback
from pathlib import Path
from typing import Any, NoReturn

from app_testbench import SCHEMA_VERSION, __version__
from app_testbench.config import Settings, build_settings
from app_testbench.device import (
    AndroidDevice,
    encode_input_text,
    normalize_keyevent,
    validate_activity,
    validate_coordinate,
    validate_mime_type,
    validate_open_uri,
    validate_package,
    validate_port,
)
from app_testbench.doctor import collect_doctor_checks
from app_testbench.errors import ConfigError, DeviceError, RunnerError, StepFailure
from app_testbench.flow import load_flow, starter_document
from app_testbench.models import Instance, RunResult
from app_testbench.mumu import MuMuManagerClient
from app_testbench.runner import FlowRunner
from app_testbench.utils import ProcessRunner, atomic_write_text, now_iso, unique_path


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ConfigError(
            f"Invalid command line: {message}",
            hint="Run `app-testbench --help` for usage.",
        )


def _finite_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed):
        raise argparse.ArgumentTypeError("must be a finite number")
    return parsed


def _nonnegative_float(value: str) -> float:
    parsed = _finite_float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def _positive_float(value: str) -> float:
    parsed = _finite_float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def _json_requested(argv: list[str]) -> bool:
    option_tokens = argv
    if "--" in argv:
        option_tokens = argv[: argv.index("--")]
    if "--json" in option_tokens:
        return True
    value = os.environ.get("APP_TESTBENCH_JSON", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _guess_command(argv: list[str]) -> str:
    commands = {
        "doctor",
        "instance",
        "install",
        "launch",
        "open",
        "close",
        "clear-data",
        "orientation",
        "reverse-port",
        "tap",
        "swipe",
        "text",
        "keyevent",
        "screenshot",
        "dump-ui",
        "logcat",
        "validate",
        "run",
        "init",
        "skill-path",
    }
    return next((token for token in argv if token in commands), "cli")


def _common_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(add_help=False)
    # Suppress defaults so subparsers do not clobber options parsed before the command.
    parser.add_argument("--adb", default=argparse.SUPPRESS, help="Path to adb.exe/adb")
    parser.add_argument("--mumumanager", default=argparse.SUPPRESS, help="Path to MuMuManager.exe")
    parser.add_argument(
        "--instance", type=int, default=argparse.SUPPRESS, help="MuMu instance index"
    )
    parser.add_argument(
        "--serial", default=argparse.SUPPRESS, help="ADB serial, for example 127.0.0.1:16384"
    )
    parser.add_argument(
        "--timeout",
        type=_finite_float,
        default=argparse.SUPPRESS,
        help="External command timeout in seconds",
    )
    parser.add_argument(
        "--json", dest="json_output", action="store_true", default=argparse.SUPPRESS
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Show tracebacks for unexpected errors",
    )
    return parser


def build_parser() -> argparse.ArgumentParser:
    common = _common_parser()
    parser = _ArgumentParser(
        prog="app-testbench",
        description="Android automation for NetEase MuMu Player via MuMuManager and ADB.",
        parents=[common],
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser(
        "doctor", parents=[common], help="Check MuMu, ADB, and instance readiness"
    )
    doctor.set_defaults(handler="doctor")

    instance = subparsers.add_parser("instance", parents=[common], help="Manage MuMu instances")
    instance_sub = instance.add_subparsers(dest="instance_command", required=True)
    instance_list = instance_sub.add_parser("list", parents=[common], help="List MuMu instances")
    instance_list.set_defaults(handler="instance_list")
    for name, help_text in (
        ("start", "Start an instance"),
        ("stop", "Shut down an instance"),
        ("restart", "Restart an instance"),
    ):
        command = instance_sub.add_parser(name, parents=[common], help=help_text)
        command.add_argument("index", nargs="?", type=int, help="Instance index (default: global)")
        if name == "start":
            command.add_argument(
                "--wait", type=_nonnegative_float, default=0, help="Wait this many seconds for boot"
            )
        command.set_defaults(handler=f"instance_{name}")

    install = subparsers.add_parser("install", parents=[common], help="Install an APK")
    install.add_argument("apk", type=Path)
    install.add_argument("--no-reinstall", action="store_true", help="Do not pass adb install -r")
    install.add_argument("--grant-permissions", action="store_true", help="Pass adb install -g")
    install.add_argument("--expected-package", help="Verify the installed package name")
    install.add_argument(
        "--expected-version-code",
        type=int,
        help="Verify the installed integer versionCode",
    )
    install.add_argument(
        "--expected-version-name",
        help="Verify the installed versionName string",
    )
    install.set_defaults(handler="install")

    launch = subparsers.add_parser("launch", parents=[common], help="Launch an app")
    launch.add_argument("package")
    launch.add_argument("--activity", help="Activity component, class name, or relative .Activity")
    launch.set_defaults(handler="launch")

    open_uri = subparsers.add_parser(
        "open", parents=[common], help="Open an HTTP(S), file, or content URI"
    )
    open_uri.add_argument("uri")
    open_uri.add_argument("--package", help="Restrict the VIEW intent to one Android package")
    open_uri.add_argument("--mime-type", help="Optional MIME type such as video/mp4")
    open_uri.set_defaults(handler="open")

    close = subparsers.add_parser("close", parents=[common], help="Force-stop an app")
    close.add_argument("package")
    close.set_defaults(handler="close")

    clear_data = subparsers.add_parser(
        "clear-data", parents=[common], help="Clear an app's data and stop its process"
    )
    clear_data.add_argument("package")
    clear_data.set_defaults(handler="clear_app_data")

    orientation = subparsers.add_parser(
        "orientation", parents=[common], help="Lock or reset the device screen orientation"
    )
    orientation.add_argument("mode", choices=["portrait", "landscape", "auto"])
    orientation.set_defaults(handler="orientation")

    reverse_port = subparsers.add_parser(
        "reverse-port", parents=[common], help="Map a device TCP port to a host TCP port"
    )
    reverse_port.add_argument("port", type=int, help="Device-side port")
    reverse_port.add_argument("--local-port", type=int, help="Host-side port (default: same port)")
    reverse_port.add_argument("--remove", action="store_true", help="Remove the mapping")
    reverse_port.set_defaults(handler="reverse_port")

    tap = subparsers.add_parser("tap", parents=[common], help="Tap screen coordinates")
    tap.add_argument("x", type=int)
    tap.add_argument("y", type=int)
    tap.set_defaults(handler="tap")

    swipe = subparsers.add_parser("swipe", parents=[common], help="Swipe between coordinates")
    swipe.add_argument("x1", type=int)
    swipe.add_argument("y1", type=int)
    swipe.add_argument("x2", type=int)
    swipe.add_argument("y2", type=int)
    swipe.add_argument("--duration-ms", type=int, default=300)
    swipe.set_defaults(handler="swipe")

    text = subparsers.add_parser("text", parents=[common], help="Type printable ASCII text")
    text.add_argument("text")
    text.set_defaults(handler="text")

    keyevent = subparsers.add_parser("keyevent", parents=[common], help="Send an Android key event")
    keyevent.add_argument("key", help="Numeric code or name such as ENTER")
    keyevent.set_defaults(handler="keyevent")

    screenshot = subparsers.add_parser("screenshot", parents=[common], help="Capture a PNG")
    screenshot.add_argument("--output", type=Path, help="PNG file path (default: screenshot.png)")
    screenshot.set_defaults(handler="screenshot")

    dump_ui = subparsers.add_parser("dump-ui", parents=[common], help="Dump the UI hierarchy")
    dump_ui.add_argument("--output", type=Path, help="XML file path (default: ui.xml)")
    dump_ui.set_defaults(handler="dump_ui")

    logcat = subparsers.add_parser("logcat", parents=[common], help="Capture a logcat snapshot")
    logcat.add_argument("--output", type=Path, help="Text file path (default: logcat.txt)")
    logcat.add_argument("--lines", type=int, default=1000)
    logcat.add_argument("--clear", action="store_true", help="Clear logcat before capture")
    logcat.set_defaults(handler="logcat")

    validate = subparsers.add_parser("validate", parents=[common], help="Validate a JSON/YAML flow")
    validate.add_argument("flow", type=Path)
    validate.set_defaults(handler="validate")

    run = subparsers.add_parser("run", parents=[common], help="Run a JSON/YAML flow")
    run.add_argument("flow", type=Path)
    run.add_argument("--output", type=Path, help="Parent directory for run artifacts")
    run.add_argument(
        "--junit-xml",
        type=Path,
        help="Write a JUnit XML report to this file",
    )
    run.add_argument(
        "--wait-for-boot",
        action="store_true",
        help="Wait for sys.boot_completed before running the flow",
    )
    run.add_argument(
        "--boot-timeout",
        type=_positive_float,
        help="Boot readiness timeout in seconds (implies --wait-for-boot)",
    )
    run.set_defaults(handler="run")

    init = subparsers.add_parser("init", parents=[common], help="Create a starter flow")
    init.add_argument(
        "--output",
        type=Path,
        help="Output file (default: app-testbench-flow.yaml for YAML, app-testbench-flow.json for JSON)",
    )
    init.add_argument("--format", choices=["yaml", "json"], default="yaml")
    init.add_argument("--force", action="store_true")
    init.set_defaults(handler="init")

    skill = subparsers.add_parser(
        "skill-path", parents=[common], help="Print the packaged Codex skill path"
    )
    skill.set_defaults(handler="skill_path")
    return parser


def _resolve_file_output(path: Path) -> Path:
    target = path.expanduser().resolve()
    if target.is_dir():
        raise ConfigError(
            f"Output path is a directory: {target}",
            hint="Pass a file path, including a file name.",
        )
    if target.parent.exists() and not target.parent.is_dir():
        raise ConfigError(f"Output parent is not a directory: {target.parent}")
    return target


def _unique_file_output(path: Path) -> Path:
    return unique_path(_resolve_file_output(path))


def _resolve_directory_output(path: Path) -> Path:
    target = path.expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise ConfigError(
            f"Output path is not a directory: {target}",
            hint="Pass a directory path for run artifacts.",
        )
    if target.parent.exists() and not target.parent.is_dir():
        raise ConfigError(f"Output parent is not a directory: {target.parent}")
    return target


def _payload(command: str, data: Any) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": True,
        "command": command,
        "generated_at": now_iso(),
        "data": data,
    }


def _emit_json(value: dict[str, Any]) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        # A Windows console can be cp936/GBK while device UI text is arbitrary
        # Unicode. JSON escapes keep the command machine-readable in that case.
        text = json.dumps(value, ensure_ascii=True, indent=2, default=str)
    print(text)


_MISSING = object()


def _error_payload(command: str, error: RunnerError, data: Any = _MISSING) -> dict[str, Any]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "command": command,
        "generated_at": now_iso(),
        "error": {
            "type": error.kind,
            "message": error.message,
            "hint": error.hint,
        },
    }
    if data is not _MISSING:
        payload["data"] = data
    return payload


def _settings_from_args(args: argparse.Namespace) -> Settings:
    return build_settings(
        adb=getattr(args, "adb", None),
        mumu_manager=getattr(args, "mumumanager", None),
        instance=getattr(args, "instance", None),
        serial=getattr(args, "serial", None),
        timeout=getattr(args, "timeout", None),
        json_output=bool(getattr(args, "json_output", False)),
    )


def _device_context(
    settings: Settings,
) -> tuple[AndroidDevice, MuMuManagerClient | None, int, str | None]:
    adb = settings.require_adb()
    runner = ProcessRunner(settings.timeout)
    instance = settings.instance if settings.instance is not None else 0
    manager = MuMuManagerClient(settings.mumu_manager, runner) if settings.mumu_manager else None
    serial = settings.serial
    if not serial and manager:
        serial = manager.resolve_serial(instance)
    device = AndroidDevice(adb, runner, serial)
    device.connect()
    return device, manager, instance, device.serial


def _preflight_device_command(args: argparse.Namespace) -> Path | None:
    action = args.handler
    try:
        if action == "install":
            args.apk = args.apk.expanduser().resolve()
            if not args.apk.is_file():
                raise ConfigError(f"APK does not exist: {args.apk}")
            expected_package = getattr(args, "expected_package", None)
            expected_version_code = getattr(args, "expected_version_code", None)
            expected_version_name = getattr(args, "expected_version_name", None)
            if expected_package is not None:
                validate_package(expected_package)
            if expected_version_code is not None and expected_version_code < 1:
                raise ConfigError("--expected-version-code must be >= 1")
            if expected_version_name is not None and not expected_version_name.strip():
                raise ConfigError("--expected-version-name cannot be empty")
            if (
                expected_version_code is not None or expected_version_name is not None
            ) and expected_package is None:
                raise ConfigError(
                    "--expected-package is required when verifying an installed version."
                )
        elif action == "launch":
            validate_package(args.package)
            if args.activity is not None:
                validate_activity(args.activity)
        elif action == "open":
            validate_open_uri(args.uri)
            if args.package is not None:
                validate_package(args.package)
            if args.mime_type is not None:
                validate_mime_type(args.mime_type)
        elif action in {"close", "clear_app_data"}:
            validate_package(args.package)
        elif action == "reverse_port":
            validate_port(args.port, name="port")
            if args.local_port is not None:
                validate_port(args.local_port, name="local-port")
            if args.remove and args.local_port is not None:
                raise ConfigError("--local-port cannot be used with --remove")
        elif action == "tap":
            validate_coordinate(args.x, name="x")
            validate_coordinate(args.y, name="y")
        elif action == "swipe":
            for name in ("x1", "y1", "x2", "y2"):
                validate_coordinate(getattr(args, name), name=name)
            if args.duration_ms < 1 or args.duration_ms > 600_000:
                raise ConfigError("--duration-ms must be between 1 and 600000")
        elif action == "text":
            encode_input_text(args.text)
        elif action == "keyevent":
            normalize_keyevent(args.key)
    except DeviceError as exc:
        raise ConfigError(exc.message, hint=exc.hint) from exc

    if action not in {"screenshot", "dump_ui", "logcat"}:
        return None
    default_name = {
        "screenshot": "screenshot.png",
        "dump_ui": "ui.xml",
        "logcat": "logcat.txt",
    }[action]
    output = _unique_file_output(args.output or Path.cwd() / default_name)
    if action == "logcat" and (args.lines < 1 or args.lines > 100_000):
        raise ConfigError("--lines must be between 1 and 100000")
    return output


def _print_instances(instances: list[Instance]) -> None:
    if not instances:
        print("No MuMu instances found.")
        return
    print(f"{'INDEX':<7} {'STATE':<18} {'ADB':<22} {'ANDROID':<8} NAME")
    for item in instances:
        print(
            f"{item.index:<7} {item.player_state:<18} "
            f"{item.serial or '-':<22} {item.android_version or '-':<8} {item.name}"
        )


def _print_checks(checks: list[Any]) -> None:
    for check in checks:
        print(f"[{check.status.upper():<4}] {check.name:<18} {check.message}")
        if check.status in {"warn", "fail"} and check.details:
            hint = check.details.get("hint")
            if hint:
                print(f"       {hint}")


def _failure_from_result(result: RunResult) -> RunnerError:
    failed_step = next((step for step in result.steps if step.status == "failed"), None)
    if failed_step is not None:
        message = f"Flow step '{failed_step.name}' failed: {failed_step.error or 'unknown error'}"
        hint = failed_step.hint or f"Inspect the run artifacts: {result.report_path}"
        return StepFailure(message, hint=hint)
    return RunnerError(
        f"Flow finished with status '{result.status}'.",
        hint=f"Inspect the run artifacts: {result.report_path}",
    )


def _finish(
    args: argparse.Namespace,
    command: str,
    data: Any,
    human: Any = None,
    *,
    ok: bool = True,
    error: RunnerError | None = None,
) -> int:
    if getattr(args, "json_output", False):
        if ok:
            payload = _payload(command, data)
        else:
            failure = error or RunnerError(
                f"{command} finished with a failed status.",
                hint="Inspect data for the structured failure details.",
            )
            payload = _error_payload(command, failure, data)
        _emit_json(payload)
    elif human:
        human(data)
    return 0 if ok else 1


def _command_doctor(args: argparse.Namespace, settings: Settings) -> int:
    checks = collect_doctor_checks(settings)
    failed = any(check.status == "fail" for check in checks)
    warned = any(check.status == "warn" for check in checks)
    status = "fail" if failed else ("warn" if warned else "pass")
    data = {
        "status": status,
        "checks": [check.to_dict() for check in checks],
        "summary": {
            "pass": sum(check.status == "pass" for check in checks),
            "warn": sum(check.status == "warn" for check in checks),
            "fail": sum(check.status == "fail" for check in checks),
        },
    }

    def human(_: Any) -> None:
        _print_checks(checks)
        print(f"\nOverall: {status.upper()}")

    failure = (
        RunnerError(
            "One or more doctor checks failed.",
            hint="Inspect data.checks for the failing environment checks.",
        )
        if failed
        else None
    )
    return _finish(args, "doctor", data, human, ok=not failed, error=failure)


def _instance_index(args: argparse.Namespace, settings: Settings) -> int:
    value = getattr(args, "index", None)
    if value is not None:
        return value
    return settings.instance if settings.instance is not None else 0


def _command_instance(args: argparse.Namespace, settings: Settings) -> int:
    manager = MuMuManagerClient(settings.require_manager(), ProcessRunner(settings.timeout))
    action = getattr(args, "handler", "")
    if action == "instance_list":
        instances = manager.list_instances()
        return _finish(
            args,
            "instance.list",
            {"instances": [item.to_dict() for item in instances]},
            lambda _: _print_instances(instances),
        )

    index = _instance_index(args, settings)
    if action == "instance_start":
        message = manager.control(index, "launch")
        if getattr(args, "wait", 0) > 0:
            instance = manager.wait_until_running(index, timeout=float(args.wait))
            message += f"\nState: {instance.player_state}"
        command = "instance.start"
    elif action == "instance_stop":
        message = manager.control(index, "shutdown")
        command = "instance.stop"
    elif action == "instance_restart":
        message = manager.control(index, "restart")
        command = "instance.restart"
    else:
        raise ConfigError(f"Unknown instance command: {action}")

    data = {"instance": index, "message": message.strip()}
    return _finish(
        args,
        command,
        data,
        lambda payload: print(f"[{payload['instance']}] {payload['message']}"),
    )


def _command_device(args: argparse.Namespace, settings: Settings) -> int:
    output = _preflight_device_command(args)
    device, _, instance, serial = _device_context(settings)
    action = args.handler
    if action == "install":
        message = device.install(
            args.apk,
            reinstall=not args.no_reinstall,
            grant_permissions=args.grant_permissions,
            expected_package=getattr(args, "expected_package", None),
            expected_version_code=getattr(args, "expected_version_code", None),
            expected_version_name=getattr(args, "expected_version_name", None),
        )
        data = {
            "instance": instance,
            "serial": serial,
            "apk": str(args.apk.resolve()),
            "message": message,
        }
        if device.last_package_identity is not None:
            data["package_identity"] = device.last_package_identity
    elif action == "launch":
        message = device.launch(args.package, args.activity)
        data = {
            "instance": instance,
            "serial": serial,
            "package": args.package,
            "message": message,
        }
    elif action == "open":
        message = device.open_uri(args.uri, package=args.package, mime_type=args.mime_type)
        data = {
            "instance": instance,
            "serial": serial,
            "uri": args.uri,
            "package": args.package,
            "mime_type": args.mime_type,
            "message": message,
        }
    elif action == "close":
        message = device.close(args.package)
        data = {
            "instance": instance,
            "serial": serial,
            "package": args.package,
            "message": message,
        }
    elif action == "clear_app_data":
        message = device.clear_app_data(args.package)
        data = {
            "instance": instance,
            "serial": serial,
            "package": args.package,
            "message": message,
        }
    elif action == "orientation":
        message = device.set_orientation(args.mode)
        data = {
            "instance": instance,
            "serial": serial,
            "mode": args.mode,
            "message": message,
        }
    elif action == "reverse_port":
        message = device.reverse_port(args.port, local_port=args.local_port, remove=args.remove)
        data = {
            "instance": instance,
            "serial": serial,
            "port": args.port,
            "local_port": args.local_port,
            "remove": args.remove,
            "message": message,
        }
    elif action == "tap":
        message = device.tap(args.x, args.y)
        data = {
            "instance": instance,
            "serial": serial,
            "x": args.x,
            "y": args.y,
            "message": message,
        }
    elif action == "swipe":
        message = device.swipe(args.x1, args.y1, args.x2, args.y2, args.duration_ms)
        data = {
            "instance": instance,
            "serial": serial,
            "from": [args.x1, args.y1],
            "to": [args.x2, args.y2],
            "duration_ms": args.duration_ms,
            "message": message,
        }
    elif action == "text":
        message = device.input_text(args.text)
        data = {"instance": instance, "serial": serial, "text": args.text, "message": message}
    elif action == "keyevent":
        message = device.keyevent(args.key)
        data = {"instance": instance, "serial": serial, "key": args.key, "message": message}
    elif action == "screenshot":
        assert output is not None
        device.screenshot(output)
        data = {
            "instance": instance,
            "serial": serial,
            "path": str(output),
            "bytes": output.stat().st_size,
        }
        message = f"Screenshot saved to {output}"
    elif action == "dump_ui":
        assert output is not None
        device.dump_ui(output)
        data = {
            "instance": instance,
            "serial": serial,
            "path": str(output),
            "nodes": device.ui_node_count(output),
            "text": device.ui_text(output),
        }
        message = f"UI hierarchy saved to {output}"
    elif action == "logcat":
        assert output is not None
        device.logcat(output, lines=args.lines, clear=args.clear)
        text = output.read_text(encoding="utf-8", errors="replace")
        data = {
            "instance": instance,
            "serial": serial,
            "path": str(output),
            "lines": len(text.splitlines()),
        }
        message = f"Logcat saved to {output}"
    else:
        raise ConfigError(f"Unknown device command: {action}")

    command = action.replace("_", "-")
    return _finish(args, command, data, lambda _: print(message))


def _command_validate(args: argparse.Namespace, _: Settings) -> int:
    flow = load_flow(args.flow)
    data = flow.to_dict()

    def human(payload: dict[str, Any]) -> None:
        print(f"Flow is valid: {payload['name']} ({payload['step_count']} steps)")
        print(f"Path: {payload['path']}")
        for section in ("setup", "steps", "teardown"):
            items = payload[section]
            if items:
                print(f"  {section}: {len(items)}")

    return _finish(args, "validate", data, human)


def _command_run(args: argparse.Namespace, settings: Settings) -> int:
    flow = load_flow(args.flow)
    output_base = _resolve_directory_output(args.output or Path.cwd() / "runs")
    junit_path = _resolve_file_output(args.junit_xml) if args.junit_xml else None
    wait_for_boot = True if args.wait_for_boot or args.boot_timeout is not None else None
    result = FlowRunner(
        settings,
        flow,
        output_base=output_base,
        junit_path=junit_path,
        wait_for_boot=wait_for_boot,
        boot_timeout=args.boot_timeout,
    ).run()
    data = result.to_dict()

    def human(payload: dict[str, Any]) -> None:
        summary = payload["summary"]
        print(
            f"{payload['status'].upper()}: {summary['passed']} passed, "
            f"{summary['failed']} failed, {summary['skipped']} skipped "
            f"in {payload['duration_ms']:,} ms"
        )
        print(f"Report: {payload['report_path']}")
        print(f"JSON:   {payload['result_path']}")
        if payload.get("junit_path"):
            print(f"JUnit:  {payload['junit_path']}")

    return _finish(
        args,
        "run",
        data,
        human,
        ok=result.status == "passed",
        error=None if result.status == "passed" else _failure_from_result(result),
    )


def _command_init(args: argparse.Namespace, _: Settings) -> int:
    default_name = "app-testbench-flow.json" if args.format == "json" else "app-testbench-flow.yaml"
    output = _resolve_file_output(args.output or Path(default_name))
    if output.exists() and not args.force:
        raise ConfigError(
            f"File already exists: {output}",
            hint="Pass --force to overwrite it.",
        )
    content = starter_document(json_format=args.format == "json")
    atomic_write_text(output, content)
    data = {"path": str(output), "format": args.format}
    return _finish(args, "init", data, lambda payload: print(f"Created {payload['path']}"))


def _command_skill_path(args: argparse.Namespace, _: Settings) -> int:
    path = Path(__file__).resolve().parent / "skills" / "SKILL.md"
    if not path.is_file():
        raise ConfigError(f"Packaged SKILL.md is missing: {path}")
    return _finish(
        args,
        "skill-path",
        {"path": str(path)},
        lambda payload: print(payload["path"]),
    )


def _dispatch(args: argparse.Namespace, settings: Settings) -> int:
    handler = getattr(args, "handler", "")
    if handler == "doctor":
        return _command_doctor(args, settings)
    if handler.startswith("instance_"):
        return _command_instance(args, settings)
    if handler in {
        "install",
        "launch",
        "open",
        "close",
        "clear_app_data",
        "orientation",
        "reverse_port",
        "tap",
        "swipe",
        "text",
        "keyevent",
        "screenshot",
        "dump_ui",
        "logcat",
    }:
        return _command_device(args, settings)
    if handler == "validate":
        return _command_validate(args, settings)
    if handler == "run":
        return _command_run(args, settings)
    if handler == "init":
        return _command_init(args, settings)
    if handler == "skill_path":
        return _command_skill_path(args, settings)
    raise ConfigError(f"Unknown command handler: {handler or '<empty>'}")


def _command_name(args: argparse.Namespace) -> str:
    handler = getattr(args, "handler", "")
    if handler.startswith("instance_"):
        return "instance." + handler.removeprefix("instance_")
    if handler == "dump_ui":
        return "dump-ui"
    if handler == "skill_path":
        return "skill-path"
    return handler or getattr(args, "command", None) or "cli"


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    json_requested = _json_requested(raw_argv)
    args = argparse.Namespace(command=_guess_command(raw_argv), json_output=json_requested)
    try:
        parser = build_parser()
        args = parser.parse_args(raw_argv)
        args.json_output = json_requested or bool(getattr(args, "json_output", False))
        settings = _settings_from_args(args)
        args.json_output = settings.json_output
        return _dispatch(args, settings)
    except RunnerError as exc:
        if getattr(args, "json_output", False):
            _emit_json(_error_payload(_command_name(args), exc))
        else:
            print(f"Error: {exc.message}", file=sys.stderr)
            if exc.hint:
                print(f"Hint: {exc.hint}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        if json_requested:
            interrupted = RunnerError("Interrupted.")
            _emit_json(_error_payload(_command_name(args), interrupted))
        else:
            print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # pragma: no cover - defensive boundary
        if getattr(args, "debug", False):
            traceback.print_exc()
        if getattr(args, "json_output", False):
            wrapped = RunnerError(f"Unexpected error: {exc}")
            _emit_json(_error_payload(_command_name(args), wrapped))
        else:
            print(f"Unexpected error: {exc}", file=sys.stderr)
            print("Re-run with --debug for a traceback.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
