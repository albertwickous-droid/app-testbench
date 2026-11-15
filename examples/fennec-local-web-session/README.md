# Fennec F-Droid local web session

This case uses a real Android browser against a deterministic web app served
from the test machine. It proves more than a launcher smoke test: Fennec must
complete first-run UI, reach a local HTTP origin through `adb reverse`, accept
text input, wait for asynchronous JavaScript state, preserve `localStorage`
across a forced stop, and return to the login screen after logout.

## Why Fennec

- Fennec F-Droid is a maintained, open-source Android browser distributed
  through F-Droid.
- Its first-run onboarding and Android password-manager prompt exercise real
  system UI that a simple Activity launcher does not cover.
- A local web origin keeps the login, search latency, result rendering, and
  session persistence deterministic without a third-party account.
- The browser remains a mainstream renderer, so the case tests the app-facing
  automation layer rather than a custom toy Android shell.

## Pinned inputs

| Input | Value |
| --- | --- |
| Package | `org.mozilla.fennec_fdroid` |
| Version | `160.0.0` (`1600020`) |
| APK source | `https://f-droid.org/repo/org.mozilla.fennec_fdroid_1600020.apk` |
| APK SHA256 | `43cf491bbc677244d7b56ba2e8ae20ccd802c9d8f6b44d6b6aff7eb1753eab1b` |
| Demo account | `qa@example.test` / `demo123` |
| Local origin | `http://127.0.0.1:18765/` |

The APK is downloaded into ignored `runs/case-assets/` storage and is never
committed.

## Run

```powershell
.\examples\fennec-local-web-session\run.ps1
```

The script downloads and verifies the APK, starts a hidden local HTTP server
when port `18765` is free, runs `doctor`, executes the flow with a JUnit report,
and stops only the server process it created. The flow closes Fennec and removes
its `adb reverse` mapping in teardown.

Manual run:

```powershell
$apk = .\examples\fennec-local-web-session\prepare.ps1
$env:FENNEC_APK = $apk
$env:FENNEC_SITE_URL = "http://127.0.0.1:18765/"
.\examples\fennec-local-web-session\serve.ps1
# In another terminal:
app-testbench run .\examples\fennec-local-web-session\flow.yaml `
  --output .\runs\examples\fennec-local-web-session `
  --junit-xml .\runs\examples\fennec-local-web-session\junit.xml `
  --wait-for-boot --boot-timeout 60
```

## What the flow verifies

1. Installs the exact package/version and clears app data for a repeatable state.
2. Completes Fennec first-run onboarding and declines the default-browser prompt.
3. Routes a host-only web origin into the Android instance with `adb reverse`.
4. Loads a real form, enters demo credentials, and dismisses the password-save UI.
5. Waits for the delayed `Workspace ready` state instead of assuming an immediate render.
6. Searches `checkout`, waits for `Checkout regression`, and opens `QA-2417`.
7. Force-stops the browser, cold-launches it, reopens the origin, and asserts the
   previous `checkout` query and authenticated session were restored.
8. Logs out, verifies that the authenticated workspace is gone, and captures
   screenshot, UI hierarchy, HTML, JSON, and JUnit evidence.

## Expected result

The run should finish with every step passed. The generated report is under a
new timestamped directory in `runs/examples/fennec-local-web-session/`; inspect
`report.html`, `result.json`, `junit.xml`, `screenshots/`, `ui/`, and `logs/`.
The committed documentation screenshots are selected from a real MuMu run at
1280x720, Android 12, Simplified Chinese UI.

## Known limits

- Coordinates and localized onboarding text are specific to the tested
  1280x720 portrait profile. Re-capture them for another resolution or locale.
- The case uses browser UI automation, not OCR or image matching. The local site
  exposes stable text in the WebView accessibility tree.
- The demo credentials are deliberately public test data, not a production
  account. Do not replace them with personal credentials in a committed flow.
- Fennec's translation and password-save prompts are browser behavior, not part
  of the test website. If they change, update the flow from fresh screenshots.
- This is an authorized app-testing example. It does not bypass authentication,
  anti-automation, anti-scraping, or access controls.
