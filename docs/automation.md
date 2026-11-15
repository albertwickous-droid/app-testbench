# Daily maintenance automation

The canonical maintenance scheduler for this workspace is **Codex native Scheduled** in local-project mode. It runs daily at 04:00 Asia/Shanghai and uses `scripts/automation/codex-scheduled-prompt.md` as its prompt.

The Windows Task Scheduler wrapper is retained only as a fallback. The default task name is `app-testbench-daily-optimizer`; after a repository rename an existing task may still use the old name (for example `mumu-runner-daily-optimizer`). Verify the actual task name with `Get-ScheduledTask` and confirm it is **disabled** so the native scheduler and the wrapper cannot edit the same worktree concurrently. Do not enable or start both schedulers for the same maintenance window.

The maintenance workflow has a deliberately narrow contract:

- **Implement automatically:** reproducible bug fixes, tests, validation, packaging, CI, documentation, and other low-risk improvements inside the existing product scope.
- **Research only:** new capabilities and expansion ideas. Every proposal is saved for human review and is not added to the product without approval.
- **Never automatically:** commit, push, tag, publish, alter remotes or secrets, start MuMu, or operate a live device. The only MuMu lifecycle action is closing it after the run, as described below.

## Native Codex Scheduled (active)

Create or edit the Codex Scheduled task with the local project folder selected, daily at 04:00, and paste the contents of [`scripts/automation/codex-scheduled-prompt.md`](../scripts/automation/codex-scheduled-prompt.md) as its prompt. The native prompt invokes the maintenance contract directly and performs MuMu cleanup as a final phase; it does not call `daily-maintenance.ps1`, so there is no nested Codex process.

Use local-project mode for this workflow. An isolated worktree separates edits but is unnecessary here and can make cleanup/report paths confusing. If the repository is moved or renamed, update the native Scheduled task's local project folder and prompt path before the next run; otherwise the scheduler may continue to target the old path.

## Windows Task Scheduler fallback (disabled)

The fallback invokes `codex exec` in the local project directory. The computer must be powered on, the maintainer must be logged in, and Codex authentication must already be configured.

From the repository root, re-enable it only when native Scheduled is intentionally unavailable:

```powershell
.\scripts\automation\register-daily-task.ps1
```

The default schedule is every day at **04:00 local time**. The task:

- wakes the computer when Windows permits it
- can start while on battery power
- starts after a missed schedule when the machine becomes available
- prevents overlapping maintenance runs
- has a two-hour execution limit
- runs with the current user's limited token, not administrator rights

Use a different task name or time if needed:

```powershell
.\scripts\automation\register-daily-task.ps1 -TaskName "app-testbench-maintenance" -At "03:30"
```

## MuMu cleanup after every run

After the Codex maintenance process finishes, the wrapper applies this shutdown policy:

- if the run finishes **before 05:00 local time**, it waits until 05:00 and then closes MuMu
- if the run finishes **at or after 05:00**, it closes MuMu immediately
- it stops only instances reported as running by `app-testbench instance list`
- it then closes the MuMu main UI process if it is still present
- it does not touch unrelated applications or MuMu remote backend services

Cleanup evidence is written to `cleanup.json` and `cleanup.md` in the run directory, and copied into the final report. If MuMu is not installed or no instance is running, the step completes without starting anything.

For a controlled manual cleanup test, use:

```powershell
.\scripts\automation\daily-maintenance.ps1 -CleanupOnly -NoWait -SkipUiProcesses
```

`-NoWait` and `-SkipUiProcesses` are test-only switches. Do not use them for the scheduled production run.

## Run manually

Inspect the exact command without executing Codex:

```powershell
.\scripts\automation\daily-maintenance.ps1 -DryRun
```

Run one maintenance cycle now:

```powershell
.\scripts\automation\daily-maintenance.ps1
```

Start the registered task immediately:

```powershell
Start-ScheduledTask -TaskName "app-testbench-daily-optimizer"
```

Check the fallback state and last result:

```powershell
Get-ScheduledTask -TaskName "app-testbench-daily-optimizer"
Get-ScheduledTaskInfo -TaskName "app-testbench-daily-optimizer"
```

The current state is `Disabled`. Disable it again before switching back to native Scheduled:

```powershell
Disable-ScheduledTask -TaskName "app-testbench-daily-optimizer"
```

Re-enable it only for a deliberate fallback window:

```powershell
Enable-ScheduledTask -TaskName "app-testbench-daily-optimizer"
```

## Artifacts

Each run writes under the ignored path:

```text
runs/automation/daily/<timestamp>/
├── prompt.md
├── run.json
├── codex.jsonl
├── codex.stderr.log
├── final.md
├── REPORT.md
├── proposals.md
├── cleanup.json
└── cleanup.md
```

The latest final response is copied to:

```text
runs/automation/latest.md
```

These files can contain source paths and source excerpts. Review them before sharing. Expected MCP/plugin warnings are written to `codex.stderr.log`; the native exit code and `codex.jsonl` determine whether the maintenance process succeeded.

## Remove the scheduled task

```powershell
Unregister-ScheduledTask -TaskName "app-testbench-daily-optimizer" -Confirm:$false
```

Removing the task does not delete any run artifacts.
