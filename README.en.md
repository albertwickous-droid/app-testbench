# App TestBench

[简体中文](README.md) | **English** | [Agent](docs/agent-deployment.md)

![App TestBench: repeatable Android app testing on MuMu](assets/banner.png)

**Repeatable Android app testing on a mature MuMu runtime. Keep every step explicit, and keep the screenshot, UI tree, logcat, and HTML report when a run fails.**

App TestBench is a Windows-first command-line tool for Android app UI testing. It turns APK installation, app launch, taps, text entry, waits, assertions, screenshots, UI dumps, and logcat collection into JSON/YAML flows. Every run produces a self-contained HTML report, `result.json`, and optional JUnit XML.

The runner does not ask a vision model to guess the next screen. The flow declares every action, and explicit UI, Activity, logcat, or file assertions decide whether a step passes. When something breaks, you get the failed step, timing, current screen, UI hierarchy, and recent logs instead of a vague "cannot reproduce" note.

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)
![Platform](https://img.shields.io/badge/platform-Windows-0078D4.svg)
![Status](https://img.shields.io/badge/status-v0.1.1-0B7A75.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> Independent open-source project. Not affiliated with or endorsed by NetEase or the MuMu team. Test only apps, accounts, devices, and data that you own or are explicitly authorized to test.

## Is this the right tool?

| What you need | Fit |
| --- | --- |
| Repeat the same app journey without clicking through it by hand | **Good fit**: define steps, waits, and assertions in JSON/YAML |
| Preserve evidence when a test fails | **Good fit**: failed-step screenshot, UI tree, logcat, timings, and HTML |
| A stable Android runtime on Windows | **Good fit**: MuMu Player is the first supported runtime backend |
| Machine-readable results for CI or an agent | **Good fit**: `result.json`, JUnit XML, and the versioned `--json` envelope |
| A one-off tap or a temporary ADB command | **Supported**, but the flow runner is the main product |
| Bypass login, CAPTCHA, anti-bot controls, rate limits, or access controls | **Not supported** |

## Supported capabilities

| Area | What is supported | What you get |
| --- | --- | --- |
| Environment and instances | `doctor`, MuMu instance list/start/stop/restart, ADB discovery, instance or serial selection | A known-good toolchain and device before a run |
| APK and app lifecycle | APK install, package/version verification, launch, URI open, force-stop, clear data, orientation | Install, cold launch, deep links, reset, and screen orientation in one flow |
| UI interaction | Coordinate tap, text/content-desc tap, swipe, printable-ASCII text, clear text, key events, Back, Home | Reusable steps instead of manual interaction |
| Waits and assertions | Fixed wait, `wait_for_text`, `wait_for_activity`, UI contains/not-contains, logcat contains, visible ANR recovery | A test that can actually pass or fail on a condition |
| Evidence | Screenshots, UI hierarchy, logcat, failure diagnostics, step status and timing | A clear record of what failed and what the app showed |
| Flow orchestration | JSON/YAML, `setup`/`steps`/`teardown`, environment interpolation, `continue_on_error`, boot readiness gate | Install, test, cleanup, and evidence in one repeatable document |
| Local test services | `reverse-port` for host-to-device ports and `open` for URIs | WebView, download, media, and local QA fixture coverage |
| Reports and CI | Self-contained HTML, `result.json`, optional JUnit XML, structured failure JSON | Humans read the report; CI and agents read the result |
| Agent support | Packaged Codex skill, English agent runbook, strict schemas, five reproducible live cases | A stable operating procedure instead of guessed coordinates and ad-hoc environments |

## First run: from installation to the first HTML report

### 1. Prepare the runtime

You need:

- Windows 10/11;
- Python 3.10 or newer;
- MuMu Player installed with ADB debugging enabled;
- a dedicated MuMu test instance, initially instance `0`;
- an app, account, and data set that you own or are authorized to test.

Start the MuMu instance first. Do not begin with a production account, personal data, or an unauthorized device.

### 2. Install App TestBench

The current supported installation path is from source:

```powershell
git clone https://github.com/albertwickous-droid/app-testbench.git
cd app-testbench
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
app-testbench --version
```

Continue when the command reports `app-testbench 0.1.1`.

### 3. Check MuMu, ADB, and the selected instance

```powershell
app-testbench doctor --json
```

Check three things in the JSON:

- MuMuManager and ADB were found;
- the selected instance is running;
- ADB can reach that instance.

If discovery fails, pass explicit paths or use environment variables:

```powershell
app-testbench doctor --json `
  --mumumanager "C:\path\to\MuMuManager.exe" `
  --adb "C:\path\to\adb.exe" `
  --instance 0
```

The supported environment variables are `APP_TESTBENCH_MUMUMANAGER`, `APP_TESTBENCH_ADB`, `APP_TESTBENCH_INSTANCE`, and `APP_TESTBENCH_SERIAL`.

### 4. Create a minimal first flow

Save this as `first-flow.yaml`. It does not need your business app. It opens Android Settings, takes a screenshot, dumps the UI hierarchy, and captures logcat so you can verify the runner and report pipeline end to end.

```yaml
version: 1
name: first-smoke
description: Open Android Settings and capture the first evidence bundle.
device:
  instance: 0
  wait_for_boot: true
  boot_timeout: 60
report:
  title: First App TestBench smoke test
  capture_screenshots: all
  collect_logcat: true
  clear_logcat: true
  include_ui_xml: true
steps:
  - name: Launch Android Settings
    action: launch
    package: com.android.settings
  - name: Let the first screen settle
    action: wait
    seconds: 2
  - name: Capture the settings screen
    action: screenshot
    label: settings
  - name: Capture the UI hierarchy
    action: dump_ui
    label: settings
teardown:
  - name: Capture recent logcat
    action: logcat
    label: final
    lines: 1000
```

### 5. Validate, then run

```powershell
app-testbench validate .\first-flow.yaml --json
app-testbench run .\first-flow.yaml `
  --output .\runs `
  --junit-xml .\runs\first-smoke-junit.xml `
  --json
```

`validate` checks the flow document without touching the device. `run` performs the device actions. Exit codes are `0` for success, `1` for execution failure, `2` for invalid arguments or flow configuration, `3` for an environment that is not ready, and `130` for interruption.

### 6. Open the artifacts

The run directory looks like this:

```text
runs/<timestamp>-first-smoke/
├── report.html       # self-contained; opens offline
├── result.json       # versioned machine-readable result
├── screenshots/
├── ui/
└── logs/
```

Open `report.html` first. Read `result.json` from CI or an agent. Pass `--junit-xml` when the result must enter a JUnit-compatible test system.

![App TestBench HTML report preview](assets/report-preview.png)

The report embeds screenshots, UI snippets, and logcat and does not load a CDN, external script, or external stylesheet. The desktop step rail scrolls independently, and the report supports Light and Dark themes.

## Start testing your own app

### Path A: verify one action at a time

```powershell
# Install and verify package name, versionCode, and versionName.
app-testbench install .\app.apk `
  --expected-package com.example.app `
  --expected-version-code 42 `
  --expected-version-name 1.2.3

# Launch the app and capture the current state.
app-testbench launch com.example.app
app-testbench screenshot --output .\artifacts\home.png
app-testbench dump-ui --output .\artifacts\home.xml
app-testbench logcat --output .\artifacts\logcat.txt --lines 2000
```

### Path B: turn the steps into a flow

1. Generate a template with `app-testbench init --output .\app-testbench-flow.yaml`.
2. Replace `device.package`, the APK path, and the sample steps with your target.
3. Inspect the real screen with `screenshot` and `dump_ui`; prefer `wait_for_text` and `tap_text` before coordinates.
4. Add `assert_ui_contains`, `wait_for_activity`, or `assert_logcat_contains` so the flow can fail for the right reason.
5. Run `app-testbench validate`, then run the flow.

A small but realistic flow:

```yaml
version: 1
name: login-smoke
device:
  instance: 0
  package: com.example.app
  wait_for_boot: true
setup:
  - action: install
    apk: ./app.apk
    expected_package: com.example.app
    expected_version_code: 42
steps:
  - action: launch
  - action: wait_for_text
    text: Login
    timeout: 20
  - action: tap_text
    text: Username
  - action: text
    text: qa-user
  - action: tap_text
    text: Continue
  - action: wait_for_activity
    activity: com.example.app/.HomeActivity
    timeout: 10
  - action: assert_ui_contains
    text: Home
teardown:
  - action: logcat
    label: final
    lines: 2000
    continue_on_error: true
```

`text` currently supports printable ASCII only. Chinese, Japanese, and other Unicode input require a separately approved ADBKeyboard, clipboard, or IME path.

## Goal-to-command map

| I want to... | Direct command | Flow action |
| --- | --- | --- |
| Start/stop/restart a MuMu instance | `app-testbench instance start 0` | Usually prepared outside the flow |
| Check runtime readiness | `app-testbench doctor --json` | Run before the business flow |
| Install and verify an APK | `app-testbench install .\app.apk --expected-package com.example.app` | `action: install` with `expected_*` |
| Launch an app | `app-testbench launch com.example.app` | `action: launch` |
| Launch a specific Activity | `app-testbench launch com.example.app --activity .MainActivity` | `action: launch` + `activity` |
| Open a URI or deep link | `app-testbench open "https://example.test/" --package com.example.app` | `action: open` |
| Force-stop an app | `app-testbench close com.example.app` | `action: close` |
| Clear app data | `app-testbench clear-data com.example.app` | `action: clear_app_data` |
| Change orientation | `app-testbench orientation landscape` | `action: orientation` |
| Tap coordinates | `app-testbench tap 540 1200` | `action: tap` |
| Tap by visible text or content description | Prefer a flow | `action: tap_text` with exact/contains, index, and timeout |
| Enter ASCII text | `app-testbench text "qa@example.test"` | `action: text` |
| Clear an input | Focus it, then use a flow | `action: clear_text` |
| Send Back or Home | `app-testbench keyevent BACK` | `action: back` / `action: home` |
| Wait for visible text | Use a flow | `action: wait_for_text`; optional ANR recovery |
| Wait for an Activity | Use a flow | `action: wait_for_activity` |
| Assert text is present/absent | Use a flow | `action: assert_ui_contains` / `action: assert_ui_not_contains` |
| Assert a logcat substring | Use a flow | `action: assert_logcat_contains` |
| Capture a screenshot | `app-testbench screenshot --output .\artifacts\home.png` | `action: screenshot` |
| Dump the UI hierarchy | `app-testbench dump-ui --output .\artifacts\ui.xml` | `action: dump_ui` |
| Capture recent logcat | `app-testbench logcat --output .\artifacts\log.txt --lines 2000` | `action: logcat` |
| Map a local test server | `app-testbench reverse-port 18765 --local-port 18765` | `action: reverse_port` |
| Produce a complete HTML report | `app-testbench run .\flow.yaml --junit-xml .\junit.xml` | Generated automatically by `run` |
| Feed results into CI | `app-testbench run .\flow.yaml --json` | `result.json` + JSON envelope |

See [`docs/flow-reference.md`](docs/flow-reference.md) for every field, alias, default, and validation rule.

## Live cases: evidence, not just "it can tap"

All five public cases were run on a real MuMu instance. Each uses a pinned APK with SHA256 verification, and every public app screenshot comes from the actual run.

| Case | Risk covered | Observed result |
| --- | --- | --- |
| [Wikipedia search, article, and cold-start persistence](examples/wikipedia-research-session/) | Live network app, onboarding, dynamic search, WebView article, saved item, force-stop/restore | **63/63 passed, 113.563 s** |
| [Firefox browser state, download, and tabs](examples/firefox-webapp-session/) | Cookie + LocalStorage, scoped test state, file download, two tabs, cold-start restore | **66/66 passed, 143.016 s** |
| [VLC media, Activity, and logcat](examples/vlc-media-playback/) | Native player Activity, byte-range MP4, decoded frames, media logs, orientation | **43/43 passed, 50.579 s** |
| [AnkiDroid deck, card, and cold start](examples/ankidroid-deck-persistence/) | Onboarding, dialogs, card entry, database persistence, post-restart assertions | **49/49 passed, 75.203 s** |
| [Markor note save, search, and cold start](examples/markor-note-persistence/) | Multi-page onboarding, editor input, file save, exact search, body recovery | **46/46 passed, 80.203 s** |

Each wrapper downloads and verifies a pinned APK, uses case-owned test data, and keeps APKs, raw screenshots, UI XML, logcat, and complete run directories under the ignored `runs/` tree.

```powershell
# Run one case at a time on a free test instance.
.\examples\wikipedia-research-session\run.ps1
.\examples\firefox-webapp-session\run.ps1
.\examples\vlc-media-playback\run.ps1
.\examples\ankidroid-deck-persistence\run.ps1
.\examples\markor-note-persistence\run.ps1
```

See [`docs/cases.md`](docs/cases.md) for versions, screenshots, observed results, evidence boundaries, and known limits.

## Why build on MuMu

Starting a temporary Android environment on Windows is easy. Making the same failure explainable a week later requires a known instance, Android image, ADB path, and retained evidence.

MuMu Player provides the mature instance lifecycle, Android runtime, and ADB connectivity. App TestBench does not reimplement that layer. It adds test orchestration, dynamic waits, assertions, failure diagnostics, and report delivery.

| Approach | Good for | Main limitation |
| --- | --- | --- |
| Manual testing on a physical device | Final acceptance and hardware behavior | Repetition cost and manually assembled evidence |
| A temporary ADB script | One action | No waits, assertions, failure context, or common result format |
| Vision-model screen clicking | Exploratory automation | Environment and per-step decisions are difficult to reproduce |
| An ad-hoc AI-built Android environment | A quick demo | Toolchain instability and hard-to-diagnose failures |
| **App TestBench + MuMu** | Frequent smoke tests, regression, WebView/browser journeys, defect handoff | v0.1.1 is Windows + MuMu first; physical-device acceptance still matters |

## Authorized scenarios and boundaries

Use App TestBench only in environments you are authorized to test. Typical fits include:

- the web version is incomplete or behaves differently, while the organization permits native-app testing;
- desktop-web automation is constrained and the team has an approved native-app test environment or test API;
- an isolated MuMu instance signs in to a dedicated test account through the normal UI, then verifies authenticated pages and permissions;
- a flow needs to verify Cookie, LocalStorage, downloads, tabs, and state after a cold start;
- a defect needs a repeatable handoff across QA, development, and product;
- behavior must be compared across instances, Android images, resolutions, app builds, or cold/warm starts.

The system, account, data, and device must be owned or explicitly authorized for testing. App TestBench does not steal cookies, export tokens, solve CAPTCHAs, evade risk controls, or bypass access controls. If a web restriction is part of the product's security design, use an organization-approved native test environment or test API rather than treating this tool as a bypass.

More examples and boundaries are in [`docs/use-cases.md`](docs/use-cases.md), [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md), and [`DISCLAIMER.md`](DISCLAIMER.md).

## Outputs and CI

Each `run` creates a unique output directory. When possible, a failure retains:

- the failed step and original error;
- a failure screenshot;
- the UI hierarchy;
- recent logcat;
- completed and skipped steps with timings;
- a consistent `result.json`, HTML report, and JUnit state.

Every device command supports `--json`. A failed `run --json` still returns the complete `data` payload and a structured `error`. The JSON contracts are packaged Draft 2020-12 schemas.

## Known limits

- v0.1.1 is Windows + MuMu Player first. It does not claim every MuMu, Android, ADB, resolution, or language combination.
- Selectors and coordinates are calibrated for pinned apps, languages, and `720x1280`; app updates require flow maintenance.
- Native `text` input supports printable ASCII only; Chinese input is not covered.
- Games, Canvas surfaces, custom-rendered UI, and incomplete accessibility trees may not be readable through `uiautomator dump`.
- The VLC case is not a DRM, HLS/DASH, subtitle, or audio-track compatibility certification.
- A passing automated run is not production release approval. Physical devices, OEM behavior, and production accounts still require separate acceptance.
- Reports and logs can contain environment data. Redact them before publishing.

## Documentation

- [Five live cases and screenshots](docs/cases.md)
- [Complete flow action reference](docs/flow-reference.md)
- [Architecture](docs/architecture.md)
- [Use cases](docs/use-cases.md)
- [Validation record](docs/validation.md)
- [Agent deployment runbook](docs/agent-deployment.md)
- [Publishing and maintenance](docs/publishing.md)
- [Changelog](CHANGELOG.md)

## Contributing

Reproducible bug reports, new flows, documentation fixes, and code improvements are welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before opening an issue or pull request. Never submit real accounts, cookies, tokens, API keys, private addresses, or unredacted customer data in an issue, PR, screenshot, or log.

## License and third-party notices

MIT. MuMu, ADB, Android, test apps, and test media remain subject to their own licenses and trademark rules. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
