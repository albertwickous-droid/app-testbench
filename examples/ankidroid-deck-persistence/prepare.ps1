[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$AssetDir = Join-Path $RepoRoot "runs\case-assets\ankidroid"
$ApkPath = Join-Path $AssetDir "com.ichi2.anki_225033004.apk"
$DownloadUrl = "https://f-droid.org/repo/com.ichi2.anki_225033004.apk"
$ExpectedHash = "c7056f611c66fc91a8e290e18268a0d708e813704f51c66e4af1534d468f6790"

New-Item -ItemType Directory -Force -Path $AssetDir | Out-Null

if (Test-Path -LiteralPath $ApkPath) {
    $currentHash = (Get-FileHash -LiteralPath $ApkPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentHash -eq $ExpectedHash) {
        Write-Output $ApkPath
        return
    }
    if (-not $Force) {
        throw "APK hash mismatch at $ApkPath. Re-run with -Force to replace only this pinned test asset."
    }
    Remove-Item -LiteralPath $ApkPath -Force
}

$TempPath = "$ApkPath.download"
if (Test-Path -LiteralPath $TempPath) {
    Remove-Item -LiteralPath $TempPath -Force
}

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempPath
    $downloadedHash = (Get-FileHash -LiteralPath $TempPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($downloadedHash -ne $ExpectedHash) {
        throw "Downloaded APK SHA256 mismatch. Expected $ExpectedHash, got $downloadedHash."
    }
    Move-Item -LiteralPath $TempPath -Destination $ApkPath
}
finally {
    if (Test-Path -LiteralPath $TempPath) {
        Remove-Item -LiteralPath $TempPath -Force
    }
}

Write-Output $ApkPath
