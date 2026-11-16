# 验证记录 / Validation Record

本页记录 App TestBench v0.1.1 的发布验证。结果只适用于下列版本、环境、App 和 flow；未执行的组合不会被写成“应该可用”。

This page records the v0.1.1 release validation for App TestBench. Results apply only to the versions, environments, apps, and flows listed below. Untested combinations are not presented as expected to work.

验证日期 / Validation date: **2026-11-16, Asia/Shanghai**

## 1. 发布门禁 / Release gate

| 检查 / Check | 实际结果 / Actual result |
| --- | --- |
| 完整 pytest | **145 passed** |
| Ruff lint | PASS |
| Ruff format check | PASS, 65 files formatted |
| wheel + sdist build | wheel and sdist built in an isolated PEP 517 environment |
| `twine check` | wheel and sdist PASSED |
| wheel contents | required Schema and `SKILL.md` present; no APK/MP4/runs/logs |
| Wikipedia live case | **63 passed / 0 failed / 0 skipped**, 113.563 s |
| Firefox/Fennec live case | **66 passed / 0 failed / 0 skipped**, 143.016 s |
| VLC live case | **43 passed / 0 failed / 0 skipped**, 50.579 s |
| clean-wheel VLC rerun | **43 passed / 0 failed / 0 skipped**, 44.625 s |
| failed `run --json` | exit `1`, `error.type=step_failure`, complete `data`, packaged Schema PASS |
| HTML offline audit | no external resource loads; screenshots embedded as data URIs |
| JUnit audit | passing and failing runs parsed with expected counts |
| public evidence | 12 PNG files checked for dimensions, metadata, and SHA256 manifest coverage |
| privacy audit | no local paths, user paths, MuMu install paths, serials, proxies, secrets, or forbidden binaries found |

Local wheel and sdist artifacts were built under ignored storage and checked with `twine check`. The GitHub Release workflow will attach the release builds and a generated `SHA256SUMS.txt`; those assets are verified after publication rather than embedding self-referential sdist hashes in the repository.

CI uses deterministic fake ADB/MuMuManager backends to verify command construction, flow execution, reporting, and Schemas. It is not a MuMu compatibility proof. The live results below were produced separately on the recorded MuMu instance.

## 2. 真实验证环境 / Live environment

| Item | Value |
| --- | --- |
| OS | Windows 10.0.26100 |
| Python | 3.11.8 |
| MuMu Player | 6.8.8.0 |
| Android | 12 |
| ADB | 1.0.41 |
| Display | 720x1280 portrait; VLC also checks 1280x720 landscape |
| System language | Simplified Chinese |
| ADB serial | resolved at runtime; not published |
| Artifact policy | APKs, MP4 files, complete run directories, logcat, UI XML, and environments stay under ignored local storage |

## 3. 真实案例 / Live cases

### Wikipedia

```text
Package: org.wikipedia
Version: r/50616-r-2026-11-03
VersionCode: 50616
SHA256: d225e5d08fe461f12fa0af7b617e6e715f3112986165c34e0572a1a056129dd1
Result: 63 passed, 0 failed, 0 skipped
Duration: 113.563 seconds
```

Coverage: onboarding, privacy/language/interest pages, live home feed, English search, WebView article, `QA Reading List`, force-stop, cold launch, and saved-item persistence.

Run ID: `20261116-171723-wikipedia-research-session`

Public evidence:

- [`search-results.png`](assets/cases/wikipedia/search-results.png)
- [`article.png`](assets/cases/wikipedia/article.png)
- [`persisted.png`](assets/cases/wikipedia/persisted.png)

### Firefox / Fennec

```text
Package: org.mozilla.fennec_fdroid
Version: 160.0.0
VersionCode: 1600020
SHA256: 43cf491bbc677244d7b56ba2e8ae20ccd802c9d8f6b44d6b6aff7eb1753eab1b
Result: 66 passed, 0 failed, 0 skipped
Duration: 143.016 seconds
```

Coverage: first-run onboarding, local QA fixture, Cookie + LocalStorage, orders page, unique file download with exact ADB-side content verification, two tabs, force-stop, and session/tab restore.

Run ID: `20261116-175711-firefox-webapp-session`

Public evidence:

- [`session.png`](assets/cases/firefox/session.png)
- [`orders.png`](assets/cases/firefox/orders.png)
- [`tabs.png`](assets/cases/firefox/tabs.png)
- [`download.png`](assets/cases/firefox/download.png)

### VLC

```text
Package: org.videolan.vlc
Version: 3.7.2
VersionCode: 13070208
APK SHA256: 727693d59c4d678c046386812a103209a25423460c9d22e38e12460f12402ab6
Media SHA256: b670602fa00934ca27c4351bb0efe7ea7a07fae57284e44226025eeed7c51254
Result: 43 passed, 0 failed, 0 skipped
Duration: 50.579 seconds
```

Coverage: real MP4 over byte-range HTTP, `VideoPlayerActivity`, first-play tutorial, decoded frame, title assertion, media-input log, `android_audiotrack` log, portrait/landscape checks.

Run ID: `20261116-174654-vlc-media-playback`

Public evidence:

- [`tutorial.png`](assets/cases/vlc/tutorial.png)
- [`player-controls.png`](assets/cases/vlc/player-controls.png)
- [`landscape.png`](assets/cases/vlc/landscape.png)
- [`resumed.png`](assets/cases/vlc/resumed.png)

## 4. 干净 wheel 安装验证 / Clean wheel verification

A fresh Python 3.11 virtual environment was created under ignored `runs/` storage. The wheel was installed with its declared `PyYAML` dependency, and every command below was invoked from the installed package rather than the source tree.

| Check | Actual result |
| --- | --- |
| `app-testbench --version` | `app-testbench 0.1.1` |
| `app-testbench doctor --json` | `ok=true`, 9 pass / 0 warn / 0 fail |
| `app-testbench skill-path` | packaged `SKILL.md` found inside the installed wheel |
| `app-testbench init` | generated `app-testbench-flow.yaml` |
| `app-testbench validate` | generated flow validated successfully |
| live VLC flow | 43/43 passed in 44.625 s |
| HTML/JUnit after clean install | self-contained HTML and 43 passing JUnit testcases verified |

## 5. 失败 JSON 契约 / Failed JSON contract

Before v0.1.1, the live failed path kept `ok=false` and `data`, but omitted the `error` object required by the published `cli-v1.schema.json`.

v0.1.1 keeps the Schema unchanged and fixes the producer. The final clean-wheel failure run produced:

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

Observed failure run:

```text
Exit code: 1
Summary: 4 passed, 1 failed, 0 skipped
Duration: 8.765 seconds
Packaged cli-v1.schema.json: PASS
Packaged result-v1.schema.json: PASS
Failure screenshot: present
Failure UI tree: present
Final logcat: present
HTML: 623,807 bytes, self-contained
JUnit: 5 tests, 1 failure, 0 errors, 0 skipped
```

Regression tests include `tests/test_cli.py::test_failed_run_json_matches_cli_schema`, which validates the failed envelope against the packaged Draft 2020-12 Schema.

## 6. 公开证据与隐私 / Public evidence and privacy

- Twelve public PNG files are committed: Wikipedia (3), Firefox/Fennec (4), VLC (4), and the redacted failure-report image (1).
- Every app screenshot comes from a real MuMu run and shows only test-created content or a local test fixture.
- The failure-report image was rendered from a temporary redacted report copy; local paths and the test serial were replaced before rendering.
- PNG files have no `tEXt`, `zTXt`, `iTXt`, `eXIf`, or `caBX` chunks.
- `tests/test_examples.py` enforces dimensions, the expected file set, metadata rejection, and SHA256 manifest coverage.
- APKs, MP4 files, complete run directories, unfiltered logcat, UI XML, virtual environments, and build outputs remain under ignored local storage.
- The public tree contains no account secrets, cookies, tokens, API keys, private keys, private IPs, ADB serials, proxy settings, local usernames, or MuMu installation paths.
- Deterministic fixture values `127.0.0.1:5555`, `127.0.0.1:16416`, `127.0.0.1:18765`, and `127.0.0.1:18766` are test-only and contain no host identity.

## 7. 未覆盖范围 / Not covered

- Not every MuMu Player, Android, ADB, Windows, resolution, language, or physical-device combination was tested.
- The live cases are calibrated for MuMu Player 6.8.8.0, Android 12, 720x1280, Simplified Chinese, and the pinned app builds.
- Wikipedia depends on live MediaWiki content and network availability.
- The Firefox fixture validates browser state mechanics, not a production identity provider.
- VLC logcat assertions use a bounded Android log buffer and stop unrelated log-heavy browser processes in setup.
- `text` remains printable ASCII only; Chinese input is not claimed.
- `wait_for_text` depends on `uiautomator dump`; games, custom-rendered surfaces, and incomplete accessibility trees may need another approach.
- The project does not provide or support bypassing login, CAPTCHA, anti-automation, anti-scraping, risk controls, rate limits, paywalls, or access controls.
- Physical devices remain the final acceptance environment for hardware, OEM, and production-account behavior.
