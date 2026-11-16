# Case image provenance

All PNG files under this directory were selected from live MuMu Player runs on
2026-11-16. They are not AI-generated mockups or manually redrawn app pages.

| Case | Source run | Public treatment |
| --- | --- | --- |
| AnkiDroid deck and card persistence | `20261116-134731-ankidroid-deck-persistence`, 49/49 passed | Three uncropped 720x1280 screenshots selected for input and post-restart persistence evidence. |
| Markor note persistence | `20261116-143121-markor-note-persistence`, 46/46 passed | Three uncropped 720x1280 screenshots selected for file discovery and post-restart content evidence. |
| CLI failure evidence | `20261116-025843-cli-failure-contract-live` (clean-wheel run), 3 passed / 1 failed / 1 skipped | The report screenshot was rendered from a temporary redacted copy; local paths and the test serial were replaced before rendering. |

The complete run directories, original screenshots, APKs, full logcat, and UI XML
remain under the ignored local `runs/` directory. See `SHA256SUMS` for the exact
public files.
