[CmdletBinding()]
param(
    [string]$Output = "",
    [string]$ApkPath = "",
    [string]$AdbPath = "",
    [switch]$SkipPrepare
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }
if (-not $ApkPath) { $ApkPath = Join-Path $RepoRoot "runs\case-assets\firefox\org.mozilla.fennec_fdroid_1600020.apk" }
$FlowPath = Join-Path $PSScriptRoot "flow.yaml"
$SitePath = Join-Path $PSScriptRoot "site"
$Port = 18765
$SiteUrl = "http://127.0.0.1:$Port/index.html"

if (-not $Output) { $Output = Join-Path $RepoRoot "runs\examples\firefox-webapp-session" }
New-Item -ItemType Directory -Force -Path $Output | Out-Null

if (-not $SkipPrepare) {
    $ApkPath = (& (Join-Path $PSScriptRoot "fetch-apk.ps1") | Select-Object -Last 1).Trim()
}
elseif (-not (Test-Path -LiteralPath $ApkPath)) {
    throw "Pinned Fennec APK is missing. Run fetch-apk.ps1 or omit -SkipPrepare."
}

function Test-LocalSite {
    param([int]$TargetPort)
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$TargetPort/index.html" -Method Head -TimeoutSec 3 -UseBasicParsing
        return $response.StatusCode -eq 200
    }
    catch { return $false }
}

function Wait-LocalSite {
    param([int]$TargetPort, [int]$TimeoutSeconds = 15)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while (-not (Test-LocalSite -TargetPort $TargetPort)) {
        if ((Get-Date) -gt $deadline) { return $false }
        Start-Sleep -Milliseconds 200
    }
    return $true
}

$startedServer = $null
if (Test-LocalSite -TargetPort $Port) {
    Write-Host "Using the existing local QA fixture on port $Port."
}
else {
    $portOwner = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $portOwner) {
        throw "Port $Port is occupied by a service that is not the local QA fixture."
    }
    $startedServer = Start-Process -FilePath $Python `
        -ArgumentList @("-m", "http.server", "$Port", "--bind", "127.0.0.1", "--directory", $SitePath) `
        -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru
    if (-not (Wait-LocalSite -TargetPort $Port)) {
        if (-not $startedServer.HasExited) {
            Stop-Process -Id $startedServer.Id -Force
            $startedServer.WaitForExit()
        }
        throw "The local QA fixture did not become ready on port $Port."
    }
}

$env:PYTHONPATH = (Join-Path $RepoRoot "src")
$env:PYTHONUTF8 = "1"
$env:FENNEC_APK = $ApkPath
$env:FENNEC_SITE_URL = $SiteUrl
$env:FENNEC_ABOUT_URL = "http://127.0.0.1:$Port/about.html"
$env:FENNEC_ORDERS_URL = "http://127.0.0.1:$Port/orders.html"
$runExit = 1
$downloadFile = "/sdcard/Download/app-testbench-browser-evidence.txt"
try {
    $doctorText = & $Python -m app_testbench doctor --json
    $doctorText | Write-Output
    if ($LASTEXITCODE -ne 0) { throw "app-testbench doctor failed with exit code $LASTEXITCODE." }
    $doctor = ($doctorText -join "`n") | ConvertFrom-Json

    $adbPath = $AdbPath
    if (-not $adbPath) {
        $adbPath = ($doctor.data.checks | Where-Object name -eq "adb" | Select-Object -First 1).message.Trim()
    }
    if (-not (Test-Path -LiteralPath $adbPath)) {
        throw "The ADB path reported by doctor is unavailable: $adbPath"
    }
    $serial = ($doctor.data.checks | Where-Object name -eq "selected_instance" | Select-Object -First 1).details.serial
    if (-not $serial) { throw "doctor did not report the selected MuMu ADB serial." }
    & $adbPath -s $serial shell rm -f $downloadFile
    if ($LASTEXITCODE -ne 0) { throw "Could not remove the previous case-owned download." }

    & $Python -m app_testbench run $FlowPath `
        --output $Output `
        --junit-xml (Join-Path $Output "junit.xml") `
        --wait-for-boot --boot-timeout 60
    $runExit = $LASTEXITCODE
    if ($runExit -ne 0) {
        throw "Firefox flow failed with exit code $runExit. Inspect $Output."
    }

    $observed = ((& $adbPath -s $serial shell cat $downloadFile 2>$null) -join "`n").Trim()
    $expected = "App TestBench browser download evidence`norder=A1101`nstatus=READY"
    if ($observed -ne $expected) {
        throw "Browser download verification failed. Observed: $observed"
    }
    $verification = "Remote path: $downloadFile`n`n$observed`n"
    [System.IO.File]::WriteAllText((Join-Path $Output "browser-download-verification.txt"), $verification, [System.Text.UTF8Encoding]::new($false))
}
finally {
    Remove-Item Env:FENNEC_APK -ErrorAction SilentlyContinue
    Remove-Item Env:FENNEC_SITE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:FENNEC_ABOUT_URL -ErrorAction SilentlyContinue
    Remove-Item Env:FENNEC_ORDERS_URL -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
    if ($null -ne $startedServer -and -not $startedServer.HasExited) {
        Stop-Process -Id $startedServer.Id -Force
        $startedServer.WaitForExit()
    }
}

Write-Host "Evidence written to $Output"
