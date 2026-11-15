---
name: app-testbench
description: Run repeatable Android app UI test flows through App TestBench, with MuMu Player as the first mature runtime backend. Use for verified APK installation, boot readiness gates, launch/close, tap/swipe/text/keyevent, screenshots, UI dump, logcat, JSON/YAML regression flows, JUnit XML, and self-contained HTML test reports.
---

# App TestBench

Use `app-testbench` when the user wants to install and exercise an Android app, reproduce a UI flow, collect screenshots/logcat, or produce an HTML QA report. MuMu Player is the first supported runtime backend.

## Operating rules

1. Run `app-testbench doctor --json` before device work when possible.
2. Prefer `--json` for every command and parse the structured result.
3. Do not shut down a MuMu instance, uninstall an app, or overwrite a report unless the user asked for that state change.
4. Treat screenshots, UI XML, and logcat as potentially sensitive.
5. Do not invent coordinates silently. Use the user's values, a current screenshot/UI inspection, or ask for the missing coordinate.
6. Text input supports printable ASCII only. Explain the ADBKeyboard/clipboard limitation for Chinese or other Unicode.
7. Report the exact `report.html`, `result.json`, and optional `junit.xml` paths when a flow finishes.

## Install / discovery

```powershell
python -m pip install -e .
app-testbench doctor --json
```

Global options can appear before or after a subcommand:

```powershell
app-testbench --instance 0 --json doctor
app-testbench doctor --instance 0 --json
```

Environment overrides:

- `APP_TESTBENCH_MUMU_MANAGER`
- `APP_TESTBENCH_ADB`
- `APP_TESTBENCH_INSTANCE`
- `APP_TESTBENCH_SERIAL`
- `APP_TESTBENCH_TIMEOUT`
- `APP_TESTBENCH_JSON=1`

## Command surface

```text
doctor
instance list|start|stop|restart
install <apk> [--expected-package ...] [--expected-version-code ...] [--expected-version-name ...]
launch <package> [--activity ...]
open <uri> [--package ...] [--mime-type ...]
close <package>
clear-data <package>
orientation portrait|landscape|auto
reverse-port <port> [--local-port ...] [--remove]
tap <x> <y>
swipe <x1> <y1> <x2> <y2> [--duration-ms ...]
text <ascii-text>
keyevent <key>
screenshot [--output ...]
dump-ui [--output ...]
logcat [--output ...] [--lines ...] [--clear]
validate <flow>
run <flow> [--output <parent-dir>] [--junit-xml <file>] [--wait-for-boot] [--boot-timeout <seconds>]
init [--output ...] [--format yaml|json]
skill-path
```

Examples:

```powershell
app-testbench --instance 0 install .\app.apk `
  --expected-package com.example.app --expected-version-code 42 --expected-version-name 1.2.3
app-testbench --instance 0 launch com.example.app
app-testbench --instance 0 open "https://example.test/" --package com.example.app --mime-type text/html
app-testbench --instance 0 reverse-port 18765 --local-port 18765
app-testbench --instance 0 orientation landscape
app-testbench --instance 0 tap 540 1200
app-testbench --instance 0 screenshot --output .\artifacts\home.png
app-testbench --instance 0 dump-ui --output .\artifacts\home.xml
app-testbench --instance 0 logcat --output .\artifacts\logcat.txt --lines 2000
app-testbench run .\app-testbench-flow.yaml --output .\runs --junit-xml .\artifacts\junit.xml --wait-for-boot
```

## Public live cases

Before inventing a new smoke test, reproduce one of the committed cases when the environment matches:

```powershell
.\examples\fennec-local-web-session\run.ps1
.\examples\vlc-http-playback\run.ps1
```

- Fennec: 71-step browser/WebView case with onboarding, login, asynchronous search, detail, cold start, and localStorage restoration.
- VLC: 30-step media case with ADB reverse, HTTP byte ranges, orientation, real playback, and MediaCodec logcat evidence.

The scripts download and verify APKs under `runs/case-assets/`. Require the documented step counts, JUnit, screenshots, and self-contained HTML before reporting success. `clear-data` is destructive to the selected app's state; use it only when the test contract requires a clean start.

## Agent workflow for a requested App journey

1. Run `doctor --json`.
2. Confirm the APK path, package name, MuMu instance, and starting screen.
3. Create a flow with `app-testbench init --output <path>` or write JSON/YAML.
4. Use `wait_for_text` before tapping stable screens; use screenshots/UI dumps for investigation.
5. Run `validate <flow> --json`.
6. Run `run <flow> --json`.
7. On failure, inspect the report's screenshot/UI/logcat and repair the flow or report the blocker with evidence.
8. Return the action summary and absolute artifact paths.

Minimal flow:

```yaml
version: 1
name: smoke
device:
  instance: 0
  package: com.example.app
  wait_for_boot: true
  boot_timeout: 60
report:
  capture_screenshots: all
  collect_logcat: true
setup:
  - action: install
    apk: ./app.apk
    expected_version_code: 42
    expected_version_name: 1.2.3
steps:
  - action: launch
  - action: wait_for_text
    text: Login
    timeout: 20
  - action: screenshot
    label: login
teardown:
  - action: logcat
    label: final
    lines: 2000
```

## Artifacts

`run` creates a unique run directory:

```text
runs/<timestamp>-<flow-name>/
├── report.html
├── result.json
├── junit.xml          # optional
├── screenshots/
├── ui/
└── logs/
```

The HTML report embeds screenshots and logcat excerpts and works offline.

## JSON contract

The packaged schemas are `app_testbench/schemas/cli-v1.schema.json` and
`app_testbench/schemas/result-v1.schema.json` (JSON Schema draft 2020-12).

Success:

```json
{
  "schema_version": "1.0",
  "ok": true,
  "command": "doctor",
  "generated_at": "2026-11-05T12:00:00+08:00",
  "data": {}
}
```

Failure:

```json
{
  "schema_version": "1.0",
  "ok": false,
  "command": "run",
  "error": {
    "type": "flow_error",
    "message": "...",
    "hint": "..."
  }
}
```

Exit codes: `0` success, `1` execution failure, `2` configuration/flow error, `3` environment not ready, `130` interrupted.

## Troubleshooting

- MuMuManager not found: pass `--mumumanager` or set `APP_TESTBENCH_MUMU_MANAGER`.
- ADB not found: pass `--adb` or set `APP_TESTBENCH_ADB`.
- No device: start the instance, then run `doctor`.
- Offline device: restart ADB or the instance; do not randomly kill unrelated processes.
- UI text unavailable: use screenshot coordinates or inspect the XML; WebView/game surfaces may not expose text.
- Unicode text cannot be entered: explain the ASCII limitation and use a separately authorized ADBKeyboard/clipboard method.

## Do not

- Do not execute arbitrary host shell commands as a substitute for a defined flow action.
- Do not use this skill to bypass authentication, anti-cheat, or app security controls.
- Do not publish a report containing personal data without redaction.
