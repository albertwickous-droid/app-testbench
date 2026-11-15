from __future__ import annotations

import base64
import xml.etree.ElementTree as ET
from pathlib import Path

from app_testbench.models import RunResult, StepResult
from app_testbench.reporting import create_run_directory, write_run_artifacts
from app_testbench.utils import now_iso

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def test_report_embeds_images_logs_and_escapes_user_content(tmp_path: Path) -> None:
    output = create_run_directory(tmp_path / "runs", "Smoke <unsafe>")
    shot = output / "screenshots" / "login.png"
    shot.write_bytes(PNG)
    log = output / "logs" / "logcat.txt"
    log.write_text("01-01 I/App: <unsafe> & log", encoding="utf-8")
    result = RunResult(
        name="Smoke <unsafe>",
        status="failed",
        started_at=now_iso(),
        finished_at=now_iso(),
        duration_ms=1234,
        environment={"serial": "127.0.0.1:16384"},
        config={
            "description": "Report <test>",
            "report": {"title": "<script>alert(1)</script>", "include_ui_xml": True},
        },
        steps=[
            StepResult(
                id="login",
                name="Login",
                action="tap",
                section="steps",
                status="failed",
                started_at=now_iso(),
                duration_ms=12,
                params={"x": 1, "y": 2},
                error="bad <state>",
                screenshots=["screenshots/login.png"],
            )
        ],
        logcat_paths=["logs/logcat.txt"],
    )
    report_path, result_path = write_run_artifacts(result, output)
    report = report_path.read_text(encoding="utf-8")
    assert "data:image/png;base64," in report
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report
    assert "bad &lt;state&gt;" in report
    assert "&lt;unsafe&gt; &amp; log" in report
    assert "Failed" in report
    assert '<meta name="viewport"' in report
    assert 'class="report-layout"' in report
    assert 'aria-pressed="true"' in report
    assert "data-theme-toggle" in report
    assert 'data-theme="dark"' in report
    assert "new URLSearchParams(window.location.search)" in report
    assert "localStorage.getItem('app-testbench-report-theme')" in report
    assert "max-height: calc(100dvh - 36px)" in report
    assert "scrollbar-width: thin" in report
    assert "min-height: 44px" in report
    assert ':root, :root[data-theme="dark"]' in report
    assert ".toolbar, button, .theme-toggle { display: none; }" in report
    assert "@media (max-width: 620px)" in report
    assert "prefers-reduced-motion" in report
    assert "<script src=" not in report
    assert "<link" not in report
    assert result_path.is_file()
    assert '"schema_version": "1.0"' in result_path.read_text(encoding="utf-8")


def test_junit_xml_export_contains_statuses_and_escaped_text(tmp_path: Path) -> None:
    output = create_run_directory(tmp_path / "runs", "junit")
    junit_path = output / "junit.xml"
    result = RunResult(
        name="junit & smoke",
        status="failed",
        started_at=now_iso(),
        finished_at=now_iso(),
        duration_ms=1500,
        environment={},
        config={},
        steps=[
            StepResult(
                id="pass",
                name="通过",
                action="back",
                section="steps",
                status="passed",
                started_at=now_iso(),
                duration_ms=100,
            ),
            StepResult(
                id="fail",
                name="失败 <step>",
                action="tap",
                section="steps",
                status="failed",
                started_at=now_iso(),
                duration_ms=200,
                error="bad <state> & value",
                hint="check > hint",
            ),
            StepResult(
                id="skip",
                name="跳过",
                action="home",
                section="teardown",
                status="skipped",
                started_at=now_iso(),
                output={"reason": "aborted <after> failure"},
            ),
        ],
        junit_path=str(junit_path),
    )

    write_run_artifacts(result, output)

    assert junit_path.is_file()
    root = ET.parse(junit_path).getroot()
    assert root.tag == "testsuites"
    assert root.attrib["tests"] == "3"
    assert root.attrib["failures"] == "1"
    assert root.attrib["skipped"] == "1"
    cases = root.findall("./testsuite/testcase")
    assert [case.attrib["name"] for case in cases] == ["通过", "失败 <step>", "跳过"]
    assert cases[1].find("failure").text == "bad <state> & value\nHint: check > hint"
    assert cases[2].find("skipped").attrib["message"] == "aborted <after> failure"
    assert '"junit_path"' in Path(result.result_path).read_text(encoding="utf-8")
    assert "JUnit XML" in Path(result.report_path).read_text(encoding="utf-8")
