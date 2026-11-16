# Case image provenance

All PNG files under this directory were selected from live MuMu Player runs on
2026-11-16. They are not AI-generated mockups or manually redrawn app pages.

| Case | Source run | Public treatment |
| --- | --- | --- |
| Wikipedia research session | `20261116-171723-wikipedia-research-session`, 63/63 passed | Three uncropped 720x1280 screenshots selected for search, article, and post-cold-start evidence. |
| Firefox/Fennec web session | `20261116-175711-firefox-webapp-session`, 66/66 passed | Four uncropped 720x1280 screenshots selected for session, orders, tabs, and case-owned download evidence. |
| VLC media playback | `20261116-174654-vlc-media-playback`, 43/43 passed | Four uncropped screenshots selected for tutorial, paused player, landscape playback, and resumed decoded frame evidence. |
| CLI failure evidence | `20261116-025843-cli-failure-contract-live` (clean-wheel run), 3 passed / 1 failed / 1 skipped | The report screenshot was rendered from a temporary redacted copy; local paths and the test serial were replaced before rendering. |

The complete run directories, original screenshots, APKs, MP4 files, full
logcat, and UI XML remain under the ignored local `runs/` directory. Every PNG
was decoded and re-encoded without ancillary metadata before publication. See
`SHA256SUMS` for the exact public files.
