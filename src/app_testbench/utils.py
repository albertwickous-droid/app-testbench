"""Shared utilities and the subprocess boundary."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app_testbench.errors import CommandTimeout, ConfigError, ExternalCommandError


def now_iso() -> str:
    """Return an ISO-8601 timestamp with the local timezone offset."""

    return datetime.now().astimezone().isoformat(timespec="seconds")


def elapsed_ms(started: float) -> int:
    return max(0, round((time.monotonic() - started) * 1000))


def duration_label(milliseconds: int) -> str:
    if milliseconds < 1000:
        return f"{milliseconds} ms"
    seconds = milliseconds / 1000
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {seconds:.0f}s"


def slugify(value: str, *, fallback: str = "item", max_length: int = 64) -> str:
    """Create a portable artifact filename stem."""

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value:
        value = fallback
    return value[:max_length].rstrip("-") or fallback


def unique_path(path: Path) -> Path:
    """Return ``path`` or a numbered sibling that does not exist."""

    if not path.exists():
        return path
    for index in range(2, 10_000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise ConfigError(f"Could not allocate a unique path under {path.parent}")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        Path(temporary).replace(path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def truncate_text(value: str, limit: int) -> str:
    if limit <= 0 or len(value) <= limit:
        return value
    return value[:limit] + f"\n... truncated ({len(value) - limit} chars omitted)"


def coerce_bool(value: Any, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    raise ConfigError(f"{field} must be a boolean")


def parse_positive_int(value: Any, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise ConfigError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field} must be an integer") from exc
    if parsed < minimum:
        raise ConfigError(f"{field} must be >= {minimum}")
    return parsed


def parse_float(value: Any, *, field: str, minimum: float = 0.0) -> float:
    if isinstance(value, bool):
        raise ConfigError(f"{field} must be a number")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field} must be a number") from exc
    if parsed < minimum:
        raise ConfigError(f"{field} must be >= {minimum:g}")
    return parsed


def path_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


@dataclass(slots=True)
class ProcessResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int

    @property
    def combined_output(self) -> str:
        parts = [part.strip() for part in (self.stdout, self.stderr) if part.strip()]
        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
        }


@dataclass(slots=True)
class BinaryResult:
    command: list[str]
    returncode: int
    stdout: bytes
    stderr: bytes
    duration_ms: int


class ProcessRunner:
    """Wrapper around subprocess with deadlines and hidden console windows."""

    def __init__(self, default_timeout: float = 30.0) -> None:
        self.default_timeout = default_timeout

    @staticmethod
    def _creation_flags() -> int:
        if os.name == "nt":
            return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return 0

    def run(
        self,
        command: list[str],
        *,
        timeout: float | None = None,
        check: bool = False,
        input_text: str | None = None,
    ) -> ProcessResult:
        timeout = timeout or self.default_timeout
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                input=input_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                creationflags=self._creation_flags(),
            )
        except subprocess.TimeoutExpired as exc:
            raise CommandTimeout(command, timeout) from exc
        except FileNotFoundError as exc:
            raise ExternalCommandError(
                f"Executable not found: {command[0]}",
                command=command,
                hint="Run `app-testbench doctor` or pass --adb / --mumumanager explicitly.",
            ) from exc
        except OSError as exc:
            raise ExternalCommandError(
                f"Could not start {command[0]}: {exc}",
                command=command,
            ) from exc

        result = ProcessResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            duration_ms=elapsed_ms(started),
        )
        if check and result.returncode != 0:
            raise ExternalCommandError(
                f"Command failed with exit code {result.returncode}: {command[0]}",
                command=command,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        return result

    def run_bytes(
        self,
        command: list[str],
        *,
        timeout: float | None = None,
        check: bool = False,
    ) -> BinaryResult:
        timeout = timeout or self.default_timeout
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=False,
                timeout=timeout,
                check=False,
                creationflags=self._creation_flags(),
            )
        except subprocess.TimeoutExpired as exc:
            raise CommandTimeout(command, timeout) from exc
        except FileNotFoundError as exc:
            raise ExternalCommandError(
                f"Executable not found: {command[0]}",
                command=command,
                hint="Run `app-testbench doctor` or pass --adb explicitly.",
            ) from exc
        except OSError as exc:
            raise ExternalCommandError(
                f"Could not start {command[0]}: {exc}",
                command=command,
            ) from exc

        result = BinaryResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout or b"",
            stderr=completed.stderr or b"",
            duration_ms=elapsed_ms(started),
        )
        if check and result.returncode != 0:
            raise ExternalCommandError(
                f"Command failed with exit code {result.returncode}: {command[0]}",
                command=command,
                returncode=result.returncode,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"),
            )
        return result


def command_label(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)
