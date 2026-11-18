"""Serializable data models used by the CLI and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app_testbench import SCHEMA_VERSION


@dataclass(slots=True)
class Instance:
    index: int
    name: str
    player_state: str
    android_started: bool
    adb_port: int | None
    adb_host: str
    android_version: str | None = None
    process_started: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def running(self) -> bool:
        if self.process_started is not None:
            return self.process_started
        state = self.player_state.strip().lower()
        if state in {"", "unknown"}:
            return self.android_started or self.adb_port is not None
        return self.android_started or (
            bool(state) and "stopped" not in state and "shutting" not in state
        )

    @property
    def serial(self) -> str | None:
        if not self.adb_port:
            return None
        host = self.adb_host or "127.0.0.1"
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        return f"{host}:{self.adb_port}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "player_state": self.player_state,
            "running": self.running,
            "android_started": self.android_started,
            "process_started": self.process_started,
            "adb_port": self.adb_port,
            "adb_host": self.adb_host,
            "serial": self.serial,
            "android_version": self.android_version,
        }


@dataclass(slots=True)
class Check:
    name: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


@dataclass(slots=True)
class StepResult:
    id: str
    name: str
    action: str
    section: str
    status: str
    started_at: str
    finished_at: str = ""
    duration_ms: int = 0
    description: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    hint: str | None = None
    screenshots: list[str] = field(default_factory=list)
    ui_files: list[str] = field(default_factory=list)
    logcat_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "action": self.action,
            "section": self.section,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "description": self.description,
            "params": self.params,
            "output": self.output,
            "error": self.error,
            "hint": self.hint,
            "screenshots": self.screenshots,
            "ui_files": self.ui_files,
            "logcat_paths": self.logcat_paths,
        }


@dataclass(slots=True)
class RunResult:
    name: str
    status: str
    started_at: str
    finished_at: str
    duration_ms: int
    environment: dict[str, Any]
    config: dict[str, Any]
    steps: list[StepResult] = field(default_factory=list)
    logcat_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    output_dir: str = ""
    report_path: str = ""
    result_path: str = ""
    junit_path: str = ""
    manifest_path: str = ""

    @property
    def passed(self) -> int:
        return sum(step.status == "passed" for step in self.steps)

    @property
    def failed(self) -> int:
        return sum(step.status == "failed" for step in self.steps)

    @property
    def skipped(self) -> int:
        return sum(step.status == "skipped" for step in self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "total": len(self.steps),
            },
            "environment": self.environment,
            "config": self.config,
            "steps": [step.to_dict() for step in self.steps],
            "logcat_paths": self.logcat_paths,
            "warnings": self.warnings,
            "output_dir": self.output_dir,
            "report_path": self.report_path,
            "result_path": self.result_path,
            "junit_path": self.junit_path,
            "manifest_path": self.manifest_path,
        }
