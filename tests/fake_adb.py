#!/usr/bin/env python3
"""Deterministic ADB fixture used by the test suite."""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
UI_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Login" resource-id="com.example:id/login" class="android.widget.TextView" content-desc="" clickable="false" enabled="true" bounds="[0,0][100,100]" />
  <node index="1" text="" resource-id="com.example:id/search" class="android.widget.Button" content-desc="Search" clickable="true" enabled="true" bounds="[300,200][500,300]" />
</hierarchy>
"""
ANR_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Fake app isn't responding" resource-id="android:id/alertTitle" class="android.widget.TextView" content-desc="" clickable="false" enabled="true" bounds="[100,200][600,300]" />
  <node index="1" text="Wait" resource-id="android:id/aerr_wait" class="android.widget.Button" content-desc="" clickable="true" enabled="true" bounds="[200,500][400,600]" />
</hierarchy>
"""


def log(argv: list[str]) -> None:
    state = os.environ.get("FAKE_ADB_STATE")
    if not state:
        return
    path = Path(state) / "adb-commands.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(argv, ensure_ascii=False) + "\n")


def main() -> int:
    argv = sys.argv[1:]
    log(argv)
    serial = None
    if "-s" in argv:
        position = argv.index("-s")
        if position + 1 < len(argv):
            serial = argv[position + 1]
            del argv[position : position + 2]
    del serial

    if not argv:
        print("fake adb", file=sys.stderr)
        return 1
    command = argv[0]
    if command == "version":
        print("Android Debug Bridge version 1.0.41")
        print("Version 35.0.2-fake")
        return 0
    if command == "devices":
        print("List of devices attached")
        print("127.0.0.1:5555\tdevice product:fake model:FakeMuMu device:fake")
        return 0
    if command == "connect":
        print("connected to 127.0.0.1:5555")
        return 0
    if command == "get-state":
        if os.environ.get("FAKE_ADB_GET_STATE_STDERR") == "1":
            print("adb server version (41) does not match this client (39)", file=sys.stderr)
        print("device")
        return 0
    if command == "install":
        print("Success")
        return 0
    if command == "reverse":
        if os.environ.get("FAKE_ADB_FAIL_REVERSE") == "1":
            print("adb reverse failed", file=sys.stderr)
            return 1
        if "--remove" in argv:
            print(f"{argv[-1]}")
        else:
            print(f"{argv[1]} {argv[2]}")
        return 0
    if command == "logcat":
        if "-c" in argv:
            return 0
        print("11-05 12:00:00.000 I/FakeApp( 1000): started")
        print("11-05 12:00:01.000 E/FakeApp( 1000): sample error")
        return 0
    if command == "exec-out":
        if len(argv) >= 2 and argv[1] == "screencap":
            sys.stdout.buffer.write(PNG)
            return 0
        if len(argv) >= 2 and argv[1] == "cat":
            if os.environ.get("FAKE_ADB_INVALID_UI") == "1":
                sys.stdout.buffer.write(b"not a UI hierarchy")
            else:
                sequence = os.environ.get("FAKE_ADB_UI_SEQUENCE")
                if sequence:
                    values = [value.strip() for value in sequence.split(",") if value.strip()]
                    state = Path(os.environ.get("FAKE_ADB_STATE", "."))
                    state.mkdir(parents=True, exist_ok=True)
                    counter = state / "ui-count.txt"
                    index = int(counter.read_text(encoding="utf-8")) if counter.exists() else 0
                    variant = values[min(index, len(values) - 1)]
                    counter.write_text(str(index + 1), encoding="utf-8")
                    sys.stdout.buffer.write(ANR_XML if variant == "anr" else UI_XML)
                else:
                    text = os.environ.get("FAKE_ADB_UI_TEXT", "Login")
                    sys.stdout.buffer.write(UI_XML.replace(b"Login", text.encode("utf-8")))
            return 0
    if command == "shell":
        if len(argv) >= 3 and argv[1] == "dumpsys" and argv[2] == "input":
            sequence = os.environ.get("FAKE_ADB_SURFACE_ORIENTATION_SEQUENCE")
            if sequence:
                values = [value.strip() for value in sequence.split(",") if value.strip()]
                state = Path(os.environ.get("FAKE_ADB_STATE", "."))
                state.mkdir(parents=True, exist_ok=True)
                counter = state / "orientation-count.txt"
                index = int(counter.read_text(encoding="utf-8")) if counter.exists() else 0
                print(f"  SurfaceOrientation: {values[min(index, len(values) - 1)]}")
                counter.write_text(str(index + 1), encoding="utf-8")
            else:
                print(
                    f"  SurfaceOrientation: {os.environ.get('FAKE_ADB_SURFACE_ORIENTATION', '0')}"
                )
            return 0
        if len(argv) >= 3 and argv[1] == "getprop" and argv[2] == "sys.boot_completed":
            sequence = os.environ.get("FAKE_ADB_BOOT_SEQUENCE")
            if sequence:
                values = [value.strip() for value in sequence.split(",") if value.strip()]
                state = Path(os.environ.get("FAKE_ADB_STATE", "."))
                state.mkdir(parents=True, exist_ok=True)
                counter = state / "boot-count.txt"
                index = int(counter.read_text(encoding="utf-8")) if counter.exists() else 0
                print(values[min(index, len(values) - 1)])
                counter.write_text(str(index + 1), encoding="utf-8")
            else:
                print(os.environ.get("FAKE_ADB_BOOT_COMPLETED", "1"))
            return 0
        if len(argv) >= 4 and argv[1] == "dumpsys" and argv[2] == "package":
            if os.environ.get("FAKE_ADB_DUMPSYS_FAIL") == "1":
                print("package service unavailable", file=sys.stderr)
                return 1
            requested = argv[3]
            package = os.environ.get("FAKE_ADB_DUMPSYS_PACKAGE", requested)
            version_code = os.environ.get("FAKE_ADB_VERSION_CODE", "42")
            version_name = os.environ.get("FAKE_ADB_VERSION_NAME", "1.2.3")
            print("Packages:")
            print(f"  Package [{package}] (fake):")
            print(f"    versionCode={version_code} minSdk=23")
            print(f"    versionName={version_name}")
            return 0
        if len(argv) >= 2 and argv[1] == "uiautomator":
            print("UI hierchary dumped to: /sdcard/app_testbench_window.xml")
            return 0
        if len(argv) >= 2 and argv[1] == "monkey":
            print("Events injected: 1")
            return 0
        if len(argv) >= 4 and argv[1] == "pm" and argv[2] == "clear":
            if os.environ.get("FAKE_ADB_FAIL_CLEAR_DATA") == "1":
                print("Failed", file=sys.stderr)
                return 1
            print("Success")
            return 0
        if len(argv) >= 3 and argv[1] == "wm":
            return 0
        if len(argv) >= 3 and argv[1] == "am" and argv[2] == "force-stop":
            if os.environ.get("FAKE_ADB_FAIL_FORCE_STOP") == "1":
                print("force-stop denied", file=sys.stderr)
                return 1
            return 0
        if len(argv) >= 3 and argv[1] == "am" and argv[2] == "start":
            if os.environ.get("FAKE_ADB_FAIL_AM_START") == "1":
                print("Error type 3", file=sys.stderr)
                print("Error: Activity class does not exist.", file=sys.stderr)
                return 0
            print("Status: ok")
            return 0
        if len(argv) >= 2 and argv[1] == "input":
            return 0
        if len(argv) >= 2 and argv[1] == "rm":
            return 0
        return 0
    print(f"unsupported fake adb command: {argv}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
