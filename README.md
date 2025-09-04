# Audio/Video Transcription Tool

A powerful, GPU-accelerated Python command-line application for transcribing audio or video files into text. Features **WhisperX** (CUDA-optimized) as the primary backend with **OpenAI Whisper API** as a legacy option. Includes advanced features like word-level alignment and speaker diarization.

## Features

### Core Transcription
- **GPU-Accelerated**: WhisperX with CUDA support for 3-5x faster processing
- **Multiple Format Support**: MP3, MP4, MPEG, MPGA, M4A, WAV, PCM
- **Intelligent Chunking**: Splits large files using silence detection to avoid mid-word cuts
- **Multiple Output Formats**: Plain text (`.txt`), SRT subtitles (`.srt`), WebVTT (`.vtt`)

### Advanced Features (WhisperX)
- **Word-Level Alignment**: Precise timing for each word
- **Speaker Diarization**: Identify and label different speakers
- **Batched Processing**: Efficient GPU memory usage
- **Auto Device Detection**: Automatically uses CUDA when available

### Reliability & Configuration
- **Dual Backend Support**: WhisperX (default) or OpenAI API (legacy)
- **Robust Error Handling**: Exponential backoff retry logic
- **Highly Configurable**: Environment variables and CLI arguments
- **Type-Safe**: Fully type-annotated codebase with mypy compliance
- **Production Ready**: Comprehensive logging, cleanup, and error codes

## Requirements

### Core Requirements
- Python 3.10+
- FFmpeg (for audio/video processing)

### Backend Requirements
- **WhisperX Backend** (recommended): CUDA-capable GPU (optional but recommended)
- **OpenAI Backend** (legacy): OpenAI API key

### Optional Features
- **Speaker Diarization**: Hugging Face account and token

## Installation

### 1. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
```bash
winget install ffmpeg
```
Or download from [https://ffmpeg.org/](https://ffmpeg.org/)

### 2. Clone and Setup

```bash
git clone <repository-url>
cd video-audio-to-text

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your settings:

```bash
# Backend selection (whisperx recommended)
TRANSCRIPTION_BACKEND=whisperx

# WhisperX settings (recommended)
WHISPERX_MODEL=large-v3
WHISPERX_DEVICE=auto
ENABLE_ALIGNMENT=true
ENABLE_DIARIZATION=false

# OpenAI settings (legacy backend)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Hugging Face token for speaker diarization
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx

# Audio processing
DEFAULT_BITRATE=128k
DEFAULT_MAX_CHUNK_MB=24
```

## Usage

### Basic Usage (WhisperX - Default)

```bash
# Basic transcription (GPU-accelerated)
python -m transcriber.cli audio.mp3

# Generate SRT subtitles with speaker labels
python -m transcriber.cli interview.m4a --format srt --enable-diarization

# High-quality transcription with word alignment
python -m transcriber.cli podcast.wav --format vtt --enable-alignment

# PCM file transcription
python -m transcriber.cli "inputs/interview.pcm" \
  --pcm-sample-rate 24000 --pcm-channels 2 --pcm-bit-depth 16 --pcm-format s16le
```

### WhisperX Advanced Options

```bash
# Large file with GPU optimization
python -m transcriber.cli large_file.mp4 \
  --whisperx-model large-v3 \
  --whisperx-batch-size 32 \
  --whisperx-device cuda \
  --enable-alignment \
  --enable-diarization

# CPU-only processing
python -m transcriber.cli audio.mp3 \
  --whisperx-device cpu \
  --whisperx-compute-type int8

# Specific language and model
python -m transcriber.cli foreign_audio.wav \
  --language es \
  --whisperx-model medium \
  --whisperx-compute-type float16
```

### Legacy OpenAI API Usage

```bash
# Use OpenAI backend (requires API key)
python -m transcriber.cli audio.mp3 \
  --backend openai \
  --model whisper-1 \
  --concurrency 2

# OpenAI with language hint
python -m transcriber.cli foreign_audio.wav \
  --backend openai \
  --language es \
  --model whisper-1
```

### Command-Line Options

#### Core Options
```
positional arguments:
  input_path            Path to audio or video file to transcribe

basic options:
  --backend {whisperx,openai}
                        Transcription backend (default: whisperx)
  --format {txt,srt,vtt}
                        Output format (default: txt)
  --language LANGUAGE   Language hint (e.g., en, es, fr)
  --verbose             Enable verbose logging
```

#### WhisperX Options (Default Backend)
```
  --whisperx-model {tiny,base,small,medium,large,large-v2,large-v3}
                        WhisperX model (default: large-v3)
  --whisperx-device {cuda,cpu,auto}
                        Device for inference (default: auto)
  --whisperx-compute-type {int8,int16,float16,float32,auto}
                        Compute precision (default: auto)
  --whisperx-batch-size BATCH_SIZE
                        Batch size for GPU inference (default: 16)
  --enable-alignment    Enable word-level alignment
  --enable-diarization  Enable speaker diarization
  --hf-token HF_TOKEN   Hugging Face token (required for diarization)
```

#### OpenAI Options (Legacy Backend)
```
  --model MODEL         OpenAI model (default: gpt-4o-mini-transcribe)
  --fallback-model MODEL
                        Fallback model (default: whisper-1)
  --concurrency CONCURRENCY
                        Concurrent API calls (default: 1)
```

#### Audio Processing Options
```
  --bitrate BITRATE     Audio bitrate (e.g., 128k, 192k)
  --max-chunk-mb SIZE   Maximum chunk size in MB (default: 24)
  --min-silence-ms MS   Minimum silence duration (default: 400)
  --silence-threshold DB
                        Silence threshold in dB (default: -40)
```

## Output Files

The tool creates output files in the same directory as the input file:

- **Text format**: `<filename>_transcription.txt`
- **SRT format**: `<filename>.srt`
- **WebVTT format**: `<filename>.vtt`

## How It Works

1. **Validation**: Checks file format and FFmpeg availability
2. **Audio Extraction**: Converts video to MP3 if needed, normalizes audio
3. **Intelligent Chunking**: Splits large files at silence boundaries to stay under API limits
4. **Transcription**: Processes chunks with retry logic and rate limiting
5. **Output Generation**: Combines results and generates final transcript

## Configuration

### Environment Variables

All settings can be configured via environment variables in the `.env` file:

#### Backend Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `TRANSCRIPTION_BACKEND` | `whisperx` | Backend to use (`whisperx` or `openai`) |

#### WhisperX Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPERX_MODEL` | `large-v3` | WhisperX model to use |
| `WHISPERX_DEVICE` | `auto` | Device for inference (`cuda`, `cpu`, `auto`) |
| `WHISPERX_COMPUTE_TYPE` | `auto` | Compute precision (`int8`, `float16`, etc.) |
| `WHISPERX_BATCH_SIZE` | `16` | Batch size for GPU inference |
| `ENABLE_ALIGNMENT` | `true` | Enable word-level alignment |
| `ENABLE_DIARIZATION` | `false` | Enable speaker diarization |
| `HF_TOKEN` | - | Hugging Face token (required for diarization) |

#### OpenAI Settings (Legacy)
| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (required for openai backend) |
| `OPENAI_MODEL` | `gpt-4o-mini-transcribe` | OpenAI model to use |
| `OPENAI_FALLBACK_MODEL` | `whisper-1` | Fallback model |
| `DEFAULT_CONCURRENCY` | `1` | Number of concurrent API calls |

#### Audio Processing
| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_BITRATE` | `128k` | Audio bitrate for conversion |
| `DEFAULT_MAX_CHUNK_MB` | `24` | Maximum chunk size in MB |
| `DEFAULT_MIN_SILENCE_MS` | `400` | Minimum silence duration for splitting |
| `DEFAULT_SILENCE_THRESHOLD` | `-40` | Silence threshold in dB |

### Silence Detection Tuning

For optimal chunking results, you may need to adjust silence detection parameters:

- **`--min-silence-ms`**: Increase for noisy audio, decrease for clean audio
- **`--silence-threshold`**: More negative values detect quieter silences

## Development

### Setup Development Environment

```bash
# Install dependencies
make venv
source .venv/bin/activate
source .venv/bin/activate && python -m transcriber.cli "inputs/МИАНовостиPythonSenior.WAV"
# Or manually:
pip install -r requirements.txt
```

### Code Quality

```bash
# Format code
make format
# or: ruff format .

# Lint code
make lint
# or: ruff check .

# Type check
make type
# or: mypy transcriber --strict
```

### Testing

```bash
# Test with sample file
python -m transcriber.cli sample.mp3 --verbose

# Show help
python -m transcriber.cli --help


cd C:\Users\alber\Helpers
$file = "rec_$((Get-Date).ToString('yyyyMMdd_HHmmss')).mp3"

ffmpeg -y -f dshow -i audio="virtual-audio-capturer" `
  -ac 2 -ar 48000 -c:a libmp3lame -b:a 192k $file

```

## Troubleshooting

### FFmpeg Not Found

**Error**: `FFmpeg not found in PATH`

**Solution**: Install FFmpeg using the instructions above, or ensure it's in your system PATH.

### API Rate Limits

**Error**: `Rate limit exceeded`

**Solution**: 
- Use `--concurrency 1` (default) to avoid overwhelming the API
- The tool automatically retries with exponential backoff
- Check your OpenAI API usage limits

### Large File Processing

For very large files (>2 hours):
- Ensure sufficient disk space for temporary files
- Consider using smaller `--max-chunk-mb` values
- Monitor API usage costs

### Memory Usage

The tool streams audio processing to minimize memory usage, but very large files may still require significant RAM during splitting.

### Silence Detection Issues

If chunks are being split poorly:
- Adjust `--min-silence-ms` (try 200-800ms)
- Modify `--silence-threshold` (try -30 to -50 dB)
- Check audio quality and background noise levels

## Exit Codes

- `0`: Success
- `2`: Invalid input/path/format
- `3`: Conversion/splitting error
- `4`: API error after retries
- `5`: Unexpected internal error

## Performance Notes

### WhisperX (Default Backend)
- **GPU acceleration**: 3-5x faster than CPU with CUDA
- **Batched processing**: Efficient memory usage with configurable batch sizes
- **Memory requirements**: 4-8GB VRAM for large models on GPU
- **CPU fallback**: Automatic fallback to CPU if CUDA unavailable
- **Processing speed**: ~10-30x real-time on GPU, ~2-5x on CPU

### OpenAI API (Legacy Backend)
- **Single chunk**: Files ≤24MB process as one chunk
- **Chunking overhead**: ~2-5 seconds per chunk for splitting
- **API timing**: ~1-3 seconds per minute of audio
- **Concurrent processing**: Use with caution due to rate limits

### Hardware Recommendations
- **GPU**: NVIDIA GPU with 6GB+ VRAM for optimal performance
- **CPU**: Modern multi-core processor for CPU fallback
- **RAM**: 8GB+ system RAM for large file processing
- **Storage**: SSD recommended for faster I/O during chunking

## Contributing

1. Follow the existing code style (ruff + mypy)
2. Add type hints to all functions
3. Update tests if adding features
4. Ensure all linting passes

## License

Licensed under the [MIT License](./LICENSE).

## Support

For issues and questions:
1. Check this README for common problems
2. Review the logs with `--verbose` flag
3. Open an issue with log output and file details
