# Architecture

## Goal

Provide a small Android execution layer for MuMu Player that is useful both to humans and agents:

- deterministic command surface
- machine-readable output
- evidence-rich reports
- strict flow validation
- explicit failure states

It is not a general-purpose RPA platform and does not attempt visual recognition.

## Layers

```text
CLI (argparse)
  ├─ settings / discovery
  ├─ doctor
  ├─ one-shot device commands
  ├─ flow validation
  └─ flow runner
       ├─ MuMuManager adapter
       ├─ ADB device adapter
       ├─ step executor
       └─ report writer
```

### `config.py`

Resolves explicit CLI values, environment variables, PATH, Windows registry entries, common MuMu layouts, and Android SDK locations. It never launches MuMu automatically.

### `mumu.py`

Wraps the documented/observed MuMuManager command family:

```text
MuMuManager.exe version
MuMuManager.exe info -v all
MuMuManager.exe info -v <index>
MuMuManager.exe control -v <index> <launch|shutdown|restart>
```

Instance JSON is normalized into `Instance`. ADB serial resolution prefers the reported `adb_port`, then probes MuMu's `16384 + 32*n` block, then falls back to the calculated base port.

### `device.py`

Wraps ADB commands with a fixed serial and bounded timeout. It validates package names, coordinates, key names, text encoding, PNG signatures, and UI XML before recording artifacts. It can poll `sys.boot_completed` as an opt-in readiness gate and can verify installed package identity/version fields through `dumpsys package`.

### `flow.py`

Implements a strict, versioned flow schema. Unknown fields and wrong types are configuration errors, not runtime surprises. Relative APK paths resolve against the flow file.

### `runner.py`

Executes `setup` → `steps` → `teardown`, records every step, and continues teardown after failures. It attempts a diagnostic screenshot and final logcat on failure.

### `reporting.py`

Creates a unique run directory and writes:

- `result.json`: stable machine-readable result
- `report.html`: self-contained UI
- `junit.xml`: optional JUnit XML export requested by `--junit-xml`

Screenshots are embedded as base64. HTML text is escaped. Logs and UI XML are truncated for report size but remain available as separate artifacts.

## Failure model

| Exception | Exit code | Typical cause |
| --- | --- | --- |
| `ConfigError` | 2 | bad CLI/environment setting or required tool unavailable |
| `FlowError` | 2 | invalid flow schema |
| `EnvironmentNotReady` | 3 | reserved for a future environment gate; current paths do not raise it |
| `DeviceError` | 1 | ADB operation failed or no unambiguous device |
| `MuMuError` | 1 | MuMuManager operation failed |
| `StepFailure` | 1 | flow assertion failed |

The CLI catches expected errors and emits a structured JSON object when `--json` is active. The packaged schemas `result-v1.schema.json` and `cli-v1.schema.json` define the machine-readable contracts for draft 2020-12 validators.

## Security boundaries

- No `shell=True` invocation of host commands.
- ADB arguments are passed as arrays; text input is encoded and quoted for the Android shell.
- YAML uses `safe_load`.
- Reports do not load external assets.
- User-controlled report text is HTML-escaped.
- The tool does not upload artifacts or collect telemetry.

Residual risks include malicious APKs, compromised ADB binaries, sensitive screenshots/logs, and user-authored flows that intentionally stop or overwrite app state.

## Test strategy

- Unit tests for flow parsing, validation, ADB helpers, MuMu JSON parsing, and report escaping.
- End-to-end tests through fake `adb` and `MuMuManager` executables.
- CLI subprocess test for the `python -m app_testbench` boundary.
- CI matrix for Windows and Linux, Python 3.10–3.12.

The fake backends cover command shape, artifacts, reports, and failure handling. They do not prove compatibility with every MuMu release; that requires a live integration test on a supported Windows host.

## Extension points

Reasonable next additions:

- ADBKeyboard/clipboard Unicode input
- `wait_for_ui` selectors by resource-id or content-desc
- multiple device profiles
- image comparison hook
- a resume/retry policy
- MCP server wrapper

Keep the core rule: generate valid artifacts, call the real backend, then verify the result.
