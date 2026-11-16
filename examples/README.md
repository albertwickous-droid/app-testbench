# 示例 / Examples

这里只放可复现的真实 MuMu 案例。每个案例都会下载并校验固定开源 APK；APK、原始截图、UI XML、logcat 和完整运行目录都写入被 Git 忽略的 `runs/`。

This directory contains reproducible live MuMu cases only. Each case downloads and verifies a pinned open-source APK. APKs, raw screenshots, UI XML, logcat, and complete run directories stay under ignored `runs/` storage.

## 案例 / Cases

| Case | Product risk covered | Live result |
| --- | --- | --- |
| [`wikipedia-research-session/`](wikipedia-research-session/) | Real network app, first-run onboarding, search, WebView article, saved-item persistence | **63/63 passed** |
| [`firefox-webapp-session/`](firefox-webapp-session/) | Browser Cookie + LocalStorage, scoped login-like state, download, two tabs, cold-start restore | **66/66 passed** |
| [`vlc-media-playback/`](vlc-media-playback/) | Native player Activity, byte-range HTTP media, decoded frames, codec/AudioTrack log assertions, orientation | **43/43 passed** |

```powershell
.\examples\wikipedia-research-session\run.ps1
.\examples\firefox-webapp-session\run.ps1
.\examples\vlc-media-playback\run.ps1
```

Each wrapper verifies the pinned APK before installing it, prints `doctor --json`, runs the flow with JUnit output, and keeps the generated evidence under `runs/`. Firefox additionally removes and verifies its own unique download file. VLC validates a byte-range server and removes its reverse-port mapping.

All public app screenshots come from these live runs. No generated or redrawn app pages are used. See [`../docs/cases.md`](../docs/cases.md) for screenshots, exact versions, observed results, evidence boundaries, and known limits.
