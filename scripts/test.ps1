#requires -Version 5.1
# Run the test suite.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

pytest
