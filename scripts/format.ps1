#!/usr/bin/env pwsh
# Code formatting script for Windows PowerShell

param(
    [switch]$Check,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Code formatting script for transcriber project

Usage: .\scripts\format.ps1 [options]

Options:
    -Check      Check formatting without making changes
    -Help       Show this help message

This script runs ruff format on the codebase.
"@
    exit 0
}

Write-Host "Formatting code with ruff..." -ForegroundColor Green

# Check if ruff is available
try {
    $ruffVersion = ruff --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Ruff not found"
    }
    Write-Host "Found ruff: $ruffVersion" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: ruff is not installed" -ForegroundColor Red
    Write-Host "Please install dependencies: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

if ($Check) {
    Write-Host "Checking code formatting..." -ForegroundColor Cyan
    ruff format --check .
} else {
    Write-Host "Formatting code..." -ForegroundColor Cyan
    ruff format .
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Code formatting completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Code formatting failed" -ForegroundColor Red
    exit 1
}
