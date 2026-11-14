#!/usr/bin/env python3
"""Deterministic MuMuManager fixture used by the test suite."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

INSTANCE = {
    "name": "Fake Phone",
    "player_state": "running",
    "is_android_started": True,
    "adb_port": 16384,
    "adb_host_ip": "127.0.0.1",
    "android_version": "12.0",
}


def log(argv: list[str]) -> None:
    state = os.environ.get("FAKE_MUMU_STATE")
    if not state:
        return
    path = Path(state) / "mumu-commands.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(argv, ensure_ascii=False) + "\n")


def main() -> int:
    argv = sys.argv[1:]
    log(argv)
    if argv == ["version"]:
        print(json.dumps({"version": "15.0.0"}))
        return 0
    if argv[:3] == ["info", "-v", "all"]:
        payload = [INSTANCE] if os.environ.get("FAKE_MUMU_ARRAY") == "1" else {"0": INSTANCE}
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    if len(argv) >= 3 and argv[:2] == ["info", "-v"]:
        index = argv[2]
        print(json.dumps({index: INSTANCE}, ensure_ascii=False))
        return 0
    if len(argv) >= 4 and argv[0] == "control":
        if os.environ.get("FAKE_MUMU_CONTROL_FAILURE") == "1":
            print(json.dumps({"success": False, "message": "fake control failure"}))
            return 0
        print(json.dumps({"success": True, "action": argv[-1]}))
        return 0
    print(f"unsupported fake MuMuManager command: {argv}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
