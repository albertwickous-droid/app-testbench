# App TestBench Agent Runbook

[简体中文](../README.md) | [English](../README.en.md) | **Agent**

If you are an agent, use this runbook as the operating contract for App TestBench. Follow only the path that matches the request. Run the checks yourself when you have shell access, and stop at the first failed gate instead of working around it.

## Choose the task

| Request | Follow |
| --- | --- |
| Install the tool, control MuMu, write a flow, or run a test | Sections 1-7 |
| Reproduce the public live cases | Sections 1-8 |
| Change source code or packaging | Sections 1-4 and 9 |
| Push the repository or configure GitHub | Sections 1-4 and 10-11 |
| Create a tag, GitHub Release, or PyPI package | Sections 1-4 and 12-13 |

State the intended task and external side effects before making changes. A request to test an app does not authorize publishing the repository. A request to push code does not authorize a tag, Release, visibility change, or PyPI upload.

## 1. Establish the operating boundary

App TestBench is a Windows-first CLI for repeatable Android app testing through MuMu Player, `MuMuManager.exe`, and ADB. The supported v0.1.1 path is Windows 10/11 with a MuMu instance that has ADB enabled.

Use the tool only for applications, accounts, devices, and test environments that the owner is authorized to test. Normal test-account login is allowed. Do not use the tool to bypass login, CAPTCHA, anti-automation controls, risk controls, rate limits, paywalls, or access controls.

Treat these actions as state-changing:

- starting, restarting, or stopping a MuMu instance
- installing or uninstalling an APK
- launching or force-stopping an app
- writing screenshots, UI dumps, logs, reports, or downloaded packages
- pushing commits, changing repository visibility, creating tags or Releases, or publishing a package

Completion criterion: the requested outcome, the allowed side effects, and the required approvals are stated explicitly.

## 2. Read the repository sources of truth

Read these files before acting:

1. `AGENTS.md`
2. `README.en.md`
3. `docs/flow-reference.md` when editing a flow
4. `docs/cases.md` when reproducing the public live cases
5. `docs/publishing.md` when publishing
6. `docs/github-repository-setup.md` when changing GitHub settings
7. `RELEASE_CHECKLIST.md` when creating a Release
8. `SECURITY.md`, `PRIVACY.md`, and `RESPONSIBLE_USE.md` before handling evidence or publishing data

When two sources appear to conflict, prefer the action that exposes less data, mutates less external state, and preserves the documented product scope.

Completion criterion: every branch used by the task has a current source of truth.

## 3. Inspect the working state

Run from the repository root:

```powershell
git status --short --branch
git log -3 --oneline --decorate
git remote -v
git config user.name
git config user.email
```

If the worktree is not clean, identify which changes belong to the current task and which predate it. Preserve unrelated changes. Do not reset, discard, overwrite, or commit them without owner approval.

Completion criterion: the current branch, remote, author identity, and ownership of every uncommitted change are known.

## 4. Install and verify the local tool

Use the checked-out source when working inside the repository:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
app-testbench --version
app-testbench --help
```

For development work, install the development extras and run the full gate:

```powershell
python -m pip install -e ".[dev]"
.\scripts\check.ps1 -SkipInstall
```

The gate must include Ruff, formatting, the full test suite, wheel and sdist builds, and `twine check`. If the package is available from a package index and the task is end-user installation, verify the package entry point directly:

```powershell
python -m pip install app-testbench
app-testbench --version
```

Do not claim PyPI availability unless the install command succeeds against the intended index and version.

Completion criterion: `app-testbench --version` succeeds, and every required local check passes.

## 5. Discover MuMu and ADB

Start with read-only discovery:

```powershell
app-testbench doctor --json
app-testbench instance list --json
```

If auto-discovery fails, pass explicit paths or set environment variables:

```powershell
# Set MUMU_HOME and ADB_HOME to your own installation directories.
$env:APP_TESTBENCH_MUMU_MANAGER = (Join-Path $env:MUMU_HOME "shell\MuMuManager.exe")
$env:APP_TESTBENCH_ADB = (Join-Path $env:ADB_HOME "adb.exe")
$env:APP_TESTBENCH_INSTANCE = "0"
$env:APP_TESTBENCH_JSON = "1"

app-testbench doctor --json
app-testbench instance list --json
```

If testing a live app, select a dedicated test instance and verify that the instance is running, the Android boot has completed, and ADB reports the expected device before installing anything.

Completion criterion: the JSON output identifies the MuMuManager path, ADB path, instance, serial or port, Android state, and any discovery error.

## 6. Write and validate the flow

Create a starter flow, then replace the example package and steps with the authorized test target:

```powershell
app-testbench init --output .\app-testbench-flow.yaml
app-testbench validate .\app-testbench-flow.yaml
```

Before choosing coordinates, collect evidence from the actual screen:

```powershell
app-testbench --instance 0 screenshot --output .\artifacts\screen.png
app-testbench --instance 0 dump-ui --output .\artifacts\screen.xml
```

Additional deterministic setup actions are available when the authorized test requires them:

```powershell
app-testbench open "https://example.test/" --package com.example.app --mime-type text/html
app-testbench reverse-port 18765 --local-port 18765
app-testbench clear-data com.example.app
app-testbench orientation landscape
```

`clear-data` is destructive to that app's local state. `reverse-port`, `orientation`, and `open` may change device/runtime state; declare them in the flow, not as unexplained side effects.

Use coordinates supported by the screenshot and UI hierarchy. Prefer text waits and assertions where the UI exposes readable text. Keep test credentials in environment variables or an approved secret store; do not write production credentials, cookies, tokens, or personal data into the flow or report.

Run the validated flow:

```powershell
app-testbench run .\app-testbench-flow.yaml `
  --output .\runs `
  --junit-xml .\artifacts\junit.xml `
  --wait-for-boot `
  --boot-timeout 60 `
  --json
```

`--boot-timeout` implies the boot-readiness wait. A failed step stops later steps and should produce diagnostic evidence when the backend allows it.

Completion criterion: validation succeeds before execution, and the run exits with a documented status rather than an unexplained shell error.

## 7. Verify the evidence

Read `result.json` and inspect the run directory. A run normally contains:

```text
runs/<timestamp>-<flow-name>/
├── report.html
├── result.json
├── screenshots/
├── ui/
└── logs/
```

Check:

1. The process exit code matches the result status.
2. Every expected step appears with its duration.
3. The first failed step includes the original error.
4. Screenshots, UI XML, logcat, and JUnit output exist when the flow requests them.
5. `report.html` opens locally and does not depend on a CDN.
6. No token, cookie, account, private hostname, or personal data will be published with the evidence.

Exit codes are `0` for success, `1` for execution failure, `2` for invalid arguments or flow configuration, and `130` for interruption.

If MuMu was started only for this task, stop it after the evidence is written. Follow any owner-specified cleanup window or automation rule.

Completion criterion: the reported pass/fail can be reproduced from the flow, exit code, and saved evidence.

## 8. Reproduce the public live cases

The v0.1.1 release includes two real Android cases. Treat them as executable examples, not synthetic documentation.

### Fennec local web session

```powershell
.\examples\fennec-local-web-session\run.ps1
```

The script downloads Fennec F-Droid `160.0.0` (`versionCode 1600020`) from the official F-Droid repository into ignored `runs/case-assets/` and verifies:

```text
SHA256: 43cf491bbc677244d7b56ba2e8ae20ccd802c9d8f6b44d6b6aff7eb1753eab1b
```

It starts a hidden repository-owned FieldDesk HTTP server, verifies the homepage marker, exposes it through `adb reverse`, installs and verifies the APK, completes onboarding and login, exercises asynchronous search and detail navigation, force-stops and cold-launches Fennec, verifies `localStorage` session/query restoration, logs out, and stops only the server it started.

Require all of the following before calling the case passed:

- process exit code `0`;
- CLI JSON has `ok: true` and `data.summary.passed == 71`;
- JUnit contains 71 testcases with zero failures and zero errors;
- 11 real screenshots exist at 720x1280;
- the local run contains UI XML, Fennec/Gecko logcat, `report.html`, `result.json`, and JUnit;
- `report.html` embeds its images and has no external script, stylesheet, or CDN dependency;
- the public assets in `docs/assets/cases/fennec/` match the recorded SHA256 manifest.

### VLC HTTP playback

```powershell
.\examples\vlc-http-playback\run.ps1
```

The script downloads VLC `3.7.2` (`versionCode 13070208`) and the Sintel trailer from their published sources into ignored `runs/case-assets/` and verifies the pinned SHA256 values. It starts the repository Range server and first requires a `206 Partial Content` response with the exact `Content-Range` before running the flow.

Require exit code `0`, `data.summary.passed == 30`, 30 JUnit testcases, five 1280x720 screenshots, the welcome/tutorial/playback images, and logcat evidence for HTTP, demux, MediaCodec, H.264/AVC, and AAC.

### Failure envelope contract

Create a temporary failing flow under `runs/` that launches an installed app and waits for a marker guaranteed not to exist. Run it with `--json`, capture stdout as UTF-8, and require:

- process exit code `1`;
- `ok: false`;
- `error.type == "step_failure"`;
- a complete `data` object with `status == "failed"`;
- the JSON envelope validates against `src/app_testbench/schemas/cli-v1.schema.json` using Draft 2020-12;
- a failure screenshot, UI XML, final logcat, HTML report, and JUnit file exist;
- later main steps are recorded as skipped while teardown still runs.

Do not relax the schema to make this pass. The regression test is `tests/test_cli.py::test_failed_run_json_matches_cli_schema`.

Cleanup rule: stop the tested apps, remove any test `adb reverse` mappings, uninstall test APKs, stop any MuMu instance started for the case, and close the MuMu main window when the owner's timing rule requires it. Do not commit APKs, raw run directories, full logs, UI XML, or unselected screenshots.

Completion criterion: the committed flow and scripts reproduce the documented step counts and real evidence on the stated MuMu/Android/display/language baseline, or the agent reports the exact environment difference.

## 9. Change source code safely

For code changes:

```powershell
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

For packaging changes, also run:

```powershell
python -m build
python -m twine check dist/*
```

Keep host command execution behind the process adapter and argument arrays. Keep flow validation strict. Escape report content, preserve offline reports, and keep telemetry and cloud uploads out of the product. Add or update tests whenever behavior changes.

Do not describe fake-backend coverage as live MuMu coverage. Record the MuMu version, Windows version, Python version, selected instance, and observed result when a live test is performed.

Completion criterion: tests and checks pass, and the final report distinguishes fake-backend tests from live-device evidence.

## 10. Publish the repository

Require explicit owner approval before changing visibility, creating a tag or Release, or publishing to a package index. A normal `git push` still requires approval to commit and push the owner's changes.

Before publishing, run:

```powershell
git status --short
git diff --check
.\scripts\check.ps1
```

Check tracked paths for likely sensitive artifacts:

```powershell
git ls-files | Select-String -Pattern '(^|/)(\.env|runs|reports|artifacts|dist|build)(/|$)|\.(apk|aab|xapk|log|pem|key|p12|pfx)$|(^|/)(cookies\.(txt|json)|auth\.json|secrets\.)'
```

The command should return nothing relevant. If it finds an APK, log, screenshot, credential file, exported session, private key, personal profile, or other sensitive data, stop and ask the owner to classify or remove it. Do not merely delete the file and continue if a real secret may already have been exposed; report it and recommend credential rotation.

Push normally and verify the remote branch:

```powershell
git push origin main
git ls-remote --heads origin main
```

Never use `git push --force` or rewrite published history. If the repository uses a proxy because of network policy, pass it only for the command being run; do not persist credentials or proxy secrets in the repository.

Completion criterion: the remote branch matches local `HEAD`, the working tree is understood, and no sensitive file is staged or tracked.

## 11. Configure GitHub

Follow `docs/github-repository-setup.md` for the current owner/repository. Verify:

- the repository description matches the product
- topics describe Android app testing rather than general RPA
- default branch is the intended branch
- Secret Scanning and push protection are enabled when available
- Dependabot security updates and private vulnerability reporting are enabled when available
- CodeQL or the configured code-scanning workflow passes
- branch and tag rulesets protect `main` and release tags
- Actions permissions follow least privilege

Changing a repository from private to public is an owner decision. Do not infer approval from a successful CI run.

Completion criterion: the repository settings match the documented setup, or the agent reports the exact setting it could not verify.

## 12. Create a release

Before creating a tag, confirm:

- the owner explicitly approved the version and tag
- `main` is clean and pushed
- the version in `pyproject.toml` and `app_testbench.__version__` match
- release notes describe actual changes and do not overstate live validation
- release assets are built from the tagged commit
- the Release workflow creates a Draft until the owner approves publication

Then run only after approval:

```powershell
git tag -a vX.Y.Z -m "App TestBench vX.Y.Z"
git push origin vX.Y.Z
```

Download the resulting wheel, sdist, and checksum file. Verify the checksums and a clean installation in a temporary environment. Do not move or delete a published tag.

Completion criterion: the tag points at the intended commit, CI passes for that tag, artifacts match their checksums, and the Release visibility matches the owner's approval.

## 13. Publish to PyPI

PyPI is a separate release channel. A GitHub tag, GitHub Release, and PyPI upload do not publish one another automatically.

Before running the PyPI workflow, confirm:

- the owner explicitly approved the package name and version
- PyPI Trusted Publishing is configured for the exact owner, repository, workflow, and environment
- the `pypi` environment exists in GitHub
- the workflow is manually triggered
- the wheel and sdist have passed `twine check`
- installation and `app-testbench --version` succeed from the intended index

After publication, verify the project page, the uploaded version, `pip install app-testbench`, and the CLI entry point. Report failure as failure; do not substitute a local editable install for a successful package publication.

Completion criterion: the intended version is visible on the package index and installs in a clean environment.

## Stop conditions

Stop and report immediately when any of these occurs:

- required authorization, login, or owner approval is missing
- the worktree contains unexplained changes
- the full test gate fails
- a real credential, cookie, token, private key, personal profile, or private user data is found
- the live MuMu environment is unavailable and the task requires live evidence
- CI fails
- a command would require force-pushing or rewriting published history
- a release step would change visibility or publish artifacts without explicit approval

## Final report

Report only facts that can be verified from commands or stored evidence:

```text
Requested task:
Repository:
Branch:
Commit:
Remote:
Worktree:
Local checks:
CI:
MuMu / Android:
Flow validation:
Run result:
Evidence paths:
Release:
PyPI:
Cleanup:
Outstanding risks:
```

Do not describe a Draft Release as a published Release. Do not describe fake-backend tests as a live-device test. Do not describe local build success as package-index availability.
