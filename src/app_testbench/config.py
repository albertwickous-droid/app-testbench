"""CLI settings and Windows-first MuMu tool discovery."""

from __future__ import annotations

import glob
import math
import os
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from app_testbench.errors import ConfigError


@dataclass(slots=True)
class Settings:
    adb: Path | None
    mumu_manager: Path | None
    instance: int | None
    serial: str | None
    timeout: float
    json_output: bool
    env: Mapping[str, str]
    instance_explicit: bool = False
    serial_explicit: bool = False

    def require_adb(self) -> Path:
        if self.adb:
            return self.adb
        raise ConfigError(
            "ADB was not found.",
            hint="Install Android platform-tools or set APP_TESTBENCH_ADB / --adb.",
        )

    def require_manager(self) -> Path:
        if self.mumu_manager:
            return self.mumu_manager
        raise ConfigError(
            "MuMuManager.exe was not found.",
            hint="Install MuMu Player or set APP_TESTBENCH_MUMU_MANAGER / --mumumanager.",
        )


def _env_value(env: Mapping[str, str], name: str) -> str | None:
    value = env.get(name, "").strip()
    return value or None


def _which(name: str, env: Mapping[str, str]) -> str | None:
    return shutil.which(name, path=env.get("PATH", ""))


def _resolve_explicit(value: str, *, label: str, env: Mapping[str, str]) -> Path:
    if not value.strip():
        raise ConfigError(f"{label} path cannot be empty.")
    expanded = Path(os.path.expandvars(os.path.expanduser(value)))
    if expanded.is_file():
        return expanded.resolve()
    found = _which(value, env)
    if found:
        return Path(found).resolve()
    raise ConfigError(f"{label} does not exist or is not executable: {value}")


def _dedupe(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        try:
            if not path.is_file():
                continue
            key = str(path.resolve()).lower() if os.name == "nt" else str(path.resolve())
        except OSError:
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(path.resolve())
    return result


def _newest_first(paths: list[Path]) -> list[Path]:
    def modified(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    return sorted(_dedupe(paths), key=modified, reverse=True)


def _registry_install_dirs() -> list[Path]:
    if os.name != "nt":
        return []
    try:
        import winreg
    except ImportError:
        return []

    locations: list[Path] = []
    keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
    ]
    for hive, key_path in keys:
        try:
            with winreg.OpenKey(hive, key_path) as root_key:
                for index in range(512):
                    try:
                        subkey_name = winreg.EnumKey(root_key, index)
                    except OSError:
                        break
                    try:
                        with winreg.OpenKey(root_key, subkey_name) as subkey:
                            display_name = str(winreg.QueryValueEx(subkey, "DisplayName")[0] or "")
                            if "mumu" not in display_name.lower():
                                continue
                            install_location = str(
                                winreg.QueryValueEx(subkey, "InstallLocation")[0] or ""
                            ).strip()
                            if install_location:
                                locations.append(Path(install_location))
                    except OSError:
                        continue
        except OSError:
            continue
    return locations


def find_mumu_manager(env: Mapping[str, str] | None = None) -> Path | None:
    env = env if env is not None else os.environ
    env_value = _env_value(env, "APP_TESTBENCH_MUMU_MANAGER")
    if env_value:
        return _resolve_explicit(env_value, label="MuMuManager", env=env)

    candidates: list[Path] = []
    for name in ("MuMuManager.exe", "MuMuManager"):
        found = _which(name, env)
        if found:
            candidates.append(Path(found))

    roots = [
        Path(env.get("ProgramFiles", r"C:\Program Files")),
        Path(env.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        Path(env.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")),
    ]
    patterns = [
        "Netease/*/nx_main/MuMuManager.exe",
        "Netease/*/nx_device/*/shell/MuMuManager.exe",
        "Netease/*/shell/MuMuManager.exe",
        "Netease/*/MuMuManager.exe",
        "MuMu*/nx_main/MuMuManager.exe",
        "MuMu*/nx_device/*/shell/MuMuManager.exe",
        "MuMu*/shell/MuMuManager.exe",
        "Programs/*/nx_main/MuMuManager.exe",
        "Programs/*/nx_device/*/shell/MuMuManager.exe",
        "Programs/*/shell/MuMuManager.exe",
    ]
    for root in roots:
        for pattern in patterns:
            for match in glob.glob(str(root / pattern)):
                candidates.append(Path(match))

    for install_dir in _registry_install_dirs():
        candidates.extend(
            [
                install_dir / "MuMuManager.exe",
                install_dir / "nx_main" / "MuMuManager.exe",
                install_dir / "shell" / "MuMuManager.exe",
            ]
        )
        candidates.extend(
            Path(item) for item in glob.glob(str(install_dir / "nx_device/*/shell/MuMuManager.exe"))
        )

    resolved = _newest_first(candidates)
    return resolved[0] if resolved else None


def find_adb(
    env: Mapping[str, str] | None = None,
    manager: Path | None = None,
) -> Path | None:
    env = env if env is not None else os.environ
    env_value = _env_value(env, "APP_TESTBENCH_ADB")
    if env_value:
        return _resolve_explicit(env_value, label="ADB", env=env)

    candidates: list[Path] = []
    for name in ("adb.exe", "adb"):
        found = _which(name, env)
        if found:
            candidates.append(Path(found))

    sdk_roots = [
        env.get("ANDROID_HOME"),
        env.get("ANDROID_SDK_ROOT"),
        str(Path(env.get("LOCALAPPDATA", Path.home())) / "Android" / "Sdk"),
    ]
    for sdk in sdk_roots:
        if sdk:
            candidates.append(Path(sdk) / "platform-tools" / "adb.exe")
            candidates.append(Path(sdk) / "platform-tools" / "adb")

    if manager:
        manager_dir = manager.parent
        install_root = manager_dir.parent
        candidates.extend(
            [
                manager_dir / "adb.exe",
                manager_dir / "adb",
                install_root / "adb.exe",
                install_root / "adb",
                install_root / "shell" / "adb.exe",
                install_root / "shell" / "adb",
                install_root / "vmonitor" / "bin" / "adb.exe",
            ]
        )
        for pattern in ("*/adb.exe", "*/*/adb.exe", "*/*/*/adb.exe"):
            candidates.extend(Path(item) for item in glob.glob(str(install_root / pattern)))

    resolved = _newest_first(candidates)
    return resolved[0] if resolved else None


def _parse_environment_int(value: str, *, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {value!r}") from exc
    if parsed < 0:
        raise ConfigError(f"{name} must be >= 0")
    return parsed


def _parse_environment_float(value: str, *, name: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {value!r}") from exc
    if not math.isfinite(parsed):
        raise ConfigError(f"{name} must be a finite number, got {value!r}")
    if parsed <= 0:
        raise ConfigError(f"{name} must be > 0")
    return parsed


def _parse_environment_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be a boolean, got {value!r}")


def build_settings(
    *,
    adb: str | None = None,
    mumu_manager: str | None = None,
    instance: int | None = None,
    serial: str | None = None,
    timeout: float | None = None,
    json_output: bool = False,
    env: Mapping[str, str] | None = None,
) -> Settings:
    env = env if env is not None else os.environ

    adb_value = adb if adb is not None else _env_value(env, "APP_TESTBENCH_ADB")
    manager_value = (
        mumu_manager if mumu_manager is not None else _env_value(env, "APP_TESTBENCH_MUMU_MANAGER")
    )

    adb_path = (
        _resolve_explicit(adb_value, label="ADB", env=env)
        if adb_value is not None
        else find_adb(env)
    )
    manager_path = (
        _resolve_explicit(manager_value, label="MuMuManager", env=env)
        if manager_value is not None
        else find_mumu_manager(env)
    )
    if manager_path and not adb_path:
        adb_path = find_adb(env, manager_path)

    instance_explicit = instance is not None
    instance_value = instance
    if instance_value is None:
        env_instance = _env_value(env, "APP_TESTBENCH_INSTANCE")
        if env_instance is not None:
            instance_value = _parse_environment_int(env_instance, name="APP_TESTBENCH_INSTANCE")
    if instance_value is not None and instance_value < 0:
        raise ConfigError("--instance must be >= 0")

    serial_explicit = serial is not None
    serial_value = serial if serial is not None else _env_value(env, "APP_TESTBENCH_SERIAL")
    if serial_value is not None:
        serial_value = serial_value.strip()
        if not serial_value or any(character.isspace() for character in serial_value):
            raise ConfigError("--serial / APP_TESTBENCH_SERIAL cannot contain whitespace")

    timeout_value = timeout
    if timeout_value is None:
        env_timeout = _env_value(env, "APP_TESTBENCH_TIMEOUT")
        timeout_value = (
            _parse_environment_float(env_timeout, name="APP_TESTBENCH_TIMEOUT")
            if env_timeout
            else 30.0
        )
    try:
        parsed_timeout = float(timeout_value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"--timeout must be a number, got {timeout_value!r}") from exc
    if not math.isfinite(parsed_timeout):
        raise ConfigError(f"--timeout must be a finite number, got {timeout_value!r}")
    if parsed_timeout <= 0:
        raise ConfigError("--timeout must be > 0")

    env_json = _env_value(env, "APP_TESTBENCH_JSON")
    json_enabled = json_output or (
        _parse_environment_bool(env_json, name="APP_TESTBENCH_JSON")
        if env_json is not None
        else False
    )

    return Settings(
        adb=adb_path,
        mumu_manager=manager_path,
        instance=instance_value,
        serial=serial_value,
        timeout=parsed_timeout,
        json_output=json_enabled,
        env=env,
        instance_explicit=instance_explicit,
        serial_explicit=serial_explicit,
    )
