"""Self-contained HTML report generation."""

from __future__ import annotations

import base64
import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from app_testbench.models import RunResult, StepResult
from app_testbench.utils import atomic_write_text, slugify, truncate_text, unique_path, write_json

_STATUS_LABELS = {
    "passed": "Passed",
    "failed": "Failed",
    "skipped": "Skipped",
    "warning": "Warning",
}


def create_run_directory(base: Path, name: str) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    candidate = base / f"{stamp}-{slugify(name, fallback='run')}"
    output = unique_path(candidate)
    (output / "screenshots").mkdir(parents=True, exist_ok=False)
    (output / "ui").mkdir(parents=True, exist_ok=False)
    (output / "logs").mkdir(parents=True, exist_ok=False)
    return output


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _json_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    except (TypeError, ValueError):
        return str(value)


def _relative(path_value: str, output_dir: Path) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    try:
        return path.resolve().relative_to(output_dir.resolve()).as_posix()
    except (ValueError, OSError):
        return path.name


def _read_text(path_value: str, *, limit: int) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    try:
        return truncate_text(path.read_text(encoding="utf-8", errors="replace"), limit)
    except OSError:
        return f"Artifact could not be read: {path}"


def _embed_image(path_value: str) -> str:
    path = Path(path_value)
    try:
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        return ""
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64,{payload}"


def _status_chip(status: str) -> str:
    normalized = status if status in _STATUS_LABELS else "warning"
    return f'<span class="chip chip-{_escape(normalized)}">{_escape(_STATUS_LABELS[normalized])}</span>'


REPORT_CSS = r"""
:root {
  color-scheme: light dark;
  --bg: #f4f6f8;
  --panel: #ffffff;
  --text: #16202a;
  --muted: #637080;
  --line: #dce3ea;
  --accent: #0b7a75;
  --accent-2: #075e5a;
  --passed: #137a45;
  --failed: #b42318;
  --skipped: #6b7280;
  --warning: #a15c00;
  --code: #0f1720;
  --code-text: #dce8f2;
  --shadow: 0 18px 50px rgba(20, 35, 50, .08);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #10161c;
    --panel: #17212a;
    --text: #e9f0f6;
    --muted: #9aa9b7;
    --line: #2a3947;
    --accent: #5dd6cc;
    --accent-2: #8ce7df;
    --passed: #64d99b;
    --failed: #ff8278;
    --skipped: #a9b4bf;
    --warning: #f4bd6a;
    --code: #0b1015;
    --code-text: #d8e6f2;
    --shadow: 0 18px 60px rgba(0, 0, 0, .25);
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--accent) 10%, transparent), transparent 34rem),
    var(--bg);
  color: var(--text);
  font: 15px/1.55 ui-sans-serif, "Segoe UI", "Microsoft YaHei", sans-serif;
}
main { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 40px 0 60px; }
h1, h2, h3, p { margin-top: 0; }
h1 { font-size: clamp(2rem, 5vw, 4.2rem); line-height: .98; letter-spacing: -.055em; }
h2 { font-size: 1.3rem; letter-spacing: -.02em; }
h3 { font-size: 1.05rem; margin-bottom: .2rem; }
a { color: var(--accent); }
code, pre { font-family: ui-monospace, "Cascadia Code", Consolas, monospace; }
.hero {
  position: relative;
  overflow: hidden;
  padding: clamp(24px, 5vw, 56px);
  border: 1px solid var(--line);
  border-radius: 28px;
  background: var(--panel);
  box-shadow: var(--shadow);
}
.hero::after {
  content: "";
  position: absolute;
  width: 280px; height: 280px; right: -90px; top: -110px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 13%, transparent);
}
.eyebrow { color: var(--accent); font-weight: 800; letter-spacing: .14em; font-size: .74rem; text-transform: uppercase; }
.lede { color: var(--muted); max-width: 760px; }
.hero-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; color: var(--muted); }
.metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 18px 0 30px; }
.metric { background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 18px; }
.metric strong { display: block; font-size: 1.8rem; letter-spacing: -.04em; }
.metric span { color: var(--muted); font-size: .82rem; text-transform: uppercase; letter-spacing: .08em; }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 22px; padding: 22px; margin-top: 18px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.chip { display: inline-flex; align-items: center; gap: 7px; border-radius: 999px; padding: 4px 10px; font-size: .75rem; font-weight: 750; border: 1px solid currentColor; }
.chip::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.chip-passed { color: var(--passed); }
.chip-failed { color: var(--failed); }
.chip-skipped { color: var(--skipped); }
.chip-warning { color: var(--warning); }
.callout { border-left: 4px solid var(--failed); background: color-mix(in srgb, var(--failed) 8%, transparent); padding: 14px 16px; border-radius: 8px; margin: 12px 0; }
.callout.warning { border-color: var(--warning); background: color-mix(in srgb, var(--warning) 9%, transparent); }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { color: var(--muted); font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; }
.toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0 18px; }
button { border: 1px solid var(--line); color: var(--text); background: var(--panel); border-radius: 10px; padding: 8px 12px; cursor: pointer; }
button.active { border-color: var(--accent); color: var(--accent); }
.step { background: var(--panel); border: 1px solid var(--line); border-radius: 18px; margin-bottom: 12px; overflow: hidden; }
.step[hidden] { display: none; }
.step-head { display: flex; justify-content: space-between; gap: 20px; padding: 17px 18px; border-left: 4px solid var(--skipped); }
.step-passed .step-head { border-left-color: var(--passed); }
.step-failed .step-head { border-left-color: var(--failed); }
.step-warning .step-head { border-left-color: var(--warning); }
.step-title { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.step-index, .action-tag { font: 700 .72rem/1 ui-monospace, Consolas, monospace; color: var(--muted); }
.action-tag { background: color-mix(in srgb, var(--accent) 10%, transparent); color: var(--accent); padding: 5px 8px; border-radius: 6px; }
.step-time { color: var(--muted); white-space: nowrap; font-size: .82rem; }
.step-body { padding: 0 18px 18px; }
.meta-row { display: flex; gap: 12px; flex-wrap: wrap; color: var(--muted); font-size: .82rem; margin-bottom: 12px; }
details { margin-top: 10px; border-top: 1px dashed var(--line); padding-top: 10px; }
summary { cursor: pointer; color: var(--accent); font-weight: 650; }
pre { margin: 10px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; background: var(--code); color: var(--code-text); padding: 14px; border-radius: 10px; font-size: .78rem; max-height: 36rem; overflow: auto; }
.shots { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-top: 12px; }
.shot { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; background: var(--bg); }
.shot img { display: block; width: 100%; max-height: 560px; object-fit: contain; background: #000; }
.shot figcaption { color: var(--muted); font-size: .75rem; padding: 8px 10px; overflow-wrap: anywhere; }
.log { border-top: 1px dashed var(--line); padding-top: 12px; margin-top: 12px; }
.log h3 { font-size: .9rem; }
.muted { color: var(--muted); }
footer { text-align: center; color: var(--muted); font-size: .78rem; margin-top: 30px; }
@media (max-width: 760px) {
  main { width: min(100% - 20px, 1180px); padding-top: 20px; }
  .metrics { grid-template-columns: repeat(2, 1fr); }
  .hero { border-radius: 18px; }
  .step-head { flex-direction: column; gap: 8px; }
}
@media print {
  body { background: #fff; }
  main { width: 100%; padding: 0; }
  .toolbar, button { display: none; }
  .step, .panel, .hero { box-shadow: none; break-inside: avoid; }
  details { display: block; }
  details > summary { display: none; }
}
"""


def _artifact_path(path_value: str, output_dir: Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else output_dir / path


def _render_step(
    step: StepResult,
    index: int,
    *,
    output_dir: Path,
    include_ui_xml: bool,
) -> str:
    status = step.status if step.status in _STATUS_LABELS else "warning"
    error_block = ""
    if step.error:
        hint = f'<p class="muted">{_escape(step.hint)}</p>' if step.hint else ""
        error_block = (
            '<div class="callout"><strong>Failure</strong>'
            f"<pre>{_escape(step.error)}</pre>{hint}</div>"
        )

    screenshots = []
    for screenshot in step.screenshots:
        absolute = _artifact_path(screenshot, output_dir)
        embedded = _embed_image(str(absolute))
        if not embedded:
            continue
        screenshots.append(
            '<figure class="shot">'
            f'<img src="{embedded}" alt="{_escape(step.name)} screenshot">'
            f"<figcaption>{_escape(_relative(str(absolute), output_dir))}</figcaption>"
            "</figure>"
        )
    screenshot_block = f'<div class="shots">{"".join(screenshots)}</div>' if screenshots else ""

    ui_blocks = []
    if include_ui_xml:
        for ui_value in step.ui_files:
            absolute = _artifact_path(ui_value, output_dir)
            xml = _read_text(str(absolute), limit=200_000)
            ui_blocks.append(
                "<details><summary>UI hierarchy</summary>"
                f'<p class="muted">{_escape(_relative(str(absolute), output_dir))}</p>'
                f"<pre>{_escape(xml)}</pre></details>"
            )

    output_block = ""
    if step.output:
        output_block = (
            "<details><summary>Output</summary>"
            f"<pre>{_escape(_json_text(step.output))}</pre></details>"
        )
    input_block = (
        f"<details><summary>Input</summary><pre>{_escape(_json_text(step.params))}</pre></details>"
    )
    description_block = (
        f'<p class="muted">{_escape(step.description)}</p>' if step.description else ""
    )

    section = step.section.capitalize()
    return (
        f'<article class="step step-{status}" data-status="{_escape(status)}">'
        '<div class="step-head"><div>'
        f'<div class="step-title"><span class="step-index">{index:02d}</span>'
        f"<h3>{_escape(step.name)}</h3>{_status_chip(status)}</div>"
        f'<span class="action-tag">{_escape(step.action)}</span>'
        "</div>"
        f'<div class="step-time">{_escape(section)} · {step.duration_ms:,} ms</div>'
        "</div>"
        f'<div class="step-body"><div class="meta-row"><span>ID: {_escape(step.id)}</span>'
        f"<span>{_escape(step.started_at)}</span></div>"
        f"{description_block}{error_block}{input_block}{output_block}"
        f"{screenshot_block}{''.join(ui_blocks)}"
        "</div></article>"
    )


def _render_table(mapping: dict[str, Any]) -> str:
    rows = []
    for key, value in mapping.items():
        rendered = _json_text(value) if isinstance(value, (dict, list)) else str(value)
        rows.append(f"<tr><th>{_escape(key)}</th><td>{_escape(rendered)}</td></tr>")
    return '<div class="table-wrap"><table><tbody>' + "".join(rows) + "</tbody></table></div>"


def _render_logs(result: RunResult, output_dir: Path, limit: int) -> str:
    blocks = []
    for path_value in result.logcat_paths:
        path = _artifact_path(path_value, output_dir)
        content = _read_text(str(path), limit=limit)
        blocks.append(
            '<div class="log">'
            f"<h3>{_escape(_relative(str(path), output_dir))}</h3>"
            f"<pre>{_escape(content or '<empty logcat>')}</pre></div>"
        )
    if not blocks:
        return '<p class="muted">No logcat artifact was captured.</p>'
    return "".join(blocks)


def _junit_time(duration_ms: int) -> str:
    return f"{max(0, duration_ms) / 1000:.3f}"


def write_junit_xml(result: RunResult, path: Path) -> Path:
    """Write a standard-library JUnit XML report for the run."""

    target = path.expanduser().resolve()
    root = ET.Element(
        "testsuites",
        {
            "name": result.name,
            "tests": str(len(result.steps)),
            "failures": str(result.failed),
            "errors": "0",
            "skipped": str(result.skipped),
            "time": _junit_time(result.duration_ms),
        },
    )
    suite = ET.SubElement(
        root,
        "testsuite",
        {
            "name": result.name,
            "tests": str(len(result.steps)),
            "failures": str(result.failed),
            "errors": "0",
            "skipped": str(result.skipped),
            "time": _junit_time(result.duration_ms),
            "timestamp": result.started_at,
        },
    )
    for step in result.steps:
        case = ET.SubElement(
            suite,
            "testcase",
            {
                "classname": step.section,
                "name": step.name,
                "time": _junit_time(step.duration_ms),
            },
        )
        if step.status == "failed":
            failure = ET.SubElement(
                case,
                "failure",
                {"message": step.error or "Step failed"},
            )
            details = [step.error or "Step failed"]
            if step.hint:
                details.append(f"Hint: {step.hint}")
            failure.text = "\n".join(details)
        elif step.status == "skipped":
            reason = str(step.output.get("reason", "Step was skipped"))
            ET.SubElement(case, "skipped", {"message": reason})
        if step.output:
            system_out = ET.SubElement(case, "system-out")
            system_out.text = json.dumps(step.output, ensure_ascii=False, indent=2, default=str)

    ET.indent(root, space="  ")
    body = ET.tostring(root, encoding="unicode")
    atomic_write_text(target, '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n")
    return target


def render_html(result: RunResult, output_dir: Path) -> str:
    report_config = result.config.get("report", {})
    include_ui_xml = bool(report_config.get("include_ui_xml", True))
    max_log_chars = int(report_config.get("max_log_chars", 200_000))
    title = str(report_config.get("title") or result.name)
    steps_html = "".join(
        _render_step(
            step,
            index,
            output_dir=output_dir,
            include_ui_xml=include_ui_xml,
        )
        for index, step in enumerate(result.steps, start=1)
    )
    if not steps_html:
        steps_html = '<p class="muted">No steps were executed.</p>'

    failed_steps = [step for step in result.steps if step.status == "failed"]
    first_failure = failed_steps[0] if failed_steps else None
    failure_banner = ""
    if first_failure:
        failure_banner = (
            '<div class="callout"><strong>Failed at '
            f"{_escape(first_failure.name)}</strong><p>{_escape(first_failure.error or '')}</p></div>"
        )
    warnings = "".join(
        f'<div class="callout warning">{_escape(warning)}</div>' for warning in result.warnings
    )
    environment_html = _render_table(result.environment)
    config_html = _render_table(result.config)
    logs_html = _render_logs(result, output_dir, max_log_chars)
    status = result.status if result.status in _STATUS_LABELS else "warning"
    total = len(result.steps)
    subtitle = result.config.get("description") or "MuMu Android automation execution report"
    artifact_links = []
    for label, path_value in (
        ("JSON result", result.result_path),
        ("JUnit XML", result.junit_path),
        ("Report", result.report_path),
    ):
        if path_value:
            artifact_links.append(
                f'<a href="{_escape(_relative(path_value, output_dir))}">{_escape(label)}</a>'
            )
    artifacts = " · ".join(artifact_links)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)} · App TestBench</title>
  <style>{REPORT_CSS}</style>
</head>
<body>
<main>
  <header class="hero">
    <div class="eyebrow">App TestBench / Android app automation report</div>
    <h1>{_escape(title)}</h1>
    <p class="lede">{_escape(subtitle)}</p>
    <div class="hero-meta">{_status_chip(status)}<span>{_escape(result.started_at)}</span><span>·</span><span>{result.duration_ms:,} ms</span><span>·</span>{artifacts}</div>
  </header>
  <section class="metrics" aria-label="Run summary">
    <div class="metric"><strong>{total}</strong><span>Total steps</span></div>
    <div class="metric"><strong>{result.passed}</strong><span>Passed</span></div>
    <div class="metric"><strong>{result.failed}</strong><span>Failed</span></div>
    <div class="metric"><strong>{result.skipped}</strong><span>Skipped</span></div>
  </section>
  {failure_banner}{warnings}
  <section class="panel">
    <div class="panel-head"><h2>Execution</h2><span class="muted">Filter steps by status</span></div>
    <div class="toolbar" role="group" aria-label="Filter steps">
      <button type="button" class="active" data-filter="all">All ({total})</button>
      <button type="button" data-filter="passed">Passed ({result.passed})</button>
      <button type="button" data-filter="failed">Failed ({result.failed})</button>
      <button type="button" data-filter="skipped">Skipped ({result.skipped})</button>
    </div>
    <div id="steps">{steps_html}</div>
  </section>
  <section class="panel">
    <div class="panel-head"><h2>Environment</h2><span class="muted">Resolved at run time</span></div>
    {environment_html}
  </section>
  <section class="panel">
    <div class="panel-head"><h2>Logcat</h2><span class="muted">Embedded for offline review</span></div>
    {logs_html}
  </section>
  <details class="panel">
    <summary>Run configuration</summary>
    {config_html}
  </details>
  <footer>Generated by App TestBench · {_escape(result.finished_at)} · Reports may contain sensitive app data</footer>
</main>
<script>
(() => {{
  const buttons = document.querySelectorAll('[data-filter]');
  const steps = document.querySelectorAll('#steps [data-status]');
  buttons.forEach((button) => {{
    button.addEventListener('click', () => {{
      buttons.forEach((item) => item.classList.remove('active'));
      button.classList.add('active');
      const filter = button.dataset.filter;
      steps.forEach((step) => {{
        step.hidden = filter !== 'all' && step.dataset.status !== filter;
      }});
    }});
  }});
}})();
</script>
</body>
</html>
"""


def write_run_artifacts(result: RunResult, output_dir: Path) -> tuple[Path, Path]:
    report_path = output_dir / "report.html"
    result_path = output_dir / "result.json"
    result.output_dir = str(output_dir.resolve())
    result.report_path = str(report_path.resolve())
    result.result_path = str(result_path.resolve())
    if result.junit_path:
        write_junit_xml(result, Path(result.junit_path))
    write_json(result_path, result.to_dict())
    atomic_write_text(report_path, render_html(result, output_dir))
    return report_path, result_path
