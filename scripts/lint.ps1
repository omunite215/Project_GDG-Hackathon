#requires -Version 5.1
# Lint + format check. Mirrors the pre-commit hook.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

ruff check .
ruff format --check .
Write-Host "lint: OK"
