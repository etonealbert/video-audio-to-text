#!/usr/bin/env pwsh
# Code linting script for Windows PowerShell

param(
    [switch]$Fix,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Code linting script for transcriber project

Usage: .\scripts\lint.ps1 [options]

Options:
    -Fix        Automatically fix linting issues where possible
    -Help       Show this help message

This script runs ruff check on the codebase.
"@
    exit 0
}

Write-Host "Linting code with ruff..." -ForegroundColor Green

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

if ($Fix) {
    Write-Host "Linting and fixing code..." -ForegroundColor Cyan
    ruff check --fix .
} else {
    Write-Host "Linting code..." -ForegroundColor Cyan
    ruff check .
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Code linting completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Code linting found issues" -ForegroundColor Yellow
    Write-Host "Run with -Fix to automatically fix some issues" -ForegroundColor Cyan
    exit 1
}
