"""MuMuManager adapter for instance lifecycle and ADB endpoint discovery."""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path
from typing import Any

from app_testbench.errors import MuMuError
from app_testbench.models import Instance
from app_testbench.utils import ProcessRunner


def _parse_json_payload(text: str) -> Any:
    stripped = text.lstrip("\ufeff \t\r\n")
    decoder = json.JSONDecoder()
    for start, character in enumerate(stripped):
        if character not in "[{":
            continue
        try:
            payload, _ = decoder.raw_decode(stripped, start)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, (dict, list)):
            return payload
    raise ValueError("no JSON object or array found")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "running"}
    return False


def _as_optional_bool(value: Any) -> bool | None:
    return None if value is None else _as_bool(value)


def _as_int(value: Any) -> int | None:
    if value in (None, "", 0, "0"):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    probe_host = host.removeprefix("[").removesuffix("]")
    try:
        with socket.create_connection((probe_host, port), timeout=timeout):
            return True
    except OSError:
        return False


class MuMuManagerClient:
    def __init__(self, executable: Path, runner: ProcessRunner) -> None:
        self.executable = executable
        self.runner = runner

    def _run(self, *args: str, check: bool = True) -> Any:
        result = self.runner.run(
            [str(self.executable), *args],
            check=False,
        )
        if check and result.returncode != 0:
            raise MuMuError(
                f"MuMuManager failed: {' '.join(args)}",
                hint=result.combined_output or "Run `app-testbench doctor`.",
            )
        return result

    def version(self) -> str:
        result = self._run("version")
        output = result.combined_output
        try:
            payload = _parse_json_payload(output)
        except (ValueError, json.JSONDecodeError):
            return output.splitlines()[0].strip() if output else "unknown"
        if isinstance(payload, dict) and payload.get("version"):
            return str(payload["version"])
        return output.splitlines()[0].strip() if output else "unknown"

    def _instance_from_mapping(self, index: int, payload: dict[str, Any]) -> Instance:
        state = str(payload.get("player_state", "") or "")
        return Instance(
            index=index,
            name=str(
                payload.get("name")
                or payload.get("player_name")
                or payload.get("vm_name")
                or f"instance-{index}"
            ),
            player_state=state or "unknown",
            android_started=_as_bool(payload.get("is_android_started")),
            process_started=_as_optional_bool(payload.get("is_process_started")),
            adb_port=_as_int(payload.get("adb_port")),
            adb_host=str(
                payload.get("adb_host_ip")
                or payload.get("host_ip")
                or payload.get("adb_host")
                or "127.0.0.1"
            ),
            android_version=(
                str(payload["android_version"]) if payload.get("android_version") else None
            ),
            raw=payload,
        )

    def list_instances(self) -> list[Instance]:
        result = self._run("info", "-v", "all")
        try:
            payload = _parse_json_payload(result.combined_output)
        except (ValueError, json.JSONDecodeError) as exc:
            preview = result.combined_output[:500] or "<empty>"
            raise MuMuError(
                "MuMuManager did not return valid instance JSON.",
                hint=f"Output: {preview}",
            ) from exc

        instances: list[Instance] = []
        if isinstance(payload, dict) and "player_state" in payload:
            instances.append(self._instance_from_mapping(0, payload))
        elif isinstance(payload, dict):
            for key, value in payload.items():
                if not isinstance(value, dict):
                    continue
                try:
                    index = int(key)
                except (TypeError, ValueError):
                    continue
                instances.append(self._instance_from_mapping(index, value))
        elif isinstance(payload, list):
            for index, value in enumerate(payload):
                if isinstance(value, dict):
                    instances.append(self._instance_from_mapping(index, value))
        return sorted(instances, key=lambda item: item.index)

    def instance(self, index: int) -> Instance:
        result = self._run("info", "-v", str(index))
        try:
            payload = _parse_json_payload(result.combined_output)
        except (ValueError, json.JSONDecodeError) as exc:
            raise MuMuError(
                f"Could not read MuMu instance {index}.",
                hint=result.combined_output[:500],
            ) from exc
        if isinstance(payload, dict):
            wrapped = payload.get(str(index))
            if isinstance(wrapped, dict):
                return self._instance_from_mapping(index, wrapped)
            if "player_state" in payload:
                return self._instance_from_mapping(index, payload)
        raise MuMuError(f"MuMu instance {index} was not present in MuMuManager output.")

    def control(self, index: int, action: str) -> str:
        if action not in {"launch", "shutdown", "restart", "show_window", "hide_window"}:
            raise MuMuError(f"Unsupported MuMu control action: {action}")
        result = self._run("control", "-v", str(index), action)
        try:
            payload = _parse_json_payload(result.combined_output)
        except (ValueError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict) and "success" in payload and not _as_bool(payload["success"]):
            detail = payload.get("message") or payload.get("error") or payload.get("msg")
            hint = str(detail) if detail else (result.combined_output[:500] or None)
            raise MuMuError(
                f"MuMuManager reported failure for {action} on instance {index}.",
                hint=hint,
            )
        return result.combined_output or f"{action} requested"

    def wait_until_running(self, index: int, timeout: float = 60.0) -> Instance:
        deadline = time.monotonic() + timeout

        def sleep_until_next_poll() -> None:
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(1.0, remaining))

        last: Instance | None = None
        while time.monotonic() < deadline:
            try:
                last = self.instance(index)
            except MuMuError:
                sleep_until_next_poll()
                continue
            if last.running and last.android_started:
                return last
            sleep_until_next_poll()
        if last:
            raise MuMuError(
                f"Instance {index} did not become ready within {timeout:g}s "
                f"(state: {last.player_state}, android_started: {last.android_started}, "
                f"process_started: {last.process_started})."
            )
        raise MuMuError(f"Instance {index} could not be queried within {timeout:g}s.")

    def resolve_serial(self, index: int, explicit: str | None = None) -> str:
        if explicit:
            return explicit
        instance_running = False
        try:
            instance = self.instance(index)
            host = instance.adb_host or "127.0.0.1"
            reported_port = instance.adb_port
            instance_running = instance.running
        except MuMuError:
            host = "127.0.0.1"
            reported_port = None

        base_port = 16384 + 32 * index
        candidates: list[int] = []
        if reported_port:
            candidates.append(reported_port)
        elif instance_running:
            candidates.extend(base_port + 32 * offset for offset in range(6))
        port = next(
            (candidate for candidate in dict.fromkeys(candidates) if _port_open(host, candidate)),
            reported_port or base_port,
        )
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        return f"{host}:{port}"
