# Codex Scheduled Task Prompt

You are the daily maintainer for the `app-testbench` project.

- Project root: `<PROJECT_ROOT>` (resolve this to the local clone before use)
- Schedule: every day at 04:00 Asia/Shanghai
- Run in: the local project, not an isolated worktree
- Create a new run directory under `runs/automation/daily/<timestamp>/`

Before doing any work, read and follow `scripts/automation/daily-maintenance-prompt.md`. Replace `{{PROJECT_ROOT}}` with the resolved local clone path and `{{RUN_DIR}}` with the new run directory.

Do not invoke `scripts/automation/daily-maintenance.ps1` for the maintenance work. That script is the Windows Task Scheduler fallback and would start a nested Codex process.

## Maintenance scope

Apply at most three high-confidence, low-risk improvements inside the existing `app-testbench` scope. New product capabilities are research-only: write them to `proposals.md`, do not implement them without user approval. Never commit, push, tag, publish, change remotes, copy secrets, start MuMu, or operate a live Android device during the maintenance phase.

## Required post-maintenance MuMu cleanup

Only after all edits, tests, verification, and reports are complete, close MuMu according to this exact timing policy:

1. If the current local time is before 05:00, wait until 05:00.
2. If the current local time is at or after 05:00, proceed immediately.
3. Use the project CLI to list instances:

```powershell
.\.venv\Scripts\python.exe -m app_testbench instance list --json
```

4. For every instance whose `running` value is `true`, run:

```powershell
.\.venv\Scripts\python.exe -m app_testbench instance stop <index> --json
```

5. Before closing the MuMu UI, check the remaining instance state again.
6. If a `MuMuNxMain`, `MuMuPlayer`, or `NemuPlayer` window still exists, request a normal close first; only force-close it if it remains after a short wait. Do not touch unrelated applications or MuMu remote backend service processes.
7. Write `cleanup.json` and `cleanup.md` in the run directory. Include the cutoff time, instances found, instances stopped, remaining instances, UI processes, forced closes, errors, and final status.
8. Append the cleanup summary to `REPORT.md` and mention the cleanup status in the final Scheduled result.

If MuMu is not running, report that no instances were found. Do not start MuMu just to close it.

At the end, report:

- changes implemented
- verification evidence
- paths to `REPORT.md`, `proposals.md`, `cleanup.json`, and `cleanup.md`
- whether cleanup ran, waited until 05:00, or was skipped because MuMu was not running
- decisions requested from the user

Do not end the task before the cleanup phase has completed.
