"""Flow execution engine with artifact collection and failure handling."""

from __future__ import annotations

import platform
import time
from pathlib import Path
from typing import Any

from app_testbench.config import Settings
from app_testbench.device import AndroidDevice
from app_testbench.errors import RunnerError, StepFailure
from app_testbench.flow import Flow, FlowStep
from app_testbench.models import RunResult, StepResult
from app_testbench.mumu import MuMuManagerClient
from app_testbench.reporting import create_run_directory, write_run_artifacts
from app_testbench.utils import ProcessRunner, elapsed_ms, now_iso, slugify, unique_path


class FlowRunner:
    def __init__(
        self,
        settings: Settings,
        flow: Flow,
        *,
        output_base: Path | None = None,
        runner: ProcessRunner | None = None,
        junit_path: Path | None = None,
        wait_for_boot: bool | None = None,
        boot_timeout: float | None = None,
        boot_interval: float = 1.0,
        flow_timeout: float | None = None,
    ) -> None:
        self.settings = settings
        self.flow = flow
        self.output_base = output_base or (Path.cwd() / "runs")
        self.runner = runner or ProcessRunner(settings.timeout)
        self.junit_path = junit_path.expanduser().resolve() if junit_path else None
        self.wait_for_boot = wait_for_boot
        self.boot_timeout = boot_timeout
        self.boot_interval = boot_interval
        self.flow_timeout = flow_timeout if flow_timeout is not None else flow.timeout_seconds
        self._deadline: float | None = None
        self.output_dir: Path | None = None
        self.device: AndroidDevice | None = None
        self.manager: MuMuManagerClient | None = None
        self.warnings: list[str] = []
        self.logcat_paths: list[str] = []
        self.environment: dict[str, Any] = {}

    def _relative(self, path: Path) -> str:
        assert self.output_dir is not None
        try:
            return path.resolve().relative_to(self.output_dir.resolve()).as_posix()
        except ValueError:
            return str(path.resolve())

    def _artifact(self, relative: str) -> Path:
        assert self.output_dir is not None
        return self.output_dir / relative

    def _environment(self, instance: int, serial: str | None) -> dict[str, Any]:
        return {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "adb": str(self.settings.adb) if self.settings.adb else None,
            "mumu_manager": (
                str(self.settings.mumu_manager) if self.settings.mumu_manager else None
            ),
            "instance": instance,
            "serial": serial,
            "timeout_seconds": self.settings.timeout,
            "flow_timeout_seconds": self.flow_timeout,
        }

    def _make_result(
        self,
        *,
        started_at: str,
        started: float,
        steps: list[StepResult],
        status: str,
    ) -> RunResult:
        return RunResult(
            name=self.flow.name,
            status=status,
            started_at=started_at,
            finished_at=now_iso(),
            duration_ms=elapsed_ms(started),
            environment=self.environment,
            config={
                "flow_path": str(self.flow.path),
                "description": self.flow.description,
                "device": self.flow.device,
                "report": self.flow.report,
                "flow_timeout_seconds": self.flow_timeout,
            },
            steps=steps,
            logcat_paths=self.logcat_paths,
            warnings=self.warnings,
        )

    def _connect(self, instance: int, requested_serial: str | None) -> None:
        adb = self.settings.require_adb()
        if self.settings.mumu_manager:
            self.manager = MuMuManagerClient(self.settings.mumu_manager, self.runner)
            try:
                self.environment["mumu_version"] = self.manager.version()
            except RunnerError as exc:
                self.warnings.append(f"Could not read MuMuManager version: {exc}")

        serial = requested_serial
        if not serial and self.manager:
            try:
                serial = self.manager.resolve_serial(instance)
            except RunnerError as exc:
                self.warnings.append(f"Could not resolve MuMu ADB port: {exc}")

        self.device = AndroidDevice(adb, self.runner, serial)
        try:
            self.environment["adb_version"] = self.device.version()
        except RunnerError as exc:
            self.warnings.append(f"Could not read ADB version: {exc}")
        self.device.connect()
        self.environment["serial"] = self.device.serial
        wait_for_boot = self.wait_for_boot
        if wait_for_boot is None:
            wait_for_boot = bool(self.flow.device.get("wait_for_boot", False))
        if wait_for_boot:
            boot_timeout = (
                self.boot_timeout
                if self.boot_timeout is not None
                else float(self.flow.device.get("boot_timeout", 60))
            )
            try:
                self.environment["boot"] = self.device.wait_until_boot_complete(
                    timeout=boot_timeout,
                    interval=self.boot_interval,
                )
            except RunnerError as exc:
                self.environment["boot"] = {
                    "ready": False,
                    "timeout_seconds": boot_timeout,
                    "error": str(exc),
                }
                raise
        if self.flow.report.get("clear_logcat"):
            self.device.clear_logcat()

    def _failure_step(self, message: str, *, error: RunnerError) -> StepResult:
        return StepResult(
            id="environment-connect",
            name="Connect to device",
            action="connect",
            section="environment",
            status="failed",
            started_at=now_iso(),
            duration_ms=0,
            error=message,
            hint=error.hint,
        )

    def run(self) -> RunResult:
        started_at = now_iso()
        started = time.monotonic()
        instance = (
            self.settings.instance
            if self.settings.instance_explicit
            else int(self.flow.device.get("instance", self.settings.instance or 0))
        )
        requested_serial = (
            self.settings.serial
            if self.settings.serial_explicit
            else self.flow.device.get("serial") or self.settings.serial
        )
        self.environment = self._environment(instance, requested_serial)
        self.output_dir = create_run_directory(self.output_base, self.flow.name)

        steps: list[StepResult] = []
        status = "passed"
        aborted = False
        try:
            self._connect(instance, requested_serial)
        except RunnerError as exc:
            self.warnings.append(str(exc))
            steps.append(self._failure_step(str(exc), error=exc))
            steps.extend(self._skipped_steps(self.flow.all_steps, "Device connection failed."))
            status = "failed"
        else:
            self._deadline = (
                time.monotonic() + self.flow_timeout if self.flow_timeout is not None else None
            )
            setup_ok = self._run_section(self.flow.setup, steps)
            if setup_ok:
                main_ok = self._run_section(self.flow.steps, steps)
                aborted = not main_ok
            else:
                aborted = True
                steps.extend(
                    self._skipped_steps(
                        self.flow.steps, "Setup failed; main steps were not executed."
                    )
                )
            if self.flow.teardown:
                # Teardown is evidence/cleanup work; let it run even after the
                # main budget expires, while still respecting per-command timeouts.
                self._run_section(
                    self.flow.teardown,
                    steps,
                    force_continue=True,
                    respect_deadline=False,
                )
            failed = aborted or any(step.status == "failed" for step in steps)
            if failed:
                status = "failed"
            self._capture_final_logcat(force=failed)

        result = self._make_result(
            started_at=started_at,
            started=started,
            steps=steps,
            status=status,
        )
        if self.junit_path is not None:
            result.junit_path = str(self.junit_path)
        write_run_artifacts(result, self.output_dir)
        return result

    def _budget_expired(self) -> bool:
        return self._deadline is not None and time.monotonic() >= self._deadline

    def _timeout_step(self, step: FlowStep) -> StepResult:
        return StepResult(
            id=step.id,
            name=step.name,
            action=step.action,
            section=step.section,
            status="failed",
            started_at=now_iso(),
            description=step.description,
            params=step.params,
            error=f"Flow timeout exceeded ({self.flow_timeout:g}s).",
            hint="The flow budget expired before this step started; teardown will still run.",
            output={"reason": "flow_timeout", "timeout_seconds": self.flow_timeout},
        )

    def _run_section(
        self,
        section: list[FlowStep],
        steps: list[StepResult],
        *,
        force_continue: bool = False,
        respect_deadline: bool = True,
    ) -> bool:
        all_passed = True
        for index, step in enumerate(section):
            if respect_deadline and self._budget_expired():
                steps.append(self._timeout_step(step))
                remaining = section[index + 1 :]
                if remaining:
                    steps.extend(self._skipped_steps(remaining, "Flow timeout exceeded."))
                return False
            result = self._execute_step(step)
            steps.append(result)
            if result.status == "failed":
                all_passed = False
                if not step.continue_on_error and not force_continue:
                    remaining = section[index + 1 :]
                    if remaining:
                        steps.extend(
                            self._skipped_steps(
                                remaining,
                                f"Aborted after step {step.id} failed.",
                            )
                        )
                    return False
        return all_passed

    def _skipped_steps(self, section: list[FlowStep], reason: str) -> list[StepResult]:
        return [
            StepResult(
                id=step.id,
                name=step.name,
                action=step.action,
                section=step.section,
                status="skipped",
                started_at=now_iso(),
                description=step.description,
                params=step.params,
                output={"reason": reason},
            )
            for step in section
        ]

    def _capture_screenshot(
        self,
        step: FlowStep,
        result: StepResult,
        label: str,
        *,
        soft: bool,
    ) -> None:
        assert self.device is not None
        assert self.output_dir is not None
        filename = f"{slugify(step.id, fallback='step')}-{label}.png"
        path = self.output_dir / "screenshots" / filename
        if path.exists():
            path = path.with_name(f"{path.stem}-{len(result.screenshots) + 1}.png")
        try:
            self.device.screenshot(path)
        except RunnerError as exc:
            if soft:
                self.warnings.append(f"Screenshot for {step.id} failed: {exc}")
                return
            raise
        result.screenshots.append(self._relative(path))

    def _capture_final_logcat(self, *, force: bool = False) -> None:
        if not self.device:
            return
        report = self.flow.report
        if not force and not report.get("collect_logcat", True):
            return
        assert self.output_dir is not None
        path = unique_path(self.output_dir / "logs" / "logcat-final.txt")
        try:
            self.device.logcat(path, lines=2000, clear=False)
        except RunnerError as exc:
            self.warnings.append(f"Final logcat capture failed: {exc}")
            return
        self.logcat_paths.append(self._relative(path))

    def _execute_step(self, step: FlowStep) -> StepResult:
        started_at = now_iso()
        started = time.monotonic()
        result = StepResult(
            id=step.id,
            name=step.name,
            action=step.action,
            section=step.section,
            status="passed",
            started_at=started_at,
            description=step.description,
            params=step.params,
        )
        try:
            result.output = self._perform_action(step, result)
            capture_all = self.flow.report.get("capture_screenshots") == "all"
            if step.action != "screenshot" and (capture_all or step.screenshot):
                self._capture_screenshot(step, result, "after", soft=True)
        except RunnerError as exc:
            result.status = "failed"
            result.error = str(exc)
            result.hint = exc.hint
            if step.action != "screenshot" and (
                self.flow.report.get("capture_screenshots") in {"all", "failures"}
                or step.screenshot
            ):
                self._capture_screenshot(step, result, "failure", soft=True)
        except Exception as exc:
            result.status = "failed"
            result.error = f"Unexpected step error: {exc}"
        result.duration_ms = elapsed_ms(started)
        return result

    def _perform_action(self, step: FlowStep, result: StepResult) -> dict[str, Any]:
        assert self.device is not None
        assert self.output_dir is not None
        params = step.params
        action = step.action

        if action == "install":
            message = self.device.install(
                Path(params["apk"]),
                reinstall=bool(params.get("reinstall", True)),
                grant_permissions=bool(params.get("grant_permissions", False)),
                expected_package=params.get("expected_package"),
                expected_version_code=params.get("expected_version_code"),
                expected_version_name=params.get("expected_version_name"),
            )
        elif action == "launch":
            message = self.device.launch(params["package"], params.get("activity"))
        elif action == "open":
            message = self.device.open_uri(
                params["uri"],
                package=params.get("package"),
                mime_type=params.get("mime_type"),
            )
        elif action == "close":
            message = self.device.close(params["package"])
        elif action == "clear_app_data":
            message = self.device.clear_app_data(params["package"])
        elif action == "orientation":
            message = self.device.set_orientation(params["mode"])
        elif action == "reverse_port":
            message = self.device.reverse_port(
                params["port"],
                local_port=params.get("local_port"),
                remove=bool(params.get("remove", False)),
            )
        elif action == "tap":
            message = self.device.tap(params["x"], params["y"])
        elif action == "tap_text":
            return self._perform_tap_text(step, result)
        elif action == "clear_text":
            message = self.device.clear_text(int(params["count"]))
        elif action == "swipe":
            message = self.device.swipe(
                params["x1"],
                params["y1"],
                params["x2"],
                params["y2"],
                params["duration_ms"],
            )
        elif action == "text":
            message = self.device.input_text(params["text"])
        elif action == "keyevent":
            message = self.device.keyevent(params["key"])
        elif action == "back":
            message = self.device.back()
        elif action == "home":
            message = self.device.home()
        elif action == "wait":
            time.sleep(float(params["seconds"]))
            message = f"Waited {float(params['seconds']):g}s"
        elif action == "screenshot":
            name = params.get("label") or step.id
            self._capture_screenshot(step, result, slugify(name, fallback="shot"), soft=False)
            message = "Screenshot captured"
        elif action == "dump_ui":
            name = params.get("label") or step.id
            path = unique_path(self.output_dir / "ui" / f"{slugify(name, fallback='ui')}.xml")
            self.device.dump_ui(path)
            result.ui_files.append(self._relative(path))
            texts = self.device.ui_text(path)
            return {
                "message": "UI hierarchy captured",
                "nodes": self.device.ui_node_count(path),
                "text_preview": texts[:30],
            }
        elif action == "logcat":
            name = params.get("label") or step.id
            path = unique_path(self.output_dir / "logs" / f"{slugify(name, fallback='logcat')}.txt")
            self.device.logcat(path, lines=params.get("lines", 1000), clear=False)
            relative = self._relative(path)
            self.logcat_paths.append(relative)
            return {"message": "Logcat captured", "path": relative}
        elif action == "wait_for_activity":
            return self._perform_activity_wait(step)
        elif action == "assert_logcat_contains":
            return self._perform_logcat_assertion(step)
        elif action in {
            "assert_ui_contains",
            "assert_ui_not_contains",
            "wait_for_text",
            "wait_for_text_gone",
        }:
            return self._perform_ui_assertion(action, step, result)
        else:
            raise StepFailure(f"Unsupported action: {action}")
        output: dict[str, Any] = {"message": message}
        if action == "install" and self.device.last_package_identity is not None:
            output["package_identity"] = self.device.last_package_identity
        return output

    def _perform_activity_wait(self, step: FlowStep) -> dict[str, Any]:
        assert self.device is not None
        params = step.params
        expected = str(params["activity"])
        deadline = time.monotonic() + float(params.get("timeout", 30))
        interval = float(params.get("interval", 0.5))
        attempts = 0
        last_identity: dict[str, str] | None = None
        last_error: str | None = None

        while True:
            attempts += 1
            try:
                observed = self.device.top_activity()
            except RunnerError as exc:
                last_identity = None
                last_error = str(exc)
            else:
                last_identity = observed
                last_error = None
                if observed["component"] == expected:
                    return {
                        "message": f"Top Activity matched: {expected}",
                        "attempts": attempts,
                        "expected_activity": expected,
                        "observed_activity": observed["component"],
                    }

            if time.monotonic() >= deadline:
                if last_identity is not None:
                    hint = (
                        f"Expected {expected}; last observed {last_identity['component']}. "
                        f"Source: {last_identity.get('source_line', '')}"
                    )
                elif last_error is not None:
                    hint = f"Last Activity probe error: {last_error}"
                else:
                    hint = "No Activity probe result was available."
                raise StepFailure(
                    f"Top Activity did not match within {float(params.get('timeout', 30)):g}s: "
                    f"{expected}",
                    hint=hint[:2000],
                )
            time.sleep(min(interval, max(0.0, deadline - time.monotonic())))

    def _perform_logcat_assertion(self, step: FlowStep) -> dict[str, Any]:
        assert self.device is not None
        params = step.params
        target = str(params["text"])
        ignore_case = bool(params.get("ignore_case", False))
        text = self.device.logcat_text(lines=int(params.get("lines", 5000)))
        needle = target.casefold() if ignore_case else target
        matched = [
            line.strip()
            for line in text.splitlines()
            if needle in (line.casefold() if ignore_case else line)
        ]
        if not matched:
            recent = text.splitlines()[-10:]
            detail = "\n".join(recent) if recent else "<no logcat output>"
            raise StepFailure(
                f"Logcat did not contain: {target}",
                hint=f"Last {len(recent)} logcat line(s):\n{detail[:2000]}",
            )
        return {
            "message": f"Found logcat text: {target}",
            "match_count": len(matched),
            "matched_line": matched[-1][:1000],
        }

    def _perform_tap_text(self, step: FlowStep, result: StepResult) -> dict[str, Any]:
        assert self.device is not None
        params = step.params
        target = str(params["text"])
        field = str(params.get("field", "any"))
        match = str(params.get("match", "contains"))
        ignore_case = bool(params.get("ignore_case", False))
        needle = target.casefold() if ignore_case else target
        wanted_index = int(params.get("index", 0))
        deadline = time.monotonic() + float(params.get("timeout", 10))
        interval = float(params.get("interval", 0.5))
        attempts = 0
        last_dump_error: str | None = None
        last_texts: list[str] = []

        while True:
            attempts += 1
            try:
                texts, xml_path = self._dump_ui_for_result(step, result)
                nodes = self.device.ui_nodes(xml_path)
                last_texts = texts
                last_dump_error = None
            except RunnerError as exc:
                last_dump_error = str(exc)
                nodes = []

            matches: list[tuple[dict[str, Any], str, str]] = []
            for node in nodes:
                if not bool(node.get("enabled", True)):
                    continue
                candidates: list[tuple[str, str]] = []
                if field in {"any", "text"}:
                    candidates.append(("text", str(node.get("text", ""))))
                if field in {"any", "content-desc"}:
                    candidates.append(("content-desc", str(node.get("content_desc", ""))))
                for candidate_field, value in candidates:
                    if not value:
                        continue
                    haystack = value.casefold() if ignore_case else value
                    matched = haystack == needle if match == "exact" else needle in haystack
                    if matched:
                        matches.append((node, candidate_field, value))
                        break

            if wanted_index < len(matches):
                node, matched_field, matched_value = matches[wanted_index]
                x, y = node["center"]
                self.device.tap(int(x), int(y))
                return {
                    "message": f"Tapped UI {matched_field}: {matched_value}",
                    "attempts": attempts,
                    "found": True,
                    "matched_field": matched_field,
                    "matched_value": matched_value,
                    "bounds": node["bounds"],
                    "tap": {"x": int(x), "y": int(y)},
                }

            if time.monotonic() >= deadline:
                detail = ", ".join(repr(value) for value in last_texts[:20])
                hint = f"Visible text: {detail or '<none>'}"
                if last_dump_error is not None:
                    hint = f"Last UI dump error: {last_dump_error}"
                if bool(params.get("optional", False)):
                    return {
                        "message": f"Optional UI text was not found: {target}",
                        "attempts": attempts,
                        "found": False,
                    }
                raise StepFailure(
                    f"UI text was not found within {float(params.get('timeout', 10)):g}s: {target}",
                    hint=hint,
                )
            time.sleep(min(interval, max(0.0, deadline - time.monotonic())))

    def _recover_anr_dialog(self, texts: list[str], xml_path: Path) -> bool:
        """Tap the Android "Wait" action when an ANR dialog is visible."""

        assert self.device is not None
        haystack = "\n".join(texts).casefold()
        markers = (
            "没有响应",
            "isn't responding",
            "is not responding",
            "keeps stopping",
        )
        if not any(marker in haystack for marker in markers):
            return False
        wait_labels = {"等待", "wait"}
        for node in self.device.ui_nodes(xml_path):
            for value in (node.get("text"), node.get("content_desc")):
                if str(value or "").strip().casefold() not in wait_labels:
                    continue
                x, y = node["center"]
                self.device.tap(int(x), int(y))
                return True
        return False

    def _dump_ui_for_result(self, step: FlowStep, result: StepResult) -> tuple[list[str], Path]:
        assert self.device is not None
        assert self.output_dir is not None
        path = self.output_dir / "ui" / f"{slugify(step.id, fallback='step')}.xml"
        self.device.dump_ui(path)
        relative = self._relative(path)
        if relative not in result.ui_files:
            result.ui_files.append(relative)
        return self.device.ui_text(path), path

    def _perform_ui_assertion(
        self, action: str, step: FlowStep, result: StepResult
    ) -> dict[str, Any]:
        params = step.params
        target = str(params["text"])
        ignore_case = bool(params.get("ignore_case", False))
        needle = target.casefold() if ignore_case else target

        if action not in {"wait_for_text", "wait_for_text_gone"}:
            texts, _ = self._dump_ui_for_result(step, result)
            haystack = "\n".join(texts)
            haystack = haystack.casefold() if ignore_case else haystack
            found = needle in haystack
            if action == "assert_ui_contains" and found:
                return {"message": f"Found UI text: {target}", "attempts": 1}
            if action == "assert_ui_not_contains" and not found:
                return {"message": f"UI text absent: {target}", "attempts": 1}
            detail = ", ".join(repr(value) for value in texts[:20])
            if action == "assert_ui_not_contains":
                raise StepFailure(
                    f"Unexpected UI text was found: {target}",
                    hint=f"Visible text: {detail or '<none>'}",
                )
            raise StepFailure(
                f"UI text was not found: {target}",
                hint=f"Visible text: {detail or '<none>'}",
            )

        deadline = time.monotonic() + float(params.get("timeout", 10))
        interval = float(params.get("interval", 0.5))
        attempts = 0
        anr_recoveries = 0
        texts: list[str] = []
        last_dump_error: str | None = None
        while True:
            attempts += 1
            try:
                texts, xml_path = self._dump_ui_for_result(step, result)
            except RunnerError as exc:
                last_dump_error = str(exc)
                texts = []
            else:
                last_dump_error = None
                if bool(params.get("recover_anr", False)) and self._recover_anr_dialog(
                    texts, xml_path
                ):
                    anr_recoveries += 1
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise StepFailure(
                            f"UI text was not found within "
                            f"{float(params.get('timeout', 10)):g}s: {target}",
                            hint=(
                                f"ANR recovery was attempted {anr_recoveries} time(s), "
                                "but the dialog remained visible."
                            ),
                        )
                    time.sleep(min(1.0, remaining))
                    continue
            haystack = "\n".join(texts)
            haystack = haystack.casefold() if ignore_case else haystack
            if action == "wait_for_text_gone" and needle not in haystack:
                return {
                    "message": f"UI text disappeared: {target}",
                    "attempts": attempts,
                    "anr_recoveries": anr_recoveries,
                    "found": False,
                }
            if action == "wait_for_text" and needle in haystack:
                return {
                    "message": f"Found UI text: {target}",
                    "attempts": attempts,
                    "anr_recoveries": anr_recoveries,
                }
            if time.monotonic() >= deadline:
                detail = ", ".join(repr(value) for value in texts[:20])
                hint = f"Visible text: {detail or '<none>'}"
                if last_dump_error is not None:
                    hint = f"Last UI dump error: {last_dump_error}"
                message = (
                    f"UI text did not disappear within "
                    f"{float(params.get('timeout', 10)):g}s: {target}"
                    if action == "wait_for_text_gone"
                    else f"UI text was not found within "
                    f"{float(params.get('timeout', 10)):g}s: {target}"
                )
                raise StepFailure(message, hint=hint)
            time.sleep(min(interval, max(0.0, deadline - time.monotonic())))
