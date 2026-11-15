[CmdletBinding()]
param(
    [string]$ApkPath = "",
    [string]$NoteTitle = "",
    [string]$AdbPath = $env:APP_TESTBENCH_ADB,
    [string]$Serial = $env:APP_TESTBENCH_SERIAL,
    [int]$Instance = 0,
    [switch]$KeepInstalled
)

$ErrorActionPreference = "Stop"
$ExpectedSha256 = "C29412E02D03E4F0511746A1BCEF48C6B73FC1F70C1024FBF04903B0B3F4C485"
$ExpectedSize = 11849016
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))

if ([string]::IsNullOrWhiteSpace($NoteTitle)) {
    $NoteTitle = "app-testbench-persistence-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
}
if ($NoteTitle -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,60}$') {
    throw "NoteTitle must use 1-61 ASCII letters, digits, dots, underscores, or hyphens."
}

if ([string]::IsNullOrWhiteSpace($ApkPath)) {
    $ApkPath = & (Join-Path $PSScriptRoot "fetch-apk.ps1") | Select-Object -Last 1
}
$ApkPath = (Resolve-Path -LiteralPath $ApkPath).Path
if ((Get-Item -LiteralPath $ApkPath).Length -ne $ExpectedSize) {
    throw "APK size does not match the pinned Markor build: $ApkPath"
}
$hash = (Get-FileHash -LiteralPath $ApkPath -Algorithm SHA256).Hash.ToUpperInvariant()
if ($hash -ne $ExpectedSha256) {
    throw "APK SHA256 does not match the pinned Markor build: $ApkPath"
}

$cli = (Get-Command app-testbench -ErrorAction SilentlyContinue).Source
if (-not $cli) {
    $localCli = Join-Path $root ".venv\Scripts\app-testbench.exe"
    if (Test-Path -LiteralPath $localCli) {
        $cli = $localCli
    }
}
if (-not $cli) {
    throw "app-testbench is not installed. See the repository README, then rerun this script."
}

if ([string]::IsNullOrWhiteSpace($AdbPath)) {
    $deviceProcess = Get-Process -Name MuMuNxDevice -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($deviceProcess -and $deviceProcess.Path) {
        $candidate = Join-Path (Split-Path -Parent $deviceProcess.Path) "adb.exe"
        if (Test-Path -LiteralPath $candidate) {
            $AdbPath = $candidate
        }
    }
}
if ([string]::IsNullOrWhiteSpace($AdbPath)) {
    $adbCommand = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($adbCommand) {
        $AdbPath = $adbCommand.Source
    }
}
if (-not $AdbPath -or -not (Test-Path -LiteralPath $AdbPath)) {
    throw "adb.exe was not found. Set APP_TESTBENCH_ADB or pass -AdbPath."
}

if ([string]::IsNullOrWhiteSpace($Serial)) {
    $devices = @(& $AdbPath devices | Where-Object { $_ -match '\s+device$' })
    if ($devices.Count -ne 1) {
        throw "Expected exactly one ready ADB device. Pass -Serial when multiple devices are connected."
    }
    $Serial = (($devices | Select-Object -First 1) -split '\s+')[0]
}

$runId = Get-Date -Format 'yyyyMMdd-HHmmss'
$caseRoot = Join-Path $root "runs\examples\markor-note-persistence\$runId"
New-Item -ItemType Directory -Force -Path $caseRoot | Out-Null
$junitPath = Join-Path $caseRoot "junit.xml"
$cliJsonPath = Join-Path $caseRoot "cli-run.json"

Write-Host "Installing pinned Markor build so the test can reset app data deterministically..."
& $cli --instance $Instance install $ApkPath --grant-permissions --expected-package net.gsantner.markor --expected-version-code 164 --expected-version-name 2026.10.0 --json
if ($LASTEXITCODE -ne 0) {
    throw "Markor installation failed with exit code $LASTEXITCODE."
}

& $AdbPath -s $Serial shell pm clear net.gsantner.markor | Out-Null
& $AdbPath -s $Serial shell cmd appops set net.gsantner.markor MANAGE_EXTERNAL_STORAGE allow | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Could not grant MANAGE_EXTERNAL_STORAGE to Markor on the test instance."
}

$env:MARKOR_APK = $ApkPath
$env:NOTE_TITLE = $NoteTitle
$runExit = 0
try {
    Write-Host "Running Markor persistence flow with note title: $NoteTitle"
    & $cli --instance $Instance run (Join-Path $PSScriptRoot "flow.yaml") --output (Join-Path $caseRoot "artifacts") --junit-xml $junitPath --wait-for-boot --boot-timeout 60 --json | Tee-Object -FilePath $cliJsonPath
    $runExit = $LASTEXITCODE
} finally {
    if (-not $KeepInstalled) {
        & $AdbPath -s $Serial shell rm -f "/sdcard/Documents/markor/$NoteTitle.md" | Out-Null
        & $AdbPath -s $Serial uninstall net.gsantner.markor | Out-Null
    }
}

Write-Host "CLI JSON: $cliJsonPath"
Write-Host "JUnit:    $junitPath"
exit $runExit
