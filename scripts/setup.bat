@echo off
REM Setup script for Windows Command Prompt
REM Creates virtual environment and installs dependencies

setlocal EnableDelayedExpansion

if "%1"=="--help" goto :help
if "%1"=="-h" goto :help

echo Setting up transcriber project for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check 'Add Python to PATH' during installation
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python: !PYTHON_VERSION!

REM Check if virtual environment exists
if exist ".venv" (
    if "%1"=="--force" (
        echo Removing existing virtual environment...
        rmdir /s /q ".venv"
    ) else (
        echo Virtual environment already exists. Use --force to recreate.
        echo Activating existing environment...
        call .venv\Scripts\activate.bat
        echo Virtual environment activated!
        goto :end
    )
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

REM Setup .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy "env.example" ".env" >nul
    echo ✓ .env file created. Please edit it with your configuration.
) else (
    echo ✓ .env file already exists
)

echo.
echo ✅ Setup completed successfully!
echo.
echo Next steps:
echo 1. Edit .env file with your configuration:
echo    notepad .env
echo.
echo 2. Test the installation:
echo    python -m transcriber.cli --help
echo.
echo 3. Run a transcription (place an audio file in the current directory):
echo    python -m transcriber.cli your-audio-file.mp3
echo.
echo To activate the environment in the future:
echo    .venv\Scripts\activate.bat
echo.
goto :end

:help
echo Setup script for transcriber project
echo.
echo Usage: scripts\setup.bat [options]
echo.
echo Options:
echo     --force     Force recreate virtual environment if it exists
echo     --help      Show this help message
echo.
echo This script will:
echo 1. Check Python installation
echo 2. Create virtual environment
echo 3. Install dependencies
echo 4. Setup .env file if needed

:end
