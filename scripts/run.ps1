#requires -Version 5.1
# Run the pipeline. Pass a log file path, or pipe a log into stdin.
#   ./scripts/run.ps1 data/sample.log
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

rawlog-triage @args
