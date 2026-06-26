#requires -Version 5.1
# Create the virtualenv, install the project (editable + dev), and install the git hook.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".venv")) {
    Write-Host "Creating .venv ..."
    python -m venv .venv
}

$py = Join-Path $root ".venv\Scripts\python.exe"
Write-Host "Installing project (editable + dev) ..."
& $py -m pip install --upgrade pip
& $py -m pip install -e ".[dev]"

Write-Host "Pointing git at committed hooks ..."
git config core.hooksPath scripts/hooks

Write-Host "Setup complete. Activate with: .\.venv\Scripts\Activate.ps1"
