# 示例 / Examples

这里只放可复现的真实 MuMu 案例。每个案例都会下载并校验固定开源 APK；APK、原始截图、UI XML、logcat 和完整运行目录都写入被 Git 忽略的 `runs/`。

This directory contains reproducible live MuMu cases only. Each case downloads and verifies a pinned open-source APK. APKs, raw screenshots, UI XML, logcat, and complete run directories stay under ignored `runs/` storage.

## 案例 / Cases

| Case | Product risk covered | Live result |
| --- | --- | --- |
| [`wikipedia-research-session/`](wikipedia-research-session/) | Real network app, first-run onboarding, dynamic search, WebView article, saved-item persistence | **63/63 passed**, 113.563 s |
| [`firefox-webapp-session/`](firefox-webapp-session/) | Browser Cookie + LocalStorage, scoped test session, download, two tabs, cold-start restore | **66/66 passed**, 143.016 s |
| [`vlc-media-playback/`](vlc-media-playback/) | Native player Activity, byte-range HTTP media, decoded frames, codec/AudioTrack log assertions, orientation | **43/43 passed**, 50.579 s |
| [`ankidroid-deck-persistence/`](ankidroid-deck-persistence/) | First-run onboarding, deck/card creation, dialog input, local database persistence | **49/49 passed**, 75.203 s |
| [`markor-note-persistence/`](markor-note-persistence/) | Multi-page onboarding, Markdown editor input, save, exact filename search, cold-start recovery | **46/46 passed**, 80.203 s |

```powershell
# Run one live case at a time on a free test instance.
.\examples\wikipedia-research-session\run.ps1
.\examples\firefox-webapp-session\run.ps1
.\examples\vlc-media-playback\run.ps1
.\examples\ankidroid-deck-persistence\run.ps1
.\examples\markor-note-persistence\run.ps1
```

Each wrapper verifies the pinned APK before installing it, prints `doctor --json`, runs the flow with JUnit output, and keeps generated evidence under `runs/`.

- Firefox additionally verifies its own unique download file and restores the browser state after a cold launch.
- VLC validates a byte-range media server, checks player Activity and logcat, and removes its reverse-port mapping.
- AnkiDroid resets only case-owned state, then verifies deck/card persistence after a cold launch.
- Markor removes its own `app-testbench-*.md` files and uninstalls the app by default.

All public app screenshots come from these live runs. No generated or redrawn app pages are used. See [`../docs/cases.md`](../docs/cases.md) for screenshots, exact versions, observed results, evidence boundaries, and known limits.
