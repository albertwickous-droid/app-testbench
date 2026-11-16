# VLC media playback / VLC 媒体播放、Activity 与底层日志

A media-focused live case for VLC for Android. It serves a real MP4 from a local byte-range HTTP server, opens the native player Activity, and verifies both visible playback state and libVLC/AudioTrack log lines.

这是 VLC for Android 的媒体案例。通过本地支持 byte-range 的 HTTP 服务播放真实 MP4，进入原生播放器 Activity，同时验证可见播放状态与 libVLC/AudioTrack 日志。

## Why this app / 为什么选它

- VLC is a mature open-source media application with a pinned F-Droid build.
- It covers a different failure surface from browser or database tests: Activity transitions, native decoding surfaces, media transport, codec initialization, AudioTrack output, and orientation.
- The player UI has stable accessibility nodes while the decoded video itself does not. The flow therefore combines `wait_for_activity`, screenshots, UI assertions, and `assert_logcat_contains`.
- It demonstrates that App TestBench is not limited to clicking text in a UI dump.

## Pinned input / 固定输入

| Field | Value |
| --- | --- |
| Package | `org.videolan.vlc` |
| Version | `3.7.2` |
| Version code | `13070208` |
| APK source | <https://f-droid.org/repo/org.videolan.vlc_13070208.apk> |
| APK SHA256 | `727693d59c4d678c046386812a103209a25423460c9d22e38e12460f12402ab6` |
| Media source | <https://media.w3.org/2010/05/sintel/trailer.mp4> |
| Media size | `4,372,373` bytes |
| Media SHA256 | `b670602fa00934ca27c4351bb0efe7ea7a07fae57284e44226025eeed7c51254` |
| Player Activity | `org.videolan.vlc/.gui.video.VideoPlayerActivity` |

## Run / 运行

```powershell
.\examples\vlc-media-playback\run.ps1
```

The wrapper downloads and verifies the APK and MP4, starts the byte-range server on `127.0.0.1:18766`, exposes it through `adb reverse`, runs the 43-action flow with JUnit, and always stops its local server in `finally`.

脚本会下载并校验 APK 与 MP4，在 `127.0.0.1:18766` 启动 byte-range 服务，通过 `adb reverse` 暴露给设备，执行 43 步 flow 与 JUnit，并在 `finally` 中停止本地服务。

## What the live flow proves / 实际覆盖

1. Installs and verifies the pinned VLC build.
2. Clears VLC state and grants runtime permissions through reinstall.
3. Completes first-run onboarding and opens the real MP4 through Android `ACTION_VIEW`.
4. Waits for `org.videolan.vlc/.gui.video.VideoPlayerActivity`.
5. Dismisses the first-play tutorial and captures decoded video frames.
6. Pauses playback and verifies the title `Sintel Trailer`.
7. Asserts logcat contains `Creating an input for 'sintel-trailer.mp4'`.
8. Asserts logcat contains the Android `android_audiotrack` output module.
9. Checks portrait and landscape relayout while the player Activity remains foreground.
10. Retains screenshots, UI tree, logcat, HTML, `result.json`, and JUnit.

Recorded result on 2026-11-16: **43 passed, 0 failed, 0 skipped, 50.579 seconds**.

## Expected evidence / 预期证据

- real tutorial, paused-player, landscape-player, and resumed-frame screenshots;
- `wait_for_activity` results for the native player component;
- logcat matches for the media input and AudioTrack module;
- self-contained HTML, `result.json`, and JUnit.

## Known limits / 已知限制

- VLC copy, buttons, and coordinates are calibrated for `3.7.2`, Simplified Chinese, `720x1280`, and the recorded MuMu Android 12 image.
- The case uses a short public MP4 and local HTTP byte-range transport. It does not claim DRM, adaptive streaming, subtitle, or audio-track behavior.
- Logcat is a bounded ring buffer. The case stops unrelated log-heavy browser processes first; very noisy devices may still require a larger buffer or a narrower future filter.
- The test is not a codec certification and does not cover hardware-specific physical-device behavior.
- Public screenshots contain no local paths, ADB serials, accounts, or private media.

## Cleanup / 清理

Teardown closes VLC, captures final logcat, removes the reverse mapping, and restores portrait orientation. The wrapper stops its local media server. On a dedicated test instance:

```powershell
app-testbench reverse-port 18766 --remove --json
app-testbench close org.videolan.vlc
app-testbench uninstall org.videolan.vlc
adb shell rm -rf /sdcard/Movies/AppTestBench
```
