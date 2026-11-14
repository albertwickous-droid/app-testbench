param(
    [string]$ProjectRoot = "",
    [string]$CodexExe = "",
    [switch]$DryRun,
    [switch]$SkipMuMuCleanup,
    [switch]$CleanupOnly,
    [switch]$NoWait,
    [switch]$SkipUiProcesses
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$utf8 = New-Object System.Text.UTF8Encoding($false)
$env:PYTHONUTF8 = "1"
$env:PIP_INDEX_URL = "https://pypi.org/simple"

if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
else {
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}

$promptPath = Join-Path $PSScriptRoot "daily-maintenance-prompt.md"
if (-not (Test-Path -LiteralPath $promptPath -PathType Leaf)) {
    throw "Maintenance prompt not found: $promptPath"
}

if (-not $CodexExe) {
    $codexCommand = Get-Command codex.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($codexCommand) {
        $CodexExe = $codexCommand.Source
    }
    elseif (Test-Path -LiteralPath (Join-Path $env:USERPROFILE ".local\bin\codex.exe") -PathType Leaf) {
        $CodexExe = Join-Path $env:USERPROFILE ".local\bin\codex.exe"
    }
    else {
        throw "codex.exe was not found. Pass -CodexExe explicitly."
    }
}
$CodexExe = (Resolve-Path -LiteralPath $CodexExe).Path

$automationRoot = Join-Path $ProjectRoot "runs\automation"
$dailyRoot = Join-Path $automationRoot "daily"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runDir = Join-Path $dailyRoot $stamp
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$lockPath = Join-Path $automationRoot "daily-maintenance.lock"
$lockStream = $null
$maintenanceStarted = $false
$cleanupDone = $false
$exitCode = 1
$metadata = $null
$metadataPath = $null
$finalPath = Join-Path $runDir "final.md"
$latestPath = Join-Path $automationRoot "latest.md"

function Write-CleanupReport {
    param(
        [string]$RunDir,
        [string]$FinalPath,
        $Cleanup
    )

    $jsonPath = Join-Path $RunDir "cleanup.json"
    $markdownPath = Join-Path $RunDir "cleanup.md"
    [System.IO.File]::WriteAllText(
        $jsonPath,
        ($Cleanup | ConvertTo-Json -Depth 8),
        $utf8
    )

    $lines = @(
        "# MuMu cleanup",
        "",
        "- Status: ``$($Cleanup.status)``",
        "- Policy: $($Cleanup.policy)",
        "- Cutoff: $($Cleanup.cutoff)",
        "- Finished: $($Cleanup.finished_at)",
        "- Stopped instances: $(@($Cleanup.stopped_instances) -join ', ')",
        "- UI processes found: $(@($Cleanup.ui_processes | ForEach-Object { $_.name }).Count)",
        "- Forced process closes: $(@($Cleanup.forced_processes).Count)",
        "- Warnings: $(@($Cleanup.warnings).Count)",
        "- Errors: $(@($Cleanup.errors).Count)",
        ""
    )
    if (@($Cleanup.warnings).Count -gt 0) {
        $lines += '## Warnings'
        $lines += ''
        $lines += @($Cleanup.warnings | ForEach-Object { "- $_" })
        $lines += ''
    }
    if (@($Cleanup.errors).Count -gt 0) {
        $lines += '## Errors'
        $lines += ''
        $lines += @($Cleanup.errors | ForEach-Object { "- $_" })
        $lines += ''
    }
    $markdown = ($lines -join "`r`n")
    [System.IO.File]::WriteAllText($markdownPath, $markdown + "`r`n", $utf8)

    if (Test-Path -LiteralPath $FinalPath -PathType Leaf) {
        [System.IO.File]::AppendAllText($FinalPath, "`r`n`r`n" + $markdown + "`r`n", $utf8)
    }
    else {
        [System.IO.File]::WriteAllText($FinalPath, $markdown + "`r`n", $utf8)
    }
}

function Invoke-MuMuCleanup {
    param(
        [string]$ProjectRoot,
        [string]$RunDir,
        [string]$Reason,
        [switch]$NoWait,
        [switch]$SkipUiProcesses
    )

    $cleanup = [ordered]@{
        policy = "Close MuMu after the maintenance run; if it finishes before 05:00, wait until 05:00; otherwise close immediately."
        reason = $Reason
        started_at = (Get-Date).ToString("o")
        cutoff = $null
        wait_seconds = 0
        finished_at = $null
        status = "unknown"
        instances_before = @()
        stopped_instances = @()
        instances_after = @()
        ui_processes = @()
        forced_processes = @()
        warnings = @()
        errors = @()
    }

    try {
        $cutoff = (Get-Date).Date.AddHours(5)
        $cleanup.cutoff = $cutoff.ToString("o")
        $now = Get-Date
        if ($NoWait) {
            $cleanup.policy = "NoWait was requested for a manual cleanup-only run; the 05:00 wait policy was bypassed."
        }
        elseif ($now -lt $cutoff) {
            $waitSeconds = [int][Math]::Ceiling(($cutoff - $now).TotalSeconds)
            $cleanup.wait_seconds = $waitSeconds
            Start-Sleep -Seconds $waitSeconds
        }

        $python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
        if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
            $cleanup.errors += "Project virtual environment was not found: $python"
        }
        else {
            try {
                $raw = & $python -m app_testbench instance list --json 2>&1
                $listExitCode = $LASTEXITCODE
                $text = ($raw | Out-String).Trim()
                if ($listExitCode -ne 0) {
                    throw "app-testbench instance list failed with exit code $listExitCode`: $text"
                }
                $payload = $text | ConvertFrom-Json
                if (-not $payload.ok) {
                    throw "app-testbench instance list returned ok=false: $text"
                }
                $instances = @($payload.data.instances)
                foreach ($instance in $instances) {
                    $cleanup.instances_before += [ordered]@{
                        index = $instance.index
                        name = $instance.name
                        player_state = $instance.player_state
                        running = $instance.running
                    }
                }
                $running = @($instances | Where-Object { $_.running -eq $true })
                foreach ($instance in $running) {
                    $stopRaw = & $python -m app_testbench instance stop ([string]$instance.index) --json 2>&1
                    $stopExitCode = $LASTEXITCODE
                    $stopText = ($stopRaw | Out-String).Trim()
                    if ($stopExitCode -eq 0) {
                        $cleanup.stopped_instances += [int]$instance.index
                    }
                    else {
                        $cleanup.errors += "Failed to stop instance $($instance.index) (exit $stopExitCode): $stopText"
                    }
                }
                Start-Sleep -Seconds 3
                $rawAfter = & $python -m app_testbench instance list --json 2>&1
                $afterExitCode = $LASTEXITCODE
                $afterText = ($rawAfter | Out-String).Trim()
                if ($afterExitCode -eq 0) {
                    $afterPayload = $afterText | ConvertFrom-Json
                    foreach ($instance in @($afterPayload.data.instances)) {
                        $cleanup.instances_after += [ordered]@{
                            index = $instance.index
                            player_state = $instance.player_state
                            running = $instance.running
                        }
                    }
                }
                else {
                    $cleanup.errors += "Post-cleanup instance list failed (exit $afterExitCode): $afterText"
                }
                $stillRunning = @($cleanup.instances_after | Where-Object { $_.running -eq $true })
                $staleUnknown = @($stillRunning | Where-Object { $_.player_state -eq "unknown" })
                $actuallyRunning = @($stillRunning | Where-Object { $_.player_state -ne "unknown" })
                if ($actuallyRunning.Count -gt 0) {
                    $cleanup.errors += "MuMu instance(s) still report running after shutdown: $(@($actuallyRunning | ForEach-Object { $_.index }) -join ', ')"
                }
                if ($staleUnknown.Count -gt 0) {
                    $cleanup.warnings += "MuMu manager reports running=true with player_state=unknown for instance(s) $(@($staleUnknown | ForEach-Object { $_.index }) -join ', '); this can be stale after the emulator UI closes."
                }
            }
            catch {
                $cleanup.errors += "MuMu instance cleanup failed: $($_.Exception.Message)"
            }
        }
    }
    catch {
        $cleanup.errors += "Cleanup timer failed: $($_.Exception.Message)"
    }

    if (-not $SkipUiProcesses) {
        try {
            $processNames = @("MuMuNxMain", "MuMuPlayer", "NemuPlayer")
            $uiProcesses = @(Get-Process -Name $processNames -ErrorAction SilentlyContinue)
            foreach ($process in $uiProcesses) {
                $cleanup.ui_processes += [ordered]@{
                    name = $process.ProcessName
                    id = $process.Id
                }
                try {
                    [void]$process.CloseMainWindow()
                }
                catch {
                    $cleanup.errors += "Could not request close for $($process.ProcessName) ($($process.Id)): $($_.Exception.Message)"
                }
            }

            if ($uiProcesses.Count -gt 0) {
                Start-Sleep -Seconds 3
                $remaining = @(Get-Process -Name $processNames -ErrorAction SilentlyContinue)
                foreach ($process in $remaining) {
                    try {
                        Stop-Process -Id $process.Id -Force
                        $cleanup.forced_processes += [ordered]@{
                            name = $process.ProcessName
                            id = $process.Id
                        }
                    }
                    catch {
                        $cleanup.errors += "Could not force-close $($process.ProcessName) ($($process.Id)): $($_.Exception.Message)"
                    }
                }
                Start-Sleep -Seconds 1
                $stillOpen = @(Get-Process -Name $processNames -ErrorAction SilentlyContinue)
                if ($stillOpen.Count -gt 0) {
                    $cleanup.errors += "MuMu UI process(es) remain after cleanup: $(@($stillOpen | ForEach-Object { "$($_.ProcessName)($($_.Id))" }) -join ', ')"
                }
            }
        }
        catch {
            $cleanup.errors += "MuMu UI cleanup failed: $($_.Exception.Message)"
        }
    }

    $cleanup.finished_at = (Get-Date).ToString("o")
    $cleanup.status = if (@($cleanup.errors).Count -gt 0) { "completed_with_errors" } else { "passed" }
    Write-CleanupReport -RunDir $RunDir -FinalPath $finalPath -Cleanup $cleanup
    return [pscustomobject]$cleanup
}

try {
    $lockStream = [System.IO.File]::Open(
        $lockPath,
        [System.IO.FileMode]::OpenOrCreate,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None
    )
    $lockText = "pid=$PID started=$((Get-Date).ToString('o'))"
    $lockBytes = [System.Text.Encoding]::UTF8.GetBytes($lockText)
    $lockStream.SetLength(0)
    $lockStream.Write($lockBytes, 0, $lockBytes.Length)
    $lockStream.Flush()

    $prompt = Get-Content -LiteralPath $promptPath -Raw
    $prompt = $prompt.Replace("{{PROJECT_ROOT}}", $ProjectRoot)
    $prompt = $prompt.Replace("{{RUN_DIR}}", $runDir)
    $promptFile = Join-Path $runDir "prompt.md"
    [System.IO.File]::WriteAllText($promptFile, $prompt, $utf8)

    $metadata = [ordered]@{
        started_at = (Get-Date).ToString("o")
        project_root = $ProjectRoot
        codex_exe = $CodexExe
        run_dir = $runDir
        sandbox = "workspace-write"
        network_access = $true
        ephemeral = $true
        mumu_cleanup = "enabled"
    }
    $metadataPath = Join-Path $runDir "run.json"
    [System.IO.File]::WriteAllText(
        $metadataPath,
        ($metadata | ConvertTo-Json -Depth 4),
        $utf8
    )

    $arguments = @(
        "exec",
        "--cd", $ProjectRoot,
        "--sandbox", "workspace-write",
        "--ephemeral",
        "-c", 'approval_policy="never"',
        "-c", 'sandbox_workspace_write.network_access=true',
        "--json",
        "-o", $finalPath,
        "-"
    )

    if ($DryRun) {
        [pscustomobject]@{
            ProjectRoot = $ProjectRoot
            CodexExe = $CodexExe
            RunDir = $runDir
            Prompt = $promptFile
            Arguments = ($arguments -join " ")
            MuMuCleanup = if ($SkipMuMuCleanup) { "skipped for this invocation" } else { "enabled" }
        } | Format-List
        return
    }

    if ($CleanupOnly) {
        $maintenanceStarted = $true
        if ($SkipMuMuCleanup) {
            $cleanup = [ordered]@{
                policy = "MuMu cleanup skipped for this invocation."
                reason = "SkipMuMuCleanup"
                started_at = (Get-Date).ToString("o")
                finished_at = (Get-Date).ToString("o")
                status = "skipped"
                stopped_instances = @()
                ui_processes = @()
                forced_processes = @()
                warnings = @()
                errors = @()
            }
            Write-CleanupReport -RunDir $runDir -FinalPath $finalPath -Cleanup $cleanup
        }
        else {
            $cleanup = Invoke-MuMuCleanup -ProjectRoot $ProjectRoot -RunDir $runDir -Reason "Manual cleanup-only run" -NoWait:$NoWait -SkipUiProcesses:$SkipUiProcesses
        }
        $cleanupDone = $true
        $metadata.cleanup_only = $true
        $metadata.cleanup = $cleanup
        [System.IO.File]::WriteAllText(
            $metadataPath,
            ($metadata | ConvertTo-Json -Depth 8),
            $utf8
        )
        if (Test-Path -LiteralPath $finalPath -PathType Leaf) {
            Copy-Item -LiteralPath $finalPath -Destination $latestPath -Force
        }
        $exitCode = if ($cleanup.status -eq "completed_with_errors") { 1 } else { 0 }
        exit $exitCode
    }

    $maintenanceStarted = $true
    $logPath = Join-Path $runDir "codex.jsonl"
    $stderrPath = Join-Path $runDir "codex.stderr.log"
    $originalErrorAction = $ErrorActionPreference
    try {
        # Codex writes expected MCP/auth warnings to stderr. In Windows PowerShell
        # 5.1 those warnings become non-terminating errors and `*>` would abort
        # the wrapper when ErrorActionPreference is Stop. Keep stdout/stderr
        # separate and let the native exit code decide success.
        $ErrorActionPreference = "Continue"
        $prompt | & $CodexExe @arguments 1> $logPath 2> $stderrPath
        $exitCode = $LASTEXITCODE
    }
    catch {
        $metadata.error = $_.Exception.Message
        [System.IO.File]::WriteAllText(
            $metadataPath,
            ($metadata | ConvertTo-Json -Depth 4),
            $utf8
        )
        throw
    }
    finally {
        $ErrorActionPreference = $originalErrorAction
    }
    $metadata.codex_finished_at = (Get-Date).ToString("o")
    $metadata.exit_code = $exitCode
    if ($exitCode -ne 0) {
        $metadata.error = "Codex exited with code $exitCode. See codex.jsonl and codex.stderr.log."
    }

    if ($SkipMuMuCleanup) {
        $cleanup = [ordered]@{
            policy = "MuMu cleanup skipped for this invocation."
            reason = "SkipMuMuCleanup"
            started_at = (Get-Date).ToString("o")
            finished_at = (Get-Date).ToString("o")
            status = "skipped"
            stopped_instances = @()
            ui_processes = @()
            forced_processes = @()
            warnings = @()
            errors = @()
        }
        Write-CleanupReport -RunDir $runDir -FinalPath $finalPath -Cleanup $cleanup
    }
    else {
        $cleanup = Invoke-MuMuCleanup -ProjectRoot $ProjectRoot -RunDir $runDir -Reason "Maintenance run finished" -NoWait:$NoWait -SkipUiProcesses:$SkipUiProcesses
    }
    $cleanupDone = $true
    $metadata.cleanup = $cleanup
    [System.IO.File]::WriteAllText(
        $metadataPath,
        ($metadata | ConvertTo-Json -Depth 8),
        $utf8
    )

    if (Test-Path -LiteralPath $finalPath -PathType Leaf) {
        Copy-Item -LiteralPath $finalPath -Destination $latestPath -Force
    }
    elseif ($exitCode -ne 0) {
        $failure = "# Daily maintenance failed`n`nThe Codex process exited with code $exitCode.`n`nSee ``$logPath``.`n"
        [System.IO.File]::WriteAllText($finalPath, $failure, $utf8)
        [System.IO.File]::WriteAllText($latestPath, $failure, $utf8)
    }
    else {
        [System.IO.File]::WriteAllText($latestPath, "Maintenance completed without a final agent message.`n", $utf8)
    }

    if (Test-Path -LiteralPath $logPath -PathType Leaf) {
        Get-Content -LiteralPath $logPath -Tail 80
    }
}
catch {
    if ($maintenanceStarted -and -not $cleanupDone) {
        if ($SkipMuMuCleanup) {
            $cleanup = [ordered]@{
                policy = "MuMu cleanup skipped for this invocation."
                reason = "SkipMuMuCleanup"
                started_at = (Get-Date).ToString("o")
                finished_at = (Get-Date).ToString("o")
                status = "skipped"
                stopped_instances = @()
                ui_processes = @()
                forced_processes = @()
                warnings = @()
                errors = @()
            }
            Write-CleanupReport -RunDir $runDir -FinalPath $finalPath -Cleanup $cleanup
        }
        else {
            $cleanup = Invoke-MuMuCleanup -ProjectRoot $ProjectRoot -RunDir $runDir -Reason "Maintenance run raised an error" -NoWait:$NoWait -SkipUiProcesses:$SkipUiProcesses
        }
        $cleanupDone = $true
        if ($metadata -and $metadataPath) {
            $metadata.cleanup = $cleanup
            [System.IO.File]::WriteAllText(
                $metadataPath,
                ($metadata | ConvertTo-Json -Depth 8),
                $utf8
            )
        }
    }
    throw
}
finally {
    if ($maintenanceStarted -and -not $cleanupDone) {
        if ($SkipMuMuCleanup) {
            $cleanup = [ordered]@{
                policy = "MuMu cleanup skipped for this invocation."
                reason = "SkipMuMuCleanup"
                started_at = (Get-Date).ToString("o")
                finished_at = (Get-Date).ToString("o")
                status = "skipped"
                stopped_instances = @()
                ui_processes = @()
                forced_processes = @()
                warnings = @()
                errors = @()
            }
            Write-CleanupReport -RunDir $runDir -FinalPath $finalPath -Cleanup $cleanup
        }
        else {
            $cleanup = Invoke-MuMuCleanup -ProjectRoot $ProjectRoot -RunDir $runDir -Reason "Maintenance run ended without explicit cleanup" -NoWait:$NoWait -SkipUiProcesses:$SkipUiProcesses
        }
        $cleanupDone = $true
        if ($metadata -and $metadataPath) {
            $metadata.cleanup = $cleanup
            [System.IO.File]::WriteAllText(
                $metadataPath,
                ($metadata | ConvertTo-Json -Depth 8),
                $utf8
            )
        }
    }
    if (Test-Path -LiteralPath $finalPath -PathType Leaf) {
        Copy-Item -LiteralPath $finalPath -Destination $latestPath -Force
    }
    if ($lockStream) {
        $lockStream.Dispose()
    }
}

exit $exitCode