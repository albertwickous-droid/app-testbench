"""Sequential flow suites and data-driven collection runs."""

from __future__ import annotations

import csv
import html
import json
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app_testbench import SCHEMA_VERSION
from app_testbench.config import Settings
from app_testbench.errors import ConfigError, FlowError
from app_testbench.flow import (
    Flow,
    _mapping,
    _read_document,
    _sequence,
    _string,
    _validate_variable_name,
    _validate_variable_value,
    flow_matches_tags,
    load_flow,
    parse_cli_variables,
)
from app_testbench.reporting import create_run_directory
from app_testbench.runner import FlowRunner
from app_testbench.utils import atomic_write_text, elapsed_ms, now_iso, sha256_file, write_json


@dataclass(slots=True)
class CaseSpec:
    flow: Flow
    label: str
    data_index: int | None = None


@dataclass(slots=True)
class SuiteDefinition:
    path: Path
    name: str
    description: str
    cases: list[CaseSpec]


@dataclass(slots=True)
class CollectionRun:
    root: Path
    status: str
    payload: dict[str, Any]
    result_path: Path
    report_path: Path
    junit_path: Path
    manifest_path: Path


def _relative(root: Path, path: Path | str) -> str:
    target = Path(path).expanduser().resolve()
    try:
        return target.relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return str(target)


def _case_variables(
    base: dict[str, Any],
    entry: dict[str, Any],
    cli_values: dict[str, str],
) -> dict[str, Any]:
    merged = dict(base)
    merged.update(entry)
    merged.update(cli_values)
    return merged


def _validate_inline_variables(value: Any, *, location: str) -> dict[str, Any]:
    raw = _mapping(value, field_name=location)
    result: dict[str, Any] = {}
    for name, item in raw.items():
        try:
            validated_name = _validate_variable_name(name, location=f"{location}.{name}")
            result[validated_name] = _validate_variable_value(
                item, location=f"{location}.{validated_name}"
            )
        except FlowError as exc:
            raise ConfigError(exc.message, hint=exc.hint) from exc
    return result


def load_suite_definition(
    path_value: str | Path,
    *,
    tags: list[str] | None = None,
    base_variables: dict[str, Any] | None = None,
    cli_vars: list[str] | None = None,
) -> SuiteDefinition:
    """Load a suite manifest and resolve its selected flows before device access."""

    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise ConfigError(f"Suite manifest does not exist: {path}")
    try:
        raw = _read_document(path)
        root = _mapping(raw, field_name="suite")
    except FlowError as exc:
        raise ConfigError(f"Could not load suite manifest: {path}", hint=exc.message) from exc
    allowed = {"version", "name", "description", "flows"}
    unknown = set(root) - allowed
    if unknown:
        raise ConfigError(f"Unknown suite field(s): {', '.join(sorted(unknown))}")
    version = root.get("version", 1)
    if str(version) != "1":
        raise ConfigError(f"Unsupported suite version: {version!r}", hint="Use version: 1")
    name = _string(root.get("name", path.stem), field_name="suite.name")
    description = _string(
        root.get("description", ""), field_name="suite.description", allow_empty=True
    )
    entries = _sequence(root.get("flows"), field_name="suite.flows")
    if not entries:
        raise ConfigError("Suite must contain at least one flow")

    cli_values = parse_cli_variables(cli_vars)
    base = dict(base_variables or {})
    cases: list[CaseSpec] = []
    for index, entry in enumerate(entries):
        location = f"suite.flows[{index}]"
        if isinstance(entry, str):
            flow_value = entry
            entry_variables: dict[str, Any] = {}
        else:
            mapping = _mapping(entry, field_name=location)
            unknown_entry = set(mapping) - {"path", "variables"}
            if unknown_entry:
                raise ConfigError(
                    f"Unknown field(s) at {location}: {', '.join(sorted(unknown_entry))}"
                )
            flow_value = _string(mapping.get("path"), field_name=f"{location}.path")
            entry_variables = _validate_inline_variables(
                mapping.get("variables", {}), location=f"{location}.variables"
            )
        flow_path = Path(flow_value).expanduser()
        if not flow_path.is_absolute():
            flow_path = path.parent / flow_path
        flow_path = flow_path.resolve()
        try:
            flow = load_flow(
                flow_path,
                variables=_case_variables(base, entry_variables, cli_values),
            )
        except FlowError as exc:
            raise FlowError(
                f"Could not load suite flow {flow_path}: {exc.message}",
                hint=exc.hint,
            ) from exc
        if flow_matches_tags(flow, tags):
            label = flow.name if len(entries) == 1 else f"{flow.name} [{index + 1}]"
            cases.append(CaseSpec(flow=flow, label=label))
    if not cases:
        requested = ", ".join(tag for tag in (tags or []) if tag.strip())
        raise ConfigError(
            f"No suite flows matched tag(s): {requested or '<empty>'}",
            hint="Add a matching tags entry to a flow or remove --tag.",
        )
    return SuiteDefinition(path=path, name=name, description=description, cases=cases)


def _load_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        stream = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise ConfigError(f"Could not read data file: {path}", hint=str(exc)) from exc
    with stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames
        if not headers:
            raise ConfigError("CSV data file must have a header row")
        if any(not header or not header.strip() for header in headers):
            raise ConfigError("CSV data headers cannot be empty")
        if len(headers) != len(set(headers)):
            raise ConfigError("CSV data headers must be unique")
        rows: list[dict[str, Any]] = []
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ConfigError(f"CSV row {line_number} has too many columns")
            if all(value is None or str(value).strip() == "" for value in row.values()):
                continue
            rows.append(
                {str(key): "" if value is None else str(value) for key, value in row.items()}
            )
    if not rows:
        raise ConfigError("Data file contains no rows")
    return rows


def _load_json_rows(path: Path) -> list[dict[str, Any]]:
    try:
        raw = _read_document(path)
    except FlowError as exc:
        raise ConfigError(f"Could not read data file: {path}", hint=exc.message) from exc
    if isinstance(raw, dict) and "cases" in raw:
        raw = raw["cases"]
    if not isinstance(raw, list):
        raise ConfigError(
            "JSON data must be a list of objects or an object with a cases list",
            hint="Use [{...}, {...}] or {cases: [{...}]}.",
        )
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        mapping = _mapping(item, field_name=f"data.cases[{index}]")
        row: dict[str, Any] = {}
        for name, value in mapping.items():
            try:
                validated_name = _validate_variable_name(name, location=f"data.cases[{index}]")
                row[validated_name] = _validate_variable_value(
                    value, location=f"data.cases[{index}].{validated_name}"
                )
            except FlowError as exc:
                raise ConfigError(exc.message, hint=exc.hint) from exc
        rows.append(row)
    if not rows:
        raise ConfigError("Data file contains no cases")
    return rows


def load_data_rows(path_value: str | Path) -> list[dict[str, Any]]:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise ConfigError(f"Data file does not exist: {path}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _load_csv_rows(path)
    if suffix in {".json", ".yaml", ".yml"}:
        return _load_json_rows(path)
    raise ConfigError(
        f"Unsupported data file extension: {suffix or '<none>'}",
        hint="Use .csv, .json, .yaml, or .yml.",
    )


def load_data_cases(
    flow_path: str | Path,
    data_path: str | Path,
    *,
    base_variables: dict[str, Any] | None = None,
    cli_vars: list[str] | None = None,
) -> list[CaseSpec]:
    rows = load_data_rows(data_path)
    base = dict(base_variables or {})
    cli_values = parse_cli_variables(cli_vars)
    cases: list[CaseSpec] = []
    for index, row in enumerate(rows, start=1):
        try:
            flow = load_flow(
                flow_path,
                variables=_case_variables(base, row, cli_values),
            )
        except FlowError as exc:
            raise FlowError(
                f"Could not load data case {index} for {Path(flow_path).name}: {exc.message}",
                hint=exc.hint,
            ) from exc
        label_value = row.get("case_name")
        label = (
            label_value.strip()
            if isinstance(label_value, str) and label_value.strip()
            else f"{flow.name} [data {index}]"
        )
        cases.append(CaseSpec(flow=flow, label=label, data_index=index))
    return cases


def _case_record(
    index: int,
    spec: CaseSpec,
    result: Any,
    root: Path,
) -> dict[str, Any]:
    failed = next((step for step in result.steps if step.status == "failed"), None)
    return {
        "index": index,
        "label": spec.label,
        "flow": result.name,
        "flow_path": str(spec.flow.path),
        "tags": spec.flow.tags,
        "variable_names": spec.flow.variable_names,
        "data_index": spec.data_index,
        "status": result.status,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "duration_ms": result.duration_ms,
        "summary": {
            "passed": result.passed,
            "failed": result.failed,
            "skipped": result.skipped,
            "total": len(result.steps),
        },
        "warnings": result.warnings,
        "error": failed.error if failed else None,
        "run_dir": _relative(root, Path(result.output_dir)),
        "report_path": _relative(root, Path(result.report_path)),
        "result_path": _relative(root, Path(result.result_path)),
        "manifest_path": _relative(root, Path(result.manifest_path)),
    }


def write_collection_junit(
    records: list[dict[str, Any]],
    path: Path,
    *,
    name: str,
    started_at: str,
    duration_ms: int,
) -> Path:
    target = path.expanduser().resolve()
    failures = sum(record["status"] == "failed" for record in records)
    skipped = sum(record["status"] == "skipped" for record in records)
    root = ET.Element(
        "testsuites",
        {
            "name": name,
            "tests": str(len(records)),
            "failures": str(failures),
            "errors": "0",
            "skipped": str(skipped),
            "time": f"{max(0, duration_ms) / 1000:.3f}",
        },
    )
    for record in records:
        suite = ET.SubElement(
            root,
            "testsuite",
            {
                "name": record["label"],
                "tests": "1",
                "failures": "1" if record["status"] == "failed" else "0",
                "errors": "0",
                "skipped": "1" if record["status"] == "skipped" else "0",
                "time": f"{max(0, record['duration_ms']) / 1000:.3f}",
                "timestamp": record["started_at"],
            },
        )
        case = ET.SubElement(
            suite,
            "testcase",
            {
                "classname": "flow",
                "name": record["label"],
                "time": f"{max(0, record['duration_ms']) / 1000:.3f}",
            },
        )
        if record["status"] == "failed":
            failure = ET.SubElement(case, "failure", {"message": record["error"] or "Flow failed"})
            failure.text = record["error"] or "Flow failed"
        elif record["status"] == "skipped":
            ET.SubElement(case, "skipped", {"message": "Flow was skipped"})
        output = ET.SubElement(case, "system-out")
        output.text = json.dumps(
            {
                "flow_path": record["flow_path"],
                "run_dir": record["run_dir"],
                "report_path": record["report_path"],
                "summary": record["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    ET.indent(root, space="  ")
    atomic_write_text(
        target,
        '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n",
    )
    return target


def _status_class(status: str) -> str:
    return status if status in {"passed", "failed", "skipped"} else "warning"


def render_collection_html(
    *,
    name: str,
    kind: str,
    description: str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    artifacts: dict[str, str],
    started_at: str,
    finished_at: str,
) -> str:
    rows = []
    for record in records:
        report_link = record["report_path"]
        error = (
            f'<p class="error">{html.escape(str(record["error"]))}</p>' if record["error"] else ""
        )
        rows.append(
            "<tr>"
            f"<td>{record['index']}</td>"
            f"<td><strong>{html.escape(record['label'])}</strong><br><span>{html.escape(record['flow_path'])}</span>{error}</td>"
            f"<td><span class='chip chip-{_status_class(record['status'])}'>{html.escape(record['status'])}</span></td>"
            f"<td>{record['duration_ms']:,} ms</td>"
            f"<td><a href='{html.escape(report_link)}'>report</a></td>"
            "</tr>"
        )
    links = " · ".join(
        f"<a href='{html.escape(path)}'>{html.escape(label)}</a>"
        for label, path in artifacts.items()
        if path
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(name)} · App TestBench {html.escape(kind)}</title>
  <style>
    :root {{ color-scheme: light dark; --bg: #f2f1eb; --panel: #fffdf8; --text: #1c2927; --muted: #65716e; --line: #dfe3db; --accent: #0f6a5e; --passed: #13784b; --failed: #b33c33; --skipped: #6b7673; }}
    @media (prefers-color-scheme: dark) {{ :root {{ --bg: #101715; --panel: #17201e; --text: #e7f0ec; --muted: #a4b0ac; --line: #2d3a36; --accent: #76d8c9; --passed: #75daa1; --failed: #ff9187; --skipped: #a9b4b0; }} }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 32px; background: var(--bg); color: var(--text); font: 15px/1.55 "Segoe UI", "Microsoft YaHei", sans-serif; }}
    main {{ max-width: 1100px; margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; font-size: clamp(2rem, 5vw, 3.5rem); letter-spacing: -.04em; }}
    .muted {{ color: var(--muted); }}
    .panel {{ margin-top: 24px; padding: 24px; border: 1px solid var(--line); border-radius: 16px; background: var(--panel); }}
    .stats {{ display: flex; flex-wrap: wrap; gap: 18px; color: var(--muted); }}
    .stats b {{ color: var(--text); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; }}
    td span {{ color: var(--muted); font-size: .82rem; }}
    .chip {{ display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: .8rem; font-weight: 700; }}
    .chip-passed {{ color: var(--passed); background: color-mix(in srgb, var(--passed) 14%, transparent); }}
    .chip-failed {{ color: var(--failed); background: color-mix(in srgb, var(--failed) 14%, transparent); }}
    .chip-skipped {{ color: var(--skipped); background: color-mix(in srgb, var(--skipped) 14%, transparent); }}
    .error {{ margin: 6px 0 0; color: var(--failed); }}
    a {{ color: var(--accent); }}
    footer {{ margin-top: 24px; color: var(--muted); font-size: .85rem; }}
  </style>
</head>
<body>
<main>
  <p class="muted">APP TESTBENCH · {html.escape(kind.upper())}</p>
  <h1>{html.escape(name)}</h1>
  <p class="muted">{html.escape(description or "Sequential flow execution with per-flow evidence.")}</p>
  <section class="panel">
    <div class="stats">
      <span><b>{summary["total"]}</b> flows</span>
      <span><b>{summary["passed"]}</b> passed</span>
      <span><b>{summary["failed"]}</b> failed</span>
      <span><b>{summary["duration_ms"]:,}</b> ms total</span>
    </div>
    <p class="muted">{links}</p>
    <table>
      <thead><tr><th>#</th><th>Flow</th><th>Status</th><th>Duration</th><th>Evidence</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </section>
  <footer>Started {html.escape(started_at)} · Finished {html.escape(finished_at)} · Local-first evidence</footer>
</main>
</body>
</html>
"""


def write_collection_manifest(root: Path, payload: dict[str, Any]) -> Path:
    manifest_path = root / "manifest.json"
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.resolve() == manifest_path.resolve():
            continue
        files.append(
            {
                "path": path.resolve().relative_to(root.resolve()).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "app-testbench-collection-manifest",
        "generated_at": now_iso(),
        "collection": {
            "name": payload["name"],
            "kind": payload["kind"],
            "status": payload["status"],
        },
        "file_count": len(files),
        "total_bytes": sum(item["size_bytes"] for item in files),
        "files": files,
    }
    write_json(manifest_path, manifest)
    return manifest_path


def run_collection(
    cases: Iterable[CaseSpec],
    settings: Settings,
    *,
    output_base: Path,
    name: str,
    kind: str,
    description: str = "",
    wait_for_boot: bool | None = None,
    boot_timeout: float | None = None,
    flow_timeout: float | None = None,
    junit_path: Path | None = None,
    tags: list[str] | None = None,
) -> CollectionRun:
    case_list = list(cases)
    if not case_list:
        raise ConfigError("Collection must contain at least one case")
    started_at = now_iso()
    started = time.monotonic()
    root = create_run_directory(output_base, name)
    cases_dir = root / "cases"
    cases_dir.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    for index, spec in enumerate(case_list, start=1):
        result = FlowRunner(
            settings,
            spec.flow,
            output_base=cases_dir,
            wait_for_boot=wait_for_boot,
            boot_timeout=boot_timeout,
            flow_timeout=flow_timeout,
        ).run()
        records.append(_case_record(index, spec, result, root))
    finished_at = now_iso()
    duration_ms = elapsed_ms(started)
    passed = sum(record["status"] == "passed" for record in records)
    failed = sum(record["status"] == "failed" for record in records)
    skipped = sum(record["status"] == "skipped" for record in records)
    status = "passed" if failed == 0 else "failed"
    result_name = "suite-result.json" if kind == "suite" else "data-result.json"
    report_name = "suite-report.html" if kind == "suite" else "data-report.html"
    result_path = root / result_name
    report_path = root / report_name
    junit = (junit_path or (root / "junit.xml")).expanduser().resolve()
    artifacts = {
        "Report": _relative(root, report_path),
        "JSON result": _relative(root, result_path),
        "JUnit XML": _relative(root, junit),
        "Evidence manifest": "manifest.json",
    }
    summary = {
        "total": len(records),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_ms": duration_ms,
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "kind": f"app-testbench-{kind}-result",
        "name": name,
        "description": description,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "tags": tags or [],
        "summary": summary,
        "cases": records,
        "output_dir": str(root.resolve()),
        "artifacts": artifacts,
    }
    write_collection_junit(
        records,
        junit,
        name=name,
        started_at=started_at,
        duration_ms=duration_ms,
    )
    write_json(result_path, payload)
    atomic_write_text(
        report_path,
        render_collection_html(
            name=name,
            kind=kind,
            description=description,
            records=records,
            summary=summary,
            artifacts=artifacts,
            started_at=started_at,
            finished_at=finished_at,
        ),
    )
    manifest = write_collection_manifest(root, payload)
    return CollectionRun(
        root=root,
        status=status,
        payload=payload,
        result_path=result_path,
        report_path=report_path,
        junit_path=junit,
        manifest_path=manifest,
    )
