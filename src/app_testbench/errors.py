"""Typed errors with stable process exit codes."""

from __future__ import annotations


class RunnerError(Exception):
    """Base class for expected app-testbench failures."""

    exit_code = 1
    kind = "runner_error"

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ConfigError(RunnerError):
    exit_code = 2
    kind = "config_error"


class FlowError(RunnerError):
    exit_code = 2
    kind = "flow_error"


class EnvironmentNotReady(RunnerError):
    exit_code = 3
    kind = "environment_error"


class ExternalCommandError(RunnerError):
    kind = "external_command_error"

    def __init__(
        self,
        message: str,
        *,
        command: list[str] | None = None,
        returncode: int | None = None,
        stdout: str = "",
        stderr: str = "",
        hint: str | None = None,
    ) -> None:
        super().__init__(message, hint=hint)
        self.command = command or []
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class CommandTimeout(RunnerError):
    kind = "timeout"

    def __init__(self, command: list[str], timeout: float) -> None:
        super().__init__(
            f"Command timed out after {timeout:g}s: {' '.join(command)}",
            hint="Close stuck emulator processes or increase --timeout.",
        )
        self.command = command
        self.timeout = timeout


class DeviceError(RunnerError):
    kind = "device_error"


class MuMuError(RunnerError):
    kind = "mumu_error"


class StepFailure(RunnerError):
    kind = "step_failure"
