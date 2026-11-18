# Flow reference

A flow is a JSON or YAML object with `version: 1`. The runner validates the whole document before touching the device.

## Top-level fields

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `version` | integer/string | no | Must be `1`; defaults to `1` |
| `name` | string | no | Flow name; defaults to the filename stem |
| `description` | string | no | Shown in the HTML report |
| `device` | object | no | Instance, serial, and default package |
| `setup` | array | no | Actions run before `steps` |
| `steps` | array | yes* | Main test actions |
| `teardown` | array | no | Actions run even after a main failure |
| `report` | object | no | Screenshot/log/report settings |

\* The document must contain at least one action across `setup`, `steps`, and `teardown`.

Unknown fields are rejected. This is intentional: a typo such as `duratoin_ms` should not silently fall back to a default.

## Device fields

```yaml
device:
  instance: 0
  serial: ${APP_TESTBENCH_SERIAL}  # optional; omit to let MuMuManager resolve it
  package: com.example.app
```

| Field | Meaning |
| --- | --- |
| `instance` | MuMu instance index; defaults to `0` |
| `serial` | Explicit ADB serial; bypasses port discovery |
| `package` | Default package for `launch` and `close` |
| `wait_for_boot` | Poll `sys.boot_completed` before actions; default `false` |
| `boot_timeout` | Boot-readiness timeout in seconds; default `60` |

Precedence:

1. CLI `--serial` / `--instance`
2. `device.serial` / `device.instance`
3. `APP_TESTBENCH_SERIAL` / `APP_TESTBENCH_INSTANCE`
4. Defaults (`0`; resolve the port from MuMuManager)

## Environment variables

Any string value may contain `${NAME}`:

```yaml
device:
  package: ${APP_PACKAGE}
setup:
  - action: install
    apk: ${APK_PATH}
```

All `${NAME}` references must exist when the flow is loaded. Missing variables produce a `FlowError` before any device action.

## Common step fields

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `action` | string | required | Whitelisted action name |
| `id` | string | section-index | Unique artifact/result identifier |
| `name` | string | humanized action | Display name |
| `description` | string | unset | Optional note copied to `result.json` and the HTML report |
| `continue_on_error` | boolean | `false` | Continue to the next step after failure |
| `screenshot` | boolean | `false` | Capture after this step even if global mode differs |

## Actions

### `install`

```yaml
- action: install
  apk: ./app.apk
  reinstall: true
  grant_permissions: false
  expected_package: com.example.app
  expected_version_code: 42
  expected_version_name: 1.2.3
```

| Field | Required | Default |
| --- | --- | --- |
| `apk` | yes | — |
| `reinstall` | no | `true` (`adb install -r`) |
| `grant_permissions` | no | `false` (`adb install -g`) |
| `expected_package` | no | unset |
| `expected_version_code` | no | unset |
| `expected_version_name` | no | unset |

Relative APK paths resolve against the flow file's directory. When any
`expected_*` field is set, the runner reads `dumpsys package <package>` after a
successful install and fails the step on a mismatch. If only version fields are
set, `device.package` supplies the package name. With no expectation fields, the
old install behavior is preserved and `dumpsys` is not called.

### `launch`

```yaml
- action: launch
  package: com.example.app
  activity: .MainActivity
```

`package` falls back to `device.package`. Without `activity`, the runner uses the Launcher Intent through `monkey`. With `activity`, it calls `am start -W -n`. A plain class name such as `MainActivity` expands to `package.MainActivity`; `.Activity` becomes the package-relative class, and a fully qualified class name is passed through.

### `open`

```yaml
- action: open
  uri: https://example.test/
  package: com.example.app
  mime_type: text/html
```

Opens an `http`, `https`, `file`, or `content` URI through an Android `ACTION_VIEW` intent. `package` is optional and restricts the intent to one app. `mime_type` is optional and normalized to lowercase. Unsafe schemes such as `javascript:` are rejected.

### `close`

```yaml
- action: close
  package: com.example.app
```

Uses `am force-stop`. `package` falls back to `device.package`.

### `clear-data`

```yaml
- action: clear-data
  package: com.example.app
```

Runs `pm clear`, which stops the app process and clears its data. `package` falls back to `device.package`. This is destructive to the app under test and should be explicit in `setup`.

### `orientation`

```yaml
- action: orientation
  mode: landscape
```

Accepted modes are `portrait`, `landscape`, and `auto`. Fixed modes call `wm fixed-to-user-rotation enabled`, lock the requested rotation, then poll `dumpsys input` until `SurfaceOrientation` matches. `auto` restores free rotation. MuMu may take a moment to settle after the orientation call, so an explicit `wait` can still be useful after relaunching an activity.

### `reverse-port`

```yaml
- action: reverse-port
  port: 18765
  local_port: 18765
```

Adds an `adb reverse tcp:<device-port> tcp:<host-port>` mapping. `local_port` defaults to the device port. Set `remove: true` in teardown, without `local_port`, to remove the mapping.


### `tap`

```yaml
- action: tap
  x: 540
  y: 1200
```

Coordinates must be integers from `0` to `100000`.

### `tap_text`

```yaml
- action: tap_text
  text: Search
  field: content-desc
  match: exact
  timeout: 10
  interval: 0.5
```

Polls the live UI hierarchy, finds a visible node whose `text` or
`content-desc` matches the requested value, and taps the center of that node.
This is less resolution-sensitive than raw coordinates and works well for
toolbar buttons, tabs, and list rows when accessibility text is present.

| Field | Values | Default |
| --- | --- | --- |
| `text` | non-empty string | required |
| `field` | `any`, `text`, `content-desc` | `any` |
| `match` | `exact`, `contains` | `contains` |
| `index` | zero-based match index | `0` |
| `timeout` | seconds | `10` |
| `interval` | seconds | `0.5` |
| `ignore_case` | boolean | `false` |
| `optional` | boolean; missing text returns `found: false` instead of failing | `false` |

UI nodes with empty or zero-size bounds are ignored. If the target remains
absent, the step fails with the last visible text and UI dump error. Set
`optional: true` for an idempotent dismissal or a dialog that may already be
closed; the output then contains `found: false` without failing the run.

### `swipe`

```yaml
- action: swipe
  x1: 540
  y1: 1600
  x2: 540
  y2: 500
  duration_ms: 500
```

`duration_ms` defaults to `300` and must be between `1` and `600000`.

### `text`

```yaml
- action: text
  text: hello world
```

Printable ASCII only. Spaces are encoded as `%s` for Android `input text`. Quoted leading and trailing spaces are preserved. Non-ASCII text fails loudly; use ADBKeyboard or clipboard automation separately.

### `clear_text`

```yaml
- action: clear_text
  count: 40
```

Sends repeated `KEYCODE_DEL` events to the currently focused input. Call a
`tap_text` or `tap` step first to focus the field. `count` defaults to `40` and
must be between `1` and `500`. This is intentionally explicit: the runner does
not guess whether an app uses a search box, a form field, or a custom editor.

### `keyevent`

```yaml
- action: keyevent
  key: ENTER
```

Accepts a numeric code, `ENTER`, or `KEYCODE_ENTER`. Names are normalized to `KEYCODE_<NAME>`.

### `back` / `home`

```yaml
- action: back
- action: home
```

### `wait`

```yaml
- action: wait
  seconds: 1.5
```

Maximum 3600 seconds.

### `screenshot`

```yaml
- action: screenshot
  label: login
```

`label` controls the artifact filename. It defaults to the step ID.

### `dump_ui`

```yaml
- action: dump_ui
  label: login-tree
```

Saves the raw UI XML. The step output also contains node count and a text preview.

### `logcat`

```yaml
- action: logcat
  label: after-login
  lines: 2000
```

`lines` defaults to `1000`. The final report also collects `logs/logcat-final.txt` when `report.collect_logcat` is true, or whenever a step fails. Repeated `dump_ui` or `logcat` labels receive numbered filenames instead of overwriting earlier evidence.

### `assert_ui_contains`

```yaml
- action: assert_ui_contains
  text: Login
  ignore_case: false
```

Dumps the UI once and searches `text` and `content-desc` values.

### `assert_ui_not_contains`

```yaml
- action: assert_ui_not_contains
  text: Error
```

Fails if the text is present. `ignore_case` defaults to `false`.

### `wait_for_text`

```yaml
- action: wait_for_text
  text: Login
  timeout: 20
  interval: 0.5
  ignore_case: false
  recover_anr: true
```

Polls `uiautomator dump` until the text appears. `timeout` is seconds (default `10`), `interval` is seconds (default `0.5`). Transient dump failures such as `null root node` are retried until the timeout; the last real dump error and UI XML are kept if the wait still fails. With `recover_anr: true`, a visible Android "app is not responding" dialog is handled by tapping its **Wait** action and continuing to poll; the step output records `anr_recoveries`.


### `wait_for_activity`

```yaml
- action: wait_for_activity
  activity: org.videolan.vlc/.gui.video.VideoPlayerActivity
  timeout: 30
  interval: 0.5
```

Polls Android's resumed/top Activity until `package/.Activity` (or a fully qualified component) matches. `timeout` defaults to `30` seconds and `interval` to `0.5`. The step result includes the observed component and current Activity identity. A timeout is a normal step failure with the last observed Activity in the hint, which is useful when a WebView, player, or deep link lands somewhere other than expected.

Activity checks complement UI dumps: they let a flow prove that a native surface transition happened even when that surface exposes little or no text to accessibility services.

### `assert_logcat_contains`

```yaml
- action: assert_logcat_contains
  text: "Creating an input for 'sintel-trailer.mp4'"
  lines: 30000
  ignore_case: true
```

Reads the device log buffer and requires at least one matching line. `lines` defaults to `5000` and accepts up to `100000`. The result records `match_count` and the last matching line; a failure includes the recent log tail.

Use this for assertions that are not visible in the UI hierarchy, such as a media framework opening a file, an audio output module initializing, or an expected SDK transition. Keep the device free of unrelated log-heavy apps when the buffer may roll over during a long wait.

## Report settings

```yaml
report:
  title: Login regression
  capture_screenshots: failures
  collect_logcat: true
  clear_logcat: false
  include_ui_xml: true
  max_log_chars: 200000
```

| Field | Values | Default |
| --- | --- | --- |
| `title` | string | flow name |
| `capture_screenshots` | `all`, `failures`, `manual` | `failures` |
| `collect_logcat` | boolean | `true` |
| `clear_logcat` | boolean | `false` |
| `include_ui_xml` | boolean | `true` |
| `max_log_chars` | integer | `200000` |

`clear_logcat: true` clears the device log buffer after connection and before setup. Use it only when you do not need logs from before the run.

JUnit XML is opt-in on the CLI:

```powershell
app-testbench run flow.yaml --junit-xml .\artifacts\junit.xml
```

The file contains one testcase per setup/step/teardown action, with failed and
skipped actions represented by the standard JUnit elements. The path is also
recorded in `result.json` as `junit_path`.

A failed step always attempts a diagnostic screenshot and a final logcat when possible, subject to device availability. `capture_screenshots: manual` suppresses automatic screenshots but does not prevent an explicit `screenshot` action.

## Execution semantics

1. Load and validate the entire flow.
2. Discover/resolve MuMu instance, ADB serial, and device.
3. If `device.wait_for_boot` or `--wait-for-boot` is enabled, poll `sys.boot_completed` up to `boot_timeout` seconds.
4. Run `setup`.
5. Run `steps` if setup did not fail.
6. Run `teardown` even when setup or steps fail.
7. Collect final logcat.
8. Write `result.json` and `report.html`; write JUnit XML when requested.

If a main step fails and `continue_on_error` is `false`, later main steps are recorded as `skipped`; teardown still runs. If `continue_on_error` is `true`, later steps run, while the overall result remains `failed`.

## Aliases

These aliases are accepted and normalized:

- `dump-ui` → `dump_ui`
- `key-event` → `keyevent`
- `assert-ui-contains` → `assert_ui_contains`
- `assert-ui-not-contains` → `assert_ui_not_contains`
- `wait-for-text` → `wait_for_text`
- `clear-data` → `clear_app_data`
- `reverse-port` → `reverse_port`
- `tap-text` → `tap_text`
- `wait-for-activity` → `wait_for_activity`
- `assert-logcat-contains` → `assert_logcat_contains`
- `clear-text` → `clear_text`

Prefer underscore names in committed examples.

## Full example

```yaml
version: 1
name: search-regression
description: Install, launch, open search, and verify results.
device:
  instance: 0
  package: com.example.app
report:
  capture_screenshots: all
  collect_logcat: true
  clear_logcat: true
setup:
  - name: Install the build under test
    action: install
    apk: ./builds/app-debug.apk
    grant_permissions: true
steps:
  - name: Launch app
    action: launch
  - name: Wait for home
    action: wait_for_text
    text: Home
    timeout: 30
  - name: Open search
    action: tap
    x: 980
    y: 180
  - name: Wait for search field
    action: wait_for_text
    text: Search
    timeout: 10
  - name: Enter query
    action: text
    text: mumu
  - name: Submit
    action: keyevent
    key: ENTER
  - name: Verify results
    action: wait_for_text
    text: Results
    timeout: 20
  - name: Capture results
    action: screenshot
    label: search-results
  - name: Save UI tree
    action: dump_ui
    label: search-results
teardown:
  - name: Close app
    action: close
    continue_on_error: true
  - name: Capture final logcat
    action: logcat
    label: final
    lines: 3000
```

## Validation behavior

`app-testbench validate flow.yaml`:

- parses JSON/YAML with safe loaders
- expands environment variables
- rejects unknown root/device/step/report fields
- validates action-specific types and ranges
- normalizes package names and paths
- does not require the APK to exist yet and does not contact MuMu/ADB

`app-testbench run flow.yaml` performs the same validation, then starts device work.
Use `--wait-for-boot` and `--boot-timeout` to enable the boot gate from the CLI;
`--boot-timeout` implies `--wait-for-boot`.

## Machine-readable contracts

The package ships versioned JSON Schema files for consumers:

- `src/app_testbench/schemas/result-v1.schema.json` validates `result.json`.
- `src/app_testbench/schemas/cli-v1.schema.json` validates the success and error
  envelopes emitted by `--json`.

Both schemas target JSON Schema draft 2020-12. They require the current stable
fields while allowing additive fields for forward-compatible releases.
