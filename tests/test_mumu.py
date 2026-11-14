from __future__ import annotations

import json
from pathlib import Path

import pytest

from app_testbench.errors import MuMuError
from app_testbench.models import Instance
from app_testbench.mumu import MuMuManagerClient
from app_testbench.utils import ProcessRunner


def test_mumu_manager_adapter(fake_tools: dict[str, Path]) -> None:
    client = MuMuManagerClient(fake_tools["manager"], ProcessRunner(10))
    assert client.version() == "15.0.0"

    instances = client.list_instances()
    assert len(instances) == 1
    instance = instances[0]
    assert instance.index == 0
    assert instance.running is True
    assert instance.serial == "127.0.0.1:16384"
    assert instance.android_version == "12.0"

    assert client.instance(0).name == "Fake Phone"
    assert client.resolve_serial(0) == "127.0.0.1:16384"
    assert "launch" in client.control(0, "launch")

    commands = [
        json.loads(line)
        for line in (fake_tools["mumu_state"] / "mumu-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert ["version"] in commands
    assert ["info", "-v", "all"] in commands
    assert ["control", "-v", "0", "launch"] in commands


def test_instance_running_respects_process_started_when_state_is_unknown() -> None:
    stopped = Instance(
        index=0,
        name="MuMu Android",
        player_state="unknown",
        android_started=False,
        adb_port=None,
        adb_host="127.0.0.1",
        process_started=False,
    )
    running = Instance(
        index=0,
        name="MuMu Android",
        player_state="unknown",
        android_started=False,
        adb_port=None,
        adb_host="127.0.0.1",
        process_started=True,
    )
    assert stopped.running is False
    assert running.running is True


def test_list_instances_accepts_top_level_array(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_MUMU_ARRAY", "1")
    client = MuMuManagerClient(fake_tools["manager"], ProcessRunner(10))
    instances = client.list_instances()
    assert len(instances) == 1
    assert instances[0].name == "Fake Phone"
    assert instances[0].running is True


def test_wait_until_running_waits_for_android_start(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    client = MuMuManagerClient(fake_tools["manager"], ProcessRunner(10))
    booting = Instance(
        index=0,
        name="MuMu Android",
        player_state="running",
        android_started=False,
        adb_port=16384,
        adb_host="127.0.0.1",
        process_started=True,
    )
    ready = Instance(
        index=0,
        name="MuMu Android",
        player_state="running",
        android_started=True,
        adb_port=16384,
        adb_host="127.0.0.1",
        process_started=True,
    )
    responses = iter([booting, ready])
    clock = [0.0]

    def fake_sleep(seconds: float) -> None:
        clock[0] += seconds

    monkeypatch.setattr(client, "instance", lambda _: next(responses))
    monkeypatch.setattr("app_testbench.mumu.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("app_testbench.mumu.time.sleep", fake_sleep)

    assert client.wait_until_running(0, timeout=5) is ready
    assert clock[0] == 1.0


def test_control_rejects_json_failure(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_MUMU_CONTROL_FAILURE", "1")
    client = MuMuManagerClient(fake_tools["manager"], ProcessRunner(10))
    with pytest.raises(MuMuError, match="reported failure"):
        client.control(0, "shutdown")


def test_resolve_serial_does_not_probe_other_instance_ports_when_target_is_stopped(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    client = MuMuManagerClient(fake_tools["manager"], ProcessRunner(10))
    stopped = Instance(
        index=0,
        name="target-stopped",
        player_state="stopped",
        android_started=False,
        adb_port=None,
        adb_host="127.0.0.1",
        process_started=False,
    )
    monkeypatch.setattr(client, "instance", lambda _: stopped)
    monkeypatch.setattr("app_testbench.mumu._port_open", lambda *args, **kwargs: True)

    assert client.resolve_serial(0) == "127.0.0.1:16384"


def test_resolve_serial_probes_fallback_ports_when_target_is_running(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    client = MuMuManagerClient(fake_tools["manager"], ProcessRunner(10))
    running = Instance(
        index=0,
        name="target-running",
        player_state="running",
        android_started=True,
        adb_port=None,
        adb_host="127.0.0.1",
        process_started=True,
    )
    monkeypatch.setattr(client, "instance", lambda _: running)
    monkeypatch.setattr("app_testbench.mumu._port_open", lambda host, port: port == 16416)

    assert client.resolve_serial(0) == "127.0.0.1:16416"


def test_wait_until_running_does_not_sleep_past_timeout(
    fake_tools: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    client = MuMuManagerClient(fake_tools["manager"], ProcessRunner(10))
    clock = [0.0]
    sleeps: list[float] = []

    def unavailable(_: int) -> Instance:
        raise MuMuError("not ready")

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr(client, "instance", unavailable)
    monkeypatch.setattr("app_testbench.mumu.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("app_testbench.mumu.time.sleep", fake_sleep)

    with pytest.raises(MuMuError, match="could not be queried"):
        client.wait_until_running(0, timeout=0.25)
    assert sleeps == [0.25]
