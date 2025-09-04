#!/usr/bin/env pwsh
# Cleanup script for Windows PowerShell

param(
    [switch]$All,
    [switch]$Venv,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Cleanup script for transcriber project

Usage: .\scripts\clean.ps1 [options]

Options:
    -All        Clean everything including virtual environment
    -Venv       Only clean virtual environment
    -Help       Show this help message

This script removes temporary files, caches, and optionally the virtual environment.
"@
    exit 0
}

Write-Host "Cleaning up project files..." -ForegroundColor Green

if ($Venv -or $All) {
    if (Test-Path ".venv") {
        Write-Host "Removing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force ".venv"
        Write-Host "✓ Virtual environment removed" -ForegroundColor Green
    } else {
        Write-Host "✓ No virtual environment to remove" -ForegroundColor Cyan
    }
}

if (-not $Venv) {
    # Clean Python cache files
    Write-Host "Removing Python cache files..." -ForegroundColor Cyan
    
    if (Test-Path "__pycache__") {
        Remove-Item -Recurse -Force "__pycache__"
    }
    
    if (Test-Path "transcriber\__pycache__") {
        Remove-Item -Recurse -Force "transcriber\__pycache__"
    }
    
    # Remove .pyc files
    Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
    
    # Clean tool caches
    if (Test-Path ".mypy_cache") {
        Remove-Item -Recurse -Force ".mypy_cache"
    }
    
    if (Test-Path ".ruff_cache") {
        Remove-Item -Recurse -Force ".ruff_cache"
    }
    
    # Clean output directories
    if (Test-Path "outputs") {
        Remove-Item -Recurse -Force "outputs"
    }
    
    if (Test-Path "temp") {
        Remove-Item -Recurse -Force "temp"
    }
    
    Write-Host "✓ Temporary files cleaned" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Cleanup completed!" -ForegroundColor Green
