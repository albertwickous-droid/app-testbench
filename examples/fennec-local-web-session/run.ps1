[CmdletBinding()]
param(
    [string]$Output = "",
    [switch]$SkipPrepare
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }
$Port = 18765
$SitePath = Join-Path $PSScriptRoot "site"
$FlowPath = Join-Path $PSScriptRoot "flow.yaml"
$AssetDir = Join-Path $RepoRoot "runs\case-assets\fennec-local-web-session"
$ApkPath = Join-Path $AssetDir "org.mozilla.fennec_fdroid_1600020.apk"

if (-not $Output) {
    $Output = Join-Path $RepoRoot "runs\examples\fennec-local-web-session"
}
New-Item -ItemType Directory -Force -Path $Output | Out-Null

if ($SkipPrepare) {
    if (-not (Test-Path -LiteralPath $ApkPath)) {
        throw "Pinned APK is missing at $ApkPath. Run prepare.ps1 first or omit -SkipPrepare."
    }
}
else {
    $ApkPath = (& (Join-Path $PSScriptRoot "prepare.ps1") | Select-Object -Last 1).Trim()
}

function Test-FieldDeskSite {
    param([int]$TargetPort)
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$TargetPort/" `
            -TimeoutSec 3 -UseBasicParsing
        if ($response.StatusCode -ne 200) { return $false }
        return $response.Content -match "FieldDesk QA Console"
    }
    catch { return $false }
}

function Wait-FieldDeskSite {
    param([int]$TargetPort, [int]$TimeoutSeconds = 15)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while (-not (Test-FieldDeskSite -TargetPort $TargetPort)) {
        if ((Get-Date) -gt $deadline) { return $false }
        Start-Sleep -Milliseconds 200
    }
    return $true
}

& $Python -m app_testbench.cli doctor --json
if ($LASTEXITCODE -ne 0) {
    throw "app-testbench doctor failed with exit code $LASTEXITCODE."
}

$startedServer = $null
if (Test-FieldDeskSite -TargetPort $Port) {
    Write-Host "Using the existing FieldDesk QA server on port $Port."
}
else {
    $portOwner = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $portOwner) {
        throw "Port $Port is occupied by a service that is not the FieldDesk QA site."
    }
    $startedServer = Start-Process -FilePath $Python `
        -ArgumentList @("-m", "http.server", "$Port", "--bind", "127.0.0.1") `
        -WorkingDirectory $SitePath -WindowStyle Hidden -PassThru
    if (-not (Wait-FieldDeskSite -TargetPort $Port)) {
        if (-not $startedServer.HasExited) {
            Stop-Process -Id $startedServer.Id -Force
            $startedServer.WaitForExit()
        }
        throw "The FieldDesk QA site did not become ready on port $Port."
    }
}

$runExit = 1
try {
    $env:FENNEC_APK = $ApkPath
    $env:FENNEC_SITE_URL = "http://127.0.0.1:$Port/"
    & $Python -m app_testbench.cli run $FlowPath `
        --output $Output `
        --junit-xml (Join-Path $Output "junit.xml") `
        --wait-for-boot --boot-timeout 60
    $runExit = $LASTEXITCODE
}
finally {
    Remove-Item Env:FENNEC_APK -ErrorAction SilentlyContinue
    Remove-Item Env:FENNEC_SITE_URL -ErrorAction SilentlyContinue
    if ($null -ne $startedServer -and -not $startedServer.HasExited) {
        Stop-Process -Id $startedServer.Id -Force
        $startedServer.WaitForExit()
    }
}

if ($runExit -ne 0) {
    throw "The Fennec flow failed with exit code $runExit."
}
