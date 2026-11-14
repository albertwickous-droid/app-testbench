param(
    [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Executable @Arguments 2>&1 | ForEach-Object { Write-Host $_ }
        return $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    Write-Host "Creating .venv..."
    $code = Invoke-Native -Executable "python" -Arguments @("-m", "venv", (Join-Path $projectRoot ".venv"))
    if ($code -ne 0) { exit $code }
}

if (-not $SkipInstall) {
    $code = Invoke-Native -Executable $venvPython -Arguments @("-m", "pip", "install", "-e", "$projectRoot[dev]")
    if ($code -ne 0) { exit $code }
}

Push-Location $projectRoot
try {
    $code = Invoke-Native -Executable $venvPython -Arguments @("-m", "ruff", "check", ".")
    if ($code -ne 0) { exit $code }

    $code = Invoke-Native -Executable $venvPython -Arguments @("-m", "ruff", "format", "--check", ".")
    if ($code -ne 0) { exit $code }

    $code = Invoke-Native -Executable $venvPython -Arguments @("-m", "pytest", "-q")
    if ($code -ne 0) { exit $code }

    $code = Invoke-Native -Executable $venvPython -Arguments @("-m", "build", "--no-isolation")
    if ($code -ne 0) { exit $code }

    $dist = Join-Path $projectRoot "dist"
    $artifacts = @(Get-ChildItem -LiteralPath $dist -File -ErrorAction Stop)
    if ($artifacts.Count -eq 0) {
        throw "No distribution artifacts found in $dist"
    }
    $twineArguments = @("-m", "twine", "check") + @($artifacts.FullName)
    $code = Invoke-Native -Executable $venvPython -Arguments $twineArguments
    if ($code -ne 0) { exit $code }

    Write-Host "All checks passed."
}
finally {
    Pop-Location
}
