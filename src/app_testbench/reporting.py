"""Self-contained HTML report generation."""

from __future__ import annotations

import base64
import html
import json
import mimetypes
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from app_testbench import SCHEMA_VERSION
from app_testbench.errors import ConfigError
from app_testbench.models import RunResult, StepResult
from app_testbench.utils import (
    atomic_write_text,
    now_iso,
    sha256_file,
    slugify,
    truncate_text,
    unique_path,
    write_json,
)

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
  --bg: #f2f1eb;
  --grid: rgba(23, 62, 54, .035);
  --panel: #fffdf8;
  --panel-strong: #ffffff;
  --text: #1c2927;
  --muted: #65716e;
  --quiet: #87918d;
  --line: #dfe3db;
  --line-strong: #cbd3c9;
  --accent: #0f6a5e;
  --accent-strong: #084c44;
  --accent-wash: #e4f1ec;
  --passed: #13784b;
  --passed-wash: #e9f6ee;
  --failed: #b33c33;
  --failed-wash: #fcebea;
  --skipped: #6b7673;
  --warning: #98621b;
  --warning-wash: #fff3dd;
  --code: #15221f;
  --code-text: #e0eee9;
  --shadow: 0 18px 44px rgba(26, 38, 34, .07);
  --radius: 16px;
}
:root[data-theme="light"] { color-scheme: light; }
:root[data-theme="dark"] {
  color-scheme: dark;
    --bg: #101715;
    --grid: rgba(213, 242, 232, .025);
    --panel: #17201e;
    --panel-strong: #1b2623;
    --text: #e7f0ec;
    --muted: #a4b0ac;
    --quiet: #7e8c87;
    --line: #2d3a36;
    --line-strong: #40504a;
    --accent: #76d8c9;
    --accent-strong: #9ce9de;
    --accent-wash: #1b3a34;
    --passed: #75daa1;
    --passed-wash: #193229;
    --failed: #ff9187;
    --failed-wash: #3a211f;
    --skipped: #a9b4b0;
    --warning: #f2c16e;
    --warning-wash: #352b1c;
    --code: #0b1210;
    --code-text: #d7e8e1;
    --shadow: 0 18px 50px rgba(0, 0, 0, .22);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    --bg: #101715;
    --grid: rgba(213, 242, 232, .025);
    --panel: #17201e;
    --panel-strong: #1b2623;
    --text: #e7f0ec;
    --muted: #a4b0ac;
    --quiet: #7e8c87;
    --line: #2d3a36;
    --line-strong: #40504a;
    --accent: #76d8c9;
    --accent-strong: #9ce9de;
    --accent-wash: #1b3a34;
    --passed: #75daa1;
    --passed-wash: #193229;
    --failed: #ff9187;
    --failed-wash: #3a211f;
    --skipped: #a9b4b0;
    --warning: #f2c16e;
    --warning-wash: #352b1c;
    --code: #0b1210;
    --code-text: #d7e8e1;
    --shadow: 0 18px 50px rgba(0, 0, 0, .22);
  }
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background-color: var(--bg);
  background-image:
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 32px 32px;
  color: var(--text);
  font: 15px/1.55 "Segoe UI Variable", "Segoe UI", "Microsoft YaHei", sans-serif;
}
::selection { background: var(--accent-wash); color: var(--accent-strong); }
main { width: min(1240px, calc(100% - 40px)); margin: 0 auto; padding: 32px 0 60px; }
h1, h2, h3, p { margin-top: 0; }
h1 { max-width: 18ch; margin-bottom: 12px; font-size: clamp(2rem, 4.5vw, 3.7rem); line-height: 1.4; letter-spacing: -.045em; }
h2 { margin-bottom: 0; font-size: 1.12rem; line-height: 1.25; letter-spacing: -.015em; }
h3 { margin-bottom: .2rem; font-size: 1rem; line-height: 1.3; }
a { color: var(--accent); text-underline-offset: 3px; }
a:hover { color: var(--accent-strong); }
code, pre { font-family: "Cascadia Code", "Cascadia Mono", Consolas, monospace; }
button, summary, a { -webkit-tap-highlight-color: transparent; }
button:focus-visible, summary:focus-visible, a:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.hero-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 10px 16px; }
.theme-toggle { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 36px; padding: 6px 10px; white-space: nowrap; }
.theme-toggle svg { width: 15px; height: 15px; flex: none; }
.theme-icon-sun { display: none; }
.theme-label-light { display: none; }
html[data-theme="dark"] .theme-icon-sun { display: block; }
html[data-theme="dark"] .theme-icon-moon { display: none; }
html[data-theme="dark"] .theme-label-dark { display: none; }
html[data-theme="dark"] .theme-label-light { display: inline; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) .theme-icon-sun { display: block; }
  :root:not([data-theme]) .theme-icon-moon { display: none; }
  :root:not([data-theme]) .theme-label-dark { display: none; }
  :root:not([data-theme]) .theme-label-light { display: inline; }
}

.hero {
  position: relative;
  overflow: hidden;
  padding: clamp(22px, 4vw, 42px);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--shadow);
}
.hero::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 4px;
  background: linear-gradient(90deg, var(--accent), var(--accent-strong));
}
.hero-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px 24px;
  padding-bottom: 14px;
  margin-bottom: 22px;
  border-bottom: 1px solid var(--line);
}
.eyebrow, .report-type, .section-kicker, .status-caption {
  font-size: .7rem;
  font-weight: 750;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.eyebrow { color: var(--accent); }
.report-type, .section-kicker, .status-caption { color: var(--quiet); }
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 32px;
}
.hero-copy { min-width: 0; }
.lede { max-width: 72ch; margin-bottom: 0; color: var(--muted); font-size: 1rem; }
.hero-status {
  display: grid;
  align-content: end;
  gap: 8px;
  min-width: 142px;
  padding-left: 22px;
  border-left: 1px solid var(--line);
}
.hero-status > strong { font-size: 1.05rem; line-height: 1.2; letter-spacing: -.015em; }
.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 24px;
  margin-top: 24px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: .82rem;
}
.hero-meta b { margin-right: 4px; color: var(--text); font-weight: 650; }

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin: 16px 0 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel);
}
.metric { min-width: 0; padding: 16px 18px; border-left: 1px solid var(--line); }
.metric:first-child { border-left: 0; background: var(--accent-wash); }
.metric strong { display: block; margin-bottom: 3px; font-size: 1.55rem; font-weight: 750; line-height: 1; letter-spacing: -.04em; }
.metric span { color: var(--muted); font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }

.report-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  grid-template-areas: "main rail";
  gap: 18px;
  align-items: start;
  margin-top: 18px;
}
.report-main { grid-area: main; min-width: 0; }
.report-rail {
  grid-area: rail;
  display: grid;
  gap: 18px;
  position: sticky;
  top: 18px;
  max-height: calc(100vh - 36px);
  max-height: calc(100dvh - 36px);
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: var(--line-strong) transparent;
  scroll-padding-block: 18px;
  padding-right: 4px;
}
.report-rail::-webkit-scrollbar { width: 8px; }
.report-rail::-webkit-scrollbar-track { background: transparent; }
.report-rail::-webkit-scrollbar-thumb { border: 2px solid var(--bg); border-radius: 999px; background: var(--line-strong); }
.report-rail::-webkit-scrollbar-thumb:hover { background: var(--muted); }
.report-rail:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.panel {
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel);
}
.report-main > .panel + .panel { margin-top: 18px; }
.rail-panel { margin: 0; }
.panel-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.section-kicker { display: block; margin-bottom: 4px; }
.section-note { color: var(--quiet); font-size: .74rem; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  width: fit-content;
  padding: 4px 10px;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-size: .74rem;
  font-weight: 750;
  line-height: 1.3;
}
.chip::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.chip-passed { color: var(--passed); background: var(--passed-wash); }
.chip-failed { color: var(--failed); background: var(--failed-wash); }
.chip-skipped { color: var(--skipped); }
.chip-warning { color: var(--warning); background: var(--warning-wash); }

.callout {
  margin: 0 0 16px;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-left: 4px solid var(--failed);
  border-radius: 0 10px 10px 0;
  background: var(--failed-wash);
}
.callout strong { display: block; margin-bottom: 6px; color: var(--failed); }
.callout p { margin: 0; color: var(--text); }
.callout.warning { border-left-color: var(--warning); background: var(--warning-wash); color: var(--text); }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: .9rem; }
th, td { padding: 9px 0; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { width: 36%; padding-right: 12px; color: var(--muted); font-size: .7rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; }
td { color: var(--text); }
tr:last-child th, tr:last-child td { border-bottom: 0; }

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0 0 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}
button {
  min-height: 36px;
  padding: 7px 11px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-strong);
  color: var(--text);
  font: inherit;
  font-size: .82rem;
  font-weight: 650;
  cursor: pointer;
  transition: background-color .16s ease, border-color .16s ease, color .16s ease;
}
button:hover { border-color: var(--line-strong); background: var(--bg); }
button.active { border-color: var(--accent); background: var(--accent-wash); color: var(--accent-strong); }

.step {
  margin-bottom: 10px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--panel-strong);
}
.step:last-child { margin-bottom: 0; }
.step[hidden] { display: none; }
.step-head { display: flex; justify-content: space-between; gap: 20px; padding: 14px 16px; border-left: 3px solid var(--skipped); }
.step-passed .step-head { border-left-color: var(--passed); }
.step-failed .step-head { border-left-color: var(--failed); }
.step-warning .step-head { border-left-color: var(--warning); }
.step-title { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
.step-title h3 { margin: 0; }
.step-index, .action-tag { font: 700 .71rem/1 "Cascadia Code", Consolas, monospace; }
.step-index { display: inline-flex; align-items: center; justify-content: center; min-width: 27px; height: 22px; padding: 0 6px; border: 1px solid var(--line); border-radius: 5px; background: var(--bg); color: var(--muted); font-variant-numeric: tabular-nums; }
.action-tag { padding: 5px 7px; border-radius: 5px; background: var(--accent-wash); color: var(--accent-strong); }
.step-time { color: var(--quiet); white-space: nowrap; font-size: .76rem; }
.step-body { padding: 12px 16px 16px; border-top: 1px solid var(--line); }
.meta-row { display: flex; gap: 12px 20px; flex-wrap: wrap; margin-bottom: 10px; color: var(--quiet); font-size: .73rem; }
.meta-row span { overflow-wrap: anywhere; }

details { margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--line); }
summary { color: var(--accent-strong); font-weight: 650; cursor: pointer; }
summary:hover { color: var(--accent); }
pre {
  max-height: 28rem;
  margin: 10px 0 0;
  padding: 13px 14px;
  overflow: auto;
  border: 1px solid #263a35;
  border-radius: 9px;
  background: var(--code);
  color: var(--code-text);
  font-size: .77rem;
  line-height: 1.55;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.shots { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 10px; margin-top: 12px; }
.shot { overflow: hidden; border: 1px solid var(--line); border-radius: 10px; background: var(--bg); }
.shot img { display: block; width: 100%; max-height: 420px; object-fit: contain; background: #000; }
.shot figcaption { padding: 8px 10px; color: var(--muted); font-size: .72rem; overflow-wrap: anywhere; }
.log { margin-top: 12px; padding-top: 12px; border-top: 1px dashed var(--line); }
.log:first-of-type { margin-top: 0; padding-top: 0; border-top: 0; }
.log h3 { margin-bottom: 0; color: var(--muted); font-size: .82rem; font-weight: 650; }
.muted { color: var(--muted); }
footer { margin-top: 28px; padding-top: 16px; border-top: 1px solid var(--line); color: var(--quiet); font-size: .76rem; }

@media (max-width: 980px) {
  main { width: min(100% - 24px, 1180px); padding-top: 18px; }
  .hero-grid { grid-template-columns: 1fr; gap: 18px; }
  .hero-status { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; padding: 14px 0 0; border-top: 1px solid var(--line); border-left: 0; }
  .hero-status > strong { margin-left: auto; }
  .report-layout { grid-template-columns: 1fr; grid-template-areas: "rail" "main"; }
  .report-rail { position: static; max-height: none; overflow: visible; scrollbar-gutter: auto; padding-right: 0; }
}
@media (max-width: 620px) {
  main { width: min(100% - 20px, 1180px); padding-bottom: 40px; }
  .hero { padding: 19px; border-radius: 13px; }
  .hero-topline { align-items: flex-start; flex-direction: column; gap: 8px; margin-bottom: 18px; }
  .hero-actions { width: 100%; justify-content: space-between; }
  .theme-toggle { min-height: 44px; }
  h1 { max-width: none; font-size: clamp(1.85rem, 9vw, 2.7rem); }
  .hero-meta { display: grid; gap: 8px; }
  .metrics { grid-template-columns: repeat(2, 1fr); }
  .metric { padding: 14px; }
  .metric:nth-child(odd) { border-left: 0; }
  .metric:nth-child(n + 3) { border-top: 1px solid var(--line); }
  .panel { padding: 15px; border-radius: 12px; }
  .panel-head { align-items: flex-start; }
  .toolbar { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  button { width: 100%; }
  .step-head { flex-direction: column; gap: 8px; padding: 13px; }
  .step-body { padding: 11px 13px 14px; }
  .step-time { white-space: normal; }
  .shots { grid-template-columns: 1fr; }
  .shot img { max-height: none; }
  footer { text-align: left; line-height: 1.6; }
}
@media print {
  @page { margin: 14mm; }
  :root, :root[data-theme="dark"] {
    color-scheme: light;
    --bg: #fff;
    --grid: transparent;
    --panel: #fff;
    --panel-strong: #fff;
    --text: #111;
    --muted: #444;
    --quiet: #666;
    --line: #ccc;
    --line-strong: #aaa;
    --accent: #0f6a5e;
    --accent-strong: #084c44;
    --accent-wash: #eef7f4;
    --passed: #13784b;
    --passed-wash: #eef8f2;
    --failed: #b33c33;
    --failed-wash: #fff0ef;
    --skipped: #555;
    --warning: #7a4b0f;
    --warning-wash: #fff8e8;
    --code: #f5f5f5;
    --code-text: #111;
    --shadow: none;
  }
  body { background: #fff; color: #111; }
  main { width: 100%; padding: 0; }
  .hero { box-shadow: none; }
  .report-layout { display: block; }
  .report-rail { position: static; max-height: none; overflow: visible; scrollbar-gutter: auto; margin-top: 18px; padding-right: 0; }
  .toolbar, button, .theme-toggle { display: none; }
  .step, .panel, .hero, .callout { break-inside: avoid; box-shadow: none; }
  details:not([open]) > :not(summary) { display: block !important; }
  a { color: #111; text-decoration: underline; }
  footer { break-before: avoid; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  button { transition: none; }
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
        f"<span>{_escape(step.started_at)}</span>"
        f"{f'<span>{_escape(step.finished_at)}</span>' if step.finished_at else ''}</div>"
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
            '<div class="callout" role="alert"><strong>Failed at '
            f"{_escape(first_failure.name)}</strong><p>{_escape(first_failure.error or '')}</p></div>"
        )
    warnings = "".join(
        f'<div class="callout warning" role="status">{_escape(warning)}</div>'
        for warning in result.warnings
    )
    environment_html = _render_table(result.environment)
    config_html = _render_table(result.config)
    logs_html = _render_logs(result, output_dir, max_log_chars)
    status = result.status if result.status in _STATUS_LABELS else "warning"
    total = len(result.steps)
    pass_rate = round((result.passed / total) * 100) if total else 0
    subtitle = result.config.get("description") or "MuMu Android automation execution report"
    artifact_links = []
    for label, path_value in (
        ("JSON result", result.result_path),
        ("Evidence manifest", result.manifest_path),
        ("JUnit XML", result.junit_path),
        ("Report", result.report_path),
    ):
        if path_value:
            artifact_links.append(
                f'<a href="{_escape(_relative(path_value, output_dir))}">{_escape(label)}</a>'
            )
    artifacts = " · ".join(artifact_links)
    artifacts_meta = f"<span><b>Artifacts</b> {artifacts}</span>" if artifacts else ""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <script>
  (() => {{
    try {{
      const requested = new URLSearchParams(window.location.search).get('theme');
      const saved = localStorage.getItem('app-testbench-report-theme');
      if (requested === 'light' || requested === 'dark') {{
        document.documentElement.dataset.theme = requested;
      }} else if (saved === 'light' || saved === 'dark') {{
        document.documentElement.dataset.theme = saved;
      }}
    }} catch (error) {{}}
  }})();
  </script>
  <title>{_escape(title)} · App TestBench</title>
  <style>{REPORT_CSS}</style>
</head>
<body>
<main>
  <header class="hero">
    <div class="hero-topline">
      <span class="eyebrow">App TestBench</span>
      <div class="hero-actions">
        <span class="report-type">Android app automation / execution report</span>
        <button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to dark mode" aria-pressed="false" title="Toggle light and dark mode">
          <span class="theme-icon" aria-hidden="true">
            <svg class="theme-icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z"/></svg>
            <svg class="theme-icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41"/></svg>
          </span>
          <span class="theme-label theme-label-dark">Dark</span>
          <span class="theme-label theme-label-light">Light</span>
        </button>
      </div>
    </div>
    <div class="hero-grid">
      <div class="hero-copy">
        <h1>{_escape(title)}</h1>
        <p class="lede">{_escape(subtitle)}</p>
      </div>
      <div class="hero-status">
        <span class="status-caption">Run status</span>
        {_status_chip(status)}
        <strong>{pass_rate}% pass rate</strong>
      </div>
    </div>
    <div class="hero-meta">
      <span><b>Started</b> {_escape(result.started_at)}</span>
      <span><b>Duration</b> {result.duration_ms:,} ms</span>
      {artifacts_meta}
    </div>
  </header>
  <section class="metrics" aria-label="Run summary">
    <div class="metric"><strong>{total}</strong><span>Total steps</span></div>
    <div class="metric"><strong>{result.passed}</strong><span>Passed</span></div>
    <div class="metric"><strong>{result.failed}</strong><span>Failed</span></div>
    <div class="metric"><strong>{result.skipped}</strong><span>Skipped</span></div>
  </section>
  <div class="report-layout">
    <div class="report-main">
      {failure_banner}{warnings}
      <section class="panel">
        <div class="panel-head">
          <div><span class="section-kicker">Timeline</span><h2>Execution</h2></div>
          <span class="section-note">Filter steps by status</span>
        </div>
        <div class="toolbar" role="group" aria-label="Filter steps">
          <button type="button" class="active" data-filter="all" aria-pressed="true">All ({total})</button>
          <button type="button" data-filter="passed" aria-pressed="false">Passed ({result.passed})</button>
          <button type="button" data-filter="failed" aria-pressed="false">Failed ({result.failed})</button>
          <button type="button" data-filter="skipped" aria-pressed="false">Skipped ({result.skipped})</button>
        </div>
        <div id="steps">{steps_html}</div>
      </section>
      <section class="panel log-panel">
        <div class="panel-head">
          <div><span class="section-kicker">Diagnostics</span><h2>Logcat</h2></div>
          <span class="section-note">Embedded for offline review</span>
        </div>
        {logs_html}
      </section>
    </div>
    <aside class="report-rail" aria-label="Run context; scroll for all details" tabindex="0">
      <section class="panel rail-panel">
        <div class="panel-head">
          <div><span class="section-kicker">Context</span><h2>Environment</h2></div>
          <span class="section-note">Resolved at run time</span>
        </div>
        {environment_html}
      </section>
      <details class="panel rail-panel" open>
        <summary>Run configuration</summary>
        {config_html}
      </details>
    </aside>
  </div>
  <footer>Generated by App TestBench · {_escape(result.finished_at)} · Reports may contain sensitive app data</footer>
</main>
<script>
(() => {{
  const root = document.documentElement;
  const buttons = Array.from(document.querySelectorAll('[data-filter]'));
  const steps = Array.from(document.querySelectorAll('#steps [data-status]'));
  const themeButton = document.querySelector('[data-theme-toggle]');
  const themeMedia = window.matchMedia('(prefers-color-scheme: dark)');
  const currentTheme = () => root.dataset.theme || (themeMedia.matches ? 'dark' : 'light');
  const syncThemeButton = () => {{
    const isDark = currentTheme() === 'dark';
    themeButton.setAttribute('aria-pressed', String(isDark));
    themeButton.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
  }};
  themeButton.addEventListener('click', () => {{
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try {{ localStorage.setItem('app-testbench-report-theme', next); }} catch (error) {{}}
    syncThemeButton();
  }});
  if (themeMedia.addEventListener) {{
    themeMedia.addEventListener('change', syncThemeButton);
  }}
  syncThemeButton();
  const applyFilter = (activeButton) => {{
    buttons.forEach((button) => {{
      const active = button === activeButton;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    }});
    const filter = activeButton.dataset.filter;
    steps.forEach((step) => {{
      step.hidden = filter !== 'all' && step.dataset.status !== filter;
    }});
  }};
  buttons.forEach((button) => button.addEventListener('click', () => applyFilter(button)));
  window.addEventListener('beforeprint', () => {{
    document.querySelectorAll('details').forEach((item) => {{ item.open = true; }});
  }});
}})();
</script>
</body>
</html>
"""


def _media_type(path: Path) -> str:
    if path.suffix.lower() == ".json":
        return "application/json"
    if path.suffix.lower() == ".xml":
        return "application/xml"
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def write_evidence_manifest(result: RunResult, output_dir: Path) -> Path:
    """Write a hash inventory for every evidence file except the manifest itself."""

    manifest_path = output_dir / "manifest.json"
    files: list[dict[str, Any]] = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.resolve() == manifest_path.resolve():
            continue
        relative = path.resolve().relative_to(output_dir.resolve()).as_posix()
        files.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "media_type": _media_type(path),
            }
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "kind": "app-testbench-evidence-manifest",
        "generated_at": now_iso(),
        "run": {
            "name": result.name,
            "status": result.status,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "duration_ms": result.duration_ms,
        },
        "file_count": len(files),
        "total_bytes": sum(item["size_bytes"] for item in files),
        "files": files,
    }
    write_json(manifest_path, payload)
    return manifest_path


def prune_old_runs(
    output_base: Path,
    keep: int,
    *,
    protected: Path | None = None,
) -> list[Path]:
    """Remove old manifest-bearing run directories, newest first.

    Only direct child directories with a manifest are eligible. This makes the
    opt-in retention command conservative and leaves unrelated folders alone.
    """

    if keep < 1:
        raise ConfigError("--keep-runs must be at least 1")
    base = output_base.resolve()
    if not base.is_dir():
        return []
    candidates: list[Path] = []
    for child in base.iterdir():
        if child.is_symlink() or not child.is_dir():
            continue
        try:
            if child.resolve().parent != base:
                continue
        except OSError:
            continue
        if not (child / "manifest.json").is_file():
            continue
        candidates.append(child)
    candidates.sort(key=lambda path: path.stat().st_mtime_ns, reverse=True)
    protected_resolved = protected.resolve() if protected is not None else None
    removed: list[Path] = []
    for path in candidates[keep:]:
        if protected_resolved is not None and path.resolve() == protected_resolved:
            continue
        if path.resolve().parent != base:
            continue
        shutil.rmtree(path)
        removed.append(path)
    return removed


def write_run_artifacts(result: RunResult, output_dir: Path) -> tuple[Path, Path]:
    report_path = output_dir / "report.html"
    result_path = output_dir / "result.json"
    result.output_dir = str(output_dir.resolve())
    result.report_path = str(report_path.resolve())
    result.result_path = str(result_path.resolve())
    result.manifest_path = str((output_dir / "manifest.json").resolve())
    if result.junit_path:
        write_junit_xml(result, Path(result.junit_path))
    write_json(result_path, result.to_dict())
    atomic_write_text(report_path, render_html(result, output_dir))
    write_evidence_manifest(result, output_dir)
    return report_path, result_path
