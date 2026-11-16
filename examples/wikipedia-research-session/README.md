# Wikipedia research session / Wikipedia 搜索与收藏持久化

A multi-step live case for the Android Wikipedia app. It uses a public F-Droid build, needs no account, and exercises a real network-backed app rather than a local demo page.

这是 Android Wikipedia 的真实多步案例。使用公开 F-Droid 构建，不需要账号，覆盖真实的网络 App、首次引导、搜索、文章 WebView、收藏和冷启动恢复。

## Why this app / 为什么选它

- Wikipedia is mature, widely used, and available as an immutable F-Droid build.
- The flow exercises a real MediaWiki search and article render, not fixture-only text.
- It combines first-run UI, a language switch, a dynamically loaded result, a WebView article, local reading-list state, force-stop, and cold-start persistence.
- No production account or private data is required.

## Pinned input / 固定输入

| Field | Value |
| --- | --- |
| Package | `org.wikipedia` |
| Version | `r/50616-r-2026-11-03` |
| Version code | `50616` |
| APK source | <https://f-droid.org/repo/org.wikipedia_50616.apk> |
| APK size | `104,747,428` bytes |
| APK SHA256 | `d225e5d08fe461f12fa0af7b617e6e715f3112986165c34e0572a1a056129dd1` |
| Test data | Search `Ada Lovelace`; create `QA Reading List` |

## Run / 运行

```powershell
.\examples\wikipedia-research-session\run.ps1
```

The first run downloads the APK into ignored `runs/case-assets/wikipedia/` and verifies size plus SHA256. Use `-SkipPrepare` only when that verified asset already exists. The wrapper exports `WIKIPEDIA_APK`, runs `doctor --json`, executes the 63-action flow with JUnit, and writes all artifacts under `runs/examples/wikipedia-research-session/` by default.

首次运行会下载 APK 到被忽略的 `runs/case-assets/wikipedia/`，并校验大小与 SHA256。只有在资产已经存在且已验证时才使用 `-SkipPrepare`。默认运行产物写入 `runs/examples/wikipedia-research-session/`。

## What the live flow proves / 实际覆盖

1. Installs and verifies package, version code, and version name.
2. Clears only the app state used by this case.
3. Completes onboarding, privacy, language selection, and optional-interest steps.
4. Waits for the live home feed, opens search, and enters `Ada Lovelace`.
5. Switches to English results and waits for the exact article description.
6. Opens the article, waits for the WebView rendering, and saves it to a new `QA Reading List`.
7. Force-stops the app, cold-launches it, and reopens saved items.
8. Asserts that the article and description survived the cold start.
9. Retains screenshots, UI trees, logcat, HTML, `result.json`, and JUnit.

Recorded result on 2026-11-16: **63 passed, 0 failed, 0 skipped, 113.563 seconds**.

## Expected evidence / 预期证据

- `report.html`: self-contained report with embedded screenshots and logs.
- `result.json`: all 63 steps, timings, status, and artifact paths.
- `screenshots/`: real onboarding, home, search, article, save sheet, saved list, and persisted list.
- `ui/`: selected UI XML dumps for search, article, saved list, and cold-start verification.
- `logs/`: selected and final logcat.
- JUnit: one testcase per action.

## Known limits / 已知限制

- The flow is calibrated for the pinned Wikipedia build, Simplified Chinese system UI, `720x1280`, and a working MuMu network connection.
- Search results come from the live MediaWiki service. A network outage, service change, or result-order change can invalidate dynamic selectors.
- The public case does not use an account and does not claim cross-device Wikipedia sync.
- The article body is a WebView. It is verified through visible text and screenshot evidence, not DOM access.
- Recalibrate selectors after changing the APK version, Android image, density, or language.

## Cleanup / 清理

The flow force-stops Wikipedia and resets orientation in teardown. The app and the case-owned reading list remain installed for inspection. On a dedicated test instance:

```powershell
app-testbench close org.wikipedia
app-testbench clear-data org.wikipedia
app-testbench uninstall org.wikipedia
```

Do not run cleanup on a shared instance that contains data you need.
