# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Opt-in Android boot-readiness gate using `sys.boot_completed`, available
  through `device.wait_for_boot`/`device.boot_timeout` and `run --wait-for-boot`.
- Optional JUnit XML export for flow runs via `run --junit-xml`, including
  passed, failed, and skipped testcases.
- Post-install package identity and version verification for flow install
  actions and the one-shot `install` command.
- Versioned draft 2020-12 JSON Schema contracts for `result.json` and the
  `--json` CLI envelope, packaged with the wheel and sdist.
- Bilingual authorized-testing use cases covering incomplete web coverage,
  isolated authenticated regression, instance/version coverage, evidence-based
  defect handoff, and AI-assisted flow authoring, with explicit anti-bypass
  boundaries.

### Changed

- Daily maintenance now documents Codex native Scheduled as the canonical
  scheduler and keeps the Windows Task Scheduler task disabled to prevent
  concurrent worktree edits.
- Sharpened the README, social preview, and launch copy around a mature MuMu
  runtime, deterministic app testing, and evidence-first verdicts while retaining
  the Beta, authorized-testing, and privacy boundaries.

## [0.1.0] - 2026-11-11

Initial public release.

### Added

- MuMu Manager and ADB discovery with environment-variable overrides.
- `doctor`, instance lifecycle commands, APK installation, launch/close, tap,
  swipe, ASCII text, keyevent, screenshot, UI dump, and logcat commands.
- JSON and YAML flow runner with assertions, setup/teardown sections,
  environment interpolation, strict validation, and structured per-step results.
- Self-contained HTML reports with embedded screenshots, logs, and per-step
  status, duration, output, and errors.
- Machine-readable `--json` output for commands and structured failures.
- Packaged Codex skill, example flows, CI, packaging metadata, and release
  documentation.
- Added bilingual disclaimer, responsible-use, privacy, and third-party notice documents
  tied to the MIT License and release checklist.
- Bilingual publishing, promotion, and launch-copy playbooks with a synthetic
  HTML report preview and social preview assets.
- Optional Windows daily maintenance automation for low-risk fixes,
  verification, expansion proposals, and timed MuMu cleanup. It never commits,
  pushes, tags, publishes, or operates a live device during maintenance.

### Security

- External host commands use argument arrays rather than `shell=True`.
- User-controlled report text is HTML-escaped and reports do not load external
  assets.
- The project has no telemetry or artifact upload behavior.
- Release publication is separated from package publication: Git tags create a
  draft GitHub Release, while PyPI requires a manual workflow with explicit
  confirmation and Trusted Publishing.
- Runtime reports, screenshots, logs, credentials, local configuration, APKs,
  and build artifacts are excluded by default.
- Issue and pull-request guidance warns against submitting secrets, personal
  screenshots, and unredacted logcat.

### Fixed

- YAML mappings with non-string field names now produce a structured flow
  validation error instead of an uncaught `TypeError`.
- `app-testbench init --format json` now defaults to `mumu-flow.json`; the YAML
  default remains `mumu-flow.yaml`.
- Flow key events are normalized and validated during flow loading, so malformed
  keys fail before any device connection is attempted.
- JSON and YAML flows reject duplicate mapping keys instead of silently keeping
  the last value.
- Flow `text` actions preserve quoted leading and trailing whitespace instead of
  silently trimming the value.
- Plain Activity class names such as `MainActivity` expand to a
  package-qualified Android component before `am start`.
- ADB `get-state` reads state from stdout, so server/daemon diagnostics on stderr
  no longer turn a ready device into an invalid state.
- `launch --activity` rejects empty or malformed component values before calling
  ADB, and an empty `--activity` no longer silently falls back to launcher
  discovery.
- Flow step `id` and `name` reject non-string values instead of coercing them.
- Step `description` values appear in `result.json` and the HTML report.
- Reused `dump_ui` and `logcat` labels allocate numbered artifacts instead of
  overwriting earlier evidence.
- `instance start --wait` rejects negative durations and waits for Android
  startup rather than only the emulator process.
- `scripts/check.ps1` handles native-tool progress written to stderr under
  Windows PowerShell 5.1.
- `APP_TESTBENCH_JSON=1` and `--json` produce JSON for success, execution,
  argument, and configuration errors.
- `assert_ui_contains` and `assert_ui_not_contains` use one UI snapshot; only
  `wait_for_text` polls.
- Flow-level `device.instance` and `device.serial` take precedence over
  environment variables as documented, while explicit CLI options still win.
- Failed flow sections record all unexecuted remaining steps as `skipped`.
- Flow integers must be whole numbers, and non-finite numeric settings are
  rejected.
- Instance status respects MuMu `is_process_started` and no longer treats an
  unknown player state as running.
- MuMuManager JSON arrays are accepted in addition to object payloads.
- `launch --activity` detects `am start` error output even when ADB exits with
  status 0.
- Flow reports reject non-string `capture_screenshots` values with a structured
  validation error.
- Explicit `--adb` and `--mumumanager` paths must point to files, so a directory
  is rejected during setting resolution rather than subprocess startup.
- `MuMuManager` control commands treat JSON payloads with `success: false` as
  failures even when the process exits with status 0.
- CLI file-output options reject directory targets and invalid parent paths with
  structured configuration errors instead of failing later during artifact writes.
- A literal `--json` passed as text after the `--` separator no longer switches
  the command into JSON output mode.
- UI hierarchy dumps remove the remote temporary XML file even when reading or
  validating the dump fails, preventing device-side debris.
- Global CLI options are honored before the subcommand, matching the documented
  examples instead of being silently replaced by subparser defaults.
- ADB auto-discovery no longer selects `adb_server.exe` as the client executable.
- Documentation no longer claims flow retry support that is not present in v0.1.0.
- Final logcat collection allocates a numbered path when a teardown step already uses
  `logcat-final`, preserving both pieces of evidence.
- `--debug` is accepted both before and after the subcommand, matching the shared
  global-option behavior.
- MuMu port fallback no longer probes sibling instance ports for a stopped target
  or overrides an explicitly reported port, preventing commands from targeting the
  wrong emulator.
- One-shot device commands validate arguments and output paths before connecting,
  and invalid arguments now return the documented configuration-error exit code.
- ADB and MuMuManager discovery honors an explicitly supplied environment `PATH`
  instead of falling back to the host process environment.
- Explicit empty `--adb` and `--mumumanager` values are rejected instead of
  silently falling back to environment-based discovery.
- `instance start --wait` no longer sleeps past the requested readiness
  timeout, so short waits return close to their configured deadline.
- Exit-code documentation now matches the implemented behavior and marks the
  unused environment-not-ready code as reserved.
