# 验证记录 / Validation Record

本页记录 App TestBench v0.1.1 发布候选在真实 MuMu、干净 wheel 环境及确定性测试后端上的验证结果。结论只适用于下文列出的版本、环境和案例；未执行的项目不会被写成“应该可用”。

This page records App TestBench v0.1.1 release-candidate validation on a live MuMu instance, in a clean wheel environment, and with deterministic test backends. Results apply only to the versions, environments, and cases listed below. A check that was not run is not presented as expected to work.

## 验证日期 / Date

2026-11-16（Asia/Shanghai）

## 发布门禁 / Release gate

| 检查 / Check | 实际结果 / Actual result |
| --- | --- |
| 完整 pytest | **132 passed** |
| Ruff lint | passed |
| Ruff format check | 64 files already formatted |
| wheel + sdist build | `app_testbench-0.1.1-py3-none-any.whl` and `app_testbench-0.1.1.tar.gz` built |
| `twine check` | wheel and sdist PASSED |
| packaged JSON Schemas | success and failure results validated against `result-v1.schema.json`; failed CLI output validated against packaged `cli-v1.schema.json` |
| public evidence test | 12 PNG files checked for expected dimensions and SHA256 manifest coverage |
| self-contained HTML check | success and failure reports contain embedded PNG data and no external resource elements (`img src`, script `src`, stylesheet `href`, or CSS imports); captured command/log text may still contain a local media URL |

CI uses deterministic fake `adb` and `MuMuManager` backends for command construction, flow execution, reports, and Schema coverage. CI results are not presented as proof of MuMu compatibility. The live cases below were executed separately on MuMu.

CI 使用确定性的假 `adb` / `MuMuManager` 后端验证命令构造、流程、报告和 Schema；它不冒充 MuMu 兼容性证明。下文真实案例均另行在 MuMu 上执行。

## 干净 wheel 安装 / Clean wheel installation

A fresh Python 3.11 virtual environment was created under ignored run storage and executed from that directory so imports came from the installed wheel, not the source tree. It installed the built wheel plus its declared `PyYAML` dependency, then used that wheel for CLI checks, a live VLC flow, and a live intentional-failure flow.

在被 `.gitignore` 排除的运行目录下创建全新的 Python 3.11 虚拟环境，并从该目录执行，确保导入来自已安装 wheel 而不是源码树；仅安装构建出的 wheel 及其声明的 `PyYAML` 依赖，然后用该 wheel 执行 CLI 检查、真实 VLC 流程和真实失败契约流程。

| 检查 / Check | 实际结果 / Actual result |
| --- | --- |
| `app-testbench --version` | `app-testbench 0.1.1` |
| `app-testbench doctor --json` | `ok=true`; 9 pass / 0 warn / 0 fail |
| `app-testbench skill-path` | packaged skill file found |
| `app-testbench init` | generated `app-testbench-flow.yaml` |
| `app-testbench validate` | generated flow and the VLC case flow passed |
| live wheel flow | VLC HTTP playback: **30/30 passed** |
| live wheel failure contract | exit code `1`, packaged CLI Schema PASS |
| final candidate wheel rerun | VLC `30/30` in 38.812 s; intentional failure `3 passed / 1 failed / 1 skipped`, exit `1`, packaged CLI Schema PASS |

## 真实 MuMu 环境 / Live MuMu environment

| 项目 / Item | 环境 / Environment |
| --- | --- |
| 操作系统 / OS | Windows 10.0.26100 |
| Python | 3.11.8 |
| MuMu Player | 6.8.8.0 |
| Android | 12 |
| ADB | 1.0.41 |
| MuMu instance | 0 |
| ADB serial | resolved by MuMuManager; not published |
| Display | 1280×720 |
| System language | Simplified Chinese |

## 案例 1：Fennec 本地 Web 会话 / Fennec local web session

固定 APK / Pinned APK:

```text
Package: org.mozilla.fennec_fdroid
Version: 160.0.0
VersionCode: 1600020
Source: official F-Droid repository
APK SHA256: 43cf491bbc677244d7b56ba2e8ae20ccd802c9d8f6b44d6b6aff7eb1753eab1b
```

执行结果 / Result:

```text
Flow status: passed
Steps: 71 passed, 0 failed, 0 skipped
Duration: 99.141 seconds
Screenshots: 11 PNG, each 720x1280
UI trees: 20 XML files
Report: 2,616,192 bytes, self-contained
JUnit: 71 tests, 0 failures, 0 errors
```

覆盖链路 / Coverage:

1. Expose a deterministic local QA site through `adb reverse` and verify its page marker before the run.
2. Install the pinned Fennec build and verify package identity.
3. Clear app state and complete first-run privacy/onboarding screens.
4. Complete the login form and verify a persisted session.
5. Exercise the translation prompt and dismiss the default-browser prompt.
6. Run an asynchronous search, wait for the result, and open a detail record.
7. Capture screenshots and UI trees at meaningful states.
8. Force-stop and cold-start the browser.
9. Verify the authenticated session and previous query are restored from `localStorage`.
10. Log out, verify the logged-out state, and collect logcat, JSON, HTML, and JUnit.

公开证据 / Public evidence:

- [`docs/cases.md`](cases.md)
- [`examples/fennec-local-web-session/`](../examples/fennec-local-web-session/)
- [`docs/assets/cases/fennec/`](assets/cases/fennec/)

原始截图、完整 UI XML、日志和运行目录保留在被 `.gitignore` 排除的本地 `runs/` 中，未提交。公开图片来自真实运行，只做了必要的裁剪、压缩和敏感字段处理。

The raw screenshots, complete UI XML, logs, and run directory remain under the ignored local `runs/` tree and are not committed. Public images come from the live run and were only cropped, compressed, or redacted where necessary.

## 案例 2：VLC HTTP 播放 / VLC HTTP playback

固定资产 / Pinned assets:

```text
Package: org.videolan.vlc
Version: 3.7.2
VersionCode: 13070208
Source: official F-Droid repository
APK SHA256: 727693d59c4d678c046386812a103209a25423460c9d22e38e12460f12402ab6

Media: Sintel trailer, non-DRM H.264/AAC
Media SHA256: b670602fa00934ca27c4351bb0efe7ea7a07fae57284e44226025eeed7c51254
```

执行结果 / Result:

```text
Flow status: passed
Steps: 30 passed, 0 failed, 0 skipped
Duration: 36.891 seconds in the clean-wheel run
Screenshots: 5 PNG, each 1280x720
Report: 1,708,158 bytes, self-contained
JUnit: 30 tests, 0 failures, 0 errors
```

覆盖链路 / Coverage:

1. Start a local HTTP range server for a pinned media file and verify a `206 Partial Content` response with the expected `Content-Range`.
2. Install the pinned VLC build and verify package identity.
3. Expose the media server through `adb reverse`.
4. Complete first-run/welcome screens and the playback tutorial.
5. Enter landscape mode and open the HTTP media URL.
6. Wait for real playback state rather than a fixed sleep.
7. Capture playback screenshots and controls.
8. Collect logcat and verify `MediaCodec`, an H.264 decoder, AAC audio, demuxing, and HTTP requests.
9. Close VLC and retain JSON, HTML, and JUnit evidence.

公开证据 / Public evidence:

- [`docs/cases.md`](cases.md)
- [`examples/vlc-http-playback/`](../examples/vlc-http-playback/)
- [`docs/assets/cases/vlc/`](assets/cases/vlc/)

原始 APK、MP4、完整 logcat、UI XML 和运行目录未提交。公开截图来自真实 MuMu 播放阶段，不是 AI 生成或手绘模拟。

The raw APK, MP4, complete logcat, UI XML, and run directory are not committed. Public screenshots come from the live MuMu playback stage and are not AI-generated or hand-drawn mockups.

## 失败 JSON 契约 / Failed JSON contract

### v0.1.0 的问题 / v0.1.0 problem

The real v0.1.0 failure output had this shape:

```json
{
  "ok": false,
  "data": {
    "status": "failed"
  }
}
```

The process exited with code `1`, but the published `cli-v1.schema.json` requires an `error` object when `ok=false`. The envelope was therefore invalid against the project's own public contract. Schema validation was not hidden or skipped.

退出码为 `1`，但公开的 `cli-v1.schema.json` 要求 `ok=false` 时包含 `error` 对象，因此旧 envelope 不满足项目自己的公开契约；没有通过跳过 Schema 校验来掩盖问题。

### v0.1.1 的修复 / v0.1.1 fix

The failed CLI output now keeps the complete `data` payload and adds a structured error:

失败时的 CLI 输出现在保留完整 `data`，并增加结构化 `error`：

```json
{
  "ok": false,
  "error": {
    "type": "step_failure",
    "message": "UI text was not found within 3s: __APP_TESTBENCH_EXPECTED_FAILURE_0_1_1__",
    "hint": "Visible text: ..."
  },
  "data": {
    "status": "failed"
  }
}
```

真实失败运行结果 / Live failure-run result:

```text
Flow: cli-failure-contract-live
Exit code: 1
Packaged cli-v1.schema.json: PASS
result-v1.schema.json: PASS
Envelope: ok=false + error.type=step_failure + complete data
Steps: 3 passed, 1 failed, 1 skipped
Duration: 12.859 seconds
Failure screenshot: present
Failure UI tree: present
Final logcat: present
HTML report: 373,659 bytes, self-contained
JUnit: 5 tests, 1 failure, 0 errors, 1 skipped
```

回归测试 `tests/test_cli.py::test_failed_run_json_matches_cli_schema` 执行真实失败路径，并用打包后的 `cli-v1.schema.json` 校验 `main([...])` 输出。Schema 未被放宽。

The regression test `tests/test_cli.py::test_failed_run_json_matches_cli_schema` executes the failure path and validates `main([...])` output against the packaged `cli-v1.schema.json`. The Schema was not relaxed.

公开证据 / Public evidence:

- [`docs/assets/cases/evidence/report-failed.png`](assets/cases/evidence/report-failed.png)
- [`docs/cases.md`](cases.md)

## HTML、截图与校验和 / HTML, screenshots, and checksums

- 成功和失败 HTML 均可离线打开。
- 截图以 `data:image/png;base64,...` 嵌入，不依赖 CDN。
- 检测到的外部 script、stylesheet、CSS import 和 HTTP(S) 依赖数量均为 0。
- 12 张公开 PNG 已由 `tests/test_examples.py` 检查尺寸，并与 [`docs/assets/cases/SHA256SUMS`](assets/cases/SHA256SUMS) 中的 SHA256 对应。
- 公开截图来自真实 MuMu 运行。报告公开图在截图前只替换了本机路径和测试 serial，没有重绘页面，也没有伪造通过/失败结果。
- 原始 APK/AAB、MP4、完整运行目录、原始 logcat、UI XML 和未筛选报告保留在被 `.gitignore` 排除的本地 `runs/` 中。

- Passed and failed HTML reports open offline.
- Screenshots are embedded as `data:image/png;base64,...`; the reports do not depend on a CDN.
- Detected external script, stylesheet, CSS-import, and HTTP(S) dependency counts are all zero.
- `tests/test_examples.py` checks the dimensions of all 12 public PNG files and matches them to [`docs/assets/cases/SHA256SUMS`](assets/cases/SHA256SUMS).
- Public screenshots come from live MuMu runs. Before rendering public report images, only local paths and the test serial were replaced; pages were not redrawn and outcomes were not fabricated.
- Raw APK/AAB files, MP4 media, complete run directories, raw logcat, UI XML, and unselected reports remain under the ignored local `runs/` tree.

## 未覆盖范围 / Not covered

- Not every MuMu Player, Android, ADB, Windows, display, language, or physical-device combination was tested.
- Fennec is validated against a deterministic local HTTP QA site. Public internet variability, production authentication providers, TLS interception, SSO, and anti-automation systems are not covered.
- VLC is validated with a non-DRM H.264/AAC file over local HTTP Range. DRM, adaptive bitrate streaming, subtitles, and audio-track switching are not covered.
- Coordinates, tutorial text, and some UI labels depend on the recorded 1280×720 Android 12 Simplified Chinese image.
- `text` remains printable-ASCII only.
- No OCR or image-template matching is provided; WebViews, games, canvas-based surfaces, and custom-rendered UI may not expose stable nodes in the UI hierarchy.
- While video is active, `uiautomator dump` may be unstable on a Surface; the VLC case uses screenshots and logcat for the playback stage.
- Physical devices remain the final acceptance environment for release-critical mobile behavior.

- 没有验证所有 MuMu Player、Android、ADB、Windows、分辨率、语言或物理设备组合。
- Fennec 只验证了确定性的本地 HTTP QA 站点；公网波动、生产身份认证、TLS 拦截、SSO 和反自动化系统不在本案例范围内。
- VLC 只验证了本地 HTTP Range 上的非 DRM H.264/AAC 文件；DRM、自适应码率、字幕和音轨切换不在本案例范围内。
- 部分坐标、教程文本和 UI 标签依赖已记录的 1280×720、Android 12、简体中文镜像。
- `text` 仍只支持可打印 ASCII。
- 没有 OCR 或图像模板匹配；WebView、游戏、Canvas 和自绘界面可能无法通过 UI 树稳定定位。
- 视频活跃期间 `uiautomator dump` 在 Surface 上可能不稳定；VLC 播放阶段以截图和 logcat 为主要证据。
- 对发布关键的移动端行为，物理设备仍是最终验收环境。