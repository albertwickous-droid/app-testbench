"""ADB-backed Android device operations."""

from __future__ import annotations

import re
import shlex
import time
import xml.etree.ElementTree as ET
from contextlib import suppress
from pathlib import Path
from typing import Any

from app_testbench.errors import DeviceError, RunnerError
from app_testbench.utils import BinaryResult, ProcessRunner

PACKAGE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")
KEY_RE = re.compile(r"^[A-Za-z0-9_]+$")
ACTIVITY_RE = re.compile(r"^[A-Za-z_.$][A-Za-z0-9_.$]*(?:/[A-Za-z_.$][A-Za-z0-9_.$]*)?$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def validate_package(package: str) -> str:
    if not PACKAGE_RE.fullmatch(package):
        raise DeviceError(f"Invalid Android package name: {package!r}")
    return package


def validate_coordinate(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DeviceError(f"{name} must be an integer")
    if value < 0 or value > 100_000:
        raise DeviceError(f"{name} must be between 0 and 100000")
    return value


def validate_activity(activity: str) -> str:
    value = activity.strip()
    if not value or not ACTIVITY_RE.fullmatch(value):
        raise DeviceError(
            f"Invalid activity component: {activity!r}",
            hint=(
                "Use a component such as com.example/.MainActivity, "
                "com.example/com.example.MainActivity, or MainActivity."
            ),
        )
    return value


def activity_component(package: str, activity: str) -> str:
    component = validate_activity(activity)
    if "/" in component:
        return component
    if component.startswith("."):
        return f"{package}/{package}{component}"
    if "." not in component:
        return f"{package}/{package}.{component}"
    return f"{package}/{component}"


def normalize_keyevent(key: str) -> str:
    value = str(key).strip()
    if value.isdigit():
        return value
    if not KEY_RE.fullmatch(value):
        raise DeviceError(f"Invalid keyevent: {key!r}")
    value = value.upper()
    return value if value.startswith("KEYCODE_") else f"KEYCODE_{value}"


def encode_input_text(text: str) -> str:
    """Encode text accepted by Android's built-in ``input text`` command."""

    if not text:
        raise DeviceError("text cannot be empty")
    for character in text:
        code = ord(character)
        if code < 32 or code > 126:
            raise DeviceError(
                "ADB `input text` only supports printable ASCII. "
                "Use the emulator clipboard or install ADBKeyboard for Chinese/Unicode input."
            )
    return text.replace(" ", "%s")


def parse_adb_devices(output: str) -> list[dict[str, str]]:
    devices: list[dict[str, str]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("List of devices") or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        item = {"serial": parts[0], "state": parts[1]}
        for token in parts[2:]:
            if ":" in token:
                key, value = token.split(":", 1)
                item[key] = value
        devices.append(item)
    return devices


def parse_package_identity(output: str) -> dict[str, Any]:
    """Extract package/version fields from ``dumpsys package`` output."""

    package_match = re.search(r"Package \[([^\]]+)\]", output)
    version_code_match = re.search(r"\bversionCode=(\d+)\b", output)
    version_name: str | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line.startswith("versionName="):
            continue
        value = line.split("=", 1)[1].strip().strip("\"'")
        if value:
            version_name = value
            break
    return {
        "package": package_match.group(1) if package_match else None,
        "version_code": int(version_code_match.group(1)) if version_code_match else None,
        "version_name": version_name,
    }


class AndroidDevice:
    def __init__(
        self,
        adb: Path,
        runner: ProcessRunner,
        serial: str | None = None,
    ) -> None:
        self.adb = adb
        self.runner = runner
        self.serial = serial
        self.last_package_identity: dict[str, Any] | None = None

    def _command(self, *args: str, serial: bool = True) -> list[str]:
        command = [str(self.adb)]
        if serial and self.serial:
            command.extend(["-s", self.serial])
        command.extend(args)
        return command

    def _run(self, *args: str, serial: bool = True, check: bool = True):
        result = self.runner.run(self._command(*args, serial=serial), check=False)
        if check and result.returncode != 0:
            detail = result.combined_output[:2000] or "no output"
            raise DeviceError(
                f"ADB command failed ({result.returncode}): {' '.join(args)}",
                hint=detail,
            )
        return result

    def version(self) -> str:
        result = self._run("version", serial=False)
        return result.combined_output.splitlines()[0].strip() if result.combined_output else ""

    def devices(self) -> list[dict[str, str]]:
        return parse_adb_devices(self._run("devices", "-l", serial=False).stdout)

    def get_state(self) -> str:
        result = self._run("get-state")
        states = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return states[-1] if states else ""

    def connect(self) -> str:
        if not self.serial:
            available = [item for item in self.devices() if item.get("state") == "device"]
            if len(available) == 1:
                self.serial = available[0]["serial"]
            else:
                raise DeviceError(
                    "No unambiguous ADB device is connected.",
                    hint="Pass --serial, start a MuMu instance, or connect only one device.",
                )

        if ":" in self.serial:
            result = self.runner.run(
                self._command("connect", self.serial, serial=False),
                check=False,
            )
            output = result.combined_output.lower()
            if result.returncode != 0 or "cannot" in output or "failed" in output:
                raise DeviceError(
                    f"Could not connect to {self.serial}.",
                    hint=result.combined_output or "Check that the instance is running.",
                )

        state = self.get_state()
        if state != "device":
            raise DeviceError(
                f"ADB reports state {state!r} for {self.serial}.",
                hint="Restart ADB (`adb kill-server`) or start the MuMu instance.",
            )
        return self.serial

    def wait_until_boot_complete(
        self,
        *,
        timeout: float = 60.0,
        interval: float = 1.0,
    ) -> dict[str, Any]:
        """Poll ``sys.boot_completed`` until Android reports a completed boot."""

        if timeout <= 0:
            raise DeviceError("boot timeout must be greater than zero")
        if interval <= 0:
            raise DeviceError("boot polling interval must be greater than zero")

        started = time.monotonic()
        attempts = 0
        last_output = ""
        while True:
            attempts += 1
            result = self._run("shell", "getprop", "sys.boot_completed", check=False)
            last_output = result.combined_output.strip()
            if result.returncode == 0 and any(
                line.strip() == "1" for line in result.stdout.splitlines()
            ):
                return {
                    "ready": True,
                    "attempts": attempts,
                    "elapsed_ms": max(0, round((time.monotonic() - started) * 1000)),
                    "last_output": last_output,
                }

            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise DeviceError(
                    f"Android boot did not complete within {timeout:g}s.",
                    hint=(
                        f"Polled sys.boot_completed {attempts} time(s); "
                        f"last output: {last_output or '<empty>'}."
                    ),
                )
            time.sleep(min(interval, remaining))

    def package_identity(self, package: str) -> dict[str, Any]:
        package = validate_package(package)
        result = self._run("shell", "dumpsys", "package", package)
        output = result.combined_output
        identity = parse_package_identity(output)
        if not identity["package"]:
            raise DeviceError(
                f"Could not read installed package identity for {package}.",
                hint=output[:2000] or "dumpsys package returned no output",
            )
        identity["dumpsys_preview"] = output[:2000]
        return identity

    def verify_package_identity(
        self,
        package: str,
        *,
        expected_version_code: int | None = None,
        expected_version_name: str | None = None,
    ) -> dict[str, Any]:
        identity = self.package_identity(package)
        mismatches: list[str] = []
        if identity["package"] != package:
            mismatches.append("package")
        if expected_version_code is not None and identity["version_code"] != expected_version_code:
            mismatches.append("versionCode")
        if expected_version_name is not None and identity["version_name"] != expected_version_name:
            mismatches.append("versionName")
        if mismatches:
            expected = {
                "package": package,
                "version_code": expected_version_code,
                "version_name": expected_version_name,
            }
            observed = {
                "package": identity["package"],
                "version_code": identity["version_code"],
                "version_name": identity["version_name"],
            }
            raise DeviceError(
                "Installed package identity did not match expectations.",
                hint=(
                    f"Mismatch: {', '.join(mismatches)}. "
                    f"Expected {expected}; observed {observed}.\n"
                    f"Dumpsys preview:\n{identity.get('dumpsys_preview', '')}"
                ),
            )
        return identity

    def install(
        self,
        apk: Path,
        *,
        reinstall: bool = True,
        grant_permissions: bool = False,
        expected_package: str | None = None,
        expected_version_code: int | None = None,
        expected_version_name: str | None = None,
    ) -> str:
        self.last_package_identity = None
        if expected_package is not None:
            validate_package(expected_package)
        if expected_version_name is not None and not expected_version_name.strip():
            raise DeviceError("expected_version_name cannot be empty")
        if not apk.is_file():
            raise DeviceError(f"APK does not exist: {apk}")
        if expected_package is None and (
            expected_version_code is not None or expected_version_name is not None
        ):
            raise DeviceError(
                "expected_package is required when verifying the installed version.",
                hint="Pass expected_package together with version expectations.",
            )
        args = ["install"]
        if reinstall:
            args.append("-r")
        if grant_permissions:
            args.append("-g")
        args.append(str(apk.resolve()))
        result = self._run(*args)
        output = result.combined_output
        if "Success" not in output and "success" not in output:
            raise DeviceError("ADB install did not report success.", hint=output[:2000])
        if expected_package is not None:
            self.last_package_identity = self.verify_package_identity(
                expected_package,
                expected_version_code=expected_version_code,
                expected_version_name=expected_version_name,
            )
        return output.strip()

    def launch(self, package: str, activity: str | None = None) -> str:
        package = validate_package(package)
        if activity is not None:
            component = activity_component(package, activity)
            result = self._run("shell", "am", "start", "-W", "-n", component)
        else:
            result = self._run(
                "shell",
                "monkey",
                "-p",
                package,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            )
        output = result.combined_output
        lowered = output.lower()
        if activity is not None and any(
            marker in lowered
            for marker in (
                "error type 3",
                "error: activity class",
                "unable to resolve intent",
                "does not exist",
            )
        ):
            raise DeviceError(
                f"Activity could not be launched: {component}",
                hint=output[:2000],
            )
        if "no activities found" in lowered or "monkey aborted" in lowered:
            raise DeviceError(
                f"No launcher activity was found for {package}.",
                hint=output[:2000],
            )
        return output.strip()

    def close(self, package: str) -> str:
        package = validate_package(package)
        result = self._run("shell", "am", "force-stop", package)
        return result.combined_output.strip() or f"Stopped {package}"

    def tap(self, x: int, y: int) -> str:
        x = validate_coordinate(x, name="x")
        y = validate_coordinate(y, name="y")
        return self._run("shell", "input", "tap", str(x), str(y)).combined_output.strip()

    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_ms: int = 300,
    ) -> str:
        x1 = validate_coordinate(x1, name="x1")
        y1 = validate_coordinate(y1, name="y1")
        x2 = validate_coordinate(x2, name="x2")
        y2 = validate_coordinate(y2, name="y2")
        if duration_ms < 1 or duration_ms > 600_000:
            raise DeviceError("duration_ms must be between 1 and 600000")
        return self._run(
            "shell",
            "input",
            "swipe",
            str(x1),
            str(y1),
            str(x2),
            str(y2),
            str(duration_ms),
        ).combined_output.strip()

    def input_text(self, text: str) -> str:
        encoded = encode_input_text(text)
        command = f"input text {shlex.quote(encoded)}"
        return self._run("shell", command).combined_output.strip()

    def keyevent(self, key: str) -> str:
        normalized = normalize_keyevent(key)
        return self._run("shell", "input", "keyevent", normalized).combined_output.strip()

    def back(self) -> str:
        return self.keyevent("KEYCODE_BACK")

    def home(self) -> str:
        return self.keyevent("KEYCODE_HOME")

    def screenshot(self, output: Path) -> Path:
        result: BinaryResult = self.runner.run_bytes(
            self._command("exec-out", "screencap", "-p"),
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout)[:1000].decode("utf-8", errors="replace")
            raise DeviceError("ADB screenshot failed.", hint=detail)
        if not result.stdout.startswith(PNG_SIGNATURE):
            preview = result.stdout[:16]
            raise DeviceError(
                "ADB screenshot did not return a PNG image.",
                hint=f"Output started with {preview!r}.",
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result.stdout)
        return output

    def _remove_remote_file(self, remote: str) -> None:
        with suppress(RunnerError):
            self.runner.run(self._command("shell", "rm", "-f", remote), check=False)

    def dump_ui(self, output: Path) -> Path:
        remote = "/sdcard/app_testbench_window.xml"
        try:
            dump = self._run("shell", "uiautomator", "dump", remote)
            dump_output = dump.combined_output
            if dump_output and "error" in dump_output.lower():
                raise DeviceError("uiautomator dump failed.", hint=dump_output[:2000])
            result = self.runner.run_bytes(
                self._command("exec-out", "cat", remote),
                check=False,
            )
            if result.returncode != 0 or b"<hierarchy" not in result.stdout[:4000]:
                detail = (result.stderr or result.stdout)[:2000].decode("utf-8", errors="replace")
                raise DeviceError("Could not read the UI hierarchy.", hint=detail)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(result.stdout)
            return output
        finally:
            self._remove_remote_file(remote)

    def ui_text(self, xml_path: Path) -> list[str]:
        try:
            root = ET.parse(xml_path).getroot()
        except (ET.ParseError, OSError) as exc:
            raise DeviceError(f"Could not parse UI XML: {xml_path}") from exc
        values: list[str] = []
        for node in root.iter():
            for attribute in ("text", "content-desc"):
                value = (node.attrib.get(attribute) or "").strip()
                if value and value not in values:
                    values.append(value)
        return values

    def ui_node_count(self, xml_path: Path) -> int:
        try:
            return sum(1 for _ in ET.parse(xml_path).getroot().iter())
        except (ET.ParseError, OSError) as exc:
            raise DeviceError(f"Could not parse UI XML: {xml_path}") from exc

    def clear_logcat(self) -> None:
        self._run("logcat", "-c", check=False)

    def logcat(
        self,
        output: Path,
        *,
        lines: int = 1000,
        clear: bool = False,
    ) -> Path:
        if lines < 1 or lines > 100_000:
            raise DeviceError("logcat lines must be between 1 and 100000")
        if clear:
            self._run("logcat", "-c", check=False)
        result = self._run("logcat", "-d", "-v", "threadtime", "-t", str(lines))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result.stdout, encoding="utf-8", newline="\n")
        return output
