#!/usr/bin/env pwsh
# Transcription wrapper script for Windows PowerShell

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$InputFile,
    
    [string]$Format = "txt",
    [string]$Backend = "whisperx",
    [string]$Language,
    [switch]$EnableAlignment,
    [switch]$EnableDiarization,
    [switch]$VerboseLogging,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Transcription wrapper script for Windows PowerShell

Usage: .\scripts\transcribe.ps1 <input-file> [options]

Parameters:
    InputFile           Path to audio or video file to transcribe

Options:
    -Format <format>    Output format: txt, srt, vtt (default: txt)
    -Backend <backend>  Backend: whisperx, openai (default: whisperx)
    -Language <lang>    Language hint (e.g., en, es, fr)
    -EnableAlignment    Enable word-level alignment (WhisperX only)
    -EnableDiarization  Enable speaker diarization (WhisperX only)
    -VerboseLogging     Enable verbose logging
    -Help               Show this help message

Examples:
    .\scripts\transcribe.ps1 audio.mp3
    .\scripts\transcribe.ps1 interview.m4a -Format srt -EnableDiarization
    .\scripts\transcribe.ps1 podcast.wav -Format vtt -EnableAlignment -VerboseLogging
"@
    exit 0
}

# Check if input file exists
if (-not (Test-Path $InputFile)) {
    Write-Host "ERROR: Input file '$InputFile' not found" -ForegroundColor Red
    exit 1
}

# Build command arguments
$args = @()
$args += $InputFile
$args += "--format", $Format
$args += "--backend", $Backend

if ($Language) {
    $args += "--language", $Language
}

if ($EnableAlignment) {
    $args += "--enable-alignment"
}

if ($EnableDiarization) {
    $args += "--enable-diarization"
}

if ($VerboseLogging) {
    $args += "--verbose"
}

Write-Host "Transcribing: $InputFile" -ForegroundColor Green
Write-Host "Format: $Format" -ForegroundColor Cyan
Write-Host "Backend: $Backend" -ForegroundColor Cyan

if ($Language) {
    Write-Host "Language: $Language" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Running transcription..." -ForegroundColor Yellow

# Run transcription
python -m transcriber.cli @args

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Transcription completed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Transcription failed" -ForegroundColor Red
    exit 1
}
