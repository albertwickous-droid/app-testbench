# Firefox WebApp session / Firefox 浏览器状态、下载与标签页

A browser-level live case for Fennec F-Droid. It uses a local, deterministic QA fixture with no password field, production credential, or external business endpoint.

这是 Fennec F-Droid 的浏览器级真实案例。测试站点是本地确定性 fixture，没有密码字段、生产凭据或外部业务接口。

## Why this app / 为什么选它

- Fennec F-Droid is a mature Firefox build with a reproducible public APK.
- It exercises browser behavior that a native-only UI test cannot cover: Cookie and LocalStorage, a scoped signed-in state, file download, two tabs, tab switching, force-stop, and restore.
- The fixture contains a synthetic username only. No password, real session, token, API key, or production user data is used.
- It models the legitimate case where an authorized browser or App-only workflow must be validated in a controlled Android environment.

## Pinned input / 固定输入

| Field | Value |
| --- | --- |
| Package | `org.mozilla.fennec_fdroid` |
| Version | `160.0.0` |
| Version code | `1600020` |
| APK source | <https://f-droid.org/repo/org.mozilla.fennec_fdroid_1600020.apk> |
| APK size | `129,815,928` bytes |
| APK SHA256 | `43cf491bbc677244d7b56ba2e8ae20ccd802c9d8f6b44d6b6aff7eb1753eab1b` |
| Local fixture | `site/` served on `127.0.0.1:18765` through `adb reverse` |
| Synthetic identity | `qa-runner` |
| Download file | `app-testbench-browser-evidence.txt` |

## Run / 运行

```powershell
.\examples\firefox-webapp-session\run.ps1
```

The wrapper downloads and verifies the pinned APK, starts a local HTTP server, runs `doctor --json`, removes the previous case-owned download file, executes the 66-action flow with JUnit, then reads the downloaded file through ADB and verifies its exact contents.

脚本会下载并校验固定 APK、启动本地 HTTP 服务、运行 `doctor --json`、删除上一次案例专属下载文件、执行 66 步 flow，然后通过 ADB 读取新下载文件并核对完整内容。

## What the live flow proves / 实际覆盖

1. Completes Firefox/Fennec first-run onboarding and declines the default-browser change.
2. Opens the local QA portal through an explicit `open` intent.
3. Creates a synthetic signed-in state without a password field.
4. Asserts `Cookie + Local Storage` on the dashboard and order page.
5. Downloads a case-owned text file and verifies its content outside the browser.
6. Opens a second tab, switches tabs, and captures the tab manager.
7. Force-stops and cold-launches the browser.
8. Verifies the signed-in state and two-tab restore.
9. Retains screenshots, UI trees, logcat, HTML, `result.json`, and JUnit.

Recorded result: see `docs/validation.md`; the committed release uses the final clean run only.

## Expected evidence / 预期证据

- `report.html` and `result.json` for the browser flow.
- `browser-download-verification.txt` written by the wrapper after exact content verification.
- real screenshots for onboarding, local portal, signed-in state, orders, download prompt, tab manager, and restored session.
- UI XML and logcat under the ignored run directory.

## Known limits / 已知限制

- Browser prompts, keyboard geometry, and tab UI are calibrated for the pinned Fennec build, Simplified Chinese system UI, and `720x1280`.
- The fixture tests browser storage and navigation mechanics. It does not test a production identity provider.
- The test does not export cookies or tokens; it only asserts visible state and server-side-like behavior inside the isolated browser.
- A cold-start pass depends on Firefox's own session-restore behavior for this build.
- Use this case only against systems and accounts you are authorized to test.

## Cleanup / 清理

The flow force-stops Fennec and removes the reverse-port mapping. The wrapper removes only `/sdcard/Download/app-testbench-browser-evidence.txt` before the run. The bundled local server is stopped by the wrapper. On a dedicated test instance:

```powershell
app-testbench reverse-port 18765 --remove --json
app-testbench close org.mozilla.fennec_fdroid
app-testbench clear-data org.mozilla.fennec_fdroid
app-testbench uninstall org.mozilla.fennec_fdroid
```
