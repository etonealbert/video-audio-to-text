# Complete Windows Setup Guide

This guide provides detailed instructions for setting up the transcriber project on Windows systems.

## Prerequisites

### 1. Install Python 3.10+

#### Option 1: Official Python Installer (Recommended)
1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download the latest Python 3.10+ installer
3. **IMPORTANT**: During installation, check "Add Python to PATH"
4. Choose "Customize installation" and ensure these are selected:
   - pip
   - py launcher
   - Add Python to environment variables

#### Option 2: Windows Package Manager (winget)
```powershell
winget install Python.Python.3.11
```

#### Option 3: Microsoft Store
Search for "Python 3.11" in the Microsoft Store and install.

#### Verify Installation
Open PowerShell or Command Prompt and run:
```powershell
python --version
pip --version
```

### 2. Install FFmpeg

#### Option 1: Using winget (Windows 10+)
```powershell
winget install ffmpeg
```

#### Option 2: Using Chocolatey
First install Chocolatey if you haven't:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

Then install FFmpeg:
```powershell
choco install ffmpeg
```

#### Option 3: Manual Installation
1. Download FFmpeg from [https://ffmpeg.org/download.html#build-windows](https://ffmpeg.org/download.html#build-windows)
2. Extract to `C:\ffmpeg` (or any folder without spaces)
3. Add FFmpeg to PATH:
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Click "Environment Variables"
   - Under "System Variables", find "Path" and click "Edit"
   - Click "New" and add `C:\ffmpeg\bin`
   - Click "OK" to save all dialogs

#### Verify Installation
```powershell
ffmpeg -version
```

### 3. Enable PowerShell Script Execution (if using PowerShell scripts)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Project Setup

### Method 1: Automated Setup (Recommended)

#### Using PowerShell (Recommended)
```powershell
# Clone the repository
git clone <repository-url>
cd video-audio-to-text

# Run the automated setup script
.\scripts\setup.ps1
```

#### Using Command Prompt
```cmd
# Clone the repository
git clone <repository-url>
cd video-audio-to-text

# Run the automated setup script
scripts\setup.bat
```

### Method 2: Manual Setup

```powershell
# Clone the repository
git clone <repository-url>
cd video-audio-to-text

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1  # PowerShell
# OR
.venv\Scripts\activate.bat  # Command Prompt

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create environment file
Copy-Item env.example .env
```

### Method 3: Using Cross-Platform Makefile

If you have GNU Make installed (e.g., via Git for Windows or MSYS2):
```powershell
make setup-env  # Create .env file
make venv       # Create virtual environment and install dependencies
```

## Configuration

### Edit the .env file

Open the `.env` file in your preferred text editor:
```powershell
notepad .env
```

Configure the settings for your use case:

```env
# Backend selection (whisperx recommended for GPU acceleration)
TRANSCRIPTION_BACKEND=whisperx

# WhisperX settings (recommended for best performance)
WHISPERX_MODEL=large-v3
WHISPERX_DEVICE=auto
ENABLE_ALIGNMENT=true
ENABLE_DIARIZATION=false

# OpenAI settings (only if using openai backend)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Hugging Face token for speaker diarization
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx

# Audio processing
DEFAULT_BITRATE=128k
DEFAULT_MAX_CHUNK_MB=24
```

## Testing the Installation

### Basic Test
```powershell
# Show help to verify installation
python -m transcriber.cli --help
```

### Test with Audio File
Place an audio file (MP3, MP4, WAV, etc.) in the project directory and run:

```powershell
# Basic transcription
python -m transcriber.cli your-audio-file.mp3

# With verbose output
python -m transcriber.cli your-audio-file.mp3 --verbose

# Generate SRT subtitles
python -m transcriber.cli your-audio-file.mp3 --format srt
```

### Using Helper Scripts
```powershell
# PowerShell wrapper script (recommended)
.\scripts\transcribe.ps1 your-audio-file.mp3 -Format srt -VerboseLogging

# Command Prompt wrapper script
scripts\run-transcriber.bat your-audio-file.mp3 --format srt --verbose
```

## GPU Support (NVIDIA CUDA)

For GPU acceleration with WhisperX:

### 1. Install NVIDIA Drivers
- Download from [https://www.nvidia.com/drivers/](https://www.nvidia.com/drivers/)
- Install the latest drivers for your GPU

### 2. Install CUDA Toolkit (Optional)
WhisperX typically includes PyTorch with CUDA support, but for optimal performance:
- Download CUDA Toolkit 11.8 or 12.x from [https://developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads)

### 3. Verify GPU Support
```powershell
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA devices:', torch.cuda.device_count())"
```

### 4. Configure for GPU
In your `.env` file:
```env
WHISPERX_DEVICE=cuda
WHISPERX_COMPUTE_TYPE=float16
WHISPERX_BATCH_SIZE=16
```

## Development Setup

For development work:

### Install Development Dependencies
```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Install with development extras (if available)
pip install -e .
```

### Development Scripts
```powershell
# Format code
.\scripts\format.ps1

# Lint code
.\scripts\lint.ps1

# Type checking
.\scripts\type-check.ps1

# Clean up temporary files
.\scripts\clean.ps1
```

## Common Issues and Solutions

### Issue: "python" command not found
**Solution**: 
1. Reinstall Python with "Add to PATH" option checked
2. Or use `py` command instead: `py -m transcriber.cli --help`

### Issue: PowerShell execution policy error
**Solution**: 
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Virtual environment activation fails
**Solution**: 
```powershell
# Delete existing environment
Remove-Item -Recurse -Force .venv

# Recreate with setup script
.\scripts\setup.ps1 -Force
```

### Issue: FFmpeg not found
**Solution**: 
1. Verify FFmpeg is installed: `ffmpeg -version`
2. If not found, reinstall FFmpeg and ensure it's in PATH
3. Restart your terminal after installation

### Issue: CUDA/GPU not detected
**Solution**: 
1. Update NVIDIA drivers
2. Verify CUDA installation
3. Check PyTorch CUDA support: `python -c "import torch; print(torch.cuda.is_available())"`

### Issue: Permission denied during installation
**Solution**: 
1. Run PowerShell as Administrator
2. Or install to user directory: `pip install --user -r requirements.txt`

### Issue: Long file paths on Windows
**Solution**: 
1. Enable long path support in Windows 10/11:
   - Run `gpedit.msc`
   - Navigate to: Computer Configuration > Administrative Templates > System > Filesystem
   - Enable "Enable Win32 long paths"
2. Or use shorter directory names

## Performance Tips

### For Better Performance on Windows:
1. **Use SSD storage** for faster I/O during audio processing
2. **Close unnecessary applications** to free up memory
3. **Use GPU acceleration** when available (NVIDIA GPUs)
4. **Adjust batch size** based on available VRAM:
   - 6GB VRAM: `WHISPERX_BATCH_SIZE=16`
   - 8GB VRAM: `WHISPERX_BATCH_SIZE=24`
   - 12GB+ VRAM: `WHISPERX_BATCH_SIZE=32`

### For Large Files:
1. Increase virtual memory if needed
2. Use lower bitrate for preprocessing: `--bitrate 64k`
3. Reduce chunk size: `--max-chunk-mb 12`

## Getting Help

1. **Check this guide** for common setup issues
2. **Run with --verbose** to see detailed logs
3. **Check the main README.md** for usage examples
4. **Review scripts/README.md** for script-specific help

## Quick Reference

### Essential Commands
```powershell
# Setup (first time)
.\scripts\setup.ps1

# Activate environment
.venv\Scripts\Activate.ps1

# Basic transcription
python -m transcriber.cli audio.mp3

# Advanced transcription
.\scripts\transcribe.ps1 audio.mp3 -Format srt -EnableAlignment -VerboseLogging

# Show help
python -m transcriber.cli --help
```

### File Locations
- **Virtual environment**: `.venv\`
- **Configuration**: `.env`
- **Scripts**: `scripts\`
- **Output files**: Same directory as input files
- **Logs**: Console output (use `--verbose` for details)
