# 验证记录 / Validation Record

本页记录 App TestBench v0.1.1 的发布候选验证。结论只适用于下列版本、环境、App 和流程；没有执行过的组合不会被写成“应该可用”。

This page records the v0.1.1 release-candidate validation for App TestBench. Results apply only to the versions, environments, apps, and flows listed below. Untested combinations are not presented as expected to work.

验证日期 / Validation date: **2026-11-16, Asia/Shanghai**

## 1. 发布门禁 / Release gate

| 检查 / Check | 实际结果 / Actual result |
| --- | --- |
| 完整 pytest | **138 passed** |
| Ruff lint | PASS |
| Ruff format check | PASS, 64 files formatted |
| wheel + sdist build | `app_testbench-0.1.1-py3-none-any.whl` and `app_testbench-0.1.1.tar.gz` built |
| `twine check` | wheel and sdist PASSED |
| failed `run --json` | exit `1`, `error.type=step_failure`, complete `data`, packaged `cli-v1.schema.json` PASS |
| result Schema | success and failure `result.json` validated with `result-v1.schema.json` |
| public evidence test | 7 PNG files checked for dimensions, privacy-sensitive metadata chunks, SHA256 manifest coverage, and expected file set |
| AnkiDroid live case | **49 passed / 0 failed / 0 skipped**, 75.203 s |
| Markor live case | **46 passed / 0 failed / 0 skipped**, 80.203 s |
| clean-wheel Markor rerun | **46 passed / 0 failed / 0 skipped**, 82.609 s |
| clean-wheel failure rerun | **3 passed / 1 failed / 1 skipped**, exit `1`, Schema PASS |
| HTML offline check | screenshots embedded as data URIs; no external script, stylesheet, or CSS import |
| JUnit | passed cases and intentional-failure case both parsed with expected counts |

CI uses deterministic fake `adb` / `MuMuManager` backends to verify command construction, flow execution, reporting, and Schemas. It is not a MuMu compatibility proof. The live results below were produced separately on the recorded MuMu instance.

CI 使用确定性的 fake `adb` / `MuMuManager` 验证命令构造、流程执行、报告和 Schema；它不是 MuMu 兼容性证明。下列真实结果均在单独记录的 MuMu 实例上执行。

## 2. 真实验证环境 / Live environment

| Item | Value |
| --- | --- |
| OS | Windows 10.0.26100 |
| Python | 3.11.8 |
| MuMu Player | 6.8.8.0 |
| Android | 12 |
| ADB | 1.0.41 |
| Instance | 0 |
| Display | 720x1280 portrait |
| System language | Simplified Chinese |
| ADB serial | resolved at runtime; not published |
| Artifact policy | APKs, complete run directories, logcat, UI XML, and environments stay under ignored local storage |

## 3. 案例 1：AnkiDroid 牌组、卡片与冷启动持久化 / Deck, card, and cold-start persistence

固定输入 / Pinned input:

```text
Package: com.ichi2.anki
Version: 2.25.3
VersionCode: 225033004
Source: https://f-droid.org/repo/com.ichi2.anki_225033004.apk
SHA256: c7056f611c66fc91a8e290e18268a0d708e813704f51c66e4af1534d468f6790
```

执行结果 / Result:

```text
Status: passed
Steps: 49 passed, 0 failed, 0 skipped
Duration: 75.203 seconds
Screenshots: 8 PNG at 720x1280
HTML: 1,853,536 bytes, self-contained
result.json: 37,973 bytes
JUnit: 14,630 bytes; 49 tests, 0 failures, 0 errors, 0 skipped
```

覆盖链路 / Coverage:

1. Install the pinned APK and verify package, version code, and version name.
2. Reset AnkiDroid app data, its all-files app-op, and only the case-owned external collection path.
3. Complete first-run onboarding and wait for an empty collection.
4. Create the `TestBench` deck through the real Android dialog.
5. Enter `Capital of France` / `Paris` through the real card form.
6. Verify the due-card count before restart.
7. Force-stop and cold-launch AnkiDroid.
8. Verify the deck and due count remain, reopen the card, and assert both saved fields.
9. Retain screenshots, UI trees, logcat, HTML, JSON, and JUnit.

Evidence root (ignored locally): `runs/v0.1.1-final/ankidroid/20261116-134731-ankidroid-deck-persistence/`.

Public evidence:

- [`card-filled.png`](assets/cases/ankidroid/card-filled.png)
- [`persistence.png`](assets/cases/ankidroid/persistence.png)
- [`saved-card.png`](assets/cases/ankidroid/saved-card.png)

## 4. 案例 2：Markor 笔记保存、搜索与冷启动持久化 / Note save, search, and cold-start persistence

固定输入 / Pinned input:

```text
Package: net.gsantner.markor
Version: 2026.10.0
VersionCode: 164
Source: https://f-droid.org/repo/net.gsantner.markor_164.apk
APK size: 11,849,016 bytes
SHA256: c29412e02d03e4f0511746a1bcef48c6b73fc1f70c1024fbf04903b0b3f4c485
Test file: app-testbench-markor.md
Body: App TestBench persistence check
```

首次正式运行 / Original recorded run:

```text
Status: passed
Steps: 46 passed, 0 failed, 0 skipped
Duration: 80.203 seconds
Screenshots: 5 PNG at 720x1280
HTML: 1,086,790 bytes, self-contained
result.json: 37,658 bytes
JUnit: 14,828 bytes; 46 tests, 0 failures, 0 errors, 0 skipped
```

干净 wheel 重跑 / Clean-wheel rerun:

```text
Environment: fresh Python 3.11 venv, installed app_testbench-0.1.1 wheel from the release candidate
Status: passed
Steps: 46 passed, 0 failed, 0 skipped
Duration: 82.609 seconds
Screenshots: 5 PNG at 720x1280
HTML: 1,088,662 bytes, self-contained
result.json: 37,847 bytes
JUnit: 14,828 bytes; 46 tests, 0 failures, 0 errors, 0 skipped
Cleanup: case-owned notes removed and Markor uninstalled by run.ps1
```

覆盖链路 / Coverage:

1. Install and verify the pinned APK.
2. Complete five onboarding pages and close the release-notes dialog using text/content-desc selectors.
3. Create and save a Markdown note.
4. Force-stop and cold-launch Markor.
5. Verify the file remains in the browser.
6. Search by exact filename, reopen the note, and assert the body survived.
7. Retain screenshots, UI trees, logcat, HTML, JSON, and JUnit.

Evidence root (ignored locally): `runs/examples/markor-note-persistence/20261116-143118/artifacts/20261116-143121-markor-note-persistence/`.

Clean-wheel evidence (ignored locally): run ID `20261116-151919-markor-note-persistence`.

Public evidence:

- [`note-persisted.png`](assets/cases/markor/note-persisted.png)
- [`note-search.png`](assets/cases/markor/note-search.png)
- [`note-reopened.png`](assets/cases/markor/note-reopened.png)

## 5. 干净 wheel 安装验证 / Clean wheel verification

A fresh Python 3.11 virtual environment was created under ignored `runs/` storage. The wheel was installed with its declared `PyYAML` dependency, and the CLI was invoked from that environment rather than from the source tree.

在被 `.gitignore` 排除的 `runs/` 下创建全新 Python 3.11 虚拟环境，安装构建出的 wheel 及其声明的 `PyYAML` 依赖，并从该环境调用 CLI，而不是从源码树导入。

| Check | Actual result |
| --- | --- |
| `app-testbench --version` | `app-testbench 0.1.1` |
| `app-testbench doctor --json` | `ok=true`, 9 pass / 0 warn / 0 fail |
| `app-testbench skill-path` | packaged `SKILL.md` found inside the installed wheel |
| `app-testbench init` | generated `app-testbench-flow.yaml` |
| `app-testbench validate` | generated flow validated successfully |
| live flow | Markor 46/46 passed in 82.609 s |
| live failure | exit 1; 3 passed / 1 failed / 1 skipped; packaged CLI Schema PASS |

## 6. 失败 JSON 契约 / Failed JSON contract

Before v0.1.1, the live failed path kept `ok=false` and `data`, but omitted the `error` object required by the published `cli-v1.schema.json`.

v0.1.1 keeps the existing Schema and fixes the producer. The failed output now contains:

```json
{
  "schema_version": "1.0",
  "ok": false,
  "command": "run",
  "error": {
    "type": "step_failure",
    "message": "Flow step '...' failed: ...",
    "hint": "Visible text: ..."
  },
  "data": {
    "status": "failed"
  }
}
```

Clean-wheel live failure result:

```text
Flow: cli-failure-contract-live
Exit code: 1
Summary: 3 passed, 1 failed, 1 skipped
Duration: 8.125 seconds
Packaged cli-v1.schema.json: PASS
Failed step: Wait for a deliberately absent marker
Failure screenshot: present
Failure UI tree: present
Final logcat: present
HTML: 346,216 bytes, self-contained
JUnit: 2,354 bytes; 5 tests, 1 failure, 0 errors, 1 skipped; 8.125 s
```

Regression test: `tests/test_cli.py::test_failed_run_json_matches_cli_schema` validates the failed `run --json` envelope against the packaged Draft 2020-12 Schema. The Schema was not relaxed.

## 7. 公开证据与隐私 / Public evidence and privacy

- Seven public PNG files are committed: three from AnkiDroid, three from Markor, and one redacted failure-report image.
- Each app screenshot comes from a real MuMu run and shows only test-created content.
- The report image was rendered from a temporary copy with local paths and the test serial replaced; the report layout and failed result were not redrawn or fabricated.
- PNG dimensions and SHA256 coverage are enforced by `tests/test_examples.py` and `docs/assets/cases/SHA256SUMS`.
- The test also rejects `tEXt`, `zTXt`, `iTXt`, and `eXIf` metadata chunks in public PNGs.
- APKs/AABs, MP4 files, complete run directories, unfiltered logcat, UI XML, virtual environments, and build outputs remain under ignored local storage.
- The public tree contains no account pages, cookies, tokens, API keys, private IPs, ADB serials, MuMu UUIDs, or local user paths.

## 8. 未覆盖范围 / Not covered

- Not every MuMu Player, Android, ADB, Windows, resolution, language, or physical-device combination was tested.
- Both cases are calibrated for MuMu Player 6.8.8.0, Android 12, 720x1280, Simplified Chinese, and the pinned app builds.
- `text` remains printable-ASCII only; this release does not claim Chinese text input.
- `wait_for_text` depends on `uiautomator dump`; games, custom-rendered surfaces, and incomplete accessibility trees may not expose stable nodes.
- AnkiDroid's web-based card renderer and collection database may change across releases.
- Markor uses one editor-focus coordinate; changing resolution, language, or app build requires recalibration.
- The failure case intentionally launches AnkiDroid and waits for a nonexistent marker. It verifies the failure envelope and retained artifacts, not an app defect.
- The project does not bypass login, CAPTCHA, anti-automation, anti-scraping, risk controls, rate limits, paywalls, or access controls.
- Physical devices remain the final acceptance environment for release-critical mobile behavior.
