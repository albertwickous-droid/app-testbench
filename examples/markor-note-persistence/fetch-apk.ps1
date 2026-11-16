[CmdletBinding()]
param(
    [string]$Destination = ""
)

$ErrorActionPreference = "Stop"
$ExpectedSha256 = "C29412E02D03E4F0511746A1BCEF48C6B73FC1F70C1024FBF04903B0B3F4C485"
$ExpectedSize = 11849016
$VersionCode = 164
$VersionName = "2026.10.0"
$Urls = @(
    "https://f-droid.org/repo/net.gsantner.markor_164.apk",
    "https://mirrors.tuna.tsinghua.edu.cn/fdroid/repo/net.gsantner.markor_164.apk",
    "https://ftp.lysator.liu.se/pub/fdroid/repo/net.gsantner.markor_164.apk",
    "https://fdroid.tetaneutral.net/fdroid/repo/net.gsantner.markor_164.apk"
)

$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
if ([string]::IsNullOrWhiteSpace($Destination)) {
    $Destination = Join-Path $root "runs\case-assets\net.gsantner.markor_164.apk"
}
$Destination = [IO.Path]::GetFullPath($Destination)
$parent = Split-Path -Parent $Destination
New-Item -ItemType Directory -Force -Path $parent | Out-Null

function Get-ApkHash([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

if (Test-Path -LiteralPath $Destination) {
    $size = (Get-Item -LiteralPath $Destination).Length
    $hash = Get-ApkHash $Destination
    if ($size -eq $ExpectedSize -and $hash -eq $ExpectedSha256) {
        Write-Host "Using verified Markor APK: $Destination"
        Write-Output $Destination
        return
    }
    throw "Existing file does not match the pinned Markor build. Move it away and rerun: $Destination"
}

$temp = "$Destination.download"
if (Test-Path -LiteralPath $temp) {
    Remove-Item -LiteralPath $temp -Force
}

Write-Host "Downloading Markor $VersionName (versionCode $VersionCode) from F-Droid or a signed-repository mirror..."
$downloaded = $false
foreach ($Url in $Urls) {
    Write-Host "Source: $Url"
    if (Test-Path -LiteralPath $temp) {
        Remove-Item -LiteralPath $temp -Force
    }
    try {
        if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
            & curl.exe -L --fail --retry 1 --connect-timeout 15 --output $temp $Url
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "curl exited with code $LASTEXITCODE for $Url"
                continue
            }
        } else {
            Invoke-WebRequest -Uri $Url -OutFile $temp
        }
    } catch {
        Write-Warning "Download failed from $Url : $($_.Exception.Message)"
        continue
    }

    $size = (Get-Item -LiteralPath $temp).Length
    $hash = Get-ApkHash $temp
    if ($size -eq $ExpectedSize -and $hash -eq $ExpectedSha256) {
        $downloaded = $true
        break
    }
    Write-Warning "Downloaded file from $Url did not match the pinned size and SHA256."
}

if (-not $downloaded) {
    if (Test-Path -LiteralPath $temp) {
        Remove-Item -LiteralPath $temp -Force
    }
    throw "Could not download the pinned Markor APK from any configured F-Droid source."
}

Move-Item -LiteralPath $temp -Destination $Destination
Write-Host "Verified Markor APK SHA256: $hash"
Write-Output $Destination
