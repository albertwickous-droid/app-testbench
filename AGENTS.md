# Agent instructions

## Project

App TestBench is a Python 3.10+ CLI for repeatable Android app UI testing. MuMu Player through MuMuManager and ADB is the first runtime backend. Preserve the focused App-testing scope; do not turn it into a general RPA platform.

## Before changing code

```powershell
.\.venv\Scripts\Activate.ps1
python -m ruff check .
python -m pytest -q
```

## Required checks

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

For packaging changes, also run:

```powershell
python -m build
python -m twine check dist/*
```

## Engineering rules

- Keep external command execution behind `ProcessRunner` and adapters.
- Never use `shell=True` for host command execution.
- Strictly validate flow fields; do not silently accept typos.
- Escape all user-controlled report content.
- Keep reports self-contained; do not add CDN dependencies.
- Preserve the no-telemetry and local-only behavior.
- Add or update tests when behavior changes.
- Do not commit APKs, logs, screenshots, `runs/`, `.env`, or tokens.

## Real-device changes

Fake-backend tests verify command shape and artifacts, not all MuMu version behavior. If a change affects device control, record the tested MuMu version and whether a live test was performed. Do not claim live verification when only fakes were used.
