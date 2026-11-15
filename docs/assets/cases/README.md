# Case image provenance

All PNG files under this directory were selected from live MuMu Player runs on
2026-11-16. They are not AI-generated mockups.

| Case | Source run | Public treatment |
| --- | --- | --- |
| Fennec local web session | `20261116-023035-fennec-local-web-session`, 71/71 passed | Five browser-content images have the URL/status bar cropped; `first-run.png` is unchanged. |
| VLC HTTP playback | `20261116-023232-vlc-http-playback`, 30/30 passed | Uncropped 1280x720 frames from the real run. |
| CLI failure evidence | `20261116-025843-cli-failure-contract-live` (clean-wheel run), 3 passed / 1 failed / 1 skipped | The report screenshot was rendered from a temporary redacted copy; local paths and the test serial were replaced before rendering. |

The complete run directories, original screenshots, APKs, full logcat, and UI XML
remain under the ignored local `runs/` directory. See `SHA256SUMS` for the exact
public files.
