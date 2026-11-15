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
$Port = 18766
$VideoSize = 4372373
$AssetDir = Join-Path $RepoRoot "runs\case-assets\vlc-http-playback"
$FlowPath = Join-Path $PSScriptRoot "flow.yaml"
$ApkPath = Join-Path $AssetDir "org.videolan.vlc_13070208.apk"
$VideoPath = Join-Path $AssetDir "sintel-trailer.mp4"

if (-not $Output) {
    $Output = Join-Path $RepoRoot "runs\examples\vlc-http-playback"
}
New-Item -ItemType Directory -Force -Path $Output | Out-Null

if ($SkipPrepare) {
    if (-not (Test-Path -LiteralPath $ApkPath) -or -not (Test-Path -LiteralPath $VideoPath)) {
        throw "Pinned VLC assets are missing. Run prepare.ps1 first or omit -SkipPrepare."
    }
}
else {
    $assets = (& (Join-Path $PSScriptRoot "prepare.ps1") | Select-Object -Last 1).Trim()
    $assetParts = $assets.Split("|", 2)
    if ($assetParts.Count -ne 2) { throw "prepare.ps1 did not return APK and video paths." }
}

function Test-RangeMediaServer {
    param([int]$TargetPort)
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$TargetPort/sintel-trailer.mp4" `
            -Headers @{ Range = "bytes=0-15" } -TimeoutSec 3 -UseBasicParsing
        $contentRange = $response.Headers["Content-Range"]
        if ($contentRange -is [array]) { $contentRange = $contentRange -join "," }
        return $response.StatusCode -eq 206 -and
            "$contentRange" -match "^bytes 0-15/$VideoSize$"
    }
    catch { return $false }
}

function Wait-RangeMediaServer {
    param([int]$TargetPort, [int]$TimeoutSeconds = 15)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while (-not (Test-RangeMediaServer -TargetPort $TargetPort)) {
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
if (Test-RangeMediaServer -TargetPort $Port) {
    Write-Host "Using the existing byte-range media server on port $Port."
}
else {
    $portOwner = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $portOwner) {
        throw "Port $Port is occupied by a service that is not the pinned byte-range media server."
    }
    $startedServer = Start-Process -FilePath $Python `
        -ArgumentList @((Join-Path $PSScriptRoot "range_server.py"), "--directory", $AssetDir,
            "--bind", "127.0.0.1", "--port", "$Port") `
        -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru
    if (-not (Wait-RangeMediaServer -TargetPort $Port)) {
        if (-not $startedServer.HasExited) {
            Stop-Process -Id $startedServer.Id -Force
            $startedServer.WaitForExit()
        }
        throw "The byte-range media server did not become ready on port $Port."
    }
}

$runExit = 1
try {
    $cacheBuster = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $env:VLC_APK = $ApkPath
    $env:VLC_MEDIA_URL = "http://127.0.0.1:$Port/sintel-trailer.mp4?case=$cacheBuster"
    & $Python -m app_testbench.cli run $FlowPath `
        --output $Output `
        --junit-xml (Join-Path $Output "junit.xml") `
        --wait-for-boot --boot-timeout 60
    $runExit = $LASTEXITCODE
}
finally {
    Remove-Item Env:VLC_APK -ErrorAction SilentlyContinue
    Remove-Item Env:VLC_MEDIA_URL -ErrorAction SilentlyContinue
    if ($null -ne $startedServer -and -not $startedServer.HasExited) {
        Stop-Process -Id $startedServer.Id -Force
        $startedServer.WaitForExit()
    }
}

if ($runExit -ne 0) {
    throw "The VLC flow failed with exit code $runExit."
}
