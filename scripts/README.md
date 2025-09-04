# Windows Scripts for Transcriber

This directory contains Windows-specific scripts to help with development and usage of the transcriber project.

## PowerShell Scripts (.ps1)

These scripts are designed for Windows PowerShell and provide the most features:

### Setup and Environment

- **`setup.ps1`** - Complete project setup
  ```powershell
  .\scripts\setup.ps1          # Standard setup
  .\scripts\setup.ps1 -Force   # Force recreate environment
  .\scripts\setup.ps1 -Help    # Show help
  ```

- **`clean.ps1`** - Clean up temporary files
  ```powershell
  .\scripts\clean.ps1          # Clean temp files only
  .\scripts\clean.ps1 -Venv    # Clean virtual environment only
  .\scripts\clean.ps1 -All     # Clean everything
  ```

### Development Tools

- **`format.ps1`** - Code formatting with ruff
  ```powershell
  .\scripts\format.ps1         # Format code
  .\scripts\format.ps1 -Check  # Check formatting without changes
  ```

- **`lint.ps1`** - Code linting with ruff
  ```powershell
  .\scripts\lint.ps1           # Check code
  .\scripts\lint.ps1 -Fix      # Fix issues automatically
  ```

- **`type-check.ps1`** - Type checking with mypy
  ```powershell
  .\scripts\type-check.ps1     # Run type checking
  ```

### Transcription

- **`transcribe.ps1`** - Enhanced transcription wrapper
  ```powershell
  # Basic usage
  .\scripts\transcribe.ps1 audio.mp3
  
  # With options
  .\scripts\transcribe.ps1 interview.m4a -Format srt -EnableDiarization -VerboseLogging
  
  # Different backend
  .\scripts\transcribe.ps1 podcast.wav -Backend openai -Language en
  ```

## Batch Scripts (.bat)

These scripts work with Windows Command Prompt (CMD) and provide basic functionality:

### Setup

- **`setup.bat`** - Basic project setup
  ```cmd
  scripts\setup.bat          # Standard setup
  scripts\setup.bat --force  # Force recreate environment
  scripts\setup.bat --help   # Show help
  ```

### Transcription

- **`run-transcriber.bat`** - Simple transcription script
  ```cmd
  # Basic usage
  scripts\run-transcriber.bat audio.mp3
  
  # With options
  scripts\run-transcriber.bat interview.m4a --format srt --enable-diarization
  ```

## Prerequisites

### For PowerShell Scripts
- Windows PowerShell 5.1+ or PowerShell Core 7+
- Execution policy must allow script execution:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### For Batch Scripts
- Windows Command Prompt (included with Windows)
- No additional setup required

## Usage Recommendations

1. **First-time setup**: Use `setup.ps1` or `setup.bat` to get started
2. **Development**: Use PowerShell scripts for better features and error handling
3. **CI/CD or automation**: Batch scripts may be more compatible with some systems
4. **Daily transcription**: Use `transcribe.ps1` for the best experience

## Troubleshooting

### PowerShell Execution Policy Error
If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found
Ensure Python is installed and in your PATH:
1. Install Python from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart your terminal/PowerShell

### Virtual Environment Issues
If virtual environment activation fails:
1. Delete `.venv` folder
2. Run setup script with `-Force` flag
3. Ensure you have permission to create files in the project directory

### Script Not Found
Ensure you're running scripts from the project root directory:
```powershell
# Correct (from project root)
.\scripts\setup.ps1

# Incorrect (from scripts directory)
.\setup.ps1
```

## Script Features Comparison

| Feature | PowerShell Scripts | Batch Scripts |
|---------|-------------------|---------------|
| Setup Environment | ✅ Full featured | ✅ Basic |
| Code Formatting | ✅ | ❌ |
| Code Linting | ✅ | ❌ |
| Type Checking | ✅ | ❌ |
| Transcription | ✅ Advanced | ✅ Basic |
| Clean Up | ✅ | ❌ |
| Error Handling | ✅ Detailed | ✅ Basic |
| Help System | ✅ | ✅ Limited |
| Color Output | ✅ | ❌ |
