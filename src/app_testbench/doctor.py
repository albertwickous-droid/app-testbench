"""Environment diagnostics used by the doctor command."""

from __future__ import annotations

import platform

from app_testbench.config import Settings
from app_testbench.device import AndroidDevice
from app_testbench.errors import RunnerError
from app_testbench.models import Check, Instance
from app_testbench.mumu import MuMuManagerClient
from app_testbench.utils import ProcessRunner


def collect_doctor_checks(settings: Settings) -> list[Check]:
    checks: list[Check] = []
    runner = ProcessRunner(settings.timeout)
    checks.append(
        Check(
            "system",
            "pass",
            f"Python on {platform.system()} {platform.release()}",
            {"platform": platform.platform(), "python": platform.python_version()},
        )
    )

    if settings.adb:
        checks.append(Check("adb", "pass", str(settings.adb)))
    else:
        checks.append(
            Check(
                "adb",
                "fail",
                "ADB was not found",
                {"env": "APP_TESTBENCH_ADB", "option": "--adb"},
            )
        )

    if settings.mumu_manager:
        checks.append(Check("mumu_manager", "pass", str(settings.mumu_manager)))
    else:
        checks.append(
            Check(
                "mumu_manager",
                "fail",
                "MuMuManager.exe was not found",
                {"env": "APP_TESTBENCH_MUMU_MANAGER", "option": "--mumumanager"},
            )
        )

    manager: MuMuManagerClient | None = None
    instances: list[Instance] = []
    if settings.mumu_manager:
        manager = MuMuManagerClient(settings.mumu_manager, runner)
        try:
            checks.append(Check("mumu_version", "pass", manager.version()))
        except RunnerError as exc:
            checks.append(Check("mumu_version", "fail", str(exc), {"hint": exc.hint}))
        try:
            instances = manager.list_instances()
            checks.append(
                Check(
                    "instances",
                    "pass" if instances else "warn",
                    f"{len(instances)} instance(s) found",
                    {"instances": [instance.to_dict() for instance in instances]},
                )
            )
        except RunnerError as exc:
            checks.append(Check("instances", "fail", str(exc), {"hint": exc.hint}))

    if settings.adb:
        device = AndroidDevice(settings.adb, runner)
        try:
            checks.append(Check("adb_version", "pass", device.version()))
        except RunnerError as exc:
            checks.append(Check("adb_version", "fail", str(exc), {"hint": exc.hint}))
        try:
            devices = device.devices()
            ready = [item for item in devices if item.get("state") == "device"]
            checks.append(
                Check(
                    "adb_devices",
                    "pass" if ready else "warn",
                    f"{len(ready)} ready device(s)",
                    {"devices": devices},
                )
            )
        except RunnerError as exc:
            checks.append(Check("adb_devices", "fail", str(exc), {"hint": exc.hint}))

    instance_index = settings.instance if settings.instance is not None else 0
    selected = next((item for item in instances if item.index == instance_index), None)
    if instances and not selected:
        checks.append(
            Check("selected_instance", "fail", f"Instance {instance_index} was not found")
        )
    elif selected:
        checks.append(
            Check(
                "selected_instance",
                "pass" if selected.running else "warn",
                f"Instance {selected.index}: {selected.player_state}",
                selected.to_dict(),
            )
        )
    elif manager:
        checks.append(Check("selected_instance", "warn", "No instance metadata available"))

    serial = settings.serial
    if not serial and selected and selected.running and manager:
        try:
            serial = manager.resolve_serial(selected.index)
        except RunnerError as exc:
            checks.append(Check("adb_connection", "fail", str(exc), {"hint": exc.hint}))
    if serial and settings.adb:
        try:
            device = AndroidDevice(settings.adb, runner, serial)
            checks.append(Check("adb_connection", "pass", f"connected to {device.connect()}"))
        except RunnerError as exc:
            checks.append(
                Check(
                    "adb_connection",
                    "fail",
                    str(exc),
                    {"hint": exc.hint, "serial": serial},
                )
            )
    elif selected and not selected.running:
        checks.append(
            Check(
                "adb_connection",
                "warn",
                "Selected instance is not running",
                {"instance": selected.index},
            )
        )

    return checks
