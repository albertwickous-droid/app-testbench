# VLC HTTP playback and codec verification

This case moves beyond UI navigation. VLC for Android opens an MP4 from a
host-side HTTP server through `adb reverse`, dismisses its first-play tutorial,
plays real video and audio, and leaves screenshot plus logcat evidence that the
application reached the expected HTTP, demux, codec, and Android MediaCodec
paths.

## Why VLC

- VLC is a widely used open-source Android media application with a real player
  lifecycle and hardware codec path.
- The case covers a different engineering class from Fennec: binary media,
  byte-range HTTP responses, first-run permissions, player onboarding, and
  external decoder behavior.
- A local W3C test asset avoids remote streaming variability while retaining a
  real browser-independent Android playback path.
- It demonstrates why App TestBench is an execution and evidence layer: a
  screenshot alone does not prove that VLC decoded the stream, so the flow also
  captures logcat.

## Pinned inputs

| Input | Value |
| --- | --- |
| Package | `org.videolan.vlc` |
| Version | `3.7.2` (`13070208`) |
| APK source | `https://f-droid.org/repo/org.videolan.vlc_13070208.apk` |
| APK SHA256 | `727693d59c4d678c046386812a103209a25423460c9d22e38e12460f12402ab6` |
| Video source | `https://media.w3.org/2010/05/sintel/trailer.mp4` |
| Video size | `4,372,373` bytes |
| Video SHA256 | `b670602fa00934ca27c4351bb0efe7ea7a07fae57284e44226025eeed7c51254` |
| Local origin | `http://127.0.0.1:18766/sintel-trailer.mp4` |

The APK and video are downloaded into ignored `runs/case-assets/` storage and
are never committed.

## Run

```powershell
.\examples\vlc-http-playback\run.ps1
```

The script verifies both pinned assets, starts a hidden HTTP/1.1 byte-range
server when port `18766` is free, executes VLC onboarding and playback, writes a
JUnit report, and stops only the server process it created. The flow closes VLC
and removes the reverse mapping in teardown.

Manual server check:

```powershell
curl.exe -D - -o NUL -H "Range: bytes=0-1023" `
  http://127.0.0.1:18766/sintel-trailer.mp4
```

Expected response: `206 Partial Content`, `Accept-Ranges: bytes`, and a
`Content-Range` header matching the requested range.

## What the flow verifies

1. Installs the exact VLC package/version and clears app data.
2. Completes VLC welcome, media-access, autoscan, and theme onboarding.
3. Opens an HTTP MP4 through an ADB-reversed server with byte-range support.
4. Dismisses the first-play tutorial without leaving the player.
5. Captures real video frames, visible controls, and the playing timeline.
6. Captures logcat containing the HTTP media open, H.264/AAC decoder setup, and
   Android hardware media codec activity.
7. Closes VLC and removes the test reverse mapping in teardown.

## Expected evidence

Useful logcat lines include:

```text
http://127.0.0.1:18766/sintel-trailer.mp4 ... successfully opened
libvlc demux: adding track ... video
libvlc demux: adding track ... audio
using OMX.qcom.video.decoder.avc
original format sz 854x480
```

The exact decoder names vary by MuMu/Android image. The committed documentation
screenshots are selected from a real MuMu run at 1280x720, Android 12,
Simplified Chinese UI.

## Known limits

- Coordinates and localized onboarding text are specific to the tested
  1280x720 landscape profile. Re-capture them for another resolution or locale.
- Active video can make `uiautomator dump` fail with `could not get idle state`.
  This case deliberately captures UI trees on onboarding/home and uses
  screenshots plus logcat during active playback.
- The test asset is a non-DRM H.264/AAC MP4. DRM, adaptive streaming, subtitle,
  and audio-track switching are outside this case.
- VLC may remember the last playback position. `run.ps1` uses a unique query
  string so each run opens the media from the beginning.
- This is an authorized app-testing example. It does not bypass authentication,
  anti-automation, anti-scraping, or access controls.
