"""Shared deterministic fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from app_testbench.config import Settings


def _wrapper(directory: Path, stem: str, script: Path) -> Path:
    if os.name == "nt":
        path = directory / f"{stem}.cmd"
        content = f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n'
    else:
        path = directory / stem
        content = f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n'
        path.chmod(0o755)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


@pytest.fixture
def fake_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    bin_dir = tmp_path / "bin"
    adb_state = tmp_path / "adb-state"
    mumu_state = tmp_path / "mumu-state"
    bin_dir.mkdir()
    adb_state.mkdir()
    mumu_state.mkdir()
    tests_dir = Path(__file__).resolve().parent
    adb = _wrapper(bin_dir, "adb", tests_dir / "fake_adb.py")
    manager = _wrapper(bin_dir, "mumumanager", tests_dir / "fake_mumumanager.py")
    monkeypatch.setenv("FAKE_ADB_STATE", str(adb_state))
    monkeypatch.setenv("FAKE_MUMU_STATE", str(mumu_state))
    return {
        "adb": adb,
        "manager": manager,
        "bin": bin_dir,
        "adb_state": adb_state,
        "mumu_state": mumu_state,
    }


@pytest.fixture
def fake_settings(fake_tools: dict[str, Path]) -> Settings:
    return Settings(
        adb=fake_tools["adb"],
        mumu_manager=fake_tools["manager"],
        instance=0,
        serial=None,
        timeout=10.0,
        json_output=False,
        env=os.environ,
    )


@pytest.fixture
def apk_file(tmp_path: Path) -> Path:
    path = tmp_path / "demo.apk"
    path.write_bytes(b"fake apk")
    return path
