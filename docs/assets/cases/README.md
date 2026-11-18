# Case image provenance

All PNG files under this directory were selected from live MuMu Player runs on
2026-11-16. They are not AI-generated mockups or manually redrawn app pages.

| Case | Source run | Public treatment |
| --- | --- | --- |
| Wikipedia research session | `20261116-171723-wikipedia-research-session`, 63/63 passed | Three uncropped 720x1280 screenshots selected for search, article, and post-cold-start evidence. |
| Firefox/Fennec web session | `20261116-175711-firefox-webapp-session`, 66/66 passed | Four uncropped 720x1280 screenshots selected for session, orders, tabs, and case-owned download evidence. |
| VLC media playback | `20261116-174654-vlc-media-playback`, 43/43 passed | Two 720x1280 and two 1280x720 screenshots selected for tutorial, paused player, landscape playback, and resumed decoded frame evidence. |
| AnkiDroid deck persistence | `20261116-134731-ankidroid-deck-persistence`, 49/49 passed | Three uncropped 720x1280 screenshots selected for card input, post-restart persistence, and reopened saved-card evidence. |
| Markor note persistence | Recorded v0.1.1 maintenance case, 46/46 passed | Three uncropped 720x1280 screenshots selected for persisted file, exact search, and reopened note evidence. |
| CLI failure evidence | `20261116-025843-cli-failure-contract-live` (clean-wheel run), 3 passed / 1 failed / 1 skipped | The report screenshot was rendered from a temporary redacted copy; local paths and the test serial were replaced before rendering. |

The complete run directories, original screenshots, APKs, MP4 files, full
logcat, and UI XML remain under the ignored local `runs/` directory. Every PNG
was decoded and re-encoded without ancillary metadata before publication. See
`SHA256SUMS` for the exact public files.

## File set

```text
ankidroid/card-filled.png
ankidroid/persistence.png
ankidroid/saved-card.png
evidence/report-failed.png
firefox/download.png
firefox/orders.png
firefox/session.png
firefox/tabs.png
markor/note-persisted.png
markor/note-reopened.png
markor/note-search.png
vlc/landscape.png
vlc/player-controls.png
vlc/resumed.png
vlc/tutorial.png
wikipedia/article.png
wikipedia/persisted.png
wikipedia/search-results.png
```
