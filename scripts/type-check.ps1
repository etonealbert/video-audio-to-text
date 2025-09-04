#!/usr/bin/env pwsh
# Type checking script for Windows PowerShell

param(
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Type checking script for transcriber project

Usage: .\scripts\type-check.ps1

This script runs mypy type checking on the transcriber module.
"@
    exit 0
}

Write-Host "Type checking with mypy..." -ForegroundColor Green

# Check if mypy is available
try {
    $mypyVersion = mypy --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Mypy not found"
    }
    Write-Host "Found mypy: $mypyVersion" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: mypy is not installed" -ForegroundColor Red
    Write-Host "Please install dependencies: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host "Running type check..." -ForegroundColor Cyan
mypy transcriber --strict

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Type checking completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Type checking found issues" -ForegroundColor Red
    exit 1
}
