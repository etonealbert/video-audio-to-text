@echo off
REM Simple transcription script for Windows Command Prompt

setlocal EnableDelayedExpansion

if "%1"=="" goto :help
if "%1"=="--help" goto :help
if "%1"=="-h" goto :help

set INPUT_FILE=%1
set FORMAT=txt
set BACKEND=whisperx
set EXTRA_ARGS=

REM Parse additional arguments
:parse_args
shift
if "%1"=="" goto :run_transcription
if "%1"=="--format" (
    shift
    set FORMAT=%1
    goto :parse_args
)
if "%1"=="--backend" (
    shift
    set BACKEND=%1
    goto :parse_args
)
if "%1"=="--verbose" (
    set EXTRA_ARGS=!EXTRA_ARGS! --verbose
    goto :parse_args
)
if "%1"=="--enable-alignment" (
    set EXTRA_ARGS=!EXTRA_ARGS! --enable-alignment
    goto :parse_args
)
if "%1"=="--enable-diarization" (
    set EXTRA_ARGS=!EXTRA_ARGS! --enable-diarization
    goto :parse_args
)
REM Add the argument as-is for other options
set EXTRA_ARGS=!EXTRA_ARGS! %1
goto :parse_args

:run_transcription
REM Check if input file exists
if not exist "%INPUT_FILE%" (
    echo ERROR: Input file '%INPUT_FILE%' not found
    exit /b 1
)

echo Transcribing: %INPUT_FILE%
echo Format: %FORMAT%
echo Backend: %BACKEND%
echo.
echo Running transcription...

REM Run transcription
python -m transcriber.cli "%INPUT_FILE%" --format %FORMAT% --backend %BACKEND% %EXTRA_ARGS%

if errorlevel 1 (
    echo.
    echo ❌ Transcription failed
    exit /b 1
) else (
    echo.
    echo ✅ Transcription completed successfully!
)
goto :end

:help
echo Transcription script for Windows Command Prompt
echo.
echo Usage: scripts\run-transcriber.bat ^<input-file^> [options]
echo.
echo Parameters:
echo     input-file          Path to audio or video file to transcribe
echo.
echo Options:
echo     --format ^<format^>    Output format: txt, srt, vtt (default: txt)
echo     --backend ^<backend^>  Backend: whisperx, openai (default: whisperx)
echo     --verbose           Enable verbose logging
echo     --enable-alignment  Enable word-level alignment (WhisperX only)
echo     --enable-diarization Enable speaker diarization (WhisperX only)
echo     --help              Show this help message
echo.
echo Examples:
echo     scripts\run-transcriber.bat audio.mp3
echo     scripts\run-transcriber.bat interview.m4a --format srt --enable-diarization
echo     scripts\run-transcriber.bat podcast.wav --format vtt --verbose

:end
