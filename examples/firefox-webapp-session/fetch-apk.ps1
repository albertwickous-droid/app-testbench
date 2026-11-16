[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$AssetDir = Join-Path $RepoRoot "runs\case-assets\firefox"
$ApkPath = Join-Path $AssetDir "org.mozilla.fennec_fdroid_1600020.apk"
$DownloadUrl = "https://f-droid.org/repo/org.mozilla.fennec_fdroid_1600020.apk"
$ExpectedHash = "43cf491bbc677244d7b56ba2e8ae20ccd802c9d8f6b44d6b6aff7eb1753eab1b"
$ExpectedSize = 129815928

New-Item -ItemType Directory -Force -Path $AssetDir | Out-Null

if (Test-Path -LiteralPath $ApkPath) {
    $item = Get-Item -LiteralPath $ApkPath
    $currentHash = (Get-FileHash -LiteralPath $ApkPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.Length -eq $ExpectedSize -and $currentHash -eq $ExpectedHash) {
        Write-Output $ApkPath
        return
    }
    if (-not $Force) {
        throw "APK mismatch at $ApkPath. Re-run with -Force to replace only this pinned asset."
    }
    Remove-Item -LiteralPath $ApkPath -Force
}

$TempPath = "$ApkPath.download"
if (Test-Path -LiteralPath $TempPath) { Remove-Item -LiteralPath $TempPath -Force }

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempPath
    $downloaded = Get-Item -LiteralPath $TempPath
    $downloadedHash = (Get-FileHash -LiteralPath $TempPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($downloaded.Length -ne $ExpectedSize) {
        throw "Downloaded APK size mismatch. Expected $ExpectedSize bytes, got $($downloaded.Length)."
    }
    if ($downloadedHash -ne $ExpectedHash) {
        throw "Downloaded APK SHA256 mismatch. Expected $ExpectedHash, got $downloadedHash."
    }
    Move-Item -LiteralPath $TempPath -Destination $ApkPath
}
finally {
    if (Test-Path -LiteralPath $TempPath) { Remove-Item -LiteralPath $TempPath -Force }
}

Write-Output $ApkPath
