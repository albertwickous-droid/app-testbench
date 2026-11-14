from __future__ import annotations

import os
from pathlib import Path

import pytest

from app_testbench.config import build_settings, find_adb
from app_testbench.errors import ConfigError


def test_find_adb_ignores_adb_server_auto_candidate(tmp_path: Path, monkeypatch) -> None:
    install_root = tmp_path / "MuMuPlayer"
    manager = install_root / "nx_main" / "MuMuManager.exe"
    adb = install_root / "shell" / "adb.exe"
    adb_server = install_root / "vmonitor" / "bin" / "adb_server.exe"
    for path in (manager, adb, adb_server):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake executable")
    os.utime(adb, (100, 100))
    os.utime(adb_server, (200, 200))
    monkeypatch.setattr("app_testbench.config.shutil.which", lambda _name, path=None: None)

    assert find_adb(env={"PATH": ""}, manager=manager) == adb.resolve()


def test_find_adb_respects_explicit_empty_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_TESTBENCH_ADB", "host-only-adb")
    monkeypatch.setattr("app_testbench.config.shutil.which", lambda _name, path=None: None)
    monkeypatch.setattr("app_testbench.config._registry_install_dirs", lambda: [])
    monkeypatch.setattr("app_testbench.config.glob.glob", lambda _: [])
    assert find_adb(env={}) is None


def test_tool_discovery_uses_explicit_environment_path(monkeypatch) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_which(name: str, path: str | None = None) -> str | None:
        calls.append((name, path))
        return None

    monkeypatch.setattr("app_testbench.config.shutil.which", fake_which)
    monkeypatch.setattr("app_testbench.config._registry_install_dirs", lambda: [])
    monkeypatch.setattr("app_testbench.config.glob.glob", lambda _: [])

    from app_testbench.config import find_adb, find_mumu_manager

    assert find_adb(env={"PATH": "auto-path"}) is None
    assert find_mumu_manager(env={"PATH": "manager-path"}) is None
    with pytest.raises(ConfigError, match="does not exist"):
        find_adb(env={"PATH": "explicit-path", "APP_TESTBENCH_ADB": "custom-adb"})
    assert calls == [
        ("adb.exe", "auto-path"),
        ("adb", "auto-path"),
        ("MuMuManager.exe", "manager-path"),
        ("MuMuManager", "manager-path"),
        ("custom-adb", "explicit-path"),
    ]


@pytest.mark.parametrize(
    ("keyword", "label"),
    [("adb", "ADB"), ("mumu_manager", "MuMuManager")],
)
@pytest.mark.parametrize("value", ["", "   "])
def test_explicit_empty_tool_path_does_not_fallback_to_environment(
    tmp_path: Path, keyword: str, label: str, value: str
) -> None:
    adb = tmp_path / "adb.exe"
    manager = tmp_path / "MuMuManager.exe"
    adb.write_bytes(b"fake")
    manager.write_bytes(b"fake")
    env = {
        "PATH": "",
        "APP_TESTBENCH_ADB": str(adb),
        "APP_TESTBENCH_MUMU_MANAGER": str(manager),
    }
    with pytest.raises(ConfigError, match=f"{label} path cannot be empty"):
        build_settings(**{keyword: value}, env=env)
