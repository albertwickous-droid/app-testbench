# 验证记录 / Validation Record

本页记录 App TestBench 当前 `main` 分支的维护验证。结论只适用于下列版本、环境、App 和流程；未执行过的组合不会被写成“应该可用”。

This page records the maintenance validation for the App TestBench `main` branch. Results apply only to the versions, environments, apps, and flows listed below. Untested combinations are not presented as expected to work.

验证日期 / Validation date: **2026-11-18, Asia/Shanghai**

> Package version remains `0.1.1`. This maintenance update does not create a tag, move `v0.1.1`, publish a GitHub Release, or publish to PyPI.

## 1. 发布门禁 / Release gate

| 检查 / Check | 实际结果 / Actual result |
| --- | --- |
| Full pytest | **148 passed** |
| Ruff lint | PASS |
| Ruff format check | PASS |
| wheel + sdist build | `app_testbench-0.1.1-py3-none-any.whl` and `app_testbench-0.1.1.tar.gz` built |
| `twine check` | wheel and sdist PASSED |
| failed `run --json` | exit `1`, structured `error`, complete `data`, packaged schema PASS |
| public evidence test | 18 PNG files checked for dimensions, privacy-sensitive metadata chunks, SHA256 manifest coverage, and expected file set |
| HTML offline check | screenshots embedded as data URIs; no external script, stylesheet, or CSS import |
| HTML themes | Light / Dark controls and independently scrollable desktop step rail verified in the generated report |

CI uses deterministic fake `adb` / `MuMuManager` backends to verify command construction, flow execution, reporting, and schemas. It is not a MuMu compatibility proof. The live results below were produced separately on the recorded MuMu instance.

## 2. 真实验证环境 / Live environment

| Item | Value |
| --- | --- |
| OS | Windows 10.0.26100 |
| Python | 3.11.8 |
| MuMu Player | 6.8.8.0 |
| Android | 12 |
| ADB | 1.0.41 |
| Instance | 0 |
| Display | 720x1280 portrait unless a case records landscape |
| System language | Simplified Chinese |
| ADB serial | resolved at runtime; not published |
| Artifact policy | APKs, complete run directories, logcat, UI XML, and environments stay under ignored local storage |

## 3. 五个真实案例 / Five live cases

| Case | Result | Duration | Evidence |
| --- | --- | --- | --- |
| Wikipedia | **63 passed / 0 failed / 0 skipped** | 113.563 s | 3 public PNGs; live search, article WebView, saved-item persistence |
| Firefox/Fennec | **66 passed / 0 failed / 0 skipped** | 143.016 s | 4 public PNGs; Cookie + LocalStorage, download, tabs, cold-start restore |
| VLC | **43 passed / 0 failed / 0 skipped** | 50.579 s | 4 public PNGs; player Activity, byte-range MP4, decoded frames, logcat, orientation |
| AnkiDroid | **49 passed / 0 failed / 0 skipped** | 75.203 s | 3 public PNGs; onboarding, deck/card creation, cold launch, reopened fields |
| Markor | **46 passed / 0 failed / 0 skipped** | 80.203 s | 3 public PNGs; note input, save, exact search, cold-start body recovery |

The published `v0.1.1` tag introduced the Wikipedia, Firefox/Fennec, and VLC cases. AnkiDroid and Markor were merged later into `main` and are part of this unversioned maintenance update.

## 4. 失败 JSON 契约 / Failed JSON contract

The failed `run --json` producer keeps the packaged Draft 2020-12 schema unchanged:

```json
{
  "schema_version": "1.0",
  "ok": false,
  "command": "run",
  "error": {
    "type": "step_failure",
    "message": "Flow step 'deliberate-failure' failed: ..."
  },
  "data": {
    "status": "failed"
  }
}
```

Observed behavior:

```text
Exit code: 1
Failure step: present
Failure screenshot: present
Failure UI tree: present
Final logcat: present
HTML: present and self-contained
JUnit: failure represented
Packaged cli-v1.schema.json: PASS
Packaged result-v1.schema.json: PASS
```

## 5. 公开证据与隐私 / Public evidence and privacy

- Eighteen public PNG files are committed: Wikipedia 3, Firefox/Fennec 4, VLC 4, AnkiDroid 3, Markor 3, and the redacted failure report 1.
- Every app screenshot comes from a real MuMu run and shows only test-created content or a local test fixture.
- The failure-report image was rendered from a temporary redacted report copy; local paths and the test serial were replaced before rendering.
- PNG files have no `tEXt`, `zTXt`, `iTXt`, `eXIf`, or `caBX` chunks.
- `tests/test_examples.py` enforces the expected file set, dimensions, metadata rejection, and SHA256 manifest coverage.
- APKs, MP4 files, complete run directories, unfiltered logcat, UI XML, virtual environments, and build outputs remain under ignored local storage.
- The public tree contains no account secrets, cookies, tokens, API keys, private keys, private IPs, ADB serials, proxy settings, local usernames, or MuMu installation paths.
- Deterministic fixture values such as `127.0.0.1:5555`, `127.0.0.1:18765`, `127.0.0.1:18766`, and the synthetic identity `qa-runner` are test-only.

## 6. 未覆盖范围 / Not covered

- Not every MuMu Player, Android, ADB, Windows, resolution, language, or physical-device combination was tested.
- The live cases are calibrated for MuMu Player 6.8.8.0, Android 12, 720x1280, Simplified Chinese, and the pinned app builds.
- Wikipedia depends on live MediaWiki content and network availability.
- The Firefox fixture validates browser state mechanics, not a production identity provider.
- VLC logcat assertions use a bounded Android log buffer and stop unrelated log-heavy browser processes in setup.
- `text` remains printable ASCII only; Chinese input is not claimed.
- `wait_for_text` depends on `uiautomator dump`; games, custom-rendered surfaces, and incomplete accessibility trees may need another approach.
- The project does not support bypassing login, CAPTCHA, anti-automation, anti-scraping, risk controls, rate limits, paywalls, or access controls.
- Physical devices remain the final acceptance environment for hardware, OEM, and production-account behavior.
