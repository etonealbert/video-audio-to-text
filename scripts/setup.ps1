#!/usr/bin/env pwsh
# Setup script for Windows PowerShell
# Creates virtual environment and installs dependencies

param(
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Setup script for transcriber project

Usage: .\scripts\setup.ps1 [options]

Options:
    -Force      Force recreate virtual environment if it exists
    -Help       Show this help message

This script will:
1. Check Python installation
2. Create virtual environment
3. Install dependencies
4. Setup .env file if needed
"@
    exit 0
}

Write-Host "Setting up transcriber project for Windows..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (Test-Path ".venv") {
    if ($Force) {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force ".venv"
    } else {
        Write-Host "Virtual environment already exists. Use -Force to recreate." -ForegroundColor Yellow
        Write-Host "Activating existing environment..." -ForegroundColor Cyan
        & ".venv\Scripts\Activate.ps1"
        Write-Host "Virtual environment activated!" -ForegroundColor Green
        exit 0
    }
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
python -m venv .venv

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
.venv\Scripts\python.exe -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
.venv\Scripts\pip.exe install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Setup .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Cyan
    Copy-Item "env.example" ".env"
    Write-Host "✓ .env file created. Please edit it with your configuration." -ForegroundColor Yellow
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

Write-Host @"

✅ Setup completed successfully!

Next steps:
1. Edit .env file with your configuration:
   notepad .env

2. Test the installation:
   python -m transcriber.cli --help

3. Run a transcription (place an audio file in the current directory):
   python -m transcriber.cli your-audio-file.mp3

To activate the environment in the future:
   .venv\Scripts\Activate.ps1

"@ -ForegroundColor Green
