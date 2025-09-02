# Audio/Video Transcription Tool

A clean, modular Python command-line application that transcribes audio or video files into text using OpenAI's Whisper API. The tool handles files of any size by intelligently splitting them into API-safe chunks while preserving timeline accuracy.

## Features

- **Multiple Format Support**: MP3, MP4, MPEG, MPGA, M4A, WAV
- **Intelligent Chunking**: Splits large files using silence detection to avoid mid-word cuts
- **Multiple Output Formats**: Plain text (`.txt`), SRT subtitles (`.srt`), WebVTT (`.vtt`)
- **Robust Error Handling**: Exponential backoff retry logic for API reliability
- **Configurable**: Environment variables and CLI arguments for all settings
- **Type-Safe**: Fully type-annotated codebase with mypy compliance
- **Production Ready**: Comprehensive logging, cleanup, and error codes

## Requirements

- Python 3.10+
- FFmpeg (for audio/video processing)
- OpenAI API key

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
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=whisper-1
DEFAULT_BITRATE=128k
DEFAULT_MAX_CHUNK_MB=24
DEFAULT_MIN_SILENCE_MS=400
DEFAULT_SILENCE_THRESHOLD=-40
DEFAULT_CONCURRENCY=1
```

## Usage

### Basic Usage

```bash
# Transcribe to plain text
python -m transcriber.cli audio.mp3

# Transcribe video with verbose output
python -m transcriber.cli video.mp4 --verbose

# Generate SRT subtitles
python -m transcriber.cli interview.m4a --format srt

# Generate WebVTT subtitles
python -m transcriber.cli podcast.wav --format vtt
```

### Advanced Options

```bash
# Large file with custom chunking
python -m transcriber.cli large_file.mp4 \
  --max-chunk-mb 20 \
  --min-silence-ms 500 \
  --silence-threshold -35

# Multiple concurrent API calls (use carefully!)
python -m transcriber.cli audio.mp3 \
  --concurrency 2 \
  --verbose

# Specify language and custom bitrate
python -m transcriber.cli foreign_audio.wav \
  --language es \
  --bitrate 192k
```

### Command-Line Options

```
positional arguments:
  input_path            Path to audio or video file to transcribe

options:
  --format {txt,srt,vtt}
                        Output format (default: txt)
  --bitrate BITRATE     Audio bitrate for conversion (e.g., 128k, 192k)
  --max-chunk-mb MAX_CHUNK_MB
                        Maximum chunk size in MB (default: 24)
  --min-silence-ms MIN_SILENCE_MS
                        Minimum silence duration in milliseconds (default: 400)
  --silence-threshold SILENCE_THRESHOLD
                        Silence threshold in dB (default: -40)
  --language LANGUAGE   Language hint for transcription (e.g., en, es, fr)
  --model MODEL         OpenAI model to use (default: whisper-1)
  --concurrency CONCURRENCY
                        Number of concurrent API calls (default: 1)
  --verbose             Enable verbose logging
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

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `OPENAI_MODEL` | `whisper-1` | Whisper model to use |
| `DEFAULT_BITRATE` | `128k` | Audio bitrate for conversion |
| `DEFAULT_MAX_CHUNK_MB` | `24` | Maximum chunk size in MB |
| `DEFAULT_MIN_SILENCE_MS` | `400` | Minimum silence duration for splitting |
| `DEFAULT_SILENCE_THRESHOLD` | `-40` | Silence threshold in dB |
| `DEFAULT_CONCURRENCY` | `1` | Number of concurrent API calls |

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

- **Single chunk**: Files ≤24MB process as one chunk
- **Chunking overhead**: ~2-5 seconds per chunk for splitting
- **API timing**: ~1-3 seconds per minute of audio
- **Concurrent processing**: Use with caution due to rate limits

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
