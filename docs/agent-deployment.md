# Agent Runbook

[简体中文](../README.md) | [English](../README.en.md) | **Agent**

> If you are an agent, treat this page as an execution contract. Follow the steps in order, preserve unrelated working-tree changes, and do not infer permission for a state-changing operation that the owner has not authorized.

App TestBench is a Windows-first Android app test execution layer built on MuMu Player, `MuMuManager.exe`, and ADB. This runbook is for an agent that must deploy, reproduce, verify, or publish the repository, not for a general product introduction.

## 1. Establish the authorization boundary

Read the repository's `AGENTS.md` first, then this page. State the requested outcome, allowed side effects, and required approvals before acting.

Treat these as state-changing operations:

- starting, stopping, or restarting MuMu;
- installing, clearing, launching, force-stopping, or uninstalling an app;
- writing screenshots, UI dumps, logcat, reports, or downloaded packages;
- creating or removing `adb reverse` mappings;
- changing repository visibility or GitHub settings;
- pushing commits, creating tags or Releases, or publishing a package.

A request to test the app does not authorize publishing. A request to push code does not authorize a tag, Release, visibility change, or package publication. Use only apps, accounts, devices, and data the owner is authorized to test.

Normal test-account login is permitted. Do not bypass login, CAPTCHA, anti-automation, anti-scraping, risk controls, rate limits, paywalls, or access controls.

## 2. Inspect the workspace before changing it

Run from the repository root:

```powershell
git status --short --branch
git diff --stat
git diff --check
git log -5 --oneline --decorate
git remote -v
```

Identify which changes predate the task and which belong to the current goal. Never reset, discard, overwrite, or commit unrelated user changes. If a `runs/` worktree or release worktree already exists, verify its ownership and intended use before touching it.

Completion criterion: current branch, remote, author identity, and ownership of every uncommitted change are known.

## 3. Install and verify the local tool

Use the checked-out source when working inside the repository:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
app-testbench --version
app-testbench --help
```

For development work, run the repository gate:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m build
python -m twine check dist/*
```

Do not claim PyPI availability unless an install against the intended package index actually succeeds. GitHub Release availability and PyPI publication are separate channels.

## 4. Discover MuMu and ADB

Start read-only:

```powershell
app-testbench doctor --json
app-testbench instance list --json
```

If discovery fails, set explicit paths for the current process:

```powershell
$env:APP_TESTBENCH_MUMU_MANAGER = (Join-Path $env:MUMU_HOME "nx_main\MuMuManager.exe")
$env:APP_TESTBENCH_ADB = (Join-Path $env:ADB_HOME "adb.exe")
$env:APP_TESTBENCH_INSTANCE = "0"
app-testbench doctor --json
```

Require all of the following before a live run:

- MuMuManager and ADB are found;
- the selected instance is running;
- Android boot is complete;
- ADB reports exactly the expected device;
- no unrelated case is using the same instance.

Do not print or commit the ADB serial, private IP, local username, proxy configuration, or absolute MuMu installation paths in public output.

## 5. Run the five public cases

Run one live case at a time. Do not start a second case while a MuMu slot is occupied.

```powershell
.\examples\wikipedia-research-session\run.ps1
.\examples\firefox-webapp-session\run.ps1
.\examples\vlc-media-playback\run.ps1
.\examples\ankidroid-deck-persistence\run.ps1
.\examples\markor-note-persistence\run.ps1
```

Expected coverage:

| Case | Required proof |
| --- | --- |
| Wikipedia | Onboarding, live search, article WebView, saved list, force-stop, cold-start persistence |
| Firefox/Fennec | Cookie + LocalStorage, case-owned download verified through ADB, two tabs, cold-start restore |
| VLC | `VideoPlayerActivity`, byte-range MP4, decoded frame, media-input log, `android_audiotrack`, portrait/landscape |
| AnkiDroid | Onboarding, deck/card creation, pending count, force-stop, cold-start persistence, reopened card fields |
| Markor | Multi-page onboarding, Markdown note input, save, exact filename search, cold-start body recovery |

A final passing case must report `failed=0` and `skipped=0` in `result.json`, with screenshots, UI XML, logcat, HTML, and JUnit present. A previously passing run is not a substitute for the clean run associated with the release candidate.

For a batch check, keep the same authorization boundary and use one of these paths:

```powershell
# Select flows by case-insensitive tag; each flow gets its own run directory.
app-testbench suite .\suite.yaml --tag smoke --output .\runs --json

# Run the same flow once per CSV/JSON row.
app-testbench run .\flow.yaml --data .\cases.csv --output .\runs --json

# Stream live events to an agent or CI job.
app-testbench run .\flow.yaml --events-jsonl .\runs\events.ndjson --json
```

A suite or data-driven run writes aggregate `suite-result.json` / `data-result.json`, HTML, JUnit, and `manifest.json`. Inspect each case report before treating the aggregate status as proof. The schemas are packaged as `events-v1.schema.json` and `collection-result-v1.schema.json`.

If a live run fails:

1. Read the failed step, error, hint, screenshot, UI tree, and logcat.
2. Determine whether the cause is code, flow, app, network, ADB, or environment.
3. Fix the actual cause; do not weaken an assertion merely to get green output.
4. Re-run from a clean state.
5. Keep failed exploratory runs in ignored `runs/`; do not publish raw evidence from them.

## 6. Verify machine-readable contracts

Validate success and failure JSON against the packaged schema, not a hand-written approximation:

```powershell
python -m pytest tests/test_cli.py -q
```

The failed `run --json` contract must contain:

```json
{
  "schema_version": "1.0",
  "ok": false,
  "command": "run",
  "error": {
    "type": "step_failure"
  },
  "data": {
    "status": "failed"
  }
}
```

Required failure behavior:

- exit code is `1`;
- `error` exists when `ok=false`;
- complete step data remains under `data`;
- failure screenshot, UI tree, logcat, HTML, and JUnit survive;
- `cli-v1.schema.json` validates without relaxation.

Also validate the successful envelope and `result-v1.schema.json` for both passing and failing runs.

## 7. Audit the public tree before committing

Run all checks from the public worktree, not from an ignored run directory:

```powershell
git status --short
git diff --check
git ls-files
```

Reject or redact:

- APK, AAB, XAPK, MP4, or other downloaded binaries;
- `runs/`, virtual environments, build outputs, caches, or raw evidence directories;
- raw logcat or unfiltered UI XML;
- local absolute paths, usernames, hostnames, ADB serials, private IPs, proxy settings, or MuMu UUIDs;
- account names, passwords, cookies, tokens, API keys, session exports, or authorization headers;
- screenshots containing a real account, chat, order, notification, contact, or production data.

Scan both tracked files and the staged diff. Public fixture values such as `127.0.0.1:18765`, `127.0.0.1:18766`, and the synthetic username `qa-runner` are acceptable only when they are clearly test-only.

Public PNG evidence must:

- come from a real MuMu run;
- show the app page or the claimed evidence state;
- contain no password field, personal account, secret, local path, or ADB serial;
- have metadata stripped;
- be listed in `docs/assets/cases/SHA256SUMS`;
- pass the screenshot dimension and file-set tests.

Completion criterion: the staged tree contains only intentional source, docs, tests, and audited public evidence.

## 8. Build and verify the installable package

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m build
python -m twine check dist/*
```

Create a fresh virtual environment under ignored storage, install the built wheel, and verify:

```powershell
app-testbench --version
app-testbench doctor --json
app-testbench skill-path
app-testbench init --output .\app-testbench-flow.yaml
app-testbench validate .\app-testbench-flow.yaml --json
```

Run at least one real flow from the clean wheel environment. Confirm that the installed package includes the schemas and skill resource it claims.

## 9. Publish only after explicit authorization

If the owner explicitly authorized a GitHub publication, use a dedicated branch and logical commits. Separate these permissions: push to `main`, create or move a tag, create or edit a GitHub Release, change visibility, and publish to PyPI. One permission does not imply the others.

For a documentation-only or implicit maintenance update, push the reviewed commit without changing the package version, tag, or Release. Never move or overwrite an existing tag.

```powershell
git switch -c codex/release-maintenance
git add <reviewed files>
git commit -m "docs: improve user onboarding and capability guidance"
git push -u origin codex/release-maintenance
```

Before a versioned release:

1. Confirm the final commit is on `main`.
2. Confirm CI is green.
3. Confirm the version in `pyproject.toml`, `CHANGELOG.md`, tag, and release notes agree.
4. Create the tag only when the owner explicitly requested a new version.
5. Create the GitHub Release from the matching file under `docs/releases/`.
6. Verify the remote tag target, Release URL, assets, and CI status.

Do not claim a successful push, tag, Release, or package publication unless the remote API or web page confirms it.

## 10. Clean up live state

At the end of the task, stop any MuMu Android instance and close the main window unless the owner requested otherwise. Remove case-owned reverse mappings and uninstall test apps from the dedicated instance.

Suggested cleanup:

```powershell
app-testbench reverse-port 18765 --remove --json
app-testbench reverse-port 18766 --remove --json
app-testbench close org.wikipedia
app-testbench close org.mozilla.fennec_fdroid
app-testbench close org.videolan.vlc
app-testbench close com.ichi2.anki
app-testbench close net.gsantner.markor
app-testbench instance stop 0 --json
```

There is no one-shot `app-testbench uninstall` command in v0.2.0. If a dedicated test instance must remove a package, use the wrapper's documented cleanup or `adb shell pm uninstall <package>` with the verified serial, and only after confirming that the package is case-owned.

Do not delete ignored `runs/` evidence that may be needed for the final report. Do not remove unrelated background MuMu services if they belong to the host owner and the task only requires stopping the Android instance.

Verify:

- no ready ADB device remains;
- the MuMu Android instance is stopped;
- the visible MuMu window is closed;
- case-owned reverse ports are gone;
- the public worktree still passes `git diff --check`.

## 11. Final report

Report only verified facts:

- branch and commit hashes;
- version, tag, CI, and Release status;
- exact live case results and durations;
- public screenshot paths;
- HTML, `result.json`, and JUnit evidence;
- failure-envelope schema result;
- privacy audit findings;
- remaining limitations and cleanup state.

If a gate fails, report the blocking check and continue fixing it. Do not describe a partial result as “basically complete.”
