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
$FlowPath = Join-Path $PSScriptRoot "flow.yaml"
$AssetDir = Join-Path $RepoRoot "runs\case-assets\ankidroid"
$ApkPath = Join-Path $AssetDir "com.ichi2.anki_225033004.apk"

if (-not $Output) {
    $Output = Join-Path $RepoRoot "runs\examples\ankidroid-deck-persistence"
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

& $Python -m app_testbench.cli doctor --json
if ($LASTEXITCODE -ne 0) {
    throw "app-testbench doctor failed with exit code $LASTEXITCODE."
}
$env:PYTHONIOENCODING = "utf-8"
$AdbPath = (& $Python -c "from app_testbench.config import build_settings; print(build_settings().require_adb())").Trim()
Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue
if (-not $AdbPath) {
    throw "ADB discovery returned an empty path."
}
$readyDevices = @(& $AdbPath devices | ForEach-Object {
    if ($_ -match '^(\S+)\s+device$') { $Matches[1] }
})
if ($readyDevices.Count -ne 1) {
    throw "Expected exactly one ready ADB device, found $($readyDevices.Count)."
}
$Serial = $readyDevices[0]

# pm clear does not revoke MANAGE_EXTERNAL_STORAGE or remove AnkiDroid's
# external collection. Reset both so every run starts from onboarding.
& $AdbPath -s $Serial install -r $ApkPath | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Could not pre-install AnkiDroid for environment reset."
}
& $AdbPath -s $Serial shell am force-stop com.ichi2.anki | Out-Null
& $AdbPath -s $Serial shell cmd appops set com.ichi2.anki MANAGE_EXTERNAL_STORAGE deny | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Could not revoke AnkiDroid's all-files access before the run."
}
& $AdbPath -s $Serial shell rm -rf /storage/emulated/0/AnkiDroid
if ($LASTEXITCODE -ne 0) {
    throw "Could not remove AnkiDroid's case-owned external collection."
}

$runExit = 1
try {
    $env:ANKIDROID_APK = $ApkPath
    & $Python -m app_testbench.cli run $FlowPath `
        --output $Output `
        --junit-xml (Join-Path $Output "junit.xml") `
        --wait-for-boot --boot-timeout 60
    $runExit = $LASTEXITCODE
}
finally {
    Remove-Item Env:ANKIDROID_APK -ErrorAction SilentlyContinue
}

if ($runExit -ne 0) {
    throw "The AnkiDroid flow failed with exit code $runExit."
}
